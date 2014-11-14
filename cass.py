from datetime import datetime
from uuid import uuid1, UUID
import random

from cassandra.cluster import Cluster

cluster = Cluster(['127.0.0.1'])
session = cluster.connect('twissandra')

# NOTE: Having a single userline key to store all of the public tweets is not
#       scalable.  This result in all public tweets being stored in a single
#       partition, which means they must all fit on a single node.
#
#       One fix for this is to partition the timeline by time, so we could use
#       a key like !PUBLIC!2010-04-01 to partition it per day.  We could drill
#       down even further into hourly keys, etc.  Since this is a demonstration
#       and that would add quite a bit of extra code, this excercise is left to
#       the reader.
PUBLIC_USERLINE_KEY = '!PUBLIC!'


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


def _get_line(table, username, start, limit):
    """
    Gets a timeline or a userline given a username, a start, and a limit.
    """
    # First we need to get the raw timeline (in the form of tweet ids)
    query = "SELECT time, tweet_id FROM {table} WHERE username=%s {time_clause} LIMIT %s"

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

    # Now we fetch the tweets themselves
    futures = []
    for row in results:
        futures.append(session.execute_async(
            "SELECT * FROM tweets WHERE tweet_id=%s", (row.tweet_id, )))

    tweets = [f.result()[0] for f in futures]
    return (tweets, next_timeuuid)


# QUERYING APIs

def get_user_by_username(username):
    """
    Given a username, this gets the user record.
    """
    rows = session.execute("SELECT * FROM users WHERE username=%s", (username, ))
    if not rows:
        raise NotFound('User %s not found' % (username,))
    else:
        return rows[0]


def get_friend_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people that the user is
    following.
    """
    rows = session.execute(
        "SELECT friend FROM friends WHERE username=%s LIMIT %s",
        (username, count))
    return [row.friend for row in rows]


def get_follower_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people following that user.
    """
    rows = session.execute(
        "SELECT follower FROM followers WHERE username=%s LIMIT %s",
        (username, count))
    return [row.follower for row in rows]


def get_users_for_usernames(usernames):
    """
    Given a list of usernames, this gets the associated user object for each
    one.
    """
    futures = []
    for user in usernames:
        future = session.execute_async("SELECT * FROM users WHERE username=%s", (user, ))
        futures.append(future)

    users = []
    for user, future in zip(usernames, futures):
        results = future.result()
        if not results:
            raise NotFound('User %s not found' % (user,))
        users.append(results[0])

    return users


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
    Given a username, get their tweet timeline (tweets from people they follow).
    """
    return _get_line("timeline", username, start, limit)


def get_userline(username, start=None, limit=40):
    """
    Given a username, get their userline (their tweets).
    """
    return _get_line("userline", username, start, limit)


def get_tweet(tweet_id):
    """
    Given a tweet id, this gets the entire tweet record.
    """
    results = session.execute("SELECT * FROM tweets WHERE tweet_id=%s", (tweet_id, ))
    if not results:
        raise NotFound('Tweet %s not found' % (tweet_id,))
    else:
        return results[0]


def get_tweets_for_tweet_ids(tweet_ids):
    """
    Given a list of tweet ids, this gets the associated tweet object for each
    one.
    """
    futures = []
    for tweet_id in tweet_ids:
        futures.append(session.execute_async(
            "SELECT * FROM tweets WHERE tweet_id=%s", (tweet_id, )))

    tweets = []
    for tweet_id, future in zip(tweet_id, futures):
        result = future.result()
        if not result:
            raise NotFound('Tweet %s not found' % (tweet_id,))
        else:
            tweets.append(result[0])

    return tweets


# INSERTING APIs

def save_user(username, password):
    """
    Saves the user record.
    """
    session.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, password))




def save_tweet(tweet_id, username, tweet, timestamp=None):
    """
    Saves the tweet record.
    """
    if timestamp is None:
        now = uuid1()
    else:
        now = _timestamp_to_uuid(timestamp)

    # Insert the tweet, then into the user's timeline, then into the public one
    session.execute(
        "INSERT INTO tweets (tweet_id, username, body) VALUES (%s, %s, %s)",
        (tweet_id, username, tweet))

    session.execute(
        "INSERT INTO userline (username, time, tweet_id) VALUES (%s, %s, %s)",
        (username, now, tweet_id))

    session.execute(
        "INSERT INTO userline (username, time, tweet_id) VALUES (%s, %s, %s)",
        (PUBLIC_USERLINE_KEY, now, tweet_id))

    # Get the user's followers, and insert the tweet into all of their streams
    futures = []
    follower_usernames = [username] + get_follower_usernames(username)
    for follower_username in follower_usernames:
        futures.append(session.execute_async(
            "INSERT INTO timeline (username, time, tweet_id) VALUES (%s, %s, %s)",
            (follower_username, now, tweet_id)))

    for future in futures:
        future.result()


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


def remove_friends(from_username, to_usernames):
    """
    Removes a friendship relationship from one user to some others.
    """
    futures = []
    for to_user in to_usernames:
        futures.append(session.execute_async(
            "DELETE FROM friends WHERE username=%s AND friend=%s",
            (from_username, to_user)))

        futures.append(session.execute_async(
            "DELETE FROM followers WHERE username=%s AND follower=%s",
            (to_user, from_username)))

    for future in futures:
        future.result()
