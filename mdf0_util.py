"""Utility functions for mdf0"""

import bcrypt
import MySQLdb as mdb
from mdf0_config import Mdf0SqlConfig


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
               LEFT JOIN Seen s on s.user_id = {} and s.message_id = m.id
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
               JOIN Seen s on s.user_id = {} and s.message_id = m.id
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

def get_message_info(conn, message_id, user_id):
    """Get the info we need to display this message. Returns a dict."""
    cur = conn.cursor()
    query = """SELECT message, parent_id, m.created, m.user_id, m.topic_id, u.name
               FROM Message m
               JOIN User u on u.id = m.user_id
               WHERE m.id=%s"""
    cur.execute(query, (message_id,))
    row = cur.fetchone()
    if not row:
        return
    result = {'message':row[0], 'parent_id':row[1], 'created':row[2], 'user_id':row[3], 'topic_id':row[4], 'user_name':row[4]}
    result['message_id'] = message_id
    result['next_id'] = get_next_message_id(conn, user_id, message_id)
    return result

def get_topic_id(conn, message_id):
    """Get the topic_id from the message_id."""
    cur = conn.cursor()
    query = "SELECT topic_id from Message where id = %s"
    cur.execute(query, (message_id,))
    row = cur.fetchone()
    if row:
        return row[0]
   

def get_first_unseen_message(conn, user_id, topic_id):
    """Get the first unseen unkilled message for this user topic."""
    cur = conn.cursor()
    query = """SELECT min(m.id) from Message m
               LEFT JOIN Kill_{} k on k.message_id = m.id
               LEFT JOIN Seen s on s.message_id = m.id and s.user_id={}
               WHERE m.topic_id ={} AND k.message_id IS NULL AND s.message_id IS NULL""".format(user_id, user_id, topic_id)
    cur.execute(query)
    row = cur.fetchone()
    if row:
        return row[0]
    

def get_next_message_id(conn, user_id, message_id, childless=None):
    """Get the next unseen unkilled message for this user."""
    if childless is None:
        childless = []
    print('get_next_message_id message_id {} childless {}'.format(message_id, childless))
    cur = conn.cursor()
        
    children = []
    query = """SELECT m.id, s.user_id 
               FROM Message m 
               LEFT JOIN Kill_{} k on k.message_id = m.id 
               LEFT JOIN Seen s on s.message_id = m.id AND s.user_id={} 
               WHERE k.message_id IS NULL and m.parent_id={} ORDER BY m.id""".format(user_id, user_id, message_id)
    cur.execute(query)
    for row in cur.fetchall():
        if row[1] is None: # haven't seen this one
            return row[0]
        if row[0] not in childless:
             children.append(row[0])
    if children:
        return get_next_message_id(conn, user_id, children[0], childless)
    childless.append(message_id)
    query = "SELECT parent_id from Message where id = %s"
    cur.execute(query, (message_id, ))
    row = cur.fetchone()
    if row[0] is None:
        return None # no more unseen messages in this topic
    return get_next_message_id(conn, user_id, row[0], childless)


def get_sql_conn(config):
    """Get a sql connection."""
    conn = mdb.connect(host=config.host, user=config.user, password=config.password, database=config.database,
                       charset='utf8mb4', use_unicode=True)
    return conn


def set_seen(conn, user_id, message_id):
    """Mark a message as seen by some user."""
    cur = conn.cursor()
    query = "INSERT IGNORE INTO Seen (user_id, message_id) values (%s, %s)"
    cur.execute(query, (user_id, message_id))
    conn.commit()


def add_reply(conn, user_id, parent_id, message):
    """Add a new reply to the supplied message"""
    topic_id = get_topic_id(conn, parent_id)
    if topic_id is None:
        raise Exception('No such message_id')
    cur = conn.cursor()
    query = "INSERT INTO Message (user_id, parent_id, topic_id, message) values (%s, %s, %s, %s)"
    cur.execute(query, (user_id, parent_id, topic_id, message))
    conn.commit()
    message_id = conn.insert_id()
    set_seen(conn, user_id, message_id)
    return message_id

def new_topic(conn, user_id, title, message):
    """Add a new topic with supplied subject. Returns the new topic_id"""
    cur = conn.cursor()
    query = "INSERT INTO Topic (title, user_id) VALUES (%s, %s)"
    cur.execute(query, (title, user_id))
    topic_id = conn.insert_id()
    query = "INSERT INTO Message (user_id, topic_id, message) values (%s, %s, %s)"
    cur.execute(query, (user_id, topic_id, message))
    message_id = conn.insert_id()
    query = "UPDATE Topic set base_message_id=%s WHERE id=%s"
    cur.execute(query, (message_id, topic_id))
    conn.commit()
    set_seen(conn, user_id, message_id)
    return topic_id

def topic_tree(conn, topic_id, user_id):
    """Return a list of all messages in the topic as a list of dicts in view order for the user"""
    cur = conn.cursor(mdb.cursors.DictCursor)
    query = """SELECT m.id AS message_id, m.created As created, m.user_id AS user_id, m.parent_id AS parent_id, m.message AS message, 
               u.name AS user_name, mk.message_id AS message_kill, uk.user_id AS user_kill, s.message_id AS seen
               FROM Message m
               JOIN User u on u.id = m.user_id
               LEFT JOIN Message_Kill mk on mk.user_id=%s and mk.message_id = m.id
               LEFT JOIN User_Kill uk on uk.user_id=%s AND uk.target_id = m.id
               LEFT JOIN Seen s on s.user_id=%s AND s.message_id = m.id
               WHERE m.topic_id=%s
               ORDER BY m.id"""
    cur.execute(query, (user_id, user_id, user_id, topic_id))
    topic_dict = {}
    qr = cur.fetchall()
    for row in qr:
        if row['parent_id'] is None:
            root = row['message_id']
        topic_dict[row['message_id']] = dict(row)
        topic_dict[row['message_id']]['children'] = []
        topic_dict[row['message_id']]['user_kill'] = bool(row['user_kill'])
        topic_dict[row['message_id']]['message_kill'] = bool(row['message_kill'])
        topic_dict[row['message_id']]['seen'] = bool(row['seen'])
        if row['parent_id'] in topic_dict: # should be true execpt root message of topic
             topic_dict[row['parent_id']]['children'].append(row['message_id'])
        topic_dict[row['message_id']]['indent'] = 0

    nodes = []
    indent = 0
    _transverse_tree(topic_dict, root, indent, nodes)
    print(repr(nodes))
    return nodes
    

def _transverse_tree(thedict, pos, indent, nodes):
    """Helper function called recursively to get the nodes in display order from thedict. Updates nodes in place, returns None."""
    thedict[pos]['indent'] = indent
    nodes.append(thedict[pos])
    indent += 1
    for node in thedict[pos]['children']:
         _transverse_tree(thedict, node, indent, nodes)
        
      

    
    

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

     
  


