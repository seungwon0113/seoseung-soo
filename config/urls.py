from django.conf.urls.static import static
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import include, path
from django.views.generic import TemplateView

from config import settings
from config.utils.naver_sitemap import sitemap
from users import urls as users_urls


def home(request: HttpRequest) -> HttpResponse:
    from products.models import Product
    from config.models import SiteSetting

    products = Product.objects.filter(is_live=True, is_sold=False).prefetch_related('colors', 'image').order_by('-created_at')
    site_settings = SiteSetting.get_settings()
    context = {
        'products': products,
        'site_settings': site_settings,
    }
    return render(request, 'home.html', context)

urlpatterns = [
    path('', home, name='home'),
    path('sitemap.xml/', sitemap, name='sitemap'),
    path('payments/', include("payments.urls"), name='payments'),
    path("users/", include(users_urls), name='users'),
    path("products/", include("products.urls"), name='products'),
    path("categories/", include("categories.urls"), name='categories'),
    path("reviews/", include("reviews.urls"), name='reviews'),
    path("inquire/", include("inquire.urls"), name='inquire'),
    path("carts/", include("carts.urls"), name='carts'),
    path("favorites/", include("favorites.urls"), name='favorites'),
    path('robots.txt/', TemplateView.as_view(template_name="../templates/users/robots.txt", content_type='text/plain')),
    path("orders/", include("orders.urls"), name='orders'),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
