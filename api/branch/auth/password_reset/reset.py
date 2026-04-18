from django.core.signing import TimestampSigner, SignatureExpired
from django.core.signing import Signer, BadSignature
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import logging
from branch.models.branch import Branch
from branch.models.manager import BranchManager
from core.utils import formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from django.core.cache import cache

logger = logging.getLogger(name=__file__)

PASSWORD_RESET_TOKEN_EXPIRY = timedelta(minutes=10).total_seconds()


class Branch__PasswordReset(APIView):
    '''
    API endpoint that allows simultaneous phone verification and customer account creation.
    '''
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _token = request.data.get('token', None)
        _new_password = request.data.get('password')

        try:
            if not all([_token,  _new_password]):
                raise ValueError("Toutes les informations sont requises.")

            signer = TimestampSigner()
            try:
                store_id = signer.unsign(_token, max_age=PASSWORD_RESET_TOKEN_EXPIRY)
            except SignatureExpired:
                raise ValueError("Le lien de réinitialisation a expiré.")
            except BadSignature:
                raise ValueError("Jeton de réinitialisation invalide ou altéré.")
            
            BranchManager.password_validator(_new_password)  # reuse your validation logic

            branch: Branch = Branch.objects.select_related('manager').get(id=store_id)
            manager:BranchManager = branch.manager
            manager.set_password(_new_password)
            manager.save(update_fields=['password']) 
            return Response(status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
