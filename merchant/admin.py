from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin
from import_export.admin import ImportExportActionModelAdmin
from branch.models.branch import Branch
from branch.models.variant import BranchVariant
from common.models.catalog.category import Category
from common.models.catalog.item import Item
from merchant.models.merchant import Merchant
from merchant.models.supplier import Supplier

# from merchant.models.supplier_category import SupplierCategory
from merchant.models.supplier_commission import SupplierCommission
from merchant.models.supplier_variant import SupplierVariant


# Register your models here.
@admin.register(Merchant)
class MerchantAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    # TODO:: add supplier , and consignment  inlines
    list_display = ["user", "business", "role", "is_active", "created_at"]
    list_filter = ("is_active",)


@admin.register(Supplier)
class SupplierAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    class BranchInline(admin.TabularInline):
        model = Branch
        fields = [
            "label",
            "city",
            "status",
            "is_active",
        ]
        show_change_link = True
        can_delete = False
        extra = 0

    # TODO: REMOVE
    class CategoryInline(admin.TabularInline):
        model = Category
        fields = [
            "index",
            "name",
            "parent",
            "is_active",
        ]
        show_change_link = True
        can_delete = False
        extra = 0

    # TODO: REMOVE
    class ItemInline(admin.TabularInline):
        model = Item
        fields = ["name", "image", "is_active"]
        show_change_link = True
        can_delete = False
        extra = 0

    list_display = ["name", "merchant", "is_active", "created_at"]
    list_filter = ("is_active",)
    inlines = [BranchInline, CategoryInline, ItemInline]


@admin.register(SupplierCommission)
class SupplierCommissionAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ["supplier", "type", "value", "start", "end"]
    list_filter = ["type"]


@admin.register(SupplierVariant)
class SupplierVariantAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):

    class BranchVariantInline(admin.TabularInline):
        model = BranchVariant
        fields = [
            "branch",
            "price",
            "discount",
            "stock",
            "max_per_order",
            "is_active",
        ]
        readonly_fields = ["stock"]  # Stock Is Branch-Level Responsibility
        show_change_link = True
        can_delete = False
        extra = 0

    list_display = ["variant", "supplier", "category", "price", "discount", "is_active"]
    inlines = [BranchVariantInline]
