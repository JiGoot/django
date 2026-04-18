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
from courier.models.courier import Courier, CourierToken
from courier.serializers import CourierSrz

from user.models import User


# Create a logger for this file
logger = logging.getLogger(__name__)


logger = logging.getLogger(name=__file__)


class Courier__Login(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    class Msg:
        INVALID_CREDENTIALS = "Identifiant ou mot de passe incorrect. Veuillez vérifier vos identifiants et réessayer."
        ACCESS_DENIED = "Accès refusé : Cette succursale est actuellement inactive."
        FCM_REQUIRED = "Jeton FCM non fourni."
        MISSING_CREDENTIALS = "Nom d'utilisateur et mot de passe sont requis."

    def post(self, request):
        try:
            _dial_code = request.data.get("dial_code", None).strip()
            _phone = request.data.get("phone", None).strip()
            _password = request.data.get("password", None).strip()
            _device = request.data.get("device", "unknown").strip()
            _fcm = request.data.get("fcm", None).strip()

            if not _dial_code or not _phone or not _password:
                raise ValueError(self.Msg.MISSING_CREDENTIALS)
            if not _fcm:
                raise ValueError(self.Msg.FCM_REQUIRED)

            # Normalize phone number by removing leading zeros
            normalized_phone = _phone.lstrip("0")
            # >> Allow users to login with multiple devices, but if user logout from one device -> it logout from all

            user = User.objects.select_related("courier").get(
                dial_code=_dial_code,
                phone=normalized_phone,
            )

            if not user.is_active:
                return Response(
                    self.Msg.ACCESS_DENIED, status=status.HTTP_403_FORBIDDEN
                )
            if not user.check_password(_password):
                raise ValueError(self.Msg.INVALID_CREDENTIALS)
            courier = user.courier
            if not courier:
                return Response(
                    self.Msg.INVALID_CREDENTIALS,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not courier.is_active:
                return Response(
                    self.Msg.ACCESS_DENIED, status=status.HTTP_403_FORBIDDEN
                )
            with transaction.atomic():
                # NOTE:: Support to the latest login device.
                # NOTE:: Update or create token for customer and device
                token, _ = CourierToken.objects.get_or_create(courier=courier)
                token.key = CourierToken.generate_key()
                token.fcm = _fcm
                token.device = _device
                # token.apn = _apn TODO for ios support
                token.save(update_fields=["key", "fcm", "device"])

                data = CourierSrz.Courier.default(courier)
                data["token"] = token.key
            return Response(data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                self.Msg.INVALID_CREDENTIALS,
                status=status.HTTP_400_BAD_REQUEST,
            )

        except User.MultipleObjectsReturned:
            return Response(
                "Impossible de traiter la demande.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Courier.DoesNotExist as e:
            logger.warning(formattedError(e))
            return Response(
                "Numéro de téléphone ou mot de passe invalide.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValueError as e:
            logger.warning(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# TODO::
# - See if it makes sens to integrate django-defender in the current login view
