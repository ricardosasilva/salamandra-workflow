from django.utils import timezone
import factory, factory.django
from factory.fuzzy import FuzzyDateTime
from mimesis_factory import MimesisField

from workflows.models import Task
from workflows.tests.factories.state import StateFactory


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = Task

    state = factory.SubFactory(StateFactory)    
    slug = MimesisField('name')

