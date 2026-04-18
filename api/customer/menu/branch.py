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


class Customer__BranchMenuView(CustomerAPIView):
    """[⎷]
    Kitchen Menu is a kitchen items list groupped by kitchen's categories
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        try:

            _branchId = kwargs["id"]
            branch: Branch = Branch.objects.select_related("supplier", "type").get(id=_branchId)
            if not branch:
                raise ValueError("Branch not found")

            categories = branch.cached.active_categories
            if len(categories) > 1:
                return Response({"view": "categories", "data": categories}, status=status.HTTP_200_OK)
            else:
                
                if not categories:
                    return Response({"view": "categories", "data": []}, status=status.HTTP_200_OK)

                category:dict = categories[0] if categories else None
                print(category.get("id"), "------------------")
                _catId = category.get("id")
                branch_variants = (
                    BranchVariant.objects.filter(
                        branch_id=_branchId,
                        is_active=True,
                        supplier_variant__variant__is_active=True,
                        supplier_variant__category__is_active=True,
                        supplier_variant__category__parent_id=_catId,
                        supplier_variant__category__parent__is_active=True,
                    )
                    .select_related(
                        "supplier_variant",
                        "supplier_variant__category",
                        "supplier_variant__category__parent",
                        "supplier_variant__variant",
                        "supplier_variant__variant__item",
                    )
                    # TODO:: Ensure item with variant stock >0 comes first
                    .annotate(
                        in_stock=Case(
                            When(stock__gt=0, then=Value(1)),  # Stock > 0 gets 1
                            default=Value(0),  # Stock <= 0 gets 0
                            output_field=IntegerField(),
                        )
                    )
                    .filter(in_stock__gt=0)
                    .order_by(
                        "supplier_variant__category__index",
                        "-popularity_score",
                        "supplier_variant__variant__item__index",
                    )
                    .distinct()  # Add distinct to avoid duplicates
                )

                result = []
                subcategory_map = {}
                item_map = {}

                for bv in branch_variants:
                    subcat = bv.supplier_variant.category  # BranchVariant belong to Subcategory only
                    item = bv.supplier_variant.variant.item
                    variant = bv.supplier_variant.variant
                    print("menu",_branchId, _catId, bv.supplier_variant.variant.item.name)

                    # --- Subcategory ---
                    if subcat.id not in subcategory_map:
                        subcategory_map[subcat.id] = {"id": subcat.id, "name": subcat.name, "items": []}
                        result.append(subcategory_map[subcat.id])

                    subcat_dict = subcategory_map[subcat.id]

                    # --- Item ---
                    item_key = (subcat.id, item.id)

                    if item_key not in item_map:
                        item_map[item_key] = {
                            "id": item.id,
                            "name": item.name,
                            "image": item.image.url if item.image else None,
                            "variants": [],
                        }
                        subcat_dict["items"].append(item_map[item_key])

                    item_dict = item_map[item_key]

                    # --- Variant ---
                    item_dict["variants"].append(
                        {
                            "id": bv.id,
                            "name": variant.name,
                            # Convert Decimal to float for JSON
                            "price": float(bv.price if bv.price else bv.supplier_variant.price),
                            "discount": float(bv.discount if bv.discount else bv.supplier_variant.discount),
                            "stock": getattr(bv, "stock", None),
                            "weight": getattr(variant, "weight", None),
                            "volume": getattr(variant, "volume", None),
                            "max_per_order": bv.max_per_order,
                            "variant_index": variant.index,  # Store for sorting
                        }
                    )

                return Response({"view": "subcategories", "data": result}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Customer__BranchMenuViewPreview(CustomerAPIView):
    """[⎷]
    Kitchen Menu is a kitchen items list groupped by kitchen's categories
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        try:

            branchId = kwargs["id"]
            branch: Branch = Branch.objects.select_related("supplier", "type").get(id=branchId)
            if not branch:
                raise ValueError("Branch not found")

            return Response(branch.cached.active_categories_preview, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
