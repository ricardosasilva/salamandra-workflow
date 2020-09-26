from django.contrib import admin

from workflows.models import Swimlane


@admin.register(Swimlane)
class SwimlaneAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'created_at',
        'modified_at',
        'name',
        'slug',
    )
    list_filter = ('created_at', 'modified_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}
    date_hierarchy = 'created_at'
