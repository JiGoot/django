from datetime import timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
import logging
import requests

# from core.utils import get_random_pin
from django.core.cache import cache
from requests import Response
from core.utils import formattedError, get_random_pin

logger = logging.getLogger(name=__file__)


class OrangeConfig:
    """Pour envoyer un SMS à {{recipient_phone_number}}, vous devez simplement utiliser votre {{access_token}},
    indiquer le {{country_sender_number}} comme senderAddress dans le corps de la requête et au niveau de l'url avec votre code pays
    mais sans préfixe + ou 00 - un tableau avec les valeurs recommandées pour ce paramètre se trouve plus bas sur cette page.
    """

    auth_header = os.environ.get("SMSDRC_AUTH_HEADER")
    sender_numbers = {
        "243": "2430000",
    }

    class sms:
        base_url = "https://api.orange.com"
        endpoint = "/smsmessaging/v1/outbound/{senderAddress}/requests"

    @staticmethod
    def getAccessTokent():
        headers = {
            "Authorization": OrangeConfig.auth_header,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {
            "grant_type": "client_credentials",
        }
        _key = "orangeapi_access_token"
        try:
            access_token = cache.get(_key, None)
            if access_token is None:
                response = requests.post(
                    "https://api.orange.com/oauth/v3/token", headers=headers, data=data
                )
                if response.status_code == 200:
                    access_token = response.json()["access_token"]
                    expires_in = response.json().get("expires_in", 60 * 60)
                    cache.set(_key, access_token, expires_in)  # One hour
                else:
                    raise Exception(
                        f"Failed to get access token. Status code: {response.status_code}"
                    )
            return access_token
        except Exception as e:
            cache.delete(_key)
            logger.exception(f"Error getting access token: {e}")

    @staticmethod
    def sendMsg(access_token, csn, to, msg):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        data = {
            "outboundSMSMessageRequest": {
                # "senderName": "JiGoot",#
                "address": f"tel:{to}",
                "senderAddress": f"tel:+2430000",
                "outboundSMSTextMessage": {
                    "message": msg,
                },
            }
        }
        url = OrangeConfig.sms.base_url + OrangeConfig.sms.endpoint.format(
            senderAddress=f"tel:+{csn}"
        )
        response = requests.post(url, json=data, headers=headers)
        return response


class OTP:
    """
    Users with poor network or slow onboarding still complete signup.
    You avoid sending multiple OTPs per number → big cost reduction.
    Security risk is noticeably lower than 72h.
    Less friction than a 10–30 min expiry, which is often too strict in your market.
    If you later handle payments, you’ll want shorter OTP windows.
    """

    def __init__(self, dial_code: str, phone: str) -> None:
        self.dial_code = dial_code
        self.phone = phone

    @property
    def tel(self):
        return f"+{self.dial_code}{self.phone}"

    def msg(self, code: str):
        return f"Code OTP JiGoot (valable 48h): {code}. À garder secret."

    @property
    def cacheKey(self):
        return f"phone_otp::+{self.dial_code}{self.phone}"

    @staticmethod
    def send(dial_code, phone):
        try:
            otp = OTP(dial_code, phone)
            # Already sent → do not resend
            if cache.get(otp.cacheKey):
                return
            code = get_random_pin(length=5)

            sent = False

            # Try Orange first if number starts with Orange prefixes
            if otp.phone.startswith(("89", "85", "84", "80")):
                try:
                    response = Orange.sms.send(otp, code)
                    if response.status_code == 201:
                        sent = True
                    else:
                        raise Exception(
                            f"Orange OTP failed ({response.status_code}): {response.text}"
                        )
                except Exception as err:
                    logger.warning(
                        f"Orange SMS failed → fallback to Twilio: {formattedError(err)}"
                    )

            # Fallback or non-Orange numbers → Twilio
            if not sent:
                message = Twilio.sms.send(dial_code, phone, code)
                if message.status not in ("queued", "sending", "sent"):
                    raise Exception(f"Twilio OTP failed. Status: {message.status}")

            # Cache OTP after successful send
            cache.set(otp.cacheKey, code, timedelta(hours=48).total_seconds())

        except Exception as e:
            logger.error(formattedError(e))


class Orange:
    class sms:
        @staticmethod
        def send(otp: OTP, code: str, locale="fr"):
            """Use Orange SMS API endpoint and return a response else an exception will be raised"""
            access_token = OrangeConfig.getAccessTokent()
            csn = OrangeConfig.sender_numbers.get(otp.dial_code, None)
            assert access_token and csn, "Missing access token or sender number."
            response = OrangeConfig.sendMsg(
                access_token,
                csn,
                otp.tel,
                otp.msg(code),
            )
            return response


class Twilio:
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)
    messages = client.messages

    # verify = client.verify.v2.services(os.environ.get('TWILIO_VERIFY_SID'))

    class sms:
        @staticmethod
        def send(dial_code, phone, code: str):
            message = Twilio.messages.create(
                from_="+12495035083",
                to=f"+{dial_code}{phone}",
                body=f"Code OTP JiGoot (valable 48h): {code}. À garder secret.",
            )
            return message

        # @staticmethod
        # def veify(otp: OTP, code: str):
        #     try:
        #         result = Twilio.verify.verification_checks.create(
        #             to=otp.tel,
        #             code=code
        #         )
        #     except TwilioRestException:
        #         return False
        #     return result.status == 'approved'
