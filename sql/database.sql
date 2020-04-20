-- create database and db user. run as mysql root
create database if not exists mdf0;
USE mdf0;
CREATE user IF NOT EXISTS mdf0user identified by 'mdf0user';
CREATE user IF NOT EXISTS mdf0user@localhost identified by 'mdf0user';

GRANT ALL on mdf0.* to  mdf0user;
GRANT ALL on mdf0.* to  mdf0user;


