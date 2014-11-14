from datetime import datetime
from uuid import uuid1, UUID
import random
from time_utilities import _timestamp_to_uuid

from cassandra.cluster import Cluster

cluster = Cluster(['127.0.0.1'])
session = cluster.connect('linkssandra')


class DatabaseError(Exception):
    """
    The base error that functions in this module will raise when things go
    wrong.
    """
    pass


class NotFound(DatabaseError):
    pass


class InvalidDictionary(DatabaseError):
    pass


# Auth Module
def get_user_by_username(username):
    """
    Given a username, this gets the user credential.
    """
    rows = session.execute("SELECT * FROM users_cred WHERE username=%s", (username, ))
    if not rows:
        raise NotFound('User %s not found' % (username,))
    else:
        return rows[0]

def save_user(username, password):
    """
    Saves the user record.
    """
    session.execute(
        "INSERT INTO users_cred (username, password) VALUES (%s, %s)",
        (username, password))



#User Module

def get_user_info_by_username(username):
    """
    Given a username, this gets the user record.
    """
    rows = session.execute("SELECT * FROM users WHERE username=%s", (username, ))
    if not rows:
        raise NotFound('User %s not found' % (username,))
    else:
        return rows[0]

def get_user_exper_by_username(username):
    """
    Given a username, this gets the user record.
    """
    rows = session.execute("SELECT * FROM users_exper WHERE username=%s", (username, ))
    if not rows:
        return ''
    else:
        return rows

def get_user_educ_by_username(username):
    """
    Given a username, this gets the user record.
    """
    rows = session.execute("SELECT * FROM users_educ WHERE username=%s", (username, ))
    if not rows:
        return ''
    else:
        return rows


def save_user_info(username,firstname,lastname,email,photo):
    """
    Given a username, this gets the user record.
    """
    now = datetime.utcnow()
    session.execute("INSERT INTO users (username, firstname, lastname, email, created_date, total_profil_view,tags,photo ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", (username,firstname,lastname,email,now,0,{},photo))
    



# Timeline

def save_post(postid, username, post, timestamp=None):
    """
    Saves the post record.
    """

    # Insert the post
    session.execute(
        "INSERT INTO posts (postid , username, body, creation_ts) VALUES (%s, %s, %s, %s)",
        (postid, username, post, timestamp))

def get_posts():
     rows = session.execute("SELECT * FROM posts ")
     if not rows:
        return ''
     else:
        return rows


def inc_total_view(username):
        # update total view 
    row = session.execute("SELECT total_profil_view FROM users WHERE username=%s", (username, ))
    if not row[0].total_profil_view:
        session.execute("UPDATE users set total_profil_view=1 WHERE username=%s", (username,))
    else:
        session.execute("UPDATE users set total_profil_view=%s WHERE username=%s", (int(row[0].total_profil_view) + 1,username,))

   





#################################################
# Prepared statements, reuse as much as possible by binding new values
posts_query = None
userline_query = None
timeline_query = None
friends_query = None
followers_query = None
remove_friends_query = None
remove_followers_query = None
add_user_query = None
get_posts_query = None
get_usernames_query = None
get_followers_query = None
get_friends_query = None



PUBLIC_USERLINE_KEY = '!PUBLIC!'

def _get_line(table, username, start, limit):
    """
    Gets a timeline or a userline given a username, a start, and a limit.
    """
    global get_posts_query
    if get_posts_query is None:
        get_posts_query = session.prepare("""
            SELECT * FROM posts WHERE postid=?
            """)

    # First we need to get the raw timeline (in the form of post ids)
    query = "SELECT time, postid FROM {table} WHERE username=%s {time_clause} LIMIT %s"

    # See if we need to start our page at the beginning or further back
    if not start:
        time_clause = ''
        params = (username, limit)
    else:
        time_clause = 'AND time < %s'
        params = (username, UUID(start), limit)

    query = query.format(table=table, time_clause=time_clause)

    results = session.execute(query, params)
    if not results:
        return [], None

    # If we didn't get to the end, return a starting point for the next page
    if len(results) == limit:
        # Find the oldest ID
        oldest_timeuuid = min(row.time for row in results)

        # Present the string version of the oldest_timeuuid for the UI
        next_timeuuid = oldest_timeuuid.urn[len('urn:uuid:'):]
    else:
        next_timeuuid = None

    # Now we fetch the posts themselves
    futures = []
    for row in results:
        futures.append(session.execute_async(
            get_posts_query, (row.postid,)))

    posts = [f.result()[0] for f in futures]
    return (posts, next_timeuuid)


# QUERYING APIs


def get_friends(username, count=5000):
    """
    Given a username, gets the people that the user is following.
    """
    friend_usernames = get_friend_usernames(username, count=count)
    return get_users_for_usernames(friend_usernames)


def get_followers(username, count=5000):
    """
    Given a username, gets the people following that user.
    """
    follower_usernames = get_follower_usernames(username, count=count)
    return get_users_for_usernames(follower_usernames)


def get_timeline(username, start=None, limit=40):
    """
    Given a username, get their post timeline (posts from people they follow).
    """
    return _get_line("timeline", username, start, limit)


def get_userline(username, start=None, limit=40):
    """
    Given a username, get their userline (their posts).
    """
    return _get_line("userline", username, start, limit)


def get_post(postid):
    """
    Given a post id, this gets the entire post record.
    """
    global get_posts_query
    if get_posts_query is None:
        get_posts_query = session.prepare("""
            SELECT * FROM posts WHERE postid=?
            """)

    results = session.execute(get_posts_query, (postid, ))
    if not results:
        raise NotFound('post %s not found' % (postid,))
    else:
        return results[0]


def get_posts_for_postids(postids):
    """
    Given a list of post ids, this gets the associated post object for each
    one.
    """
    global get_posts_query
    if get_posts_query is None:
        get_posts_query = session.prepare("""
            SELECT * FROM posts WHERE postid=?
            """)

    futures = []
    for postid in postids:
        futures.append(session.execute_async(get_posts_query, (postid,)))

    posts = []
    for postid, future in zip(postid, futures):
        result = future.result()
        if not result:
            raise NotFound('post %s not found' % (postid,))
        else:
            posts.append(result[0])

    return posts




def _timestamp_to_uuid(time_arg):
    # TODO: once this is in the python Cassandra driver, use that
    microseconds = int(time_arg * 1e6)
    timestamp = int(microseconds * 10) + 0x01b21dd213814000L

    time_low = timestamp & 0xffffffffL
    time_mid = (timestamp >> 32L) & 0xffffL
    time_hi_version = (timestamp >> 48L) & 0x0fffL

    rand_bits = random.getrandbits(8 + 8 + 48)
    clock_seq_low = rand_bits & 0xffL
    clock_seq_hi_variant = 0b10000000 | (0b00111111 & ((rand_bits & 0xff00L) >> 8))
    node = (rand_bits & 0xffffffffffff0000L) >> 16
    return UUID(
        fields=(time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node),
        version=1)


def save_post(postid, username, post, timestamp=None):
    """
    Saves the post record.
    """

    global posts_query
    global userline_query
    global timeline_query

    # Prepare the statements required for adding the post into the various timelines
    # Initialise only once, and then re-use by binding new values
    if posts_query is None:
        posts_query = session.prepare("""
            INSERT INTO posts (postid, username, body,creation_ts)
            VALUES (?, ?, ?,?)
            """)

    if userline_query is None:
        userline_query = session.prepare("""
            INSERT INTO userline (username, time, postid)
            VALUES (?, ?, ?)
            """)

    if timeline_query is None:
        timeline_query = session.prepare("""
            INSERT INTO timeline (username, time, postid)
            VALUES (?, ?, ?)
            """)

    if timestamp is None:
        now = uuid1()
    else:
        now = _timestamp_to_uuid(timestamp)

    # Insert the post
    session.execute(posts_query, (postid, username, post,now,))
    # Insert post into the user's timeline
    session.execute(userline_query, (username, now, postid,))
    # Insert post into the public timeline
    session.execute(userline_query, (PUBLIC_USERLINE_KEY, now, postid,))

    # Get the user's followers, and insert the post into all of their streams
    futures = []
    follower_usernames = [username] + get_follower_usernames(username)
    for follower_username in follower_usernames:
        futures.append(session.execute_async(
            timeline_query, (follower_username, now, postid,)))

    for future in futures:
        future.result()

def get_follower_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people following that user.
    """
    global get_followers_query
    if get_followers_query is None:
        get_followers_query = session.prepare("""
            SELECT follower FROM followers WHERE username=? LIMIT ?
            """)

    rows = session.execute(get_followers_query, (username, count))
    return [row.follower for row in rows]


def get_friend_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people that the user is
    following.
    """
    global get_friends_query
    if get_friends_query is None:
        get_friends_query = session.prepare("""
            SELECT friend FROM friends WHERE username=? LIMIT ?
            """)

    rows = session.execute(get_friends_query, (username, count))
    return [row.friend for row in rows]




def add_friends(from_username, to_usernames):
    """
    Adds a friendship relationship from one user to some others.
    """
    now = datetime.utcnow()
    futures = []
    for to_user in to_usernames:
        futures.append(session.execute_async(
            "INSERT INTO friends (username, friend, since) VALUES (%s, %s, %s)",
            (from_username, to_user, now)))

        futures.append(session.execute_async(
            "INSERT INTO followers (username, follower, since) VALUES (%s, %s, %s)",
            (to_user, from_username, now)))

    for future in futures:
        future.result()
