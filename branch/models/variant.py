from model_utils import FieldTracker
from branch.models.branch import Branch
from common.models.catalog.category import Category
from common.models.catalog.variant import Variant
from django.db import models
from django.db.models import Sum, Max
from django.core.validators import MinValueValidator, MaxValueValidator
from core.managers import ObjectsManager
from core.utils import CommissionType, StockMovementType
from django.utils.translation import gettext_lazy as _
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from merchant.models.supplier_variant import SupplierVariant

logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from order.models.item import OrderItem


"""
JiGoot Store is a rapid delivery service founded in 2025 (official launch). 
It pioneered the dark store model in DR Congo, operating small, local warehouses that serve as fulfillment centers. 
This setup enables JiGoot Store to deliver a wide range of FMCG products—including fresh produce, 
dairy, snacks, beverages, personal care items, small electronics and household goods—within 15 to 30 minutes of ordering.
"""


class BranchVariant(models.Model):
    """
    The amount it costs the platform, to acquire or produce the item
    Or the aggreed share of the merchant(consignor) per consignment item sold
    """

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="branch_variants")
    supplier_variant = models.ForeignKey(
        SupplierVariant, on_delete=models.CASCADE, related_name="branch_variants"
    )

    # The agreed selling price per unit in this consignment's city scope
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    # NOTE:: stock is editable only through stock movements
    stock = models.PositiveSmallIntegerField(default=0, editable=False)

    # > Maximum allowed per order for this branch. Leave empty for no limit.
    max_per_order = models.PositiveIntegerField(default=10)
    # --- Ranking fields (computed via scheduled job) ---
    popularity_score = models.FloatField(default=0, db_index=True, editable=True)
    trend_score = models.FloatField(default=0, db_index=True, editable=True)
    is_active = models.BooleanField(default=False)
    tracker = FieldTracker(fields=["price", "discount", "stock"])
    objects = ObjectsManager()

    class Meta:
        unique_together = ["branch", "supplier_variant"]
        ordering = [
            "-is_active",
            "branch",
        ]
        indexes = [
            models.Index(fields=["branch", "is_active"]),
            models.Index(fields=["branch", "-popularity_score"]),
            models.Index(fields=["branch", "-trend_score"]),
        ]

    @property
    def name(self):
        return f"{self.branch.label} | {self.supplier_variant.variant.item.name} - {self.supplier_variant.variant.name}"

    def __str__(self):
        return self.name

    

    def has_stock(self, qty: int) -> bool:
        return self.stock >= qty

    def confirm_sale(self, item: "OrderItem", initiator=None):
        """> Convert reserved stock into final sale (delivery + payment)."""
        with transaction.atomic():
            # Find total reserved qty for this order's item
            # Extra reserve movements for the same item are possible if it as ben adjusted after initial reservation.
            # e.g. Customer changes item qty (more/less) before order is finalized.
            reserved_qty = (
                self.stock_movements.filter(
                    type__in=[
                        StockMovementType.Outflow.reserve,
                        StockMovementType.Inflow.release,
                    ],
                    order_item=item,
                ).aggregate(total=models.Sum("qty"))["total"]
                or 0
            )

            # Validation checks. If any of these fail, no stock is changed.
            if reserved_qty == 0:
                return  # Nothing to confirm
            if reserved_qty != item.qty:
                raise ValueError(
                    f"Reserved qty ({reserved_qty}) != item[{item.id}] '{item.name[:20]}' qty ({item.qty})"
                )

            # Release only currently reserved stock first
            self.release(reserved_qty, item, initiator=initiator)

            # Then record the final sale movement
            self.stock_movements.create(
                type=StockMovementType.Outflow.sale,
                order_item=item,
                initiator=initiator,
                qty=reserved_qty,
            )

    def rollup_stock_movements(self, keep_latest=10):
        """> Keep the latest N stock movements, by collapsiing oldest ones."""

        with transaction.atomic():
            movements = self.stock_movements.order_by("-created")
            if movements.count() <= keep_latest:
                return

            # Collapse older movements into one,suring both StockMovemnt creation and deletion of old ones.
            old_movements = movements[keep_latest:]
            total_qty = old_movements.aggregate(Sum("qty"))["qty__sum"] or 0

            if total_qty != 0:
                self.stock_movements.create(
                    qty=total_qty,
                    type="rollup",
                    created=old_movements.first().created,
                    note=f"Compacted size: {old_movements.count()}",
                )

            # Delete old movements
            old_movements.delete()


class BranchVariantDailySales(models.Model):
    """
    This track daily item sold in the given branch.
    This is used later to compute Branch variant popularity and trend scores
    """

    branch_variant = models.ForeignKey(BranchVariant, on_delete=models.CASCADE, related_name="daily_sales")

    date = models.DateField(db_index=True)
    qty = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch_variant", "date"],
                name="unique_branch_variant_per_day",
            )
        ]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["branch_variant", "date"]),
        ]
