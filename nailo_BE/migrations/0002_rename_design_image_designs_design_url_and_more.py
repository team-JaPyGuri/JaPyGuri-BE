# Generated by Django 5.1.2 on 2024-11-07 13:11

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nailo_be", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="designs",
            old_name="design_image",
            new_name="design_url",
        ),
        migrations.RenameField(
            model_name="shops",
            old_name="intro_image",
            new_name="shop_id",
        ),
        migrations.RenameField(
            model_name="shops",
            old_name="shopper_key",
            new_name="shop_key",
        ),
        migrations.RenameField(
            model_name="shops",
            old_name="shopper_id",
            new_name="shop_name",
        ),
        migrations.RenameField(
            model_name="shops",
            old_name="shopper_name",
            new_name="shop_url",
        ),
        migrations.AlterField(
            model_name="customers",
            name="customer_key",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="request",
            name="request_key",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="response",
            name="price",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="response",
            name="response_key",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
    ]
