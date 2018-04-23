import datetime
from datetime import timedelta

from zeus import tasks
from zeus_forum.models import ForumUpdatesRegistration, Post


def new_posts_since(poll, since):
    return Post.objects.filter(poll=poll, posted_at__gte=since)


def assert_can_notify(poll):
    assert poll.forum_enabled
    assert poll.feature_forum_open


def notify_poll_instant(poll, post):
    notifications = ForumUpdatesRegistration.objects.instant(poll)
    poll.logger.info("Will handle %d notifications" % notifications.count())
    for notification in notifications:
        notify_voter_instant(notification.voter, post, notification)


def notify_poll_periodic(poll, hours):
    notifications = ForumUpdatesRegistration.objects.periodic(poll)
    poll.logger.info("Will handle %d notifications" % notifications.count())
    for notification in notifications:
        yesterday = datetime.datetime.now() - timedelta(hours=hours)
        new_posts = new_posts_since(poll, yesterday)
        notify_voter_periodic(notification.voter, new_posts, notification,
                              yesterday)
    poll.forum_last_periodic_notification_at = datetime.datetime.now()
    poll.save()


def notify_voter_periodic(voter, posts, notification, date_since):
    subject_tpl = 'email/forum_notify_periodic_subject.txt'
    body_tpl = 'email/forum_notify_periodic_body.txt'
    tpl_vars = {
        'new_ids': posts.filter(parent__isnull=True).values_list('id', flat=True),
        'posts_ids': posts.filter(parent__isnull=True).values_list('id', flat=True),
        'comments_ids': posts.filter(parent__isnull=False).values_list('id', flat=True),
        'date_since': date_since
    }

    return tasks.single_voter_email.delay(
        voter.uuid,
        voter.contact_methods,
        'periodic_forum_notification',
        subject_template_email=subject_tpl,
        template_vars=tpl_vars,
        body_template_email=body_tpl,
        body_template_sms=body_tpl,
        update_date=False,
        notify_once=True,
        forum_notification=notification,
        update_notification_date=True
    )


def notify_voter_instant(voter, post, notification):
    subject_tpl = 'email/forum_notify_instant_subject.txt'
    body_tpl = 'email/forum_notify_instant_body.txt'
    tpl_vars = {
        'post_id': post.pk
    }

    return tasks.single_voter_email.delay(
        voter.uuid,
        voter.contact_methods,
        'instant_forum_notification',
        subject_template_email=subject_tpl,
        template_vars=tpl_vars,
        body_template_email=body_tpl,
        body_template_sms=body_tpl,
        update_date=False,
        notify_once=True,
        forum_notification=notification,
        update_notification_date=True
    )

