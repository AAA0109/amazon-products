# Generated by Django 3.2.9 on 2022-03-07 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0013_alter_book_managed"),
    ]

    operations = [
        migrations.AddField(
            model_name="adgroup",
            name="default_bid",
            field=models.DecimalField(
                decimal_places=2, default=0.67, max_digits=8, null=True
            ),
        ),
    ]
