from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    url('^auth/', include('auth.urls')),
    url('^user/', include('user.urls')),
    url('^posts/', include('posts.urls')),
    url('^jobs/', include('jobs.urls')),
    url('^', include('posts.urls')),


)

if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
        (r'^media/(?P<path>.*)$', 'serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
