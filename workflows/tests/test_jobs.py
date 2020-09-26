from django.contrib.auth import get_user_model
from django.test import TestCase

from workflows.models import WorkflowVersion


class TestJobs(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass
        # pipeline = PipelineFactory()
        # state1 = StateFactory(is_initial=True, is_final=False, pipeline=pipeline)
        # state2 = StateFactory(is_initial=False, is_final=False, pipeline=pipeline)
        # state3 = StateFactory(is_initial=False, is_final=True, pipeline=pipeline)

        # state1.next.add(state2)
        # state2.required.add(state1)
        # state2.next.add(state3)
        # state3.required.add(state2)

        # user = UserFactory()

    def test_estoque(self):
        pass
        # pipeline = Pipeline.objects.last()
        # user = get_user_model().objects.last()
        # job = Job.objects.create_job(pipeline=pipeline, user=user)
        # # Check for state
        # self.assertEqual(JobState.objects.filter(job=job).count(), 1)

        # Start state
        # state = job
