# Generated by Django 5.1.3 on 2024-12-19 04:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0011_remove_wallet_created_at_remove_wallet_updated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
