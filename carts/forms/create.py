from typing import Any, cast

from django import forms

from products.models import Color, Product, Size


class CartCreateForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, initial=1)
    color_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    size_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs.update({
            'class': 'form-control',
            'min': '1'
        })
    
    def clean_product_id(self) -> Product:
        product_id = cast(int, self.cleaned_data.get('product_id'))
        try:
            product = Product.objects.get(id=product_id)
            return product
        except Product.DoesNotExist:
            raise forms.ValidationError('존재하지 않는 상품입니다.')

    def clean_color_id(self) -> Color | None:
        color_id = self.cleaned_data.get('color_id')
        if not color_id:
            return None
        try:
            return Color.objects.get(id=color_id)
        except Color.DoesNotExist:
            raise forms.ValidationError('존재하지 않는 색상입니다.')

    def clean_size_id(self) -> Size | None:
        size_id = self.cleaned_data.get('size_id')
        if not size_id:
            return None
        try:
            return Size.objects.get(id=size_id)
        except Size.DoesNotExist:
            raise forms.ValidationError('존재하지 않는 사이즈입니다.')

    def clean(self) -> dict[str, Any]:
        cleaned_data = cast(dict[str, Any], super().clean())

        product = cast(Product | None, cleaned_data.get('product_id'))
        quantity = cast(int | None, cleaned_data.get('quantity'))

        if product and quantity:
            if quantity > product.stock:
                self.add_error('quantity', '재고가 부족합니다.')

        return cleaned_data