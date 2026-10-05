"""Config flow for the appleJuice Core integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util import network

from .api import AppleJuiceAuthError, AppleJuiceClient, AppleJuiceError
from .const import (
    CONF_OPTION_POLLING_RATE,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TLS,
    CONF_URL,
    DEFAULT_PORT,
    DEFAULT_POLLING_RATE,
    DOMAIN,
    MAX_POLLING_RATE,
    MIN_POLLING_RATE,
)
from .coordinator import AppleJuiceConfigEntry

_LOGGER = logging.getLogger(__name__)


def _schema(defaults: Mapping[str, Any], with_connection: bool = True) -> vol.Schema:
    """Form schema, prefilled with defaults."""
    fields: dict[Any, Any] = {}
    if with_connection:
        fields[vol.Required(CONF_URL, default=defaults.get(CONF_URL, ""))] = str
        fields[vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT))] = NumberSelector(
            NumberSelectorConfig(min=1, max=65535, step=1, mode=NumberSelectorMode.BOX)
        )
    fields[vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, ""))] = TextSelector(
        TextSelectorConfig(type=TextSelectorType.PASSWORD)
    )
    if with_connection:
        fields[vol.Optional(CONF_TLS, default=defaults.get(CONF_TLS, False))] = bool
    return vol.Schema(fields)


class AppleJuiceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for appleJuice Core."""

    VERSION = 1

    async def _validate(self, host: str, port: int, password: str, tls: bool) -> str | None:
        """Return an error key or None if the core answers."""
        if not network.is_host_valid(host):
            return "host_error"
        if not 1 <= port <= 65535:
            return "port_error"

        client = AppleJuiceClient(async_get_clientsession(self.hass), host, port, password, tls)
        try:
            info = await client.get_xml("/xml/information.xml")
        except AppleJuiceAuthError:
            return "invalid_auth"
        except AppleJuiceError:
            return "core_connection_error"
        if info.find("generalinformation") is None:
            return "core_connection_error"
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = {**user_input, CONF_PORT: int(user_input[CONF_PORT])}
            error = await self._validate(
                user_input[CONF_URL],
                user_input[CONF_PORT],
                user_input[CONF_PASSWORD],
                user_input.get(CONF_TLS, False),
            )
            if error is None:
                await self.async_set_unique_id(f"{user_input[CONF_URL]}:{user_input[CONF_PORT]}".lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{user_input[CONF_URL]}:{user_input[CONF_PORT]}", data=user_input
                )
            errors[{"host_error": CONF_URL, "port_error": CONF_PORT}.get(error, "base")] = error

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Start reauthentication after the core rejected the password."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for a new password."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            error = await self._validate(
                entry.data[CONF_URL],
                entry.data[CONF_PORT],
                user_input[CONF_PASSWORD],
                entry.data.get(CONF_TLS, False),
            )
            if error is None:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_schema({}, with_connection=False),
            description_placeholders={"host": entry.data[CONF_URL]},
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change host, port, password or TLS of an existing entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = {**user_input, CONF_PORT: int(user_input[CONF_PORT])}
            error = await self._validate(
                user_input[CONF_URL],
                user_input[CONF_PORT],
                user_input[CONF_PASSWORD],
                user_input.get(CONF_TLS, False),
            )
            if error is None:
                await self.async_set_unique_id(f"{user_input[CONF_URL]}:{user_input[CONF_PORT]}".lower())
                self._abort_if_unique_id_mismatch(reason="wrong_core")
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
            errors["base"] = error

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(user_input or entry.data),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: AppleJuiceConfigEntry) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlowWithReload):
    """Handle options; the entry reloads automatically after saving."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_OPTION_POLLING_RATE: int(user_input[CONF_OPTION_POLLING_RATE])}
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_OPTION_POLLING_RATE,
                        default=self.config_entry.options.get(CONF_OPTION_POLLING_RATE, DEFAULT_POLLING_RATE),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_POLLING_RATE,
                            max=MAX_POLLING_RATE,
                            step=1,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
