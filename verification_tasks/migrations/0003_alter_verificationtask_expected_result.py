# Generated by Django 5.2.1 on 2025-05-28 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification_tasks", "0002_verificationtask_expected_result"),
    ]

    operations = [
        migrations.AlterField(
            model_name="verificationtask",
            name="expected_result",
            field=models.CharField(
                choices=[("true", "True"), ("false", "False"), ("unknown", "Unknown")],
                default="true",
                help_text="Expected result for the task.",
                max_length=7,
            ),
        ),
    ]
