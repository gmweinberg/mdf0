"""Functions for creating, modifying, merging, and delting users."""

from dataclasses import dataclass
import MySQLdb as mdb
from uuid import uuid4
import bcrypt
from kill_util import recursive_kill

@dataclass
class Mdf0User:
    user_id: int
    name: str
    temp: bool
    can_post: bool


def get_user_info(conn, user_id):
    """Get an MDF0User object containing the info corresponding to this user_id."""
    cur = conn.cursor(mdb.cursors.DictCursor)
    query = "SELECT name, temp, verified FROM User where id = %s"
    cur.execute(query, (user_id,))
    row = cur.fetchone()
    return Mdf0User(user_id=user_id, name=row['name'], temp=bool(row['temp']), can_post=bool(row['verified']))

def create_temp_user(conn):
    """Create a temporary guest user. The temp user can view and mark things as read and can kill but cannot post (or log in)
        Returns the Mdf0User."""
    user_name = uuid4()
    cur = conn.cursor()
    query = "INSERT INTO User (name, password, temp, verified, created, last_access) values (%s, 'LOL', 1, 0, NOW(), NOW())"
    cur.execute(query, (user_name,))
    user_id = conn.insert_id()
    conn.commit()
    return get_user_info(conn, user_id)

def register(conn, name, password, email, old_user_id=None):
    """Create a new user. Merge in the old user if he exists. Returns an MDF0User object."""
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    query = "INSERT INTO User (name, password, email, temp, verified, created, last_access) values (%s, %s, %s, 0, 1, NOW(), NOW())"
    cur.execute(query, (name, hashed, email))
    user_id = conn.insert_id()
    conn.commit()
    if old_user_id:
        merge_user(conn, old_user_id, user_id)
        delete_user(conn, old_user_id)
    recursive_kill(conn, user_id=user_id)
    return get_user_info(conn, user_id)

def login(conn, name, password, old_user_id=None):
    """Attempt to log in a user using a name and password. If it fails return false. If it succeeds, return an Mdf0User.
       Merge in a temporary user_id if present."""
    user_id = check_password(conn, name, password)
    if not user_id:
        return False
    if old_user_id:
        merge_user(conn, old_user_id=old_user_id, new_user_id = user_id)
        delete_user(conn, old_user_id)
    recursive_kill(conn, user_id=user_id)
    return get_user_info(conn, user_id)



def merge_user(conn, old_user_id, new_user_id):
    """Merge an old_user_id into a new_user_id"""
    # We only do this for temp users, who will not have messages
    cur = conn.cursor()
    query = "INSERT IGNORE INTO User_Kill (user_id, target_id, created) SELECT %s, target_id, created from User_Kill where user_id=%s"
    cur.execute(query, (new_user_id, old_user_id))        
    query = "INSERT IGNORE INTO Message_Kill (user_id, message_id, created) SELECT %s, message_id, created from Message_Kill where user_id=%s"
    cur.execute(query, (new_user_id, old_user_id))     
    query = "INSERT IGNORE INTO Seen (user_id, message_id, created) SELECT %s, message_id, created from Seen where message_id=%s"
    cur.execute(query, (new_user_id, old_user_id))
    conn.commit()      

def delete_user(conn, user_id):
    """Remove a user from all tables"""
    # we only do this for temp/unregistered users, who will not have messages.
    cur = conn.cursor()
    query = "DELETE from User where id = %s"
    cur.execute(query, (user_id,))    
    query = "DELETE from User_Kill where user_id = %s"
    cur.execute(query, (user_id,))    
    query = "DELETE from Message_Kill where user_id = %s"
    cur.execute(query, (user_id,))    
    query = "DELETE from Seen where user_id = %s"
    cur.execute(query, (user_id,))
    query = "DROP TABLE IF EXISTS Kill_{}".format(user_id)
    cur.execute(query)
    conn.commit()

def update_access(conn, user_id):
    cur = conn.cursor()
    query = "UPDATE User set last_access = NOW() WHERE user_id=%s"
    cur.execute(query, (user_id,))
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

