from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('user.views',
    url(r'^/?$', 'profile', name='profile'),
    url(r'^welcome/$', 'welcome', name='welcome'),
    url(r'^(?P<username>\w+)/$', 'userprofile', name='userprofile'),
)
