from django.db import models
import cloudinary, cloudinary.uploader
import cloudinary
from cloudinary.models import CloudinaryField
from user_app.models import UserDetails,Address
from django.utils import timezone
from django.db.models import Avg
from django.conf import settings
from decimal import Decimal




# Create your models here.

class categorys(models.Model):
    id=models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=100)
    is_active=models.BooleanField(default=True)
    is_delete=models.BooleanField(default=False)


    def __str__(self):
        return self.name
    
import uuid
class Product(models.Model):
    product_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    product_name = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)  # Make discount optional
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=100)
    description = models.TextField(max_length=2000)
    category = models.ForeignKey(categorys, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_delete=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # For new arrivals sorting


    @property
    def total_quantity(self):
        """Calculate total quantity based on variants."""
        return sum(variant.stock for variant in self.variants.all())

    def __str__(self):
        return self.product_name
    
    def delete(self, using=None, keep_parents=False):
        self.is_delete = True
        self.save()

  
    
class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=10,blank=True,null=True)  
    color = models.CharField(max_length=50, blank=True,null=True)  # E.g., "Red", "Blue"
    stock = models.PositiveIntegerField(default=0,blank=True,null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Stock for this variant
    is_active = models.BooleanField(default=True)

    @property
    def is_out_of_stock(self):
        """Check if this variant is out of stock."""
        return self.stock == 0

    def reduce_stock(self, quantity):
        """Reduce stock when an order is placed."""
        if quantity > self.stock:
            raise ValueError("Insufficient stock for this variant.")
        self.stock -= quantity
        self.save()
        
    def __str__(self):
        return f"{self.product.product_name} - {self.size or 'No size'} - {self.color or 'No color'}"

    

class VariantImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='images')
    image = cloudinary.models.CloudinaryField('image', folder='variant_images/')
    is_primary = models.BooleanField(default=False)  

    def __str__(self):
        return f"Image for {self.variant.product.product_name} - {self.variant.color} ({self.variant.size})"
    
User = UserDetails()


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart'
    )
    coupon = models.ForeignKey(
        'Coupon', null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
        return sum(item.total_price for item in self.cart_items.all())

    def calculate_discount(self):
        if self.coupon:
            if self.coupon.discount_type == 'percentage':
                return self.calculate_total() * (self.coupon.discount_value / 100)
            elif self.coupon.discount_type == 'fixed':
                return min(self.coupon.discount_value, self.calculate_total())
        return 0

    def calculate_grand_total(self):
        return self.calculate_total() - self.calculate_discount()

    

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    price = models.IntegerField()
    quantity = models.PositiveIntegerField(default=1)
    discount=models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.variant.product.product_name} ({self.variant.size or 'No size'}, {self.variant.color or 'No color'}) in {self.cart.user.email}'s cart"

    @property
    def total_price(self):
        """Calculate the total price for this cart item based on the variant."""
        return self.quantity * self.variant.price
    


class Order(models.Model):
   

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery'),
        ('wallet', 'Wallet')
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,  # Address can be null for now in case of order modification
        related_name='orders',
        null=True,
        blank=True
    )
    order_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)  # Flag to track payment status
    is_delivered = models.BooleanField(default=False)
    delivery_date = models.DateTimeField(null=True, blank=True)
    is_delivered = models.BooleanField(default=False)
    

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"

    def calculate_total(self):
        """Calculate the total amount for the order based on items."""
        self.total_amount = sum(item.total_price for item in self.order_items.all())
        self.save()

    def mark_as_paid(self):
        """Mark the order as paid."""
        self.is_paid = True
        self.save()

    def mark_as_delivered(self):
        """Mark the order as delivered."""
        self.is_delivered = True
        self.delivery_date = timezone.now()
        self.save()

    def process_payment(self):
        """Handle wallet payment logic."""
        if self.payment_method == 'wallet':
            if self.user.wallet.balance >= self.total_amount:
                self.user.wallet.debit(self.total_amount)
                self.mark_as_paid()
            else:
                raise ValueError("Insufficient wallet balance")

    def __str__(self):
        status = "Paid" if self.is_paid else "Pending"
        delivery_status = "Delivered" if self.is_delivered else "Not Delivered"
        return f"Order {self.id} - {status} - {delivery_status}"



class OrderItem(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
        ('returned', 'Returned'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')



    def __str__(self):
        return f"{self.quantity} x {self.variant.product.product_name} ({self.variant.size or 'No size'}, {self.variant.color or 'No color'})"

    @property
    def total_price(self):
        """Calculate the total price for this order item."""
        return self.quantity * self.price
    

class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating between 1 and 5
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.product_name} by {self.user.email}"

    class Meta:
        ordering = ['-created_at']  # Order reviews by the most recent first



from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    # Unique coupon code
    code = models.CharField(max_length=20, unique=True)
    
    # Coupon name (added as per the view)
    name = models.CharField(max_length=100)  
    
    # Condition or restrictions related to the coupon
    condition = models.TextField(null=True, blank=True)
    
    # Offer rate (additional discount rate for specific offers)
    offer_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Expiry date of the coupon (validity date)
    validity_date = models.DateTimeField(null=True, blank=True)

    # Discount type (Percentage or Fixed Amount)
    discount_type = models.CharField(
        max_length=10, choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')]
    )
    
    # The value of the discount
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Maximum uses for the coupon
    max_uses = models.PositiveIntegerField(default=1,null=True, blank=True)
    
    # Tracks the number of times the coupon has been used
    used_count = models.PositiveIntegerField(default=0)
    is_delete = models.BooleanField(default=False)  # Add this field
    is_active = models.BooleanField(default=True)   # Optional

    def is_valid(self):
        """Check if the coupon is still valid based on various conditions."""
        if self.validity_date and self.validity_date < timezone.now():
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True
    
    # def is_valid(self):
    #     """Check if the coupon is valid."""
    #     if self.validity_date and self.validity_date < now():
    #         return False
    #     if self.max_uses and self.used_count >= self.max_uses:
    #         return False
    #     return True


    def __str__(self):
        return self.name  # Return the name of the coupon


