from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from branch.models.manager import BranchManagerToken
from core.rabbitmq.broker import publisher
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from branch.models.manager import BranchManager, BranchManagerToken


class BranchManagerAuth(TokenAuthentication):
    model = BranchManagerToken

    def authenticate_credentials(self, key):
        try:
            # Select related 'manager' and branch to avoid extra queries
            token = self.model.objects.select_related('manager', 'manager__branch').get(key=key)
        except self.model.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        manager:BranchManager = token.manager 
        if not manager.branch:
            raise AuthenticationFailed("Manager is not assigned to any active branch")
        # Check active status depending on role
        if manager.branch and not manager.branch.is_active:
            raise AuthenticationFailed("Branch inactive or deleted")
            
        return (manager, token)