from django.contrib import admin

from workflows.models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'workflow_version',
        'created_by',
        'is_finished',
        'uuid',
        'created_at',
        'modified_at',
    )
    list_filter = ('created_at', 'modified_at', 'created_by')
    date_hierarchy = 'created_at'
    raw_id_fields = ('created_by', )
