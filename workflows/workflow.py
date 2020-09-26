import re

from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

from workflows.conf import settings as workflows_settings
from workflows.exceptions import SwinlaneDoesNotExist
from workflows.models import Activity, ActivityStatus
from workflows.models import State as StateModel
from workflows.models import Swimlane, Workflow, WorkflowVersion
from workflows.utils import camel_to_snake_case, fullname


class State(object):
    due_time = workflows_settings.WORKFLOWS_DUE_TIME
    due_time_warning =  workflows_settings.WORKFLOWS_DUE_TIME_WARNING
    is_final = False
    is_initial = False
    max_unassigned_time = workflows_settings.WORKFLOWS_MAX_UNASSIGNED_TIME
    max_unassigned_time_warning = workflows_settings.WORKFLOWS_MAX_UNASSIGNED_TIME_WARNING
    required = []  # List of State names required to be finished berfore start this state.
    swimlanes = []  # List of swimlanes slugs
    order = None

    @property
    def fullname(self):
        return fullname(self)

    def _check_activities(self, state):
        if hasattr(self, 'activities'):
            for activity in self.activities:
                activity = Activity.objects.create_from_config(state=state, slug=activity, config=self.activities[activity])

    def _check_orphans_activities(self, state):
        for activity_instance in Activity.objects.filter(state=state):
            print(f' :: Checking Activity "{activity_instance}"')
            if hasattr(self, 'activities'):
                activity = self.activities.get(activity_instance.slug)
                if activity:
                    # Check status
                    for status_instance in ActivityStatus.objects.filter(activity=activity_instance):
                        if not activity.get('status').get(status_instance.slug):
                            print(f'    !! Orphan status: {status_instance.slug} on activity {activity_instance.slug} on state {state}')

                else:
                    print(f'    !! Orphan activity {activity_instance.slug} on state {state}')
            else:
                print(f'    !! Orphan activity {activity_instance.slug} on state {state}')

    def _check_swimlanes(self):
        for swimlane_slug in self.swimlanes:
            swinlane, created = Swimlane.objects.get_or_create(slug=swimlane_slug, defaults={'name': swimlane_slug})

    def _create_db_instance(self, workflow_version, is_initial):
        state, created = StateModel.objects.get_or_create(
            slug=self.slug,
            workflow_version=workflow_version,
            defaults={
                "due_time": self.due_time,
                "due_time_warning": self.due_time_warning,
                "max_unassigned_time": self.max_unassigned_time,
                "max_unassigned_time_warning": self.max_unassigned_time_warning
            }
        )
        state.class_name = fullname(self)
        state.name = self.name
        state.description = self.description
        state.is_final = self.is_final
        state.is_initial = is_initial
        state.due_time = self.due_time
        state.due_time_warning = self.due_time_warning
        state.max_unassigned_time = self.max_unassigned_time
        state.max_unassigned_time_warning = self.max_unassigned_time_warning
        if self.order:
            state.order = self.order
        state.swimlanes.clear()

        for swimlane in self.swimlanes:
            try:
                swimlane_instance = Swimlane.objects.get(slug=swimlane)
                state.swimlanes.add(swimlane_instance)
            except ObjectDoesNotExist:
                raise SwinlaneDoesNotExist('The swimlane "{}" defined on {} was not found.'.format(swimlane, self.__class__))

        state.save()

        return state

    def process(self, workflow_version, is_initial):
        self._check_swimlanes()
        state = self._create_db_instance(workflow_version, is_initial)
        self._check_activities(state=state)
        self._check_orphans_activities(state=state)


class BaseWorkflow(object):

    @property
    def forms(self):
        forms = {}
        for state in self.states:
            if hasattr(state, 'forms'):
                forms.update(state.forms)
        return forms

    def _create_db_instance(self, slug, version):
        workflow, created = Workflow.objects.get_or_create(slug=slug, defaults={"description": self.description})
        workflow.description = self.description
        workflow.save()

        workflow_version, created = WorkflowVersion.objects.get_or_create(workflow=workflow, version=version)
        return workflow_version

    def _check_forms(self):
        """ Check for unique slugs """
        slugs = []
        for StateClass in self.states:
            if hasattr(StateClass, 'forms'):
                forms_slugs = list(StateClass.forms.keys())
                if not len(list(set(forms_slugs) & set(slugs))) > 0:
                    slugs = slugs + forms_slugs
                else:
                    duplicate = list(set(forms_slugs) & set(slugs))
                    raise Exception(f'The forms slug must be unique. There is a duplicated one: {duplicate} ')

    def process(self, slug, version):
        self._check_forms()
        workflow_version = self._create_db_instance(slug, version)

        slugs = [state.slug for state in self.states]
        if len(slugs) > len(set(slugs)):
            # TODO: Create custom Exception
            raise Exception('There is two states with the same slug')

        for StateClass in self.states:
            state = StateClass()
            is_initial = False
            if self.initial_state == StateClass:
                is_initial = True
            state.process(workflow_version=workflow_version, is_initial=is_initial)

    def get_form(self, slug):
        return self.forms.get(slug)


class Workflows(object):

    def get_additional_forms(self):
        return settings.WORKFLOWS_WORKFLOWS
