import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .base import UUIDBaseModel
from .state import State
from .task import Task

logger = logging.getLogger(__name__)


class ActivityManager(models.Manager):

    def create_from_config(self, state, slug, config):
        name = config.get('name')
        status = config.get('status')

        activity, created = super().get_or_create(state=state, slug=slug, defaults={'name': name})

        for activity_status in status:
            activity_status, created = ActivityStatus.objects.get_or_create(activity=activity, slug=activity_status, defaults={'name': status[activity_status]})

        return activity_status


class Activity(UUIDBaseModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=70)
    objects = ActivityManager()

    class Meta:
        verbose_name_plural = 'Activities'
        unique_together = [
            'slug', 'state'
        ]

    def __str__(self):
        return f'{self.name}'


class ActivityStatus(UUIDBaseModel):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='status')
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=70)
    
    class Meta:
        verbose_name_plural = 'Activities status'

    def __str__(self):
        return f'{self.name}'



class TaskActivity(UUIDBaseModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_activities')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='task_activities')
    status = models.ForeignKey(ActivityStatus, blank=True, null=True, on_delete=models.CASCADE, related_name='task_activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name='task_status_selected_by')
    datetime = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at',]
        unique_together = [
            'task', 'activity'
        ]
        verbose_name_plural = 'Task Activities'

    def __str__(self):
        return f'{self.pk} - {self.task} - {self.activity} - {self.status}'

    def clean(self):
        errors = {}

        if self.activity and self.activity.state.workflow_version != self.task.job.workflow_version:
            errors['activity'] = ValidationError(_('The activity must be one of the task states.'))

        if self.status and self.status.activity != self.activity:
            errors['status'] = ValidationError(_("The status must be one of the activity status."))

        if len(errors):
            raise ValidationError(errors)


@receiver(post_save, sender=Task)
def post_save_task(sender, instance, created, **kwargs):
    if created:
        # Create the activities for the task
        for activity in instance.state.activities.all():
            TaskActivity.objects.create(task=instance, activity=activity)
