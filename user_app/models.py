from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password



class UserDetailsManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class UserDetails(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=15, default="Anonymous")
    lastname = models.CharField(max_length=15, default="Anonymous")
    email = models.EmailField(max_length=254, unique=True)
    phone = models.CharField(max_length=15, unique=True, default="0000000000")
    password = models.CharField(max_length=128)
    otp = models.IntegerField(null=True, blank=True)
    otp_created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstname', 'lastname', 'phone']

    objects = UserDetailsManager()

    def save(self, *args, **kwargs):
        if self.pk:  # Check if the instance is already created
            original = UserDetails.objects.get(pk=self.pk)
            self.email = original.email  # Revert email changes
        super().save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)


from django.db import models
from django.conf import settings


class Address(models.Model):
    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('work', 'Work'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address_line = models.TextField()
    location = models.CharField(max_length=100)
    landmark = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')
    is_delete=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.address_type}"
    
from django.conf import settings
from django.db import models

class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    variant = models.ForeignKey(
        'admin_app.Variant',  # Reference to the Variant model in the admin app
        on_delete=models.CASCADE,
        related_name='wishlisted'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')  # Prevent duplicate wishlist entries

    def __str__(self):
        return f"{self.user.email} - {self.variant.product.product_name} ({self.variant.name})"




class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

# Transaction Model to keep track of wallet transactions
class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, related_name='transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('credit', 'Credit'), ('debit', 'Debit')])
    description = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of ₹{self.amount} on {self.date}"
