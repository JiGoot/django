from django.http.request import HttpRequest
from djangoql.admin import DjangoQLSearchMixin
from import_export.admin import ImportExportActionModelAdmin
from django.contrib import messages
from django.contrib import admin
from branch.models.manager import BranchManager
from core.mqtt import publish_message
from core.tasks.fcm import FCM_Notify
from core.utils import formattedError
from order.models import Order, OrderItem
from django.utils import timezone
from customer.models.payment import Payment

# Register your models here.
from core.rabbitmq.broker import publisher
from django.db.models import QuerySet


@admin.action(description="🔔 Send incoming alert")
def notify_incoming_order(self, request, queryset):
    try:
        # assert Stat.get_all(), "Q-Cluster for async-task not running"
        orders: QuerySet[Order] = queryset
        for order in orders:
            # if order.status == Order.Status.placed:
            manager: BranchManager = order.branch.manager
            publisher.publish(
                FCM_Notify.Branch.incoming,
                manager.token.fcm,
                order.code,
                order.placed_at.isoformat(),
            )
            # print(manager.token.fcm)
            # FCM_Notify.Branch.incoming(
            #     manager.token.fcm,
            #     order.code,
            #     order.placed_at.isoformat(),
            # )
            messages.success(request, f"#{order} Incoming alert successfully sent")
    except Exception as e:
        messages.error(request, str(e) if isinstance(e, AssertionError) else formattedError(e))


@admin.action(description="Publish trip offer via MQTT")
def mqtt_publish_offer(modeladmin, request, queryset):
    for order in queryset:

        if order.branch:
            topic = f"branch/{order.branch.id}/incoming/"
            payload = {
                "type": "incoming/",
                "id": order.id,
                "code": order.code,
                "status": order.status,
                # "placed_at": order.placed_at.isoformat(),
            }
            publish_message(topic, payload, retain=True)
            modeladmin.message_user(request, f"offer {order.id} published to driver {order.branch}")


@admin.action(description="📦 Mark as picked up")
def mark_as_pickedup(self, request, queryset):
    try:
        if not queryset:
            raise ValueError("No order selected")
        if len(queryset) > 1:
            raise ValueError("Select only one order")
        order: Order = queryset[0]
        if order.status != Order.Status.ready:
            raise ValueError("Order must be 'ready' for pickup")
        order.status = Order.Status.picked_up
        order.pickedup_at = timezone.now()
        order.save(update_fields=["status", "pickedup_at"])

        token = order.customer.tokens.first()
        publisher.publish(
            FCM_Notify.Customer.order_pickup,
            token.fcm,
            order.id,
            order.code,
            int((order.eat - order.pickedup_at).total_seconds() / 60),
        )
        messages.success(request, f"#{order} picked up")

    except Exception as e:
        messages.error(request, str(e) if isinstance(e, AssertionError) else formattedError(e))


@admin.action(description="📍 Mark as drop-off")
def mark_as_droppedoff(self, request, queryset):
    try:
        if not queryset:
            raise ValueError("No order selected")
        if len(queryset) > 1:
            raise ValueError("Select only one order")
        order: Order = queryset[0]
        if order.status != Order.Status.picked_up:
            raise ValueError("Order must be 'picked up' for drop-off")
        order.status = Order.Status.delivered
        order.delivered_at = timezone.now()
        order.save(update_fields=["status", "delivered_at"])

        token = order.customer.tokens.first()
        publisher.publish(
            FCM_Notify.Customer.order_dropoff,
            token.fcm,
            order.id,
            order.code,
        )
        messages.success(request, f"#{order} dropped off")

    except Exception as e:
        messages.error(request, str(e) if isinstance(e, AssertionError) else formattedError(e))


@admin.register(Order)
class OrderAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    class PaymentInline(admin.TabularInline):
        model = Payment
        fields = ["customer", "method", "amount", "currency"]
        show_change_link = True
        extra = 0

    class OrderItemInline(admin.TabularInline):
        model = OrderItem
        fields = ["name", "price", "discount", "qty", "removed"]
        readonly_fields = ["name"]
        show_change_link = True
        extra = 0
        max_num = 0

    list_display = ["code", "type", "status", "branch", "placed_at"]
    list_filter = ["status", "placed_at"]
    search_fields = ["code"]
    inlines = [PaymentInline, OrderItemInline]
    readonly_fields = [
        "customer",
        "branch",
        "code",
        "subtotal",
        "small_order_fee",
        "delivery_fee",
        "placed_at",
    ]

    actions = [mqtt_publish_offer, notify_incoming_order, mark_as_pickedup, mark_as_droppedoff]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False  # Can add an order from the admin panel


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "name", "price", "discount", "qty", "removed"]
    list_filter = [
        "removed",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False  # Can add an orderitem from the admin panel
