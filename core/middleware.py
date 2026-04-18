# middleware.py
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from common.models.app import App
from core import settings
from core.utils import AppType, AppOs, getDeviceUtcOffset


class ReadOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled and request method is modifying
        if settings.READ_ONLY and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            response = Response(
                "The system is under maintenance. Please try again later.",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
            # Manually render the response
            response.accepted_renderer = JSONRenderer()
            response.accepted_media_type = "application/json"
            response.renderer_context = {}
            return response.render()  # Ensures the content is rendered
        return self.get_response(request)


from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache



class ManagerVersionHeaderMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path.startswith("/api/manager/"):
            response["X-Min-Version"] = getattr(
                settings, "MANAGER_MIN_APP_VERSION", "1.0.0"
            )
            response["X-Latest-Version"] = getattr(
                settings, "MANAGER_LATEST_APP_VERSION", "1.0.0"
            )
            response["X-Update-Url"] = getattr(settings, "MANAGER_UPDATE_URL", "")
        return response


# class MinVersionHeaderMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         response = self.get_response(request)

#         if hasattr(request, "min_version"):
#             response["X-Min-Version"] = request.min_version

#         return response
