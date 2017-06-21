import urllib
import datetime
import json
import os

from math import ceil

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
from django.conf import settings

from helios.view_utils import render_template
from helios.models import Election, Poll, CastVote, Voter

import bleach
from zeus_forum.forms import PostForm
from zeus_forum.models import Post


PAGINATE_BY = getattr(settings, 'ZEUS_FORUM_PAGINATE_BY', 20)


def _last_page(count, paginate_by=PAGINATE_BY):
    page = int(ceil(count / float(paginate_by)))
    return 1 if page == 0 else page


def _get_edit_post_or_404(id, voter, poll, election, **kwargs):
    return get_object_or_404(Post, id=id, voter=voter, poll=poll,
                             election=election, is_replaced=False,
                             deleted=False, voter__excluded_at__isnull=True)


def _index(request, election, poll, extra=None):
    extra = extra or {}
    post = None
    post_id = request.GET.get('post_id', None)
    reply = request.GET.get('reply', None)
    page = request.GET.get('page', None)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = None
    user = request.zeususer
    voter = None

    forum_url = reverse('election_poll_forum', args=(election.uuid, poll.uuid))
    if post_id:
        forum_url += "?post_id={}".format(post_id)

    if request.zeususer.is_voter:
        voter = request.zeususer._user

    posts = Post.objects.filter(election=election, poll=poll, level=0)
    edit_id = request.GET.get('edit')
    edit = None
    if edit_id and request.method == 'GET':
        edit = _get_edit_post_or_404(edit_id, voter, poll, election)
        if not edit.can_edit:
            messages.error(request,
                           _("You cannot modify a post with existing replies"))
            return HttpResponseRedirect(forum_url + "#site-messages")

        if not voter or (edit.voter != voter):
            raise PermissionDenied()
        extra['edit'] = edit
        extra['post_body'] = edit.body
        post_id = edit.parent.pk if edit.parent else edit_id

    if post_id:
        try:
            post = posts.get(id=post_id, deleted=False)
        except Post.DoesNotExist:
            raise Http404
        posts = posts.filter(id=post_id)

    paginate = not post_id
    paginate_replies = True

    if paginate and page and (_last_page(posts.count()) < page):
        return HttpResponseRedirect(forum_url + "#forum")

    expand = request.GET.get('expand')
    paginate = False if expand else paginate
    paginate_replies = False if expand else paginate_replies

    SORT_FIELDS = {
        'date': 'posted_at',
        'voter': 'voter__voter_surname',
        'id': 'id',
        'replies': 'num_replies'
    }

    sort_by = request.GET.get('sort_by', 'id')
    if sort_by not in SORT_FIELDS:
        sort_by = 'id'

    #if sort_by == 'replies':
        #posts = posts.annotate(num_replies=Count('tree_id'))

    sort_by = SORT_FIELDS.get(sort_by, 'id')
    sort_type = request.GET.get('sort_type', 'asc')
    if sort_type == 'desc':
        sort_by = '-' + sort_by

    posts = posts.order_by(sort_by).filter(is_replaced=False).select_related('voter') # exclude replaced

    replies = None
    if post:
        replies = post.replies.order_by(sort_by).select_related('voter')

    context = {
        'election' : election,
        'poll': poll,
        'user': user,
        'posts': posts,
        'post_id': post_id,
        'post': post,
        'max_level': 0,
        'reply': reply,
        'paginate_by': PAGINATE_BY,
        'paginate': paginate,
        'expand': expand,
        'paginate_replies': paginate_replies,
        'replies': replies
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
        post.deleted_reason = request.POST.get('reason', None)

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
        edit = _get_edit_post_or_404(edit_id, voter, poll, election)
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
        'poll': poll.id,
        'post_body': edit.body if edit else None
    })

    forum_url = reverse('election_poll_forum', args=(election.uuid, poll.uuid))
    if edit and not edit.can_edit:
        messages.error(request,
                       _("You cannot modify a post with existing replies"))
        return HttpResponseRedirect(forum_url + "#site-messages")

    form = PostForm(data, instance=edit, poll=poll)
    if form.is_valid():
        post = form.save(user)
        url = reverse('election_poll_forum', args=(election.uuid, poll.uuid))

        if parent:
            page = _last_page(parent.get_active_children().count())
            url = url + '?post_id={}&page={}'.format(parent.id, int(page))
        elif edit and post.parent:
            page = _last_page(post.parent.get_active_children().count())
            url = url + '?post_id={}&page={}'.format(post.parent.id, int(page))
        else:
            page = _last_page(Post.objects.active_posts(poll=post.poll, level=0).count())
            url = url + '?page={}'.format(int(page))

        url += "#{}".format(post.id)
        return HttpResponseRedirect(url)
    else:
        context = {
            'form': form,
            'edit': edit,
            'post_body': form.data.get('body', edit.body)
        }
        return _index(request, election, poll, context)
