from rest_framework.request import Request
from .models import Affiche
from django.db.models.query import QuerySet
from typing import Optional, Union
from rest_framework import serializers

class AfficheSrz:
     class Customer (serializers.ModelSerializer):
        class Meta:
            model = Affiche
            fields = ["id", "name", "image"]


        
    
    
    # class Customer:
    #     @staticmethod
    #     def default(data: object) -> Union[dict, list]:
    #         def __default(obj: Affiche):
    #             return {
    #                 "id": obj.pk,
    #                 "name": obj.name,
    #                 "image": obj.image.url,
    #                 # "start": obj.start.isoformat() if obj.start else None,
    #                 # "end": obj.end.isoformat() if obj.end else None,
    #             }

    #         if isinstance(data, Affiche):
    #             return __default(data)
    #         elif isinstance(data, QuerySet) or isinstance(data, list):
    #             return [__default(obj) for obj in data]
