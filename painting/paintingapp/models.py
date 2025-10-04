from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='category_images/')

    def __str__(self):
        return self.name

class Artist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='artists/', null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    payment_method = models.CharField(max_length=50, default='COD')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class UserSubmission(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='user_submissions/')
    artist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class CustomizedPainting(models.Model):
    STYLE_CHOICES = [
        ('oil', 'Oil Painting'),
        ('watercolor', 'Watercolor'),
        ('sketch', 'Sketch'),
        ('popart', 'Pop Art'),
        ('impressionist', 'Impressionist'),
    ]

    SIZE_CHOICES = [
        ('small', 'Small (12" x 16")'),
        ('medium', 'Medium (16" x 20")'),
        ('large', 'Large (20" x 24")'),
        ('xlarge', 'Extra Large (24" x 36")'),
    ]

    FRAME_CHOICES = [
        ('none', 'No Frame'),
        ('classic', 'Classic Wood'),
        ('modern', 'Modern Metal'),
        ('vintage', 'Vintage Gold'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    style = models.CharField(max_length=20, choices=STYLE_CHOICES)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES)
    frame = models.CharField(max_length=20, choices=FRAME_CHOICES)
    image = models.ImageField(upload_to='customized_paintings/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    class Meta:
        ordering = ['-created_at']
