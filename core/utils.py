import math
import time
from django.utils.functional import classproperty
import uuid
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django_redis import get_redis_connection  # Requires django-redis package
from django.core.cache import cache
from django.core.signing import TimestampSigner
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from datetime import datetime, timedelta
import os
import shutil
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
import random
import pytz
import logging
from core import settings

from typing import TYPE_CHECKING
from math import radians, sin, cos, sqrt, atan2
from geopy.distance import geodesic

logger = logging.getLogger(__name__)


"""
Use geodesic_haversine (geopy’s geodesic) if you want slightly more accurate distances over longer distances or irregular terrain.
Use your haversine function if you want faster calculation, and your distances are short (a few km in a city, which is typical for delivery).
For delivery ETA in a city: haversine is enough.
"""


class Logger:
    def __init__(self, path: str) -> None:
        self.path = path
        self.instance = logging.getLogger(__name__)

    def info(self, message: str) -> None:
        message = f"\033[96m{message}\033[0m"
        (print(message) if settings.DEBUG else self.instance.info(f"{self.path} | {message}"))

    def error(self, message: str) -> None:
        message = f"\033[91m{message}\033[0m"
        (print(message) if settings.DEBUG else self.instance.error(f"{self.path} | {message}"))

    def success(self, message: str) -> None:
        message = f"\033[92m{message}\033[0m"
        (print(message) if settings.DEBUG else self.instance.info(f"{self.path} | {message}"))

    def warning(self, message: str) -> None:
        message = f"\033[93m{message}\033[0m"
        (print(message) if settings.DEBUG else self.instance.warning(f"{self.path} | {message}"))


def geodesic_haversine(point1, point2):
    coords1 = (point1.y, point1.x)  # (lat, lon)
    coords2 = (point2.y, point2.x)
    return geodesic(coords1, coords2).km


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth in [m]"""
    R = 6371000  # meters

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def haversine_m(lat1, lon1, lat2, lon2):

    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))



def versioned_upload(base_path, instance, filename):
    '''Generate a versioned upload path for a file.'''
    ext = os.path.splitext(filename)[1].lower()
    if instance.pk:
        version = int(time.time()) 
        return f"{base_path}{instance.pk}_v{version}{ext}"
    else:
        return f"{base_path}temp/{uuid.uuid4().hex}{ext}"


# class classproperty:
#     def __init__(self, f):
#         self.f = f

#     def __get__(self, _, cls):
#         return self.f(cls)





class DashStatus:
    scheduled = "scheduled"
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"

    @classproperty
    def choices(cls):
        return (
            (cls.scheduled, "Scheduled"),
            (cls.active, "Active"),
            (cls.paused, "Paused"),
            (cls.completed, "Completed"),
            (cls.cancelled, "Cancelled"),
        )

    @classproperty
    def values(cls):
        return (cls.scheduled, cls.active, cls.paused, cls.completed, cls.cancelled)


class BrSupports:
    """NOTE We used integer value instead of str because we wouldd like to order first by open, busy, closed"""

    delivery = "delivery"
    pickup = "pickup"


class CountryCode:
    cd = "cd"

    @classproperty
    def choices(cls):
        return ((cls.cd, "CD"),)

    @classproperty
    def values(cls):
        return [
            cls.cd,
        ]


class Currency:
    cdf = "cdf"

    @classproperty
    def choices(cls):
        return ((cls.cdf, "CDF"),)

    @classproperty
    def values(cls):
        return [
            cls.cdf,
        ]


class OrderTiming:
    asap = "asap"
    scheduled = "scheduled"

    @classproperty
    def choices(cls):
        return (
            (cls.asap, "ASAP"),
            (cls.scheduled, "Scheduled"),
        )

    @classproperty
    def values(cls):
        return [cls.asap, cls.scheduled]


class OrderFulfillment:
    delivery = "delivery"
    self_pickup = "self-pickup"

    @classproperty
    def choices(cls):
        return (
            (cls.delivery, "Delivery"),
            (cls.self_pickup, "Self-Pickup"),
        )

    @classproperty
    def values(cls):
        return [cls.delivery, cls.self_pickup]


class CouponTypes:
    subtotal = "subtotal"
    delivery = "delivery"


class TranzMethods:
    cash = "cash"
    mpesa = "m-psea"
    airtel_money = "airtel_money"
    orange_money = "orange_money"


TRANZMETHODS_CHOICES = (
    (TranzMethods.cash, "Cash"),
    (TranzMethods.mpesa, "M-Pesa"),
    (TranzMethods.airtel_money, "Airtel Money"),
    (TranzMethods.orange_money, "Orange Money"),
)


class PayoutStatus:
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

    @classproperty
    def choices(cls):
        return (
            (cls.pending, "Pending"),
            (cls.completed, "Completed"),
            (cls.cancelled, "Cancelled"),
        )

    @classproperty
    def values(cls):
        return [cls.pending, cls.completed, cls.cancelled]


class Languages:
    en = "en"
    fr = "fr"


class ScheduleOffset:
    cdf = "cdf"
    usd = "usd"
    eur = "eur"


class Gender:
    male = "male"
    female = "female"

    @classproperty
    def choices(cls):
        return (
            (cls.male, "Male"),
            (cls.female, "Female"),
        )

    @classproperty
    def values(cls):
        return [cls.male, cls.female]


class DialCode:
    cd = "243"

    @classproperty
    def choices(cls):
        return ((cls.cd, "243"),)

    @classproperty
    def values(cls):
        return [
            cls.cd,
        ]


class CreditType:
    credit = "credit"  # For earnings, related to order fulfilment
    remit = "remit"  # courier cod return to store
    refund = "refund"  # money in

    @classproperty
    def choices(cls) -> tuple:
        return (
            (cls.credit, "Credit"),
            (cls.remit, "Remit"),
            (cls.refund, "Refund"),
        )

    @classproperty
    def values(cls) -> tuple:
        return (
            cls.credit,
            cls.remit,
            cls.refund,
        )


class DebitType:
    commission = "commission"
    debit = "debit"  # money out
    collect = "debt"  # courier cod collect
    fee = "fee"  # Provider fee during payout
    payout = "payout"
    penalty = "penalty"
    sms = "sms"
    withdrawal = "withdrawal"

    @classproperty
    def choices(cls):
        return (
            (cls.commission, "Commission"),
            (cls.debit, "Debit"),
            (cls.collect, "Collect"),
            (cls.payout, "Payout"),
            (cls.penalty, "Penalty"),
            (cls.withdrawal, "Withdrawal"),
        )

    @classproperty
    def values(cls):
        return (
            cls.commission,
            cls.debit,
            cls.collect,
            cls.payout,
            cls.penalty,
            cls.withdrawal,
        )


class Issuers:
    kitchen = "B"
    customer = "C"
    courier = "D"  # Dasher
    platform = "P"


class CancelledBy:
    customer = "customer"
    branch = "branch"
    support = "support"
    system = "system"

    @classproperty
    def choices(cls):
        return (
            (cls.customer, "Customer"),
            (cls.branch, "Branch"),
            (cls.support, "Support"),
            (cls.system, "System"),
        )

    @classproperty
    def values(cls):
        return tuple(v for v, _ in cls.choices)



class CancelledReason:
    out_of_stock = "out of stock"
    customer_request = "customer request"
    unreachable_customer = "unreachable customer"
    delivery_failure = "delivery failure"
    payment_failure = "payment failure"
    suspected_fraud = "suspected fraud"
    system_error = "system error"
    other = "other"

    @classproperty
    def choices(cls):
        return (
            (cls.out_of_stock, "Out of Stock"),
            (cls.customer_request, "Customer Request"),
            (cls.unreachable_customer, "Unreachable Customer"),
            (cls.delivery_failure, "Delivery Failure"),
            (cls.payment_failure, "Payment Failure"),
            (cls.suspected_fraud, "Suspected Fraud"),
            (cls.system_error, "System Error"),
            (cls.other, "Other"),
        )

    @classproperty
    def values(cls):
        return (
            cls.out_of_stock,
            cls.customer_request,
            cls.unreachable_customer,
            cls.delivery_failure,
            cls.payment_failure,
            cls.suspected_fraud,
            cls.system_error,
            cls.other,
        )


class OfferStatus:
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

    @classproperty
    def choices(cls):
        return (
            (cls.pending, "Pending"),
            (cls.accepted, "Accepted"),
            (cls.rejected, "Rejected"),
        )

    @classproperty
    def values(cls):
        return (
            cls.pending,
            cls.accepted,
            cls.rejected,
        )


class SubstitutionPref:
    skip = "skip"
    cancel = "cancel"  # Cancel the entire order (on item unavailable, only for OrderItem level)
    best_match = "best_match"
    selection = "selection"  # Substitution will occur from selected alternative

    @classproperty
    def choices(cls):
        return (
            (cls.skip, "Skip"),
            (cls.cancel, "Cancel"),
            (cls.best_match, "Best Match"),
            (cls.selection, "Selection"),
        )

    @classproperty
    def values(cls):
        return (
            cls.skip,
            cls.cancel,
            cls.best_match,
            cls.selection,
        )


class WalletType:
    customer = "customer"
    courier = "courier"
    merchant = "merchant" # or supplier

    @classproperty
    def choices(cls):
        return ((cls.customer, "Customer"),
            (cls.courier, "Courier"),
            (cls.merchant, "Merchant"),
        )

    @classproperty
    def values(cls):
        return tuple(v for v, _ in cls.choices)


class AppType:
    branch = "branch"
    courier = "courier"
    customer = "customer"

    @classproperty
    def choices(cls):
        return (
            (cls.branch, "Branch"),
            (cls.courier, "Courier"),
            (cls.customer, "Customer"),
        )

    @classproperty
    def values(cls):
        return (cls.branch, cls.courier, cls.customer)


class AppOs:
    android = "android"
    ios = "ios"
    # web = 'web'

    @classproperty
    def choices(cls):
        return ((cls.android, "Android"), (cls.ios, "IOS"))

    @classproperty
    def values(cls):
        return (cls.android, cls.ios)


class ReleaseStages:
    dev = "dev"
    alpha = "alpha"
    beta = "beta"
    stable = "stable"

    @classproperty
    def choices(cls):
        return (
            (cls.dev, "Dev"),
            (cls.alpha, "Alpha"),
            (cls.beta, "Beta"),
            (cls.stable, "Stable"),
        )

    @classproperty
    def values(cls):
        return (cls.dev, cls.alpha, cls.beta, cls.stable)


class ReleaseChannels:
    app_store = "app-store"
    play_store = "play-store"
    shorebird = "shorebird"

    @classproperty
    def choices(cls):
        return (
            (cls.app_store, "App store"),
            (cls.play_store, "Play store"),
            (cls.shorebird, "Shorebird"),
        )

    @classproperty
    def values(cls):
        return tuple(v for v, _ in cls.choices)







class CommissionType:
    fixed = "fixed"
    percent = "percent"

    @classproperty
    def choices(cls):
        return (
            (cls.fixed, "Fixed"),
            (cls.percent, "Percent"),
        )

    @classproperty
    def values(cls):
        return (cls.fixed, cls.percent)


class CourierStatus:
    """NOTE We used integer value instead of str because we wouldd like to order first by online, busy, closed"""

    online = "online"
    paused = "paused"
    offline = "offline"

    @classproperty
    def choices(cls):
        return (
            (cls.online, "Online"),
            (cls.paused, "Paused"),
            (cls.offline, "Offline"),
        )

    @classproperty
    def values(cls):
        return (cls.online, cls.paused, cls.offline)


class ShareType:
    fixed = "fixed"
    percent = "percent"

    @classproperty
    def choices(cls):
        return (
            (cls.fixed, "Fixed Amount"),
            (cls.percent, "Percent"),
        )

    @classproperty
    def values(cls):
        return (cls.fixed, cls.percent)


class StockMovementType:
    class Inflow:
        consign_in = "consign-in"  # Stock received on consignment basis from a consignor.
        customer_return = "customer-return"  # Returned by customer (e.g. wrong item, defective, damaged )
        production_in = "production-in"  # Manufactured in-house (kitchen)
        release = "release"  # Cancelled reservation (put back into availability)
        restock = "restock"  # Normal restocking by the platform / consignor
        transfer_in = "transfer-in"  # Stock received by the new owner / consignor / branch.

        @classproperty
        def choices(cls):
            return (
                (cls.consign_in, "Consign In"),
                (cls.customer_return, "Customer Return"),
                (cls.production_in, "Production In"),
                (cls.release, "Release"),
                (cls.restock, "Restock"),
                (cls.transfer_in, "Transfer In"),
            )

        @classproperty
        def values(cls):
            return (
                cls.consign_in,
                cls.customer_return,
                cls.production_in,
                cls.release,
                cls.restock,
                cls.transfer_in,
            )

    class Outflow:
        consign_out = "consign-out"  # Stock return to the consignor. TODO:: when or under which circumstances should we allow this?
        damage = "damage"  # unusable goods scrapped / expired
        donation = "donation"  # Donated to charity or non-profit
        loss = "loss"  # Theft or other unexplained loss
        reserve = "reserve"  # Reserved but not yet sold (temporary hold)
        sale = "sale"  # Sold to customer
        sample = "sample"  # Free issue for promotion/merchandising
        transfer_out = "transfer-out"  # Stock sent out by the current owner / consignor / branch.

        @classproperty
        def choices(cls):
            return (
                (cls.consign_out, "Consign Out"),
                (cls.damage, "Damage"),
                (cls.donation, "Donation"),
                (cls.loss, "Loss"),
                (cls.reserve, "Reserve"),
                (cls.sale, "Sale"),
                (cls.sample, "Sample"),
                (cls.transfer_out, "Transfer Out"),
            )

        @classproperty
        def values(cls):
            return (
                cls.consign_out,
                cls.damage,
                cls.donation,
                cls.loss,
                cls.reserve,
                cls.sale,
                cls.sample,
                cls.transfer_out,
            )

    class Neutral:
        adjustment = "adjustment"  # Manual correction, reconciliation, or stocktake fix
        rollup = "rollup"  # Aggregated movements used for data consolidation; does not affect daily operations but keeps stock consistent.

        @classproperty
        def choices(cls):
            return ((cls.adjustment, "Adjustment"), (cls.rollup, "Rollup"))

        @classproperty
        def values(cls):
            return (cls.adjustment, cls.rollup)

    @classproperty
    def choices(cls):
        return cls.Inflow.choices + cls.Outflow.choices + cls.Neutral.choices

    @classproperty
    def values(cls):
        return cls.Inflow.values + cls.Outflow.values + cls.Neutral.values


class Timezones:
    kinshasa = "Africa/Kinshasa"

    @classproperty
    def choices(cls):
        return ((cls.kinshasa, cls.kinshasa),)

    @classproperty
    def values(cls):
        return (cls.kinshasa,)





class Weekday:
    """ISO (1=Monday, 7=Sunday)"""

    monday = 1
    tuesday = 2
    wednesday = 3
    thursday = 4
    friday = 5
    saturday = 6
    sunday = 7

    @classproperty
    def maps(cls):
        return {
            cls.monday: "Monday",
            cls.tuesday: "Tuesday",
            cls.wednesday: "Wednesday",
            cls.thursday: "Thursday",
            cls.friday: "Friday",
            cls.saturday: "Saturday",
            cls.sunday: "Sunday",
        }

    @classproperty
    def choices(cls):
        return (
            (cls.monday, cls.maps[cls.monday]),
            (cls.tuesday, cls.maps[cls.tuesday]),
            (cls.wednesday, cls.maps[cls.wednesday]),
            (cls.thursday, cls.maps[cls.thursday]),
            (cls.friday, cls.maps[cls.friday]),
            (cls.saturday, cls.maps[cls.saturday]),
            (cls.sunday, cls.maps[cls.sunday]),
        )

    @classproperty
    def values(cls):
        return (
            cls.monday,
            cls.tuesday,
            cls.wednesday,
            cls.thursday,
            cls.friday,
            cls.saturday,
            cls.sunday,
        )


def normalize_email(email):
    """
    Normalize the email address by lowercasing the domain part of it.
    """
    email = email or ""
    try:
        email_name, domain_part = email.strip().rsplit("@", 1)
    except ValueError:
        pass
    else:
        email = email_name + "@" + domain_part.lower()
    return email


def delete_image_utility(instance):
    if instance.image:
        # enough for deleting cloud base file (AWS S3)
        instance.image.delete(save=False)
        # required if file exist locally
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if media_root and os.path.exists(media_root):
            try:
                root = os.path.dirname(os.path.dirname(__file__))
                shutil.rmtree(root + instance.image)
            except Exception as e:
                logger.exception(formattedError(e))


"""
NOTE A regular expression (regex) is a sequence of characters that defines a 
search pattern is [r] before the string
- (?=.*[a-z]) atleast one char should be a latin lowercase
- (?=.*[A-Z]) atleast one char should be a latin uppercase
- (?=.*[0-9]) atleast one char should be a digit
- (?=.*[!@#$&%*~?]) atleast one char should belong to the special charaters given list
- [a-zA-Z0-9]{8,} insure that string is at least 8 characters. And all character 
should belong to abc...xyzABC...XYZ01...789 !@#$&%*~?
"""


# def string_to_list(string: str):
#     """NOTE: Clean a string list representation, by replacing comma and type(s) with only comma."""
#     pattern = r"\s*,\s*"
#     replace_with = ","
#     # NOTE replace each pattern spaces-comma-spaces with simply comma
#     return re.sub(pattern, replace_with, string).strip().split(',')


def distance(x1, y1, x2, y2):
    """Calculating distance. This remove the complexity of having to have and manage spatial database
    1 = 111 km
    0.1 = 11.1km
    0.01 = 1.11km
    0.001 = 0.111km
    0045 = 0.5km"""
    if x1 != None or x1 != None or y1 != None or y2 != None:
        # this is 1.11km in degrees. By dividing distance with [r] we get distance as a multiple of [r]
        r = 0.01
        return (((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 / r) * 1.11
    return None


"""
    [duration] is express in sec
"""


"""In order to do not interrupt the server when error occured, we make use of "try except" syntax bloc.
But when it does occured the "try except" catch that exception and thus we can make use of to ease debug."""


# def formattedError(e: Exception):
#     return f"{e} -> {e.__traceback__.tb_frame.f_code.co_filename} in line {e.__traceback__.tb_lineno}."


def formattedError(e: Exception):
    # Get the absolute path of the file where the exception occurred
    absolute_path = e.__traceback__.tb_frame.f_code.co_filename
    # Convert to a relative path based on the current working directory
    relative_path = os.path.relpath(absolute_path, os.getcwd())
    # Format the error message
    return f">>> {e} -> {relative_path} in line {e.__traceback__.tb_lineno}."


def get_random_code():
    # Seconds since midnight
    now = datetime.now()

    # Day of month (1-31) and seconds since midnight
    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
    time_component = (now.day << 17) + seconds_since_midnight  # shift day to avoid overlap

    # Hex representation, trimmed leading zeros
    time_hex = f"{time_component:X}"

    # 3-character random block
    rand_block = random_alphanumeric_string(3)

    # Combine with dash
    return f"{rand_block}-{time_hex}"


def get_random_pin(length=6):
    # choose from all lowercase letter
    letters = "0123456789"
    # +''.join(random.choice(string.digits) for i in range(3))
    pin = "".join(random.choice(letters) for i in range(length))
    return pin


def random_alphanumeric_string(length=2):
    # choose from all lowercase letter
    # "A0HBR1QC2DF3EV4F5GWT6HAX7UI8JB9KZ9LY8M7N6O5P4MQ3R2KS1T0UVWXYZ"
    letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ"  # withou `O` to avoid confusion with `0`
    # +''.join(random.choice(string.digits) for i in range(3))
    code = "".join(random.choice(letters) for i in range(length))
    return code


def getDeviceUtcOffset(request, format="%Y-%m-%dT%H:%M:%S.%fZ"):
    """INFO:: Return how accurate the request UTC is from the server UTC,
    If the request header missing utc, return"""
    _utc = request.META.get("HTTP_UTC", None)
    if _utc:
        offset = timezone.now() - datetime.strptime(_utc, format).replace(tzinfo=pytz.utc)
        return offset.total_seconds()


# NOTE:: We avoid using the extension in the path to avoid
# duplicate when the image is apdated with one of an other format
# Supported formate are : PNG, JPG, JPEG, WEBP, GIF(affiche only)


# NOTE:: Keep in mind that both customer courier
# can move from a city to an other from a country to an other.


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name


def verify_email_token(token):
    signer = TimestampSigner()
    try:
        signed_email = force_str(urlsafe_base64_decode(token))
        email = signer.unsign(signed_email, max_age=timedelta(hours=48).total_seconds())
        return email
    except Exception:
        return None  # Handle invalid token case


def verify_password_reset_token(token, max_age=3600):  # max_age in seconds (e.g. 1 hour)
    signer = TimestampSigner()

    try:
        signed_value = force_str(urlsafe_base64_decode(token))
        email = signer.unsign(signed_value, max_age=max_age)

        # Check the prefix
        if not email:
            return None

        # Return the email without the prefix
        return email

    except (BadSignature, SignatureExpired):
        return None


# TODO:: Have a button to clear cache in the dashboar


def clear_wallet_caches():
    """
    Deletes all Redis keys starting with 'wallet_'.
    """
    redis = get_redis_connection("default")  # Uses your Django cache settings
    cursor = "0"
    while cursor != 0:
        cursor, keys = redis.scan(cursor=cursor, match="wallet_*")  # Pattern to match
        if keys:
            redis.delete(*keys)
    return True


logger = logging.getLogger(__name__)


def update_user_timestamp(model_class, id: int, dt: str, field: str):
    label = model_class.__name__
    try:
        instance = model_class.objects.get(id=id)
        timestamp = parse_datetime(dt)
        if timestamp is None:
            logger.warning(f"Invalid datetime string '{dt}' for {label} ID {id}")
            return
        if timestamp.tzinfo is None:
            timestamp = make_aware(timestamp)

        setattr(instance, field, timestamp)
        instance.save(update_fields=[field])
    except model_class.DoesNotExist:
        logger.warning(f"{label} with ID {id} does not exist.")
    except Exception as e:
        logger.error(formattedError(e))
