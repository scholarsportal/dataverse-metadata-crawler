"""HTTP client class for making GET requests."""
import asyncio
from types import TracebackType
from typing import Optional

import httpx


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

    async def _async_semaphore_client(self, url: str) -> httpx.Response | None:
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
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                # print(f'HTTP request Error for {url}: {exc}')
                return None

    def sync_get(self, url: str) -> httpx.Response | None:
        """Synchronous GET request.

        Args:
            url (str): URL to GET

        Returns:
            httpx.Response: Response object
        """
        if self.sync_client.is_closed:
            self.sync_client = httpx.Client(timeout=None)
        with self.sync_client as client:
            try:
                response = client.get(url)
                if response.status_code != self.httpx_success_status:
                    # print(f'HTTP request Error for {url}: {response.status_code}')
                    return None

            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                # print(f'HTTP request Error for {url}: {exc}')
                return None

            return response

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
