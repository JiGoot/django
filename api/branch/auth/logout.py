import logging
from branch.models.branch import Branch
from branch.models.manager import BranchManager, BranchManagerToken
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from common.authentication import BranchManagerAuth
from django.db import transaction

# Create a logger for this file
logger = logging.getLogger(__name__)


class Branch__Signout(APIView):
    '''
    NOTE Even if an error occured or not, customer will still be disconnected regarddless,
    cause the authentication token will still be deleted from the customer device, error or not.
    Cause when login a new token is always generated
    '''
    authentication_classes = [BranchManagerAuth,]
    permission_classes = [permissions.IsAuthenticated,]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        try:
            manager: BranchManager = request.user
            with transaction.atomic():
                # Get the token key from the request auth
                key = request.auth.key
                # Delete the releted token
                BranchManagerToken.objects.filter(key=key).delete()
                branch = manager.branch
                branch.status = Branch.Status.closed
                branch.save(update_fields=['status'])
                # TODO log status and close reason 

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
