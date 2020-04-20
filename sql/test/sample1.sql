-- wipe out all exising data. Make sure to use the test database before executing :-)
-- run this as the mysql test user.

-- mysql -u mdf0_testuser -pmdf0user mdf0_test < sample1.sql

TRUNCATE TABLE User;
TRUNCATE TABLE Topic;
TRUNCATE TABLE Message;
TRUNCATE TABLE Seen;
TRUNCATE TABLE User_Kill;
TRUNCATE TABLE Message_Kill;

INSERT INTO User (id, name, password) VALUES (1000, 'Particle Man', '$2b$12$i1sdmT5oq74yWY5Q3txOeOy72.DPZXlmFG6hOzfBWCVGvnjMx2Rm2'); -- testuser
INSERT INTO User (id, name, password) VALUES (1001, 'Triangle Man', '$2b$12$i1sdmT5oq74yWY5Q3txOeOy72.DPZXlmFG6hOzfBWCVGvnjMx2Rm2'); -- testuser
INSERT INTO User (id, name, password) VALUES (1002, 'Person Person', '$2b$12$i1sdmT5oq74yWY5Q3txOeOy72.DPZXlmFG6hOzfBWCVGvnjMx2Rm2'); -- testuser
INSERT INTO User (id, name, password) VALUES (1003, 'Simplicius', '$2b$12$i1sdmT5oq74yWY5Q3txOeOy72.DPZXlmFG6hOzfBWCVGvnjMx2Rm2'); -- testuser
INSERT INTO User (id, name, password) VALUES (1004, 'Cornholio', '$2b$12$i1sdmT5oq74yWY5Q3txOeOy72.DPZXlmFG6hOzfBWCVGvnjMx2Rm2'); -- testuser
INSERT INTO User (id, name, password) VALUES (1005, 'Mrs. Wright', '$2b$12$i1sdmT5oq74yWY5Q3txOeOy72.DPZXlmFG6hOzfBWCVGvnjMx2Rm2'); -- testuser
INSERT INTO User (id, name, password) VALUES (1006, 'Mr. Rection', '$2b$12$i1sdmT5oq74yWY5Q3txOeOy72.DPZXlmFG6hOzfBWCVGvnjMx2Rm2'); -- testuser

Insert into Topic (id, title, user_id) VALUES (1001, 'Start Here', 1006);
Insert into Topic (id, title, user_id) VALUES (1002, 'Experience is Garbage', 1002);
-- Insert into Topic (id, title, user_id) VALUES (1003, 'Is Skepicism of any value?', 1006);
-- Insert into Topic (id, title, user_id) VALUES (1004, 'Us and Them: Elimnating Them', 1001);
-- Insert into Topic (id, title, user_id) VALUES (1005, 'Us and Them: Choosing the New Them', 1001);

Insert Into User_Kill (user_id, target_id) VALUES (1000, 1001);
Insert Into User_Kill (user_id, target_id) VALUES (1001, 1000);
Insert Into User_Kill (user_id, target_id) VALUES (1001, 1002);

INSERT INTO Message (id, user_id, parent_id, topic_id, message) values 
(1001, 1005, null, 1001, 'This is the first message in the sample topic.'),
(1002, 1006, 1001, 1001, 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),
(1003, 1004, 1002, 1001, "No it doesn't"),
(1004, 1002, 1001, 1001, "The first shall be last."),
(1005, 1000, 1004, 1001, "where does that leave the ones in the middle?"),
(1006, 1005, 1005, 1001, "At the bottom.");

INSERT INTO Message (id, user_id, parent_id, topic_id, message) values 
(2000, 1002, null, 1002, "Our experiences give us no fundamental insight into the nature of reality, because we cannot distinguish between abuse we have actually experienced vs. abuse we believe we have experienced because we are so brain-damaged."),
(2001, 1000, 2000, 1002,  "Some of us are more brain-damaged than others. The less brain-damaged among us generally have no trouble distinguishing between reality and hallucinations. When I'm trippping balls, I know I'm tripping balls."),
(2002, 1002, 2001, 1002, "Saying it doesn't make it so. Even if we grant that sometimes when you are hallucinating you are aware of it, you can't be sure that other times when you believe you are actually experiencing things, in fact you are merely imagining them."),
(2003, 1006, 2001, 1002, "I think that is only partially true. Introspection can be a guide to how much confidence we should feel in our sensory impressions. But certainty only goes on way: we can know we're out of our gords, but we can never be quite sure we are in them.");

INSERT INTO Message_Kill (user_id, message_id) VALUES (1004, 1004);






