from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from zeus_forum.models import Post


def set_menu(menu, ctx):
    ctx['menu_active'] = menu


def common_json_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return unicode(obj)


def handle_voter_login_redirect(request, voter, default):
    _next = request.GET.get('next', None)
    _next = request.session.get('next', _next)
    _next = _next or default

    forum_post = request.GET.get('redirect_forum_post', None)
    if forum_post:
        _next = Post.objects.get(id=forum_post).url

    forum = request.GET.get('redirect_forum', None)
    if forum:
        election_uuid = voter.poll.election.uuid
        poll_uuid = voter.poll.uuid
        _next = reverse('election_poll_forum', args=(election_uuid, poll_uuid))
        _next += "#forum"

    if _next.startswith("http"):
        #TODO: prevent open redirects
        pass

    return HttpResponseRedirect(_next)
