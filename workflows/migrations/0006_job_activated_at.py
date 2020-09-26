# Generated by Django 2.2.1 on 2019-10-11 08:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0005_auto_20190921_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='activated_at',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='Use to schedule jobs. The initial tasks only become active after this date and time.'),
        ),
    ]