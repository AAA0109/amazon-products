# Generated by Django 3.2.13 on 2023-02-13 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0048_reportdata_units_sold_14d"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportdata",
            name="attributed_conversions_30d",
            field=models.PositiveIntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name="reportdata",
            name="units_sold_14d",
            field=models.PositiveIntegerField(default=0, null=True),
        ),
    ]
