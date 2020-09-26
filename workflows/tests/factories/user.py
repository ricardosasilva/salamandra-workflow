from django.contrib.auth import get_user_model

import factory, factory.django
from mimesis_factory import MimesisField



class UserFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = get_user_model()

    first_name = MimesisField('name')
    last_name = MimesisField('name')
