from customer.models.customer import Customer
from firebase_admin import messaging
import logging
from core.utils import formattedError

logger = logging.getLogger(name=__file__)



class CoreNotify:
        class Admin:
            def server_error(msg: str, locals):
                try:
                    # INFO :: Get JiGootsupport users
                    users = Customer.objects.filter(
                        dial_code='243', phone='975823671')
                    tokens = list(users.values_list('fcm', flat=True))
                    message = messaging.MulticastMessage(
                        android=messaging.AndroidConfig(priority='high'),
                        notification=messaging.Notification(
                            title="server error", body=msg,
                        ),
                        data={"locals": str(locals)},
                        tokens=tokens,
                    )
                    messaging.send_multicast(message)
                except Exception as e:
                    msg = formattedError(e)
                    logger.exception(msg)
