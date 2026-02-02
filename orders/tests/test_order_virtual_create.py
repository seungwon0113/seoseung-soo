import json
from typing import Any, Dict

import pytest
from django.urls import reverse

from config.utils.setup_test_method import TestSetupMixin
from orders.models import Order, OrderItem
from orders.services.order_services import OrderService
from products.models import Color


@pytest.mark.django_db
class TestOrderCreateVirtualView(TestSetupMixin):
    def setup_method(self) -> None:
        self.setup_test_user_data()
        self.setup_test_products_data()

    def test_requires_authentication(self) -> None:
        response = self.client.post(reverse("orders:virtual-create"))
        assert response.status_code == 302

    def test_invalid_json(self) -> None:
        self.client.force_login(self.customer_user)
        response = self.client.post(
            reverse("orders:virtual-create"),
            data="{invalid_json}",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "잘못된 JSON 형식" in response.json()["error"]

    def test_create_virtual_order_success(self) -> None:
        self.client.force_login(self.customer_user)
        self.product.price = 35000
        self.product.save()

        items_data = [
            {
                "product_id": self.product.id,
                "quantity": 2,
            }
        ]

        is_valid, error_message, validated_items, total_amount = (
            OrderService.validate_and_prepare_order_items(items_data)
        )
        assert is_valid

        preorder_key = OrderService.create_preorder_cache(
            self.customer_user.id, validated_items, total_amount
        )

        payload: Dict[str, Any] = {
            "preOrderKey": preorder_key
        }

        response = self.client.post(
            reverse("orders:virtual-create"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "orderId" in data
        assert data["status"] == "PENDING"
        assert data["totalAmount"] == 70000

        order = Order.objects.get(order_id=data["orderId"])
        assert order.user == self.customer_user
        assert order.status == Order.Status.PENDING
        assert order.total_amount == 70000

        order_items = OrderItem.objects.filter(order=order)
        assert order_items.count() == 1
        order_item = order_items.first()
        assert order_item is not None
        assert order_item.quantity == 2

    def test_create_virtual_order_with_color(self) -> None:
        self.client.force_login(self.customer_user)
        self.product.price = 35000
        self.product.save()
        color = Color.objects.create(name="빨강", hex_code="#FF0000")
        self.product.colors.add(color)

        items_data = [
            {
                "product_id": self.product.id,
                "color_id": color.id,
                "quantity": 1,
            }
        ]

        is_valid, error_message, validated_items, total_amount = (
            OrderService.validate_and_prepare_order_items(items_data)
        )
        assert is_valid

        preorder_key = OrderService.create_preorder_cache(
            self.customer_user.id, validated_items, total_amount
        )

        payload: Dict[str, Any] = {
            "preOrderKey": preorder_key
        }

        response = self.client.post(
            reverse("orders:virtual-create"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        order = Order.objects.get(order_id=data["orderId"])
        order_item = OrderItem.objects.filter(order=order).first()
        assert order_item is not None
        assert order_item.color == color

    def test_create_virtual_order_missing_preorder_key(self) -> None:
        self.client.force_login(self.customer_user)

        payload: Dict[str, Any] = {
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 1,
                }
            ]
        }

        response = self.client.post(
            reverse("orders:virtual-create"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "preOrderKey가 필요합니다." in data["error"]

    def test_create_virtual_order_invalid_preorder_key(self) -> None:
        self.client.force_login(self.customer_user)

        payload: Dict[str, Any] = {
            "preOrderKey": "order:preorder:invalid"
        }

        response = self.client.post(
            reverse("orders:virtual-create"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "주문 정보가 만료되었거나 유효하지 않습니다." in data["error"]

    def test_create_virtual_order_unauthorized_preorder_key(self) -> None:
        self.client.force_login(self.customer_user)
        self.product.price = 35000
        self.product.save()

        items_data = [
            {
                "product_id": self.product.id,
                "quantity": 1,
            }
        ]

        is_valid, error_message, validated_items, total_amount = (
            OrderService.validate_and_prepare_order_items(items_data)
        )
        assert is_valid

        preorder_key = OrderService.create_preorder_cache(
            self.admin_user.id, validated_items, total_amount
        )

        payload: Dict[str, Any] = {
            "preOrderKey": preorder_key
        }

        response = self.client.post(
            reverse("orders:virtual-create"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert "권한이 없습니다." in data["error"]
