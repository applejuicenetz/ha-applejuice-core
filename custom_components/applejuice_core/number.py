"""Number platform: connection settings of the appleJuice Core."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AppleJuiceConfigEntry
from .entity import AppleJuiceSettingEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AppleJuiceNumberDescription(NumberEntityDescription):
    """Describes a numeric core setting."""

    tag: str
    # settings.xml speichert Raten in Byte/s, die GUIs zeigen KB/s.
    divisor: int = 1


NUMBERS: tuple[AppleJuiceNumberDescription, ...] = (
    AppleJuiceNumberDescription(
        key="maxupload",
        tag="maxupload",
        name="Max Upload",
        icon="mdi:upload",
        device_class=NumberDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBYTES_PER_SECOND,
        native_min_value=3,
        native_max_value=1048576,
        native_step=1,
        divisor=1024,
    ),
    AppleJuiceNumberDescription(
        key="maxdownload",
        tag="maxdownload",
        name="Max Download",
        icon="mdi:download",
        device_class=NumberDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBYTES_PER_SECOND,
        native_min_value=0,
        native_max_value=1048576,
        native_step=1,
        divisor=1024,
    ),
    AppleJuiceNumberDescription(
        key="speedperslot",
        tag="speedperslot",
        name="Speed per Slot",
        icon="mdi:speedometer",
        device_class=NumberDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBYTES_PER_SECOND,
        native_min_value=1,
        native_max_value=1024,
        native_step=1,
    ),
    AppleJuiceNumberDescription(
        key="maxconnections",
        tag="maxconnections",
        name="Max Connections",
        icon="mdi:lan-connect",
        native_min_value=30,
        native_max_value=100000,
        native_step=1,
    ),
    AppleJuiceNumberDescription(
        key="maxnewconnectionsperturn",
        tag="maxnewconnectionsperturn",
        name="Max New Connections per Turn",
        icon="mdi:lan-pending",
        native_min_value=1,
        native_max_value=200,
        native_step=1,
    ),
    AppleJuiceNumberDescription(
        key="maxsourcesperfile",
        tag="maxsourcesperfile",
        name="Max Sources per File",
        icon="mdi:source-branch",
        native_min_value=1,
        native_max_value=100000,
        native_step=1,
    ),
)


class AppleJuiceNumber(AppleJuiceSettingEntity, NumberEntity):
    """Numeric core setting."""

    entity_description: AppleJuiceNumberDescription
    _attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Current value."""
        raw = self._raw
        if raw is None:
            return None
        try:
            return int(raw) // self.entity_description.divisor
        except ValueError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set value."""
        await self._async_set(int(value) * self.entity_description.divisor)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AppleJuiceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up number platform."""
    async_add_entities(AppleJuiceNumber(entry.runtime_data, desc) for desc in NUMBERS)
