from django.conf.urls import include, patterns, url

urlpatterns = patterns('zeus.views.forum',
    url(r'^$', 'index', name='election_poll_forum'),
    url(r'^post$', 'post', name='election_poll_forum_post'),
    url(r'^post/delete$', 'delete', name='election_poll_forum_post_delete'),
    url(r'^post/edit$', 'edit', name='election_poll_forum_post_edit')
)
