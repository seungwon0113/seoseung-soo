import base64
import os
import uuid
from typing import Any, Dict, List, Tuple

import requests
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from carts.models import Cart
from orders.models import Order, OrderItem
from orders.services.order_services import OrderService
from payments.models import Payment, PaymentLog
from products.models import Color, Size

TOSS_API_BASE = os.getenv("TOSS_API_BASE")


class TossPaymentService:
    @staticmethod
    def get_toss_headers() -> Dict[str, str]:
        secret_key = os.getenv("TOSS_SECRET_KEY", "")
        if not secret_key:
            raise ValueError("TOSS_SECRET_KEY not found in environment")

        encoded_key = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("utf-8")

        return {
            "Authorization": f"Basic {encoded_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def generate_order_id() -> str:
        return f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    @staticmethod
    def generate_order_name(items_data: List[Dict[str, Any]]) -> str:
        if len(items_data) == 1:
            product_name = items_data[0].get("product_name", "상품")
            return str(product_name) if product_name else "상품"
        product_name = items_data[0].get('product_name', '상품')
        return f"{str(product_name) if product_name else '상품'} 외 {len(items_data) - 1}건"

    @staticmethod
    def calculate_shipping_fee(amount: int) -> int:
        return 0 if amount >= 50000 else 3000

    @staticmethod
    def prepare_payment_request(
        pre_order_key: str,
        cache_data: Dict[str, Any],
        base_url: str,
        used_point: int = 0,
    ) -> Tuple[str, str, int, Dict[str, Any]]:
        order_id = TossPaymentService.generate_order_id()
        items_data = cache_data.get("items", [])
        order_name = TossPaymentService.generate_order_name(items_data)
        order_total = int(cache_data.get("amount", 0))
        used_point_value = max(0, int(used_point))
        amount_after_point = max(0, order_total - used_point_value)
        shipping_fee = TossPaymentService.calculate_shipping_fee(order_total)
        final_amount = amount_after_point + shipping_fee

        success_url = f"{base_url}/payments/toss/success/?preOrderKey={pre_order_key}"
        fail_url = f"{base_url}/payments/toss/fail/?preOrderKey={pre_order_key}"

        return order_id, order_name, final_amount, {
            "success": True,
            "orderId": order_id,
            "amount": final_amount,
            "orderName": order_name,
            "successUrl": success_url,
            "failUrl": fail_url,
        }

    @staticmethod
    def confirm_payment_with_api(
        payment_key: str,
        order_id: str,
        amount: int
    ) -> Tuple[bool, str, Dict[str, Any], int]:
        url = f"{TOSS_API_BASE}/payments/confirm"
        payload = {"paymentKey": payment_key, "orderId": order_id, "amount": amount}

        try:
            res = requests.post(
                url,
                headers=TossPaymentService.get_toss_headers(),
                json=payload,
                timeout=10
            )
            data: Dict[str, Any] = res.json()

            if res.status_code == 200:
                return True, "", data, res.status_code
            else:
                PaymentLog.objects.create(
                    provider="toss",
                    event_type="CONFIRM_FAIL",
                    request_url=url,
                    request_payload=payload,
                    response_payload=data,
                    status_code=res.status_code,
                )
                error_message = data.get("message", "결제 승인 실패")
                return False, error_message, data, res.status_code

        except requests.exceptions.RequestException as e:
            PaymentLog.objects.create(
                provider="toss",
                event_type="CONFIRM",
                request_url=url,
                request_payload=payload,
                response_payload={"error": str(e)},
                status_code=503,
            )
            return False, "결제 승인 요청 중 오류 발생", {}, 503

    @staticmethod
    def validate_payment_amount(cache_data: Dict[str, Any], amount: int) -> Tuple[bool, str]:
        order_total = int(cache_data.get("amount", 0))
        used_point = int(cache_data.get("used_point", 0)) or 0
        amount_after_point = max(0, order_total - used_point)
        shipping_fee = TossPaymentService.calculate_shipping_fee(order_total)
        expected_final_amount = amount_after_point + shipping_fee

        if expected_final_amount != amount:
            return False, "결제 금액이 주문 정보와 일치하지 않습니다."
        return True, ""

    @staticmethod
    def create_order_and_payment(
        order_id: str,
        user_id: int,
        items_data: List[Dict[str, Any]],
        amount: int,
        payment_key: str,
        payment_data: Dict[str, Any],
        request_url: str,
        request_payload: Dict[str, Any],
        response_status_code: int,
        used_point: int = 0,
    ) -> None:
        user = get_user_model().objects.get(id=user_id)
        order_name = TossPaymentService.generate_order_name(items_data)

        metadata_used_point = 0
        metadata = payment_data.get("metadata")
        if isinstance(metadata, dict):
            metadata_used_point = int(metadata.get("usedPoint", 0))

        used_point_value = used_point if used_point else metadata_used_point
        used_point_value = max(0, used_point_value)

        with transaction.atomic():
            order = Order.objects.create(
                order_id=order_id,
                user=user,
                product_name=order_name,
                total_amount=amount,
                status="PENDING",
            )

            colors_map = OrderService.get_options_map(items_data, "color_id", Color)
            sizes_map = OrderService.get_options_map(items_data, "size_id", Size)

            order_items = []
            for item_data in items_data:
                color_id = item_data.get("color_id")
                size_id = item_data.get("size_id")
                color = colors_map.get(color_id) if color_id and isinstance(color_id, int) else None
                size = sizes_map.get(size_id) if size_id and isinstance(size_id, int) else None

                order_items.append(
                    OrderItem(
                        order=order,
                        product_id=item_data["product_id"],
                        product_name=item_data["product_name"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        subtotal=item_data["quantity"] * item_data["unit_price"],
                        color=color,
                        size=size,
                    )
                )
            OrderItem.objects.bulk_create(order_items)

            payment = Payment.objects.create(
                order=order,
                provider="toss",
                method=payment_data.get("method", "CARD"),
                payment_key=str(payment_key),
                amount=amount,
                receipt_url=payment_data.get("receipt", {}).get("url", ""),
                status="REQUESTED",
                used_point=used_point_value,
                raw_response=payment_data,
            )

            payment.approve()

            PaymentLog.objects.create(
                provider="toss",
                event_type="CONFIRM",
                request_url=request_url,
                request_payload=request_payload,
                response_payload=payment_data,
                status_code=response_status_code,
                payment=payment,
            )

            TossPaymentService.clear_cart_after_payment(user_id, items_data)

    @staticmethod
    def clear_cart_after_payment(user_id: int, items_data: List[Dict[str, Any]]) -> None:
        user = get_user_model().objects.get(id=user_id)

        product_ids = [item["product_id"] for item in items_data if item.get("product_id") is not None]
        if not product_ids:
            return

        all_cart_items = Cart.objects.filter(
            user=user,
            product_id__in=product_ids
        ).select_related('color', 'size').order_by('id')

        cart_items_by_key: Dict[tuple[int, int | None, int | None], List[Cart]] = {}
        for cart_item in all_cart_items:
            key = (cart_item.product_id, cart_item.color_id, cart_item.size_id)
            if key not in cart_items_by_key:
                cart_items_by_key[key] = []
            cart_items_by_key[key].append(cart_item)

        items_to_delete: List[Cart] = []
        items_to_update: List[Cart] = []

        for item_data in items_data:
            product_id = item_data.get("product_id")
            color_id = item_data.get("color_id")
            size_id = item_data.get("size_id")
            order_quantity = item_data.get("quantity", 1)

            if product_id is None:
                continue

            key = (product_id, color_id, size_id)
            cart_items = cart_items_by_key.get(key, [])

            if not cart_items:
                continue

            remaining_quantity = order_quantity
            for cart_item in cart_items:
                if remaining_quantity <= 0:
                    break

                if cart_item.quantity <= remaining_quantity:
                    remaining_quantity -= cart_item.quantity
                    items_to_delete.append(cart_item)
                else:
                    cart_item.quantity -= remaining_quantity
                    items_to_update.append(cart_item)
                    remaining_quantity = 0

        if items_to_delete:
            Cart.objects.filter(id__in=[item.id for item in items_to_delete]).delete()

        if items_to_update:
            Cart.objects.bulk_update(items_to_update, ['quantity'])
