from django.utils.translation import ugettext_lazy as _
from django import forms
from django.conf import settings

from zeus_forum.models import Post
from zeus_forum.util import parse_markdown


BODY_LIMIT = getattr(settings, 'ZEUS_FORUM_POST_LIMIT', 100000)

class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.poll = kwargs.pop('poll')
        return super(PostForm, self).__init__(*args, **kwargs)

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        if parent and parent.level > 0:
            raise forms.ValidationError(_("Cannot reply to this post"))
        return parent

    def clean_body(self):
        body = self.cleaned_data.get('body')
        body = body and body.strip()
        if len(body) > BODY_LIMIT:
            raise forms.ValidationError(_("post content too long"))
        if not body:
            raise forms.ValidationError(_("empty post content"))

        try:
            parse_markdown(body)
        except Exception, e:
            self.poll.logger.exception(e)
            raise forms.ValidationError(_("invalid post content"))

        return body

    def save(self, user, *args, **kwargs):
        instance = super(PostForm, self).save(*args, commit=False, **kwargs)
        Post.objects.mk_post_for_zeususer(user, instance)
        return instance


    class Meta:
        model = Post
        fields = (
            'parent', 'election', 'poll', 'body'
        )
