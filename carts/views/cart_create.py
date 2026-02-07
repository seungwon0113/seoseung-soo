from typing import cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views import View

from carts.forms.create import CartCreateForm
from carts.models import Cart
from products.utils.url_slug import product_name_to_slug
from users.models import User


class CartCreateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = CartCreateForm(request.POST)
        user = cast(User, request.user)
        if form.is_valid():
            product = form.cleaned_data['product_id']
            quantity = form.cleaned_data['quantity']
            color = form.cleaned_data.get('color_id')
            size = form.cleaned_data.get('size_id')

            existing_cart = Cart.objects.filter(user=user, product=product, color=color, size=size).first()

            if existing_cart:
                new_quantity = existing_cart.quantity + quantity
                if new_quantity > product.stock:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f'재고가 부족합니다. (현재 재고: {product.stock}개)'
                        })
                    messages.error(request, f'재고가 부족합니다. (현재 재고: {product.stock}개)')
                    return redirect('products-detail', product_name=product_name_to_slug(product.name))

                existing_cart.quantity = new_quantity
                existing_cart.save()
                message = f'{product.name} 상품이 장바구니에 추가되었습니다.'
            else:
                Cart.objects.create(
                    user=user,
                    product=product,
                    quantity=quantity,
                    color=color,
                    size=size,
                )
                message = f'{product.name} 상품이 장바구니에 추가되었습니다.'

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message
                })

            messages.success(request, message)
            return redirect('products-detail', product_name=product_name_to_slug(product.name))

        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(str(error))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': '; '.join(error_messages)
            })

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, str(error))

        product_name_from_post = request.POST.get('product_name', '')
        if product_name_from_post:
            return redirect('products-detail', product_name=product_name_to_slug(product_name_from_post))
        return redirect('customer-product-list')