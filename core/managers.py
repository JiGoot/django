from django.db import models

class ObjectsManager(models.Manager):
    def get_or_none(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            return None  
    
    
        
# class CouirerManager(ObjectsManager):
    
#     def get_or_none(self, *args, **kwargs):
#         try:
#             return self.get(*args, **kwargs)
#         except self.model.DoesNotExist:
#             return None  
    


