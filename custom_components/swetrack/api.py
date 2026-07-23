"""Asynchronous client for the public SweTrack API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession


class SweTrackApiError(Exception):
    """Base SweTrack API exception."""


class SweTrackAuthError(SweTrackApiError):
    """Authentication failed."""


class SweTrackRateLimitError(SweTrackApiError):
    """API rate limit was reached."""


@dataclass(slots=True)
class SweTrackResponse:
    """Normalized API response."""

    data: Any
    headers: dict[str, str]


class SweTrackApiClient:
    """Small async client for SweTrack."""

    def __init__(self, session: ClientSession, api_key: str, base_url: str) -> None:
        self._session = session
        self._api_key = api_key.strip()
        self._base_url = base_url.rstrip("/") + "/"

    async def async_get_account(self) -> SweTrackResponse:
        """Return account information."""
        return await self._request("GET", "account/info")

    async def async_get_devices(self) -> SweTrackResponse:
        """Return all devices and their current state."""
        return await self._request("GET", "devices/info")

    async def async_get_event_count(self) -> SweTrackResponse:
        """Return one event page whose pagination contains the total count."""
        return await self._request(
            "POST",
            "events/list",
            json_data={
                "pagesize": 1,
                "page": 1,
                "sort": "latest",
                "onlywithposition": False,
            },
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
    ) -> SweTrackResponse:
        url = self._base_url + path.lstrip("/")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=json_data,
                timeout=30,
            ) as response:
                await self._raise_for_status(response)
                try:
                    payload = await response.json(content_type=None)
                except ValueError as err:
                    text = await response.text()
                    raise SweTrackApiError(
                        f"SweTrack returned invalid JSON: {text[:200]}"
                    ) from err

                return SweTrackResponse(
                    data=payload,
                    headers={key.lower(): value for key, value in response.headers.items()},
                )
        except SweTrackApiError:
            raise
        except ClientError as err:
            raise SweTrackApiError(f"Communication with SweTrack failed: {err}") from err

    @staticmethod
    async def _raise_for_status(response: ClientResponse) -> None:
        if response.status in (401, 403):
            raise SweTrackAuthError("Invalid or expired SweTrack API key")
        if response.status == 429:
            raise SweTrackRateLimitError("SweTrack API rate limit reached")
        if response.status >= 400:
            body = await response.text()
            raise SweTrackApiError(
                f"SweTrack API returned HTTP {response.status}: {body[:300]}"
            )
