""" Kill and unkill functions"""
import MySQLdb as mdb

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
    
def kill_message(conn, user_id, message_id):
    """Mark a message as killed for a user."""
    cur = conn.cursor()
    query = "INSERT IGNORE INTO Message_Kill (user_id, message_id) values (%s, %s)"
    cur.execute(query, (user_id, message_id))
    conn.commit()

def kill_user(conn, user_id, target_id):
    """Mark a target as killed for a viewer user. User_id is who is doing the killing, target_id is who is being killed"""
    cur = conn.cursor()
    query = "INSERT IGNORE INTO User_Kill (user_id, target_id) values (%s, %s)"
    cur.execute(query, (user_id, target_id))
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


