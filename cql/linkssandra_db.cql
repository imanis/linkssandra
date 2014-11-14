

CREATE KEYSPACE linkssandra_v2 WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };

use linkssandra_v2;

//-----------------------Profil

CREATE TABLE users_cred (
   username varchar,
   password varchar,
   PRIMARY KEY (username)
);

// Basic entity table
CREATE TABLE users (
   username varchar,
   firstname varchar,
   lastname varchar,
   email varchar,
   created_date timestamp,
   total_profil_view int,
   tags map<varchar,int>,
   PRIMARY KEY (username)
);

//Experiences
CREATE TABLE users_exper (
   username varchar,
   exper_id uuid,
   company_id uuid,
   company_name varchar,
   exper_titel varchar;
   start_time timestamp,
   end_time timestamp,
   description text,
   PRIMARY KEY (username)
);

//Education & training 
CREATE TABLE users_educ (
   username varchar,
   educ_id uuid,
   school_id uuid,
   school_name varchar,
   degree varchar,
   field varchar,
   start_time timestamp,
   end_time timestamp,
   description text,
   PRIMARY KEY (username)
);


//------------------------------ tags

// Creating index tables for user tag keywords
CREATE TABLE tag_index (
   tag varchar, 
   username uuid,
   timestamp timestamp,
   PRIMARY KEY (tag, username )
);



//-------------------------Posts & Comments

// One-to-many entity table
CREATE TABLE posts(
   postid uuid,
   username varchar,
   body varchar, 
   creation_ts timeuuid,
   PRIMARY KEY (postid,creation_ts)
) WITH CLUSTERING ORDER BY (creation_ts DESC);

// Comments as a one-to-many 
CREATE TABLE comments (
   postid  uuid,
   username varchar,
   comment_ts timestamp,
   comment varchar,
   PRIMARY KEY (postid ,comment_ts,username)
) WITH CLUSTERING ORDER BY (comment_ts DESC, username ASC);


CREATE TABLE userline (
    username text,
    time timeuuid,
    postid uuid,
    PRIMARY KEY (username, time)
) WITH CLUSTERING ORDER BY (time DESC);

CREATE TABLE timeline (
    username text,
    time timeuuid,
    postid uuid,
    PRIMARY KEY (username, time)
) WITH CLUSTERING ORDER BY (time DESC);




//--------------------------- Friendship

CREATE TABLE followers (
    username varchar,
    follower varchar,
    since timestamp,
    PRIMARY KEY (username, follower)
);

CREATE TABLE friends (
    username varchar,
    friend varchar,
    since timestamp,
    PRIMARY KEY (username, friend)
);


//-----------------------------Companies

CREATE TABLE companies(
   companyname varchar,
   baselocation varchar,
   website varchar,
   size int,
   created_date timestamp,
   total_company_view int,
   PRIMARY KEY companyname 
);

// One-to-many entity table
CREATE TABLE jobs(
   jobid uuid,
   companyname varchar,
   title varchar
   body text,
   creation_ts timeuuid,
   tags map<varchar,int>,
   PRIMARY KEY (jobid ,creation_ts)
) WITH CLUSTERING ORDER BY (creation_ts DESC);



