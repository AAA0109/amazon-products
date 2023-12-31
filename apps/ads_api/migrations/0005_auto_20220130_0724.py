# Generated by Django 3.2.9 on 2022-01-30 07:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0004_alter_report_report_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="adgroup",
            name="last_updated_date_on_amazon",
            field=models.PositiveBigIntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name="adgroup",
            name="state",
            field=models.CharField(
                choices=[
                    ("enabled", "Enabled"),
                    ("paused", "Paused"),
                    ("archived", "Archived"),
                ],
                default="enabled",
                max_length=99,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="ProductAd",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product_ad_id", models.PositiveBigIntegerField(unique=True)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("enabled", "Enabled"),
                            ("paused", "Paused"),
                            ("archived", "Archived"),
                        ],
                        default="enabled",
                        max_length=99,
                        null=True,
                    ),
                ),
                ("asin", models.CharField(default="", max_length=99, null=True)),
                (
                    "last_updated_date_on_amazon",
                    models.PositiveBigIntegerField(default=0, null=True),
                ),
                (
                    "serving_status",
                    models.CharField(default="", max_length=99, null=True),
                ),
                (
                    "ad_group",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="ads_api.adgroup",
                        verbose_name="Ad Group",
                    ),
                ),
                (
                    "campaign",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="ads_api.campaign",
                        verbose_name="Campaign",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
