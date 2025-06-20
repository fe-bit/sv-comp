# Generated by Django 5.2.1 on 2025-05-25 21:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("verification_tasks", "0001_initial"),
        ("verifiers", "0002_alter_verifier_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerificationSpecification",
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
                ("name", models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Benchmark",
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
                ("status", models.CharField(max_length=50)),
                ("raw_core", models.TextField()),
                ("cpu", models.FloatField()),
                ("memory", models.FloatField()),
                ("test_date", models.DateTimeField()),
                (
                    "verification_task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="verification_tasks.verificationtask",
                    ),
                ),
                (
                    "verifier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="verifiers.verifier",
                    ),
                ),
                (
                    "verification_specs",
                    models.ManyToManyField(
                        blank=True, to="benchmarks.verificationspecification"
                    ),
                ),
            ],
            options={
                "ordering": ["verification_task", "verifier"],
                "unique_together": {("verification_task", "verifier")},
            },
        ),
    ]
