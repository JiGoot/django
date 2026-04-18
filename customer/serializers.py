from customer.models.customer import Customer
from rest_framework.request import Request
from django.db.models.query import QuerySet


class CustomerSrz:
    '''[Customer] object(s) serialiser for [jigoot Eat app]'''
    class Customer:

        @staticmethod
        def default(data: object):
            def __default(obj: Customer):
                return {
                    'id': obj.id,
                    'name': obj.user.name,
                    'last_name': obj.user.last_name,
                    'gender': obj.user.gender,
                    'dial_code': obj.user.dial_code,
                    'phone': obj.user.phone,
                    'email': obj.user.email,
                }
            if isinstance(data, Customer):
                return __default(data)
            elif isinstance(data, QuerySet):
                if data.model == Customer:
                    return [__default(order) for order in data]
                raise ValueError("Requires Customer queryset")
            return None

    '''
    ------------------------------------------------------------
    ------------------------------------------------------------
    ------------------------------------------------------------
    '''
    class Branch:
        @staticmethod
        def default(data: object):
            def __default(obj: Customer):
                return {
                    'name': obj.user.name,
                    'dial_code': obj.user.dial_code,
                    'phone': obj.user.phone,
                }
            if isinstance(data, Customer):
                return __default(data)
            elif isinstance(data, QuerySet):
                if data.model == Customer:
                    return [__default(order) for order in data]
            return None

    class Courier:
        @staticmethod
        def default(data: object):
            return CustomerSrz.Branch.default(data)
