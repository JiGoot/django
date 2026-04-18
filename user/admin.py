from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from core.utils import formattedError
from user.models import User
from django.contrib import messages
from typing import Optional

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name','last_name', 'gender', 'dial_code', 'phone', 'email', )
    filter_horizontal = ('groups', 'user_permissions')

    def get_readonly_fields(self, request, obj: Optional[User]):
        readonly_fields = ['last_login',]
        if (request.user != obj) or not request.user.has_perm("user.can_change_user"):
            readonly_fields.__add__(['password', ])
        return readonly_fields

    # def save_model(self, request, obj:User, form, change):
    #     try:
    #         # Check if the password field has been changed
    #         if 'password' in form.changed_data:
    #             obj.set_password(obj.password)
    #         super().save_model(request, obj, form, change)
    #     except Exception as e:
    #         return messages.error(request, str(e) if isinstance(e, AssertionError)else formattedError(e))
    
