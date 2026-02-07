import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from config.utils.setup_test_method import TestSetupMixin
from orders.models import Order
from orders.services.order_exchange_refund_services import OrderExchangeRefundService


@pytest.mark.django_db
class TestOrderExchangeRefundService(TestSetupMixin):
    def setup_method(self) -> None:
        self.setup_test_user_data()
        self.setup_test_products_data()
        self.setup_test_order_data()
        self.order.shipping_status = "DELIVERED"
        self.order.status = "PAID"
        self.order.save()

    def test_request_exchange_refund_success(self) -> None:
        request_type = Order.ExchangeRefundType.EXCHANGE
        reason = Order.ExchangeRefundReason.SIZE_MISMATCH
        
        success, message = OrderExchangeRefundService.request_exchange_refund(self.order, request_type, reason)
        
        assert success is True
        assert "접수되었습니다" in message
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "PENDING"
        assert self.order.exchange_refund_type == request_type
        assert self.order.exchange_refund_reason == reason
        assert self.order.exchange_refund_requested_at is not None

    def test_request_exchange_refund_not_delivered(self) -> None:
        self.order.shipping_status = "PENDING"
        self.order.save()
        request_type = Order.ExchangeRefundType.EXCHANGE
        reason = Order.ExchangeRefundReason.SIZE_MISMATCH
        
        success, message = OrderExchangeRefundService.request_exchange_refund(self.order, request_type, reason)
        
        assert success is False
        assert "배송 완료된 주문만" in message

    def test_request_exchange_refund_already_pending(self) -> None:
        self.order.exchange_refund_request_status = "PENDING"
        self.order.save()
        request_type = Order.ExchangeRefundType.EXCHANGE
        reason = Order.ExchangeRefundReason.SIZE_MISMATCH
        
        success, message = OrderExchangeRefundService.request_exchange_refund(self.order, request_type, reason)
        
        assert success is False
        assert "이미 교환/반품 요청이 처리되었거나 진행 중입니다" in message

    def test_approve_exchange_refund_success(self) -> None:
        self.order.exchange_refund_request_status = "PENDING"
        self.order.save()
        admin_note = "승인 메모"
        
        success, message = OrderExchangeRefundService.approve_exchange_refund(self.order, admin_note)
        
        assert success is True
        assert "승인되었습니다" in message
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "APPROVED"
        assert self.order.exchange_refund_admin_note == admin_note
        assert self.order.exchange_refund_processed_at is not None

    def test_approve_exchange_refund_without_admin_note(self) -> None:
        self.order.exchange_refund_request_status = "PENDING"
        self.order.save()
        
        success, message = OrderExchangeRefundService.approve_exchange_refund(self.order, None)
        
        assert success is True
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "APPROVED"

    def test_approve_exchange_refund_not_pending(self) -> None:
        self.order.exchange_refund_request_status = "APPROVED"
        self.order.save()
        
        success, message = OrderExchangeRefundService.approve_exchange_refund(self.order, None)
        
        assert success is False
        assert "처리할 수 없는 교환/반품 요청입니다" in message

    def test_reject_exchange_refund_success(self) -> None:
        self.order.exchange_refund_request_status = "PENDING"
        self.order.save()
        admin_note = "거부 사유"
        
        success, message = OrderExchangeRefundService.reject_exchange_refund(self.order, admin_note)
        
        assert success is True
        assert "거부되었습니다" in message
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "REJECTED"
        assert self.order.exchange_refund_admin_note == admin_note
        assert self.order.exchange_refund_processed_at is not None

    def test_reject_exchange_refund_empty_admin_note(self) -> None:
        self.order.exchange_refund_request_status = "PENDING"
        self.order.save()
        
        success, message = OrderExchangeRefundService.reject_exchange_refund(self.order, "")
        
        assert success is False
        assert "거부 사유를 입력해주세요" in message

    def test_reject_exchange_refund_whitespace_admin_note(self) -> None:
        self.order.exchange_refund_request_status = "PENDING"
        self.order.save()
        
        success, message = OrderExchangeRefundService.reject_exchange_refund(self.order, "   ")
        
        assert success is False
        assert "거부 사유를 입력해주세요" in message

    def test_reject_exchange_refund_not_pending(self) -> None:
        self.order.exchange_refund_request_status = "APPROVED"
        self.order.save()
        admin_note = "거부 사유"
        
        success, message = OrderExchangeRefundService.reject_exchange_refund(self.order, admin_note)
        
        assert success is False
        assert "처리할 수 없는 교환/반품 요청입니다" in message


@pytest.mark.django_db
class TestOrderExchangeRefundRequestView(TestSetupMixin):
    def setup_method(self) -> None:
        self.setup_test_user_data()
        self.setup_test_products_data()
        self.setup_test_order_data()
        self.order.user = self.customer_user
        self.order.shipping_status = "DELIVERED"
        self.order.status = "PAID"
        self.order.save()

    def test_get_redirects_to_status(self) -> None:
        self.client.force_login(self.customer_user)
        url = reverse("orders:exchange-refund-request", kwargs={"order_id": self.order.id})
        
        response = self.client.get(url)
        
        assert response.status_code == 302
        assert response["Location"] == reverse("orders:status")

    def test_post_valid_form(self) -> None:
        self.client.force_login(self.customer_user)
        url = reverse("orders:exchange-refund-request", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "type": Order.ExchangeRefundType.EXCHANGE,
            "reason": Order.ExchangeRefundReason.SIZE_MISMATCH,
        }, follow=True)
        
        assert response.status_code == 200
        messages_list = list(get_messages(response.wsgi_request))
        assert any("접수되었습니다" in str(msg) for msg in messages_list)
        
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "PENDING"

    def test_post_invalid_form(self) -> None:
        self.client.force_login(self.customer_user)
        url = reverse("orders:exchange-refund-request", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {}, follow=True)
        
        assert response.status_code == 200
        messages_list = list(get_messages(response.wsgi_request))
        assert len(messages_list) > 0, f"Expected error message, but got: {[str(msg) for msg in messages_list]}"

    def test_post_unauthorized_order(self) -> None:
        from users.models import User
        other_user = User.objects.create_user(
            role='customer',
            username='otheruser',
            email='other@example.com',
            password='password',
            personal_info_consent=True,
            terms_of_use=True
        )
        self.client.force_login(other_user)
        url = reverse("orders:exchange-refund-request", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "type": Order.ExchangeRefundType.EXCHANGE,
            "reason": Order.ExchangeRefundReason.SIZE_MISMATCH,
        })
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestAdminExchangeRefundListView(TestSetupMixin):
    def setup_method(self) -> None:
        self.setup_test_user_data()
        self.setup_test_products_data()
        self.setup_test_order_data()
        self.order.shipping_status = "DELIVERED"
        self.order.status = "PAID"
        self.order.exchange_refund_request_status = "PENDING"
        self.order.exchange_refund_type = Order.ExchangeRefundType.EXCHANGE
        self.order.exchange_refund_reason = Order.ExchangeRefundReason.SIZE_MISMATCH
        self.order.save()

    def test_list_view_requires_admin(self) -> None:
        self.client.force_login(self.customer_user)
        url = reverse("orders:admin-exchange-refund-list")
        
        response = self.client.get(url)
        
        assert response.status_code == 403

    def test_list_view_with_admin(self) -> None:
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-list")
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert "orders" in response.context

    def test_list_view_with_search_query(self) -> None:
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-list")
        
        response = self.client.get(url, {"q": self.order.order_id})
        
        assert response.status_code == 200
        orders = response.context["orders"]
        assert len(orders) > 0

    def test_list_view_with_status_filter(self) -> None:
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-list")
        
        response = self.client.get(url, {"status": "PENDING"})
        
        assert response.status_code == 200
        orders = response.context["orders"]
        assert len(orders) > 0


@pytest.mark.django_db
class TestAdminExchangeRefundProcessView(TestSetupMixin):
    def setup_method(self) -> None:
        self.setup_test_user_data()
        self.setup_test_products_data()
        self.setup_test_order_data()
        self.order.shipping_status = "DELIVERED"
        self.order.status = "PAID"
        self.order.exchange_refund_request_status = "PENDING"
        self.order.exchange_refund_type = Order.ExchangeRefundType.EXCHANGE
        self.order.exchange_refund_reason = Order.ExchangeRefundReason.SIZE_MISMATCH
        self.order.save()

    def test_approve_exchange_refund(self) -> None:
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-process", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "action": "approve",
            "admin_note": "승인 메모",
        })
        
        assert response.status_code == 302
        assert response["Location"] == reverse("orders:admin-exchange-refund-list")
        messages_list = list(get_messages(response.wsgi_request))
        assert len(messages_list) > 0
        assert any("승인되었습니다" in str(msg) for msg in messages_list)
        
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "APPROVED"

    def test_approve_exchange_refund_without_admin_note(self) -> None:
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-process", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "action": "approve",
            "admin_note": "",
        })
        
        assert response.status_code == 302
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "APPROVED"

    def test_reject_exchange_refund(self) -> None:
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-process", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "action": "reject",
            "admin_note": "거부 사유",
        })
        
        assert response.status_code == 302
        assert response["Location"] == reverse("orders:admin-exchange-refund-list")
        messages_list = list(get_messages(response.wsgi_request))
        assert len(messages_list) > 0
        assert any("거부되었습니다" in str(msg) for msg in messages_list)
        
        self.order.refresh_from_db()
        assert self.order.exchange_refund_request_status == "REJECTED"

    def test_invalid_action(self) -> None:
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-process", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "action": "invalid",
            "admin_note": "",
        })
        
        assert response.status_code == 302
        assert response["Location"] == reverse("orders:admin-exchange-refund-list")
        messages_list = list(get_messages(response.wsgi_request))
        assert len(messages_list) > 0
        assert any("잘못된 요청입니다" in str(msg) for msg in messages_list)

    def test_requires_admin(self) -> None:
        self.client.force_login(self.customer_user)
        url = reverse("orders:admin-exchange-refund-process", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "action": "approve",
            "admin_note": "",
        })
        
        assert response.status_code == 403

    def test_process_exchange_refund_error_message(self) -> None:
        self.order.exchange_refund_request_status = "APPROVED"
        self.order.save()
        self.client.force_login(self.admin_user)
        url = reverse("orders:admin-exchange-refund-process", kwargs={"order_id": self.order.id})
        
        response = self.client.post(url, {
            "action": "approve",
            "admin_note": "",
        }, follow=True)
        
        assert response.status_code == 200
        messages_list = list(get_messages(response.wsgi_request))
        assert len(messages_list) > 0
        assert any("처리할 수 없는" in str(msg) for msg in messages_list)
