from typing import Any

from django.conf import settings
from django.db import models

from products.models import Color, Size


class Order(models.Model):
    class CancellationRequestStatus(models.TextChoices):
        NONE = "NONE", "없음"
        PENDING = "PENDING", "취소요청"
        APPROVED = "APPROVED", "취소승인"
        REJECTED = "REJECTED", "취소거부"
        
    class CancellationReason(models.TextChoices):
        NOT_LIKE_COLOR = "NOT_LIKE_COLOR", "색상이 마음에 안 들어요"
        NOT_LIKE_DESIGN = "NOT_LIKE_DESIGN", "디자인이 마음에 안 들어요"
        LONG_TIME_DELIVERY = "LONG_TIME_DELIVERY", "배송 시간이 길어요"
        SIMPLE_CHANGE_OF_MIND = "SIMPLE_CHANGE_OF_MIND", "단순히 마음 바뀜"
        TOO_EXPENSIVE = "TOO_EXPENSIVE", "너무 비싸요"
        NO_NEED_ANYMORE = "NO_NEED_ANYMORE", "필요 없어졌어요"
        OTHER = "OTHER", "기타"
        
    class Status(models.TextChoices):
        PENDING = "PENDING", "결제대기"
        PAID = "PAID", "결제완료"
        CANCELLED = "CANCELLED", "결제취소"
        FAILED = "FAILED", "결제실패"
    
    class ShippingStatus(models.TextChoices):
        PENDING = "PENDING", "배송대기"
        SHIPPING = "SHIPPING", "배송중"
        DELIVERED = "DELIVERED", "배송완료"

    class ExchangeRefundRequestStatus(models.TextChoices):
        NONE = "NONE", "없음"
        PENDING = "PENDING", "교환/반품요청"
        APPROVED = "APPROVED", "교환/반품승인"
        REJECTED = "REJECTED", "교환/반품거부"
    
    class ExchangeRefundType(models.TextChoices):
        EXCHANGE = "EXCHANGE", "교환"
        REFUND = "REFUND", "환불"
    
    class ExchangeRefundReason(models.TextChoices):
        SIZE_MISMATCH = "SIZE_MISMATCH", "사이즈가 안 맞아요"
        NOT_LIKE_COLOR = "NOT_LIKE_COLOR", "색상이 마음에 안 들어요"
        NOT_LIKE_DESIGN = "NOT_LIKE_DESIGN", "디자인이 마음에 안 들어요"
        WRONG_PRODUCT = "WRONG_PRODUCT", "다른 상품이 왔어요"
        DEFECTIVE = "DEFECTIVE", "제품 불량이에요"
        WRONG_DELIVERY = "WRONG_DELIVERY", "배송 오류"
        OTHER = "OTHER", "기타"
        
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=64, unique=True)
    product_name = models.CharField(max_length=255)
    total_amount = models.PositiveIntegerField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    shipping_status = models.CharField(max_length=20, choices=ShippingStatus.choices, default=ShippingStatus.PENDING)
    
    cancellation_request_status = models.CharField(max_length=20, choices=CancellationRequestStatus.choices, default=CancellationRequestStatus.NONE)
    cancellation_reason = models.CharField(max_length=50, choices=CancellationReason.choices, null=True, blank=True)
    cancellation_requested_at = models.DateTimeField(null=True, blank=True, verbose_name="취소 요청 시간")
    cancellation_processed_at = models.DateTimeField(null=True, blank=True, verbose_name="취소 처리 시간")
    cancellation_admin_note = models.TextField(null=True, blank=True, verbose_name="관리자 메모")
    
    exchange_refund_request_status = models.CharField(max_length=20, choices=ExchangeRefundRequestStatus.choices, default=ExchangeRefundRequestStatus.NONE, verbose_name="교환/반품 요청 상태")
    exchange_refund_type = models.CharField(max_length=20, choices=ExchangeRefundType.choices, null=True, blank=True, verbose_name="교환/반품 유형")
    exchange_refund_reason = models.CharField(max_length=50, choices=ExchangeRefundReason.choices, null=True, blank=True, verbose_name="교환/반품 사유")
    exchange_refund_requested_at = models.DateTimeField(null=True, blank=True, verbose_name="교환/반품 요청 시간")
    exchange_refund_processed_at = models.DateTimeField(null=True, blank=True, verbose_name="교환/반품 처리 시간")
    exchange_refund_admin_note = models.TextField(null=True, blank=True, verbose_name="관리자 메모")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"[{self.order_id}] {self.user} ({self.status})"


class OrderItem(models.Model):
    """주문 상세 항목"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.PositiveIntegerField()
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField()
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        # 자동으로 subtotal 계산
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"
