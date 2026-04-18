import logging
from branch.models.manager import BranchManager, BranchManagerToken
from core.utils import CourierStatus, formattedError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from common.authentication import BranchManagerAuth
from django.db import transaction

from courier.authentication import CourierAuthentication, CourierAuthentication
from courier.models.courier import Courier, CourierToken

# Create a logger for this file
logger = logging.getLogger(__name__)


class Courier__Logout(APIView):
    """
    NOTE Even if an error occured or not, customer will still be disconnected regarddless,
    cause the authentication token will still be deleted from the customer device, error or not.
    Cause when login a new token is always generated
    """

    authentication_classes = [
        CourierAuthentication,
    ]
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        try:
            courier: Courier = request.user
            with transaction.atomic():
                # Get the token key from the request auth
                key = request.auth.key
                # Delete the releted token
                CourierToken.objects.filter(key=key).delete()

                courier.status = Courier.Status.offline
                courier.save(update_fields=["status"])
                # TODO log status and close reason

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
