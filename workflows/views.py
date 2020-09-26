from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View

from workflows.models import Task


class FinishTaskView(View):
    error_redirect = None
    success_redirect = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_data(self, request, task):
        return None

    def get_task(self, task_id):
        return get_object_or_404(Task, pk=task_id)

    def get_success_redirect(self, request):
        if self.success_redirect is None:
            raise ValidationError(_('You need to define a success_redirect attribute or override get_success_redirect method when extending FinishTaskView'))

        return redirect(self.success_redirect)

    def get_error_redirect(self, request):
        return redirect(request.META.get('HTTP_REFERER'))

    def post(self, request, task_id):
        task = self.get_task(task_id=task_id)
        if task.user == request.user:
            try:
                task.finish(finished_by=request.user, data=self.get_data(request, task))
            except ValidationError as e:
                messages.error(request, e.message)
                return self.get_error_redirect(request)

            return self.get_success_redirect(request)
        else:
            messages.error(self.request, _("Your aren't the task owner."))
            return self.get_success_redirect(request)