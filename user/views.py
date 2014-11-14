import uuid

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from user.forms import WelcomForm
from user.models import Document


from fileutilities import handle_uploaded_file
import uuid

import cass_link as cass
#import pdb
#pdb.set_trace()

def welcome(request):
    if request.method == 'POST':
        form = WelcomForm(request.POST, request.FILES)
        if request.user['is_authenticated']:
			if form.is_valid():
				picpath = 'media/DATA/'+request.session['username']+'/photo/'+str(uuid.uuid4())
				handle_uploaded_file(request.FILES['photo'],picpath)
				cass.save_user_info(request.session['username'], form.cleaned_data['firstname'],form.cleaned_data['lastname'],form.cleaned_data['email'],picpath)
				return HttpResponseRedirect('/timeline/')
	return HttpResponseRedirect('/auth/login')
    form = WelcomForm()
    context = {
        'form': form
    }
    return render_to_response(
        'user/welcome.html', context, context_instance=RequestContext(request))

def profile(request):
	if request.user['is_authenticated']:
		username = request.session['username']
		try:
			data = cass.get_user_info_by_username(username)
			exper = cass.get_user_exper_by_username(username)
			context = {
				'userdata': data,
				'userexper': exper,						
				'username': username
			    }
			return render_to_response(
				'user/editprofile.html', context, context_instance=RequestContext(request))
		except:
			HttpResponseRedirect('/user/welcome')
	return HttpResponseRedirect('/auth/login')

def userprofile(request, username):
	cass.inc_total_view(username)
	data = cass.get_user_info_by_username(username)
	exper = cass.get_user_exper_by_username(username)
	if data:
		context = {
			'userdata': data,
			'userexper': exper,						
			'username': username
		    }
		return render_to_response(
			'user/profile.html', context, context_instance=RequestContext(request))
	raise Http404

def addfriend(request, friend):
	if request.user['is_authenticated']:
		if friend :
			cass.add_friends(
                request.session['username'],
                [friend]
            )
    		return HttpResponseRedirect('/user/'+friend)
	return HttpResponseRedirect('/auth/login')
