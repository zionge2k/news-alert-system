"""
HTTP client interface and implementation.

This module provides an abstraction over HTTP clients with retry logic,
error handling, and connection management.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

import aiohttp
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class HttpClient(ABC):
    """Interface for HTTP clients."""

    @abstractmethod
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a GET request.

        Args:
            url: The URL to request
            params: Query parameters
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        pass

    @abstractmethod
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a POST request.

        Args:
            url: The URL to request
            data: Form data
            json_data: JSON data
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        pass

    @abstractmethod
    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a PUT request.

        Args:
            url: The URL to request
            data: Form data
            json_data: JSON data
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        pass

    @abstractmethod
    async def delete(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a DELETE request.

        Args:
            url: The URL to request
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        pass


class AioHttpClient(HttpClient):
    """Implementation of HttpClient using aiohttp."""

    def __init__(
        self,
        base_url: str = "",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1,
        rotate_user_agent: bool = True,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            rotate_user_agent: Whether to use a random user agent for each request
            default_headers: Default HTTP headers to include with every request
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rotate_user_agent = rotate_user_agent
        self.default_headers = default_headers or {}
        self._session = None
        self._user_agent = UserAgent() if rotate_user_agent else None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """
        Ensure that a session exists and create one if it doesn't.

        Returns:
            The aiohttp client session
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Get headers for a request, combining default headers, user agent (if enabled), and request-specific headers.

        Args:
            headers: Request-specific headers

        Returns:
            The combined headers
        """
        combined_headers = self.default_headers.copy()

        if self.rotate_user_agent:
            combined_headers["User-Agent"] = self._user_agent.random

        if headers:
            combined_headers.update(headers)

        return combined_headers

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: The URL to request
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails after all retries
        """
        if not url.startswith(("http://", "https://")):
            url = f"{self.base_url}{url}"

        request_headers = await self._get_headers(headers)
        session = await self._ensure_session()

        for attempt in range(self.max_retries):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    raise_for_status=True,
                ) as response:
                    try:
                        return await response.json()
                    except json.JSONDecodeError:
                        # If not JSON, return the text
                        text = await response.text()
                        return {"text": text}
            except aiohttp.ClientError as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay
                    backoff_delay = self.retry_delay * (2**attempt)
                    logger.info(f"Retrying in {backoff_delay} seconds...")
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(
                        f"Request failed after {self.max_retries} attempts: {e}"
                    )
                    raise Exception(f"HTTP request failed: {e}")

    async def close(self) -> None:
        """Close the HTTP client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a GET request.

        Args:
            url: The URL to request
            params: Query parameters
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        return await self._request("GET", url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a POST request.

        Args:
            url: The URL to request
            data: Form data
            json_data: JSON data
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        return await self._request(
            "POST", url, data=data, json_data=json_data, headers=headers
        )

    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a PUT request.

        Args:
            url: The URL to request
            data: Form data
            json_data: JSON data
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        return await self._request(
            "PUT", url, data=data, json_data=json_data, headers=headers
        )

    async def delete(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a DELETE request.

        Args:
            url: The URL to request
            headers: HTTP headers

        Returns:
            The response body as a dictionary

        Raises:
            Exception: If the request fails
        """
        return await self._request("DELETE", url, headers=headers)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
