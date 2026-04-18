from django.contrib import admin
from customer.models.customer import Customer, CustomerDevice
from customer.models.payment import Payment
# Register your models here.


'''WARNING: passwerd is not updated when set through the admin panel
because set_password is not called'''


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    class CustomerDeviceInline(admin.TabularInline):
        model = CustomerDevice
        fields = ["fcm", "name", "platform", "last_active"]
        readonly_fields = ["fcm", "name","platform", "last_active", "created_at"]
        show_change_link = True
    list_display = ['user', 'gender', 'dial_code', 'phone', 'is_active', 'last_seen']
    list_filter = ('last_seen', 'created_at')
    search_help_text = "Search by name, last name or phone"
    readonly_fields = ['score', 'last_seen']
    inlines = [CustomerDeviceInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'customer', 'amount', 'currency', 'method']
    readonly_fields = ('customer',
                       'amount', 'currency', 'method', 'gateway', 'reference')
    list_filter = ("method", 'currency')
    search_fields = ('name', 'last_name', "phone", )
    search_help_text = "Search by name, last name or phone"
