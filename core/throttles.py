from rest_framework.throttling import SimpleRateThrottle
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle





class OtpRequestThrottle(SimpleRateThrottle):
    scope = 'otp_request'

    def get_cache_key(self, request, view):
        # Use user ID if authenticated, or IP address if anonymous
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
