from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from branch.models.branch import Branch
from common.authentication import BranchManagerAuth
from common.models.catalog.category import Category
from branch.models.manager import BranchManager
from core.utils import formattedError

import logging


logger = logging.getLogger(__file__)


class Branch__MenuSubcategories(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            # The parent Subcategory id, which in  is [Category].
            parentId = kwargs["id"]
            manager: BranchManager = BranchManager.objects.first()  # request.user
            branch: Branch = manager.branch
            if not branch:
                raise ValueError("Invalid branch")
            data = []

            subcategories = Category.objects.filter(parent_id=parentId).order_by(
                "-is_active", "name"
            )
            data = [
                {"id": c.id, "name": c.name, "is_active": c.is_active}
                for c in subcategories
            ]
            return Response(data, status=status.HTTP_200_OK)
        except (ValueError, ObjectDoesNotExist) as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
