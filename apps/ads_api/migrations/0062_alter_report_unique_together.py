# Generated by Django 3.2.13 on 2023-04-19 13:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0061_auto_20230419_1339"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="report",
            unique_together={("report_type", "profile_id", "start_date", "end_date")},
        ),
    ]