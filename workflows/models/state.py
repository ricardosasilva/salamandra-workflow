import datetime
import importlib
import logging

import humanize
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from .base import UUIDBaseModel
from .swimlane import Swimlane
from .workflow import WorkflowVersion


logger = logging.getLogger(__name__)


class State(UUIDBaseModel):
    workflow_version = models.ForeignKey(WorkflowVersion, on_delete=models.PROTECT, related_name='states')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(editable=True)
    swimlanes = models.ManyToManyField(Swimlane, related_name='states', blank=True)
    class_name = models.CharField(max_length=255, help_text=_('Name of python class with the code to evaluate state transition.'))
    due_time = models.PositiveIntegerField(help_text=_("Task's due time in minutes."))
    due_time_warning = models.PositiveIntegerField(help_text=_('Time in minutes after the task creation to put it on warning status.'))
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    max_unassigned_time = models.PositiveIntegerField(help_text=_('Max time, in minutes, the task may reamin unassigned.'))
    max_unassigned_time_warning = models.PositiveIntegerField(help_text=_('Max time, in minutes, the task may reamin unassigned before it\'s status is set to warning.'))
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [['workflow_version', 'class_name'], ['workflow_version', 'slug']]

    def __str__(self):
        return '{} - {}'.format(self.workflow_version.workflow.description, self.name)

    @property
    def due_time_humanized(self):
        return humanize.naturaldelta(datetime.timedelta(minutes=self.due_time))

    @property
    def due_time_warning_humanized(self):
        return humanize.naturaldelta(datetime.timedelta(minutes=self.due_time_warning))


    @property
    def get_class(self):
        module = '.'.join(self.class_name.split('.')[:-1])
        class_name = self.class_name.split('.')[-1]
        module_ = importlib.import_module(module)
        class_ = getattr(module_, class_name)
        return class_

    def next(self, data={}, task=None):
        # Get next states  by calling the subclass State class next() method (The one you defined on your class)
        next_state_classes = self.get_class().next(data=data, task=task)
        next_states = []
        for state_class in next_state_classes:
            try:
                from workflows.workflow import State as WorkflowState
                if isinstance(state_class, dict):
                    class_name = state_class.get('state')().fullname
                    activated_at = state_class.get('activated_at', timezone.now())
                    additional_due_time = state_class.get('additional_due_time', 0)
                elif issubclass(state_class, WorkflowState):
                    class_name = state_class().fullname
                    activated_at = timezone.now()
                    additional_due_time = 0
                else:
                    logger.error('The returned state must be a dict or a subclass of State')
                    raise Exception('The returned state must be a dict or a subclass of State')

                next_state = State.objects.get(workflow_version=self.workflow_version, class_name=class_name)
                next_states.append({'state': next_state, 'activated_at': activated_at, 'additional_due_time': additional_due_time})
            except Exception as e:
                logger.exception('Error creating next state')
                logger.exception(e)

        return next_states

    def required_states(self):
        required = self.get_class().required
        classes = [name().fullname for name in required]
        return State.objects.filter(workflow_version=self.workflow_version, class_name__in=classes)
