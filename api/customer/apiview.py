import logging
from rest_framework.views import APIView
from api.services.travel_metrics import get_travel_metrics
from common.models.app import App, Release
from core.utils import AppType, formattedError, getDeviceUtcOffset


# TODO: cache results by (os, bundle_id) to avoid DB hits on every request,
# implement expiration as needed based on app release changes.
class CustomerAPIView(APIView):
    def dispatch(self, request, *args, **kwargs):
        # Move the logic to dispatch which runs BEFORE the view method
        host = request.get_host() or ""
        host = host.split(":")[0]
        parts = host.split(".")
        subdomain = parts[0] if len(parts) > 2 else None

        if subdomain == "api":
            platform = request.META.get("HTTP_X_APP_OS")
            bundle_id = request.META.get("HTTP_X_APP_BUNDLE_ID")

            if platform and bundle_id:
                try:
                    # TODO: cache app by (os, bundle_id) and last_release by app; app.cached.last_release
                    app = App.objects.filter(
                        type=AppType.customer, os=platform, bundle_id=bundle_id
                    ).first()
                    release = (
                        Release.objects.filter(app=app).order_by("-created_at").first()
                    )

                    # branch in request for views to use
                    request.app = app
                    request.latest_release = release # app.cached.last_release

                except AttributeError as e:
                    request.app = None
                    request.latest_release = None

        return super().dispatch(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        # Still set headers in finalize_response
        release = getattr(request, "latest_release", None)
        if release:
            response["X-Version"] = release.version
            response["X-Min-Version"] = release.min_version
            response["X-Utc-Offset"] = getDeviceUtcOffset(request)

        return super().finalize_response(request, response, *args, **kwargs)
