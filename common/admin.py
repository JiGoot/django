from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin
from import_export.admin import ImportExportActionModelAdmin
from django.contrib import messages
from branch.models.variant import BranchVariant
from common.models import City, Country, Slot, OtpRequest, Zone
from common.models.app import App, Release
from common.models.catalog.category import Category
from common.models.catalog.item import Item
from common.models.catalog.section import Section, SectionCategory
from common.models.catalog.variant import Variant
from common.models.city_service import CityService

# from common.models.log import CancelledOrder
from common.models.gateway import Gateway, GatewayRule
from common.models.service import Service
from core.admin.actions import activate_selected, deactivate_selected
from core.utils import formattedError
from courier.dispatcher import CourierDispatcher
from merchant.models.supplier_variant import SupplierVariant


"""==== Release ===="""


# Register your models here.@
@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = [
        "version",
        "app",
        "stage",
        "channels",
        "min_version",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["version"]
    readonly_fields = ["created_at", "updated_at"]



"""==== App ===="""


@admin.register(App)
class AppAdmin(admin.ModelAdmin):

    class ReleaseInline(admin.TabularInline):
        model = Release
        fields = ("version", "stage", "channels", "min_version")
        readonly_fields = ("version", "stage", "channels", "min_version")
        extra = 0  # Show [extra] empty rows by default
        show_change_link = True
        can_delete = False

    list_display = ["type", "os", "bundle_id", "url"]
    list_filter = ["type", "os"]
    search_fields = ["type", "bundle_id"]
    inlines = [ReleaseInline]


from django.db.models import Case, When, Value, IntegerField


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    class Categoryline(admin.TabularInline):  # or use StackedInline for a different layout
        model = SectionCategory
        fields = ("index", "category", "is_active")
        extra = 0  # Show [extra] empty rows by default
        show_change_link = True
        can_delete = False

        # Filter FK choices → only parent categories
        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == "category":
                kwargs["queryset"] = Category.objects.filter(parent__isnull=True)
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = ["name", "index", "is_active"]
    inlines = [Categoryline]


@admin.register(SectionCategory)
class SectionCategoryAdmin(admin.ModelAdmin):
    list_display = ["section", "category", "index", "is_active"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    class SubcategoryInline(admin.TabularInline):
        model = Category
        fields = ("index", "name", "is_active")
        extra = 0  # Show [extra] empty rows by default
        show_change_link = True
        can_delete = False

    list_display = ["name", "parent", "type", "is_active", "image"]
    list_filter = ["is_active", "type"]
    actions = [activate_selected, deactivate_selected]

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     return qs.annotate(
    #         has_parent=Case(
    #             When(parent__isnull=False, then=Value(0)),
    #             default=Value(1),
    #             output_field=IntegerField(),
    #         )
    #     ).order_by("has_parent", "-is_active",  "name")

    # def get_inlines(self, request, obj: Category):
    #     if not obj:
    #         return []  # When creating a new category, show nothing

    #     if obj.parent is None:
    #         # It's a parent category → allow subcategories
    #         return [self.SubcategoryInline]

    #     # It's a subcategory → allow category items
    #     return [self.CategoryItemInline]


# @admin.register(CategoryItem)
# class CategoryItemAdmin(admin.ModelAdmin):
#     list_display = ["category", "item", "index"]
#     actions = [activate_selected, deactivate_selected]


@admin.register(Item)
class ItemAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    class ItemVariantInline(admin.TabularInline):
        model = Variant
        fields = ("index", "name", "weight", "volume")
        extra = 0  # Show [extra] empty rows by default
        can_delete = False
        show_change_link = True  # 👈 allows clicking through to the detail page

    list_display = ["name", "type_codes", "owner", "is_active", "image"]
    list_filter = ["is_active", "types"]
    search_help_text = "Search by supplier's name"
    inlines = [ItemVariantInline]


@admin.register(Variant)
class ItemVariantAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):

    class SupplierVariantInline(admin.TabularInline):
        model = SupplierVariant
        fields = ("supplier", "price", "discount", "is_active")
        extra = 0
        show_change_link = True
        can_delete = False

    list_display = ["item", "index", "name", "weight", "volume"]
    inlines = [SupplierVariantInline]


@admin.register(Country)
class CountryAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ["code", "dial_code", "currency", "smallest_bill"]
    search_fields = ("code",)
    search_help_text = "Search by country's name"


def start_dispatcher(modeladmin, request, queryset):
    """
    Admin action to start dispatcher for selected city
    """
    try:
        for city in queryset:
            couriers, orders, offers = CourierDispatcher.start(city.pk)
            messages.success(request, f"Successfully {city.name} dispatcher, {len(offers)} offers")
    except Exception as e:
        messages.error(request, f"Dispatcher failed: {formattedError(e)(e)}")


@admin.register(City)
class CityAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    class CityServiceInline(admin.TabularInline):
        model = CityService
        extra = 0 # Number of empty rows to show for adding new services
        fields = ['service', 'min_age', 'is_active'] # The specific fields you want to edit
    list_display = [
        "name",
        "length",
        "country",
        "timezone",
        "currency",
        "delivery_fee_base_amount",
        "delivery_fee_cpm",
        "delivery_fee_cpk",
    ]
    search_fields = ("name",)
    search_help_text = "Search by country's name"
    list_filter = ("country", "timezone")
    actions = [
        start_dispatcher,
    ]
    inlines = [CityServiceInline]



@admin.register(Service)
class ServiceTypeAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ("name", "index","is_active", "image")
    list_filter = ("is_active",)


@admin.register(Slot)
class SlotAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = [
        "id",
        "start",
        "end",
        "max_capacity",
    ]
    list_filter = ["max_capacity"]

    def has_add_permission(self, request, obj=None) -> bool:
        return False


# @admin.register(CancelledOrder)
# class CancelledOrderAdmin(admin.ModelAdmin):
#     list_display = ['order_type', 'order_code', 'by', 'reason']


@admin.register(Gateway)
class GatewayAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ["name", "country", "is_active", "currency", "min", "max"]
    list_filter = ["country", "is_active"]


@admin.register(GatewayRule)
class GatewayAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ["gateway", "min", "max", "fixed_fee", "percent_fee", "currency"]
    list_filter = [
        "gateway__country",
    ]


@admin.register(Zone)
class ZoneAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = [
        "name",
        "is_active",
        "detour_index",
        "start",
        "end",
    ]
    search_fields = ("name",)
    search_help_text = "Search by zone's name"
    list_filter = ("city__country", "city", "is_active")


# Register your models here.


@admin.register(OtpRequest)
class OtpRequestAdmin(admin.ModelAdmin):
    list_display = [
        "by",
        "dial_code",
        "phone",
        "channel",
        "created_at",
    ]
    readonly_fields = [
        "channel",
        "created_at",
    ]
