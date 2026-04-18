# from django.db import models


# class BaseVariant(models.Model):
#     index = models.PositiveSmallIntegerField(default=0)
#     name = models.CharField(
#         max_length=25, help_text="The variant otion or item portion"
#     )
#     weight = models.PositiveIntegerField(help_text="Grams")
#     volume = models.PositiveIntegerField(help_text="cm3")

#     class Meta:
#         abstract = True

#     def __str__(self):
#         return self.name
