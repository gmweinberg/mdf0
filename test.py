#!/usr/bin/python
import subprocess
import argparse

from mdf0_config import get_config
from mdf0_util import get_sql_conn, get_topic_stats, get_next_message_id, set_seen, topic_tree
from kill_util import recursive_kill
from mdf0_test_util import sync_seen, diddle_message_times, verify_all

verbose = False
config_file = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--config', help='config filename', default="./etc/test.conf")
    # params we may need for actions
    parser.add_argument('--user', help='user_id', type=int, default=None)
    parser.add_argument('--message', help='message_id', type=int, default=None)
    parser.add_argument('--topic', help='show tree list for topic', type=int, default=None)
    # actions
    parser.add_argument('--sync', help='sync_seen', action='store_true')
    parser.add_argument('--diddle', help='diddle message times', action='store_true')
    parser.add_argument('--stats', help='get topic stats', action='store_true')
    parser.add_argument('--next', help='get next message', action='store_true')
    parser.add_argument('--seen', help='set message seen by user', action='store_true')
    parser.add_argument('--restore', help='restore test database to initial state.', action='store_true')
    args = parser.parse_args()
    verbose = args.verbose
    sql_config = get_config(args.config)
    conn = get_sql_conn(sql_config)
    if args.restore:
        with open('./sql/schema.sql', 'r') as schema:
            subprocess.run(['mysql', '-h',  sql_config.host, '-u', sql_config.user, '-p{}'.format(sql_config.password), sql_config.database], stdin=schema)
        with open('./sql/test/sample1.sql', 'r') as sample_data:
            subprocess.run(['mysql', '-h',  sql_config.host, '-u', sql_config.user, '-p{}'.format(sql_config.password), sql_config.database], stdin=sample_data)
        args.diddle = True
        args.sync = True
        verify_all(conn)
        
    if args.stats:
        recursive_kill(conn, args.user)
        get_topic_stats(conn, args.user)
    if args.next:
        print(get_next_message_id(conn, args.user, args.message))
    if args.seen:
         set_seen(conn, user_id=args.user, message_id=args.message)
    if args.sync:
        sync_seen(conn)
    if args.diddle:
       diddle_message_times(conn)
    if args.topic:
       print(repr(topic_tree(conn, user_id=args.user, topic_id=args.topic)))

