# Generated by Django 5.2.1 on 2025-05-29 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("benchmarks", "0006_benchmark_status_display"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="benchmark",
            options={"ordering": ["verifier", "verification_task"]},
        ),
        migrations.RenameField(
            model_name="benchmark",
            old_name="raw_core",
            new_name="raw_score",
        ),
    ]
