# Generated by Django 3.2.13 on 2023-03-22 09:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0057_auto_20230321_1048"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="target",
            name="expression_text",
        ),
        migrations.RemoveField(
            model_name="target",
            name="expression_type",
        ),
    ]
