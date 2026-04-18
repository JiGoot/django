from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from datetime import datetime, timedelta
import pytz
from courier.models.courier import Courier
from core.rabbitmq.broker import publisher
from courier.models import CourierToken
from django.utils import timezone


class CourierAuthentication(TokenAuthentication):
    model = CourierToken

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.select_related(
                "courier__user", "courier__city"
            ).get(key=key)
        except self.model.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        courier: Courier = token.courier  # this is a Courier instance
        if not courier.is_active or not courier.user.is_active:
            raise AuthenticationFailed("User inactive or deleted")

        now = timezone.now()

        # ⏱ Update token.used_at if stale (>5 minutes)
        if not token.used_at or (now - token.used_at).total_seconds() > 300:
            publisher.publish(
                CourierToken.Tasks.update_used_at, token.key, now.isoformat()
            )

        # ⏱ Update courier.last_seen as usual (throttled)
        if not courier.last_seen or (now - courier.last_seen).total_seconds() > 300:
            publisher.publish(
                Courier.Tasks.update_last_seen, courier.id, now.isoformat()
            )
            pass
        return (courier, token)

        # class CourierAuthentication(TokenAuthentication):
        #     model = CourierAuthToken

        #     def authenticate_credentials(self, key):
        #         try:
        #             token = self.model.objects.select_related('user__user').get(key=key)
        #         except self.model.DoesNotExist:
        #             raise AuthenticationFailed('Invalid token')

        #         courier = token.user
        #         if not courier.is_active or not courier.user.is_active:
        #             raise AuthenticationFailed('User inactive or deleted')

        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        if (now - token.created) > timedelta(days=7):
            raise AuthenticationFailed("Token has expired")

        return (courier.user, token)
