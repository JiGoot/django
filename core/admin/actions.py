from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

@admin.action(description=_("🟢 Activate"))
def activate_selected(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        ngettext(
            "%d item was successfully activated.",
            "%d items were successfully activated.",
            updated,
        ) % updated,
        messages.SUCCESS,
    )

@admin.action(description=_("🔴 Deactivate"))
def deactivate_selected(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        ngettext(
            "%d item was successfully deactivated.",
            "%d items were successfully deactivated.",
            updated,
        ) % updated,
        messages.SUCCESS,
    )