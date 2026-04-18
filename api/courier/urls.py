# [⎷] version 1.0.0
from django.urls import path
from api.courier.active_orders import Courier__ActiveOrders
from api.courier.auth.login import Courier__Login
from api.courier.auth.logout import Courier__Logout
from api.courier.courier import Courier__Profile
from api.courier.history import Courier__OrdersHistory
from api.courier.home import Courier__HomeView
from api.courier.order.actions.dropoff import Courier__OrderDropoff
from api.courier.order.actions.pickup import Courier__OrderPickup
from api.courier.order.get import Courier__GetOrder

from api.courier.schedules import AddDashShifts, AddScheduleShifts, Courier__Shifts, ShiftConfirmation
from api.courier.transactions import Courier__TransactionsView
from api.courier.updates import Courier__StatusUpdate
from api.courier.actions.incoming import Courier__AcceptOffer
 
urlpatterns = [
    path('auth/login/', Courier__Login.as_view(), name='courier-login'),
    path('auth/logout/', Courier__Logout.as_view(), name='courier-logout'),

    path('status/update/<str:status>/', Courier__StatusUpdate.as_view(), name='status-update'), 
    path('order/<int:orderID>/', Courier__GetOrder.as_view(), name='order-with-items'),

    # order action
    path('order/<int:orderID>/pickup/', Courier__OrderPickup.as_view(), name='courier-order-pickup'),
    path('order/<int:orderID>/dropoff/', Courier__OrderDropoff.as_view(), name='courier-order-dropoff'),

    path('profile/', Courier__Profile.as_view(), name='courier'),
    path('active-orders/', Courier__ActiveOrders.as_view(), name='courier-orders-summary'),






    path('home/', Courier__HomeView.as_view(), name='home-view'),  
    path('transactions/<str:currency>/', Courier__TransactionsView.as_view(), name='courier-transactions'),   
    path('orders/history/', Courier__OrdersHistory.as_view(), name='orders-history'),    

    # path('order/<int:order_id>/grouped/items/', Courier__OrderItemsByCategory.as_view(), name='order-items-grouped') ,
    # path('delivery/slots/<str:date>/', CourierShiftSlotsAPI.as_view(), name='weekdays-delivery-slots'),
    path('confirm/shift/<int:shift_id>/', ShiftConfirmation.as_view(), name='shift-confirmation'),
    path('shifts/', Courier__Shifts.as_view(), name='courier-shifts'),
    path('add/dash/shift/', AddDashShifts.as_view(), name='add-adsh-shift'),
    path('add/scheduled/shifts/', AddScheduleShifts.as_view(), name='add-schduled-shifts'),
    path('accept/offer/<int:order_id>/', Courier__AcceptOffer.as_view(), name='accept-offer'), 
    path('decline/offer/<int:order_id>/', ShiftConfirmation.as_view(), name='decline-offer'),
    path('pickup/<int:order_id>/', Courier__OrderPickup.as_view(), name='order-pickup'),
    path('dropoff/<int:order_id>/', Courier__OrderDropoff.as_view(), name='courier-storeorder-dropoff'),
]
 