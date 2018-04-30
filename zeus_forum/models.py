import datetime

from datetime import timedelta
from math import ceil

from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse

from mptt.models import MPTTModel, TreeForeignKey, TreeManager

from zeus_forum.util import lock_atomic


USER_TYPE_CHOCIES = (
    ('admin', 'Admin'),
    ('voter', 'Voter')
)

EDIT_POST_TIME_LIMIT = getattr(settings, 'ZEUS_FORUM_POST_EDIT_TIME_LIMIT', 30)
PAGINATE_BY = getattr(settings, 'ZEUS_FORUM_PAGINATE_BY', 20)


class PostManager(TreeManager):

    PAGINATE_BY = PAGINATE_BY


    def last_page(self, count):
        page = int(ceil(count / float(PAGINATE_BY)))
        return 1 if page == 0 else page

    def get_active_post(self, **kwargs):
        return self.active_posts(**kwargs).get()

    def active_posts(self, **kwargs):
        return self.filter(is_replaced=False, **kwargs)

    @transaction.atomic
    def delete_post(self, user, post):
        pass

    def mk_post_for_zeususer(self, user, post):

        with lock_atomic(post.poll.pk):
            # handle post update. create a new entry instead of updating entry
            # fields.
            if post.pk:
                old_post = Post.objects.get(pk=post.pk)
                old_post.pk = None
                old_post.deleted = True
                old_post.deleted_at = datetime.datetime.now()
                old_post.is_replaced = True
                old_post.save()

                post.replaces = old_post
                post.is_modification = True
                post.save()
                return post

            post.voter = None
            post.admin = None
            post.post_index = Post.objects.filter(poll=post.poll,
                                                 election=post.election).count()

            utype = None
            _user = user._user
            if user.is_voter:
                utype = 'voter'
                post.voter = _user

            if user.is_admin:
                utype = 'admin'
                post.admin = _user

            post.user_type = utype
            return post.save()


class Post(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='comments')

    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, default=None, auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None)

    is_modification = models.BooleanField(default=False)
    is_replaced = models.BooleanField(default=False, db_index=True)

    replaces = models.ForeignKey('self', null=True, default=None,
                                 related_name='replaced_by')

    election = models.ForeignKey('helios.Election', db_index=True)
    poll = models.ForeignKey('helios.Poll', null=True, default=None, blank=True, db_index=True)
    title = models.CharField(max_length=300, null=True, default=None)
    body = models.TextField()

    user_type = models.CharField(max_length=100, choices=USER_TYPE_CHOCIES)
    voter = models.ForeignKey('helios.Voter', null=True, default=None)
    admin = models.ForeignKey('heliosauth.User', null=True, default=None)

    deleted = models.BooleanField(default=False, db_index=True)
    deleted_reason = models.TextField(null=True, blank=True)
    deleted_by_admin = models.ForeignKey('heliosauth.User', null=True, default=None, related_name='deleted_posts')
    post_index = models.PositiveIntegerField(null=True, default=None)

    objects = PostManager()

    @property
    def _page(self, paginate_by=PAGINATE_BY):
        if self.parent:
            posts = self.parent.get_active_children()
        else:
            posts = Post.objects.active_posts(poll=self.poll, level=0)

        count = posts.filter(id__lte=self.id).count()

        page = int(ceil(count / float(paginate_by)))
        return 1 if page == 0 else page

    @property
    def url(self):
        poll = self.poll
        election = poll.election
        forum_url = reverse('election_poll_forum', args=(
            election.uuid, poll.uuid))

        if self.parent:
            url = forum_url + '?post_id={}&page={}'.format(
                self.parent.id, int(self._page))
        else:
            url = forum_url + '?post_id={}&page=0'.format(self.id)

        return url + "#%d" % self.pk

    @property
    def post_id(self):
        return (self.post_index + 1) if self.post_index is not None else self.id

    @property
    def replied(self):
        return self.get_non_deleted_children().count() > 0

    def expired(self, delta, now=None):
        now = now or datetime.datetime.now()
        return (self.updated_at + delta) <= now

    def can_edit(self, user=None, voter=None):
        if not self.poll.feature_forum_open:
            return False
        if voter == self.voter and not self.replied:
            return not self.expired(timedelta(minutes=EDIT_POST_TIME_LIMIT))
        return False

    def can_delete(self, user=None, voter=None):
        if voter:
            return self.can_edit(user, voter)
        if user and user.is_admin:
            return self.poll.feature_forum_open

    @property
    def replies(self):
        return self.get_active_children()

    @property
    def user(self):
        return self.voter or self.trustee or self.admin

    @property
    def post_date(self):
        return self.updated_at or self.posted_at

    @property
    def deleted_by(self):
        if self.deleted_by_admin:
            return _('election admin')
        return self.voter.forum_display

    def get_non_deleted_children(self):
        return self.get_children().filter(deleted=False)

    @property
    def has_non_deleted_children(self):
        return self.get_non_deleted_children().count()

    def get_active_children(self):
        return self.get_children().filter(is_replaced=False)

    @property
    def has_active_children(self):
        return self.get_non_deleted_children().count()

    @property
    def find_latest(self):
        latest = self
        while latest.replaces:
            latest = latest.replaces
        return latest

    def voter_excluded(self):
        return bool(self.voter.excluded_at)



FORUM_NOTIFICATION_FREQUENCY_CHOICES = (
    ('periodic', _('Daily')),
    ('instant', _('Instant')),
)

class ForumUpdatesRegistrationManager(models.Manager):

    @transaction.atomic
    def register(self, poll, voter, frequency):
        from helios.models import Voter

        if not poll.forum_enabled:
            raise PermissionDenined

        try:
            voter = poll.voters.get(pk=voter.pk)
        except Voter.DoesNotExist:
            raise PermissionDenined

        self.filter(voter=voter).delete()
        reg = self.create(
            poll = poll,
            voter = voter,
            frequency = frequency,
            active = True,
            last_notified_at = datetime.datetime.now()
        )
        msg = "Voter {!r} registered for forum updates ({!r})".format(
            voter.voter_login_id, frequency)
        poll.logger.info(msg)
        return reg

    def unregister(self, poll, voter):
        regs = self.filter(poll=poll, voter=voter)
        for reg in regs:
            reg.delete()
            msg = "Voter {!r} un-registered from forum updates"
            poll.logger.info(msg.format(reg.voter.voter_login_id))

    def voter_registrations(self, voter):
        return self.poll_registrations(poll=voter.poll).filter(voter=voter)

    def poll_registrations(self, poll):
        return self.filter(poll=poll, active=True)

    def instant(self, poll):
        return self.poll_registrations(poll).filter(frequency='instant')

    def periodic(self, poll):
        return self.poll_registrations(poll).filter(frequency='periodic')

    def active_polls(self, frequencies=['periodic']):
        from helios.models import Poll
        forum_open = Poll.objects.forum_open()
        ids = self.filter(poll__in=forum_open) \
               .filter(active=True, frequency__in=frequencies) \
               .distinct('poll') \
               .values('poll__id')
        return map(lambda x:x['poll__id'], ids)



class ForumUpdatesRegistration(models.Model):
    poll = models.ForeignKey('helios.Poll', null=True, default=None, blank=True, db_index=True)
    voter = models.ForeignKey('helios.Voter', null=True, default=None)
    frequency = models.CharField(max_length=100,
                                 choices=FORUM_NOTIFICATION_FREQUENCY_CHOICES)
    active = models.BooleanField(default=True)
    last_notified_at = models.DateTimeField(null=True, default=None,
                                            auto_now=True)

    objects = ForumUpdatesRegistrationManager()
