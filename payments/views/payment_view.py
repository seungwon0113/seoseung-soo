
from typing import cast

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from membership.models import UserPoint
from payments.models import BankChoices
from payments.services.payment_service import PaymentService
from users.models import User


class PaymentView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        pre_order_key = request.GET.get('preOrderKey')
        toss_client_key = getattr(settings, 'TOSS_CLIENT_KEY', '')
        user = cast(User, request.user)

        context = PaymentService.prepare_payment_context(
            pre_order_key=pre_order_key,
            toss_client_key=toss_client_key,
            user_id=user.id
        )

        context['bank_choices'] = BankChoices.choices
        context['point_balance'] = UserPoint.get_user_balance(user)

        return render(request, 'payments/payment.html', context)

