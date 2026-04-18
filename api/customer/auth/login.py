import logging
from typing import Optional
from api.customer.apiview import CustomerAPIView
from api.customer.jwt_serializer import CustomerTokenObtainPairSerializer
from branch.models.manager import BranchManagerToken
from customer.models.customer import Customer, CustomerDevice
from customer.serializers import CustomerSrz
from core.utils import formattedError
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.utils import timezone
from user.models import User

logger = logging.getLogger(name=__file__)


# class Customer__Login(CustomerAPIView):
#     permission_classes = (permissions.AllowAny,)
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     class Msg:
#         INVALID_CREDENTIALS = "Numéro de téléphone ou mot de passe invalide."
#         ACCESS_DENIED = "Accès refusé. Veuillez contacter le support pour obtenir de l'aide."
#         FCM_REQUIRED = "FCM token not provided"

#     def post(self, request):
#         _dial_code = request.data.get("dial_code", None)
#         _phone = request.data.get("phone", None)
#         _password = request.data.get("password", None)
#         _device = request.data.get("device", "unknown")
#         _platform = request.data.get("platform", "unknown")
#         _fcm = request.data.get("fcm", None)

#         try:
#             if not all([_dial_code, _phone, _password]):
#                 raise ValueError("Tous les identifiants sont requis.")
#             # if not _fcm and _apn:
#             #     raise ValueError(self.Msg.FCM_REQUIRED)
            

#             # Normalize phone number by removing leading zeros
#             normalized_phone = _phone.lstrip("0")
#             # >> Allow users to login with multiple devices, but if user logout from one device -> it logout from all

#             user = User.objects.select_related("customer").get(
#                 dial_code=_dial_code,
#                 phone=normalized_phone,
#             )
#             print(88888, request.data, user)

#             if not user.is_active:
#                 return Response(self.Msg.ACCESS_DENIED, status=status.HTTP_403_FORBIDDEN)
#             if not user.check_password(_password):
#                 raise ValueError(self.Msg.INVALID_CREDENTIALS)
#             customer = user.customer
#             if not customer:
#                 customer, _ = Customer.objects.select_related("user").get_or_create(user=user)
#             if not customer.is_active:
#                 return Response(self.Msg.ACCESS_DENIED, status=status.HTTP_403_FORBIDDEN)
#             with transaction.atomic():
#                 # NOTE:: Support to the latest login device.
#                 # NOTE:: Update or create token for customer and device
#                 device, _ = CustomerDevice.objects.get_or_create(fcm=_fcm)
#                 token.key = CustomerDevice.generate_key()
#                 token.fcm = _fcm
#                 token.device = _device
#                 # token.apn = _apn TODO for ios support
#                 token.save(update_fields=["key", "fcm", "device"])

#                 data = CustomerSrz.Customer.default(customer)
#                 data["token"] = token.key
#             return Response(data, status=status.HTTP_200_OK)

        
#         except ValueError as e:
#             logger.warning(formattedError(e))
#             return Response(formattedError(e), status=status.HTTP_400_BAD_REQUEST)
#         except User.MultipleObjectsReturned:
#             return Response("Impossible de traiter la demande.", status=status.HTTP_400_BAD_REQUEST)
#         except User.DoesNotExist as e:
#             return Response(self.Msg.INVALID_CREDENTIALS, status=status.HTTP_400_BAD_REQUEST)
#         except Customer.DoesNotExist as e:
#             return Response(self.Msg.INVALID_CREDENTIALS, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.exception(formattedError(e))
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework_simplejwt.views import TokenObtainPairView

class Customer__Login(TokenObtainPairView):
    serializer_class = CustomerTokenObtainPairSerializer