# Generated by Django 5.0.7 on 2025-01-28 14:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0014_alter_wishlist_unique_together_wishlist_variant_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wishlist',
            name='variant',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='wishlisted', to='admin_app.variantsize'),
        ),
    ]


