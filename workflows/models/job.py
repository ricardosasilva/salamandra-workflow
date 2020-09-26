from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import UUIDBaseModel
from .workflow import WorkflowVersion


class JobManager(models.Manager):

    def create_job(self, workflow_version, user, name='', data=None, activated_at=None):
        if not activated_at:
            activated_at = timezone.now()
        return super(JobManager, self).create(workflow_version=workflow_version, created_by=user, name=name, data=data, activated_at=activated_at)


class Job(UUIDBaseModel):
    """A job is a workflow instance."""
    activated_at = models.DateTimeField(default=timezone.now, help_text=_('Use to schedule jobs. The initial tasks only become active after this date and time.'))
    name = models.CharField(help_text=_('A text to help to identify the purpose of the job.'), max_length=50)
    workflow_version = models.ForeignKey(WorkflowVersion, on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    start_datetime = models.DateTimeField(blank=True, null=True)
    finish_datetime = models.DateTimeField(blank=True, null=True)
    data = JSONField(blank=True, null=True)
    objects = JobManager()

    class Meta:
        verbose_name = _('Job')
        verbose_name_plural = _('Jobs')

    @property
    def is_finished(self):
        return False

    def __str__(self):
        return self.name

    def clean(self):
        if not self.workflow_version.is_active:
            raise ValidationError(_('You need to select an active workflow version.'))

        if self.tasks.exists():
            job_state = self.tasks.first()
            if self.workflow_version != job_state.state.workflow_version:
                raise ValidationError(_('It is not possible to change the workflow version of a created job.'))
