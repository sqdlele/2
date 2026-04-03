from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from PIL import Image


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    available = models.BooleanField(default=True, verbose_name='Доступен')
    stock = models.PositiveIntegerField(default=0, verbose_name='Количество на складе')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False, verbose_name='Главное изображение')
    
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
    
    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)
        
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Корзина {self.user.username}'
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
    
    def get_total_price(self):
        return self.quantity * self.product.price


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Избранное {self.user.username}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Заказ #{self.id} - {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
    
    def get_total_price(self):
        return self.quantity * self.price