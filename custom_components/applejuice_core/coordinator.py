"""Data update coordinator for the appleJuice Core integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from xml.etree.ElementTree import Element

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AppleJuiceAuthError, AppleJuiceClient, AppleJuiceError
from .const import CONF_OPTION_POLLING_RATE, CONF_PORT, CONF_URL, DEFAULT_POLLING_RATE, DOMAIN

_LOGGER = logging.getLogger(__name__)

type AppleJuiceConfigEntry = ConfigEntry[AppleJuiceCoordinator]


class AppleJuiceCoordinator(DataUpdateCoordinator[Element]):
    """Polls modified.xml, share.xml and settings.xml and merges them into one tree."""

    config_entry: AppleJuiceConfigEntry

    def __init__(self, hass: HomeAssistant, entry: AppleJuiceConfigEntry, client: AppleJuiceClient) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.version: str | None = None
        self.system: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"appleJuice Core {entry.data[CONF_URL]}:{entry.data[CONF_PORT]}",
            config_entry=entry,
            update_interval=timedelta(seconds=entry.options.get(CONF_OPTION_POLLING_RATE, DEFAULT_POLLING_RATE)),
        )

    async def _async_setup(self) -> None:
        """Fetch static core information (version and system)."""
        try:
            info = await self.client.get_xml("/xml/information.xml")
        except AppleJuiceAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except AppleJuiceError as err:
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN, translation_key="cannot_connect"
            ) from err

        general = info.find("generalinformation")
        if general is not None:
            self.version = general.findtext("version")
            self.system = general.findtext("system")
        _LOGGER.debug("version %s, system %s", self.version, self.system)

    async def _async_update_data(self) -> Element:
        """Fetch all XML documents and merge them below one root."""
        try:
            modified, share, settings = await asyncio.gather(
                self.client.get_xml("/xml/modified.xml"),
                self.client.get_xml("/xml/share.xml"),
                self.client.get_xml("/xml/settings.xml"),
            )
        except AppleJuiceAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except AppleJuiceError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="cannot_connect"
            ) from err

        root = Element("root")
        root.extend(list(modified))
        root.extend(list(share))
        root.append(settings)
        return root
