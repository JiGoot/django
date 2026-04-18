from django.db.models import QuerySet

from wallet.models.payout import Payout, PayoutMethod






class PayoutMethodSrz:
    @staticmethod
    def default(data: object):
        def __default(obj: PayoutMethod):
            return {
                'id': obj.pk,
                'provider': obj.provider.name,
                'currency': obj.provider.currency,
                'number': obj.number,
                'holder': obj.holder,
                'is_default': obj.is_default,
            }

        if isinstance(data, QuerySet) or isinstance(data, list):
            return [__default(payout) for payout in data]
        return __default(data)


class PayoutSrz:
    @staticmethod
    def default(data: object):
        def __default(obj: Payout):
            return {
                'id': obj.pk,
                'status': obj.status,
                'amount': obj.amount,
                'currency': obj.currency,
                'method': {
                    'provider': obj.provider,
                    'number': obj.number,
                    'holder': obj.holder,
                },
                'created_at': obj.created_at,
                'updated_at': obj.updated_at,
                'note': obj.note,
            }

        if isinstance(data, QuerySet) or isinstance(data, list):
            return [__default(payout) for payout in data]
        return __default(data)
