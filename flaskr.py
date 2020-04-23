import os
import logging

from flask import Flask, request, session, render_template, redirect
from markupsafe import escape
from mdf0_util import (get_config, get_sql_conn, check_password, get_topic_stats, get_topic_id, get_message_info, get_next_message_id, get_first_unseen_message, 
                      new_topic, add_reply, set_seen)
from kill_util import recursive_kill, kill_message, kill_user, unkill_message, unkill_user
from secret import get_secret_key

app = Flask(__name__)
app.secret_key = get_secret_key()

config = get_config('/home/gweinberg/projects/mdf0/etc/test.conf')
#logging.basicConfig(format='%(asctime)s %(message)s')
#logging.basicConfig(filename=config.get('logging', 'file'), level=logging.INFO)
conn = get_sql_conn(config)

def get_user_id():
    user_id = session.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
        except Exception:
            user_id = None
    return user_id 

def show_next(conn, user_id, message_id):
    """Show the next message if there is one."""
    next_id = get_next_message_id(conn, user_id, message_id)
    if next_id is None:
        topic_id = get_topic_id(conn, message_id)
        return redirect('/nothing/{}'.format(topic_id))
    return redirect('/message/{}'.format(next_id))

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
    user_id = get_user_id()
    message_info = get_message_info(conn, user_id=user_id, message_id=message_id)
    if not message_info:
        return redirect('/oops')
    set_seen(conn, user_id, message_id)
    return render_template('message.html', message_info=message_info)

@app.route('/oops')
def show_oops():
    """Display an error page."""
    return render_template('oops.html')


@app.route('/killmessage/<int:message_id>')
def killmessage(message_id):
    """Mark a message as killed, then display the next message."""
    user_id = get_user_id()
    kill_message(conn, user_id=user_id, message_id=message_id)
    recursive_kill(conn, user_id)
    return show_next(conn, user_id, message_id)

@app.route('/killuser')
def killuser():
    """Mark a user as killed, then display the next message."""
    user_id = get_user_id()
    message_id = request.args.get('message')
    target_id = request.args.get('user')
    try:
         message_id = int(message_id)
         target_id = int(target_id)
    except Exception:
        return redirect('/oops')

    kill_user(conn, user_id, target_id)
    recursive_kill(conn, user_id)
    return show_next(conn, user_id, message_id)

@app.route('/reply', methods=['POST'])
def reply():
    """Reply to a message"""
    user_id = get_user_id()
    message = request.form.get('message') # new message text
    message_id = request.form.get('message_id')
    try:
        message_id = int(message_id)
    except Exception:
        message_id = None
    if message_id is None or not message:
        return redirect('/oops')
    add_reply(conn, user_id, message_id, message)
    return show_next(conn, user_id, message_id)

@app.route('/newtopic', methods=['GET'])
def new_topic_form():
    """Show a form allowing a user to enter a new topic"""
    return render_template('newtopic.html')


@app.route('/newtopic', methods=['POST'])
def process_new_topic():
    """Process a new topic form."""
    user_id = get_user_id()
    message = request.form.get('message') # new message text
    title = request.form.get('title')
    if not message or not title:
        return redirect('/oops')
    new_topic(conn, user_id, title, message)
    return redirect('/topics')        

    

    
