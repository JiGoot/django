# from branch.models.category import BranchCategory
# from django.db.models.query import QuerySet


# class BranchCategorySrz:
#     class Customer:
#         @staticmethod
#         def default(data: object):
#             def __default(obj: BranchCategory):
#                 serialized = {
#                     "id": obj.id,
#                     "name": obj.supplier_category.category.name,
#                     "image": obj.supplier_category.category.image,
#                     "is_active": obj.is_active,
#                 }
#                 return serialized

#             if isinstance(data, BranchCategory):
#                 return __default(data)
#             elif isinstance(data, QuerySet) or isinstance(data, list):
#                 return [__default(obj) for obj in data]
