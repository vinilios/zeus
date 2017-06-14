import datetime

from django.db import models, transaction
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from django.utils.translation import ugettext_lazy as _
from zeus_forum.util import lock_atomic


USER_TYPE_CHOCIES = (
    ('admin', 'Admin'),
    ('voter', 'Voter')
)


class PostManager(TreeManager):

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
    is_replaced = models.BooleanField(default=False)

    replaces = models.ForeignKey('self', null=True, default=None,
                                 related_name='replaced_by')

    election = models.ForeignKey('helios.Election')
    poll = models.ForeignKey('helios.Poll', null=True, default=None, blank=True)
    title = models.CharField(max_length=300, null=True, default=None)
    body = models.TextField()

    user_type = models.CharField(max_length=100, choices=USER_TYPE_CHOCIES)
    voter = models.ForeignKey('helios.Voter', null=True, default=None)
    admin = models.ForeignKey('heliosauth.User', null=True, default=None)

    deleted = models.BooleanField(default=False, db_index=True)
    deleted_by_admin = models.ForeignKey('heliosauth.User', null=True, default=None, related_name='deleted_posts')
    post_index = models.PositiveIntegerField(null=True, default=None)

    objects = PostManager()

    @property
    def post_id(self):
        return (self.post_index + 1) if self.post_index is not None else self.id

    @property
    def can_edit(self):
        return self.get_active_children().count() == 0

    @property
    def can_delete(self):
        return True

    @property
    def replies(self):
        return self.get_children().filter(is_replaced=False)

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

    def get_active_children(self):
        return self.get_children().filter(deleted=False)

    @property
    def has_active_children(self):
        return self.get_active_children().count()

    @property
    def find_latest(self):
        latest = self
        while latest.replaces:
            latest = latest.replaces
        return latest
