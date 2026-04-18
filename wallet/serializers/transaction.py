from django.db.models import QuerySet
from wallet.models.transaction import Transaction


class TransactionSrz:
    @staticmethod
    def default(data: object):
        def __default(obj: Transaction):
            return {
                "id": obj.id,
                "type": obj.type,
                "amount": obj.amount, 
                "currency": obj.currency,
                "gateway": obj.gateway,  
                "reference": obj.reference,
                "created_at": obj.created_at,
            }
        if isinstance(data, Transaction):
            return __default(data)
        elif isinstance(data, QuerySet) or isinstance(data, list):
            return [__default(tranz) for tranz in data]
