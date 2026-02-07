import json
from typing import TYPE_CHECKING, Any, Dict, Generator, cast
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse

from users.models import SocialUser
from users.services.oauth_state import OAuthStateService
from users.services.social_login import (
    AppleLoginService,
    GoogleLoginService,
    KakaoLoginService,
    NaverLoginService,
    SocialLoginService,
)

if TYPE_CHECKING:
    from users.models import User

User = get_user_model()  # type: ignore

@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def google_login_url() -> str:
    return reverse('google-login')


@pytest.fixture
def test_user() -> 'User':
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        personal_info_consent=True,
        terms_of_use=True
    )

@pytest.mark.django_db
class TestSocialLoginService:
    def test_creates_user_and_social_account(self) -> None:
        """처음 로그인 시 User + SocialUser 모두 생성된다."""
        user, created = SocialLoginService.get_or_create_user(
            provider="google",
            social_id="12345",
            email="user@example.com",
            extra_info={"first_name": "홍길동"},
        )

        assert created
        assert User.objects.count() == 1
        assert SocialUser.objects.count() == 1

        social = SocialUser.objects.first()
        assert social is not None
        assert social.provider == "google"
        assert social.user == user

    def test_reuses_existing_social_user(self) -> None:
        """같은 provider + social_id면 같은 User를 재사용한다."""
        user1, _ = SocialLoginService.get_or_create_user("google", "99999", "test@example.com")
        user2, _ = SocialLoginService.get_or_create_user("google", "99999", "test@example.com")
        assert user1 == user2
        assert User.objects.count() == 1
        assert SocialUser.objects.count() == 1

    def test_links_existing_email_user(self) -> None:
        """이메일로 이미 존재하는 User가 있으면 소셜 계정만 연결된다."""
        existing = User.objects.create_user(
            username="test",
            email="exist@example.com",
            password=None,
            personal_info_consent=False,
            terms_of_use=False,
        )

        user, created = SocialLoginService.get_or_create_user(
            provider="kakao",
            social_id="abcde",
            email="exist@example.com",
        )

        assert created  # 새 소셜 계정이 만들어짐
        assert user == existing
        assert SocialUser.objects.filter(user=existing, provider="kakao").exists()

    def test_unique_constraint_prevents_duplicates(self) -> None:
        """provider + social_id 중복 생성 시 에러 발생"""
        SocialLoginService.get_or_create_user("naver", "abc123", "user@naver.com")
        with pytest.raises(IntegrityError):
            # 같은 provider/social_id 중복 삽입 방지 확인
            SocialUser.objects.create(
                provider="naver",
                social_id="abc123",
                user=cast(User, User.objects.first()),
            )

@pytest.mark.django_db
class TestPlatformServicesIntegration:
    """플랫폼별 서비스가 SocialLoginService를 올바르게 호출하는지 확인"""

    @patch("users.services.social_login.SocialLoginService.get_or_create_user")
    def test_google_service_delegates_to_common_logic(self, mock_get_or_create: MagicMock) -> None:
        mock_get_or_create.return_value = (MagicMock(), True)
        info = {
            "sub": "g123",
            "email": "user@gmail.com",
            "name": "홍길동",
            "picture": "https://example.com/pic.jpg",
        }

        GoogleLoginService.get_or_create_user(info)

        mock_get_or_create.assert_called_once_with(
            "google",
            "g123",
            "user@gmail.com",
            {"first_name": "홍길동", "profile_image": "https://example.com/pic.jpg"},
        )

    @patch("users.services.social_login.SocialLoginService.get_or_create_user")
    def test_kakao_service_delegates_to_common_logic(self, mock_get_or_create: MagicMock) -> None:
        mock_get_or_create.return_value = (MagicMock(), True)
        info = {
            "id": 12345,
            "kakao_account": {
                "email": "test@kakao.com",
                "profile": {
                    "nickname": "카카오사용자",
                    "profile_image_url": "https://example.com/image.jpg",
                },
            },
        }

        KakaoLoginService.get_or_create_user(info)

        mock_get_or_create.assert_called_once_with(
            "kakao",
            "12345",
            "test@kakao.com",
            {"first_name": "카카오사용자", "profile_image": "https://example.com/image.jpg"},
        )

    @patch("users.services.social_login.SocialLoginService.get_or_create_user")
    def test_naver_service_delegates_to_common_logic(self, mock_get_or_create: MagicMock) -> None:
        mock_get_or_create.return_value = (MagicMock(), True)
        info = {"id": "n1", "email": "user@naver.com", "name": "홍길동"}

        NaverLoginService.create_or_get_user(info)

        mock_get_or_create.assert_called_once_with("naver", "n1", "user@naver.com", {"first_name": "홍길동"})

    @patch("users.services.social_login.SocialLoginService.get_or_create_user")
    def test_apple_service_delegates_to_common_logic(self, mock_get_or_create: MagicMock) -> None:
        mock_get_or_create.return_value = (MagicMock(), True)
        info = {"apple_id": "a123", "email": "apple@icloud.com"}

        AppleLoginService.create_or_get_user(info)

        mock_get_or_create.assert_called_once_with(
            provider="apple",
            social_id="a123",
            email="apple@icloud.com",
        )

class TestGoogleLoginView:
    
    def test_google_login_missing_credential(self, client: Client, google_login_url: str) -> None:
        response = client.post(
            google_login_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert not data['success']
        assert data['message'] == 'Google 인증 정보가 없습니다.'
    
    def test_google_login_invalid_json(self, client: Client, google_login_url: str) -> None:
        response = client.post(
            google_login_url,
            data="invalid json",
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert not data['success']
        assert data['message'] == '잘못된 JSON 형식입니다.'
    

    @pytest.mark.django_db
    @patch('users.services.social_login.GoogleLoginService.authenticate_user')
    def test_google_login_authentication_failure(self, mock_authenticate: Any, client: Client, google_login_url: str) -> None:
        mock_authenticate.return_value = (None, "토큰 검증 실패")
        
        response = client.post(
            google_login_url,
            data=json.dumps({'credential': 'fake_credential'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert not data['success']
        assert data['message'] == '토큰 검증 실패'
    

    @pytest.mark.django_db
    @patch('users.services.social_login.GoogleLoginService.authenticate_user')
    def test_google_login_success(self, mock_authenticate: Any, client: Client, google_login_url: str, test_user: 'User') -> None:
        mock_authenticate.return_value = (test_user, None)
        
        response = client.post(
            google_login_url,
            data=json.dumps({'credential': 'valid_credential'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success']
        assert data['message'] == 'Google 로그인에 성공했습니다. 홈페이지로 이동합니다.'
        assert data['redirect_url'] == '/'
        assert data['user']['id'] == test_user.id
        assert data['user']['username'] == test_user.username
    

    @pytest.mark.django_db
    @patch('users.services.social_login.GoogleLoginService.authenticate_user')
    def test_google_login_with_next_parameter(self, mock_authenticate: Any, client: Client, google_login_url: str, test_user: 'User') -> None:
        mock_authenticate.return_value = (test_user, None)
        
        response = client.post(
            f"{google_login_url}?next=/profile/",
            data=json.dumps({'credential': 'valid_credential'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success']
        assert data['redirect_url'] == '/profile/'
    

    @pytest.mark.django_db
    @patch('users.services.social_login.GoogleLoginService.authenticate_user')
    def test_google_login_with_unsafe_next_parameter(self, mock_authenticate: Any, client: Client, google_login_url: str, test_user: 'User') -> None:
        mock_authenticate.return_value = (test_user, None)
        
        response = client.post(
            f"{google_login_url}?next=https://evil.com/",
            data=json.dumps({'credential': 'valid_credential'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success']
        assert data['redirect_url'] == '/'
    
    @pytest.mark.django_db
    @patch('users.services.social_login.GoogleLoginService.authenticate_user')
    def test_google_login_user_authentication_failure(self, mock_authenticate: Any, client: Client, google_login_url: str) -> None:
        """Google 로그인 - 사용자 인증 실패 (user가 None인 경우)"""
        mock_authenticate.return_value = (None, None)  # user가 None인 경우
        
        response = client.post(
            google_login_url,
            data=json.dumps({'credential': 'valid_credential'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert not data['success']
        assert data['message'] == '사용자 인증에 실패했습니다.'
    
    @pytest.mark.django_db
    @patch('users.services.social_login.GoogleLoginService.authenticate_user')
    def test_google_login_server_error(self, mock_authenticate: Any, client: Client, google_login_url: str) -> None:
        """Google 로그인 - 서버 오류"""
        mock_authenticate.side_effect = Exception("서버 내부 오류")
        
        response = client.post(
            google_login_url,
            data=json.dumps({'credential': 'valid_credential'}),
            content_type='application/json'
        )
        
        assert response.status_code == 500
        data = response.json()
        assert not data['success']
        assert '서버 오류가 발생했습니다' in data['message']


class TestGoogleSocialLoginService:
    
    @pytest.mark.django_db
    def test_google_generate_unique_username(self) -> None:
        # 기존 사용자가 없는 경우
        username = GoogleLoginService._generate_unique_username('test@example.com')
        assert username == 'test'
        
        # 기존 사용자가 있는 경우
        User.objects.create_user(
            username='test', 
            email='existing@example.com',
            personal_info_consent=True,
            terms_of_use=True
        )
        username = GoogleLoginService._generate_unique_username('test@example.com')
        assert username == 'test_1'
        
        # 여러 기존 사용자가 있는 경우
        User.objects.create_user(
            username='test_1', 
            email='existing2@example.com',
            personal_info_consent=True,
            terms_of_use=True
        )
        username = GoogleLoginService._generate_unique_username('test@example.com')
        assert username == 'test_2'
    
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_verify_token_success(self, mock_verify: Any) -> None:
        mock_verify.return_value = {
            'iss': 'accounts.google.com',
            'sub': '12345',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/picture.jpg'
        }
        
        result = GoogleLoginService.verify_google_token('valid_token')
        
        assert result is not None
        assert result['sub'] == '12345'
        assert result['email'] == 'test@example.com'
    
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_verify_token_wrong_issuer(self, mock_verify: Any) -> None:
        mock_verify.return_value = {
            'iss': 'evil.com',
            'sub': '12345',
            'email': 'test@example.com'
        }
        
        result = GoogleLoginService.verify_google_token('invalid_token')
        
        assert result is None
    
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_verify_token_value_error(self, mock_verify: Any) -> None:
        mock_verify.side_effect = ValueError("Invalid token")
        
        result = GoogleLoginService.verify_google_token('invalid_token')
        
        assert result is None
    
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_verify_token_general_exception(self, mock_verify: Any) -> None:
        mock_verify.side_effect = Exception("Network error")
        
        result = GoogleLoginService.verify_google_token('invalid_token')
        
        assert result is None

    @patch("users.services.social_login.SocialLoginService.get_or_create_user")
    def test_google_login_calls_common_service(self, mock_get_or_create: MagicMock) -> None:
        mock_get_or_create.return_value = (MagicMock(), True)
        user_info = {
            "sub": "g123",
            "email": "user@gmail.com",
            "name": "홍길동",
            "picture": "https://example.com/pic.jpg",
        }

        GoogleLoginService.get_or_create_user(user_info)

        mock_get_or_create.assert_called_once_with(
            "google",
            "g123",
            "user@gmail.com",
            {"first_name": "홍길동", "profile_image": "https://example.com/pic.jpg"},
        )
    
    @pytest.mark.django_db
    def test_google_get_or_create_user_existing_by_google_id(self) -> None:
        # 기존 사용자 생성
        existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123',
            personal_info_consent=True,
            terms_of_use=True
        )
        
        google_user_info = {
            'sub': '12345',
            'email': 'existing@example.com',
            'name': 'Existing User'
        }
        
        user, _ = GoogleLoginService.get_or_create_user(google_user_info)
        
        assert user is not None
        assert user.id == existing_user.id
    
    @pytest.mark.django_db
    def test_google_get_or_create_user_existing_by_email(self) -> None:
        # 기존 사용자 생성 (Google ID 없음)
        existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123',
            personal_info_consent=True,
            terms_of_use=True
        )
        
        google_user_info = {
            'sub': '12345',
            'email': 'existing@example.com',
            'name': 'Existing User'
        }
        
        user, _ = GoogleLoginService.get_or_create_user(google_user_info)
        
        assert user is not None
        assert user.id == existing_user.id
    
    @pytest.mark.django_db
    def test_google_get_or_create_user_missing_data(self) -> None:
        google_user_info = {
            'sub': '12345',
            'email': '',
            'name': 'Test User'
        }

        user, _ = GoogleLoginService.get_or_create_user(google_user_info)
        assert user is not None
        assert user.email.startswith("google_")
    
    @pytest.mark.django_db
    def test_google_authenticate_user_success(self) -> None:
        google_user_info = {
            'sub': '12345',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/picture.jpg'
        }
        
        with patch.object(GoogleLoginService, 'verify_google_token', return_value=google_user_info):
            user, error = GoogleLoginService.authenticate_user('valid_token')
            
            assert user is not None
            assert error is None
            assert user.email == 'test@example.com'
    
    @pytest.mark.django_db
    def test_google_authenticate_user_token_verification_failed(self) -> None:
        with patch.object(GoogleLoginService, 'verify_google_token', return_value=None):
            user, error = GoogleLoginService.authenticate_user('invalid_token')
            
            assert user is None
            assert error == "Google 토큰 검증에 실패했습니다."
    
    @pytest.mark.django_db
    def test_google_authenticate_user_creation_failed(self) -> None:
        google_user_info = {
            "sub": "12345",
            "email": "test@example.com",
            "name": "Test User",
        }

        with patch(
                "users.services.social_login.GoogleLoginService.verify_google_token",
                return_value=google_user_info,
        ), patch(
            "users.services.social_login.GoogleLoginService.get_or_create_user",
            return_value=(None, "DB 오류"),
        ):
            user, error = GoogleLoginService.authenticate_user("valid_token")

            assert user is None
            assert error == "사용자 생성/조회에 실패했습니다."
    
    @pytest.mark.django_db
    def test_google_authenticate_user_exception(self) -> None:
        with patch.object(GoogleLoginService, 'verify_google_token', side_effect=Exception("Database error")):
            user, error = GoogleLoginService.authenticate_user('valid_token')
            
            assert user is None
            assert error == "Google 토큰 검증 중 오류가 발생했습니다."
    
    @pytest.mark.django_db
    def test_kakao_generate_unique_username(self) -> None:
        # 기존 사용자가 없는 경우
        username = KakaoLoginService._generate_unique_username('카카오사용자')
        assert username == '카카오사용자'
        
        # 기존 사용자가 있는 경우
        User.objects.create_user(
            username='카카오사용자', 
            email='existing@example.com',
            personal_info_consent=True,
            terms_of_use=True
        )
        username = KakaoLoginService._generate_unique_username('카카오사용자')
        assert username == '카카오사용자_1'
    
    @pytest.mark.django_db
    @patch('requests.get')
    def test_kakao_get_user_info_success(self, mock_get: Any) -> None:
        from unittest.mock import Mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 12345,
            'kakao_account': {
                'email': 'test@kakao.com',
                'profile': {
                    'nickname': '카카오사용자',
                    'profile_image_url': 'https://example.com/image.jpg'
                }
            }
        }
        mock_get.return_value = mock_response
        
        result = KakaoLoginService.get_kakao_user_info('valid_token')
        
        assert result is not None
        assert result['id'] == 12345
        assert result['kakao_account']['email'] == 'test@kakao.com'
    
    @pytest.mark.django_db
    @patch('requests.get')
    def test_kakao_get_user_info_failure(self, mock_get: Any) -> None:
        from unittest.mock import Mock
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_get.return_value = mock_response
        
        result = KakaoLoginService.get_kakao_user_info('invalid_token')
        
        assert result is None
    
    @pytest.mark.django_db
    def test_kakao_get_or_create_user_new_user(self) -> None:
        kakao_user_info = {
            'id': 12345,
            'kakao_account': {
                'email': 'newuser@kakao.com',
                'profile': {
                    'nickname': '카카오사용자',
                    'profile_image_url': 'https://example.com/picture.jpg'
                }
            }
        }

        user, error = KakaoLoginService.get_or_create_user(kakao_user_info)

        assert error is None
        assert user is not None
        assert user.email == 'newuser@kakao.com'
        assert user.first_name == '카카오사용자'
        assert user.profile_image == 'https://example.com/picture.jpg'
        assert user.personal_info_consent is False
        assert user.terms_of_use is False
    
    @pytest.mark.django_db
    def test_kakao_authenticate_user_success(self) -> None:
        kakao_user_info = {
            'id': 12345,
            'kakao_account': {
                'email': 'test@kakao.com',
                'profile': {
                    'nickname': '카카오사용자',
                    'profile_image_url': 'https://example.com/picture.jpg'
                }
            }
        }
        
        with patch.object(KakaoLoginService, 'get_kakao_user_info', return_value=kakao_user_info):
            user, error = KakaoLoginService.authenticate_user('valid_token')
            
            assert user is not None
            assert error is None
            assert user.email == 'test@kakao.com'

@pytest.mark.django_db
class TestNaverLoginService:
    @patch("users.services.social_login.requests.get")
    def test_get_access_token_success(self, mock_get: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mock_token"}
        mock_get.return_value = mock_response

        token = NaverLoginService.get_access_token("code123", "state456")
        assert token == "mock_token"

    @patch("users.services.social_login.requests.get")
    def test_get_access_token_failure(self, mock_get: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        token = NaverLoginService.get_access_token("code123", "state456")
        assert token is None

    @patch("users.services.social_login.requests.get")
    def test_get_user_info_success(self, mock_get: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resultcode": "00",
            "response": {"id": "12345", "email": "test@naver.com"}
        }
        mock_get.return_value = mock_response

        user_info = NaverLoginService.get_user_info("access_token_abc")
        assert user_info is not None
        assert user_info["email"] == "test@naver.com"

    @patch("users.services.social_login.requests.get")
    def test_get_user_info_failure_status_code(self, mock_get: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        user_info = NaverLoginService.get_user_info("invalid_token")
        assert user_info is None

    @pytest.mark.django_db
    def test_create_or_get_user_new(self) -> None:
        user_info: Dict[str, Any] = {
            "id": "1",
            "email": "new@naver.com",
            "name": "홍길동",
        }
        user, error = NaverLoginService.create_or_get_user(user_info)
        assert error is None
        assert user is not None
        assert user.email == "new@naver.com"
        assert user.username == "new"

    @pytest.mark.django_db
    def test_create_or_get_user_existing(self) -> None:
        existing = User.objects.create_user(
            username="naver_100",
            email="old@naver.com",
            personal_info_consent=True,
            terms_of_use=True,
        )
        SocialUser.objects.create(
            user=existing,
            provider="naver",
            social_id="100",
            email="old@naver.com",
        )

        user_info = {"id": "100", "email": "new@naver.com"}
        user, error = NaverLoginService.create_or_get_user(user_info)
        assert user is not None
        assert error is None
        assert user.id == existing.id
        assert user.email == "old@naver.com"

    @pytest.mark.django_db
    def test_create_or_get_user_missing_id(self) -> None:
        user_info = {"email": "missing@naver.com"}
        user, error = NaverLoginService.create_or_get_user(user_info)
        assert user is None
        assert error == "네이버 사용자 ID가 없습니다."

@pytest.mark.django_db
class TestNaverLoginView:

    def test_get_login_redirects_with_state(self, client: Client) -> None:
        response = client.get(reverse("naver-login"))
        assert response.status_code == 302
        assert "nid.naver.com/oauth2.0/authorize" in (getattr(response, "url", "") or "")
        assert "naver_state" in client.session

    @patch("users.views.social_login.NaverLoginService.create_or_get_user")
    @patch("users.views.social_login.NaverLoginService.get_user_info")
    @patch("users.views.social_login.NaverLoginService.get_access_token")
    def test_callback_success(
            self,
            mock_get_token: MagicMock,
            mock_get_info: MagicMock,
            mock_create_user: MagicMock,
            client: Client,
    ) -> None:

        session = client.session
        session["naver_state"] = "mock_state"
        session.save()
        client.cookies["sessionid"] = cast(str, session.session_key)

        mock_get_token.return_value = "mock_access_token"
        mock_get_info.return_value = {"id": "abc123", "email": "user@naver.com", "name": "테스트유저"}

        fake_user = User.objects.create_user(
            username="user",
            email="user@naver.com",
            password="test1234",
            personal_info_consent=False,
            terms_of_use=False,
        )
        mock_create_user.return_value = (fake_user, None)

        response = client.get(reverse("naver-callback"), {"code": "mock_code", "state": "mock_state"})

        assert response.status_code == 302
        assert (getattr(response, "url", "") or "") == reverse("home")

    def test_callback_invalid_state_redirects_login(self, client: Client) -> None:
        """state 불일치 시 로그인으로 리다이렉트"""
        client.session["naver_state"] = "real_state"
        client.session.save()

        response = client.get(reverse("naver-callback"), {"code": "abc", "state": "fake"})
        assert response.status_code == 302
        assert (getattr(response, "url", "") or "") == reverse("login")

    @patch("users.services.social_login.requests.get")
    def test_callback_token_failure(self, mock_get: MagicMock, client: Client) -> None:
        """토큰 발급 실패 시 로그인 리다이렉트"""
        client.session["naver_state"] = "mock_state"
        client.session.save()

        mock_res = MagicMock()
        mock_res.status_code = 401
        mock_get.return_value = mock_res

        response = client.get(reverse("naver-callback"), {"code": "mock_code", "state": "mock_state"})
        assert response.status_code == 302
        assert (getattr(response, "url", "") or "") == reverse("login")

    @patch("users.services.social_login.requests.get")
    def test_callback_userinfo_failure(self, mock_get: MagicMock, client: Client) -> None:
        """유저 정보 요청 실패 시 로그인 리다이렉트"""
        client.session["naver_state"] = "mock_state"
        client.session.save()

        token_res = MagicMock()
        token_res.status_code = 200
        token_res.json.return_value = {"access_token": "mock_token"}

        profile_res = MagicMock()
        profile_res.status_code = 500

        mock_get.side_effect = [token_res, profile_res]

        response = client.get(reverse("naver-callback"), {"code": "mock_code", "state": "mock_state"})
        assert response.status_code == 302
        assert (getattr(response, "url", "") or "") == reverse("login")

@pytest.fixture
def client_with_session(client: Client) -> Generator[Client, None, None]:
    session = client.session
    session["apple_state"] = "valid_state"
    session.save()
    yield client

@pytest.mark.django_db
class TestAppleLoginView:
    """애플 로그인 뷰 테스트"""

    def test_missing_code_returns_400(self, client_with_session: Client) -> None:
        state = OAuthStateService.create_state()
        url = reverse("apple-callback")
        res = client_with_session.post(url, {"state": state})
        assert res.status_code == 400
        assert "code 누락" in res.json()["error"]

    def test_state_mismatch_returns_400(self, client_with_session: Client) -> None:
        # 존재하지 않는 state 사용
        url = reverse("apple-callback")
        res = client_with_session.post(url, {"code": "abc123", "state": "invalid"})
        assert res.status_code == 400
        assert "state 불일치" in res.json()["error"]

    @patch("users.services.social_login.AppleLoginService.exchange_token", autospec=True)
    def test_token_exchange_failure_returns_400(
            self,
            mock_exchange: MagicMock,
            client_with_session: Client
    ) -> None:
        """Apple 토큰 교환 실패 시 400"""
        state = OAuthStateService.create_state()
        mock_exchange.return_value = None

        url = reverse("apple-callback")
        res = client_with_session.post(url, {"code": "abc123", "state": state})

        assert res.status_code == 400
        assert "Apple 토큰 교환 실패" in res.json()["error"]

    @patch("users.services.social_login.AppleLoginService.authenticate_user", autospec=True)
    @patch("users.services.social_login.AppleLoginService.exchange_token", autospec=True)
    def test_authentication_failure_returns_400(
            self,
            mock_exchange: MagicMock,
            mock_auth: MagicMock,
            client_with_session: Client
    ) -> None:
        """id_token 파싱 실패 시 400"""
        state = OAuthStateService.create_state()
        mock_exchange.return_value = {"id_token": "fake_token"}
        mock_auth.return_value = (None, "id_token 파싱 실패")

        url = reverse("apple-callback")
        res = client_with_session.post(url, {"code": "abc123", "state": state})

        assert res.status_code == 400
        assert "id_token 파싱 실패" in res.json()["error"]

    @patch("users.services.social_login.AppleLoginService.authenticate_user", autospec=True)
    @patch("users.services.social_login.AppleLoginService.exchange_token", autospec=True)
    def test_successful_login_redirects_to_home(
            self,
            mock_exchange: MagicMock,
            mock_auth: MagicMock,
            client_with_session: Client
    ) -> None:
        """정상 로그인 시 홈페이지로 리다이렉트"""
        state = OAuthStateService.create_state()

        user = User.objects.create_user(
            username="appleuser",
            email="apple@example.com",
            password="test1234",
            personal_info_consent=True,
            terms_of_use=True,
        )
        mock_exchange.return_value = {"id_token": "valid_token"}
        mock_auth.return_value = (user, None)

        url = reverse("apple-callback")
        res = client_with_session.post(url, {"code": "abc123", "state": state})

        assert res.status_code == 302
        assert res["Location"] == "/"


@pytest.mark.django_db
class TestSocialLoginServiceLowCoverageBranches:
    def test_social_login_service_missing_social_id(self) -> None:
        user, error = SocialLoginService.get_or_create_user(
            provider="google",
            social_id="",
            email="test@example.com",
        )
        assert user is None
        assert error == "소셜 ID 누락"

    def test_social_login_service_integrity_error(self, monkeypatch: Any) -> None:
        def mock_create(*args: Any, **kwargs: Any) -> None:
            raise IntegrityError("duplicate")

        monkeypatch.setattr(
            SocialUser.objects, "create", mock_create, raising=False
        )

        user, error = SocialLoginService.get_or_create_user(
            provider="google",
            social_id="g123",
            email="test@example.com",
        )
        assert user is None
        assert error == "이미 연결된 소셜 계정입니다."

    def test_social_login_service_generic_exception(self, monkeypatch: Any) -> None:
        def mock_get_or_create(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("db connection failed")

        monkeypatch.setattr(
            User.objects, "get_or_create", mock_get_or_create, raising=False
        )
        user, error = SocialLoginService.get_or_create_user(
            provider="google",
            social_id="g999",
            email="new@example.com",
        )
        assert user is None
        assert "DB 오류" in str(error)


@pytest.mark.django_db
class TestGoogleLoginServiceUncoveredBranches:
    def test_google_get_or_create_user_missing_sub_and_id(self) -> None:
        user, error = GoogleLoginService.get_or_create_user({"email": "x@y.com"})
        assert user is None
        assert error == "Google 사용자 ID(sub)가 누락되었습니다."

    def test_google_get_or_create_user_social_service_returns_error(self) -> None:
        with patch(
            "users.services.social_login.SocialLoginService.get_or_create_user",
            return_value=(None, "이미 연결된 소셜 계정입니다."),
        ):
            user, error = GoogleLoginService.get_or_create_user(
                {"sub": "g123", "email": "a@b.com", "name": "Test"}
            )
        assert user is None
        assert error == "이미 연결된 소셜 계정입니다."


@pytest.mark.django_db
class TestKakaoLoginServiceUncoveredBranches:
    @patch("users.services.social_login.requests.get")
    def test_get_kakao_user_info_non_dict_response(
        self, mock_get: MagicMock
    ) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = ["not", "a", "dict"]
        mock_get.return_value = mock_res
        result = KakaoLoginService.get_kakao_user_info("token")
        assert result is None

    @patch("users.services.social_login.requests.get")
    def test_get_kakao_user_info_non_200(self, mock_get: MagicMock) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 401
        mock_res.text = "Unauthorized"
        mock_get.return_value = mock_res
        result = KakaoLoginService.get_kakao_user_info("token")
        assert result is None

    @patch("users.services.social_login.requests.get")
    def test_get_kakao_user_info_exception(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = Exception("network error")
        result = KakaoLoginService.get_kakao_user_info("token")
        assert result is None

    def test_kakao_get_or_create_user_social_returns_error(self) -> None:
        with patch(
            "users.services.social_login.SocialLoginService.get_or_create_user",
            return_value=(None, "DB 오류"),
        ):
            user, error = KakaoLoginService.get_or_create_user(
                {"id": "k1", "kakao_account": {"email": "k@k.com", "profile": {}}}
            )
        assert user is None
        assert error == "DB 오류"

    @patch.object(KakaoLoginService, "get_kakao_user_info", return_value=None)
    def test_kakao_authenticate_user_info_fail(
        self, mock_info: MagicMock
    ) -> None:
        user, error = KakaoLoginService.authenticate_user("token")
        assert user is None
        assert error == "카카오 사용자 정보 조회에 실패했습니다."

    @patch.object(KakaoLoginService, "get_or_create_user", return_value=(None, "err"))
    @patch.object(KakaoLoginService, "get_kakao_user_info")
    def test_kakao_authenticate_user_creation_fail(
        self, mock_info: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_info.return_value = {"id": "k1", "kakao_account": {}}
        user, error = KakaoLoginService.authenticate_user("token")
        assert user is None
        assert error == "err"

    @patch.object(KakaoLoginService, "get_or_create_user", return_value=(None, None))
    @patch.object(KakaoLoginService, "get_kakao_user_info")
    def test_kakao_authenticate_user_none_without_error(
        self, mock_info: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_info.return_value = {"id": "k1", "kakao_account": {}}
        user, error = KakaoLoginService.authenticate_user("token")
        assert user is None
        assert error == "사용자 생성/조회에 실패했습니다."

    @patch.object(KakaoLoginService, "get_kakao_user_info", side_effect=Exception("x"))
    def test_kakao_authenticate_user_exception(
        self, mock_info: MagicMock
    ) -> None:
        user, error = KakaoLoginService.authenticate_user("token")
        assert user is None
        assert error == "x"


class TestNaverLoginServiceUncoveredBranches:
    @patch("users.services.social_login.requests.get")
    def test_naver_get_access_token_non_200(self, mock_get: MagicMock) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 400
        mock_get.return_value = mock_res
        result = NaverLoginService.get_access_token("code", "state")
        assert result is None

    @patch("users.services.social_login.requests.get")
    def test_naver_get_access_token_json_decode_error(
        self, mock_get: MagicMock
    ) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.side_effect = json.JSONDecodeError("x", "y", 0)
        mock_get.return_value = mock_res
        result = NaverLoginService.get_access_token("code", "state")
        assert result is None

    @patch("users.services.social_login.requests.get")
    def test_naver_get_access_token_response_not_dict(
        self, mock_get: MagicMock
    ) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = []
        mock_get.return_value = mock_res
        result = NaverLoginService.get_access_token("code", "state")
        assert result is None

    @patch("users.services.social_login.requests.get")
    def test_naver_get_access_token_no_access_token(
        self, mock_get: MagicMock
    ) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"other": "value"}
        mock_get.return_value = mock_res
        result = NaverLoginService.get_access_token("code", "state")
        assert result is None

    @patch("users.services.social_login.requests.get")
    def test_naver_get_user_info_non_200(self, mock_get: MagicMock) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 401
        mock_get.return_value = mock_res
        result = NaverLoginService.get_user_info("token")
        assert result is None

    @patch("users.services.social_login.requests.get")
    def test_naver_get_user_info_result_code_not_00(
        self, mock_get: MagicMock
    ) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"resultcode": "01", "message": "err"}
        mock_get.return_value = mock_res
        result = NaverLoginService.get_user_info("token")
        assert result is None


@pytest.mark.django_db
class TestNaverCreateOrGetUserUncoveredBranches:
    def test_naver_create_or_get_user_empty_info(self) -> None:
        user, error = NaverLoginService.create_or_get_user({})
        assert user is None
        assert error == "네이버 사용자 정보가 비어있습니다."

    def test_naver_create_or_get_user_missing_naver_id(self) -> None:
        user, error = NaverLoginService.create_or_get_user(
            {"email": "n@n.com", "name": "X"}
        )
        assert user is None
        assert error == "네이버 사용자 ID가 없습니다."

    def test_naver_create_or_get_user_missing_email(self) -> None:
        user, error = NaverLoginService.create_or_get_user(
            {"id": "n1", "name": "X"}
        )
        assert user is None
        assert error == "네이버 이메일 정보가 없습니다."


class TestAppleLoginServiceUncoveredBranches:
    @patch("users.services.social_login.os.getenv")
    def test_apple_build_client_secret_missing_env(
        self, mock_getenv: MagicMock
    ) -> None:
        mock_getenv.return_value = ""
        with pytest.raises(ValueError, match="Apple OAuth 환경변수가 누락"):
            AppleLoginService._build_client_secret()

    @patch("users.services.social_login.os.getenv")
    def test_apple_get_login_url_missing_env(
        self, mock_getenv: MagicMock
    ) -> None:
        mock_getenv.return_value = ""
        with pytest.raises(ValueError, match="APPLE_CLIENT_ID"):
            AppleLoginService.get_login_url("state")

    @patch("users.services.social_login.requests.post")
    def test_apple_exchange_token_request_exception(
        self, mock_post: MagicMock
    ) -> None:
        mock_post.side_effect = Exception("timeout")
        with patch.object(
            AppleLoginService, "_build_client_secret", return_value="secret"
        ):
            result = AppleLoginService.exchange_token("code")
        assert result is None

    @patch("users.services.social_login.requests.post")
    def test_apple_exchange_token_non_200(self, mock_post: MagicMock) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 400
        mock_post.return_value = mock_res
        with patch.object(
            AppleLoginService, "_build_client_secret", return_value="secret"
        ):
            result = AppleLoginService.exchange_token("code")
        assert result is None

    @patch("users.services.social_login.requests.post")
    def test_apple_exchange_token_json_value_error(
        self, mock_post: MagicMock
    ) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.side_effect = ValueError("invalid json")
        mock_post.return_value = mock_res
        with patch.object(
            AppleLoginService, "_build_client_secret", return_value="secret"
        ):
            result = AppleLoginService.exchange_token("code")
        assert result is None

    @patch("users.services.social_login.requests.post")
    def test_apple_exchange_token_response_not_dict_or_has_error(
        self, mock_post: MagicMock
    ) -> None:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"error": "invalid_grant"}
        mock_post.return_value = mock_res
        with patch.object(
            AppleLoginService, "_build_client_secret", return_value="secret"
        ):
            result = AppleLoginService.exchange_token("code")
        assert result is None

    def test_apple_parse_id_token_exception(self) -> None:
        result = AppleLoginService.parse_id_token("invalid.jwt.token")
        assert result is None

    def test_apple_authenticate_user_id_token_parse_fails(self) -> None:
        with patch.object(
            AppleLoginService, "parse_id_token", return_value=None
        ):
            user, error = AppleLoginService.authenticate_user(id_token="x")
        assert user is None
        assert error == "id_token 검증에 실패했습니다."

    def test_apple_authenticate_user_code_none(self) -> None:
        user, error = AppleLoginService.authenticate_user(code=None)
        assert user is None
        assert error == "인가 코드(code)가 없습니다."

    def test_apple_authenticate_user_exchange_fails(self) -> None:
        with patch.object(
            AppleLoginService, "exchange_token", return_value=None
        ):
            user, error = AppleLoginService.authenticate_user(code="c")
        assert user is None
        assert error == "애플 토큰 교환에 실패했습니다."

    def test_apple_authenticate_user_id_token_not_string(self) -> None:
        with patch.object(
            AppleLoginService, "exchange_token",
            return_value={"id_token": 123},
        ):
            user, error = AppleLoginService.authenticate_user(code="c")
        assert user is None
        assert "id_token이 존재하지 않거나" in str(error)

    def test_apple_authenticate_user_sub_or_email_missing(self) -> None:
        with patch.object(
            AppleLoginService, "parse_id_token",
            return_value={"sub": "s1"},
        ):
            user, error = AppleLoginService.authenticate_user(id_token="x")
        assert user is None
        assert "sub/email" in str(error)

    def test_apple_authenticate_user_create_fails(self) -> None:
        with patch.object(
            AppleLoginService, "parse_id_token",
            return_value={"sub": "s1", "email": "e@e.com"},
        ), patch.object(
            AppleLoginService, "create_or_get_user",
            return_value=(None, "이미 연결된 계정"),
        ):
            user, error = AppleLoginService.authenticate_user(id_token="x")
        assert user is None
        assert error == "이미 연결된 계정"


class TestAppleLoginServiceAdditionalBranches:
    def test_apple_create_or_get_user_empty_info(self) -> None:
        user, error = AppleLoginService.create_or_get_user({})
        assert user is None
        assert error == "애플 사용자 정보가 비어있습니다."

    def test_apple_create_or_get_user_missing_apple_id(self) -> None:
        user, error = AppleLoginService.create_or_get_user({"email": "apple@example.com"})
        assert user is None
        assert error == "애플 사용자 ID(sub)가 없습니다."

    @pytest.mark.django_db
    def test_apple_create_or_get_user_social_returns_none(self) -> None:
        with patch(
            "users.services.social_login.SocialLoginService.get_or_create_user",
            return_value=(None, "DB 오류"),
        ):
            user, error = AppleLoginService.create_or_get_user(
                {"apple_id": "a1", "email": "a@a.com"}
            )
        assert user is None
        assert error == "DB 오류"


