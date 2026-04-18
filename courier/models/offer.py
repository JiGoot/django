import logging
from django.utils.translation import gettext_lazy as _
from django.db import models
from core.managers import ObjectsManager
from core.utils import OfferStatus
from courier.models.courier import Courier

# Create your models here.
logger = logging.getLogger(__file__)


class CourierOffer(models.Model):
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, related_name='offers')
    order = models.ForeignKey('order.Order', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=OfferStatus.choices, default=OfferStatus.pending
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(auto_now_add=True, null=True)
    reminder_count = models.PositiveIntegerField(default=0)
    objects = ObjectsManager()

    class Meta:
        ordering = ['-created_at']
        # indexes = [

        # ]
