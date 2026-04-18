from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from branch.models.branch import Branch
# from branch.models.category import BranchCategory
from common.authentication import BranchManagerAuth
from branch.models.manager import BranchManager
from common.models.catalog.category import Category
from core.utils import formattedError

import logging


logger = logging.getLogger(__file__)


class Branch__MenuCategory(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            manager: BranchManager = request.user
            branch: Branch = manager.branch
            if not branch:
                raise ValueError("Invalid branch")
            data = []
            categories = (
                Category.objects.filter(
                    supplier_id=branch.supplier_id, parent__isnull=True,
                )
                .select_related("supplier")
                .order_by(
                    "-is_active",
                    "index",
                )
            )
            data = [
                {
                    "id": c.id,
                    "name": c.name,
                    "is_active": c.is_active,
                }
                for c in categories
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
