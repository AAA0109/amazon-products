# Generated by Django 3.2.13 on 2023-03-01 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0052_alter_datebookprice_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="report_location",
            field=models.CharField(default="", max_length=1024),
        ),
    ]