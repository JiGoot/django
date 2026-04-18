# [⎷] version 1.0.0
from django.urls import path
from api.branch.active_orders import Branch__ActiveOrders
from api.branch.auth.password_reset.request import Branch__RequestPasswordReset
from api.branch.auth.password_reset.reset import Branch__PasswordReset
from api.branch.auth.password_reset.verify import Branch__VerifyPasswordRest
from api.branch.branch import Branch__Profile
from api.branch.menu.category import Branch__MenuCategory
from api.branch.menu.items import Branch__ItemStatusUpdate, Branch__MenuItems
from api.branch.menu.subcategory import Branch__MenuSubcategories
from api.branch.order.actions.accept import Branch__AcceptOrder
from api.branch.order.actions.ready import Branch__ReadyOrder
from api.branch.order.actions.cancel import Branch__CancelOrder
from api.branch.order.get import Branch__GetOrder
from api.branch.history import Branch__History
from api.branch.dashboard import Branch__DashBoard
from api.branch.updates import Branch__StatusUpdate
from api.branch.auth.login import Branch__Login
from api.branch.auth.logout import Branch__Signout
 
urlpatterns = [
    path('menu/categories/', Branch__MenuCategory.as_view()),
    path('menu/<int:id>/subcategories/', Branch__MenuSubcategories.as_view()),
    path('menu/<int:id>/items/', Branch__MenuItems.as_view()),
    path('menu/item/<int:id>/status-update/', Branch__ItemStatusUpdate.as_view(), name='branch-item-update'),
    path('auth/login/', Branch__Login.as_view(), name='branch-signin'),
    path('auth/logout/', Branch__Signout.as_view(), name='branch-signout'),
    path('profile/', Branch__Profile.as_view(), name='branch'),
    path('active-orders/', Branch__ActiveOrders.as_view(), name='branch-orders-summary'),
    
    # INFO:: Reset Password
    path('auth/request/password-reset/', Branch__RequestPasswordReset.as_view(), name='branch-request-password-reset'),
    path('auth/verify/password-reset/', Branch__VerifyPasswordRest.as_view(), name='branch-verify-password-reset'),
    path('auth/password-reset/', Branch__PasswordReset.as_view(), name='branch-password-reset'),

    path('status-update/', Branch__StatusUpdate.as_view(), name='status-update'),
    path('dashboard/', Branch__DashBoard.as_view(), name='branch-dashboard'),
    path('history/', Branch__History.as_view(), name='branch-history'),
    path('order/<int:orderID>/', Branch__GetOrder.as_view(), name='order-with-items'),

    # order action
    path('accept/order/<int:orderID>/', Branch__AcceptOrder.as_view(), name='branch-order-accept'),
    path('ready/order/<int:orderID>/', Branch__ReadyOrder.as_view(), name='branch-order-ready'),
    path('cancel/order/<int:orderID>/', Branch__CancelOrder.as_view(), name='branch-order-cancelled'),

]
