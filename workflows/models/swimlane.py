from django.db import models
from django_extensions.db.fields import AutoSlugField

from .base import UUIDBaseModel


class Swimlane(UUIDBaseModel):
    name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from=['name',], editable=True)

    def __str__(self):
        return self.name
