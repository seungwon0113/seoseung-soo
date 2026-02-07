import json
import logging
import uuid
from typing import Optional

from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from users.services.oauth_state import OAuthStateService
from users.services.social_login import (
    AppleLoginService,
    GoogleLoginService,
    NaverLoginService,
)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleLoginView(View):
    
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            # JSON 데이터 파싱
            data = json.loads(request.body)
            credential = data.get('credential')
            
            if not credential:
                return JsonResponse({
                    'success': False,
                    'message': 'Google 인증 정보가 없습니다.'
                }, status=400)
            
            # Google 로그인 서비스로 인증 처리
            user, error = GoogleLoginService.authenticate_user(credential)

            if error:
                return JsonResponse({
                    'success': False,
                    'message': error
                }, status=400)

            if user:
                # 사용자 로그인
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                
                next_url = request.GET.get('next') or request.session.pop('login_next', '/')
                if not url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    next_url = '/'  # 안전하지 않은 URL은 홈페이지로 리다이렉트
                
                return JsonResponse({
                    'success': True,
                    'message': 'Google 로그인에 성공했습니다. 홈페이지로 이동합니다.',
                    'redirect_url': next_url,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.role
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '사용자 인증에 실패했습니다.'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 JSON 형식입니다.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'서버 오류가 발생했습니다: {str(e)}'
            }, status=500)


class NaverLoginView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        # CSRF 공격 방지를 위한 랜덤 state 값 생성
        state = uuid.uuid4().hex

        # 나중에 콜백에서 비교하기 위해 세션에 저장
        request.session["naver_state"] = state

        login_url = NaverLoginService.get_login_url(state)
        return redirect(login_url)

class NaverCallbackView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        code: Optional[str] = request.GET.get("code")
        state: Optional[str] = request.GET.get("state")
        session_state: Optional[str] = request.session.get("naver_state")

        # state 불일치 시 CSRF 의심 요청으로 간주
        if code is None or state is None or state != session_state:
            logging.warning(f"CSRF suspicion: code={code}, state={state}, session_state={session_state}")
            messages.error(request, "잘못된 접근입니다.")
            return redirect("login")

        access_token = NaverLoginService.get_access_token(code, state)
        if not access_token:
            messages.error(request, "토큰 발급에 실패했습니다.")
            return redirect("login")


        user_info = NaverLoginService.get_user_info(access_token)
        if not user_info:
            messages.error(request, "사용자 정보 요청에 실패했습니다.")
            return redirect("login")

        user, error = NaverLoginService.create_or_get_user(user_info)
        if error:
            logging.error(f"Naver login failed: {error}")
            messages.error(request, f"{error}")
            return redirect("login")

        login(request, user)

        next_url = request.session.pop("login_next", "/")
        if not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()
            ):
            next_url = '/'
        return redirect(next_url)

class AppleLoginView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        # Redis에 state 저장 (TTL 10분)
        state = OAuthStateService.create_state()
        login_url = AppleLoginService.get_login_url(state)
        return redirect(login_url)

@method_decorator(csrf_exempt, name="dispatch")
class AppleCallbackView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return redirect("/")

    def post(self, request: HttpRequest) -> HttpResponse:
        code = request.POST.get("code")
        state = request.POST.get("state")

        if not code:
            return JsonResponse({"error": "code 누락"}, status=400)
        if not state or not OAuthStateService.validate_state(state):
            return JsonResponse({"error": "state 불일치"}, status=400)

        token_payload = AppleLoginService.exchange_token(code)
        if not token_payload or "id_token" not in token_payload:
            return JsonResponse({"error": "Apple 토큰 교환 실패"}, status=400)

        id_token = token_payload["id_token"]
        user, error = AppleLoginService.authenticate_user(id_token=id_token)
        if error or not user:
            return JsonResponse({"error": error or "사용자 인증 실패"}, status=400)

        login(request, user)

        next_url = request.session.pop("login_next", "/")
        if not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
            next_url = '/'
        return redirect(next_url)