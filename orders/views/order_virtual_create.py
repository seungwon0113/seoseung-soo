import json
from typing import Any, Dict, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from config.utils.cache_helper import CacheHelper
from orders.models import Order, OrderItem
from orders.services.order_services import OrderService
from payments.services.toss_payment_service import TossPaymentService
from products.models import Color, Size
from users.models import User


@method_decorator(csrf_protect, name="dispatch")
class OrderCreateVirtualView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

        user = cast(User, request.user)

        pre_order_key = data.get("preOrderKey")
        if not pre_order_key:
            return JsonResponse({"error": "preOrderKey가 필요합니다."}, status=400)
        cache_data = CacheHelper.get(pre_order_key)
        if not cache_data:
            return JsonResponse(
                {"error": "주문 정보가 만료되었거나 유효하지 않습니다."},
                status=400,
            )
        if cache_data.get("user_id") != user.id:
            return JsonResponse({"error": "권한이 없습니다."}, status=403)
        items_data = cache_data.get("items", [])

        is_valid, error_message, validated_items, total_amount = (
            OrderService.validate_and_prepare_order_items(items_data)
        )

        if not is_valid:
            return JsonResponse({"error": error_message}, status=400)

        order_id = TossPaymentService.generate_order_id()
        order_name = TossPaymentService.generate_order_name(validated_items)

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                order_id=order_id,
                product_name=order_name,
                total_amount=int(total_amount),
                status="PENDING",
            )

            colors_map = OrderService.get_options_map(validated_items, "color_id", Color)
            sizes_map = OrderService.get_options_map(validated_items, "size_id", Size)

            order_items = []
            for item in validated_items:
                color_id = item.get("color_id")
                size_id = item.get("size_id")
                color = colors_map.get(color_id) if isinstance(color_id, int) else None
                size = sizes_map.get(size_id) if isinstance(size_id, int) else None
                order_items.append(
                    OrderItem(
                        order=order,
                        product_id=int(item["product_id"]),
                        product_name=item["product_name"],
                        quantity=int(item["quantity"]),
                        unit_price=int(item["unit_price"]),
                        subtotal=int(item["quantity"]) * int(item["unit_price"]),
                        color=color,
                        size=size,
                    )
                )

            OrderItem.objects.bulk_create(order_items)

        return JsonResponse({
            "success": True,
            "orderId": order_id,
            "totalAmount": int(total_amount),
            "status": "PENDING",
        }, status=200)
