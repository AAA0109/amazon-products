# Generated by Django 3.2.9 on 2022-03-21 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0020_auto_20220316_1711"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="type",
            field=models.CharField(
                choices=[("vendor", "Vendor"), ("seller", "Seller")],
                default="vendor",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="adgroup",
            name="serving_status",
            field=models.CharField(
                choices=[
                    ("AD_GROUP_ARCHIVED", "Ad Group Archived"),
                    ("AD_GROUP_PAUSED", "Ad Group Paused"),
                    ("AD_GROUP_STATUS_ENABLED", "Ad Group Enabled"),
                    ("AD_POLICING_SUSPENDED", "Ad Suspended"),
                    ("AD_GROUP_INCOMPLETE", "Ad Group Incomplete"),
                    ("CAMPAIGN_OUT_OF_BUDGET", "Campaign Budget Limited"),
                    ("CAMPAIGN_PAUSED", "Campaign Paused"),
                    ("CAMPAIGN_ARCHIVED", "Campaign Archived"),
                    ("CAMPAIGN_INCOMPLETE", "Campaign Incomplete"),
                    ("ACCOUNT_OUT_OF_BUDGET", "Account Budget Limited"),
                    ("PENDING_START_DATE", "Pending Start Data"),
                ],
                default="AD_GROUP_STATUS_ENABLED",
                max_length=99,
                null=True,
            ),
        ),
    ]