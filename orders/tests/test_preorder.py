import json
from typing import Any, Dict

import pytest
from django.urls import reverse

from config.utils.cache_helper import CacheHelper
from config.utils.setup_test_method import TestSetupMixin


@pytest.mark.django_db
class TestPreorder(TestSetupMixin):
    def setup_method(self) -> None:
        self.setup_test_user_data()
        self.setup_test_products_data()
        
    def test_requires_authentication(self) -> None:
        response = self.client.post(reverse("orders:preorder"))
        assert response.status_code == 302

    def test_invalid_json(self) -> None:
        self.client.force_login(self.customer_user)
        response = self.client.post(
            reverse("orders:preorder"),
            data="{invalid_json}",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "잘못된 요청입니다." in response.json()["message"]
        
    def test_preorder_success(self) -> None:
        self.client.force_login(self.customer_user)

        payload: Dict[str, Any] = {
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 2,
                }
            ]
        }

        response = self.client.post(
            reverse("orders:preorder"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "redirectUrl" in data
        redirect_url: str = data["redirectUrl"]
        assert redirect_url.startswith("/payments/?preOrderKey=")

        pre_order_key = redirect_url.split("preOrderKey=", 1)[1]
        assert pre_order_key.startswith("order:preorder:")

        cached = CacheHelper.get(pre_order_key)
        assert cached is not None
        assert cached["user_id"] == self.customer_user.id
        assert len(cached["items"]) == 1

    def test_preorder_invalid_items(self) -> None:
        self.client.force_login(self.customer_user)

        payload: Dict[str, Any] = {
            "items": [
                {
                    "product_id": 999999,
                    "quantity": 1,
                }
            ]
        }

        response = self.client.post(
            reverse("orders:preorder"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "존재하지 않는 상품" in data["message"]