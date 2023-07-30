# Generated by Django 3.2.13 on 2022-10-20 12:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0034_auto_20221019_1452"),
    ]

    operations = [
        migrations.CreateModel(
            name="Rank",
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
                (
                    "keyword",
                    models.CharField(blank=True, default="", max_length=250, null=True),
                ),
                ("rank_sb", models.PositiveIntegerField(default=0)),
                ("rank_sp", models.PositiveIntegerField(default=0)),
                ("rank_org", models.PositiveIntegerField(default=0)),
                (
                    "book",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="ads_api.book",
                        verbose_name="Book",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
