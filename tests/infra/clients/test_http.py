"""
HTTP 클라이언트 테스트

이 모듈은 뉴스 알림 시스템에서 사용하는 HTTP 클라이언트의 테스트를 제공합니다.
aiohttp를 사용한 비동기 HTTP 요청과 응답 처리에 대한 테스트 케이스를 포함합니다.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientResponse, ClientSession, ClientTimeout
from aiohttp.client_exceptions import (
    ClientConnectorError,
    ClientError,
    ServerTimeoutError,
)

# Add project root to path to support imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infra.clients.http import AioHttpClient, HttpClient


class TestHttpClient:
    """HTTP 클라이언트 테스트 클래스"""

    @pytest.fixture
    def mock_response(self):
        """HTTP 응답을 모킹하는 픽스처"""
        mock_resp = AsyncMock(spec=ClientResponse)
        mock_resp.status = 200
        mock_resp.reason = "OK"
        mock_resp.json = AsyncMock(return_value={"data": "test"})
        mock_resp.text = AsyncMock(return_value="response text")
        mock_resp.read = AsyncMock(return_value=b"binary data")
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.__aenter__.return_value = mock_resp
        mock_resp.__aexit__.return_value = None
        return mock_resp

    @pytest.fixture
    def mock_session(self, mock_response):
        """ClientSession을 모킹하는 픽스처"""
        mock_session = MagicMock(spec=ClientSession)
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.put = AsyncMock(return_value=mock_response)
        mock_session.delete = AsyncMock(return_value=mock_response)
        mock_session.patch = AsyncMock(return_value=mock_response)
        mock_session.head = AsyncMock(return_value=mock_response)
        mock_session.options = AsyncMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        return mock_session

    @pytest.fixture
    def default_headers(self):
        """기본 테스트용 HTTP 헤더"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }

    @pytest.mark.asyncio
    async def test_get_request(self, mock_session, default_headers):
        """HTTP GET 요청 테스트"""
        url = "https://api.example.com/data"

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with aiohttp.ClientSession() as session:
                # 요청 실행
                response = await session.get(url, headers=default_headers)

                # 호출 검증
                mock_session.get.assert_called_once_with(url, headers=default_headers)

                # 응답 검증
                assert response.status == 200
                data = await response.json()
                assert data == {"data": "test"}

    @pytest.mark.asyncio
    async def test_post_request_with_json(self, mock_session, default_headers):
        """JSON 데이터로 HTTP POST 요청 테스트"""
        url = "https://api.example.com/create"
        json_data = {"name": "Test", "value": 123}

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with aiohttp.ClientSession() as session:
                # 요청 실행
                response = await session.post(
                    url, headers=default_headers, json=json_data
                )

                # 호출 검증
                mock_session.post.assert_called_once_with(
                    url, headers=default_headers, json=json_data
                )

                # 응답 검증
                assert response.status == 200
                data = await response.json()
                assert data == {"data": "test"}

    @pytest.mark.asyncio
    async def test_post_request_with_form_data(self, mock_session, default_headers):
        """폼 데이터로 HTTP POST 요청 테스트"""
        url = "https://api.example.com/submit"
        form_data = {"field1": "value1", "field2": "value2"}

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with aiohttp.ClientSession() as session:
                # 요청 실행
                response = await session.post(
                    url, headers=default_headers, data=form_data
                )

                # 호출 검증
                mock_session.post.assert_called_once_with(
                    url, headers=default_headers, data=form_data
                )

                # 응답 검증
                assert response.status == 200

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """오류 처리 테스트"""
        url = "https://api.example.com/error"

        # 네트워크 오류 모킹
        mock_error_session = MagicMock(spec=ClientSession)
        mock_error_session.get = AsyncMock(
            side_effect=ClientConnectorError(
                connection_key=None, os_error=OSError("Connection refused")
            )
        )
        mock_error_session.__aenter__.return_value = mock_error_session
        mock_error_session.__aexit__.return_value = None

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_error_session):
            async with aiohttp.ClientSession() as session:
                # 예외 처리 확인
                with pytest.raises(ClientConnectorError):
                    await session.get(url)

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """타임아웃 처리 테스트"""
        url = "https://api.example.com/slow"

        # 타임아웃 오류 모킹
        mock_timeout_session = MagicMock(spec=ClientSession)
        mock_timeout_session.get = AsyncMock(
            side_effect=ServerTimeoutError("Timeout exceeded")
        )
        mock_timeout_session.__aenter__.return_value = mock_timeout_session
        mock_timeout_session.__aexit__.return_value = None

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_timeout_session):
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=5)) as session:
                # 예외 처리 확인
                with pytest.raises(ServerTimeoutError):
                    await session.get(url)

    @pytest.mark.asyncio
    async def test_http_error_status(self):
        """HTTP 오류 상태 코드 테스트"""
        url = "https://api.example.com/not-found"

        # 404 응답 모킹
        mock_404_response = AsyncMock(spec=ClientResponse)
        mock_404_response.status = 404
        mock_404_response.reason = "Not Found"
        mock_404_response.text = AsyncMock(return_value="Resource not found")
        mock_404_response.json = AsyncMock(
            side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
        )
        mock_404_response.__aenter__.return_value = mock_404_response
        mock_404_response.__aexit__.return_value = None

        mock_error_session = MagicMock(spec=ClientSession)
        mock_error_session.get = AsyncMock(return_value=mock_404_response)
        mock_error_session.__aenter__.return_value = mock_error_session
        mock_error_session.__aexit__.return_value = None

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_error_session):
            async with aiohttp.ClientSession() as session:
                response = await session.get(url)

                # 응답 검증
                assert response.status == 404
                assert response.reason == "Not Found"
                text = await response.text()
                assert text == "Resource not found"

                # JSON 디코딩 실패 테스트
                with pytest.raises(json.JSONDecodeError):
                    await response.json()

    @pytest.mark.asyncio
    async def test_session_resource_cleanup(self, mock_session):
        """세션 리소스 정리 테스트"""
        with patch("aiohttp.ClientSession", return_value=mock_session):
            session = aiohttp.ClientSession()
            await session.close()

            # 세션이 닫혔는지 확인
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_ssl_verification(self, mock_session):
        """SSL 인증 테스트"""
        url = "https://api.example.com/secure"

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # SSL 검증 활성화
            async with aiohttp.ClientSession(verify_ssl=True) as session:
                await session.get(url)

            # SSL 검증 비활성화
            async with aiohttp.ClientSession(verify_ssl=False) as session:
                await session.get(url)

    @pytest.mark.asyncio
    async def test_custom_headers(self, mock_session):
        """사용자 정의 헤더 테스트"""
        url = "https://api.example.com/headers"
        custom_headers = {
            "User-Agent": "CustomBot/1.0",
            "Authorization": "Bearer token123",
            "Accept-Language": "ko-KR",
            "X-Custom-Header": "Custom Value",
        }

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with aiohttp.ClientSession() as session:
                # 요청 실행
                response = await session.get(url, headers=custom_headers)

                # 호출 검증
                mock_session.get.assert_called_once_with(url, headers=custom_headers)

    @pytest.mark.asyncio
    async def test_delete_request(self, mock_session):
        """HTTP DELETE 요청 테스트"""
        url = "https://api.example.com/resource/123"

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with aiohttp.ClientSession() as session:
                # 요청 실행
                response = await session.delete(url)

                # 호출 검증
                mock_session.delete.assert_called_once_with(url)

                # 응답 검증
                assert response.status == 200

    @pytest.mark.asyncio
    async def test_put_request(self, mock_session):
        """HTTP PUT 요청 테스트"""
        url = "https://api.example.com/resource/123"
        data = {"name": "Updated Resource", "active": True}

        # ClientSession 모킹
        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with aiohttp.ClientSession() as session:
                # 요청 실행
                response = await session.put(url, json=data)

                # 호출 검증
                mock_session.put.assert_called_once_with(url, json=data)

                # 응답 검증
                assert response.status == 200
                result = await response.json()
                assert result == {"data": "test"}


class TestRequestsIntegration:
    """실제 HTTP 통합 테스트 (건너뜀)"""

    @pytest.mark.skip(reason="실제 네트워크 요청은 CI/CD 환경에서 건너뜁니다")
    @pytest.mark.asyncio
    async def test_real_http_request(self):
        """실제 HTTP 요청 테스트 (로컬 개발 시에만 실행)"""
        # 환경 변수로 비활성화 가능
        if os.environ.get("SKIP_REAL_REQUESTS", "false").lower() == "true":
            pytest.skip("실제 네트워크 요청 테스트를 건너뜁니다")

        url = "https://httpbin.org/get"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                assert response.status == 200
                data = await response.json()
                assert "url" in data
                assert data["url"] == url


# HTTP 클라이언트 예제 (실제 사용 시 별도 파일로 분리할 수 있음)
class HttpClient:
    """HTTP 클라이언트 예제 클래스"""

    def __init__(self, base_url: str = "", timeout: int = 30):
        """
        HTTP 클라이언트 초기화

        Args:
            base_url: 기본 URL (모든 요청에 사용)
            timeout: 기본 타임아웃 (초)
        """
        self.base_url = base_url
        self.timeout = timeout
        self._session = None

    async def __aenter__(self):
        """비동기 컨텍스트 관리자 진입"""
        self._session = aiohttp.ClientSession(timeout=ClientTimeout(total=self.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 관리자 종료"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _build_url(self, path: str) -> str:
        """경로에서 전체 URL 생성"""
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    async def get(self, path: str, **kwargs) -> ClientResponse:
        """GET 요청 수행"""
        url = self._build_url(path)
        return await self._session.get(url, **kwargs)

    async def post(self, path: str, **kwargs) -> ClientResponse:
        """POST 요청 수행"""
        url = self._build_url(path)
        return await self._session.post(url, **kwargs)

    async def put(self, path: str, **kwargs) -> ClientResponse:
        """PUT 요청 수행"""
        url = self._build_url(path)
        return await self._session.put(url, **kwargs)

    async def delete(self, path: str, **kwargs) -> ClientResponse:
        """DELETE 요청 수행"""
        url = self._build_url(path)
        return await self._session.delete(url, **kwargs)


class TestHttpClientClass:
    """HTTP 클라이언트 클래스 테스트"""

    @pytest.fixture
    def mock_response(self):
        """HTTP 응답을 모킹하는 픽스처"""
        mock_resp = AsyncMock(spec=ClientResponse)
        mock_resp.status = 200
        mock_resp.reason = "OK"
        mock_resp.json = AsyncMock(return_value={"data": "test"})
        mock_resp.text = AsyncMock(return_value="response text")
        mock_resp.read = AsyncMock(return_value=b"binary data")
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.__aenter__.return_value = mock_resp
        mock_resp.__aexit__.return_value = None
        return mock_resp

    @pytest.fixture
    def mock_client_session(self, mock_response):
        """ClientSession 클래스를 모킹하는 픽스처"""
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session_instance = AsyncMock()
            mock_session_instance.get = AsyncMock(return_value=mock_response)
            mock_session_instance.post = AsyncMock(return_value=mock_response)
            mock_session_instance.put = AsyncMock(return_value=mock_response)
            mock_session_instance.delete = AsyncMock(return_value=mock_response)
            mock_session_instance.close = AsyncMock()
            mock_session_instance.closed = False

            mock_session_cls.return_value = mock_session_instance
            yield mock_session_cls, mock_session_instance

    @pytest.mark.asyncio
    async def test_http_client_context_manager(self, mock_client_session):
        """HTTP 클라이언트 컨텍스트 관리자 테스트"""
        mock_session_cls, mock_session_instance = mock_client_session

        # 컨텍스트 관리자 테스트
        async with HttpClient(base_url="https://api.example.com") as client:
            # 세션이 생성되었는지 확인
            mock_session_cls.assert_called_once()

            # 기본 URL 확인
            assert client.base_url == "https://api.example.com"

            # GET 요청 테스트
            await client.get("/users")
            mock_session_instance.get.assert_called_once_with(
                "https://api.example.com/users"
            )

        # 컨텍스트 종료 후 세션이 닫혔는지 확인
        mock_session_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_client_methods(self, mock_client_session):
        """HTTP 클라이언트 메서드 테스트"""
        mock_session_cls, mock_session_instance = mock_client_session

        async with HttpClient(base_url="https://api.example.com") as client:
            # 절대 URL 테스트
            absolute_url = "https://other-api.example.com/data"
            await client.get(absolute_url)
            mock_session_instance.get.assert_called_with(absolute_url)

            # POST 요청 테스트
            json_data = {"name": "Test"}
            await client.post("/users", json=json_data)
            mock_session_instance.post.assert_called_once_with(
                "https://api.example.com/users", json=json_data
            )

            # PUT 요청 테스트
            update_data = {"name": "Updated"}
            await client.put("/users/123", json=update_data)
            mock_session_instance.put.assert_called_once_with(
                "https://api.example.com/users/123", json=update_data
            )

            # DELETE 요청 테스트
            await client.delete("/users/123")
            mock_session_instance.delete.assert_called_once_with(
                "https://api.example.com/users/123"
            )


class TestHttpClient(unittest.TestCase):
    """Test case for HTTP client implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.http_client = AioHttpClient(
            base_url="https://example.com/api",
            timeout=10,
            max_retries=2,
            retry_delay=1,
            rotate_user_agent=False,
        )

    def tearDown(self):
        """Tear down test fixtures."""
        # Close the client if it was opened
        if self.http_client._session and not self.http_client._session.closed:
            # Can't use asyncio.run here as it would create a new event loop
            pass

    @pytest.mark.asyncio
    async def test_ensure_session(self):
        """Test ensuring a session exists."""
        # Call the method
        session = await self.http_client._ensure_session()

        # Assertions
        self.assertIsInstance(session, aiohttp.ClientSession)
        self.assertEqual(session, self.http_client._session)

        # Call again to test reuse
        session2 = await self.http_client._ensure_session()
        self.assertEqual(session, session2)

    @pytest.mark.asyncio
    async def test_get_headers(self):
        """Test getting request headers."""
        # Set default headers
        self.http_client.default_headers = {"X-Default": "Value"}

        # Call the method
        headers = await self.http_client._get_headers()

        # Assertions
        self.assertEqual(headers, {"X-Default": "Value"})

        # With request-specific headers
        headers = await self.http_client._get_headers({"X-Custom": "Custom"})
        self.assertEqual(headers, {"X-Default": "Value", "X-Custom": "Custom"})

        # Test override
        headers = await self.http_client._get_headers({"X-Default": "Override"})
        self.assertEqual(headers, {"X-Default": "Override"})

    @pytest.mark.asyncio
    async def test_user_agent_rotation(self):
        """Test user agent rotation."""
        # Create client with user agent rotation
        client = AioHttpClient(rotate_user_agent=True)

        # Get headers twice
        headers1 = await client._get_headers()
        headers2 = await client._get_headers()

        # Should have User-Agent in both
        self.assertIn("User-Agent", headers1)
        self.assertIn("User-Agent", headers2)

        # Should be different user agents
        self.assertNotEqual(headers1["User-Agent"], headers2["User-Agent"])

    @pytest.mark.asyncio
    async def test_request_success(self):
        """Test a successful request."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"data": "test"})

        # Mock client session
        mock_session = MagicMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        # Mock ensure_session to return our mock session
        self.http_client._ensure_session = AsyncMock(return_value=mock_session)

        # Call the method
        result = await self.http_client._request("GET", "/test")

        # Assertions
        mock_session.request.assert_called_once()
        self.assertEqual(result, {"data": "test"})

    @pytest.mark.asyncio
    async def test_request_error_retry(self):
        """Test request retry on error."""
        # Mock client session
        mock_session = MagicMock()
        mock_session.request = AsyncMock(
            side_effect=[aiohttp.ClientError("Test error"), MagicMock()]
        )

        # Mock response for second attempt
        mock_response = mock_session.request.side_effect[1]
        mock_response.json = AsyncMock(return_value={"data": "retry success"})

        # Mock ensure_session and sleep
        self.http_client._ensure_session = AsyncMock(return_value=mock_session)

        # Patch asyncio.sleep to avoid actual delay
        with patch("asyncio.sleep", AsyncMock()):
            # Call the method
            result = await self.http_client._request("GET", "/test")

        # Assertions
        self.assertEqual(mock_session.request.call_count, 2)
        self.assertEqual(result, {"data": "retry success"})

    @pytest.mark.asyncio
    async def test_request_max_retries(self):
        """Test request max retries."""
        # Mock client session
        mock_session = MagicMock()
        mock_session.request = AsyncMock(
            side_effect=[
                aiohttp.ClientError("Error 1"),
                aiohttp.ClientError("Error 2"),
                # No third attempt expected
            ]
        )

        # Mock ensure_session and sleep
        self.http_client._ensure_session = AsyncMock(return_value=mock_session)

        # Patch asyncio.sleep to avoid actual delay
        with patch("asyncio.sleep", AsyncMock()):
            # Call the method - should raise exception after max retries
            with self.assertRaises(Exception):
                await self.http_client._request("GET", "/test")

        # Assertions
        self.assertEqual(
            mock_session.request.call_count, 2
        )  # Should attempt exactly max_retries (2)

    @pytest.mark.asyncio
    async def test_request_url_handling(self):
        """Test URL handling in requests."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"data": "test"})

        # Mock client session
        mock_session = MagicMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        # Mock ensure_session to return our mock session
        self.http_client._ensure_session = AsyncMock(return_value=mock_session)

        # Test relative URL
        await self.http_client._request("GET", "/relative")
        mock_session.request.assert_called_with(
            method="GET",
            url="https://example.com/api/relative",
            params=None,
            data=None,
            json=None,
            headers={},
            timeout=aiohttp.ClientTimeout(total=10),
            raise_for_status=True,
        )

        # Reset mock
        mock_session.request.reset_mock()

        # Test absolute URL
        await self.http_client._request("GET", "https://other.com/test")
        mock_session.request.assert_called_with(
            method="GET",
            url="https://other.com/test",
            params=None,
            data=None,
            json=None,
            headers={},
            timeout=aiohttp.ClientTimeout(total=10),
            raise_for_status=True,
        )

    @pytest.mark.asyncio
    async def test_get(self):
        """Test GET method."""
        # Mock _request method
        self.http_client._request = AsyncMock(return_value={"data": "test"})

        # Call the method
        result = await self.http_client.get(
            "/test", params={"param": "value"}, headers={"X-Test": "Header"}
        )

        # Assertions
        self.http_client._request.assert_called_once_with(
            "GET", "/test", params={"param": "value"}, headers={"X-Test": "Header"}
        )
        self.assertEqual(result, {"data": "test"})

    @pytest.mark.asyncio
    async def test_post(self):
        """Test POST method."""
        # Mock _request method
        self.http_client._request = AsyncMock(return_value={"data": "test"})

        # Call the method
        result = await self.http_client.post(
            "/test",
            data={"form": "data"},
            json_data={"json": "data"},
            headers={"X-Test": "Header"},
        )

        # Assertions
        self.http_client._request.assert_called_once_with(
            "POST",
            "/test",
            data={"form": "data"},
            json_data={"json": "data"},
            headers={"X-Test": "Header"},
        )
        self.assertEqual(result, {"data": "test"})

    @pytest.mark.asyncio
    async def test_put(self):
        """Test PUT method."""
        # Mock _request method
        self.http_client._request = AsyncMock(return_value={"data": "test"})

        # Call the method
        result = await self.http_client.put(
            "/test",
            data={"form": "data"},
            json_data={"json": "data"},
            headers={"X-Test": "Header"},
        )

        # Assertions
        self.http_client._request.assert_called_once_with(
            "PUT",
            "/test",
            data={"form": "data"},
            json_data={"json": "data"},
            headers={"X-Test": "Header"},
        )
        self.assertEqual(result, {"data": "test"})

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test DELETE method."""
        # Mock _request method
        self.http_client._request = AsyncMock(return_value={"data": "test"})

        # Call the method
        result = await self.http_client.delete("/test", headers={"X-Test": "Header"})

        # Assertions
        self.http_client._request.assert_called_once_with(
            "DELETE", "/test", headers={"X-Test": "Header"}
        )
        self.assertEqual(result, {"data": "test"})

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client."""
        # Mock session
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()

        # Set the session
        self.http_client._session = mock_session

        # Call the method
        await self.http_client.close()

        # Assertions
        mock_session.close.assert_called_once()
        self.assertIsNone(self.http_client._session)

    @pytest.mark.asyncio
    async def test_close_no_session(self):
        """Test closing the client with no session."""
        # Ensure no session
        self.http_client._session = None

        # Call the method - should not raise
        await self.http_client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using the client as a context manager."""
        # Mock methods
        self.http_client.connect = AsyncMock()
        self.http_client.disconnect = AsyncMock()

        # Use as context manager
        async with self.http_client:
            pass

        # Assertions
        self.http_client.connect.assert_called_once()
        self.http_client.disconnect.assert_called_once()
