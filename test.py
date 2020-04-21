#!/usr/bin/python
import argparse

from mdf0_util import get_config, get_sql_conn, get_topic_stats, recursive_kill
from mdf0_test_util import sync_seen, diddle_message_times

verbose = False
config_file = None



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--sync', help='sync_seen', action='store_true')
    parser.add_argument('--diddle', help='diddle message times', action='store_true')
    parser.add_argument('--config', help='config filename', default="./etc/test.conf")
    parser.add_argument('--user', help='user_id', type=int, default=None)
    args = parser.parse_args()
    verbose = args.verbose
    config = get_config(args.config)
    conn = get_sql_conn(config)
    if args.user:
        recursive_kill(conn, args.user)
        get_topic_stats(conn, args.user)
    if args.sync:
        sync_seen(conn)
    if args.diddle:
       diddle_message_times(conn)

