from django.core.exceptions import ObjectDoesNotExist
import logging
from rest_framework.response import Response
from api.customer.apiview import CustomerAPIView
from common.models.app import App, Release
from rest_framework import permissions, status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from typing import Optional
from core.utils import formattedError
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class LatestReleaseView(CustomerAPIView):
    """
    Returns the latest app release metadata for the upgrader client.
    The response will also include version headers via middleware.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    # TODO:: add ratelit
    def get(self, request, *args, **kwargs):
        try:
            # Use the app instance already fetched in finalize_response
            release: Optional[Release] = getattr(request, "latest_release", None)
            #TODO:: else Get the customer laates version
            return Response(
                {
                    "version": release.version,
                    # "msg": release.msg,
                    "changelog": release.changelog,
                    # "update_url": release.app.update_url,
                    "created_at": release.created_at,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, ValueError) or isinstance(e, ObjectDoesNotExist):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
