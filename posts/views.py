import uuid

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from posts.forms import PostForm

import cass_link as cass


NUM_PER_PAGE = 40

def timeline(request):
    form = PostForm(request.POST or None)
    if request.user['is_authenticated'] and form.is_valid():
        postid = uuid.uuid4()
        cass.save_post(postid, request.session['username'], form.cleaned_data['body'])
        return HttpResponseRedirect(reverse('timeline'))
    start = request.GET.get('start')
    if request.user['is_authenticated']:
        posts, next_timeuuid = cass.get_timeline(
            request.session['username'], start=start, limit=NUM_PER_PAGE)
    else:
        posts, next_timeuuid = cass.get_userline(
            cass.PUBLIC_USERLINE_KEY, start=start, limit=NUM_PER_PAGE)
    context = {
        'form': form,
        'posts': posts,
        'next': next_timeuuid,
    }
    return render_to_response(
        'posts/timeline.html', context, context_instance=RequestContext(request))


def publicline(request):
    start = request.GET.get('start')
    posts, next_timeuuid = cass.get_userline(cass.PUBLIC_USERLINE_KEY, start=start, limit=NUM_PER_PAGE)
    context = {
        'posts': posts,
        'next': next_timeuuid,
    }
    return render_to_response(
        'posts/publicline.html', context, context_instance=RequestContext(request))


def userline(request, username=None):
    try:
        user = cass.get_user_by_username(username)
    except cass.DatabaseError:
        raise Http404

    # Query for the friend ids
    friend_usernames = []
    if request.user['is_authenticated']:
        friend_usernames = cass.get_friend_usernames(username) + [username]

    # Add a property on the user to indicate whether the currently logged-in
    # user is friends with the user
    is_friend = username in friend_usernames

    start = request.GET.get('start')
    posts, next_timeuuid = cass.get_userline(username, start=start, limit=NUM_PER_PAGE)
    context = {
        'user': user,
        'username': username,
        'posts': posts,
        'next': next_timeuuid,
        'is_friend': is_friend,
        'friend_usernames': friend_usernames,
    }
    return render_to_response(
        'posts/userline.html', context, context_instance=RequestContext(request))
