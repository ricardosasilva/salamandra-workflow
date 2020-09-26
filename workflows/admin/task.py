from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from workflows.models import Task


def abandon_tasks(modeladmin, request, queryset):
    for task in queryset.all():
        try:
            task.abandon()
        except Exception as e:
            message = '{message} (Task uuid={uuid})'.format(uuid=task.uuid, message=e.message)
            modeladmin.message_user(request, message, level=messages.ERROR)

abandon_tasks.short_description = _("Abandon selected tasks")



def finish_tasks(modeladmin, request, queryset):
    for task in queryset.all():
        try:
            task.finish(finished_by=request.user)
        except Exception as e:
            message = '{message} (Task uuid={uuid})'.format(uuid=task.uuid, message=e.message)
            modeladmin.message_user(request, message, level=messages.ERROR)

finish_tasks.short_description = _("Finish selected tasks")


def pause_tasks(modeladmin, request, queryset):
    for task in queryset.all():
        try:
            task.pause()
        except Exception as e:
            message = '{message} (Task uuid={uuid})'.format(uuid=task.uuid, message=e.message)
            modeladmin.message_user(request, message, level=messages.ERROR)

pause_tasks.short_description = _("Pause selected tasks")


def start_tasks(modeladmin, request, queryset):
    for task in queryset.all():
        try:
            task.start(user=request.user, started_by=request.user)
        except Exception as e:
            message = '{message} (Task uuid={uuid})'.format(uuid=task.uuid, message=e.message)
            modeladmin.message_user(request, message, level=messages.ERROR)

start_tasks.short_description = _("Start selected tasks")


def reopen_tasks(modeladmin, request, queryset):
    for task in queryset.all():
        try:
            task.reopen(user=request.user)
        except Exception as e:
            message = '{message} (Task uuid={uuid})'.format(uuid=task.uuid, message=e.message)
            modeladmin.message_user(request, message, level=messages.ERROR)

reopen_tasks.short_description = _("Reopen selected tasks")


def unpause_tasks(modeladmin, request, queryset):
    for task in queryset.all():
        try:
            task.unpause()
        except Exception as e:
            message = '{message} (Task uuid={uuid})'.format(uuid=task.uuid, message=e.message)
            modeladmin.message_user(request, message, level=messages.ERROR)

unpause_tasks.short_description = _("Unpause selected tasks")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    actions = [ abandon_tasks, finish_tasks, pause_tasks, reopen_tasks, start_tasks, unpause_tasks ]
    list_display = (
        'job',
        'user',
        'state',
        'workflow',
        'activated_at',
        'warning_datetime',
        'due_datetime',
        'is_started',
        'is_paused',
        'is_finished',
        'is_canceled',
        'uuid',
        'created_at',
        'modified_at'
    )
    list_filter = (
        'created_at',
        'modified_at',
        'activated_at',
        'state',
        'is_paused',
        'is_finished',
        'is_canceled'
    )
    date_hierarchy = 'activated_at'
    readonly_fields = ['uuid', 'due_status', 'status', 'due_datetime']
    search_fields = ['state__name__icontains', ]
    raw_id_fields = ['job', 'user', 'state', 'started_by', 'paused_by', 'finished_by']

    def due_status(self, obj):
        return obj.due_status_display

    def status(self, obj):
        return obj.status_display
