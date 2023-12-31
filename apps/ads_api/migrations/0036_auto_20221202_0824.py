# Generated by Django 3.2.13 on 2022-12-02 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads_api", "0035_rank"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newrelease",
            name="country_code",
            field=models.CharField(
                choices=[
                    ("US", "Us"),
                    ("CA", "Ca"),
                    ("MX", "Mx"),
                    ("UK", "Uk"),
                    ("AU", "Au"),
                    ("DE", "De"),
                    ("ES", "Es"),
                    ("FR", "Fr"),
                    ("IT", "It"),
                ],
                default="US",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="country_code",
            field=models.CharField(
                choices=[
                    ("US", "Us"),
                    ("CA", "Ca"),
                    ("MX", "Mx"),
                    ("UK", "Uk"),
                    ("AU", "Au"),
                    ("DE", "De"),
                    ("ES", "Es"),
                    ("FR", "Fr"),
                    ("IT", "It"),
                ],
                default="US",
                max_length=99,
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="marketplace_string_id",
            field=models.CharField(
                choices=[
                    ("ATVPDKIKX0DER", "US"),
                    ("A2EUQ1WTGCTBG2", "CA"),
                    ("A1AM78C64UM0Y8", "MX"),
                    ("A1F83G8C2ARO7P", "UK"),
                    ("A39IBJ37TRP1C6", "AU"),
                    ("A1PA6795UKMFR9", "DE"),
                    ("A1RKKUPIHCS9HS", "ES"),
                    ("A13V1IB3VIYZZH", "FR"),
                    ("APJ6JRA9NG5V4", "IT"),
                ],
                default="ATVPDKIKX0DER",
                max_length=99,
            ),
        ),
    ]
