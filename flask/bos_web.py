# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '..', 'database', 'boxofficemojo.db'),
))

app.config.from_envvar('BOW_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/<year>/<week>')
def show_weekly_top10(year, week):
    year = int(year)
    week = int(week)
    db = get_db()
    cur = db.execute('''select weekly_gross, theater_count, title, image_url, bom_movie_weekly.mojo_id
from bom_movie_weekly
inner join bom_movie_details
on bom_movie_weekly.mojo_id = bom_movie_details.mojo_id
where year = {} and week = {}
order by weekly_gross DESC'''.format(year, week))
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

