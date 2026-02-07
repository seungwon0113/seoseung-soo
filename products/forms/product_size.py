from django import forms

from products.models import Size


class ProductSizeForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = Size
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "사이즈 이름 (예: S, M, L, XL)"
            }),
        }
        labels = {
            "name": "사이즈 이름",
        }
