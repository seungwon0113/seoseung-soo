import uuid
from decimal import Decimal
from typing import Any, Dict, List, Tuple, TypeVar

from django.db.models import Count, Model, Q, QuerySet
from django.utils import timezone

from config.utils.cache_helper import CacheHelper
from orders.models import Order
from products.models import Color, Product, Size

T = TypeVar("T", bound=Model)


class OrderService:
    @staticmethod
    def generate_preorder_key() -> str:
        return f"order:preorder:{uuid.uuid4().hex[:10]}"

    @staticmethod
    def validate_products(product_ids: List[int]) -> Tuple[bool, str, Dict[int, Product]]:
        products = Product.objects.filter(id__in=product_ids).prefetch_related('colors', 'sizes')
        product_map = {p.id: p for p in products}

        if len(product_ids) != len(product_map):
            return False, "존재하지 않는 상품이 포함되어 있습니다.", {}

        return True, "", product_map

    @staticmethod
    def _validate_option(
        option_id: int,
        product: Product,
        model: type[T],
        product_relation_name: str,
        option_name: str,
        option_name_subject: str,
    ) -> Tuple[bool, str]:
        if not model.objects.filter(id=option_id).exists():  # type: ignore[attr-defined]
            return False, f"존재하지 않는 {option_name}입니다."

        product_relation = getattr(product, product_relation_name)
        if not product_relation.filter(id=option_id).exists():
            return False, f"'{product.name}' 상품에 선택하신 {option_name_subject} 존재하지 않습니다."

        return True, ""

    @staticmethod
    def validate_color(color_id: int, product: Product) -> Tuple[bool, str]:
        return OrderService._validate_option(color_id, product, Color, "colors", "색상", "색상이")

    @staticmethod
    def validate_size(size_id: int, product: Product) -> Tuple[bool, str]:
        return OrderService._validate_option(size_id, product, Size, "sizes", "사이즈", "사이즈가")

    @staticmethod
    def get_options_map(
        items: List[Dict[str, Any]], option_key: str, model: type[T]
    ) -> Dict[int, T]:
        option_ids = [item[option_key] for item in items if item.get(option_key)]
        if not option_ids:
            return {}
        return {obj.id: obj for obj in model.objects.filter(id__in=option_ids)}  # type: ignore[attr-defined]

    @staticmethod
    def calculate_item_price(product: Product) -> Decimal:
        if product.sale_price:
            return Decimal(str(product.price)) - Decimal(str(product.sale_price))
        return Decimal(str(product.price))

    @staticmethod
    def validate_and_prepare_order_items(
        items_data: List[Dict[str, Any]]
    ) -> Tuple[bool, str, List[Dict[str, Any]], Decimal]:
        if not items_data:
            return False, "주문 항목이 비어있습니다.", [], Decimal("0.0")

        product_ids = list(set([item["product_id"] for item in items_data if "product_id" in item]))

        is_valid, error_message, product_map = OrderService.validate_products(product_ids)
        if not is_valid:
            return False, error_message, [], Decimal("0.0")

        validated_items: List[Dict[str, Any]] = []
        total_amount = Decimal("0.0")

        for item in items_data:
            product_id = item["product_id"]
            product = product_map[product_id]
            color_id = item.get("color_id")
            size_id = item.get("size_id")

            if color_id:
                is_valid, error_message = OrderService.validate_color(color_id, product)
                if not is_valid:
                    return False, error_message, [], Decimal("0.0")

            if size_id:
                is_valid, error_message = OrderService.validate_size(size_id, product)
                if not is_valid:
                    return False, error_message, [], Decimal("0.0")

            quantity = int(item.get("quantity", 1))
            price = OrderService.calculate_item_price(product)
            item_total = price * quantity
            total_amount += item_total

            validated_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": quantity,
                "unit_price": int(price),
                "color_id": color_id,
                "size_id": size_id,
            })

        return True, "", validated_items, total_amount

    @staticmethod
    def create_preorder_cache(
        user_id: int, validated_items: List[Dict[str, Any]], total_amount: Decimal
    ) -> str:
        preorder_key = OrderService.generate_preorder_key()
        cache_data = {
            "user_id": user_id,
            "items": validated_items,
            "amount": int(total_amount),
            "created_at": timezone.now().isoformat(),
        }

        CacheHelper.set(preorder_key, cache_data, timeout=60 * 15)

        return preorder_key


class OrderStatisticsService:
    @staticmethod
    def calculate_order_stats(orders: QuerySet[Order]) -> Dict[str, int]:
        return orders.filter(status=Order.Status.PAID).aggregate(
            preparing=Count('id', filter=Q(shipping_status=Order.ShippingStatus.PENDING)),
            shipping=Count('id', filter=Q(shipping_status=Order.ShippingStatus.SHIPPING)),
            delivered=Count('id', filter=Q(shipping_status=Order.ShippingStatus.DELIVERED)),
        )

    @staticmethod
    def calculate_cancellation_exchange_refund_stats(orders: QuerySet[Order]) -> Dict[str, int]:
        return orders.aggregate(
            cancellation=Count('id', filter=Q(
                cancellation_request_status__in=[Order.CancellationRequestStatus.PENDING, Order.CancellationRequestStatus.APPROVED]
            )),
            exchange=Count('id', filter=Q(
                exchange_refund_request_status__in=[Order.ExchangeRefundRequestStatus.PENDING, Order.ExchangeRefundRequestStatus.APPROVED],
                exchange_refund_type=Order.ExchangeRefundType.EXCHANGE
            )),
            refund=Count('id', filter=Q(
                exchange_refund_request_status__in=[Order.ExchangeRefundRequestStatus.PENDING, Order.ExchangeRefundRequestStatus.APPROVED],
                exchange_refund_type=Order.ExchangeRefundType.REFUND
            )),
        )

    @staticmethod
    def attach_products_to_orders(orders_list: List[Order]) -> None:
        all_product_ids: set[int] = set()
        for order in orders_list:
            order.items_list = list(order.items.all())  # type: ignore[attr-defined]
            for item in order.items_list:  # type: ignore[attr-defined]
                all_product_ids.add(item.product_id)

        products_dict: Dict[int, Product]
        if all_product_ids:
            products = Product.objects.filter(id__in=all_product_ids).prefetch_related('image', 'colors')
            products_dict = {p.id: p for p in products}
        else:
            products_dict = {}

        for order in orders_list:
            for item in order.items_list:  # type: ignore[attr-defined]
                item.product = products_dict.get(item.product_id)