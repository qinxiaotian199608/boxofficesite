#!/usr/bin/python3
#coding:utf-8

import os
import sqlite3
from common import *

class database:
    def __init__(self, filename = "videos.db"):
        self.filename = filename
        self.conn = sqlite3.connect(os.path.join('database', filename))
        self.cursor = self.conn.cursor()
        with open(os.path.join('database', 'schema.sql'), mode='r') as f:
            self.cursor.executescript(f.read())
        self.conn.commit()

    def str_process(self, str_in):
        str_out = str_in.replace('"', '""')
        str_out = str_out.replace("'", "''")
        return str_out

    def get_video_downloaded(self, program, url):
        c = self.cursor
        c.execute('SELECT video_downloaded FROM record WHERE program = "{program}" AND url = "{url}";'.format(**locals()))
        fetchone = c.fetchone()
        return True if fetchone and fetchone[0] else False

    def get_title(self, program, url):
        c = self.cursor
        c.execute('SELECT title FROM record WHERE program = "{program}" AND url = "{url}";'.format(**locals()))
        fetchone = c.fetchone()
        return fetchone[0] if fetchone and fetchone[0] else None

    def set_title(self, program, url, title):
        c = self.cursor
        conn = self.conn
        log.debug('title = {}'.format(title))
        title = self.str_process(title)
        c.execute('UPDATE record SET title = "{title}" WHERE program = "{program}" AND url = "{url}";'.format(**locals()))
        conn.commit()

    def add_video_record(self, program, url):
        c = self.cursor
        conn = self.conn
        log.debug('url = {}'.format(url))
        c.execute('INSERT OR IGNORE INTO record (program, url) VALUES ("{program}", "{url}");'.format(**locals()))
        conn.commit()

    def set_video_downloaded(self, program, url):
        c = self.cursor
        conn = self.conn
        log.debug('url = {}'.format(url))
        c.execute('UPDATE record SET video_downloaded = 1 WHERE program = "{program}" AND url = "{url}";'.format(**locals()))
        conn.commit()

    def set_video_file(self, program, url, video_file):
        c = self.cursor
        conn = self.conn
        log.debug('video_file = {}'.format(video_file))
        video_file = self.str_process(video_file)
        c.execute('UPDATE record SET video_file = "{video_file}" WHERE program = "{program}" AND url = "{url}";'.format(**locals()))
        conn.commit()

    def set_audio_file(self, program, video_file, audio_file):
        c = self.cursor
        conn = self.conn
        log.debug('video_file = {}, audio_file = {}'.format(video_file, audio_file))
        video_file = self.str_process(video_file)
        audio_file = self.str_process(audio_file)
        c.execute('UPDATE record SET audio_file = "{audio_file}" WHERE program = "{program}" AND video_file = "{video_file}";'.format(**locals()))
        conn.commit()

    def set_audio_converted(self, program, audio_file):
        c = self.cursor
        conn = self.conn
        log.debug('audio_file = {}'.format(audio_file))
        audio_file = self.str_process(audio_file)
        c.execute('UPDATE record SET audio_converted = 1 WHERE program = "{program}" AND audio_file = "{audio_file}";'.format(**locals()))
        conn.commit()

    def get_file_need_convert(self, program):
        c = self.cursor
        conn = self.conn
        c.execute('SELECT video_file FROM record WHERE program = "{program}" AND video_downloaded = 1 AND audio_converted = 0;'.format(**locals()))
        return c.fetchall()

    def set_audio_normalized(self, program, audio_file):
        c = self.cursor
        conn = self.conn
        log.debug('audio_file = {}'.format(audio_file))
        audio_file = self.str_process(audio_file)
        c.execute('UPDATE record SET audio_normalized = 1 WHERE program = "{program}" AND audio_file = "{audio_file}";'.format(**locals()))
        conn.commit()

    def get_file_need_normalize(self, program):
        c = self.cursor
        conn = self.conn
        c.execute('SELECT audio_file FROM record WHERE program = "{program}" AND audio_normalized = 0 AND audio_converted = 1;'.format(**locals()))
        return c.fetchall()
