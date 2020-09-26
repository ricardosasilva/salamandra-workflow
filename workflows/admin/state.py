from django.contrib import admin

from workflows.models import State


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'uuid',
        'workflow_version',
        'is_initial',
        'is_final',
        'due_time_warning_humanized',
        'due_time_humanized',
        'order',
        'created_at',
        'modified_at',
    )
    list_filter = ('created_at', 'modified_at', 'is_initial', 'is_final',)
    readonly_fields = ('uuid', )
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}
    date_hierarchy = 'created_at'
    ordering = ['workflow_version', 'order']