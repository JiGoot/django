from model_utils import FieldTracker
from model_utils.models import TimeStampedModel
from branch.models.variant import BranchVariant
from core.managers import ObjectsManager
from core.utils import StockMovementType, formattedError
from django.utils.translation import gettext_lazy as _
import logging
from django.db import models
from django.db import transaction

from user.models import User

logger = logging.getLogger(__name__)


"""Stock ledger / inventory movements / inventory transactions"""


class StockMovement(TimeStampedModel):
    type = models.CharField(max_length=15, choices=StockMovementType.choices)
    branch_variant = models.ForeignKey(BranchVariant, on_delete=models.RESTRICT, related_name="stock_movements")

    staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        # related_name="stock_movements",
    )
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        # related_name="stock_movements",
    )
    qty = models.SmallIntegerField()
    # cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tracker = FieldTracker()
    objects = ObjectsManager()

    @property
    def branch(self):
        return self.branch_variant.branch



    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return self.modified.strftime("%Y-%m-%d %H:%M")

    def save(self, *args, **kwargs):
        # NOTE:: Enforce positive qty for inflows, negative qty for outflows.
        if self.type in StockMovementType.Inflow.values:
            self.qty = abs(self.qty)
        elif self.type in StockMovementType.Outflow.values:
            self.qty = -abs(self.qty)

        is_new = self._state.adding
        with transaction.atomic():
            # NOTE:: Incrementally update StoreVariant stock while Ensure both StockMovement and StoreVariant
            # are updated together or not at all
            try:
                if not is_new and self.tracker.has_changed("qty"):
                    old_qty = self.tracker.previous("qty")
                    delta = self.qty - old_qty
                else:
                    delta = self.qty if is_new else 0

                # NOTE:: Save StockMovement first to ensure it has a PK
                super().save(*args, **kwargs)

                # NOTE:: Only update storevariant stock if there's a change in qty
                if delta:
                    self.branch_variant.stock = (self.branch_variant.stock or 0) + delta
                    self.branch_variant.save(update_fields=["stock"])
            except Exception as e:
                logger.error(formattedError(e))
