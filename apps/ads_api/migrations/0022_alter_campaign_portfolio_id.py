# Generated by Django 3.2.9 on 2022-03-29 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0021_auto_20220321_1224"),
    ]

    operations = [
        migrations.AlterField(
            model_name="campaign",
            name="portfolio_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
