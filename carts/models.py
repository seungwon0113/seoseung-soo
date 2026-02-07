from django.core.validators import MinValueValidator
from django.db import models

from config.basemodel import BaseModel
from products.models import Color, Product, Size
from users.models import User


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'carts'