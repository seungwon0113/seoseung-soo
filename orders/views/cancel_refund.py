from typing import cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from orders.models import Order
from orders.services.order_services import OrderStatisticsService
from users.models import User


class CancelRefundView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        user = cast(User, request.user)

        orders = Order.objects.filter(user=user)

        order_stats = OrderStatisticsService.calculate_order_stats(orders)
        cancellation_exchange_refund_stats = OrderStatisticsService.calculate_cancellation_exchange_refund_stats(orders)

        cancellation_exchange_refund_orders = orders.filter(
            Q(cancellation_request_status__in=[Order.CancellationRequestStatus.PENDING, Order.CancellationRequestStatus.APPROVED, Order.CancellationRequestStatus.REJECTED]) |
            Q(exchange_refund_request_status__in=[Order.ExchangeRefundRequestStatus.PENDING, Order.ExchangeRefundRequestStatus.APPROVED, Order.ExchangeRefundRequestStatus.REJECTED])
        )
        cancellation_exchange_refund_orders = cancellation_exchange_refund_orders.distinct().order_by('-created_at').prefetch_related('items__color', 'items__size')[:10]

        OrderStatisticsService.attach_products_to_orders(list(cancellation_exchange_refund_orders))

        context = {
            'user': user,
            'order_stats': order_stats,
            'cancellation_exchange_refund_stats': cancellation_exchange_refund_stats,
            'cancellation_exchange_refund_orders': cancellation_exchange_refund_orders,
            'current_page': 'orders',
        }

        return render(request, "orders/cancel_refund.html", context)
