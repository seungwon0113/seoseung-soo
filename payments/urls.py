from django.urls import path

from payments.views import (
    PaymentView,
    TossConfirmView,
    TossFailView,
    TossPaymentRequestView,
    TossSuccessView,
)
from payments.views.point_only_view import PointOnlyPaymentView
from payments.views.virtual_bank_view import (
    TossVirtualRequestView,
    TossVirtualWebhookView,
)

app_name = "payments"

urlpatterns = [
    path("", PaymentView.as_view(), name="payment"),
    path("toss/request/", TossPaymentRequestView.as_view(), name="toss-request"),
    path("toss/success/", TossSuccessView.as_view(), name="toss-success"),
    path("toss/fail/", TossFailView.as_view(), name="toss-fail"),
    path("toss/confirm/", TossConfirmView.as_view(), name="toss-confirm"),
    path("toss/virtual/request/", TossVirtualRequestView.as_view(), name="toss-virtual-request"),
    path("toss/webhook/", TossVirtualWebhookView.as_view(), name="toss-webhook"),
    path("point-only/", PointOnlyPaymentView.as_view(), name="point-only"),
]
