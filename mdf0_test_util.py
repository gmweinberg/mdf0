"""Functions useful for manipulating test data from mdf0"""

from datetime import datetime, timedelta
import MySQLdb as mdb


def sync_seen(conn):
    """Mark all messages as seen by their authors. Mark all parents of seen messages as seen."""
    # This function is primarily useful for getting seen correct for test data.
    cur = conn.cursor()
    query = """INSERT IGNORE INTO Seen (user_id, message_id)
                WITH RECURSIVE  rseen as (
                   SELECT m.user_id, m.id, m.parent_id from Message m
               UNION
                   select  rseen.user_id, m.id, m.parent_id FROM rseen JOIN Message m on m.id = rseen.parent_id
               )
               SELECT user_id, id from rseen
            """
    cur.execute(query)
    conn.commit()

def diddle_message_times(conn):
    """Set the post times so our posts don;t all have the same time"""
    cur = conn.cursor()
    query = "SELECT id from Message order by 1"
    cur.execute(query)
    query = "UPDATE Message set created=%s where id=%s"
    ids = [row[0] for row in cur.fetchall()]
    now = datetime.today()
    then = now - len(ids) * timedelta(hours=1)
    for anid in ids:
         cur.execute(query, (then, anid))
         then += timedelta(hours=1)
    conn.commit()

def verify_all(conn):
    """Mark all users as verified."""
    cur = conn.cursor()
    query = "UPDATE User set verified=1"
    cur.execute(query)
    conn.commit() 
