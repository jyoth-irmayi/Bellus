# Generated by Django 5.0.7 on 2025-01-16 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0040_alter_order_order_id_alter_order_payment_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
