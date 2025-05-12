"""HTTP client class for making GET requests."""
import asyncio
from types import TracebackType
from typing import Optional

import httpx
from urllib.parse import urljoin

class HttpxClient:
    """HTTP client class for making GET requests."""

    def __init__(self, config: dict) -> None:
        """Initialize HTTP client.

        Args:
            config (dict): Configuration settings
            semaphore (asyncio.Semaphore): Semaphore object for limiting concurrent requests
            sync_client (httpx.Client): Synchronous HTTP client
            async_client (httpx.AsyncClient): Asynchronous HTTP client
            async_sleep_time (int): Sleep time for asynchronous requests
        """  # noqa: W505
        self.config = config
        self.semaphore = asyncio.Semaphore(10)  # 10 concurrent requests # TODO: make this configurable
        self.sync_client = httpx.Client(timeout=None, headers=dict(config['HEADERS']))
        self.async_client = httpx.AsyncClient(timeout=None, headers=dict(config['HEADERS']))
        self.async_sleep_time = 0  # TODO: make this configurable
        self.httpx_success_status = 200

    def __enter__(self) -> 'HttpxClient':
        """Enter context manager.

        Returns:
            HttpxClient: Self reference
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Exit context manager and cleanup resources.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        self.sync_client.close()
        if not self.async_client.is_closed:
            asyncio.run(self.async_client.aclose())

    async def __aenter__(self) -> 'HttpxClient':
        """Enter asynchronous context manager."""
        return self

    async def __aexit__(self,
                        exc_type: Optional[type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        """Exit asynchronous context manager and cleanup resources."""
        await self.async_client.aclose()
        self.sync_client.close()

    async def _async_semaphore_client(self, url: str) -> httpx.Response | list[str]:
        """Asynchronous HTTP client with semaphore.

        Args:
            url (str): URL to GET

        Returns:
            httpx.Response: Response object
        """
        async with self.semaphore:
            try:
                response = await self.async_client.get(url)
                if response.status_code != self.httpx_success_status:
                    # print(f'HTTP request Error for {url}: {response.status_code}')
                    return response
                return response
            except (httpx.HTTPStatusError, httpx.RequestError):
                # print(f'HTTP request Error for {url}: {exc}')
                return httpx.Response(
                status_code=500,  # Server error as a fallback
                text='Error occurred during request',
                request=httpx.Request('GET', url)
            )

    def authenticate_api_key(self) -> bool:
        """Authenticate the API key for the Dataverse repository.

        Returns:
            bool: True if the API key is valid, False otherwise
        """
        base_url: str = self.config.get('BASE_URL', '')
        api_key: str = self.config.get('API_KEY', '')
        auth_headers: dict = {'X-Dataverse-key': api_key}
        auth_url = urljoin(base_url, '/api/info/version')

        try:
            with self.sync_client as client:
                response = client.get(auth_url, headers=auth_headers)
                return response.status_code == self.httpx_success_status
        except (httpx.HTTPStatusError, httpx.RequestError):
            return False

    def authenticate_dv_connection(self) -> bool:
        """Authenticate the connection to the Dataverse repository.

        Returns:
            bool: True if the connection is successful, False otherwise
        """
        base_url: str = self.config.get('BASE_URL', '')
        public_url: str = urljoin(base_url, '/api/info/version')

        try:
            with self.sync_client as client:
                response = client.get(public_url)
                return response.status_code == self.httpx_success_status
        except (httpx.HTTPStatusError, httpx.RequestError):
            return False

    def sync_get(self, url: str) -> httpx.Response | None:
        """Synchronous GET request.

        Args:
            url (str): URL to GET

        Returns:
            httpx.Response | None: Response object or None if error
        """
        try:
            # Create a new client for each request to avoid the "closed client" issue
            with httpx.Client(timeout=None, headers=dict(self.config['HEADERS'])) as client:
                response = client.get(url)
                return response if response.status_code == self.httpx_success_status else None
        except (httpx.HTTPStatusError, httpx.RequestError):
            return httpx.Response(
                status_code=500,  # Server error as a fallback
                text='Error occurred during request',
                request=httpx.Request('GET', url)
            )

    async def async_get(self, url_list: list) -> list:
        """Asynchronous GET request.

        Args:
            url_list (list): List of URLs to GET

        Returns:
            list: List of httpx.Response objects
        """
        tasks = [self._async_semaphore_client(url) for url in url_list]

        # Using asyncio.gather to collect results
        return await asyncio.gather(*tasks)
