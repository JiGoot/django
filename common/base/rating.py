from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.managers import ObjectsManager

class BaseRating(models.Model):
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    objects = ObjectsManager()
    # TODO, next version add a image field , which customer can show a visual prof off what they are saying  
    

    class Meta:
        abstract = True