"""appleJuice Core XML API client."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode
from xml.etree.ElementTree import Element

import aiohttp
from defusedxml import DefusedXmlException
from defusedxml import ElementTree as DefusedET

from .const import TIMEOUT

_LOGGER = logging.getLogger(__name__)


class AppleJuiceError(Exception):
    """Base error of the appleJuice Core client."""


class AppleJuiceConnectionError(AppleJuiceError):
    """Core is not reachable or returned an invalid answer."""


class AppleJuiceAuthError(AppleJuiceError):
    """Core rejected the password."""


class AppleJuiceUnsupportedError(AppleJuiceError):
    """Core does not know the requested function."""


class AppleJuiceClient:
    """Small async client for the Core XML/function API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        password: str,
        tls: bool,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._base = f"{'https' if tls else 'http'}://{host}:{port}"
        self._password_hash = hashlib.md5(password.encode()).hexdigest()  # noqa: S324 - protocol requirement

    async def _get(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        """GET a path and return the body. The password is never logged."""
        query = {"password": self._password_hash, **(params or {})}
        url = f"{self._base}{path}?{urlencode(query)}"
        _LOGGER.debug("GET %s%s", self._base, path)

        try:
            async with asyncio.timeout(TIMEOUT):
                async with self._session.get(url, allow_redirects=False) as response:
                    if 300 <= response.status < 400:
                        location = response.headers.get("Location", "")
                        if "wrongpassword" in location:
                            raise AppleJuiceAuthError("wrong password")
                        raise AppleJuiceUnsupportedError(f"{path} redirected to {location}")
                    response.raise_for_status()
                    return await response.text()
        except TimeoutError as err:
            raise AppleJuiceConnectionError("timeout") from err
        except aiohttp.ClientError as err:
            raise AppleJuiceConnectionError(str(err)) from err

    async def get_xml(self, endpoint: str) -> Element:
        """Fetch and parse an XML endpoint, e.g. /xml/modified.xml."""
        text = await self._get(endpoint)
        try:
            return DefusedET.fromstring(text)
        except (DefusedET.ParseError, DefusedXmlException) as err:
            raise AppleJuiceConnectionError(f"invalid XML from {endpoint}") from err

    async def call_function(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        """Call /function/<method>."""
        await self._get(f"/function/{method}", params)


def parse_version(version: str | None) -> tuple[int, ...] | None:
    """Parse '0.35.185.93' (optionally with suffix) into a comparable tuple."""
    if not version:
        return None
    try:
        return tuple(int(p) for p in re.sub(r"[^0-9.]", "", version).strip(".").split("."))
    except ValueError:
        return None
