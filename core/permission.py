import secrets
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from core import settings


class CustomerAppAuth(BaseAuthentication):
    '''Authenticate the Customer app device'''

    def authenticate(self, request):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != settings.CUSTOMER_API_KEY:
            raise AuthenticationFailed("Failed to identify customer device")
        request.app_name = "com.jigoot.www"

        return None  # No user authentication, just app validation


# class BranchAppAuth(BaseAuthentication):
#     '''Authenticate the Store app device'''

#     def authenticate(self, request):
#         api_key = request.headers.get("X-API-Key")
#         if not api_key or api_key != settings.BRANCH_API_KEY:
#             raise AuthenticationFailed("Failed to identify branch device")
#         request.app_name = "com.jigoot.branch"
#         return None  # No user authentication, just app validation



class CourierAppAuth(BaseAuthentication):
    '''Authenticate the Courier app device'''

    def authenticate(self, request):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != settings.COURIER_API_KEY:
            raise AuthenticationFailed("Failed to identify courier device")
        request.app_name = "com.jigoot.courier"
        return None

# class DefaultAppAuth(BaseAuthentication):
#     def authenticate(self, request):
#         api_key = request.headers.get("X-API-Key")
#         if not api_key or api_key != settings.DEFAULT_API_KEY:
#             return None

#         request.app_name = "com.default.client"  # Generic name for non-mobile clients
#         return None
