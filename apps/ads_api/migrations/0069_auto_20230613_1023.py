# Generated by Django 3.2.13 on 2023-06-13 10:23

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ads_api", "0068_auto_20230613_1022"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="keyword",
            name="external_created",
        ),
        migrations.RemoveField(
            model_name="target",
            name="external_created",
        ),
    ]