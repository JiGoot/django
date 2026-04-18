from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import logging
from django.db import models
from branch.models.variant import BranchVariant
from core.managers import ObjectsManager
from core.utils import SubstitutionPref
from order.models.order import Order

logger = logging.getLogger(__name__)


"""
Should you auto-cancel or not?
Yes, you absolutely should auto-cancel.

* Reasons for Auto-Cancellation:
- Customer Experience: Prevents customers from waiting indefinitely for an order that will never be fulfilled. It provides a definitive answer and allows them to reorder from another establishment or choose another option.
- Operational Efficiency: Flags stores/kitchens that are unresponsive or potentially overwhelmed. This data can be used to improve operations, flag staffing issues, or even temporarily disable a store if they consistently fail to accept orders.
- Service Level Agreements (SLAs): Helps enforce performance standards for your partners.
- Inventory Accuracy (especially FMCG): If a store can't accept an order because an item is out of stock, auto-cancellation prevents the customer from thinking their order is confirmed when it isn't.
- Preventing Stale Orders: Avoids situations where a manager comes in hours later, sees an old order, and tries to accept it, leading to a terrible customer experience.

* What to do when an order auto-cancels:
- Notify the Customer Immediately: Clearly state that the order could not be accepted by the store/kitchen and has been canceled. Offer alternatives (e.g., suggested other nearby stores, reorder option).
- Notify the Store/Kitchen: Inform them that an order was auto-canceled due to non-acceptance and provide details. This can serve as an alert for them to check their system or staffing.
- Analyze Trends: Track auto-cancellation rates for each store/kitchen to identify recurring issues.
- In summary: Implement a clear, enforced auto-cancellation policy with different time limits for different product categories (e.g., shorter for hot food, slightly longer for FMCG). This protects the customer experience and maintains the integrity of your platform.


Recommendations for Time Limits:
Given the blend of FMCG and kitchen food, you'll likely need a nuanced approach.

* For Kitchen Food Orders (Especially Hot Food):
Recommended Auto-Cancellation: 3-5 minutes.
Rationale: This forces quick action from the kitchen. Customers expect rapid acknowledgment for prepared food. Any longer, and the customer might assume the order wasn't received or the kitchen is too busy, leading them to cancel themselves or become agitated. Some platforms even use as short as 1-2 minutes.

* For FMCG Orders (Standard Groceries, Non-Perishables):
Recommended Auto-Cancellation: 10-20 minutes.
Rationale: While still aiming for quick acceptance, FMCG orders often have more items to review, and the immediate time pressure is slightly less intense than hot food. This gives the store a bit more breathing room.

Considerations: If it's a very large grocery order or a scheduled delivery for hours later, you might extend this slightly, but usually not beyond 30 minutes.
"""
"""
------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------
                    ORDER ITEM
------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------
"""


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(BranchVariant, on_delete=models.SET_NULL, null=True, blank=True)
    # TODO:: Store alternative branch variant , this is set during prearation.
    qty = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    removed = models.BooleanField(default=False)
    name = models.CharField(max_length=100, editable=False)  # Item name + variant name
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )

    # Substitution rule snapshot with the following keys (preference, alternatives)
    substitution = models.JSONField()

    objects = ObjectsManager()

    @property
    def type(self):
        return self.order.type

    @property
    def total(self):
        return self.qty * self.price * (1 - self.discount)

    def __str__(self):
        return self.name
