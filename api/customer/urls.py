# [⎷] version 1.0.0
from api.customer.branch import Customer__GetBranch
from api.customer.catalog.main.tags import Customer__BranchTypeTags
from api.customer.catalog.vertical_types import Customer__VerticalTypes
from django.urls import path
from api.customer.app import LatestReleaseView
from api.customer.auth.is_registered import Customer__Registerd
from api.customer.auth.login import Customer__Login
from api.customer.auth.logout import Customer_Logout
from api.customer.auth.password_reset import (
    CustomerPasswordReset,
    CustomerRequestPasswordReset,
    CustomerVerifyPasswordRest,
)
from api.customer.auth.signup import CustomerSignUp, CustomerSignupRequest
from api.customer.catalog.main.ads import Customer__CarouselAds
from api.customer.catalog.main.features.kitchens import Customer__FeatureKitchens
from api.customer.catalog.main.kitchens import Customer__GetNearbyBranches
from api.customer.city import Customer__GetCity
from api.customer.menu.item import Customer__BranchMenuItemView
from api.customer.menu.store.discounts import Customer__BranchDiscounts
from api.customer.orders.cancel import Customer__OrderCancel
from api.customer.cart import CityCart

# from api.customer.catalog.main.store import Customer__NearbyStore
from api.customer.catalog.main.features.categories import Customer__FeatureCats

# from api.customer.catalog.kitchen import Customer__BranchTypeTags, Customer__KitchenCatalog
from api.customer.history import Customer__Orders

# from api.customer.coupon import Customer__ValidateCouponView
from api.customer.menu.category import Customer__BranchCategoryMenuView
from api.customer.orders.get import Customer__GetOrder
from api.customer.orders.placement import Customer__PlacingStoreOrder
from api.customer.orders.schedule_slots import Customer__ScheduleSlotList

# from api.customer.otp import Customer__RequestOTP, Customer__VerifyOTP
from api.customer.menu.branch import Customer__BranchMenuView, Customer__BranchMenuViewPreview
from api.customer.zones import Customer__GetZone, MapGeometryData

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    
    #
    path("app/latest/", LatestReleaseView.as_view()),
    path("auth/registered/", Customer__Registerd.as_view(), name="customer-is-registered"),
    # INFO:: Reset Password
    path(
        "auth/request/password-reset/",
        CustomerRequestPasswordReset.as_view(),
        name="customer-request-password-reset",
    ),
    path(
        "auth/verify/password-reset/",
        CustomerVerifyPasswordRest.as_view(),
        name="customer-verify-password-reset",
    ),
    path(
        "auth/password-reset/",
        CustomerPasswordReset.as_view(),
        name="customer-password-reset",
    ),
    # Simple Auth JWT
    path("auth/login/", Customer__Login.as_view(), name="customer-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/logout/", Customer_Logout.as_view(), name="customer-logout"),

    # INFO:: Signup
    path(
        "auth/request/signup/",
        CustomerSignupRequest.as_view(),
        name="customer-request-signup",
    ),
    path("auth/signup/", CustomerSignUp.as_view(), name="customer-signup"),
    # INFO customer orders API endpoint
    path("get/order/<int:id>/", Customer__GetOrder.as_view(), name="customer-order"),
    path(
        "cancel/order/<int:id>/",
        Customer__OrderCancel.as_view(),
        name="customer-order-cancellation",
    ),
    # INFO:: Order history
    path("orders/", Customer__Orders.as_view(), name="customer-orders"),
    # INFO:: Order Placement
    path("place/order/", Customer__PlacingStoreOrder.as_view(), name="order-create"),
    # path('validate/coupon/', Customer__ValidateCouponView.as_view(), name='customer-coupon-validation'),
    # INFO:: Main Catalog
    path("carousel/ads/", Customer__CarouselAds.as_view(), name="ads"),
    # path("v1/nearby/store/", Customer__NearbyStore.as_view(), name="nearby-store"),
    # INFO:: Features
    path("v1/feature/categories/", Customer__FeatureCats.as_view(), name="feature-categories"),
    path("v1/feature/kitchens/", Customer__FeatureKitchens.as_view(), name="feature-kitchens"), # REMOVE:: Deprecated in favor of `featured/kitchens/` from v5.2.3+43
    path("featured/kitchens/", Customer__FeatureKitchens.as_view(), name="featured-kitchens"),
    # Kitchen List
    # -------
    path("city/vertical-types/", Customer__VerticalTypes.as_view(), name="vertical-types"), # REMOVE:: Deprecated link in favor of `city/services/` from v5.2.3+43
    path("city/services/", Customer__VerticalTypes.as_view(), name="city-services"),
    path("tags/", Customer__BranchTypeTags.as_view(), name="tags"),
    # REMOVE::
    path("<int:type_id>/tags/", Customer__BranchTypeTags.as_view(), name="branch-type-tags"),
    path("<int:type>/nearby-branches/", Customer__GetNearbyBranches.as_view(), name="nearby-branches"),
    # ------ Branch Menu ------
    path("branch/<int:id>/menu/", Customer__BranchMenuView.as_view(), name="branch-menu"),
    path("branch/<int:brId>/item/<int:id>/", Customer__BranchMenuItemView.as_view(), name="branch-menu-item"),
    path("branch/<int:id>/menu/preview", Customer__BranchMenuViewPreview.as_view(), name="branch-menu-preview"),
    # ----- Branch-Category menu -----
    path(
        "branch/<int:branch_id>/category/<int:category_id>/menu/",
        Customer__BranchCategoryMenuView.as_view(),
        name="branch-category-menu",
    ),
    # -------
    # --------
    # TODO:: Deprecated `v1/store/catalog/` from v5.2.3+43
    # path("v1/store/catalog/", Customer__Nearby_Store.as_view(), name="store-catalog"),
    # INFO:: Menu
    path(
        "v1/store/<int:branch_id>/discounts/menu/",
        Customer__BranchDiscounts.as_view(),
        name="branch-discounts",
    ),
    # Getters
    path("branch/<int:id>/", Customer__GetBranch.as_view(), name="customer-branch"),
    path("city/<int:id>/", Customer__GetCity.as_view(), name="customer-city"),
    path("zone/<int:id>/", Customer__GetZone.as_view(), name="customer-zone"),
    path("cart/<int:zone>/meta/", CityCart.as_view(), name="cart-and-meta"),
    path(
        "scheduling-slots/",
        Customer__ScheduleSlotList.as_view(),
        name="scheduling-slots",
    ),
    # Map
    path("map/zones/", MapGeometryData.as_view(), name="map-zones"),
]
