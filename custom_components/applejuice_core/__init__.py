"""appleJuice Core integration for Home Assistant."""

import asyncio
import logging
from datetime import timedelta
import xml.etree.ElementTree as ET

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    DOMAIN,
    CONF_URL,
    CONF_PORT,
    CONF_PASSWORD,
    CONF_TLS,
    PLATFORMS,
    CONF_OPTION_POLLING_RATE,
)

from .api import get_xml_data

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

_LOGGER.debug("loading appleJuice Core init")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the appleJuice Core integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    hass.data[DOMAIN][entry.entry_id].config_entry = entry
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if await hass.config_entries.async_forward_entry_unload(entry, "sensor"):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    global SCAN_INTERVAL

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    if entry.options.get(CONF_OPTION_POLLING_RATE) is not None:
        SCAN_INTERVAL = timedelta(seconds=entry.options.get(CONF_OPTION_POLLING_RATE))
    else:
        SCAN_INTERVAL = timedelta(seconds=30)

    coordinator = AppleJuiceCoordinator(hass, config_entry=entry)

    await coordinator.async_config_entry_first_refresh()

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        coordinator.platforms.append(platform)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


class AppleJuiceCoordinator(DataUpdateCoordinator):
    """Handles periodic XML data retrieval."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the coordinator with update interval settings."""
        self.system = None
        self.version = None
        self.platforms = []
        self.updaters = [
            _async_update_modified,
            _async_update_share,
        ]
        self.hass = hass
        self.config_entry = config_entry

        self.name = f"appleJuice Core {config_entry.data.get(CONF_URL)}:{config_entry.data.get(CONF_PORT)}"

        super().__init__(hass, _LOGGER, name=self.name, update_interval=SCAN_INTERVAL, always_update=False)

    async def _async_setup(self):
        """Fetch general device information (version and system)."""
        xml_data = await get_xml_data(self.hass,
                                      self.config_entry.data.get(CONF_URL),
                                      self.config_entry.data.get(CONF_PORT),
                                      self.config_entry.data.get(CONF_PASSWORD),
                                      self.config_entry.data.get(CONF_TLS),
                                      "/xml/information.xml")

        if xml_data is not None:
            general_info = xml_data.find("generalinformation")
            if general_info is not None:
                general_info = xml_data.find("generalinformation")
                self.version = general_info.find("version").text if general_info.find("version") is not None else "Unknown"
                self.system = general_info.find("system").text if general_info.find("system") is not None else "Unknown"
                _LOGGER.debug("version %s, system %s", self.version, self.system)
            else:
                _LOGGER.debug("version and system not found in XML data")
        else:
            _LOGGER.debug("/xml/information.xml xml data not found")

    async def _async_update_data(self):
        """Update data via library."""
        combined_data = ET.Element("root")

        for updater in self.updaters:
            xml_data = await updater(self)
            if xml_data is not None:
                for child in xml_data:
                    combined_data.append(child)

        return combined_data


async def _async_update_modified(self):
    """Fetch XML data asynchronously."""
    return await get_xml_data(self.hass,
                              self.config_entry.data.get(CONF_URL),
                              self.config_entry.data.get(CONF_PORT),
                              self.config_entry.data.get(CONF_PASSWORD),
                              self.config_entry.data.get(CONF_TLS),
                              "/xml/modified.xml")


async def _async_update_share(self):
    """Fetch XML share data asynchronously."""
    return await get_xml_data(self.hass,
                              self.config_entry.data.get(CONF_URL),
                              self.config_entry.data.get(CONF_PORT),
                              self.config_entry.data.get(CONF_PASSWORD),
                              self.config_entry.data.get(CONF_TLS),
                              "/xml/share.xml")
