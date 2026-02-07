from typing import Any, List, Union, cast

from django import forms
from django.core.files.uploadedfile import UploadedFile

from products.models import Product


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data: Any, initial: Any = None) -> Union[List[UploadedFile], UploadedFile, None]:
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ProductForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'sale_price', 'stock', 'is_live', 'is_sold', 'categories', 'colors', 'sizes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '상품명을 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': '상품 설명을 입력하세요',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '가격을 입력하세요',
                'step': '0.01',
                'min': '0'
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '할인가격을 입력하세요 (선택사항)',
                'step': '0.01',
                'min': '0'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '재고 수량을 입력하세요',
                'min': '0'
            }),
            'is_live': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'is_sold': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-checkbox-multiple'
            }),
            'colors': forms.SelectMultiple(attrs={
                'class': 'form-select-multiple'
            }),
            'sizes': forms.SelectMultiple(attrs={
                'class': 'form-select-multiple'
            })
        }

    def clean_price(self) -> float:
        price = cast(float, self.cleaned_data.get('price'))
        if price <= 0:
            raise forms.ValidationError("가격은 0보다 커야 합니다.")
        return price

    def clean_stock(self) -> int:
        stock = cast(int, self.cleaned_data.get('stock'))
        if stock < 0:
            raise forms.ValidationError("재고는 0 이상이어야 합니다.")
        return stock

    def clean_sale_price(self) -> Union[float, None]:
        sale_price = self.cleaned_data.get('sale_price')
        if sale_price is not None:
            if sale_price < 0:
                raise forms.ValidationError("할인 금액은 0보다 크거나 같아야 합니다.")
            price = self.cleaned_data.get('price')
            if price and sale_price > price:
                raise forms.ValidationError("할인 금액은 정가보다 클 수 없습니다.")
        return sale_price


class ProductImageForm(forms.Form):
    image: MultipleFileField = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-file',
            'accept': 'image/*',
            'multiple': True,
            'id': 'id_image'
        })
    )

