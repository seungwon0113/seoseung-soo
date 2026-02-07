from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from products.forms.product_size import ProductSizeForm
from products.models import Size
from products.services.size import SizeService
from users.utils.permission import AdminPermission


class AdminProductSizeView(AdminPermission, View):
    def _get_context(self, form: ProductSizeForm) -> dict[str, Any]:
        return {
            "form": form,
            "sizes": SizeService.get_all_sizes(),
            "title": "사이즈 관리",
        }

    def get(self, request: HttpRequest) -> HttpResponse:
        context = self._get_context(ProductSizeForm())
        return render(request, "products/admin/admin_product_size.html", context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ProductSizeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("admin-product-size")
        context = self._get_context(form)
        return render(request, "products/admin/admin_product_size.html", context)


class AdminSizeUpdateView(AdminPermission, View):
    def _get_context(self, form: ProductSizeForm, size: Size) -> dict[str, Any]:
        return {
            "form": form,
            "sizes": SizeService.get_all_sizes(),
            "size": size,
            "title": "사이즈 수정",
        }

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        size = get_object_or_404(Size, pk=pk)
        form = ProductSizeForm(instance=size)
        context = self._get_context(form, size)
        return render(request, "products/admin/admin_product_size.html", context)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        size = get_object_or_404(Size, pk=pk)
        form = ProductSizeForm(request.POST, instance=size)
        if form.is_valid():
            form.save()
            return redirect("admin-product-size")
        context = self._get_context(form, size)
        return render(request, "products/admin/admin_product_size.html", context)


class AdminSizeDeleteView(AdminPermission, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        size = get_object_or_404(Size, pk=pk)
        size.delete()
        return redirect("admin-product-size")
