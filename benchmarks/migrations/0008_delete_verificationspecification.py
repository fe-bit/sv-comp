# Generated by Django 5.2.1 on 2025-06-02 16:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('benchmarks', '0007_alter_benchmark_options_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='VerificationSpecification',
        ),
    ]
