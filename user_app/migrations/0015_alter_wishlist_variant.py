# Generated by Django 5.0.7 on 2025-01-03 03:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0038_remove_order_status_orderitem_status'),
        ('user_app', '0014_alter_wishlist_unique_together_wishlist_variant_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wishlist',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlisted', to='admin_app.variant'),
        ),
    ]
