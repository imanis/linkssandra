from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('user.views',
    url(r'^addfriend/(?P<friend>\w+)/$', 'addfriend', name='addfriend'),
    url(r'^/?$', 'profile', name='profile'),
    url(r'^welcome/$', 'welcome', name='welcome'),
    url(r'^(?P<username>\w+)/$', 'userprofile', name='userprofile'),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
