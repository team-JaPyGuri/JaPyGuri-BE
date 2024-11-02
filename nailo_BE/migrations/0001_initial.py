# Generated by Django 5.1.2 on 2024-11-02 14:14

import django.db.models.deletion
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
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("customer_id", models.CharField(max_length=255, unique=True)),
                ("customer_pw", models.CharField(max_length=255)),
                ("customer_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "generated_image",
                    models.URLField(blank=True, max_length=500, null=True),
                ),
                ("design_book", models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Designs",
            fields=[
                (
                    "design_key",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("design_name", models.CharField(max_length=255)),
                ("price", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "design_image",
                    models.URLField(blank=True, max_length=500, null=True),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Shops",
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
                ("shopper_key", models.CharField(max_length=255)),
                ("shopper_id", models.CharField(max_length=255)),
                ("shopper_name", models.CharField(max_length=255)),
                ("lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("lng", models.DecimalField(decimal_places=6, max_digits=9)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("intro_image", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Request",
            fields=[
                (
                    "request_key",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
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
                    "customer_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="nailo_BE.customers",
                    ),
                ),
                (
                    "design_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="nailo_BE.designs",
                    ),
                ),
                (
                    "shopper_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="nailo_BE.shops",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Response",
            fields=[
                (
                    "response_key",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("price", models.CharField(max_length=255)),
                ("contents", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="nailo_BE.customers",
                    ),
                ),
                (
                    "request_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="nailo_BE.request",
                    ),
                ),
                (
                    "shopper_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="nailo_BE.shops"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="designs",
            name="shopper_name",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="nailo_BE.shops"
            ),
        ),
    ]