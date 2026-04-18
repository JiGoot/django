from django.db import models


class NameField(models.CharField):
    '''
    Is for lower case char field
    '''
    def __init__(self, *args, **kwargs) -> None:
        super(NameField, self).__init__(*args, **kwargs)
    def get_prep_value(self, value):
        return str(value).lower