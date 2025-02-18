import logging
from dataclasses import dataclass
from collections.abc import Callable
from datetime import datetime

from homeassistant.const import (
    EntityCategory,
    UnitOfInformation,
    UnitOfDataRate,
)

from homeassistant.core import callback

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from .const import DOMAIN
from .entity import BaseAppleJuiceCoreEntity

_LOGGER = logging.getLogger(__name__)

CONF_HTTPS = "https"
CONF_UPDATE_INTERVAL = "update_interval"

# Define unique icons for each sensor
SENSOR_ICONS = {
    "applejuice_servers": "mdi:server",
    "connected_server_name": "mdi:server-network",
}


@dataclass
class AppleJuiceCoreSensorDescription(SensorEntityDescription):
    """Class describing appleJuice Core sensor entities."""

    key: str
    name: str
    value_fn: Callable | None = None
    sensor_name: str | None = None
    icon: str | None = None
    unit: str | None = None
    state_class: str | None = None
    device_class: str | None = None
    subscriptions: list | None = None
    entity_category: str | None = None


SENSORS: tuple[AppleJuiceCoreSensorDescription, ...] = [
    AppleJuiceCoreSensorDescription(
        key="credits",
        name="Credits",
        icon="mdi:cash",
        unit=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        subscriptions=[("information", "credits")],
        value_fn=lambda sensor: round(int(sensor.coordinator.data.find("information").attrib.get("credits", "0")) / 1024 / 1024 / 1024, 2),
    ),
    AppleJuiceCoreSensorDescription(
        key="sessionupload",
        name="Session Upload",
        icon="mdi:upload-network",
        unit=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        subscriptions=[("information", "sessionupload")],
        value_fn=lambda sensor: round(int(sensor.coordinator.data.find("information").attrib.get("sessionupload", "0")) / 1024 / 1024 / 1024, 2),
    ),
    AppleJuiceCoreSensorDescription(
        key="sessiondownload",
        name="Session Download",
        icon="mdi:download-network",
        unit=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        subscriptions=[("information", "sessiondownload")],
        value_fn=lambda sensor: round(int(sensor.coordinator.data.find("information").attrib.get("sessiondownload", "0")) / 1024 / 1024 / 1024, 2),
    ),
    AppleJuiceCoreSensorDescription(
        key="uploadspeed",
        name="Upload Speed",
        icon="mdi:upload",
        unit=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        subscriptions=[("information", "uploadspeed")],
        value_fn=lambda sensor: round(int(sensor.coordinator.data.find("information").attrib.get("uploadspeed", "0")) / 1024 / 1024, 2),
    ),
    AppleJuiceCoreSensorDescription(
        key="downloadspeed",
        name="Download Speed",
        icon="mdi:download",
        unit=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        subscriptions=[("information", "downloadspeed")],
        value_fn=lambda sensor: round(int(sensor.coordinator.data.find("information").attrib.get("downloadspeed", "0")) / 1024 / 1024, 2),
    ),
    AppleJuiceCoreSensorDescription(
        key="openconnections",
        name="Connections",
        icon="mdi:connection",
        state_class=SensorStateClass.TOTAL,
        subscriptions=[("information", "openconnections")],
        value_fn=lambda sensor: sensor.coordinator.data.find("information").attrib.get("openconnections", "0"),
    ),
    AppleJuiceCoreSensorDescription(
        key="downloads",
        name="Downloads",
        icon="mdi:download-multiple",
        state_class=SensorStateClass.TOTAL,
        subscriptions=[("download")],
        value_fn=lambda sensor: len(sensor.coordinator.data.findall("download")),
    ),
    AppleJuiceCoreSensorDescription(
        key="uploads",
        name="Uploads",
        icon="mdi:upload-multiple",
        device_class=SensorStateClass.TOTAL,
        subscriptions=[("upload")],
        value_fn=lambda sensor: len(sensor.coordinator.data.findall("upload")),
    ),
    AppleJuiceCoreSensorDescription(
        key="known_servers",
        name="Known Servers",
        icon="mdi:server",
        device_class=SensorStateClass.TOTAL,
        subscriptions=[("server")],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda sensor: len(sensor.coordinator.data.findall("server")),
    ),
    AppleJuiceCoreSensorDescription(
        key="connected_server_name",
        name="Connected Server",
        icon="mdi:server-network",
        device_class=SensorStateClass.TOTAL,
        subscriptions=[("networkinfo")],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda sensor: sensor.coordinator.data.find("server[@id='{}']".format(sensor.coordinator.data.find("networkinfo").attrib.get("connectedwithserverid", ""))).attrib.get("host", "Unknown"),
    ),
    AppleJuiceCoreSensorDescription(
        key="connectedsince",
        name="Connected Since",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.DATE,
        subscriptions=[("networkinfo", "connectedsince")],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda sensor: datetime.fromtimestamp(int(sensor.coordinator.data.find("networkinfo").attrib.get("connectedsince", "0")) / 1000.0),
    ),
    AppleJuiceCoreSensorDescription(
        key="shared_files",
        name="Shared Files",
        icon="mdi:folder-file-outline",
        device_class=SensorStateClass.TOTAL,
        subscriptions=[("shares")],
        value_fn=lambda sensor: len(sensor.coordinator.data.find("shares").findall("share")),
    ),
    AppleJuiceCoreSensorDescription(
        key="shared_size",
        name="Share Size",
        icon="mdi:file-outline",
        unit=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        subscriptions=[("shares")],
        value_fn=lambda sensor: round(sum(int(share.attrib.get("size", 0)) for share in sensor.coordinator.data.find("shares").findall("share")) / 1024 / 1024 / 1024, 2),
    ),
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_basic_sensor(coordinator, entry, async_add_entities)


async def async_setup_basic_sensor(coordinator, entry, async_add_entities):
    """Set basic sensor platform."""
    async_add_entities([AppleJuiceCoreSensor(coordinator, entry, desc) for desc in SENSORS])


class AppleJuiceCoreSensor(BaseAppleJuiceCoreEntity, SensorEntity):
    """AppleJuiceCoreSensor Sensor class."""

    def __init__(self, coordinator, entry, description):
        """Init."""
        super().__init__(coordinator, entry)
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self.entity_description = description
        self._attr_native_value = description.value_fn(self)
        self._attr_icon = description.icon
        self._attr_native_unit_of_measurement = description.unit

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value_fn(self)
        self.async_write_ha_state()
