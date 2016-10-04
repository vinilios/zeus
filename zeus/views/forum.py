import urllib
import datetime
import json
import os

try:
  from collections import OrderedDict
except ImportError:
  from django.utils.datastructures import SortedDict as OrderedDict

from zeus.forms import ElectionForm
from zeus.forms import PollForm, PollFormSet
from zeus.utils import *
from zeus.views.utils import *
from zeus import tasks
from zeus import reports
from zeus import auth
from zeus.views.poll import voters_email

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.forms.models import modelformset_factory
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _

from helios.view_utils import render_template
from helios.models import Election, Poll, CastVote, Voter

import bleach
from zeus_forum.forms import PostForm
from zeus_forum.models import Post



def _index(request, election, poll, extra=None):
    extra = extra or {}
    post = None
    post_id = request.GET.get('post_id', None)
    reply = request.GET.get('reply', None)
    user = request.zeususer
    voter = None

    forum_url = reverse('election_poll_forum', args=(election.uuid, poll.uuid))
    if post_id:
        forum_url += "?post_id={}".format(post_id)

    if request.zeususer.is_voter:
        voter = request.zeususer._user

    posts = Post.objects.active_posts(election=election, poll=poll, level=0)
    edit_id = request.GET.get('edit')
    edit = None
    if edit_id and request.method == 'GET':
        edit = get_object_or_404(Post, id=edit_id, voter=voter, poll=poll,
                                 election=election)
        if edit.get_active_children().count():
            messages.error(request,
                           _("You cannot modify a post with existing replies"))
            return HttpResponseRedirect(forum_url + "#")

        if not voter or (edit.voter != voter):
            raise PermissionDenied()
        extra['edit'] = edit
        post_id = edit.parent.pk if edit.parent else edit_id

    if post_id:
        try:
            post = posts.get(id=post_id, deleted=False)
        except Post.DoesNotExist:
            raise Http404
        posts = posts.filter(id=post_id)

    paginate = not post_id
    paginate_replies = True

    context = {
        'election' : election,
        'poll': poll,
        'user': user,
        'posts': posts,
        'post_id': post_id,
        'post': post,
        'max_level': 0,
        'reply': reply,
        'paginate_by': 10,
        'paginate': paginate,
        'paginate_replies': paginate_replies
    }
    context.update(extra)
    if poll:
        context['poll'] = poll

    set_menu('forum', context)
    return render_template(request, 'election_forum_view', context)


@auth.election_user_required
@auth.requires_poll_features('forum_visible')
@require_http_methods(["GET"])
def index(request, election, poll=None):
    return _index(request, election, poll)


@auth.election_user_required
@auth.requires_poll_features('forum_can_post')
@require_http_methods(["POST"])
def edit(request, election, post_id=None):
    pass


@auth.poll_voter_or_admin_required
@auth.requires_poll_features('forum_can_post')
@require_http_methods(["POST"])
def delete(request, election, poll):
    post_id = request.POST.get('post', None)
    user = request.zeususer
    kwargs = {}
    admin = None
    if not user.is_admin:
        kwargs['voter'] = user._user
        kwargs['poll'] = user._user.poll
    else:
        admin = user._user

    post = get_object_or_404(Post, deleted=False, id=post_id, **kwargs)
    post.deleted = True
    post.deleted_at = datetime.datetime.now()
    if admin:
        post.deleted_by_admin = admin
    post.save()
    messages.success(request, _("Forum post deleted successfully."))
    url = reverse('election_poll_forum', args=(election.uuid, poll.uuid))
    if post.parent:
        url += "?post_id={}".format(post.parent.id)
    return HttpResponseRedirect(url + "#site-messages")



@auth.election_user_required
@auth.requires_poll_features('forum_can_post')
@require_http_methods(["POST"])
def post(request, election, poll):
    if not request.zeususer.is_voter and not request.zeususer.is_admin:
        raise PermissionDenied

    admin = None
    if request.zeususer.is_admin:
        admin = request.zeususer._user

    voter = None
    if request.zeususer.is_voter:
        voter = request.zeususer._user

    is_voter = request.zeususer.is_voter
    user = request.zeususer

    if is_voter and poll.id != voter.poll.id:
        raise PermissionDenied

    if poll is None and is_voter:
        poll = voter.poll

    edit_id = request.POST.get('edit')
    edit = None
    if edit_id:
        edit = get_object_or_404(Post, poll=poll, election=election, id=edit_id,
                                 voter=voter, deleted=False)
        if not voter or (edit.voter != voter):
            raise PermissionDenied()
        parent = edit.parent

    else:
        ref = request.POST.get('ref')
        parent = None
        if ref:
            parent = get_object_or_404(Post, election=election, poll=poll,
                                       id=ref, deleted=False)

    data = request.POST.dict()
    data.update({
        'parent': parent and parent.id,
        'election': election.id,
        'poll': poll.id
    })

    forum_url = reverse('election_poll_forum', args=(election.uuid, poll.uuid))
    if edit and edit.get_active_children().count():
        messages.error(request,
                       _("You cannot modify a post with existing replies"))
        return HttpResponseRedirect(forum_url + "#")

    form = PostForm(data, instance=edit, poll=poll)
    if form.is_valid():
        post = form.save(user)
        url = reverse('election_poll_forum', args=(election.uuid, poll.uuid))
        if parent:
            url = url + '?post_id={}'.format(parent.id)
        elif edit and post.parent:
            url = url + '?post_id={}'.format(post.parent.id)
        url += "#{}".format(post.id)
        return HttpResponseRedirect(url)
    else:
        context = {
            'form': form,
            'edit': edit
        }
        return _index(request, election, poll, context)
