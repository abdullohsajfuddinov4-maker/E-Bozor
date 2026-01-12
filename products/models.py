from django.db import models
from users.models import CustomUser
from django.db.models import Avg
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Product(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=17)
    tg_username = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    count = models.PositiveIntegerField(default=1) # new

    @property
    def average_rating(self):
        avg = self.comments.filter(rating__gt=0).aggregate(avg=Avg('rating'))['avg']
        return avg or 0

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-id',)


class ProductImage(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to='product_images')


class Comment(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    body = models.CharField(max_length=150)
    rating = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Comment of {self.author.username}"
