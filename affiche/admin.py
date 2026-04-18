from django.contrib import admin
from .models import Affiche


@admin.register(Affiche)
class AfficheAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'index', 'is_active', 'start', 'end']
    list_filter = ("city",)
    search_fields = ('name', )
    search_help_text = "Search by name"
