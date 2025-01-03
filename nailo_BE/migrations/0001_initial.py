# Generated by Django 5.1.2 on 2024-11-22 03:16

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customers",
            fields=[
                (
                    "customer_key",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("customer_id", models.CharField(max_length=255, unique=True)),
                ("customer_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "generated_image",
                    models.URLField(blank=True, max_length=500, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Designs",
            fields=[
                (
                    "design_key",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("design_name", models.CharField(max_length=255)),
                ("price", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("design_url", models.URLField(blank=True, max_length=500, null=True)),
                ("like_count", models.IntegerField(null=True)),
                ("tag", models.CharField(blank=True, max_length=50, null=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Shops",
            fields=[
                (
                    "shop_key",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("shop_id", models.CharField(max_length=255)),
                ("shop_name", models.CharField(max_length=255)),
                ("lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("lng", models.DecimalField(decimal_places=6, max_digits=9)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("shop_url", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Request",
            fields=[
                (
                    "request_key",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("price", models.IntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("contents", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="nailo_be.customers",
                    ),
                ),
                (
                    "design",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="nailo_be.designs",
                    ),
                ),
                (
                    "shop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="nailo_be.shops",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Response",
            fields=[
                (
                    "response_key",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("price", models.IntegerField()),
                ("contents", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response",
                        to="nailo_be.customers",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="nailo_be.request",
                    ),
                ),
                (
                    "shop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response",
                        to="nailo_be.shops",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="designs",
            name="shop",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="nailo_be.shops"
            ),
        ),
        migrations.CreateModel(
            name="Like",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("liked_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="like",
                        to="nailo_be.customers",
                    ),
                ),
                (
                    "design",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="liked_design",
                        to="nailo_be.designs",
                    ),
                ),
            ],
            options={
                "unique_together": {("customer", "design")},
            },
        ),
    ]
