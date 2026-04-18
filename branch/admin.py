from typing import Iterable
from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin
from import_export.admin import ImportExportActionModelAdmin
from branch.models.delivery_type import DeliveryType

from branch.models.feature import Feature, FeatureBranch
from branch.models.shift import Shift
from branch.models.branch import Branch
from branch.models.stock import StockMovement
from branch.models.tag import Tag
from branch.models.variant import BranchVariant
from branch.models.manager import BranchManager, BranchManagerToken
from django.contrib import messages
from common.models.boundary.city import H3_BRANCH_RES
from core.utils import formattedError

from core.rabbitmq.broker import publisher
from core.tasks.fcm import FCM_Notify


@admin.action(description="🔔 Send test incoming alert")
def notify_incoming(self, request, queryset):
    try:
        # assert Stat.get_all(), "Q-Cluster for async-task not running"
        # orders = queryset.filter(status=Order.Status.placed)
        branch: Branch = queryset.first()
        manager: BranchManager = branch.manager
        token = BranchManagerToken.objects.filter(manager=manager).first()
        # messages.success(request, f"FCM: {token.fcm}")
        # for order in orders:
        publisher.publish(FCM_Notify.Branch.incoming, token.fcm, "CT-267U", "2025-11-10 23:00:00")
        # publisher.publish(math.sin, 3.14)
        messages.success(request, "Successfully sent")
    except Exception as e:
        messages.error(request, str(e) if isinstance(e, AssertionError) else formattedError(e))


import h3


@admin.action(description="🔄 h3 index")
def refresh_h3_index(self, request, queryset):
    try:
        # assert Stat.get_all(), "Q-Cluster for async-task not running"
        # orders = queryset.filter(status=Order.Status.placed)
        for branch in queryset:
            branch.h3_res8 = h3.latlng_to_cell(branch.lat, branch.lng, H3_BRANCH_RES)
            branch.save(update_fields=["h3_res8"])
        messages.success(request, "Successfully refreshed")
    except Exception as e:
        messages.error(request, str(e) if isinstance(e, AssertionError) else formattedError(e))


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    class BranchManagerInline(admin.TabularInline):
        model = BranchManager
        fields = ("username", "password", "last_seen")
        readonly_fields = ["last_seen"]
        show_change_link = True
        can_delete = False

    class DeliveryTypeInline(admin.TabularInline):
        model = DeliveryType
        fields = ("code", "base_dispatch_buffer", "max_dispatch_buffer", "cutoff_time", "is_active")
        show_change_link = True
        extra = 0
        can_delete = False

    class BranchShiftInline(admin.TabularInline):
        model = Shift
        fields = ["weekdays", "start", "end", "is_active"]
        extra = 0
        show_change_link = True
        can_delete = False

    list_display = [
        "label",
        "type",
        "supplier",
        "status",
        "city",
        "h3_res8",
        "is_active",
    ]
    list_filter = ["is_active", "type"]
    min_zoom = 12
    max_zoom = 18
    num_zoom = 6
    inlines = [BranchManagerInline, DeliveryTypeInline, BranchShiftInline]
    actions = [notify_incoming, refresh_h3_index]
    # TODO:: manager can be added if null , else it can only be edited or deleted


@admin.register(Tag)
class TagAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ("name", "index", "is_active", "image")
    list_filter = ("type", "is_active")


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    class FeatureBranchInline(admin.TabularInline):
        model = FeatureBranch
        fields = ["brancch", "index", "is_active"]
        show_change_link = True

    list_display = ["label", "is_active"]


@admin.register(FeatureBranch)
class FeatureBranchAdmin(admin.ModelAdmin):
    list_display = ["feature", "branch", "index", "is_active"]


@admin.register(BranchManager)
class BranchManagerAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    class BranchManagerTokenInline(admin.TabularInline):
        model = BranchManagerToken
        fields = ["key", "device", "used_at"]
        readonly_fields = ["key", "device", "used_at", "created_at"]
        show_change_link = True

    list_display = ["username", "last_seen", "created_at"]
    inlines = [BranchManagerTokenInline]


@admin.register(BranchManagerToken)
class BranchManagerTokenAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ["key", "device", "used_at"]
    readonly_fields = ["fcm"]


@admin.register(Shift)
class ShiftsAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ["branch", "weekdays", "start", "end", "is_active"]
    list_filter = ["weekdays", "is_active"]


from django.db.models import Sum


@admin.register(BranchVariant)
class BranchVariantAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):

    @admin.action(description="🔄 Recalculate stock")
    def recalculate_stock(modeladmin, request, queryset: Iterable[BranchVariant]):
        updated, errors = 0, 0
        for variant in queryset:
            try:
                total = variant.stock_movements.aggregate(total=Sum("qty"))["total"] or 0
                if variant.stock != total:
                    variant.stock = total
                    variant.save(update_fields=["stock"])
                    updated += 1
            except Exception as e:
                errors += 1
                modeladmin.message_user(request, f"Error recalculating {variant}: {e}", messages.ERROR)
        if updated:
            modeladmin.message_user(request, f"{updated} stock(s) recalculated.", messages.SUCCESS)
        if not updated and not errors:
            modeladmin.message_user(request, "No changes needed.", messages.INFO)

    @admin.action(description="📚 Rollup stock movements")
    def rollup_stock_movements(modeladmin, request, queryset: Iterable[BranchVariant]):
        rolled_up_count = 0
        for variant in queryset:
            variant.rollup_stock_movements()
            rolled_up_count += 1

        if rolled_up_count:
            modeladmin.message_user(
                request,
                f"{rolled_up_count} rolled up stock movements.",
                messages.SUCCESS,
            )
        else:
            modeladmin.message_user(request, "No stock movements needed rollup.", messages.INFO)

    class StockMovementInline(admin.TabularInline):
        model = StockMovement
        fields = ("type", "staff", "qty")
        extra = 0  # Show [extra] empty rows by default
        show_change_link = False  # Default
        # can_update = False
        can_delete = False
        ordering = ["-created"]
        max_num = 10
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"

        def get_readonly_fields(self, request, obj=None):
            readonly = list(super().get_readonly_fields(request, obj))
            if request.user.is_superuser:
                # superuser can edit all fields inline
                return readonly  # or [] if you want everything editable
            # non-superuser: make all fields readonly
            return readonly + ["type", "initiator", "qty", "cost", "note"]

        def has_change_permission(self, request, obj=None):
            # Only superusers can update inline
            if request.user.is_superuser:
                self.show_change_link = True
                return True
            self.show_change_link = False
            return False

    list_display = ["supplier_variant", "branch", "price", "discount", "stock", "is_active"]
    list_filter = ["is_active"]
    readonly_fields = [
        "stock",
        "popularity_score",
        "trend_score",
    ]
    actions = [recalculate_stock, rollup_stock_movements]
    inlines = [StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ["type", "branch_variant", "staff", "qty", "modified", "created_at"]
    list_filter = ["type", "created_at"]
