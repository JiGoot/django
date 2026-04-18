"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""
import os
from django_hosts.middleware import HostsRequestMiddleware
# from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application


# Web-socket --- STEP 3
# NOTE: Initialize Djjango ASGI appliaction early to ensure the AppRegistry is populated
# before importing ORM models.

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # No HostsRequestMiddleware!
    # "websocket": ... (leave empty if not used)
})