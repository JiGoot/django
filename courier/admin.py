from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin
from import_export.admin import ImportExportActionModelAdmin

from courier.models import Courier, CourierShift,  CourierToken
from courier.models.offer import CourierOffer


@admin.register(CourierToken)
class CourierTokenAdmin(admin.ModelAdmin):
    list_display = ['key', 'courier', 'created_at']
    readonly_fields = ["key", 'courier']


@admin.register(Courier)
class CourierAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    class CourierTokenInline(admin.TabularInline):
        model = CourierToken
        fields = ['key', 'device', 'created_at']
        readonly_fields = ['device', 'created_at']
        extra = 0

    list_display = ['id',  'user', 'status',]
    list_filter = ['status', ]
    readonly_fields = ('fcm', )
    inlines = [CourierTokenInline, ]



@admin.register(CourierShift)
class ShiftAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ['courier', 'id', 'start', 'end', 'zone',]
    list_filter = ('zone', 'status', 'slots')

    def has_add_permission(self, request, obj=None) -> bool:
        return False

@admin.register(CourierOffer)
class CourierOfferOfferAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    list_display = ['courier', 'order', 'status', 'notified_at', 'reminder_count', 'created_at']
    list_filter = ("status", 'notified_at')

    def has_add_permission(self, request, obj=None) -> bool:
        return False
# Register your models here. Nakata03 oshinakata

