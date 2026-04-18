import logging
from model_utils import FieldTracker
from branch.models.tag import Tag
from core.managers import ObjectsManager
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.core.exceptions import ValidationError
from core.mixin.file_cleanup import FileCleanupMixin
from core.utils import CommissionType, versioned_upload

from merchant.models.merchant import Merchant
from merchant.models.supplier_commission import SupplierCommission

logger = logging.getLogger(__name__)

"""
A Supplier typically refers to the organizational entity that:
A Supplier is any organization or individual business entity that owns/manages a catalog of items and one or more kitchens, 
which operate physically to fulfill customer orders. 
It centralizes ownership, branding, and product definitions.

1. Independent Suppliers: Single-owner businesses with one or more kitchens. Small-scale, often local businesses.
    - Street food sellers
    - Home-based cooks
    - Local fast food kiosks
    - Corner cafés
    - Single-location small suppliers
🟢 Typically own 1 kitchen
🟢 Flexible menus, low overhead
🔴 May not have formal branding

🍴 2. Traditional Suppliers: National or regional chains with standardized menus. Dine-in or takeout eateries.
    - Sit-down suppliers
    - Bistros and grills
    - Ethnic food houses (e.g., African, Chinese, Indian)
    - Hotel suppliers
🟢 Own one or more kitchens
🟢 Usually have branded menus
🔵 May support self-pickup and dine-in


🍔 3. Supplier Chains / Franchises: Branded businesses with multiple branches.
    - Burger joints, pizza chains
    - Local or regional food chains
    - International fast food brands (e.g., KFC, Chicken Inn)
🟢 Centralized menu (via FoodItem)
🟢 Distributed kitchens across regions
🔵 May support scheduled orders, loyalty programs


🛵 4. Cloud Kitchens / Virtual Brands: Brands that only operate through delivery kitchens (no dine-in).
Delivery-only food brands without dine-in spaces.
    - Ghost kitchens
    - Multi-brand kitchen facilities
    - Virtual supplier brands operating inside existing kitchens
🟢 Operate behind the scenes
🟢 Low cost, scalable
🔵 Often run multiple brands from one physical kitchen

🍹 5. Beverage & Dessert Vendors: Specialized in drinks, smoothies, pastries, etc.
    - Juice and smoothie bars
    - Milkshake and tea brands (e.g., bubble tea)
    - Ice cream parlors
    - Bakeries and cake shops
🟢 Often niche or brand-driven
🟢 Can be independent or part of suppliers

🎉 6. Event & Catering Services: Sell food on-demand or for events.
    - Caterers for weddings or parties
    - Large-order-only food services
    - “Order by tray” vendors
🟢 May not have kitchens open daily
🔵 Typically support scheduled orders only

🧑‍🍳 7. Commissary / Shared Kitchen Operators: Rent out cooking space to other food businesses.
    - Central kitchen hubs
    - Business incubators
    - Food accelerators
🟢 Usually serve other food businesses, not end customers
🔴 May not list menus directly on your platform (but can be the "parent" business)

🏫 8. Institutional Food Services: In-house food operations for organizations.
    - School cafeterias
    - Hospital kitchens
    - Workplace canteens
🟢 Sometimes open to the public
🔵 May have restricted ordering (e.g., campus-only)

🛍️ 9. Retail Food Sellers: Selling packaged, ready-to-eat, or raw food.
    - Supermarkets with deli or ready meals
    - Frozen food brands
    - Farmers and specialty product sellers (e.g., honey, juice)
🔵 May sell through platform via pickup/delivery
🔴 Not always kitchen-based

4. Food Entrepreneurs:
    - One person or company operates multiple food brands from the same or different kitchens.
5. Institutional or Corporate Food Services:
    - Schools, hospitals, or companies with internal kitchens selling food.

"""


class Supplier(FileCleanupMixin, models.Model):

    def upload_logo(instance, filename):
        return versioned_upload("supplier/logo/", instance, filename)

    def upload_image(instance, filename):
        return versioned_upload("supplier/profile/images/", instance, filename)

    # NOTE:: Fields
    merchant = models.ForeignKey(Merchant, on_delete=models.RESTRICT, related_name="suppliers")
    country = models.ForeignKey("common.Country", on_delete=models.RESTRICT)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)
    tags = models.ManyToManyField(Tag, related_name="suppliers", blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    # TODO: one or more kitchen can have the same email as long they can verify the provided email
    logo = models.ImageField(upload_to=upload_logo, null=True, blank=True)
    image = models.ImageField(upload_to=upload_image, null=True, blank=True)
    # HQ
    address = models.CharField(max_length=150, null=True, help_text="HQ address")
    landmark = models.CharField(max_length=255, null=True, blank=True)
    rccm = models.CharField(max_length=100, null=True, blank=True, help_text="ex: RCCM 125-541-52")

    commission = models.ForeignKey(
        SupplierCommission,
        on_delete=models.RESTRICT,
        null=True,
        related_name="+",  # disables reverse accessor
    )
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    tracker = FieldTracker(fields=["logo", "image"])
    objects = ObjectsManager()

    class Meta:
        ordering = ("country", "-is_active", "name")
        unique_together = ("name", "country")

    def __str__(self):
        return self.name

    def clean(self):
        # INFO:: This method is automatically cally from django forms such as in the admin pannel
        # we my need to call it explicitly from a vie before caling the save mathod.
        return super().clean()

    def save(self, *args, **kwargs):
        # Model-specific logic here
        self.cleanup_files()
        super().save(*args, **kwargs)
