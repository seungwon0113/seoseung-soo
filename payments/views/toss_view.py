import json
from typing import Any, Dict, cast

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from config.utils.cache_helper import CacheHelper
from payments.services.toss_payment_service import TossPaymentService


@method_decorator(csrf_protect, name='dispatch')
class TossPaymentRequestView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

        pre_order_key = data.get("preOrderKey")
        if not pre_order_key:
            return JsonResponse({"error": "preOrderKey가 누락되었습니다."}, status=400)

        cache_data = CacheHelper.get(pre_order_key)
        if not cache_data:
            return JsonResponse({"error": "주문 정보가 만료되었거나 유효하지 않습니다."}, status=400)

        if cache_data.get("user_id") != request.user.id:
            return JsonResponse({"error": "권한이 없습니다."}, status=403)

        used_point = max(0, int(data.get("usedPoint", 0) or 0))
        order_total = int(cache_data.get("amount", 0))
        if used_point > order_total:
            return JsonResponse({"error": "사용 포인트가 주문 금액을 초과할 수 없습니다."}, status=400)

        cache_data["used_point"] = used_point
        CacheHelper.set(pre_order_key, cache_data, timeout=60 * 15)

        base_url = settings.HOST_URL if not settings.DEBUG else request.build_absolute_uri("/")[:-1]
        _, _, _, response_data = TossPaymentService.prepare_payment_request(
            pre_order_key=pre_order_key,
            cache_data=cache_data,
            base_url=base_url,
            used_point=used_point,
        )

        return JsonResponse(response_data, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class TossSuccessView(View):

    def get(self, request: HttpRequest) -> HttpResponse:
        payment_key = request.GET.get("paymentKey")
        order_id = request.GET.get("orderId")
        amount = request.GET.get("amount")
        pre_order_key = request.GET.get("preOrderKey")

        if not all([payment_key, order_id, amount]):
            return JsonResponse({"success": False, "error": "잘못된 요청입니다."}, status=400)

        order_id = cast(str, order_id)

        confirm_url = (
            f"/payments/toss/confirm/?paymentKey={payment_key}"
            f"&orderId={order_id}&amount={amount}"
            f"&preOrderKey={pre_order_key or ''}"
        )
        return redirect(confirm_url)


@method_decorator(csrf_exempt, name='dispatch')
class TossFailView(View):

    def get(self, request: HttpRequest) -> JsonResponse:
        pre_order_key = request.GET.get("preOrderKey")
        if pre_order_key:
            CacheHelper.delete(pre_order_key)

        return JsonResponse({
            "success": False,
            "message": request.GET.get("message", "결제 실패"),
        }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class TossConfirmView(View):

    def get(self, request: HttpRequest) -> HttpResponse:
        payment_key = request.GET.get("paymentKey")
        order_id = request.GET.get("orderId")
        amount_str = request.GET.get("amount")
        pre_order_key = request.GET.get("preOrderKey")

        if not all([payment_key, order_id, amount_str, pre_order_key]):
            return JsonResponse({"success": False, "error": "요청 정보 누락"}, status=400)

        payment_key = cast(str, payment_key)
        order_id = cast(str, order_id)
        amount_str = cast(str, amount_str)
        pre_order_key = cast(str, pre_order_key)

        try:
            amount = int(amount_str)
        except (ValueError, TypeError):
            return JsonResponse({"success": False, "error": "잘못된 금액 형식"}, status=400)

        is_success, error_message, payment_data, status_code = (
            TossPaymentService.confirm_payment_with_api(
                payment_key=payment_key,
                order_id=order_id,
                amount=amount
            )
        )

        if not is_success:
            return JsonResponse({"success": False, "error": error_message}, status=400)

        # 캐시 데이터 확인
        cache_data = CacheHelper.get(pre_order_key)
        if cache_data is None:
            return JsonResponse(
                {"success": False, "error": "preOrderKey가 만료되었거나 유효하지 않습니다."},
                status=400,
            )

        # 사용자 확인
        user_id = cache_data.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "error": "유효하지 않은 사용자"}, status=400)

        # 결제 금액 검증
        is_valid, error_message = TossPaymentService.validate_payment_amount(cache_data, amount)
        if not is_valid:
            return JsonResponse({"success": False, "error": error_message}, status=400)

        # 주문 및 결제 정보 생성
        items_data = cache_data.get("items", [])
        request_url = f"{settings.TOSS_API_BASE}/payments/confirm"
        request_payload = {"paymentKey": payment_key, "orderId": order_id, "amount": amount}

        used_point = int(cache_data.get("used_point", 0)) if cache_data.get("used_point") else 0

        try:
            TossPaymentService.create_order_and_payment(
                order_id=order_id,
                user_id=user_id,
                items_data=items_data,
                amount=amount,
                payment_key=payment_key,
                payment_data=payment_data,
                request_url=request_url,
                request_payload=request_payload,
                response_status_code=status_code,
                used_point=used_point,
            )
        except IntegrityError:
            return JsonResponse({"success": True, "message": "이미 승인된 결제입니다."}, status=200)

        # 캐시 삭제
        CacheHelper.delete(pre_order_key)

        # 세션에 성공 정보 저장
        request.session['payment_success'] = True
        request.session['order_id'] = order_id

        return redirect('orders:status')



