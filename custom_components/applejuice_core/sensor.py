"""Sensor platform for the appleJuice Core integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from xml.etree.ElementTree import Element

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfDataRate, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AppleJuiceConfigEntry
from .entity import AppleJuiceCoreEntity, AppleJuiceNetworkEntity

PARALLEL_UPDATES = 0

GB = 1024**3
MB = 1024**2


def _attr(data: Element, tag: str, name: str, default: str = "0") -> str:
    """Attribute of a top-level tag."""
    node = data.find(tag)
    return node.attrib.get(name, default) if node is not None else default


def _info_gb(name: str) -> Callable[[Element], float]:
    return lambda data: round(int(_attr(data, "information", name)) / GB, 2)


def _info_mb(name: str) -> Callable[[Element], float]:
    return lambda data: round(int(_attr(data, "information", name)) / MB, 2)


def _downloads_with_status(status: str) -> Callable[[Element], int]:
    return lambda data: sum(1 for d in data.findall("download") if d.attrib.get("status") == status)


def _connected_server(data: Element) -> str | None:
    server_id = _attr(data, "networkinfo", "connectedwithserverid", "")
    server = data.find(f"server[@id='{server_id}']") if server_id else None
    return server.attrib.get("host") if server is not None else None


def _connected_since(data: Element) -> datetime | None:
    millis = int(_attr(data, "networkinfo", "connectedsince"))
    return datetime.fromtimestamp(millis / 1000.0, tz=UTC) if millis else None


def _shares(data: Element) -> list[Element]:
    node = data.find("shares")
    return node.findall("share") if node is not None else []


@dataclass(frozen=True, kw_only=True)
class AppleJuiceSensorDescription(SensorEntityDescription):
    """Describes an appleJuice sensor."""

    value_fn: Callable[[Element], Any]


SENSORS_CORE: tuple[AppleJuiceSensorDescription, ...] = (
    AppleJuiceSensorDescription(
        key="credits",
        name="Credits",
        icon="mdi:cash",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_info_gb("credits"),
    ),
    AppleJuiceSensorDescription(
        key="sessionupload",
        name="Session Upload",
        icon="mdi:upload-network",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_info_gb("sessionupload"),
    ),
    AppleJuiceSensorDescription(
        key="sessiondownload",
        name="Session Download",
        icon="mdi:download-network",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_info_gb("sessiondownload"),
    ),
    AppleJuiceSensorDescription(
        key="uploadspeed",
        name="Upload Speed",
        icon="mdi:upload",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_info_mb("uploadspeed"),
    ),
    AppleJuiceSensorDescription(
        key="downloadspeed",
        name="Download Speed",
        icon="mdi:download",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_info_mb("downloadspeed"),
    ),
    AppleJuiceSensorDescription(
        key="openconnections",
        name="Connections",
        icon="mdi:connection",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: int(_attr(data, "information", "openconnections")),
    ),
    AppleJuiceSensorDescription(
        key="downloads_total",
        name="Downloads Total",
        icon="mdi:download-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.findall("download")),
    ),
    AppleJuiceSensorDescription(
        key="downloads_active",
        name="Downloads Active",
        icon="mdi:download-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_downloads_with_status("0"),
    ),
    AppleJuiceSensorDescription(
        key="downloads_ready",
        name="Downloads ready",
        icon="mdi:download-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_downloads_with_status("14"),
    ),
    AppleJuiceSensorDescription(
        key="downloads_paused",
        name="Downloads paused",
        icon="mdi:download-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_downloads_with_status("18"),
    ),
    AppleJuiceSensorDescription(
        key="uploads",
        name="Uploads",
        icon="mdi:upload-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.findall("upload")),
    ),
    AppleJuiceSensorDescription(
        key="connected_server_name",
        name="Connected Server",
        icon="mdi:server-network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_connected_server,
    ),
    AppleJuiceSensorDescription(
        key="connectedsince",
        name="Connected Since",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_connected_since,
    ),
    AppleJuiceSensorDescription(
        key="shared_files",
        name="Shared Files",
        icon="mdi:folder-file-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(_shares(data)),
    ),
    AppleJuiceSensorDescription(
        key="shared_size",
        name="Share Size",
        icon="mdi:file-outline",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(sum(int(s.attrib.get("size", 0)) for s in _shares(data)) / GB, 2),
    ),
)

SENSORS_NETWORK: tuple[AppleJuiceSensorDescription, ...] = (
    AppleJuiceSensorDescription(
        key="users",
        name="Users",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: int(_attr(data, "networkinfo", "users")),
    ),
    AppleJuiceSensorDescription(
        key="global_files",
        name="Global Files",
        icon="mdi:folder-file-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: int(_attr(data, "networkinfo", "files")),
    ),
    AppleJuiceSensorDescription(
        key="global_file_size",
        name="Global Size",
        native_unit_of_measurement=UnitOfInformation.TERABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(float(_attr(data, "networkinfo", "filesize").replace(",", ".")) / MB, 2),
    ),
    AppleJuiceSensorDescription(
        key="known_servers",
        name="Known Servers",
        icon="mdi:server",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.findall("server")),
    ),
)


class AppleJuiceCoreSensor(AppleJuiceCoreEntity, SensorEntity):
    """Sensor of the Core device."""

    entity_description: AppleJuiceSensorDescription

    @property
    def native_value(self) -> Any:
        """Current value, None if the data is malformed."""
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except (ValueError, TypeError, AttributeError):
            return None


class AppleJuiceNetworkSensor(AppleJuiceNetworkEntity, AppleJuiceCoreSensor):
    """Sensor of the Network device."""


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AppleJuiceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        [AppleJuiceCoreSensor(coordinator, desc) for desc in SENSORS_CORE]
        + [AppleJuiceNetworkSensor(coordinator, desc) for desc in SENSORS_NETWORK]
    )
