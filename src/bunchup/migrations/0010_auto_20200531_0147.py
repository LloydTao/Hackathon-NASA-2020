# Generated by Django 3.0.5 on 2020-05-31 00:47

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('bunchup', '0009_auto_20200531_0034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='finish_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 1, 0, 47, 48, 465180, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='activity',
            name='hub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bunchup.Hub'),
        ),
    ]
