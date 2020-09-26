import importlib
import inspect

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from workflows.conf import settings
from workflows.models import Workflow


class Command(BaseCommand):
    help = 'Sync workflow settings to DB'

    def handle(self, *args, **options):
        workflows = settings.WORKFLOWS_WORKFLOWS
        for slug in workflows.keys():
            workflow_settings = workflows.get(slug)
            versions = workflow_settings.get('versions')

            for version in versions.keys():
                version_path = versions.get(version)
                workflow = importlib.import_module(version_path).Workflow()
                workflow.process(slug=slug, version=version)
