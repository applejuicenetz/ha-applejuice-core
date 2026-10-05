"""appleJuice Core integration for Home Assistant."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AppleJuiceClient
from .const import DOMAIN, CONF_PASSWORD, CONF_PORT, CONF_TLS, CONF_URL, PLATFORMS
from .coordinator import AppleJuiceConfigEntry, AppleJuiceCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: AppleJuiceConfigEntry) -> bool:
    """Set up appleJuice Core from a config entry."""
    client = AppleJuiceClient(
        async_get_clientsession(hass),
        entry.data[CONF_URL],
        entry.data[CONF_PORT],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_TLS, False),
    )
    coordinator = AppleJuiceCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    _async_register_devices(hass, entry, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AppleJuiceConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _async_register_devices(hass: HomeAssistant, entry: AppleJuiceConfigEntry, coordinator: AppleJuiceCoordinator) -> None:
    """Register Core and Network device and link the Network to the Core.

    The link is set via the device id, because `via_device` in DeviceInfo is deprecated.
    """
    registry = dr.async_get(hass)
    core = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=coordinator.name,
        model="appleJuice Core",
        manufacturer="appleJuiceNETZ",
        sw_version=coordinator.version,
        hw_version=coordinator.system,
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    network = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.entry_id}_network")},
        name="appleJuice Network",
        model="appleJuice Network",
        manufacturer="appleJuiceNETZ",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    if network.via_device_id != core.id:
        registry.async_update_device(network.id, via_device_id=core.id)
