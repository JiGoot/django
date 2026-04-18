from datetime import timedelta
import logging
from branch.models.branch import Branch
from core.utils import formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from django.core.cache import cache

logger = logging.getLogger(name=__file__)


class Branch__RequestPasswordReset(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _username = request.data.get('username', None)

        try:
            if not _username:
                raise ValueError("L'identifiant ne peut pas être vide")

            # INFO:: Parse username and retreive branch parameters 
            parsed = Branch.parse_username(_username )
            if not parsed:
                raise ValueError("Format d’identifiant invalide")
            _label, _code, _country_code = parsed

            # INFO:: Get branch
            branch: Branch = Branch.objects.select_related('city').filter(
                label=_label,
                code=_code,
                city__country__code=_country_code
            ).first()

            if branch and branch.is_active:
                # if not branch.supervisor:
                #     raise ValueError("Cannot proceed, branch's supervisor not assigned")
                # if not branch.supervisor.is_staff or not branch.supervisor.is_active:
                #     raise ValueError("Assinged supervisor is not staff or active")
                if not cache.get(branch.otp_cache_key):
                    branch.send_reset_otp(branch.id)  
                else:
                    logger.info(f"OTP already sent recently for branch {_username}")

            # Always return 200 to avoid leaking whether the user exists
            # If the branch exists and is actif, an OTP will be sent to the branch supervisor email.
            return Response(status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
