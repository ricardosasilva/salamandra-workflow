import django


job_finished = django.dispatch.Signal(providing_args=["job_pk",])
job_started = django.dispatch.Signal(providing_args=["job_pk",])

task_created = django.dispatch.Signal(providing_args=['task_pk', ])
task_finished = django.dispatch.Signal(providing_args=['task_pk', ])
task_started = django.dispatch.Signal(providing_args=['task_pk', ])