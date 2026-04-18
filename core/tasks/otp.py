# from datetime import datetime, timedelta
# import logging

# from common.models.otp_request import OtpRequest, RequestedBy
# from core import verify
# from core.utils import Currency, TranzTypes, formattedError, get_random_pin
# from courier.models import Courier, CourierTransaction, CourierWallet
# from django.core.exceptions import ValidationError
# from django.core.cache import cache 
# logger = logging.getLogger(__file__)
# SMS_OTP_COST = 0.1


# class OTP:
#     def __init__(self, dial_code: str, phone: str) -> None:
#         self.dial_code = dial_code
#         self.phone = phone

#     @property
#     def tel(self):
#         return f"+{self.dial_code}{self.phone}"

#     @property
#     def cacheKey(self):
#         '''
#         Key used for caching the OTP code. 
#         The telephone should have the following format +243975823671
#         '''
#         return f'otp__{self.tel}'
    