# Generated by Django 2.2.1 on 2020-09-19 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0008_update_tasks_due_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
