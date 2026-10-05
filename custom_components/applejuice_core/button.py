"""Button platform for the appleJuice Core integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import AppleJuiceError, parse_version
from .const import DOMAIN, SHARECHECK_AFTER_CORE_VERSION
from .coordinator import AppleJuiceConfigEntry
from .entity import AppleJuiceCoreEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AppleJuiceButtonDescription(ButtonEntityDescription):
    """Describes a core function button."""

    method: str
    after_core_version: str | None = None


BUTTONS: tuple[AppleJuiceButtonDescription, ...] = (
    AppleJuiceButtonDescription(
        key="exitcore",
        name="Exit Core",
        icon="mdi:exit-run",
        entity_category=EntityCategory.CONFIG,
        method="exitcore",
    ),
    AppleJuiceButtonDescription(
        key="sharecheck",
        name="Share Check",
        icon="mdi:folder-search",
        entity_category=EntityCategory.CONFIG,
        method="sharecheck",
        after_core_version=SHARECHECK_AFTER_CORE_VERSION,
    ),
    AppleJuiceButtonDescription(
        key="cleandownloadlist",
        name="Clean Download List",
        icon="mdi:playlist-remove",
        entity_category=EntityCategory.CONFIG,
        method="cleandownloadlist",
    ),
)


class AppleJuiceButton(AppleJuiceCoreEntity, ButtonEntity):
    """Button calling a core function."""

    entity_description: AppleJuiceButtonDescription

    async def async_press(self) -> None:
        """Call the function on the core."""
        try:
            await self.coordinator.client.call_function(self.entity_description.method)
        except AppleJuiceError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="function_failed",
                translation_placeholders={"function": self.entity_description.method},
            ) from err


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AppleJuiceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up button platform."""
    coordinator = entry.runtime_data
    core_version = parse_version(coordinator.version)

    def supported(desc: AppleJuiceButtonDescription) -> bool:
        if desc.after_core_version is None:
            return True
        # Nur anzeigen, wenn Core-Version strikt größer als after_core_version ist.
        return core_version is not None and core_version > parse_version(desc.after_core_version)

    async_add_entities(AppleJuiceButton(coordinator, desc) for desc in BUTTONS if supported(desc))
