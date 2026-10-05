"""Binary sensor platform for the appleJuice Core integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from xml.etree.ElementTree import Element

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AppleJuiceConfigEntry
from .entity import AppleJuiceCoreEntity

PARALLEL_UPDATES = 0


def _networkinfo_flag(name: str, default: str) -> Callable[[Element], bool]:
    def value(data: Element) -> bool:
        node = data.find("networkinfo")
        return (node.attrib.get(name, default) if node is not None else default) == "true"

    return value


@dataclass(frozen=True, kw_only=True)
class AppleJuiceBinarySensorDescription(BinarySensorEntityDescription):
    """Describes an appleJuice binary sensor."""

    value_fn: Callable[[Element], bool]


BINARY_SENSORS: tuple[AppleJuiceBinarySensorDescription, ...] = (
    AppleJuiceBinarySensorDescription(
        key="firewalled",
        name="Firewall",
        icon="mdi:security",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_networkinfo_flag("firewalled", "false"),
    ),
    AppleJuiceBinarySensorDescription(
        key="paused",
        name="Paused",
        icon="mdi:pause-circle",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_networkinfo_flag("paused", "true"),
    ),
)


class AppleJuiceBinarySensor(AppleJuiceCoreEntity, BinarySensorEntity):
    """Binary sensor of the Core device."""

    entity_description: AppleJuiceBinarySensorDescription

    @property
    def is_on(self) -> bool:
        """Current state."""
        return self.entity_description.value_fn(self.coordinator.data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AppleJuiceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensor platform."""
    async_add_entities(AppleJuiceBinarySensor(entry.runtime_data, desc) for desc in BINARY_SENSORS)
