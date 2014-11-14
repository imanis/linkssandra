from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('jobs.views',
    url(r'^/?$', 'jobs', name='jobs'),
)
