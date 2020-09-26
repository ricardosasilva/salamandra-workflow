from django.contrib import admin

from workflows.models import Workflow, WorkflowVersion


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = (
        'slug',
        'description',
        'uuid',
        'created_at',
        'modified_at',
        'is_active'
    )
    list_filter = ('created_at', 'modified_at', 'is_active')
    search_fields = ('description', 'slug')
    date_hierarchy = 'created_at'
    readonly_fields = ('uuid', )


def create_new_version(modeladmin, request, queryset):
    workflows = queryset.order_by('workflow__pk').distinct('workflow')
    for workflow_version in workflows:
        workflow_version.create_new_version()
create_new_version.short_description = "Create new version for selected workflow"


@admin.register(WorkflowVersion)
class WorkflowVersionAdmin(admin.ModelAdmin):
    list_display = (
        'workflow',
        'version',
        'uuid',
        'created_at',
        'modified_at',
        'is_active'
    )
    list_filter = ('created_at', 'modified_at', 'is_active', 'workflow')
    date_hierarchy = 'created_at'
    actions = [create_new_version, ]
