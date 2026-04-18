from collections import defaultdict
import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.models.variant import BranchVariant
from common.models.catalog.category import Category
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.utils import formattedError
from django.db.models.query import QuerySet, Prefetch
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

# Define a custom ordering function for categories

# Create a logger for this file
logger = logging.getLogger(__name__)

UNCATEGORIZED_NAME = "Other"

from django.db.models import Prefetch, Case, When, Value, IntegerField

class Customer__BranchMenuItemView(CustomerAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        try:
            branch_id = kwargs["brId"]
            item_id = kwargs["id"]

            qs = (
                BranchVariant.objects.filter(
                    branch_id=branch_id,
                    stock__gt=0,
                    is_active=True,
                    supplier_variant__is_active=True,
                    supplier_variant__variant__is_active=True,
                    supplier_variant__variant__item__is_active=True,
                    supplier_variant__variant__item_id=item_id,
                )
                .select_related(
                    "supplier_variant__variant__item"
                )
                .order_by(
                    "-popularity_score",
                    "supplier_variant__variant__item__index",
                )
            )

            if not qs.exists():
                return Response(
                    {"error": "Item not found or not available in this branch"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the first item for metadata
            first_bv = qs[0]
            item = first_bv.supplier_variant.variant.item

            return Response(
                {
                    "id": item.id,
                    "name": item.name,
                    "image": item.image.url if item.image else None,
                    "description": getattr(item, "description", None),
                    "variants": [
                        {
                            "id": bv.id,
                            "name": bv.supplier_variant.variant.name,
                            "price": float(bv.price or bv.supplier_variant.price),
                            "discount": float(bv.discount or bv.supplier_variant.discount),
                            "stock": bv.stock,
                            "weight": bv.supplier_variant.variant.weight,
                            "volume": bv.supplier_variant.variant.volume,
                            "max_per_order": bv.max_per_order,
                            "variant_index": bv.supplier_variant.variant.index,
                            "popularity_score": bv.popularity_score,
                        }
                        for bv in qs.iterator()  # More memory efficient for large datasets
                    ],
                },
                status=status.HTTP_200_OK,
            )

        except KeyError as e:
            return Response(
                {"error": f"Missing parameter: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(formattedError(e))
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )