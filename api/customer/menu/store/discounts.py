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
from django.db.models import Prefetch
from django.core.cache import cache


# Define a custom ordering function for categories

# Create a logger for this file
logger = logging.getLogger(__name__)

UNCATEGORIZED_NAME = "Other"


class Customer__BranchDiscounts(CustomerAPIView):
    """[⎷]
    A branch menu(category menu) is more precisely a branch category items list
    grouped by branch(category)'s subcategories.
    """
    class Keys:
        @classmethod
        def discounts(cls, branch_id):
            return f"customer:{branch_id}_discounts"

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            _branchId = kwargs["branch_id"]
            cached = cache.get(self.Keys.discounts(_branchId)) 
            try:
                if cached:
                    cached["cached"] = True
                    return Response(cached, status=status.HTTP_200_OK)
            except Exception as e:
                logger.warning(formattedError(e))
            bvs = (
                BranchVariant.objects.filter(
                    branch_id=_branchId,
                    discount__gt=0,
                    is_active=True,
                )
                .select_related("variant", "variant__item")
                .prefetch_related(
                    Prefetch(
                        "variant__item__categories",
                        queryset=Category.objects.filter(
                            parent__isnull=False,  # Only get subcategories
                        ).order_by("index"),
                        to_attr="ordered_categories",
                    )
                )
                .order_by(
                    "variant__item__category_items__category__index",
                    "variant__item__category_items__index",
                    "variant__index",
                )
                .distinct()  # Add distinct to avoid duplicates
            )


            subcat_map = {}

            for bv in bvs:
                variant = bv.variant
                item = variant.item

                # Get filtered subcategories
                subcats = item.ordered_categories  # Already filtered in the prefetch

                if not subcats:
                    continue

                # IMPORTANT: Since we filtered in prefetch, all categories here are valid
                # No need for additional filtering unless you want extra safety

                for subcat in subcats:  # Renamed 'sub' to 'subcat' for clarity
                    if subcat.id not in subcat_map:
                        subcat_map[subcat.id] = {
                            "id": subcat.id,
                            "name": subcat.name,
                            "index": subcat.index,  # Store index for sorting
                            "items": {},  # temporary dict for deduplication
                        }

                    if item.id not in subcat_map[subcat.id]["items"]:
                        subcat_map[subcat.id]["items"][item.id] = {
                            "id": item.id,
                            "name": item.name,
                            "image": (
                                item.image.url
                                if item.image and hasattr(item.image, "url")
                                else None
                            ),
                            "variants": [],
                        }

                    # Add variant
                    subcat_map[subcat.id]["items"][item.id]["variants"].append(
                        {
                            "id": bv.id,
                            "name": variant.name,
                            "price": float(
                                bv.price
                            ),  # Convert Decimal to float for JSON
                            "discount": float(bv.discount) if bv.discount else 0.0,
                            "stock": getattr(bv, "stock", None),
                            "weight": getattr(variant, "weight", None),
                            "volume": getattr(variant, "volume", None),
                            "max_per_order": getattr(bv, "max_per_order", None),
                            "variant_index": variant.index,  # Store for sorting
                        }
                    )

            # Convert dict to list with proper sorting
            payload = []

            for subcat_data in subcat_map.values():
                # Sort items by their index (or name as fallback)
                items_list = sorted(
                    subcat_data["items"].values(),
                    key=lambda x: (x.get("index", 0), x["name"]),
                )

                # Sort variants within each item by variant index
                for item in items_list:
                    item["variants"] = sorted(
                        item["variants"],
                        key=lambda v: (v.get("variant_index", 0), v["name"]),
                    )

                payload.append(
                    {
                        "id": subcat_data["id"],
                        "name": subcat_data["name"],
                        "index": subcat_data["index"],
                        "items": items_list,
                    }
                )

            # Sort subcategories by index (or name as fallback)
            payload = sorted(payload, key=lambda x: (x.get("index", 0), x["name"]))
            return Response(payload, status=status.HTTP_200_OK)

        except (ObjectDoesNotExist, ValueError) as e:
            logger.warning(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
