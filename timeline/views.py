import uuid

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from timeline.forms import PostForm
from django.core.urlresolvers import reverse
from uuid import uuid1, uuid4, UUID

import cass_link as cass

NUM_PER_PAGE = 40

def timeline(request):
    form = PostForm(request.POST or None)
    if request.user['is_authenticated'] and form.is_valid():
        post_id =  uuid.uuid4()
	creation_ts= uuid.uuid1()
        cass.save_post(post_id, request.session['username'], form.cleaned_data['body'],creation_ts )
        return HttpResponseRedirect(reverse('timeline'))
    if request.user['is_authenticated']:
        posts = cass.get_posts()
   	context = {
       	 'form': form,
       	 'posts': posts,
    	}
	return render_to_response(
        'timeline/timeline.html', context, context_instance=RequestContext(request))
    return HttpResponseRedirect('/auth/login')



	
