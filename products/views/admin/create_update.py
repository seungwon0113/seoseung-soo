from typing import cast

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from products.forms.product_form import ProductForm, ProductImageForm
from products.models import Product, ProductImage
from products.services.color import ColorService
from products.services.size import SizeService
from users.models import User
from users.utils.permission import AdminPermission


class ProductCreateView(AdminPermission, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        form = ProductForm()
        image_form = ProductImageForm()
        colors = ColorService.get_all_colors()
        sizes = SizeService.get_all_sizes()
        context = {
            'form': form,
            'image_form': image_form,
            'colors': colors,
            'sizes': sizes,
            'title': '상품 등록'
        }
        return render(request, 'products/admin/admin_product_create.html', context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ProductForm(request.POST)
        image_form = ProductImageForm(request.POST, request.FILES)
        
        if form.is_valid() and image_form.is_valid():
            product = form.save(commit=False)
            product.user = cast(User, request.user)
            product.save()
            
            form.save_m2m()
            
            images = request.FILES.getlist('image')
            if images:
                # TODO: i 변수를 사용하고 있지않음 확인 후 수정 필요
                for i, image in enumerate(images):
                    product_image = ProductImage.objects.create(image=image)
                    product.image.add(product_image)
            
            return redirect('product-list')
        
        colors = ColorService.get_all_colors()
        sizes = SizeService.get_all_sizes()
        context = {
            'form': form,
            'image_form': image_form,
            'colors': colors,
            'sizes': sizes,
            'title': '상품 등록'
        }
        return render(request, 'products/admin/admin_product_create.html', context)


class ProductUpdateView(AdminPermission, View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(instance=product)
        image_form = ProductImageForm()
        colors = ColorService.get_all_colors()
        sizes = SizeService.get_all_sizes()
        context = {
            'form': form,
            'image_form': image_form,
            'product': product,
            'colors': colors,
            'sizes': sizes,
            'title': '상품 수정'
        }
        return render(request, 'products/admin/admin_product_create.html', context)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(request.POST, instance=product)
        image_form = ProductImageForm(request.POST, request.FILES)
        
        if form.is_valid() and image_form.is_valid():
            form.save()
            
            # 새 이미지 추가 (이미지가 있는 경우에만)
            images = request.FILES.getlist('image')
            if images:
                for image in images:
                    product_image = ProductImage.objects.create(image=image)
                    product.image.add(product_image)
            
            return redirect('product-list')
        
        colors = ColorService.get_all_colors()
        sizes = SizeService.get_all_sizes()
        context = {
            'form': form,
            'image_form': image_form,
            'product': product,
            'colors': colors,
            'sizes': sizes,
            'title': '상품 수정'
        }
        return render(request, 'products/admin/admin_product_create.html', context)


