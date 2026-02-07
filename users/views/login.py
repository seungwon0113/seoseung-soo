from typing import cast

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from users.forms.login import LoginForm
from users.models import User


class LoginView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        user = cast(User, request.user)
        if user.is_authenticated:
            return redirect('home')
        next_url = request.GET.get("next", "")
        if next_url:
            request.session["login_next"] = next_url
        form = LoginForm()
        context = {
            'form': form,
            'google_client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'kakao_rest_api_key': settings.KAKAO_REST_API_KEY,
            'next': next_url,
        }
        return render(request, 'users/login.html', context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = LoginForm(request.POST)
        next_url = request.POST.get("next") or request.GET.get("next")
        context = {
            'form': form,
            'google_client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'kakao_rest_api_key': settings.KAKAO_REST_API_KEY,
            'next': next_url or "",
        }
        if form.is_valid():
            # 실제 로그인 로직 추가
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    return redirect(next_url)
                else:
                    return redirect('home')
            else:
                form.add_error(None, '유효하지 않은 사용자명 또는 비밀번호입니다.')

        return render(request, 'users/login.html', context)

class LogoutView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        return redirect('home')