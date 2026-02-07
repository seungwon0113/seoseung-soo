from django.urls import path

from products.views.admin.create_update import ProductCreateView, ProductUpdateView
from products.views.admin.delete_image import DeleteProductImageView
from products.views.admin.detail_or_list import AdminMypageView, AdminProductListView
from products.views.admin.product_color_views import (
    AdminColorDeleteView,
    AdminColorUpdateView,
    AdminProductColorView,
)
from products.views.admin.product_size_views import (
    AdminProductSizeView,
    AdminSizeDeleteView,
    AdminSizeUpdateView,
)
from products.views.customers.product_list import ProductListView
from products.views.products_detail import ProductsDetailView

urlpatterns = [
    path("<str:product_name>", ProductsDetailView.as_view(), name="products-detail"),
    path("admin_page/", AdminMypageView.as_view(), name="admin-mypage"),
    path("admin/products_list/", AdminProductListView.as_view(), name="product-list"),
    path("admin/create/", ProductCreateView.as_view(), name="product-create"),
    path("admin/<int:pk>/update/", ProductUpdateView.as_view(), name="product-update"),
    path("admin/image/<int:image_id>/delete/", DeleteProductImageView.as_view(), name="product-delete-image"),
    path("admin/color/", AdminProductColorView.as_view(), name="admin-product-color"),
    path("admin/color/<int:pk>/update/", AdminColorUpdateView.as_view(), name="admin-color-update"),
    path("admin/color/<int:pk>/delete/", AdminColorDeleteView.as_view(), name="admin-color-delete"),
    path("admin/size/", AdminProductSizeView.as_view(), name="admin-product-size"),
    path("admin/size/<int:pk>/update/", AdminSizeUpdateView.as_view(), name="admin-size-update"),
    path("admin/size/<int:pk>/delete/", AdminSizeDeleteView.as_view(), name="admin-size-delete"),
    path("list/", ProductListView.as_view(), name="customer-product-list"),
]