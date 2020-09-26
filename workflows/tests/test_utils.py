import datetime

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from workflows.tests.factories import WorkflowVersionFactory
from workflows.tests.workflow_v1 import Workflow
from workflows.utils import add_workday


class TestUtils(TestCase):

    def test_util(self):
        timezone = pytz.timezone("America/Sao_Paulo")

        tests = [
            {'initial': '2019-12-31 17:00', 'minutes': 2880, 'final': '2020-01-03 17:00'},
            {'initial': '2020-07-31 17:00', 'minutes': 120, 'final': '2020-08-03 09:00'},
            {'initial': '2020-07-31 17:00', 'minutes': 1440, 'final': '2020-08-03 17:00'},
            {'initial': '2020-07-30 16:00', 'minutes': 540, 'final': '2020-07-31 09:00'},
        ]

        for test in tests:
            initial_datetime = timezone.localize(datetime.datetime.fromisoformat(test['initial']))
            final_datetime = timezone.localize(datetime.datetime.fromisoformat(test['final']))
        
            result = add_workday(initial_datetime, test.get('minutes'))
            self.assertEqual(result, final_datetime)
