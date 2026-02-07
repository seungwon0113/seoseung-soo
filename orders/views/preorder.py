import json
from typing import Any, Dict, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.views import View

from orders.services.order_services import OrderService
from users.models import User


class OrderPreorderView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "잘못된 요청입니다."}, status=400)

        items_data = data.get("items", [])
        is_valid, error_message, validated_items, total_amount = (
            OrderService.validate_and_prepare_order_items(items_data)
        )
        if not is_valid:
            return JsonResponse({"success": False, "message": error_message}, status=400)

        user = cast(User, request.user)
        preorder_key = OrderService.create_preorder_cache(user.id, validated_items, total_amount)

        return JsonResponse(
            {
                "success": True,
                "redirectUrl": f"/payments/?preOrderKey={preorder_key}",
            }
        )
