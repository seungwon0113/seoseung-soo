import json
import uuid
from typing import Any, Dict, cast

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from config.utils.cache_helper import CacheHelper
from membership.models import UserPoint
from orders.services.order_services import OrderService
from payments.services.toss_payment_service import TossPaymentService
from users.models import User


@method_decorator(csrf_protect, name="dispatch")
class PointOnlyPaymentView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

        pre_order_key = data.get("preOrderKey")
        used_point = int(data.get("usedPoint", 0))

        if not pre_order_key:
            return JsonResponse({"error": "preOrderKey가 필요합니다."}, status=400)

        if used_point < 1000:
            return JsonResponse(
                {"error": "포인트는 최소 1,000P 이상부터 사용 가능합니다."},
                status=400,
            )

        user = cast(User, request.user)
        user_balance = UserPoint.get_user_balance(user)
        if user_balance < used_point:
            return JsonResponse({"error": "보유 포인트가 부족합니다."}, status=400)

        cache_data = CacheHelper.get(pre_order_key)
        if not cache_data:
            return JsonResponse(
                {"error": "주문 정보가 만료되었거나 유효하지 않습니다."},
                status=400,
            )

        if cache_data.get("user_id") != user.id:
            return JsonResponse({"error": "권한이 없습니다."}, status=403)

        items_data = cache_data.get("items", [])
        order_amount = int(cache_data.get("amount", 0))
        shipping_fee = TossPaymentService.calculate_shipping_fee(order_amount)
        total_amount = order_amount + shipping_fee

        if used_point < total_amount:
            return JsonResponse(
                {"error": "사용 포인트가 결제 금액보다 적습니다."},
                status=400,
            )

        used_point_value = total_amount

        is_valid, error_message, validated_items, _ = (
            OrderService.validate_and_prepare_order_items(items_data)
        )
        if not is_valid:
            return JsonResponse({"error": error_message}, status=400)

        order_id = TossPaymentService.generate_order_id()
        payment_key = f"point-only-{order_id}-{uuid.uuid4().hex[:8]}"

        try:
            TossPaymentService.create_order_and_payment(
                order_id=order_id,
                user_id=user.id,
                items_data=validated_items,
                amount=0,
                payment_key=payment_key,
                used_point=used_point_value,
                payment_method="POINT",
            )

            CacheHelper.delete(pre_order_key)

            request.session["payment_success"] = True
            request.session["order_id"] = order_id

            base_url = (
                settings.HOST_URL
                if not settings.DEBUG
                else request.build_absolute_uri("/")[:-1]
            )
            redirect_url = f"{base_url}/orders/status/"

            return JsonResponse(
                {
                    "success": True,
                    "redirectUrl": redirect_url,
                    "orderId": order_id,
                },
                status=200,
            )

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
