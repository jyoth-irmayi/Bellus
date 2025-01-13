# Generated by Django 5.1.3 on 2024-12-16 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0033_cart_coupon'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coupon',
            old_name='expiry_date',
            new_name='validity_date',
        ),
        migrations.AddField(
            model_name='coupon',
            name='condition',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='coupon',
            name='name',
            field=models.CharField(default=True, max_length=100),
        ),
        migrations.AddField(
            model_name='coupon',
            name='offer_rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
