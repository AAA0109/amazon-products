# Generated by Django 3.2.9 on 2022-01-26 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0003_auto_20220126_1626"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="report_id",
            field=models.CharField(
                db_index=True, default="", max_length=254, unique=True
            ),
        ),
    ]
