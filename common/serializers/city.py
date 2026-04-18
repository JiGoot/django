from django.db.models.query import QuerySet
from common.models import City, Slot, Gateway, Zone
from common.models.gateway import Gateway
from typing import Optional, Union


class CitySrz:

    @staticmethod
    def default(data: object):
        def __default(obj: City):
            return {
                "id": obj.pk,
                "name": obj.name,
                "country_code": obj.country.code,
                "currency": obj.currency,
                "smallest_bill": obj.smallest_bill,
                "small_order": {
                    "threshold": obj.small_order_threshold,
                    "fee": obj.small_order_fee,
                },
                # TODO:: `"delivery"` is deprecated and replaced by `"delivery_fee"`
                # since v5.2.3+43
                "delivery": {
                    "base_fee": obj.delivery_fee_base_amount,
                    "cap_amount": obj.delivery_fee_cap_amount,
                    "cpm": obj.delivery_fee_cpm,
                    "cpk": obj.delivery_fee_cpk,
                },
                "delivery_fee": {
                    "base_amount": obj.delivery_fee_base_amount,
                    "cap_amount": obj.delivery_fee_cap_amount,
                    "cpm": obj.delivery_fee_cpm,
                    "cpk": obj.delivery_fee_cpk,
                },
                "service_fee": {
                    "rate": obj.service_fee_rate,
                    "cap_amount": obj.service_fee_cap_amount,
                },
                "bbox": obj.bbox,
            }

        if isinstance(data, City):
            return __default(data)
        elif isinstance(data, (list, QuerySet)):
            if all(isinstance(obj, City) for obj in data):
                return [__default(obj) for obj in data]
