from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse

import cass_link as cass

def jobs(request):
	if request.user['is_authenticated']:
		text = """<h1>jobs !</p>"""
		return HttpResponse(text)



	return HttpResponseRedirect('/auth/login')
