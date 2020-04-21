import os

from flask import Flask, request, session, render_template, redirect
from markupsafe import escape
from mdf0_util import (get_config, get_sql_conn, check_password, get_topic_stats, recursive_kill, get_message_info, get_first_unseen_message)
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

@app.route('/topic/<int:topic_id>')
def show_first_message(topic_id):
    user_id = get_user_id()
    message_id = get_first_unseen_message(conn, user_id, topic_id)
    if message_id is None:
        return redirect('/nothing/{}'.format(topic_id))
    return redirect('/message/{}'.format(message_id))

@app.route('/nothing/<int:topic_id>')
def show_nothing(topic_id):
    """Display no more messages for this topic."""
    return render_template('nothing.html')

@app.route('/message/<int:message_id>')
def show_message(message_id):
    message_info = get_message_info(conn, message_id=message_id)
    if not message_info:
        return redirect('/oops') 
    message = message_info['message']
    parent_id = message_info.get('parent_id')
    return render_template('message.html', message=message, parent_id=parent_id)

@app.route('/oops')
def show_oops():
    """Display an error page."""
    return render_template('oops.html')

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    return 'Subpath %s' % escape(subpath)

