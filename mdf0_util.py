"""Utility functions for mdf0"""

import MySQLdb as mdb
from configparser import ConfigParser
import bcrypt

def get_config(config_filename):
    """Return a ConfigParser object from the filename."""
    config = ConfigParser()
    config.read(config_filename)
    return config

def get_topic_guest_stats(conn):
    """Get the name, total messages, and last message for each topic. Returns a dict."""
    # Ghosts are messages user has not seen and will never see due to kills.
    # unseen + ghosts + seen should equal total
    # name, total messages, last message. Last message might be killed
    cur = conn.cursor()
    result = {}
    query = """select t.id, t.title, max(m.created), count(m.id)
               FROM Topic t
               JOIN Message m on topic_id = t.id
               GROUP BY 1, 2
            """
    cur.execute(query)
    qr = cur.fetchall()
    for row in qr:
        result[row[0]] = {'title':row[1], 'last':row[2], 'total':row[3], 'unseen':0, 'seen':0, 'ghosts':0}
    return result


def get_topic_stats(conn, user_id):
    """Get the stats for each topic. Returns a dict
       topic_id: title, total, unseen, last, ghosts, seen"""
    result = get_topic_guest_stats(conn)
    if user_id is None:
        return result
    cur = conn.cursor()
    
    # unseen messages
    query = """SELECT t.id, count(m.id) FROM Topic t
               JOIN Message m on m.topic_id = t.id
               LEFT JOIN Seen s on s.user_id = {} and s.message_id = t.id
               LEFT JOIN Kill_{} km on km.message_id = m.id
               WHERE s.user_id IS NULL and km.message_id IS NULL
               GROUP BY 1""".format(user_id, user_id)
    cur.execute(query)
    qr = cur.fetchall()
    for row in qr:
        result[row[0]]['unseen'] = row[1]
    # seen messages
    query = """SELECT t.id, count(m.id) FROM Topic t
               JOIN Message m on m.topic_id = t.id
               JOIN Seen s on s.user_id = {} and s.message_id = t.id
               GROUP BY 1""".format(user_id)
    cur.execute(query)
    qr = cur.fetchall()
    for row in qr:
        result[row[0]]['seen'] = row[1]
    # ghosts
    query = """SELECT t.id, count(m.id) FROM Topic t
               JOIN Message m on m.topic_id = t.id
               LEFT JOIN Seen s on s.user_id = {} and s.message_id = t.id
               JOIN Kill_{} km on km.message_id = m.id
               WHERE s.user_id IS NULL
               GROUP BY 1""".format(user_id, user_id)
    cur.execute(query)
    qr = cur.fetchall()
    for row in qr:
        result[row[0]]['ghosts'] = row[1]

    print(result)
    return result

def get_message_info(conn, message_id):
    """Get the info we need to display this message. Returns a dict."""
    # for now it's just the message text and the parent_id
    cur = conn.cursor()
    query = """SELECT message, parent_id from Message where id=%s"""
    cur.execute(query, (message_id))
    row = cur.fetchone()
    if row:
        return {'message':row[0], 'parent_id':row[1]}
    

def get_first_unseen_message(conn, user_id, topic_id):
    """Get the first unseen unkilled message for this user topic."""
    cur = conn.cursor()
    query = """SELECT min(m.id) from Message m
               LEFT JOIN Kill_{} k on k.message_id = m.id
               LEFT JOIN Seen s on s.user_id = m.user_id
               WHERE m.user_id ={} AND k.message_id IS NULL AND s.message_id IS NULL""".format(user_id, user_id)
    cur.execute(query)
    row = cur.fetchone()
    if row:
        return row[0]
    

def get_next_message_id(conn, user_id, message_id, childless=None):
    """Get the next unseen unkilled message for this user."""
    if childless is None:
        childless = []
    cur = conn.cursor()
    children = []
    query = """SELECT m.id, s.user_id 
               FROM Message m 
               LEFT JOIN Kill_{} k on k.message_id = m.id 
               LEFT JOIN Seen s on s.user_id = m.user_id 
               WHERE k.message_id IS NULL and m.parent_id={} ORDER BY m.id""".format(user_id, message_id)
    cur.execute(query)
    for row in cur.fetchall():
        if row[1] is None: # haven't seen this one
            return row[0]
        if row[0] not in childless:
             children.append(row[0])
    if children:
        return get_next_message_id(conn, user_id, row[0], childless)
    childless.append(message_id)
    query = "SELECT parent_id from Message where id = %s"
    cur.execute(query, message_id)
    row = cur.fetchone()
    if row[0] is None:
        return None # no more unseen messages in this topic
    return get_next_message_id(conn, user_id, row[0], childless)


def recursive_kill(conn, user_id):
    """Create a table to store all killed messages for a user."""
    # We use a recursive sql query to find messages with killed parents or user kills
    cur = conn.cursor()
    query = 'DROP TABLE IF EXISTS Kill_{}'.format(user_id)
    cur.execute(query)
    query = 'CREATE TABLE Kill_{} (message_id int primary key not null)'.format(user_id)
    cur.execute(query)
    query = """INSERT IGNORE INTO Kill_{} (message_id)
               WITH RECURSIVE ukm as (
                      Select m.id FROM Message m join User_Kill uk on uk.user_id = {} and uk.target_id = m.user_id
                  UNION
                      select m.id from Message m join ukm on m.parent_id = ukm.id
               )
               SELECT id from ukm
             """.format(user_id, user_id)
    # print(query)
    cur.execute(query)
    query = """ INSERT IGNORE INTO Kill_{} (message_id)
                WITH RECURSIVE mkm as (
                   SELECT m1.id from Message m1 join Message_Kill mk on mk.user_id = {} and m1.id = mk.message_id
               UNION
                   select m1.id from Message m1 join mkm on m1.parent_id = mkm.id
               )
               SELECT id from mkm
            """.format(user_id, user_id)
    # print(query)
    cur.execute(query)
    conn.commit()
    

def get_sql_conn(config):
    """Get a sql connection."""
    conn = mdb.connect(host=config.get('sql', 'host'), user=config.get('sql', 'user'), password=config.get('sql', 'password'), database=config.get('sql', 'database'),
                       charset='utf8mb4', use_unicode=True)
    return conn


def kill_message(conn, user_id, message_id):
    """Mark a message as killed for a user."""
    cur = conn.cursor()
    query = "INSERT IGNORE INTO Message_Kill (user_id, message_id) values (%s, %s)"
    cur.execute(query, (user_id, message_id))
    conn.commit()

def kill_user(conn, user_id, target_id):
    """Mark a target as killed for a viewer user."""
    cur = conn.cursor()
    query = "INSERT IGNORE INTO User_Kill (user_id, target_id) values (%s, %s)"
    cur.execute(query, (user_id, target_id))
    conn.commit()

def set_seen(conn, user_id, message_id):
    """Mark a message as seen by some user."""
    cur = conn.cursor()
    query = "INSERT IGNORE INTO Seen (user_id, message_id) values (%s, %s)"
    cur.execute(query, (user_id, message_id))
    conn.commit()

def unkill_message(conn, user_id, message_id):
    """Remove the kill for a user message"""
    cur = conn.cursor()
    query = "DELETE * from  Message_Kill where user_id=%s and message_id=%s"
    cur.execute(query, (user_id, message_id))
    conn.commit()

def unkill_user(conn, user_id, target_id):
    """Remove the kill for a user target"""
    cur = conn.cursor()
    query = "DELETE * from  User_Kill where user_id=%s and target_id=%s"
    cur.execute(query, (user_id, target_id))
    conn.commit()


def check_password(conn, username, password):
    """Check if the supplied username and password are valid according to bcrypt. Returns user_id if username and password match, None otherwise"""
    cur = conn.cursor()
    query = "SELECT id, password FROM User where name = %s"
    cur.execute(query, (username,))
    row = cur.fetchone()
    if not row:
        return
    if bcrypt.checkpw(password.encode('utf8'), row[1].encode('utf8')):
        return row[0]

          
     
  


