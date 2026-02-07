import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_size_product_sizes'),
        ('carts', '0003_cart_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.size'),
        ),
    ]
