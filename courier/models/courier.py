import pytz
from common.base.token import AbstractToken
from core.utils import CourierStatus, formattedError, update_user_timestamp
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from courier.validators import CourierPasswordValidator
from core.utils import DashStatus
from core.managers import ObjectsManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import logging
from django.utils.functional import classproperty
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from core.rabbitmq.broker import publisher
from courier.apps import CourierConfig
from user.models import User

logger = logging.getLogger(__file__)

# when courier login the app their status will be set to either active if their scheduled shift have already started
#  or unavailable if their scheduled shift have not started yet

# the courier can take break, at any time and for as long as needed for as many time as desired , they should simply keep in mind that
# they might not receive or earn money during that time

# to interrupt or end an ongoing shift before it scheduled end time, by loging out of the app. Doing they are not going to be able to
# receive order and make money, it can also impact the dasher rating and elegibility to certain offer.

# teir is no predefine shift in doordash, giving dasher more controls


class Courier(models.Model):

    class Status:
        """NOTE We used integer value instead of str because we wouldd like to order first by open, busy, closed"""

        online = "online"
        paused = "paused"
        offline = "offline"

        @classproperty
        def choices(cls):
            return (
                (cls.online, "online"),
                (cls.paused, "paused"),
                (cls.offline, "offline"),
            )

        @classproperty
        def values(cls):
            return tuple(v for v, _ in cls.choices)

    user = models.OneToOneField(User, on_delete=models.RESTRICT, null=True)
    city = models.ForeignKey("common.City", on_delete=models.RESTRICT, related_name="couriers")

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.offline)
    can_dash_now = models.BooleanField(default=False)
    paused_at = models.DateTimeField(null=True, blank=True)
    max_load = models.PositiveSmallIntegerField(default=2)
    max_slots_per_day = models.IntegerField(default=5)
    max_slots_per_week = models.IntegerField(default=8)
    # trusted couriers can go up to 2.0, for example

    # --- GeoDjango specific-field ---
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    # INFO::  Perormance Metrics
    worthiness = models.FloatField(default=1.0)
    score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    rating = models.FloatField(default=5.0, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True, editable=False)
    fcm = models.CharField(max_length=250, null=True, blank=True, editable=False)

    objects = ObjectsManager()

    class Meta:
        ordering = ("city", "user__name", "user__last_name")

    @property
    def is_authenticated(self):
        return True

    @property
    def cached(self):
        """
        Importing inside the method is a valid and common way to avoid circular imports in Python.
        No performance issue. The import runs only once and is cached in sys.modules. The overhead of calling the method is negligible.
        """
        from courier.cached.courier import CachedCourier

        return CachedCourier(self)

    @property
    def max_debt(self):
        return self.city.debt_cap * self.worthiness

    @property
    def commission_rate(self):
        return 0.25

    """ NOTE password should always be set using [set_password]
    Define a method that sets the password for the courier. [make_password] taks a raw string as password and
    return its hashed string version using a one-way algorithm. this means that it is impossible to recover
    the original raw string password from the hashed string password. But it is possible to verify
    if a given raw string password is matches the hashed string pwd.
    This is done to protect the security and privacy of the password, as storing or displying the raw password would expose it to potential attackers or unauthorized users.
    NOTE [check_password] checks if the given password matches the courier's password
    """

    @property
    def is_online(self):
        if self.active_shift() and self.status == self.Status.online:
            return True
        return False

    def set_password(self, raw_pwd: str):
        """INFO:: Validate raw password and if valid set password into hash"""
        validator = CourierPasswordValidator()
        validator(raw_pwd)
        self.password = make_password(raw_pwd)

    def check_password(self, raw_pwd: str):
        if self.password:
            validator = CourierPasswordValidator()
            validator(raw_pwd)
            return check_password(raw_pwd, self.password)
        return False

    def active_shift(self):
        tz = pytz.timezone(self.city.timezone)  # e.g. "Africa/Kinshasa"
        local_now = timezone.now().astimezone(tz)
        return self.cached.shifts.filter(
            status=DashStatus.confirmed, start__lte=local_now, end__gte=local_now
        ).first()

    # TODO nex version add [activity] and [priority] metric has with yandex.pro

    def update_coords(self, lat, lng):
        """INFO:: Update courier location coords when courier is not offline
        This is used during orders dispatch process."""
        if self.status != self.Status.offline:
            self.lat = lat
            self.lng = lng
            self.save(update_fields=("lat", "lng"))

    """NOTE: Assign [order] to [courier]  while increasing [courier][load].
     TODO Do not forget to decrease [courier][load] when order is delivered"""

    """Bedian Average or Weighted Average"""

    def updateRating(self, vote):
        # [m] minimum number f votes required to reflete  the exact tendency of the peaple
        m = 100
        self.rating = (self.votes / (self.votes + m)) * vote + (m / (self.votes + m)) * self.rating
        self.votes += 1
        if self.rating < 3.5:
            # TODO Jigoot has the right to susppend the contract with the kitchen
            pass

    class Tasks:
        @staticmethod
        def update_last_seen(id: int, dt: str):
            update_user_timestamp(Courier, id, dt, "last_seen")


""" ---------------------------------------------------------------------------
    ---------------------------------------------------------------------------
                                # AUTHENTICATION
---------------------------------------------------------------------------
--------------------------------------------------------------------------- """


class CourierToken(AbstractToken):
    courier = models.OneToOneField(
        Courier, related_name="token", on_delete=models.CASCADE, verbose_name=_("User")
    )
    device = models.CharField(max_length=50, default="unknown", editable=False)
    fcm = models.CharField(max_length=255, null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = f"{CourierConfig.name}_token"
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
        ordering = ["used_at"]

    def __str__(self):
        return f"{self.courier} ➤ {self.device}"

    class Tasks:
        @staticmethod
        def update_used_at(key: str, dt: str):
            try:
                token = CourierToken.objects.get(key=key)
                timestamp = parse_datetime(dt)
                if timestamp is None:
                    logger.warning(f"Invalid datetime string '{dt}' for CustomerToken Key")
                    return
                if timestamp.tzinfo is None:
                    timestamp = make_aware(timestamp)

                token.used_at = timestamp
                token.save(update_fields=["used_at"])
            except CourierToken.DoesNotExist:
                logger.warning(f"CourierToken with key {key[:10]}... does not exist.")
            except Exception as e:
                logger.error(formattedError(e))

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
            now = timezone.now()
            publisher.publish(CourierToken.Tasks.update_used_at, self.courier.id, now.isoformat())
        return super().save(*args, **kwargs)
