TODO:: Describe JiGoot and it key feature


# Affiches
Affiche are a way to show case campaigns and advertisement. Each Affiche is associated to a single city.

# Images 
Image are stored in AWS S3 bucket, in `WebP` formart. This is because `WebP` offers better compression rates than JPEG and PNG, providing high-quality images at smaller file sizes. It supports both lossless and lossy compression.

## Image Requirements:
- supplier profile : A (854×480) with cropping enforced
- supplier item image : A (480x480) with cropping enforced


# 1.0.3 / 13-dec-24
-> Move `CourierShiftSlot` from common.models to courier app as BaseSlot

# 1.0.2 / 19-oct-24
### FoodBusiness Cache Manager Refactoring
- add a `kitchen/cache.py` file in which a `KitchenCacheManager` is implemented.
- modified `kitchen/models.py` by adding a `__init__` method to initialize  `KitchenCacheManager`.Allowing to access a kitchen instance cache manage as follow `obj.cached`
- replace all ocurrance of `cached_branch_shifts` with `cached.shifts`. which requires modifications on the following: `KitchenShift.clean()`, `KitchenSrz.FoodBusiness.default()` and `KitchenSrz.Customer.catolog()`
- update `has_discount` in `KitchenSrz.customer.catalog` on `'has_discount': obj.cached.discounted,`
- add in `kitchen.cache.py`, `on_shift_update` and `on_item_update` signal reeceivers

#### CityCacheManager Refactor
refactore City cache manager to be similar to kitchen cache manager implementation
- in commmon folder create a `cache.py` file for the common model cache managers such as `CityCacheManager`.
- `affiches.retrieve()` to `affiches`
- `zones.retrieve()` to `zones`
- ...

### Website
- add a website template and static css, js files..
- add a `core/views.py` to reender the website
- in `core/urls.py` we added `path('', views.home, name='home')` as een endpoint to the home view.

### Remove or Rename
- remove `BaseShift` and moved all it fied directly to `KitchenShift`
- renamed `common.models.slot.py` to `common.models.ordering_slot.py`
- rename all the occurance of `platform_delivery_enabled` to `kitchen.platform_deliver`
- rename all the occurance of `OrderingSlot` to `OrderingSlot` 
- rename all occurance of `DeliverySlot` to `CourierShiftSlot`
* run migrations


### Add Fields
- add `kitchen.delivery_zones` field
- add related name`branches` to `kitchen.zone` field 
* run migrations

### 05-07-2025
- add a store and kitchen branch wrapper
- rename FoodBusiness and KitchenItem to Kitchen and BranchKitchen
- rename KitchenOrder, KitchenShift and KitchenManager's kicthen field to branch
- renamed KitchenProfile to FoodBusiness
- rename KitchenItem profile field to kitchen 

### 07-07-2025
- rename FoodBusiness to Business
- rename Kitchen and BranchItem to  FoodBusiness and KitchenItem
- rename KitchenCatalog to FoodCatalog
- rename BranchShift to KitchenSift
- unified store and kitchen manager models


### 08-07-2025
- unified store and kitchen order model
- unified store and kitchen order item model
Now we have unified customer payment model , as well as unified store and kitchen manager,  order and orderitem models
Allow with a single order dispatch  to account for both store and kitchen orders, making the dispatch process more accurate. 
this also allow to have a unified wallet transaction model which we already had, but now it con be linked directly to the associated order if any. thus avoiding generic linking
- renamed PayoutProvider to Gateway and PayoutProviderRule to GatewayRule


### 30-07-2025
- Add a minversion middleware to add the branch min-version to the response header. which is initially added to the 'BranchAppAuth'

### 31-08-25
- rename `KitchenItem` to `KitchenVariant`

### 14-09-25
- Improve the Store movement model and type to account for store variant transfer of ownership between store (platform-owned) or consignor  