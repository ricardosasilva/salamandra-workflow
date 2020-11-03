import datetime

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from workflows.signals import job_finished, task_created, task_finished
from workflows.utils import add_workday

from .base import UUIDBaseModel
from .job import Job
from .state import State


@receiver(post_save, sender=Job)
def post_save_job(sender, instance, created, **kwargs):
    if created:
        Task.objects.create_initial_task(job=instance)


@receiver(post_save, sender=State)
def post_save_state(sender, instance, created, **kwargs):
    if not created:
        for task in Task.objects.filter(is_finished=False):
            task.warning_datetime = task.calculate_warning_datetime()
            task.due_datetime = task.calculate_due_datetime()
            task.save()


class TaskQuerySet(models.QuerySet):

    def is_active(self):
        return self.filter(activated_at__lte=timezone.now())

    def filter_waiting_tasks(self, workflow=None, swimlanes=None):
        """Return a list of tasks with no user assigned to it

        Keyword arguments:
        worflow -- Use to filter by workflow (default None)
        swimlanes -- Use to filter by swimlanes (default None)
        """
        tasks = self.filter(user=None, is_finished=False)
        if workflow:
            tasks = tasks.filter(job__workflow_version__workflow=workflow)

        if swimlanes:
            tasks = tasks.filter_by_swimlanes(swimlanes)

        return tasks

    def filter_in_progress(self):
        return self.is_active().exclude(user=None).exclude(is_finished=True).exclude(is_paused=True)

    def filter_paused_tasks(self):
        return self.filter(is_paused=True)

    def filter_finished_tasks(self, user=None, workflow=None):
        tasks = self.filter(is_finished=True)
        if user:
            tasks = tasks.filter(user=user)
        if workflow:
            tasks = tasks.filter(job__workflow_version__workflow=workflow)
        return tasks

    def filter_late_tasks(self):
        tasks = self.filter(
            Q(is_finished=True, finish_datetime__gt=F('due_datetime'))|
            Q(is_finished=False, due_datetime__lt=timezone.now())
        )
        return tasks

    def filter_on_time_tasks(self):
        tasks = self.filter(
            Q(is_finished=True, finish_datetime__lte=F('due_datetime'))|
            Q(is_finished=False, warning_datetime__gt=timezone.now())
        )
        return tasks

    def filter_warning_tasks(self):
        tasks = self.filter(
            Q(is_finished=True, finish_datetime__lte=F('due_datetime'), finish_datetime__gt=F('warning_datetime'))|
            Q(is_finished=False, warning_datetime__lt=timezone.now(), due_datetime__gt=timezone.now())
        )
        return tasks


    def filter_by_swimlanes(self, swimlanes):
        if isinstance(swimlanes, str):
            swimlanes = [swimlanes, ]

        query = Q()
        for swinlane in swimlanes:
            query.add(Q(state__swimlanes__slug=swinlane), Q.OR)
        return self.filter(query)

    def filter_assigned_tasks(self, user=None, workflow=None, swimlanes=None):
        """Return a list of tasks assigned to some user

        Keyword arguments:
        user -- Use to filter by user (default None)
        worflow -- Use to filter by workflow (default None)
        swimlanes -- Use to filter by swimlanes (default None)
        """
        tasks = self.filter(is_finished=False).exclude(user=None)
        if user:
            tasks = tasks.filter(user=user)
        if workflow:
            tasks = tasks.filter(job__workflow_version__workflow=workflow)

        if swimlanes:
            tasks = tasks.filter_by_swimlanes(swimlanes)
        return tasks

    # TOOD: Change name to filter unfinished tasks maybe
    def filter_active_tasks(self, job=None):
        """Return the list of tasks not yet finished for the job."""
        tasks = self.filter(is_finished=False)
        if job:
            tasks = tasks.filter(job=job)
        return tasks


class TaskManager(models.Manager):

    def create_initial_task(self, job):
        initial_state = job.workflow_version.states.get(is_initial=True)
        return super(TaskManager, self).create(
            activated_at=job.activated_at,
            job=job,
            state=initial_state,
            initial_data=job.data,
            final_data=job.data)

    def get_forms(self, task):
        if hasattr(task.state.get_class, 'forms'):
            return task.state.get_class.forms
        else:
            return {}

    # TODO: Rename as Process next
    def create_next_tasks(self, task):
        if not task.state.is_final:
            # next states
            for next_state in task.state.next(data=task.final_data, task=task):
                state = next_state.get('state')
                activated_at = next_state.get('activated_at', timezone.now())
                additional_due_time = next_state.get('additional_due_time', 0)
                # due_time = next_state.get('due_time')
                required_states = state.required_states()

                if state.is_final:
                    # Cancel other tasks for the same job
                    Task.objects.cancel_active_tasks(job=task.job, finished_by=task.finished_by, data=task.final_data)

                # Check for finished tasks on required states
                for required_state in required_states:
                    # TODO: Refactory
                    required_task = Task.objects.filter(job=task.job, state=required_state).order_by('-modified_at').first()
                    if not required_task.is_finished:
                        return

                if required_states.count() == 0 or Task.objects.filter(job=task.job, state__in=required_states, is_finished=True).exists():
                    task = Task.objects.create(
                        job=task.job,
                        state=state,
                        initial_data=task.final_data,
                        final_data=task.final_data,
                        activated_at=activated_at,
                        additional_due_time=additional_due_time
                    )
                    Task.send_and_log(task_created, sender=task.job.workflow_version.slug, task_pk=task.pk)

    def get_initial_task(self, job):
        initial_state = job.workflow_version.states.get(is_initial=True)
        return job.tasks.get(state=initial_state)

    def cancel_active_tasks(self, job, finished_by, data=None):
        """Cancel active tasks for the job."""
        for task in self.filter_active_tasks(job=job):
            task.cancel(finished_by=finished_by, data=data)


class Task(UUIDBaseModel):
    """A single task inside a job."""
    activated_at = models.DateTimeField(default=timezone.now, help_text=_('Use to schedule tasks. The task only become active after this date and time.'))
    due_datetime = models.DateTimeField(blank=True, null=True, help_text=_('The deadline to finish the task.'))
    warning_datetime = models.DateTimeField(blank=True, null=True, help_text=_('Date and time to change the task to the warning status.'))
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name='tasks')
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='tasks')
    is_started = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name='tasks_started_by')
    paused_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name='tasks_paused_by')
    finished_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name='tasks_finished_by')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name='tasks')
    additional_due_time = models.PositiveIntegerField(help_text=_("Additional task's due time in minutes."), default=0)
    initial_data = JSONField(blank=True, null=True)
    final_data = JSONField(blank=True, null=True)

    start_datetime = models.DateTimeField(blank=True, null=True)
    pause_datetime = models.DateTimeField(blank=True, null=True)
    finish_datetime = models.DateTimeField(blank=True, null=True)

    objects = TaskManager.from_queryset(TaskQuerySet)()

    STATUS_IN_PROGRESS = 'pro'
    STATUS_FINISHED = 'fin'
    STATUS_PAUSED = 'pau'
    STATUS_WAITING = 'wai'

    STATUS_CHOICES = [
        [STATUS_IN_PROGRESS, _('In progress')],
        [STATUS_FINISHED, _('Finished')],
        [STATUS_PAUSED, _('Paused')],
        [STATUS_WAITING, _('Waiting')]
    ]

    DUE_ON_TIME = 'ont'
    DUE_WARNING = 'war'
    DUE_LATE = 'lat'

    DUE_CHOICES = [
        [DUE_ON_TIME, _('On time')],
        [DUE_WARNING, _('Warning')],
        [DUE_LATE, _('Late')]
    ]


    DUE_CSS_STATUS_CLASS_MAP = {
        DUE_ON_TIME: 'success',
        DUE_WARNING: 'warning',
        DUE_LATE: 'danger',
    }

    DUE_CSS_STATUS_ICON = {
        STATUS_PAUSED: 'mdi-pause',
        STATUS_IN_PROGRESS: 'mdi-play',
        STATUS_FINISHED: 'mdi-check',
        STATUS_WAITING: 'mdi-clock'
    }

    DUE_CSS_BACKGROUND_STATUS_MAP = {
        DUE_ON_TIME: '',
        DUE_WARNING: 'warning',
        DUE_LATE: 'danger'
    }

    class Meta:
        ordering = ['-created_at', ]
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    def __str__(self):
        return f'{self.pk} - {self.job} - {self.state}'

    @property
    def data(self):
        """ Task data.

        Returns (json)
        """
        if self.is_finished:
            return self.final_data
        else:
            return self.initial_data

    @property
    def due_css_class(self):
        return self.DUE_CSS_STATUS_CLASS_MAP[self.due_status]

    @property
    def due_css_icon(self):
        return self.DUE_CSS_STATUS_ICON[self.status]

    @property
    def due_css_background(self):
        return self.DUE_CSS_BACKGROUND_STATUS_MAP[self.due_status]

    @property
    def due_status(self):
        if self.is_finished:
            delta = self.finish_datetime - self.activated_at
        else:
            delta = timezone.now() - self.activated_at

        time_since_creation = int(delta.total_seconds()/60)
        if time_since_creation > self.state.due_time:
            return self.DUE_LATE

        if (time_since_creation <= self.state.due_time) and (time_since_creation >= self.state.due_time_warning):
            return self.DUE_WARNING

        return self.DUE_ON_TIME

    @property
    def due_status_display(self):
        return dict(self.DUE_CHOICES).get(self.due_status, self.due_status)

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def is_editable(self):
        """ Is the task in an editable status """
        return self.status is self.STATUS_IN_PROGRESS

    @property
    def time_until_due(self):
        """Remaining time to complete this task.

        Returns (timedelta or None)
        """
        if self.is_finished:
            return None

        time_until = (self.activated_at + datetime.timedelta(minutes=self.state.due_time) + datetime.timedelta(minutes=self.additional_due_time)) - timezone.now()
        if time_until.total_seconds() > 0:
            return time_until
        else:
            return None

    @property
    def overdue_time(self):
        """Amount of time this task is overdue.

        Return (timedelta or None)
        """
        if self.is_finished:
            reference_time = self.finish_datetime
        else:
            reference_time = timezone.now()

        overdue = reference_time - (self.activated_at + datetime.timedelta(minutes=self.state.due_time))
        if overdue.total_seconds() > 0:
            return overdue
        else:
            return None

    @property
    def status(self):
        if not self.is_started:
            return self.STATUS_WAITING

        if self.is_finished:
            return self.STATUS_FINISHED

        if self.is_paused:
            return self.STATUS_PAUSED

        if self.is_started and not self.is_finished and not self.is_paused:
            return self.STATUS_IN_PROGRESS

    @property
    def workflow(self):
        return self.state.workflow_version.workflow

    def save(self, *args, **kwargs):
        self.due_datetime = self.calculate_due_datetime()
        self.warning_datetime = self.calculate_warning_datetime()
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}

        if self.state.workflow_version != self.job.workflow_version:
            errors['state'] = ValidationError(_('The state must be one of the job workflow.'))

        if not self.is_started and self.is_paused:
            errors['is_paused'] = ValidationError(_("It's not possible to pause an unstarted task."))

        if not self.is_started and self.is_finished:
            errors['is_finished'] = ValidationError(_("It's not possible to finish an unstarted task."))

        if (self.start_datetime and self.finish_datetime) and (self.start_datetime > self.finish_datetime):
            errors['finish_datetime'] = ValidationError(_("The finish time must be greater than start time."))

        if (self.is_started and not self.user):
            errors['user'] = ValidationError(_("Select an user to start the task."))

        if len(errors):
            raise ValidationError(errors)

    def calculate_due_datetime(self):
        delta_minutes = self.state.due_time + self.additional_due_time
        # due_datetime = self.activated_at + datetime.timedelta(minutes=self.state.due_time) + datetime.timedelta(minutes=self.additional_due_time)
        return add_workday(self.activated_at, delta_minutes)

    def calculate_warning_datetime(self):
        delta_minutes = self.state.due_time_warning + self.additional_due_time
        return add_workday(self.activated_at, delta_minutes)

    def abandon(self):
        if self.is_finished:
            raise ValidationError(_("It's not possible to abandon a finished task"))

        self.is_paused = False
        self.is_started = False
        self.pause_datetime = None
        self.paused_by = None
        self.user = None
        self.started_by = None
        self.start_datetime = None
        self.save()

    def cancel(self, finished_by, data=None):
        """Cancel the task. It is called when the job is finished by another parallel task and do not spawn next tasks."""
        if data:
            self.final_data = data
        self.is_canceled = True
        self.is_finished = True
        self.is_paused = False
        self.finish_datetime = timezone.now()
        self.finished_by = finished_by
        self.save()

    def finish(self, finished_by, data=None):
        if not self.is_started:
            raise ValidationError(_("It's not possible to finish an unstarted task."))

        if self.is_finished:
            raise ValidationError(_("The task is already finished."))

        if data:
            self.final_data = data
            self.save()
        Task.objects.create_next_tasks(task=self)

        self.is_finished = True
        self.is_paused = False
        self.finish_datetime = timezone.now()
        self.finished_by = finished_by
        self.save()
        Task.send_and_log(task_finished, sender=self.job.workflow_version.slug, task_pk=self.pk)
        if self.state.is_final:
            Task.send_and_log(job_finished, sender=self.job.workflow_version.slug, job_pk=self.job.pk)


    def pause(self, user=None):
        if  self.is_paused:
            raise ValidationError(_("The task is already paused."))

        if not self.is_started:
            raise ValidationError(_("It's not possible to pause an unstarted task."))

        if self.is_finished:
            raise ValidationError(_("It's not possible to pause a finished task."))

        self.is_paused = True
        self.paused_by = user
        self.pause_datetime = timezone.now()
        self.save()

    def reopen(self, user):
        if not self.is_started:
            raise ValidationError(_("It's not possible to reopen an unstarted task."))

        if not self.is_finished:
            raise ValidationError(_("It's not possible to reopen an already open task."))

        # Check for next tasks
        # if Task.objects.filter(job=self.job, state__in=self.state.next.all(), is_started=True).exists():
        #     raise ValidationError(_("It's not possible to reopen the task. The next tasks is already started"))
        # else:
        # Task.objects.filter(job=self.job, state__in=self.state.next.all()).delete()

        self.start_datetime = timezone.now()
        self.is_finished = False
        self.is_canceled = False
        self.finished_by = None
        self.finish_datetime = None
        self.save()

    def start(self, started_by, user):
        if self.is_finished:
            raise ValidationError(_("The task is already finished."))

        if self.is_started:
            raise ValidationError(_("The task is already started."))

        self.is_started = True
        self.start_datetime = timezone.now()
        self.started_by = started_by
        self.user = user
        self.save()

    def unpause(self):
        if not self.is_paused:
            raise ValidationError(_("The task is not paused."))

        self.is_paused = False
        self.save()


TASKS_ACTIONS_CHOICES = [
    ['0', 'Iniciou a tarefa'],
    ['1', 'Pausou a tarefa'],
    ['3', 'Abandonou a tarefa'],
    ['4', 'Finalizou a tarefa'],
    ['5', 'Reabriu a tarefa']
]


class TaskLog(UUIDBaseModel):
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(choices=TASKS_ACTIONS_CHOICES, max_length=1)
