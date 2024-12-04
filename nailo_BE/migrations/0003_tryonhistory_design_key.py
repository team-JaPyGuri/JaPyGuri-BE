# Generated by Django 5.1.2 on 2024-12-04 01:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nailo_be", "0002_tryonhistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="tryonhistory",
            name="design_key",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="nailo_be.designs",
            ),
            preserve_default=False,
        ),
    ]