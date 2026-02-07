from typing import Tuple

from django.utils import timezone

from orders.models import Order


class OrderExchangeRefundService:
    @staticmethod
    def request_exchange_refund(order: Order, request_type: str, reason: str) -> Tuple[bool, str]:
        if order.shipping_status != Order.ShippingStatus.DELIVERED:
            return False, "배송 완료된 주문만 교환/반품이 가능합니다."
        
        if order.exchange_refund_request_status != Order.ExchangeRefundRequestStatus.NONE:
            return False, "이미 교환/반품 요청이 처리되었거나 진행 중입니다."
        
        order.exchange_refund_request_status = Order.ExchangeRefundRequestStatus.PENDING
        order.exchange_refund_type = request_type
        order.exchange_refund_reason = reason
        order.exchange_refund_requested_at = timezone.now()
        order.save(update_fields=["exchange_refund_request_status", "exchange_refund_type", "exchange_refund_reason", "exchange_refund_requested_at"])
        
        return True, "교환/반품 요청이 접수되었습니다. 관리자 검토 후 처리됩니다."

    @staticmethod
    def approve_exchange_refund(order: Order, admin_note: str | None = None) -> Tuple[bool, str]:
        if order.exchange_refund_request_status != Order.ExchangeRefundRequestStatus.PENDING:
            return False, "처리할 수 없는 교환/반품 요청입니다."
        
        order.exchange_refund_request_status = Order.ExchangeRefundRequestStatus.APPROVED
        order.exchange_refund_processed_at = timezone.now()
        if admin_note:
            order.exchange_refund_admin_note = admin_note
        order.save(update_fields=["exchange_refund_request_status", "exchange_refund_processed_at", "exchange_refund_admin_note"])
        
        return True, f"주문 {order.order_id}의 교환/반품 요청이 승인되었습니다."

    @staticmethod
    def reject_exchange_refund(order: Order, admin_note: str) -> Tuple[bool, str]:
        if order.exchange_refund_request_status != Order.ExchangeRefundRequestStatus.PENDING:
            return False, "처리할 수 없는 교환/반품 요청입니다."
        
        if not admin_note or not admin_note.strip():
            return False, "거부 사유를 입력해주세요."
        
        order.exchange_refund_request_status = Order.ExchangeRefundRequestStatus.REJECTED
        order.exchange_refund_processed_at = timezone.now()
        order.exchange_refund_admin_note = admin_note.strip()
        order.save(update_fields=["exchange_refund_request_status", "exchange_refund_processed_at", "exchange_refund_admin_note"])
        
        return True, f"주문 {order.order_id}의 교환/반품 요청이 거부되었습니다."
