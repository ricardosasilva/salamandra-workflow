import logging
import uuid

from django.conf import settings
from django.db import models
from django_extensions.db.fields import ShortUUIDField

logger = logging.getLogger(__name__)


class DateLogMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @classmethod
    def send_and_log(cls, signal, sender=None, **kwargs):
        """Replacement for Signal.send_robust with logging"""
        sender = sender or cls.__class__
        rvs = signal.send_robust(sender=sender, **kwargs)
        for f, exc in rvs:
            if exc is not None:
                logger.error("signal handler %s failed on %r",
                             getattr(f, '__name__', f), cls,
                             exc_info=(type(exc), exc, exc.__traceback__))


class BaseModel(DateLogMixin):

    class Meta:
        abstract = True
        ordering = ('-created_at', )

    def __str__(self):
        return str(self.id)

    @property
    def short_id(self):
        return hashids.encode(int(self.pk))


class UUIDBaseModel(DateLogMixin):
    # uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    uuid = ShortUUIDField(unique=True)

    class Meta:
        abstract = True
        ordering = ('-created_at', )

    def __str__(self):
        return str(self.uuid)

    @property
    def short_id(self):
        return hashids.encode(int(self.uuid))


class ActiveMixin(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
