from django.contrib.auth import get_user_model
from django.test import TestCase

from workflows.tests.factories import WorkflowVersionFactory
from workflows.tests.workflow_v1 import Workflow


class TestJobs(TestCase):

    @classmethod
    def setUpTestData(cls):
        workflow = Workflow()
        workflow.process(slug='test', version='1')
        cls.workflow = workflow

    def test_workflow(self):
        print (self.workflow)