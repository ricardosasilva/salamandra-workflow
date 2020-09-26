import  datetime

from django.db import migrations


def update_tasks(apps, schema_editor):
    Task = apps.get_model('workflows', 'Task')

    for task in Task.objects.all():
        task.warning_datetime = task.activated_at + datetime.timedelta(minutes=task.state.due_time_warning) + datetime.timedelta(minutes=task.additional_due_time)
        task.due_datetime = task.activated_at + datetime.timedelta(minutes=task.state.due_time) + datetime.timedelta(minutes=task.additional_due_time)
        task.save()


def reverse_update_tasks(apps, schema_editor):
    Task = apps.get_model('workflows', 'Task')

    for task in Task.objects.all():
        task.warning_datetime = None
        task.due_datetime = None
        task.save()


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0007_auto_20200611_0611'),
    ]

    operations = [
        migrations.RunPython(update_tasks, reverse_code=reverse_update_tasks),
    ]
