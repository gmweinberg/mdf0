import os

from flask import Flask, request, session, render_template, redirect
from markupsafe import escape
from mdf0_util import (get_config, get_sql_conn, check_password, get_topic_stats, recursive_kill)
from secret import get_secret_key

app = Flask(__name__)
app.secret_key = get_secret_key()

config = get_config('/home/gweinberg/projects/mdf0/etc/test.conf')
conn = get_sql_conn(config)

def get_user_id():
    user_id = session.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
        except Exception:
            user_id = None
    return user_id 


@app.route("/")
def hello():
    return "Hello, World!"

@app.route('/register', methods=['GET'])
def show_register_form():
    return render_template('register.html', action="register")

@app.route('/login', methods=['GET'])
def show_login_form():
    return render_template('login.html', action="login", message=None, username='')

@app.route('/login', methods=['POST'])
def process_login_form():
    username = request.form.get('username', '')
    user_id = check_password(conn, request.form['username'], request.form['password'])
    if user_id:
        session['user_id'] = user_id
        recursive_kill(conn, user_id)
        return redirect('/topics')
    else:
        return render_template('login.html', message='lolNope!', username=escape(username))

@app.route('/topics')
def show_topics():
    user_id = get_user_id()
    topic_stats = get_topic_stats(conn, user_id)
    return render_template('topics.html', user_id=user_id, topic_stats=topic_stats)

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    return 'Subpath %s' % escape(subpath)

