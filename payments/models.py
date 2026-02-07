from django.db import models
from django.utils import timezone

from membership.models import UserPoint
from orders.models import Order


class BankChoices(models.TextChoices):
    KOOKMIN = "KOOKMIN", "국민은행"
    SHINHAN = "SHINHAN", "신한은행"
    WOORI = "WOORI", "우리은행"
    NH = "NH", "농협은행"



class Payment(models.Model):
    """PG 결제 정보"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")

    provider = models.CharField(  # PG사 구분
        max_length=20,
        choices=[
            ("toss", "토스페이"),
            ("kakao", "카카오페이"),
            ("payco", "페이코"),
            ("naver", "네이버페이"),
            ("bank", "무통장입금"),
        ],
    )

    method = models.CharField(  # 결제 수단
        max_length=30,
        choices=[
            ("CARD", "신용카드"),
            ("EASY_PAY", "간편결제"),
            ("TRANSFER", "계좌이체"),
            ("VBANK", "가상계좌"),
            ("VIRTUAL_ACCOUNT", "무통장입금"),
            ("POINT", "포인트"),
        ],
    )

    payment_key = models.CharField(max_length=100, unique=True)
    amount = models.PositiveIntegerField()
    approved_at = models.DateTimeField(null=True, blank=True)
    receipt_url = models.URLField(null=True, blank=True)
    is_used_point = models.BooleanField(default=False, verbose_name="포인트 사용 여부")
    used_point = models.PositiveIntegerField(default=0, verbose_name="사용 포인트 금액")
    earned_point = models.PositiveIntegerField(default=0, verbose_name="포인트 적립금")

    status = models.CharField(
        max_length=20,
        choices=[
            ("REQUESTED", "요청됨"),
            ("WAITING_FOR_DEPOSIT", "입금대기"),
            ("APPROVED", "승인됨"),
            ("CANCELLED", "취소됨"),
            ("FAILED", "실패"),
        ],
        default="REQUESTED",
    )

    raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 무통장입금용 필드
    bank_name = models.CharField(
        max_length=20,
        choices=BankChoices.choices,
        blank=True,
        null=True,
        help_text="Toss API 은행 코드"
    )
    account_number = models.CharField(max_length=50, null=True, blank=True)
    account_holder = models.CharField(max_length=100, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)

    def approve(self) -> None:
        """결제 승인 처리 (포인트 차감 및 적립)"""
        if self.status == "APPROVED":
            # 이미 승인 처리된 결제는 중복으로 처리하지 않음
            return

        user = self.order.user

        current_balance = UserPoint.get_user_balance(user)

        if self.used_point > 0:
            if current_balance < self.used_point:
                raise ValueError("보유 포인트가 부족합니다.")

            current_balance -= self.used_point
            UserPoint.objects.create(
                user=user,
                point_type=UserPoint.PointType.USE,
                amount=-self.used_point,
                description=f"주문 {self.order.order_id} 결제 사용",
                balance_after=current_balance,
                related_order=self.order,
            )
            self.is_used_point = True

        self.status = "APPROVED"
        self.approved_at = timezone.now()

        earn_amount = int(self.order.total_amount * 0.05)  # 예: 5% 적립
        if earn_amount > 0:
            new_balance = current_balance + earn_amount
            UserPoint.objects.create(
                user=user,
                point_type=UserPoint.PointType.EARN,
                amount=earn_amount,
                description=f"주문 {self.order.order_id} 결제 적립",
                balance_after=new_balance,
                related_order=self.order,
            )
            self.earned_point = earn_amount

        self.save(
            update_fields=[
                "status",
                "approved_at",
                "is_used_point",
                "earned_point",
            ]
        )
        self.order.status = "PAID"
        self.order.save(update_fields=["status"])


class PaymentLog(models.Model):
    """PG 요청/응답 로그"""

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="logs",
        null=True,
        blank=True,
    )
    provider = models.CharField(max_length=20)
    event_type = models.CharField(max_length=50)  # APPROVE / CANCEL / REFUND 등
    request_url = models.CharField(max_length=255, null=True, blank=True)
    request_payload = models.JSONField()
    response_payload = models.JSONField(null=True, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.provider}] {self.event_type} ({self.status_code})"
