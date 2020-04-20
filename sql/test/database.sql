-- create test database. run as mysql root
create database if not exists mdf0_test;
use mdf0_test;
create user IF NOT EXISTS mdf0_testuser identified by 'mdf0user';
create user IF NOT EXISTS mdf0_testuser@localhost identified by 'mdf0user';

GRANT ALL on mdf0_test.* to  mdf0_testuser;
GRANT ALL on mdf0_test.* to  mdf0_testuser@localhost;




