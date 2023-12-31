# Generated by Django 3.2.9 on 2022-03-16 17:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0018_report_report_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="current_bsr",
            field=models.PositiveIntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="target_acos",
            field=models.PositiveSmallIntegerField(
                default=0,
                validators=[
                    django.core.validators.MaxValueValidator(199),
                    django.core.validators.MinValueValidator(0),
                ],
            ),
        ),
    ]
