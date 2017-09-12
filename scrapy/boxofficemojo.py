from common import *
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import traceback
from pyquery import PyQuery as pq
import re
import sqlite3
import os
import time

mojo_earliest_year = 2017

class bom_session:
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=5)
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        #self.douban = douban.douban()

    def set_database(self, db):
        self.db = db

    def get_weeks_number_for_year(self, year):
        '''http://www.boxofficemojo.com/weekly/?yr=2016&p=.htm'''
        log.debug("year = {}".format(year))
        try:
            url = "http://www.boxofficemojo.com/weekly/?yr={}&p=.htm".format(year)
            r = self.session.get(url)
            if (r.status_code == 200):
                log_file(r.text, "get_weeks_number_for_year.html")
                pq_page = pq(r.text)
            else:
                log.error("get '{}' fail, code".format(url, r.status_code))
                return 0

        except:
            traceback.print_exc()
            return 0

        return int(pq_page('table').eq(2).find('tr').eq(2).find('td').eq(7).text())

    def get_lastest_list(self):
        '''last week on website: http://www.boxofficemojo.com/weekly/?view=year&p=.htm'''
        try:
            url = "http://www.boxofficemojo.com/weekly/?view=year&p=.htm";
            r = self.session.get(url)
            if (r.status_code == 200):
                log_file(r.text, "get_lastest_list.html")
                return r.text
            else:
                log.error("get '{}' fail, code".format(url, r.status_code))
                return None

        except:
            traceback.print_exc()
            return None

    def get_lastest_year_week(self):
        content = self.get_lastest_list()
        if not content:
            return 0, 0

        pq_page = pq(content)
        mojo_last = pq_page('body > div[id=container] > div[id=main] > div[id=body] > table > tr > td > center > table > tr > td').eq(8)('a').attr('href')
        log.debug("mojo last url: {}".format(mojo_last))
        m = re.match(r"\/weekly\/chart\/\?yr=(\d{4})\&wk=(\d{2})\&p=\.htm", mojo_last)

        if m:
            return m.group(1, 2)
        else:
            log.error("mojo last string: {}".format(mojo_last))
            return 0, 0

    def update_by_year_week(self, year, week):
        log.debug("update database: year = {}, week = {}".format(year, week))
        page = self.get_mojo_week(year, week)

        #total movie count
        try:
            movies_on_this_week =int(re.search("TOTAL \((\d+) MOVIES\):", page).group(1))
        except:
            #no movie count, should be not exist
            traceback.print_exc()
            log.error("no movie this week?")
            return

        pq_page = pq(page)
        table_content = pq_page("center")
        td_list = table_content.find('td')

        for index in range(0, movies_on_this_week):
            self.update_one_movie_in_week(index, td_list, year, week)

        self.db.update_by_year_week(year, week, movies_on_this_week)

    def update_one_movie_in_week(self, i, td_list, year, week):
        start_offset = 15
        td_for_each_movie = 12
        offset = start_offset + i * td_for_each_movie
        movie_desc_url = td_list.eq(offset + 2).find('a').eq(0).attr['href']
        try:
            mojo_id = re.search("id=(.*)\.htm", movie_desc_url, re.IGNORECASE).group(1)
            #log.debug('mojo_id = {}'.format(mojo_id))
        except:
            mojo_id = ''

        if mojo_id:
            movie_title = td_list.eq(offset + 2).find('a').eq(0).text()
            #log.debug('movie_title = {}'.format(movie_title))
            if re.search("studio=(.*)\.htm", td_list.eq(offset + 3).find('a').eq(0).attr['href']):
                studio = re.search("studio=(.*)\.htm", td_list.eq(offset + 3).find('a').eq(0).attr['href']).group(1)
            else:
                studio = ''
            #log.debug('studio = {}'.format(studio))
            weekly_gross = td_list.eq(offset + 4).text().replace('$', '').replace(',', '')
            #log.debug('weekly_gross = {}'.format(weekly_gross))
            theater_count = td_list.eq(offset + 6).text().replace(',', '')
            #log.debug('theater_count = {}'.format(theater_count))

            self.db.update_one_movie_in_week(mojo_id, year, week, studio, weekly_gross, theater_count)
            self.get_movie_desc(mojo_id)

    def convert_release_date(self, date_str):
        '''date_str as June 2, 2017, output as 2017-06-02'''
        month_dict = {'January':'1', 'February':'2', 'March':'3', 'April': '4', 'May':'5', 'June':'6', 'July':'7', 'August':'8', 'September':'9', 'October':'10', 'November':'11', 'December':'12'}
        try:
            month, day, year = date_str.split(' ')
            month = month_dict[month]
            day = day.replace(',', '')
        except:
            log.error('error, string = {}'.format(date_str))
            month, day, year = ('1', '1', '1970')
        return "{}-{}-{}".format(year, month.zfill(2), day.zfill(2))

    def convert_runtime(self, runtime_str):
        '''2 hrs. 21 min.'''
        minutes = 0
        for s in runtime_str.split('.'):
            if 'hrs' in s:
                for s2 in s.split(' '):
                    if s2.isdigit():
                        minutes += 60 * int(s2)
            elif 'min' in s:
                for s2 in s.split(' '):
                    if s2.isdigit():
                        minutes += int(s2)

        return minutes

    def convert_budget(self, budget_str):
        '''$149 million'''
        budget = 0
        budget_str = budget_str.replace('$', '')
        if 'million' in budget_str:
            for s in budget_str.split(' '):
                for s2 in s.split(' '):
                    if s2.isdigit():
                        budget += 1000000 * int(s2)

        return budget

    def get_movie_desc(self, mojo_id):
        '''http://www.boxofficemojo.com/movies/?page=main&id={mojo_id}.htm'''
        if not self.db.exist_mojo_desc(mojo_id):
            page = self.get_mojo_desc(mojo_id)
            pq_page = pq(page)
            try:
                image_url = pq_page('[valign="top"][align="center"]').eq(0).find('img')[0].attrib['src']
            except:
                image_url = ''

            title = pq_page('td[valign="top"][align="center"]').eq(1).find('b').eq(0).text()
            title = title.replace('"', '').replace("'", '')
            desc_list = pq_page('td[valign="top"][align="center"]').eq(1).find('td')
            distributor = desc_list.eq(2).find('b').text()
            release_date = self.convert_release_date(desc_list.eq(3).find('b').text())
            genre = desc_list.eq(4).find('b').text()
            runtime = self.convert_runtime(desc_list.eq(5).find('b').text())
            mpaa_rate = desc_list.eq(6).find('b').text()
            budget = self.convert_budget(desc_list.eq(7).find('b').text())
            self.db.update_mojo_desc(mojo_id, title, distributor, release_date, genre, runtime, mpaa_rate, image_url, budget)
            time.sleep(3)
        else:
            log.debug('{} exist in database, no need to update'.format(mojo_id))


    def get_mojo_desc(self, mojo_id):
        retry = 0
        while retry < 5:
            try:
                r = self.session.get('http://www.boxofficemojo.com/movies/?page=main&id={}.htm'.format(mojo_id))
                if (r.status_code == 200):
                    log_file(r.text, "mojo_{}".format(mojo_id))
                    return r.text
                else:
                    log.error("get mojo id = {}, status = {}".format(mojo_id, r.status_code))
                    retry += 1
                    time.sleep(3)
            except:
                retry = 5
                log.error("get mojo desc error")
                traceback.print_exc()

    def get_mojo_week(self, year, week):
        try:
            r = self.session.get('http://www.boxofficemojo.com/weekly/chart/?yr={}&wk={}&p=.htm'.format(year, str(week).zfill(2)))
            if (r.status_code == 200):
                log_file(r.text, "mojo_{}_{}".format(year, week))
                return r.text
            else:
                log.error("get mojo week {}".format(r.status_code))
        except:
           log.error("get mojo week error")
           traceback.print_exc()

    def update_full(self):
        lastest_year, lastest_week = self.get_lastest_year_week()
        lastest_year = int(lastest_year)
        lastest_week = int(lastest_week)
        for year in range(lastest_year, 1981, -1):
            log.info('year = {}'.format(year))
            if year == lastest_year:
                for week in range(lastest_week, 0, -1):
                    log.info('week = {}'.format(week))
                    self.update_by_year_week(year, week)
            else:
                for week in range(int(self.get_weeks_number_for_year(year)), 0, -1):
                    log.info('week = {}'.format(week))
                    self.update_by_year_week(year, week)

    def update_new(self):
        lastest_year, lastest_week = self.get_lastest_year_week()
        lastest_year = int(lastest_year)
        lastest_week = int(lastest_week)
        lastest_year_db, lastest_week_db = self.db.get_lastest_year_week()
        for year in range(lastest_year_db, lastest_year + 1):
            log.info('year = {}'.format(year))
            if year == lastest_year_db:
                start_week = lastest_week_db + 1
            else:
                start_week = 1

            if year == lastest_year:
                end_week = lastest_week + 1
            else:
                end_week = int(self.get_weeks_number_for_year(year)) + 1

            for week in range(start_week, end_week):
                log.info('week = {}'.format(week))
                self.update_by_year_week(year, week)

class bom_db:
    def __init__(self):
        self.conn = sqlite3.connect(os.path.join('database', 'boxofficemojo.db'))
        self.cur = self.conn.cursor()
        with open(os.path.join('database', 'boxofficemojo.sql')) as fp:
            self.cur.executescript(fp.read())  # or con.executescript

    def exist_year_weak(self, year, week):
        self.cur.execute("SELECT * FROM bom_weekly_movie_count WHERE year = ? AND week = ?", (year, week))
        sql_fetchone = self.cur.fetchone()
        if not sql_fetchone:
            return False
        else:
            return True

    def exist_mojo_desc(self, mojo_id):
        self.cur.execute('SELECT * FROM bom_movie_details WHERE mojo_id = ?', (mojo_id, ))
        sql_fetchone = self.cur.fetchone()
        if not sql_fetchone:
            return False
        else:
            return True

    def update_by_year_week(self, year, week, movies_on_this_week):
        self.cur.execute('INSERT OR REPLACE INTO bom_weekly_movie_count VALUES ("{}", "{}", "{}")'.format(year, week, movies_on_this_week))
        self.conn.commit()
        log.debug("year={}, week={}, movies_on_this_week={}".format(year, week, movies_on_this_week))

    def update_one_movie_in_week(self, mojo_id, year, week, studio, weekly_gross, theater_count):
        self.cur.execute('INSERT OR REPLACE INTO bom_movie_weekly VALUES ("{mojo_id}", "{year}", "{week}", "{studio}", "{weekly_gross}", "{theater_count}")'.format(**locals()))
        self.conn.commit()
        log.debug("mojo_id={}, year={}, week={}, studio={}, weekly_gross={}, theater_count={}".format(mojo_id, year, week, studio, weekly_gross, theater_count))

    def update_mojo_desc(self, mojo_id, title, distributor, release_date, genre, runtime, mpaa_rate, image_url, budget):
        self.cur.execute('INSERT OR REPLACE INTO bom_movie_details VALUES ("{mojo_id}", "{title}", "{distributor}", "{release_date}", "{genre}", "{runtime}", "{mpaa_rate}", "{image_url}", "{budget}")'.format(**locals()))
        self.conn.commit()
        log.debug("mojo_id={}, title={}, distributor={}, release_date={}, genre={}, runtime={}, mpaa_rate={}, image_url={}, budget={}".format(mojo_id, title, distributor, release_date, genre, runtime, mpaa_rate, image_url, budget))

    def get_lastest_year_week(self):
        self.cur.execute('SELECT MAX("year") FROM bom_weekly_movie_count')
        year = self.cur.fetchone()[0]
        self.cur.execute('SELECT MAX("week") FROM bom_weekly_movie_count WHERE year={}'.format(year))
        week = self.cur.fetchone()[0]
        log.debug('lastest year, week in database is {}, {}'.format(year, week))
        return year, week


def update_mojo_full(last_year, last_week):
    last_year = int(last_year)
    last_week = int(last_week)
    for year in range(last_year, mojo_earliest_year - 1, -1):
        log.info("{}".format(year))
        for week in range(last_week if year == last_year else get_last_week(year), 0, -1):
            log.info("check in database: year = {}, week = {}".format(year, week))
            if not exist_year_weak(year, week):
                update_mojo(year, week)
            else:
                update_mojo(year, week)
                pass

def scrapy(args):
    log.debug("scrapy")
    db = bom_db()
    s = bom_session()
    s.set_database(db)
    lastest_year, lastest_week = s.get_lastest_year_week()
    if args.new:
        s.update_new()
    elif args.full:
        s.update_full()
    elif args.year and args.week:
        s.update_by_year_week(args.year, args.week)
