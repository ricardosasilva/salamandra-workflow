import importlib

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from .base import ActiveMixin, UUIDBaseModel


class Workflow(UUIDBaseModel, ActiveMixin):
    slug = models.SlugField(editable=True, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.slug


class WorkflowVersionQuerySet(models.QuerySet):

    def last_version(self, workflow):
        return self.filter(workflow=workflow).order_by('version').last()


class WorkflowVersionManager(models.Manager):
    pass


class WorkflowVersion(UUIDBaseModel, ActiveMixin):
    workflow = models.ForeignKey(Workflow, on_delete=models.PROTECT, related_name='versions')
    version = models.PositiveIntegerField(default=1)
    objects = WorkflowVersionManager.from_queryset(WorkflowVersionQuerySet)()

    class Meta:
        unique_together = [['workflow', 'version'] ]

    def __str__(self):
        return self.slug

    @property
    def get_class(self):
        workflow_module = settings.WORKFLOWS_WORKFLOWS.get(self.workflow.slug).get('versions').get(self.version)
        module_ = importlib.import_module(workflow_module)
        class_ = getattr(module_, 'Workflow')
        return class_

    @property
    def get_forms(self):
        workflow_class = self.get_class()

    @property
    def next_version(self):
        return WorkflowVersion.objects.filter(workflow=self.workflow, version__gt=self.version).first()

    @property
    def previous_version(self):
        return WorkflowVersion.objects.filter(workflow=self.workflow, version__lt=self.version).first()

    @property
    def slug(self):
        return '{}.v{}'.format(self.workflow.slug, self.version)

    def create_new_version(self):
        return WorkflowVersion.objects.create_new_version(workflow=self.workflow)
