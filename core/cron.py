from django.contrib.admin.models import LogEntry
from django.utils import timezone 
from datetime import timedelta

# APPLY CRON
# python manage.py crontab add

def cleanup_admin_log():
    VALIDITY_DAYS = 45 
    cutoff_date = timezone.now() - timedelta(days=VALIDITY_DAYS)
    deleted_count, _ = LogEntry.objects.filter(action_time__lt=cutoff_date).delete()


