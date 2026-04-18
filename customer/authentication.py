# from customer.models.customer import Customer, CustomerToken
# from core.rabbitmq.broker import publisher
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# from django.utils import timezone
 

# class JWTAuthentication(TokenAuthentication):
#     model = CustomerToken

#     def authenticate_credentials(self, key):
#         try:
#             token = self.model.objects.select_related('customer__user').get(key=key)
#         except self.model.DoesNotExist:
#             raise AuthenticationFailed("Invalid token")

#         customer:Customer = token.customer  # this is a Customer instance
#         if not customer.is_active or not customer.user.is_active:
#             raise AuthenticationFailed("User inactive or deleted")

#         now = timezone.now()

#         # ⏱ Update token.used_at if stale (>5 minutes)
#         if not token.used_at or (now - token.used_at).total_seconds() > 300:
#             publisher.publish(CustomerToken.Tasks.update_used_at, token.key, now.isoformat())
        
#         # ⏱ Update customer.last_seen as usual (throttled)
#         if not customer.last_seen or (now - customer.last_seen).total_seconds() > 300:
#             publisher.publish(Customer.Tasks.update_last_seen, customer.id, now.isoformat())
#             pass
#         return (customer, token)
