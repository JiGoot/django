# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import datetime
import firebase_admin
from core import settings
from firebase_admin import messaging, credentials

# if not firebase_admin._apps:
#     cred = credentials.Certificate(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
#     firebase_admin.initialize_app(cred)


# def send_to_token(message: messaging.Message):
#     '''
#     Send a Single message to a single device usin device unique token
#     This [registration_token] comes from the client FCM SDKs.
#     '''

#     # try:
#     # Send a message to the device corresponding to the provided
#     # registration token.
#     response = messaging.send(message)
#     # Response is a message ID string.
#     return response


def send_to_topic(topic: str, **kwargs):
    # [START send_to_topic]
    # The topic name can be optionally prefixed with "/topics/".

    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=kwargs['notification'],
        data=kwargs['data'],
        topic=topic,
    )

    # Send a message to the devices subscribed to the provided topic.
    response = messaging.send(message)
    # [END send_to_topic]


def send_to_condition():
    # [START send_to_condition]
    # Define a condition which will send to devices which are subscribed
    # to either the Google stock or the tech industry topics.
    condition = "'stock-GOOG' in topics || 'industry-tech' in topics"

    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=messaging.Notification(
            title='$GOOG up 1.43% on the day',
            body='$GOOG gained 11.80 points to close at 835.67, up 1.43% on the day.',
        ),
        condition=condition,
    )

    # Send a message to devices subscribed to the combination of topics
    # specified by the provided condition.
    response = messaging.send(message)


def send_dry_run():
    message = messaging.Message(
        data={
            'score': '850',
            'time': '2:45',
        },
        token='token',
    )

    # [START send_dry_run]
    # Send a message in the dry run mode.
    response = messaging.send(message, dry_run=True)


def android_message():
    # [START android_message]
    message = messaging.Message(
        android=messaging.AndroidConfig(
            ttl=datetime.timedelta(seconds=3600),
            priority='normal',
            notification=messaging.AndroidNotification(
                title='$GOOG up 1.43% on the day',
                body='$GOOG gained 11.80 points to close at 835.67, up 1.43% on the day.',
                icon='stock_ticker_update',
                color='#f45342'
            ),
        ),
        topic='industry-tech',
    )
    # [END android_message]
    return message


def apns_message():
    # [START apns_message]
    message = messaging.Message(
        apns=messaging.APNSConfig(
            headers={'apns-priority': '10'},
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(
                        title='$GOOG up 1.43% on the day',
                        body='$GOOG gained 11.80 points to close at 835.67, up 1.43% on the day.',
                    ),
                    badge=42,
                ),
            ),
        ),
        topic='industry-tech',
    )
    # [END apns_message]
    return message


def webpush_message():
    # [START webpush_message]
    message = messaging.Message(
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title='$GOOG up 1.43% on the day',
                body='$GOOG gained 11.80 points to close at 835.67, up 1.43% on the day.',
                icon='https://my-server/icon.png',
            ),
        ),
        topic='industry-tech',
    )
    # [END webpush_message]
    return message


def all_platforms_message():
    # [START multi_platforms_message]
    message = messaging.Message(
        notification=messaging.Notification(
            title='$GOOG up 1.43% on the day',
            body='$GOOG gained 11.80 points to close at 835.67, up 1.43% on the day.',
        ),
        android=messaging.AndroidConfig(
            ttl=datetime.timedelta(seconds=3600),
            priority='normal',
            notification=messaging.AndroidNotification(
                icon='stock_ticker_update',
                color='#f45342'
            ),
        ),
        apns=messaging.APNSConfig(

            payload=messaging.APNSPayload(
                aps=messaging.Aps(badge=42),
            ),
        ),
        topic='industry-tech',
    )
    # [END multi_platforms_message]
    return message


'''
[START subscribe]
These registration tokens come from the client FCM SDKs.
'''


def subscribe_to_topic(topic: str, registration_tokens: list = []):
    # Subscribe the devices corresponding to the registration tokens to the
    # topic.
    response = messaging.subscribe_to_topic(registration_tokens, topic)


'''
[START unsubscribe]
These registration tokens come from the client FCM SDKs.
'''


def unsubscribe_from_topic(topic: str, registration_tokens: list = []):
    # Unubscribe the devices corresponding to the registration tokens from the
    # topic.
    response = messaging.unsubscribe_from_topic(registration_tokens, topic)
    # See the TopicManagementResponse reference documentation
    # for the contents of response.


'''
Send a list of messages to 
'''


def send_all(registration_token):
    # registration_token = 'YOUR_REGISTRATION_TOKEN'
    # [START send_all]
    # Create a list containing up to 500 messages.
    messages = [

        # by token
        messaging.Message(
            notification=messaging.Notification(
                title='Price drop', body='5% off all electronics', image=None),
            token=registration_token,
        ),
        # by topic subscripption
        messaging.Message(
            notification=messaging.Notification(
                'Price drop', '2% off all books'),
            topic='readers-club',
        ),
    ]

    response = messaging.send_all(messages)


'''
[START send_multicast]
Create a list containing up to 500 registration tokens.
These registration tokens come from the client FCM SDKs
'''


def send_multicast(registration_tokens: list, notification: None, data: dict = {}):

    message = messaging.MulticastMessage(
        notification=notification,
        data=data,
        tokens=registration_tokens,
    )
    response = messaging.send_multicast(message)
    return response.success_count


def send_multicast_and_handle_errors():
    # [START send_multicast_error]
    # These registration tokens come from the client FCM SDKs.
    registration_tokens = [
        'YOUR_REGISTRATION_TOKEN_1',
        # ...
        'YOUR_REGISTRATION_TOKEN_N',
    ]

    message = messaging.MulticastMessage(
        data={'score': '850', 'time': '2:45'},
        tokens=registration_tokens,
    )
    response = messaging.send_multicast(message)
    if response.failure_count > 0:
        responses = response.responses
        failed_tokens = []
        for idx, resp in enumerate(responses):
            if not resp.success:
                # The order of responses corresponds to the order of the registration tokens.
                failed_tokens.append(registration_tokens[idx])


'''
    Placed
        "title": "Order #37 Placed ✔️",
        "body": "Hi John, your order has been successfully placed. Thank you for choosing us! 😊"
    Accepted
        "title":  "Order #37 Accepted ⏰",
        "body": "Great news! Your order has been accepted and is being processed. We’ll let you know when it’s ready."
    Ready
        "title":  "Order #37 Ready 🍽️",
        "body": "Your order is now ready for pickup or delivery. Enjoy your meal! 😋"
    Picked-up
        "title":  "Order #37 Picked Up 🚗",
        "body": "Your order has been picked up and is on its way to you. It should arrive in about 15 minutes."
    Arrived
        "title":  "Order #37 Arrived 🏠",
        "body": "Your order has arrived. Please be ready to receive it. Bon appétit! 🍽️"
    Delivered
        "title":  "Order #37 Delivered 🎉",
        "body": "Congratulations! Your order has been successfully delivered. We hope you enjoyed it. 😊"

    Cancelled
        "title":  "Order #37 Cancelled ❌",
        "body": "We’re sorry to inform you that your order has been cancelled. Please contact customer support for assistance. 😢"
'''
