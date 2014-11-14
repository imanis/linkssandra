import uuid

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from user.forms import WelcomForm

import cass_link as cass


def welcome(request):
    if request.method == 'POST':
        form = WelcomForm(request.POST)
        if request.user['is_authenticated'] and form.is_valid():
        	cass.save_user_info(request.session['username'], form.cleaned_data['firstname'],form.cleaned_data['lastname'],form.cleaned_data['email'])
		return HttpResponseRedirect('/timeline/')

    form = WelcomForm()
    context = {
        'form': form
    }
    return render_to_response(
        'user/welcome.html', context, context_instance=RequestContext(request))

def profile(request):
	if request.user['is_authenticated']:
		data = cass.get_user_info_by_username(request.session['username'])
		context = {
			'userdata': data,
			'username': request.session['username']
		    }
		return render_to_response(
			'user/profile.html', context, context_instance=RequestContext(request))
	return HttpResponseRedirect('/auth/login')

def userprofile(request, username):
	data = cass.get_user_info_by_username(username)
	if data:
		context = {
			'userdata': data,
			'username': username
		    }
		return render_to_response(
			'user/profile.html', context, context_instance=RequestContext(request))
	raise Http404

