"""Text platform: string settings of the appleJuice Core."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.text import TextEntity, TextEntityDescription, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AppleJuiceConfigEntry
from .entity import AppleJuiceSettingEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AppleJuiceTextDescription(TextEntityDescription):
    """Describes a string core setting."""

    tag: str
    # settings.xml nutzt <nick>, setsettings erwartet nickname.
    param: str


TEXTS: tuple[AppleJuiceTextDescription, ...] = (
    AppleJuiceTextDescription(
        key="nickname",
        tag="nick",
        param="nickname",
        name="Nickname",
        icon="mdi:account",
        native_min=1,
        native_max=255,
        mode=TextMode.TEXT,
    ),
)


class AppleJuiceText(AppleJuiceSettingEntity, TextEntity):
    """String core setting."""

    entity_description: AppleJuiceTextDescription

    @property
    def native_value(self) -> str | None:
        """Current value."""
        return self._raw

    async def async_set_value(self, value: str) -> None:
        """Set value."""
        await self._async_set(value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AppleJuiceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up text platform."""
    async_add_entities(AppleJuiceText(entry.runtime_data, desc) for desc in TEXTS)
