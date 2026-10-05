"""Switch platform: boolean settings of the appleJuice Core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AppleJuiceConfigEntry
from .entity import AppleJuiceSettingEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AppleJuiceSwitchDescription(SwitchEntityDescription):
    """Describes a boolean core setting."""

    tag: str


SWITCHES: tuple[AppleJuiceSwitchDescription, ...] = (
    AppleJuiceSwitchDescription(
        key="autoconnect",
        tag="autoconnect",
        name="Auto Connect",
        icon="mdi:connection",
    ),
)


class AppleJuiceSwitch(AppleJuiceSettingEntity, SwitchEntity):
    """Boolean core setting."""

    entity_description: AppleJuiceSwitchDescription

    @property
    def is_on(self) -> bool | None:
        """Current state."""
        raw = self._raw
        return None if raw is None else raw.strip().lower() == "true"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on."""
        await self._async_set("true")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off."""
        await self._async_set("false")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AppleJuiceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switch platform."""
    async_add_entities(AppleJuiceSwitch(entry.runtime_data, desc) for desc in SWITCHES)
