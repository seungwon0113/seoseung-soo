from typing import cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from orders.forms.cancellation import OrderCancellationForm
from orders.forms.exchange_refund import OrderExchangeRefundForm
from orders.models import Order
from orders.services.order_services import OrderStatisticsService
from users.models import User


class OrderView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        user = cast(User, request.user)

        orders = Order.objects.filter(user=user)
        order_stats = OrderStatisticsService.calculate_order_stats(orders)
        cancellation_exchange_refund_stats = OrderStatisticsService.calculate_cancellation_exchange_refund_stats(orders)

        shipping_orders = orders.filter(
            status=Order.Status.PAID,
            shipping_status__in=[Order.ShippingStatus.PENDING, Order.ShippingStatus.SHIPPING, Order.ShippingStatus.DELIVERED],
            cancellation_request_status=Order.CancellationRequestStatus.NONE,
            exchange_refund_request_status=Order.ExchangeRefundRequestStatus.NONE
        ).order_by('-created_at').prefetch_related('items__color', 'items__size')[:10]

        OrderStatisticsService.attach_products_to_orders(list(shipping_orders))

        payment_success = request.session.pop('payment_success', False)
        order_id = request.session.pop('order_id', None)

        cancellation_form = OrderCancellationForm()
        exchange_refund_form = OrderExchangeRefundForm()
        
        context = {
            'user': user,
            'order_stats': order_stats,
            'cancellation_exchange_refund_stats': cancellation_exchange_refund_stats,
            'shipping_orders': shipping_orders,
            'current_page': 'orders',
            'payment_success': payment_success,
            'order_id': order_id,
            'cancellation_form': cancellation_form,
            'exchange_refund_form': exchange_refund_form,
        }

        return render(request, "orders/order_mypage.html", context)


