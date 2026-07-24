"""HTTP client class for making GET requests."""

import asyncio

import httpx2

from dvmeta.models.config import Config
from dvmeta.services.client.endpoints import Endpoints


class HttpxClient:
    """HTTP client class for making GET requests."""

    def __init__(self, config: Config) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config
        self.semaphore_num = config.semaphore_limit
        self.base_url = config.base_url

        self.header = (
            {"Accept": "application/json"}
            if not config.api_token
            else {"Accept": "application/json", "X-Dataverse-key": config.api_token}
        )

    async def _async_semaphore_client(
        self, request: httpx2.Request, semaphore: asyncio.Semaphore, client: httpx2.AsyncClient
    ) -> httpx2.Response:
        """Asynchronous HTTP client with semaphore.

        Args:
            request: Pre-built request object.
            semaphore: Semaphore bound to the current event loop.
            client: Async client bound to the current event loop.

        Returns:
            httpx2.Response: Response object.
        """
        async with semaphore:
            try:
                return await client.send(request)
            except (httpx2.HTTPStatusError, httpx2.RequestError):
                return httpx2.Response(
                    status_code=500, text="Error occurred during request", request=request
                )

    def check_dv_collection(self, *, auth: bool) -> httpx2.Response:
        """Check the connection to the Dataverse repository.

        Args:
            auth: Whether to authenticate with the API token or not.

        Returns:
            httpx2.Response: The response from the Dataverse repository.
        """
        endpoint = Endpoints.user_info() if auth else Endpoints.version_info()
        try:
            with httpx2.Client(timeout=None, headers=self.header, base_url=self.base_url) as client:
                return client.get(endpoint, headers=self.header if auth else None)
        except (httpx2.HTTPStatusError, httpx2.RequestError):
            return httpx2.Response(
                status_code=500, text="Error occurred during request", request=httpx2.Request("GET", endpoint)
            )

    def sync_get(self, url: str, params: list | dict | None = None) -> httpx2.Response | None:
        """Synchronous GET request.

        Args:
            url: The URL to request.
            params: Query parameters, by default None.

        Returns:
            The response, or None if the request was unsuccessful.
        """
        try:
            # Create a new client for each request to avoid the "closed client" issue
            with httpx2.Client(timeout=None, headers=self.header, base_url=self.base_url) as client:
                response = client.get(url, params=params)
                return response if response.is_success else None
        except (httpx2.HTTPStatusError, httpx2.RequestError):
            return httpx2.Response(
                status_code=500,  # Server error as a fallback
                text="Error occurred during request",
                request=httpx2.Request("GET", url),
            )

    async def async_get(self, url_list: list) -> list:
        """Asynchronous GET request.

        Args:
            url_list: List of URLs (str) or pre-built httpx2.Request objects to GET.

        Returns:
            list: List of httpx2.Response objects.
        """
        semaphore = asyncio.Semaphore(self.semaphore_num)
        async with httpx2.AsyncClient(
            timeout=None, headers=self.header, base_url=self.base_url
        ) as client:
            built = [
                client.build_request(r.method, str(r.url))
                if isinstance(r, httpx2.Request)
                else client.build_request("GET", r)
                for r in url_list
            ]
            tasks = [self._async_semaphore_client(request, semaphore, client) for request in built]
            return await asyncio.gather(*tasks)
