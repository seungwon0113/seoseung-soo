from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from config.utils.filtering import Filtering
from orders.models import Order
from orders.services.order_cancellation_services import OrderCancellationService
from users.utils.permission import AdminPermission


class AdminCancellationListView(AdminPermission, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        q = (request.GET.get("q") or "").strip()
        status = (request.GET.get("status") or "").strip()

        orders_qs = Filtering.cancellation_list_filter(request)

        base_qs = Order.objects.filter(
            cancellation_request_status__in=[
                Order.CancellationRequestStatus.PENDING,
                Order.CancellationRequestStatus.APPROVED,
                Order.CancellationRequestStatus.REJECTED,
            ]
        )
        agg = base_qs.aggregate(
            pending=Count("id", filter=Q(cancellation_request_status=Order.CancellationRequestStatus.PENDING)),
            approved=Count("id", filter=Q(cancellation_request_status=Order.CancellationRequestStatus.APPROVED)),
            rejected=Count("id", filter=Q(cancellation_request_status=Order.CancellationRequestStatus.REJECTED)),
        )
        cancellation_stats = {
            "pending": agg["pending"],
            "approved": agg["approved"],
            "rejected": agg["rejected"],
        }

        paginator = Paginator(orders_qs, 20)
        page_obj = paginator.get_page(request.GET.get("page") or "1")

        context = {
            "q": q,
            "status": status,
            "page_obj": page_obj,
            "orders": page_obj.object_list,
            "cancellation_stats": cancellation_stats,
        }
        return render(request, "orders/admin/cancellation_list.html", context)


class AdminCancellationProcessView(AdminPermission, View):
    def post(self, request: HttpRequest, order_id: int) -> HttpResponse:
        action = request.POST.get("action")
        admin_note = request.POST.get("admin_note", "").strip()

        order = get_object_or_404(Order, id=order_id)
        
        if action == "approve":
            success, message = OrderCancellationService.approve_cancellation(order, admin_note if admin_note else None)
        elif action == "reject":
            success, message = OrderCancellationService.reject_cancellation(order, admin_note)
        else:
            messages.error(request, "잘못된 요청입니다.")
            return redirect("orders:admin-cancellation-list")
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect("orders:admin-cancellation-list")
