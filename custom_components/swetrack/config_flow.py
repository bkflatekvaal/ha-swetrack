"""Config flow for SweTrack."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import SweTrackApiClient, SweTrackApiError, SweTrackAuthError
from .const import (
    API_BASE_URL,
    CONF_ACCOUNT_ID,
    CONF_ACCOUNT_LANGUAGE,
    CONF_ACCOUNT_NAME,
    CONF_API_KEY,
    CONF_ENABLED_DEVICES,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_MODE,
    DEFAULT_MANUAL_INTERVAL,
    DEFAULT_UPDATE_MODE,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    UPDATE_MODE_AUTO,
    UPDATE_MODE_MANUAL,
)
from .models import derive_account_identity, extract_device_list, normalize_device


class SweTrackConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a SweTrack config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            client = SweTrackApiClient(
                async_get_clientsession(self.hass), api_key, API_BASE_URL
            )
            try:
                account = await client.async_get_account()
                await client.async_get_devices()
            except SweTrackAuthError:
                errors["base"] = "invalid_auth"
            except SweTrackApiError:
                errors["base"] = "cannot_connect"
            else:
                account_id, account_name, account_language = derive_account_identity(
                    account.data, api_key
                )
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=account_name,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_ACCOUNT_ID: account_id,
                        CONF_ACCOUNT_NAME: account_name,
                        CONF_ACCOUNT_LANGUAGE: account_language,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Start reauthentication after an authentication failure."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Validate and save replacement credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            client = SweTrackApiClient(
                async_get_clientsession(self.hass), api_key, API_BASE_URL
            )

            try:
                account = await client.async_get_account()
                await client.async_get_devices()
            except SweTrackAuthError:
                errors["base"] = "invalid_auth"
            except SweTrackApiError:
                errors["base"] = "cannot_connect"
            else:
                account_id, account_name, account_language = derive_account_identity(
                    account.data, api_key
                )

                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_mismatch(reason="wrong_account")

                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_API_KEY: api_key,
                        CONF_ACCOUNT_ID: account_id,
                        CONF_ACCOUNT_NAME: account_name,
                        CONF_ACCOUNT_LANGUAGE: account_language,
                    },
                    title=account_name,
                )

        reauth_entry = self._get_reauth_entry()
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
            description_placeholders={"account": reauth_entry.title},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return SweTrackOptionsFlow()


class SweTrackOptionsFlow(config_entries.OptionsFlow):
    """Configure devices and polling."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        coordinator = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)

        device_options: list[dict[str, str]] = []
        all_ids: list[str] = []
        if coordinator is not None:
            for device_id, device in coordinator.data.items():
                all_ids.append(device_id)
                device_options.append({"value": device_id, "label": device.name})

        current_enabled = self.config_entry.options.get(
            CONF_ENABLED_DEVICES, all_ids
        )

        if user_input is not None:
            mode = user_input[CONF_UPDATE_MODE]
            interval = int(
                user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_MANUAL_INTERVAL)
            )
            return self.async_create_entry(
                title="",
                data={
                    CONF_UPDATE_MODE: mode,
                    CONF_UPDATE_INTERVAL: interval,
                    CONF_ENABLED_DEVICES: user_input.get(
                        CONF_ENABLED_DEVICES, all_ids
                    ),
                },
            )

        schema: dict[Any, Any] = {
            vol.Required(
                CONF_UPDATE_MODE,
                default=self.config_entry.options.get(
                    CONF_UPDATE_MODE, DEFAULT_UPDATE_MODE
                ),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": UPDATE_MODE_AUTO, "label": "Automatic"},
                        {"value": UPDATE_MODE_MANUAL, "label": "Fixed interval"},
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_UPDATE_INTERVAL, DEFAULT_MANUAL_INTERVAL
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_UPDATE_INTERVAL,
                    max=MAX_UPDATE_INTERVAL,
                    step=10,
                    unit_of_measurement="s",
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }

        if device_options:
            schema[
                vol.Optional(CONF_ENABLED_DEVICES, default=current_enabled)
            ] = SelectSelector(
                SelectSelectorConfig(
                    options=device_options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
        )
