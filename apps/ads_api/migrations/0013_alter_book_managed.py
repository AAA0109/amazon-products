# Generated by Django 3.2.9 on 2022-03-04 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0012_auto_20220303_1732"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="managed",
            field=models.BooleanField(default=False),
        ),
    ]
