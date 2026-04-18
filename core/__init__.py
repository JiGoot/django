# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# from __future__ import absolute_import, unicode_literals
# from .celery import app as celery_app

# __all__ = ('celery_app',)
import os
from dotenv import load_dotenv
import firebase_admin

load_dotenv(override=True)
if not firebase_admin._apps:
    cred = firebase_admin.credentials.Certificate(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )
    firebase_admin.initialize_app(cred)

