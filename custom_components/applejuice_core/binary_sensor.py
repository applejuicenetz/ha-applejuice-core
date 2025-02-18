"""Binary sensors platform for appleJuice Core integration."""
import logging
from dataclasses import dataclass

from homeassistant.const import (
    EntityCategory,
)

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import DOMAIN
from .entity import BaseAppleJuiceCoreEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class AppleJuiceCoreBinarySensorDescription(BinarySensorEntityDescription):
    """Class describing appleJuice Core binary_sensor entities."""

    key: str
    name: str
    sensor_name: str | None = None
    subscriptions: list | None = None
    icon: str | None = None
    device_class: str | None = None
    entity_category: str | None = None


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the binary_sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_update_binary_sensors(coordinator, entry, async_add_devices)


async def async_setup_update_binary_sensors(coordinator, entry, async_add_entities):
    """Set Machine Update binary sensor."""

    desc = AppleJuiceCoreBinarySensorDescription(
        key="firewalled",
        sensor_name="firewalled",
        name="Firewall",
        subscriptions=[("networkinfo", "firewalled")],
        icon="mdi:security",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    )

    await coordinator.async_refresh()

    async_add_entities([AppleJuiceCoreBinarySensor(coordinator, entry, desc)])


class AppleJuiceCoreBinarySensor(BaseAppleJuiceCoreEntity, BinarySensorEntity):
    """appleJuice Core binary_sensor class."""

    def __init__(
            self,
            coordinator,
            entry,
            description,
    ) -> None:
        """Initialize the binary_sensor class."""
        _LOGGER.debug("loading appleJuice Core binary_sensor")
        super().__init__(coordinator, entry)
        self.entity_description = description
        self.sensor_name = description.sensor_name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self._attr_icon = description.icon

    @property
    def is_on(self):
        """Return true if the system is firewalled."""
        xml_data = self.coordinator.data
        if xml_data is not None:
            networkinfo = xml_data.find("networkinfo")
            return networkinfo.attrib.get("firewalled", "false") == "true"
        return False
