DROP TABLE IF EXISTS `User`;
CREATE TABLE `User` (
    id int not null primary key auto_increment,
    name varchar(255) not null,
    password varchar(255) not null,
    email varchar(255) NULL,
    temp tinyint NOT NULL default 0,
    verified tinyint NOT NULL default 0,
    created timestamp not null default CURRENT_TIMESTAMP,
    last_access timestamp NOT NULL);

CREATE UNIQUE INDEX user_email on User (email);
 
DROP TABLE IF EXISTS `Topic`;
CREATE TABLE `Topic` (
    id int not null primary key auto_increment,
    title varchar(255) NOT NULL,
    user_id int not null, -- this probably isn't necessary
    base_message_id int NULL,
    created timestamp not null default CURRENT_TIMESTAMP);

DROP TABLE IF EXISTS `Message`;
CREATE TABLE `Message` (
    id int not null primary key auto_increment,
    created timestamp not null default CURRENT_TIMESTAMP,
    user_id int not null,
    parent_id int NULL,
    topic_id int NULL,
    message text NOT NULL);

-- index everything here!
CREATE INDEX message_user on Message (user_id);
CREATE INDEX message_parent on Message (parent_id);
CREATE INDEX message_topic on Message (topic_id);

DROP TABLE IF EXISTS `Seen`;
CREATE TABLE `Seen` (
    user_id int not null,
    message_id int not null,
    created timestamp not null default CURRENT_TIMESTAMP,
    primary key (user_id, message_id)
    );

DROP TABLE IF EXISTS User_Kill;
CREATE TABLE User_Kill (
    user_id int not null,
    target_id int not null,
    created timestamp not null default CURRENT_TIMESTAMP,
    primary key (user_id, target_id)
    );

DROP TABLE IF EXISTS Message_Kill;
CREATE TABLE Message_Kill (
    user_id int not null,
    message_id int not null,
    created timestamp not null default CURRENT_TIMESTAMP,
    primary key (user_id, message_id)
    );

DROP TABLE IF EXISTS Upvote;
CREATE TABLE Upvote (
    user_id int not null,
    message_id int not null,
    created timestamp not null default CURRENT_TIMESTAMP,
    primary key (user_id, message_id)
    );

