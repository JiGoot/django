import json
from datetime import datetime, timedelta
from firebase_admin import messaging

from core.utils import formattedError
from courier.models import Courier
from courier.serializers import CourierSrz
from firebase_admin import messaging
import logging

from order.models.order import Order
from order.serializers.order import OrderSrz


logger = logging.getLogger(name=__file__)
'''
NOTE Name convention to notify JiGoot [Eats] of order [status_update]
class OrderNotify:
    class Eats:
        @staticmethod
        def status_update(order:Order):
            ...
            fcm.send... 

NOTE - only customer, kitchen.kitchen or jigoot statff can cancel an order


The `tag` parameter allows you to replace a specific notification that already exists in the notification tray.
When a new notification with the same `tag` is received, it replaces the previous one.

You can also use the `collapse_key` field to group notifications. 
FCM will deliver only the most recent message with the same `collapse_key` 
if the device is offline, and this helps prevent multiple similar notifications.
'''


class OrderNotify:

    
    '''
    ----------------------------------------------------------------------------------------
                                    to Store
    ----------------------------------------------------------------------------------------
    '''
    class Branch:
        def on_placed(order_id: int, lngCode: str = 'en'):
            '''NOTE - Send order status upadate notification on behalf to.'''
            _order:Order = Order.objects.select_related('branch').filter(id=order_id).first()
            if isinstance(_order, Order):
                try:
                    # delay = timedelta()
                    # if kitchen.status == Branch.Status.busy and kitchen.delay_start:
                    #     if (timezone.now() - kitchen.delay_start) < timedelta(minutes=30):
                    #         delay = kitchen.delay
                    # TODO base TTL value on order.scheduled value between standard and scheduled order
                    message = messaging.Message(
                        android=messaging.AndroidConfig(
                            priority='high',
                            # TODO:: TTL shouldn't it be in seconds ?
                            ttl= timedelta(minutes=_order.branch.ttr +10)),
                        data={
                            "notification": json.dumps({
                                "title": "new offer",
                                "body": "a new offer is available. Tap to review details."
                            }),
                            "route": "/incoming",
                            "order": json.dumps(OrderSrz.Customer.basic(_order)),
                        },  
                        token=_order.branch.manager.fcm,
                    )
                    messaging.send(message)
                except Exception as exc:
                    logger.exception(formattedError(exc))

        def on_cancelled(order_id: int, lngCode: str = 'en'):
            '''NOTE - Send order status upadate notification on behalf to.'''
            _order = Order.objects.select_related('branch').filter(id=order_id).first()
            if isinstance(_order, Order):
                try:
                    message = messaging.Message(
                        android=messaging.AndroidConfig(priority='high'),
                        notification=messaging.Notification(
                            title=f"Order #{_order.code} is cancelled",
                            body="Sorry, the customer has cancelled the order."
                        ),
                        token=_order.branch.manager.fcm,
                    )
                    messaging.send(message)
                except Exception as exc:
                    logger.exception(formattedError(exc))

        def on_courier_arrival(order_id: int):
            '''NOTE - Send order status upadate notification on behalf to.'''
            _order = Order.objects.select_related('branch').get_or_none(id=order_id)
            if isinstance(_order, Order):
                if _order.status in [Order.Status.ready, Order.Status.picked_up]:
                    try:
                        _orderID = f'#{_order.pk}{_order.customer.pk}'
                        message = messaging.Message(
                            android=messaging.AndroidConfig(
                                # keep trying for 10min until sucess
                                ttl=datetime.timedelta(seconds=2*60),
                                priority='high',
                            ),

                            data={
                                "route": "/incoming",
                                "courier": json.dumps(CourierSrz.Branch.default(_order.courier)),
                            },
                            token=_order.branch.manager.fcm,
                        )
                        messaging.send(message)

                    except Exception as e:
                        logger.exception(
                            f"{e} in line {e.__traceback__.tb_lineno}")

    
    '''
    ----------------------------------------------------------------------------------------
                                    to Customer
    ----------------------------------------------------------------------------------------
    '''

    class Customer:
        def on_accepted(id: int, order_id: int, lngCode: str = 'en'):
            try:
                _order = Order.objects.select_related('customer').filter(id=order_id).first()
                if not isinstance(_order, Order):
                    raise Exception("order not found")
                rMsg = messaging.Message(
                    android=messaging.AndroidConfig(
                        notification=messaging.AndroidNotification(
                            channel_id="jigoot",
                        ),
                        priority='high',
                    ),
                    data={
                        "notification": json.dumps({
                            "title": f"#{_order.code} accepted",
                            "body": f"order is accepted and being prepared"
                        }),
                        "route": "/order",
                        "order": json.dumps(OrderSrz.Customer.basic(_order)),
                    }, 
                    token=_order.customer.fcm,
                ) 
                messaging.send(rMsg)
            except Exception as exc:
                logger.exception(formattedError(exc))

        def on_cancelled(id: int, lngCode: str = 'en'):
            try:
                _order = Order.objects.select_related('customer').filter(id=id).first()
                # TODO  get cancelled order with the associated order, similarly to what we did 
                # for order placement unpaid orders checks
                if not isinstance(_order, Order):
                    raise Exception("order not found")
                key = f"#{_order.code}-status"
                rMsg = messaging.Message(
                    android=messaging.AndroidConfig(
                        collapse_key=key,
                        notification=messaging.AndroidNotification(
                            channel_id="jigoot",
                            tag=key,
                        ),
                        priority='high',
                    ),
                    notification=messaging.Notification(
                        title=f"Order cancellation",
                        body=f"order #{_order.code} is successfully cancelled"
                    ),
                    token=_order.customer.fcm,
                )
                messaging.send(rMsg)
            except Exception as exc:
                logger.exception(formattedError(exc))

        def on_arrival(order_id: int):
            '''NOTE - Send order status upadate notification on behalf to.'''
            try:
                _order = Order.objects.select_related('customer').filter(id=order_id).first()
                if not isinstance(_order, Order):
                    raise Exception("order not found")
                if _order.status == Order.Status.picked_up:
                    rMsg = messaging.Message(
                        android=messaging.AndroidConfig(
                            priority='high',
                        ),
                        data={
                            "notification": json.dumps({
                                "title": f"#{_order.code} is on the way",
                                "body": f"order is accepted and being prepared"
                            }),
                            "route": "/order",
                            "order": json.dumps(OrderSrz.Customer.basic(_order)),
                        }, 
                        token=_order.customer.fcm,
                    )
                    messaging.send(rMsg)
            except Exception as exc:
                logger.exception(formattedError(exc))

    '''
    ----------------------------------------------------------------------------------------
                                    to Courier
    ----------------------------------------------------------------------------------------
    '''
    # class Courier:
    #     '''
    #     We send a silent message to handle case where the app is terminater (not running)
    #     cause Completely closing the app will prevent them from receiving new offer notifications.

    #     If the app is completely closed (i.e., not running at all), couriers will not receive offers.
    #     These offers rely on real-time communication between the courier's device and the server to push new delivery requests.

    #     INFO :: set [time_to_live] specifies how long FCM servers should attempt to deliver a message to the target device
    #     before discarding it. In other words, it controls the lifespan of a message in the FCM system if the device is offline or unable to receive the message immediately
    #     '''
    #     def kitchen_offer(courierId: int, orderId: int):
    #         try:
    #             app = None
    #             courier: Courier = Courier.objects.get(pk=courierId)
    #             order: Order = Order.objects.get(pk=orderId)
    #             route = '/incoming/kitchen'
    #             serialized = json.dumps(OrderSrz.Courier.listTile(order))
    #             message = messaging.Message(
    #                 token=courier.fcm,
    #                 android=messaging.AndroidConfig(priority='high', ttl=300),
    #                 data={
    #                     "notification": json.dumps(
    #                         {
    #                             "title": "New offer",
    #                             "body": "A new offer is available. Tap to review details."
    #                         },
    #                     ),
    #                     "route": route,
    #                     "order": serialized,
    #                 },

    #             )
    #             messaging.send(message, app=app)
    #         except Exception as e:
    #             logger.exception(formattedError(e))

    #     def store_offer(courierId: int, orderId: int):
    #         try:
    #             app = None
    #             courier: Courier = Courier.objects.get(pk=courierId)
    #             order: Order = Order.objects.get(pk=orderId)
    #             route = '/incoming/store'
    #             serialized = json.dumps(OrderSrz.Courier.listTile(order))
    #             message = messaging.Message(
    #                 token=courier.fcm,
    #                 android=messaging.AndroidConfig(priority='high', ttl=300),
    #                 data={
    #                     "notification": json.dumps(
    #                         {
    #                             "title": "New offer",
    #                             "body": "A new offer is available. Tap to review details."
    #                         },
    #                     ),
    #                     "route": route,
    #                     "order": serialized,
    #                 },

    #             )
    #             messaging.send(message, app=app)
    #         except Exception as e:
    #             logger.exception(formattedError(e))

    class Courier:

        def on_cancelled(order_id: int, lngCode: str = 'en'):
            '''NOTE - Send order status upadate notification on behalf to.'''
            _order = Order.objects.select_related('customer').filter(id=order_id).first()
            # TODO:: Fixe
            if isinstance(_order, Order):
                try:
                    message = messaging.Message(
                        android=messaging.AndroidConfig(priority='high'),
                        notification=messaging.Notification(
                            title=f"Order #{_order.code} is cancelled",
                            body="Sorry, the customer has cancelled the order."
                        ),
                        token=_order.customer.fcm,
                    )
                    messaging.send(message)
                except Exception as exc:
                    logger.exception(formattedError(exc))

        def new_offer(courier: Courier, order: Order,):
            '''
            We send a silent message to handle case where the app is terminater (not running)
            cause Completely closing the app will prevent them from receiving new offer notifications.

            If the app is completely closed (i.e., not running at all), couriers will not receive offers. 
            These offers rely on real-time communication between the courier's device and the server to push new delivery requests.

            INFO :: set [time_to_live] specifies how long FCM servers should attempt to deliver a message to the target device
            before discarding it. In other words, it controls the lifespan of a message in the FCM system if the device is offline or unable to receive the message immediately
            '''
            try:
                message = messaging.Message(
                    android=messaging.AndroidConfig(
                        priority='high',
                        ttl=150),
                    data={
                        "notification": json.dumps({
                            "title": "new offer",
                            "body": "a new offer is available. Tap to review details."
                        }),
                        "route": "/incoming",
                        "order": json.dumps(OrderSrz.Courier.listTile(order)),
                    },
                    token=courier.fcm,   
                )
                messaging.send(message)
            except Exception as e:
                logger.exception(formattedError(e))


'''
This is like we are calling couriers, amd the first to pickup the phone will be assign to deliver the order.
So we Send a fcm message with "data" key but without "notification" key, this is to prevent having a notification in the notification drawer.
If the notification is displayed in the notification drawer, it can becom quickly obselet, and of no use to the courier, that allow us to solve in a sens 
the problem of trying to cancel oblete now notification from courier device
'''


def notifyOrderWave(orderData, tokens):
    topic = "wave-#${order.pk}"
    message = messaging.MulticastMessage(
        data={
            "route": "/order/incoming/wavedetails",  # open the incoming order wave
            "args": {
                "order": orderData
            }
        },
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="jigoot"
            )
        ),
        token=tokens,
    )
    messaging.send_multicast(message)
