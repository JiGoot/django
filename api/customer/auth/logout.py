import logging
from api.customer.apiview import CustomerAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.utils import formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from customer.models.customer import CustomerDevice

logger = logging.getLogger(name=__file__)


class Customer_Logout(CustomerAPIView):
    """
    NOTE Even if an error occured or not, customer will still be disconnected regarddless,
    cause the authentication token will still be deleted from the customer device, error or not.
    Cause when login a new token is always generated
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [
        permissions.BasePermission,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):

        try:
            refresh_token_str = request.data.get("refresh")
            if not refresh_token_str:
                return Response({"detail": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

            # 1. Database Cleanup: Find and update the device tracking this token
            # We use filter().update() to avoid DoesNotExist errors if the device was already deleted
            CustomerDevice.objects.filter(refresh_token=refresh_token_str).delete(
                refresh_token=None, fcm=None  # Optional: stop pushes to logged-out devices
            )

            # 2. Token Invalidation: Add the token to the Blacklist
            token = RefreshToken(refresh_token_str)
            token.blacklist()

            return Response({"detail": "Successfully logged out from this device."}, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception(f"Couldn’t log out properly. Try again. {formattedError(exc)}")
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
