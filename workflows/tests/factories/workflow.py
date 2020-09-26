from django.utils import timezone
import factory, factory.django
from factory.fuzzy import FuzzyDateTime
from mimesis_factory import MimesisField

from workflows.models import Workflow, WorkflowVersion


class WorkflowFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = Workflow

    slug = MimesisField('name')


class WorkflowVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkflowVersion

    workflow = factory.SubFactory(WorkflowFactory)
    