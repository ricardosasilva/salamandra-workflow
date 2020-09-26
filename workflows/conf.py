from django.conf import settings
from appconf import AppConf


class WorkflowsAppConf(AppConf):
    DUE_TIME = 3*24*60
    DUE_TIME_WARNING = 2*24*60
    MAX_UNASSIGNED_TIME = 12*60
    MAX_UNASSIGNED_TIME_WARNING = 12*60
    WORKFLOWS = {}

    class Meta:
        prefix = 'workflows'
