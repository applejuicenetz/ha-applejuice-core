"""appleJuice Client."""

import asyncio
import hashlib
import logging

import aiohttp
import defusedxml.ElementTree as ET

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import TIMEOUT

_LOGGER = logging.getLogger(__name__)


async def get_xml_data(hass: HomeAssistant, url: str, port: int, password: str, tls: bool, endpoint: str):
    """Fetch XML data asynchronously using aiohttp."""

    session = aiohttp_client.async_get_clientsession(hass)

    try:
        protocol = "https" if tls else "http"
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        full_url = f"{protocol}://{url}:{port}{endpoint}?password={hashed_password}"

        _LOGGER.debug("call url: %s", full_url)

        async with asyncio.timeout(TIMEOUT):
            async with session.get(full_url) as response:
                response.raise_for_status()
                xml_text = await response.text()

                return ET.fromstring(xml_text)

    except aiohttp.ClientError as e:
        _LOGGER.error("Error while fetching XML data: %s", e)

    return None
