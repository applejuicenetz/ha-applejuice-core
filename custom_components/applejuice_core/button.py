from dataclasses import dataclass
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, SHARECHECK_AFTER_CORE_VERSION
from .api import call_function, parse_version
from .entity import BaseAppleJuiceCoreEntity


@dataclass
class AppleJuiceCoreButtonDescription(ButtonEntityDescription):
    """Beschreibung für appleJuice Core Button-Entities."""
    key: str
    name: str
    sensor_name: str | None = None
    subscriptions: list | None = None
    icon: str | None = None
    device_class: str | None = None
    entity_category: str | None = None
    method: str | None = None
    after_core_version: str | None = None


class AppleJuiceCoreButton(BaseAppleJuiceCoreEntity, ButtonEntity):
    """aAppleJuiceCoreButton class."""

    def __init__(self, coordinator, entry, description):
        """Init."""
        super().__init__(coordinator, entry)
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self.entity_description = description
        self._attr_device_class = description.device_class
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category

    async def async_press(self):
        await call_function(
            self.coordinator.hass,
            self.config_entry.data.get("url"),
            self.config_entry.data.get("port"),
            self.config_entry.data.get("password"),
            self.config_entry.data.get("tls"),
            self.entity_description.method
        )


BUTTONS: tuple[AppleJuiceCoreButtonDescription, ...] = (
    AppleJuiceCoreButtonDescription(
        key="exitcore",
        name="Exit Core",
        icon="mdi:exit-run",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        method="exitcore",
    ),
    AppleJuiceCoreButtonDescription(
        key="sharecheck",
        name="Share Check",
        icon="mdi:folder-search",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        method="sharecheck",
        after_core_version=SHARECHECK_AFTER_CORE_VERSION,
    ),
    AppleJuiceCoreButtonDescription(
        key="cleandownloadlist",
        name="Clean Download List",
        icon="mdi:playlist-remove",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        method="cleandownloadlist",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set button platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_basic_sensor(coordinator, entry, async_add_entities)


async def async_setup_basic_sensor(coordinator, entry, async_add_entities):
    """Set button platform."""
    core_version = parse_version(coordinator.version)

    def supported(desc):
        if desc.after_core_version is None:
            return True
        # Nur anzeigen, wenn Core-Version strikt größer als after_core_version ist.
        return core_version is not None and core_version > parse_version(desc.after_core_version)

    async_add_entities([AppleJuiceCoreButton(coordinator, entry, desc) for desc in BUTTONS if supported(desc)])
