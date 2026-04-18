import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.models.variant import BranchVariant
from common.models.catalog.category import Category
from common.models.catalog.variant import Variant
from core.utils import formattedError
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.authentication import JWTAuthentication
from collections import defaultdict
from django.db.models import Prefetch, Case, When, Value, IntegerField


# Define a custom ordering function for categories

# Create a logger for this file
logger = logging.getLogger(__name__)

UNCATEGORIZED_NAME = "Other"


class Customer__BranchCategoryMenuView(CustomerAPIView):
    """[⎷]
    A branch menu(category menu) is more precisely a branch category items list
    grouped by branch(category)'s subcategories.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        _branchId = kwargs["branch_id"]
        _catId = kwargs["category_id"]

        try:
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
                print(_branchId,_catId, bv.supplier_variant.variant.item.name)

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

            return Response(result, status=status.HTTP_200_OK)

        except (ObjectDoesNotExist, ValueError) as e:
            logger.warning(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# from django.db.models import F, Avg, Window
# from django.db.models.functions import RowNumber


# class Customer__BranchCategoryMenuViewPreview(CustomerAPIView):
#     """[⎷]
#     A branch menu(category menu) is more precisely a branch category items list
#     grouped by branch(category)'s subcategories.
#     """

#     authentication_classes = [JWTAuthentication]
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def get(self, request, *args, **kwargs):
#         _branchId = kwargs["branch_id"]
#         _catId = kwargs["category_id"]

#         # Aggregate popularity per item
#         # This return category_id | item_id | item_popularity
#         item_scores = (
#             BranchVariant.objects.filter(
#                 branch_id=_branchId,
#                 category__parent_id=_catId,
#                 is_active=True,
#                 supplier_variant__variant__is_active=True,
#                 category__parent__is_active=True,
#                 category__is_active=True,
#             )
#             .values(
#                 "category_id",  # subcategory
#                 "item_id",  # IMPORTANT: group by item
#             )
#             .annotate(
#                 in_stock=Case(
#                     When(stock__gt=0, then=Value(1)),  # Stock > 0 gets 1
#                     default=Value(0),  # Stock <= 0 gets 0
#                     output_field=IntegerField(),
#                 )
#             )
#             .filter(in_stock__gt=0)
#             .annotate(item_popularity=Avg("popularity_score"))
#             .annotate(
#                 row_number=Window(
#                     expression=RowNumber(),
#                     partition_by=[F("category_id")],
#                     order_by=F("item_popularity").desc(),
#                 )
#             )
#             .filter(row_number__lte=12)  # top 12 items per subcategory
#         )

#         result = []
#         subcategory_map = {}

#         for item in item_scores:
#             subcat = item.categories
#             if subcat_id not in subcategory_map:
#                 subcategory_map[subcat_id] = {
#                     "id": subcat_id,
#                     "name": item["supplier_variant__variant__item__category__name"],
#                     "items": [],
#                 }
#                 result.append(subcategory_map[subcat_id])

#             subcategory_map[subcat_id]["items"].append(
#                 {
#                     "id": item["supplier_variant__variant__item_id"],
#                     "name": item["supplier_variant__variant__item__name"],
#                     "popularity": item["item_popularity"],
#                 }
#             )
