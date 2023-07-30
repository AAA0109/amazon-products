# Generated by Django 3.2.13 on 2023-02-17 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0051_datebookprice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datebookprice",
            name="price",
            field=models.DecimalField(decimal_places=2, default=9.99, max_digits=8),
        ),
    ]