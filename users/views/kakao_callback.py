import requests
from django.conf import settings
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from users.services.social_login import KakaoLoginService


@method_decorator(csrf_exempt, name='dispatch')
class KakaoCallbackView(View):
    """카카오 로그인 콜백 처리 뷰"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            # 인증 코드 받기
            code = request.GET.get('code')
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'message': '인증 코드가 없습니다.'
                }, status=400)
            
            # 인증 코드를 액세스 토큰으로 교환
            token_response = requests.post(
                'https://kauth.kakao.com/oauth/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': settings.KAKAO_REST_API_KEY,
                    'client_secret': settings.KAKAO_CLIENT_SECRET,
                    'redirect_uri': settings.KAKAO_REDIRECT_URI,
                    'code': code
                }
            )
            
            if token_response.status_code != 200:
                return JsonResponse({
                    'success': False,
                    'message': '액세스 토큰 획득에 실패했습니다.'
                }, status=400)
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                return JsonResponse({
                    'success': False,
                    'message': '액세스 토큰이 없습니다.'
                }, status=400)
            
            # 카카오 로그인 서비스로 인증 처리
            user, error = KakaoLoginService.authenticate_user(access_token)
            
            if error:
                return JsonResponse({
                    'success': False,
                    'message': error
                }, status=400)
            
            if user:
                # 사용자 로그인
                login(request, user)
                
                # 안전한 리다이렉트 URL 결정
                next_url = request.GET.get('next') or request.session.pop('login_next', '/')
                if not url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    next_url = '/'
                
                return redirect(next_url)
            else:
                return JsonResponse({
                    'success': False,
                    'message': '사용자 인증에 실패했습니다.'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'서버 오류가 발생했습니다: {str(e)}'
            }, status=500)
