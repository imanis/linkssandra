from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('auth.views',
    url('^login/$', 'login', name='login'),
    url('^logout/$', 'logout', name='logout'),

)
