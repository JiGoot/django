# import os
# import time
# import uuid
# from common.models.boundary.country import Country
# from django.utils.translation import gettext_lazy as _
# import logging
# from django.db import models
# from common.models.catalog.category import Category
# from common.models.catalog.item import Item

# logger = logging.getLogger(__name__)


# # Shelf are store , store_category  and store based, 
# TODO:: Collection is country based and could be overwitten to be city based 
# class Collection(models.Model):
#     IMAGE_PATH = "store/shelves/"

#     index = models.PositiveSmallIntegerField(default=0, help_text="Display order")
#     name = models.CharField(max_length=50, unique=True)
#     category = models.OneToOneField(Category, on_delete=models.RESTRICT, null=True)
#     description = models.CharField(max_length=250)
#     is_active = models.BooleanField(default=True, help_text="Whether the collection is visible")


#     def __str__(self):
#         return self.name


# class CollectionItem(models.Model):
#     collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='collitems')
#     src = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='collitems')
#     index = models.PositiveSmallIntegerField(default=0)  # Ordering of item within collection

#     class Meta:
#         unique_together = ['collection', 'src']
#         ordering = ['index']
