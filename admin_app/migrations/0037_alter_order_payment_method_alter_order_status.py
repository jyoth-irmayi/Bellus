# Generated by Django 5.1.3 on 2024-12-17 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0036_remove_coupon_min_order_value_coupon_is_active_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('paypal', 'PayPal'), ('cod', 'Cash on Delivery'), ('wallet', 'Wallet')], default='cod', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('canceled', 'Canceled'), ('returned', 'Returned')], default='pending', max_length=20),
        ),
    ]
