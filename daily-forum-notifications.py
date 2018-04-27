import sys
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()

from zeus import tasks

tasks.periodic_forum_notifications.delay()
