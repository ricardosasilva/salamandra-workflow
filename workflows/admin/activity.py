from django.contrib import admin

from workflows.models import Activity, ActivityStatus, TaskActivity



def workflow_version(obj):
    return obj.state.workflow_version


class ActivityStatusInline(admin.TabularInline):
    model = ActivityStatus


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    inlines = [ActivityStatusInline, ]
    list_display = ['slug', 'state', 'name', workflow_version]
    readonly_fields = ['state', workflow_version]


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    raw_id_fields = ['task', 'user',]
    list_display = ['user', 'created_at', 'task', 'status']
    list_filter = ['created_at', 'task__state']