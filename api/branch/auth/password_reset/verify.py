from django.core.signing import TimestampSigner, SignatureExpired
from datetime import timedelta
import logging
from branch.models.branch import Branch
from core import verify
from core.utils import formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from django.core.cache import cache

logger = logging.getLogger(name=__file__)

PASSWORD_RESET_TOKEN_EXPIRY = timedelta(minutes=10).total_seconds()

class Branch__VerifyPasswordRest(APIView):
    '''
    API endpoint that verifies OTP for password reset.
    '''
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _username = request.data.get('username', None)
        _code = request.data.get('code', None)

        try:
            if not all([_username, _code]):
                raise ValueError("Missing data.")
            
            # Parse username
            _label, _suffix, _country_code = Branch.parse_username(_username)
            branch: Branch = Branch.objects.select_related('city').filter(
                label=_label,
                code=_suffix,
                city__country__code=_country_code
            ).first()

            if not branch or not branch.is_active:
                raise ValueError("....") # TODO: come up with a better message
            cached_code = cache.get(branch.otp_cache_key)
            if not cached_code:
                raise ValueError("Demande de réinitialisation invalide ou expirée.")
            if str(cached_code) != str(_code):
                raise ValueError("Code de vérification invalide ou expiré")

            # Hash the user_id
            signer = TimestampSigner()
            signed_store_id = signer.sign(branch.id)

            cache.delete(branch.otp_cache_key)  # Cleanup
            return Response({"token": signed_store_id}, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

