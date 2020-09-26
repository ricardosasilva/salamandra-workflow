import factory, factory.django
from mimesis_factory import MimesisField

from workflows.models import State
from workflows.tests.factories.workflow import WorkflowVersionFactory


class StateFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = State

    workflow_version = factory.SubFactory(WorkflowVersionFactory)
    name = MimesisField('person.identifier', mask='state-#')
    description = MimesisField('description')
    slug = MimesisField('name')