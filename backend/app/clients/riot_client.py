"""
Riot API Low-Level HTTP Client Module.

Solely responsible for low-level HTTP transport with the Riot Games Developer API.
Handles connection pooling, X-Riot-Token header injection, request routing,
exponential backoff retries with Retry-After header support, timeout enforcement,
and HTTP error handling.
"""

import time
import logging
from typing import Any, Dict, Optional
import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from app.core.settings import settings
from app.core.exceptions import (
    ConfigError,
    RiotAPIException,
    RiotAuthenticationError,
    RiotNotFoundError,
    RiotRateLimitError,
    RiotServerError,
)

logger = logging.getLogger("gamepulse.riot_client")


class RiotClient:
    """
    HTTP Client for Riot Games Developer API.

    Enforces single-responsibility low-level HTTP transport. All high-level business logic
    is delegated to dedicated domain services.
    """

    BASE_URL_TEMPLATE = "https://{region}.api.riotgames.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_region: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
    ) -> None:
        """
        Initializes the RiotClient HTTP Session.

        Args:
            api_key (str, optional): Riot API Key. Defaults to settings.RIOT_API_KEY.
            default_region (str, optional): Default routing region. Defaults to settings.RIOT_DEFAULT_REGION.
            timeout (float, optional): Timeout in seconds. Defaults to settings.RIOT_REQUEST_TIMEOUT.
            max_retries (int, optional): Max retries for 429/5xx responses. Defaults to settings.RIOT_MAX_RETRIES.
            backoff_factor (float, optional): Backoff factor for retries. Defaults to settings.RIOT_BACKOFF_FACTOR.
        """
        self._api_key = api_key or settings.RIOT_API_KEY
        if not self._api_key or not self._api_key.strip():
            raise ConfigError("RiotClient initialized without a valid API Key.")

        self.default_region = default_region or settings.RIOT_DEFAULT_REGION
        self.timeout = timeout if timeout is not None else settings.RIOT_REQUEST_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else settings.RIOT_MAX_RETRIES
        self.backoff_factor = backoff_factor if backoff_factor is not None else settings.RIOT_BACKOFF_FACTOR

        self._session = requests.Session()
        self._session.headers.update({
            "X-Riot-Token": self._api_key,
            "Accept": "application/json",
            "User-Agent": "GamePulse-AI/1.0",
        })

    def _build_url(self, endpoint: str, region: Optional[str] = None) -> str:
        """Constructs target URL for a region and endpoint path."""
        target_region = (region or self.default_region).lower()
        base_url = self.BASE_URL_TEMPLATE.format(region=target_region)
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{base_url}{endpoint}"

    def get(
        self,
        endpoint: str,
        region: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes an HTTP GET request with automatic retry handling."""
        return self._request_with_retry("GET", endpoint, region=region, params=params)

    def post(
        self,
        endpoint: str,
        region: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes an HTTP POST request with automatic retry handling."""
        return self._request_with_retry("POST", endpoint, region=region, json=json, params=params)

    def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        region: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Centralized request dispatcher with exponential backoff and 429 Retry-After support."""
        url = self._build_url(endpoint, region=region)
        attempt = 0

        while attempt <= self.max_retries:
            attempt += 1
            logger.debug(f"HTTP {method} request to {url} (Attempt {attempt}/{self.max_retries + 1})")

            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                )
                logger.info(f"Riot API Response [{response.status_code}] for {url}")

                if 200 <= response.status_code < 300:
                    try:
                        return response.json()
                    except ValueError:
                        return {"message": "Success with no content or non-JSON body"}

                status_code = response.status_code
                body_snippet = response.text[:200]

                if status_code in (401, 403):
                    logger.warning(f"Authentication failed ({status_code}) for URL {url}: {body_snippet}")
                    raise RiotAuthenticationError(
                        f"Riot API Authentication Failed ({status_code}). Check your API Key.",
                        status_code=status_code,
                        response_body=body_snippet,
                    )

                if status_code == 404:
                    logger.info(f"Resource not found (404) for URL {url}")
                    raise RiotNotFoundError(
                        "Requested Riot API resource not found (404).",
                        status_code=404,
                        response_body=body_snippet,
                    )

                if status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    logger.warning(
                        f"Rate limit hit (429) on {url}. Retry-After header specifies {retry_after}s. "
                        f"Attempt {attempt}/{self.max_retries + 1}"
                    )
                    if attempt <= self.max_retries:
                        time.sleep(retry_after)
                        continue
                    raise RiotRateLimitError(
                        f"Riot API rate limit exceeded after {self.max_retries} retries.",
                        retry_after=retry_after,
                        response_body=body_snippet,
                    )

                if status_code >= 500:
                    backoff_sleep = self.backoff_factor ** attempt
                    logger.warning(
                        f"Riot API Server Error ({status_code}) on {url}. "
                        f"Backing off for {backoff_sleep:.2f}s (Attempt {attempt}/{self.max_retries + 1})"
                    )
                    if attempt <= self.max_retries:
                        time.sleep(backoff_sleep)
                        continue
                    raise RiotServerError(
                        f"Riot API server error ({status_code}) after retries.",
                        status_code=status_code,
                        response_body=body_snippet,
                    )

                raise RiotAPIException(
                    f"Riot API request failed with status code {status_code}",
                    status_code=status_code,
                    response_body=body_snippet,
                )

            except Timeout as err:
                logger.error(f"Request timeout after {self.timeout}s for URL: {url} (Attempt {attempt})")
                if attempt <= self.max_retries:
                    time.sleep(self.backoff_factor ** attempt)
                    continue
                raise RiotAPIException(f"Request timed out after {self.timeout}s for endpoint: {endpoint}") from err

            except ConnectionError as err:
                logger.error(f"Connection failure to Riot API: {url} (Attempt {attempt})")
                if attempt <= self.max_retries:
                    time.sleep(self.backoff_factor ** attempt)
                    continue
                raise RiotAPIException(f"Network failure while connecting to endpoint: {endpoint}") from err

            except RequestException as err:
                logger.error(f"HTTP request exception for {url}: {err}")
                raise RiotAPIException(f"HTTP client exception: {str(err)}") from err

        raise RiotAPIException(f"Failed to execute HTTP request after {self.max_retries} attempts.")
