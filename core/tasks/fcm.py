from django.db.models import Prefetch
from datetime import datetime, timedelta
import json
import logging
from firebase_admin import messaging
from core.utils import formattedError
from order.models.order import Order
from order.serializers.order import OrderSrz


logger = logging.getLogger(__file__)


class FCM_Notify:
    class Branch:
        @staticmethod
        def incoming(fcm: str, code: str, placed_at: str):
            """NOTE - Send incoming order notification to the corresponding branch"""
            message = messaging.Message(
                android=messaging.AndroidConfig(
                    collapse_key="incoming",
                    priority="high",
                    ttl=timedelta(minutes=10),
                ),
                data={
                    "route": "/incoming",
                    "code": code,
                    "placed_at": placed_at,
                },
                token=fcm,
            )
            messaging.send(message)

    class Customer:
        @staticmethod
        def order_pickup(fcm: str, id: int, code: str, eat: int):
            """NOTE - Send incoming order notification to the corresponding branch

            Title: 🚚 Order #${code} picked up
            Body: Your order is on the way. Delivery in about ${eat} min.

            """
            message = messaging.Message(
                android=messaging.AndroidConfig(
                    collapse_key="status_update",
                    priority="high",
                    ttl=timedelta(minutes=10),
                ),
                notification=messaging.Notification(
                    title=f"🚚 Commande #${code} récupérée",
                    body=f"Votre commande est en route. Livraison dans environ {eat} min.",
                ),
                data={
                    "route": "/order/status",
                    "id": str(id),
                    "code": code,
                },
                token=fcm,
            )
            messaging.send(message)

        @staticmethod
        def order_dropoff(fcm: str, id: int, code: str):
            """NOTE - Send incoming order notification to the corresponding branch

            Title: 🚚 Order #${code} picked up
            Body: Your order is on the way. Delivery in about ${eat} min.

            """
            message = messaging.Message(
                android=messaging.AndroidConfig(
                    collapse_key="status_update",
                    priority="high",
                    ttl=timedelta(minutes=10),
                ),
                notification=messaging.Notification(
                    title=f"📍 Commande #${code} livrée",
                    body=f"Votre commande a été livrée.",
                ),
                data={
                    "route": "/order/status",
                    "id": str(id),
                    "code": code,
                },
                token=fcm,
            )
            messaging.send(message)

        def order_cancelled(
            fcm: str, id: int, code: str, reason: str, lngCode: str = "en"
        ):
            """NOTE - Send order status upadate notification on behalf to."""
            try:
                message = messaging.MulticastMessage(
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(channel_id="jigoot"),
                    ),
                    notification=messaging.Notification(
                        title=f"🚫 order cancelled",
                        body=f"Kitchen has cancelled order #{code}.\n{reason}",
                    ),
                    data={
                        "route": "/order/status",
                        "id": str(id),
                        "code": code,
                    },
                    tokens=[token.fcm for token in customer.tokens.all()].append(
                        courier.fcm
                    ),
                )
                messaging.send(message)
            except Exception as e:
                logger.exception(formattedError(e))

    class Courier:
        pass
