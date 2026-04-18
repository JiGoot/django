from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions, serializers
from django.contrib.auth import get_user_model

from customer.models.customer import Customer, CustomerDevice

User = get_user_model()


class DeviceInfoSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, default="unknown")
    platform = serializers.CharField(required=False, default="web")


class CustomerTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        """
        This overwrite optimized for Microservices.
        Used to define what data is encoded into the encrypted part of the JWT (the "claims").
        This ensures that the refresh token (and its child access token) both contain the user_id.
        This way, any service that validates the token knows exactly who the customer is without querying the database.
        By adding these claims, you are moving toward a stateless architecture where any microservice (Order, Payment, Tracking)
        can trust the token's identity without asking the Auth service "Who is User 20?".
        """
        token = super().get_token(user)

        # Add custom claims to the Access Token
        token["user_type"] = "customer"
        token["user_id"] = user.id
        if hasattr(user, "customer"):
            token["customer_id"] = user.customer.id
        return token

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default username field (email) from the serializer
        # We are removing the old version of the "email" field (the one that was required=True by default)
        self.fields.pop(User.USERNAME_FIELD, None)
        # Add your custom fields
        self.fields["email"] = serializers.EmailField(required=False, allow_null=True)
        self.fields["dial_code"] = serializers.CharField(required=False, allow_null=True)
        self.fields["phone"] = serializers.CharField(required=False, allow_null=True)
        self.fields["password"] = serializers.CharField(write_only=True)  # CRITICAL

        # Nested device field
        self.fields["device"] = DeviceInfoSerializer(required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        dial_code = attrs.get("dial_code")
        phone = attrs.get("phone")
        password = attrs.get("password")
        user = None

        # 1. Identification Logic
        if email:
            try:
                user = User.objects.select_related("customer").get(email=email)
            except User.DoesNotExist:
                pass  # Keep user as None to trigger the final check
        elif dial_code and phone:
            try:
                user = User.objects.select_related("customer").get(dial_code=dial_code, phone=phone)
            except User.DoesNotExist:
                pass
        # 2. Manual Validation
        if user is None:
            raise exceptions.AuthenticationFailed("No account found with these credentials")

        if not user.check_password(password):
            raise exceptions.AuthenticationFailed("Incorrect password")

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User is inactive")

        # Check for Customer profile
        try:
            customer: Customer = user.customer
        except ObjectDoesNotExist:
            raise exceptions.AuthenticationFailed("Not a registered Customer account")

        # 3. TOKEN GENERATION (The fix for the KeyError)
        # We manually do what Simple JWT does, skipping the broken super() call
        refresh = self.get_token(user)

        # 4. Device Management
        device_data = attrs.get("device")
        name = device_data.get("name")
        platform = device_data.get("platform")

        # We use the unique FCM token to find the device.
        # If it exists, we update the owner (customer) and metadata.
        CustomerDevice.objects.update_or_create(
            refresh_token=str(refresh),
            defaults={
                "customer": customer,
                "name": name,
                "platform": platform,
            },
        )

        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        # Optional: Add extra info to response
        data["customer"] = {
            "name": user.name,
            "last_name": user.last_name,
            "gender": user.gender,
            "dial_code": user.dial_code,
            "phone": user.phone,
            "email": user.email,
            # Customer Profile specific
            "id": customer.id,
            "substitution_pref": customer.substitution_pref,
        }

        return data
