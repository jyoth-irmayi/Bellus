# Generated by Django 5.1.3 on 2024-12-08 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0024_order_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='price',
            field=models.IntegerField(default=0),
        ),
    ]
