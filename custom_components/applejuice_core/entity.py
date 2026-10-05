"""Base entities for the appleJuice Core integration."""

from __future__ import annotations

from xml.etree.ElementTree import Element

from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AppleJuiceError
from .const import DOMAIN
from .coordinator import AppleJuiceCoordinator


class AppleJuiceCoreEntity(CoordinatorEntity[AppleJuiceCoordinator]):
    """Entity attached to the appleJuice Core device."""

    _attr_has_entity_name = True
    _unique_id_prefix = ""

    def __init__(self, coordinator: AppleJuiceCoordinator, description: EntityDescription) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{self._unique_id_prefix}{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Device of the Core."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=self.coordinator.name,
            sw_version=self.coordinator.version,
            hw_version=self.coordinator.system,
            model="appleJuice Core",
            manufacturer="appleJuiceNETZ",
            entry_type=DeviceEntryType.SERVICE,
        )


class AppleJuiceNetworkEntity(AppleJuiceCoreEntity):
    """Entity attached to the appleJuice Network device."""

    @property
    def device_info(self) -> DeviceInfo:
        """Device of the Network (linked to the Core device in __init__)."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.config_entry.entry_id}_network")},
            name="appleJuice Network",
            model="appleJuice Network",
            manufacturer="appleJuiceNETZ",
            entry_type=DeviceEntryType.SERVICE,
        )


class AppleJuiceSettingEntity(AppleJuiceCoreEntity):
    """Entity backed by /xml/settings.xml and /function/setsettings."""

    _attr_entity_category = EntityCategory.CONFIG
    _unique_id_prefix = "setting_"

    @property
    def _raw(self) -> str | None:
        """Raw value of this setting in settings.xml."""
        data: Element | None = self.coordinator.data
        if data is None:
            return None
        node = data.find(f"settings/{self.entity_description.tag}")
        return node.text if node is not None else None

    @property
    def available(self) -> bool:
        """Available if the value is present in settings.xml."""
        return super().available and self._raw is not None

    async def _async_set(self, value: str | int) -> None:
        """Write one setting and refresh."""
        param = getattr(self.entity_description, "param", None) or self.entity_description.tag
        try:
            await self.coordinator.client.call_function("setsettings", {param: value})
        except AppleJuiceError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="cannot_connect"
            ) from err
        await self.coordinator.async_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Write state on update."""
        self.async_write_ha_state()
