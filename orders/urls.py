from django.urls import path

from .views import OrderCreateView, OrderView
from .views.admin.cancellation import (
    AdminCancellationListView,
    AdminCancellationProcessView,
)
from .views.admin.exchange_refund import (
    AdminExchangeRefundListView,
    AdminExchangeRefundProcessView,
)
from .views.admin.order_list import AdminOrderListView
from .views.admin.shipping_management import ShippingManagementView
from .views.cancel_refund import CancelRefundView
from .views.cancellation import OrderCancellationRequestView
from .views.exchange_refund import OrderExchangeRefundRequestView
from .views.order_virtual_create import OrderCreateVirtualView
from .views.preorder import OrderPreorderView

app_name = "orders"

urlpatterns = [
    path("status/", OrderView.as_view(), name="status"),
    path("cancel-refund/", CancelRefundView.as_view(), name="cancel-refund"),
    path("create/", OrderCreateView.as_view(), name="create"),
    path("virtual/create/", OrderCreateVirtualView.as_view(), name="virtual-create"),
    path("preorder/", OrderPreorderView.as_view(), name="preorder"),
    path("cancel/<int:order_id>/", OrderCancellationRequestView.as_view(), name="cancel-request"),
    path("exchange-refund/<int:order_id>/", OrderExchangeRefundRequestView.as_view(), name="exchange-refund-request"),
    path("admin/list/", AdminOrderListView.as_view(), name="admin-order-list"),
    path("admin/shipping/", ShippingManagementView.as_view(), name="admin-shipping-management"),
    path("admin/cancellation/", AdminCancellationListView.as_view(), name="admin-cancellation-list"),
    path("admin/cancellation/<int:order_id>/process/", AdminCancellationProcessView.as_view(), name="admin-cancellation-process"),
    path("admin/exchange-refund/", AdminExchangeRefundListView.as_view(), name="admin-exchange-refund-list"),
    path("admin/exchange-refund/<int:order_id>/process/", AdminExchangeRefundProcessView.as_view(), name="admin-exchange-refund-process"),
]
