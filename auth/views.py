from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from auth.forms import LoginForm, RegistrationForm

import cass_link as cass

def login(request):
    if request.user['is_authenticated']:
	return HttpResponseRedirect('/')
    login_form = LoginForm()
    register_form = RegistrationForm()
    next = request.REQUEST.get('next')
    if 'kind' in request.POST:
        if request.POST['kind'] == 'login':
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username = login_form.get_username()
                request.session['username'] = username
                if next:
                    return HttpResponseRedirect(next)
                return HttpResponseRedirect('/user')
        elif request.POST['kind'] == 'register':
            register_form = RegistrationForm(request.POST)
            if register_form.is_valid():
                username = register_form.save()
                request.session['username'] = username
                if next:
                    return HttpResponseRedirect(next)
                return HttpResponseRedirect('/user/welcome')
    context = {
        'login_form': login_form,
        'register_form': register_form,
        'next': next,
    }
    return render_to_response(
        'auth/login.html', context, context_instance=RequestContext(request))

def logout(request):
    request.session.pop('username', None)
    return render_to_response(
        'auth/logout.html', {}, context_instance=RequestContext(request))


