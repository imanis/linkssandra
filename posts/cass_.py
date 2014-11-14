
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
            SELECT * FROM posts WHERE post_id=?
            """)

    # First we need to get the raw timeline (in the form of post ids)
    query = "SELECT time, post_id FROM {table} WHERE username=%s {time_clause} LIMIT %s"

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
            get_posts_query, (row.post_id,)))

    posts = [f.result()[0] for f in futures]
    return (posts, next_timeuuid)


# QUERYING APIs


def get_user_by_username(username):
    """
    Given a username, this gets the user record.
    """
    global get_usernames_query
    if get_usernames_query is None:
        get_usernames_query = session.prepare("""
            SELECT * FROM users WHERE username=?
            """)

    rows = session.execute(get_usernames_query, (username,))
    if not rows:
        raise NotFound('User %s not found' % (username,))
    else:
        return rows[0]

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


def get_post(post_id):
    """
    Given a post id, this gets the entire post record.
    """
    global get_posts_query
    if get_posts_query is None:
        get_posts_query = session.prepare("""
            SELECT * FROM posts WHERE post_id=?
            """)

    results = session.execute(get_posts_query, (post_id, ))
    if not results:
        raise NotFound('post %s not found' % (post_id,))
    else:
        return results[0]


def get_posts_for_post_ids(post_ids):
    """
    Given a list of post ids, this gets the associated post object for each
    one.
    """
    global get_posts_query
    if get_posts_query is None:
        get_posts_query = session.prepare("""
            SELECT * FROM posts WHERE post_id=?
            """)

    futures = []
    for post_id in post_ids:
        futures.append(session.execute_async(get_posts_query, (post_id,)))

    posts = []
    for post_id, future in zip(post_id, futures):
        result = future.result()
        if not result:
            raise NotFound('post %s not found' % (post_id,))
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


def save_post(post_id, username, post, timestamp=None):
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
            INSERT INTO posts (post_id, username, body)
            VALUES (?, ?, ?)
            """)

    if userline_query is None:
        userline_query = session.prepare("""
            INSERT INTO userline (username, time, post_id)
            VALUES (?, ?, ?)
            """)

    if timeline_query is None:
        timeline_query = session.prepare("""
            INSERT INTO timeline (username, time, post_id)
            VALUES (?, ?, ?)
            """)

    if timestamp is None:
        now = uuid1()
    else:
        now = _timestamp_to_uuid(timestamp)

    # Insert the post
    session.execute(posts_query, (post_id, username, post,))
    # Insert post into the user's timeline
    session.execute(userline_query, (username, now, post_id,))
    # Insert post into the public timeline
    session.execute(userline_query, (PUBLIC_USERLINE_KEY, now, post_id,))

    # Get the user's followers, and insert the post into all of their streams
    futures = []
    follower_usernames = [username] + get_follower_usernames(username)
    for follower_username in follower_usernames:
        futures.append(session.execute_async(
            timeline_query, (follower_username, now, post_id,)))

    for future in futures:
        future.result()



