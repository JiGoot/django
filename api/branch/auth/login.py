from branch.serializers.branch import BranchSrz
from common.authentication import BranchManagerAuth
from branch.models.manager import BranchManager, BranchManagerToken
from core.utils import formattedError
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView


# Create a logger for this file
logger = logging.getLogger(__name__)


logger = logging.getLogger(name=__file__)


class Branch__Login(APIView):
    # authentication_classes = [BranchAppAuth]
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    class Msg:
        INVALID_CREDENTIALS = (
            "Identifiant ou mot de passe incorrect. Veuillez vérifier vos identifiants et réessayer."
        )
        ACCESS_DENIED = "Accès refusé : Cette succursale est actuellement inactive."
        FCM_REQUIRED = "Jeton FCM non fourni."
        MISSING_CREDENTIALS = "Nom d'utilisateur et mot de passe sont requis."

    def post(self, request):
        try:
            _username = request.data.get("username", "").strip()
            _password = request.data.get("password", "").strip()
            _fcm = request.data.get("fcm", None).strip()
            _device = request.data.get("device", "Unknown").strip()

            if not _username or not _password:
                raise ValueError(self.Msg.MISSING_CREDENTIALS)
            if not _fcm:
                raise ValueError(self.Msg.FCM_REQUIRED)

            # Parse and validate branch identity
            manager: BranchManager = (
                BranchManager.objects.select_related(
                    "branch",
                    "branch__type",
                    "branch__supplier",
                )
                .filter(username=_username)
                .first()
            )
            if not manager:
                raise ValueError("Invalid credentials")

            if not isinstance(manager, BranchManager) or not manager.is_active:
                return Response(self.Msg.ACCESS_DENIED, status=status.HTTP_403_FORBIDDEN)

            # Check is password
            if not manager.check_password(_password):
                raise ValueError(self.Msg.INVALID_CREDENTIALS)

            # Save FCM and generate token
            with transaction.atomic():
                token, created = BranchManagerToken.objects.get_or_create(manager=manager)
                token.key = BranchManagerToken.generate_key()
                token.fcm = _fcm
                token.device = _device
                token.save(update_fields=["key", "fcm", "device"])
                if token:
                    data = {
                        "token": token.key,
                        "branch": BranchSrz.Branch.default(manager.branch),
                    }
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(formattedError(e))
            if isinstance(e, (ValueError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(
                formattedError(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# TODO::
# - See if it makes sens to integrate django-defender in the current login view
