from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from branch.models.branch import Branch
from branch.models.variant import BranchVariant
from common.authentication import BranchManagerAuth
from branch.models.manager import BranchManager
from core.utils import formattedError

import logging


logger = logging.getLogger(__file__)


class Branch__MenuItems(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    # class CacheKeys:

    def get(self, request, *args, **kwargs):
        try:
            # The parent Subcategory id, which in  [Category].
            manager: BranchManager = request.user
            branch: Branch = manager.branch
            if not branch:
                raise ValueError("Invalid branch")

            qs = (
                BranchVariant.objects.filter(
                    branch__manager=manager,
                    is_active=True,
                    variant__item__categories__id=kwargs["id"],
                    variant__item__category_items__is_active=True,
                )
                .select_related("variant", "variant__item")
                .prefetch_related(
                    Prefetch(
                        "variant__item__category_items",
                        queryset=CategoryItem.objects.filter(
                            category_id=kwargs["id"],
                            is_active=True,
                        ).select_related("category"),
                        to_attr="filtered_cat_items",
                    )
                )
                .order_by("variant__item_id")
                .distinct()
            )

            items_map = {}

            for sv in qs:
                item = sv.variant.item

                if item.id not in items_map:
                    items_map[item.id] = {
                        "id": item.id,
                        "name": item.name,
                        "is_active": item.is_active,
                        "variants": [],
                    }

                items_map[item.id]["variants"].append(
                    {
                        "id": sv.id,
                        "name": sv.variant.name,
                        "weight": sv.variant.weight,
                        "volume": sv.variant.volume,
                        "price": sv.price,
                        "discount": sv.discount,
                        "stock": sv.stock,
                        "is_active": sv.is_active,
                    }
                )

            return Response(items_map.values(), status=status.HTTP_200_OK)

        except (ValueError, ObjectDoesNotExist) as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Branch__ItemStatusUpdate(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [
        permissions.BasePermission,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        try:
            _branch: Branch = request.user.branch

            _branch.items.filter(id=kwargs["id"]).update(**request.data)
            return Response(status=status.HTTP_200_OK)
        except (AssertionError, ObjectDoesNotExist) as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


'''
I'll help you create a query to get items available in a specific branch and subcategory. Here's how you can structure this based on common relationships between these models:


## Query to get items available in a branch and subcategory:

```python
def get_items_in_branch_subcategory(branch, subcategory):
    """
    Get all items available in a specific branch and subcategory
    """
    items = Item.objects.filter(
        subcategory=subcategory,
        variant__branchvariant__branch=branch
    ).distinct()
    
    return items

# Usage example:
branch = Branch.objects.get(id=1)
subcategory = Subcategory.objects.get(id=5)

available_items = get_items_in_branch_subcategory(branch, subcategory)
```

## More detailed query with related data:

```python
def get_items_with_variants_in_branch_subcategory(branch, subcategory):
    """
    Get items with their available variants in a specific branch and subcategory
    """
    items = Item.objects.filter(
        subcategory=subcategory,
        variant__branchvariant__branch=branch
    ).prefetch_related(
        'variant_set__branchvariant_set'
    ).distinct()
    
    return items

# Or if you want to include branch-specific variant information:
def get_detailed_items_in_branch_subcategory(branch, subcategory):
    """
    Get items with branch variant details
    """
    from django.db.models import Prefetch

    branch_variants_prefetch = Prefetch(
        'variant_set__branchvariant_set',
        queryset=BranchVariant.objects.filter(branch=branch)
    )
    
    items = Item.objects.filter(
        subcategory=subcategory
    ).prefetch_related(branch_variants_prefetch).distinct()

    # Filter items that have at least one variant available in the branch
    items = [item for item in items if item.variant_set.filter(branchvariant__branch=branch).exists()]

    return items
```

## Using Django ORM with annotations:

```python
from django.db.models import Exists, OuterRef

def get_available_items_optimized(branch, subcategory):
    """
    Optimized query using subqueries
    """
    items = Item.objects.filter(
        subcategory=subcategory
    ).annotate(
        is_available_in_branch=Exists(
            BranchVariant.objects.filter(
                branch=branch,
                variant__item_id=OuterRef('pk')
            )
        )
    ).filter(is_available_in_branch=True)
    
    return items
```

## If you need to check availability status:

```python
def get_items_with_availability(branch, subcategory):
    """
    Get items with availability information
    """
    items = Item.objects.filter(subcategory=subcategory).prefetch_related(
        Prefetch(
            'variant_set__branchvariant_set',
            queryset=BranchVariant.objects.filter(branch=branch),
            to_attr='branch_variants'
        )
    )

    # Add custom property to check if item is available in branch
    for item in items:
        item.is_available_in_branch = any(
            hasattr(variant, 'branch_variants') and variant.branch_variants
            for variant in item.variant_set.all()
        )

    return [item for item in items if item.is_available_in_branch]
```

## Template usage example:

```python
# views.py
def branch_subcategory_items(request, branch_id, subcategory_id):
    branch = get_object_or_404(Branch, id=branch_id)
    subcategory = get_object_or_404(Subcategory, id=subcategory_id)

    items = get_items_in_branch_subcategory(branch, subcategory)

    context = {
        'branch': branch,
        'subcategory': subcategory,
        'items': items,
    }
    return render(request, 'branch_items.html', context)
```

Choose the approach that best fits your needs:
- Use the first simple query if you just need the items
- Use the prefetch_related version if you need variant details
- Use the annotated version for better performance with large datasets

The key is following the relationship chain: `Item → Variant → StoreVariant → Store` and `Item → Subcategory`.
'''
