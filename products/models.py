from typing import Any

from django.db import models

from categories.models import Category
from config.basemodel import BaseModel
from config.utils.image_path import image_upload_path
from users.models import User


def product_image_upload_path(instance: 'ProductImage', filename: str) -> str:
    return image_upload_path('products', filename)


class ProductImage(BaseModel):
    image = models.ImageField(upload_to=product_image_upload_path)
    
    class Meta:
        db_table = 'products_image'

class Size(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        db_table = 'products_size'

class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, blank=True, null=True)  # 예: #ff0000 (선택적)
    class Meta:
        db_table = 'products_color'

class Product(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, null=True, blank=True, db_index=True)
    description = models.TextField()
    image = models.ManyToManyField(ProductImage, blank=True, db_table='product_image_cdt')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.IntegerField()
    is_live = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, blank=True, db_table='product_category_cdt')
    colors = models.ManyToManyField(Color, blank=True, db_table='product_color_cdt')
    sizes = models.ManyToManyField(Size, blank=True, db_table='product_size_cdt')
    
    class Meta:
        db_table = 'products'
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        from products.utils.url_slug import product_name_to_slug
        
        should_regenerate_slug = not self.slug
        if self.pk and not should_regenerate_slug:
            try:
                old_product = Product.objects.get(pk=self.pk)
                if old_product.name != self.name:
                    should_regenerate_slug = True
            except Product.DoesNotExist:
                should_regenerate_slug = True

        if should_regenerate_slug:
            base_slug = product_name_to_slug(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class WishList(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    class Meta:
        db_table = 'wish_list'