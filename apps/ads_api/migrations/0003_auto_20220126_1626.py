# Generated by Django 3.2.9 on 2022-01-26 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0002_rename_campaign_id_campaign_campaign_id_amazon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="target",
            name="expression_text",
            field=models.CharField(default="", max_length=99, null=True),
        ),
        migrations.AlterField(
            model_name="target",
            name="resolved_expression_text",
            field=models.CharField(default="", max_length=99, null=True),
        ),
    ]