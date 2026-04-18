from django.db import models
from branch.models.branch import Branch
from core.utils import CancelledBy, CancelledReason
from core.managers import ObjectsManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)



class BranchStatusLog(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.RESTRICT, null=True)
    status = models.CharField(max_length=10, choices=Branch.Status.choices)
    reason = models.TextField(max_length=250, blank=True,help_text='Busy or closed reason')
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ObjectsManager()

# class CancelledOrder(models.Model):
#     order_type = models.CharField(max_length=10)
#     order_id = models.PositiveIntegerField()
#     order_code = models.CharField(max_length=10)
#     order = 
#     by = models.CharField(max_length=10, choices=CancelledBy.choices)
#     reason = models.CharField(max_length=20, choices=CancelledReason.choices)
#     notes = models.TextField(
#         blank=True,
#         null=True,
#         verbose_name=_('Additional Notes')
#     )
#     created_at = models.DateTimeField(auto_now_add=True, editable=False)
#     objects = ObjectsManager()

#     class Meta:
#         unique_together = ('order_type', 'order_id')
#         ordering = ['-created_at']


class RequestChannels:
    sms = "sms"
    email = "email"


'''
According to documentations, they're unique, but you can't bind them to a specific device since they might change.

Documentation for IOS:
The registration token may change when:
- The app is restored on a new device
- The user uninstalls/reinstall the app
- The user clears app data.

Documentation for Android:

The registration token may change when:

- The app deletes Instance ID
- The app is restored on a new device
- The user uninstalls/reinstall the app
- The user clears app data.
'''

# Create your models here.
# Create a model to store the device id and the number of requests


class RequestedBy:
    kitchen = "kitchen"
    customer = "customer"
    courier = "courier"


class OtpRequest(models.Model):
    REQUESTED_BY = (
        (RequestedBy.kitchen, "Kitchen"),
        (RequestedBy.customer, "Customer"),
        (RequestedBy.courier, "Courier")
    )
    CHANNEL_CHOICES = (
        # NOTE: (real value, name admin)
        (RequestChannels.sms, "SMS"),
        # (RequestChannels.email, "eMail"),
    )
    dial_code = models.CharField(max_length=3)
    phone = models.CharField(max_length=15)
    by = models.CharField(max_length=15, choices=REQUESTED_BY)
    channel = models.CharField(max_length=15, choices=CHANNEL_CHOICES)
    otp = models.CharField(max_length=6, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ObjectsManager()

    class Meta:
        ordering = ('-created_at',)
