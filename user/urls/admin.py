from django.contrib import admin
from django.urls import path

admin.site.site_header = 'JiGoot'         # default: "Django Administration"

urlpatterns = [
    path('', admin.site.urls),
]