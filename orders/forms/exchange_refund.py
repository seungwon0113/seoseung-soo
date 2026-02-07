from django import forms

from orders.models import Order


class OrderExchangeRefundForm(forms.Form):
    type = forms.ChoiceField(
        label="교환/반품 유형",
        choices=[('', '--- 교환/반품 유형을 선택해주세요 ---')] + list(Order.ExchangeRefundType.choices),
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control",
            "id": "exchangeRefundType"
        }),
        help_text="교환 또는 반품을 선택해주세요."
    )
    reason = forms.ChoiceField(
        label="교환/반품 사유",
        choices=[('', '--- 교환/반품 사유를 선택해주세요 ---')] + list(Order.ExchangeRefundReason.choices),
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control",
            "id": "exchangeRefundReason"
        }),
        help_text="교환/반품 사유를 선택해주세요."
    )
