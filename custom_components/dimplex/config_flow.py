"""Config flow for Dimplex integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    DimplexApiClient,
    validate_credentials,
    login_with_credentials,
    get_devices,
    DimplexAuthError,
    DimplexApiError,
    DimplexLoginError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Regex to extract device ID from various formats (supports sn-*-mac-* pattern)
DEVICE_ID_PATTERN = re.compile(r"(sn-[^-]+-mac-[A-F0-9-]+)", re.IGNORECASE)


def extract_device_id(user_input: str) -> str | None:
    """Extract device ID from user input (URL or direct ID)."""
    user_input = user_input.strip()

    # Check if it's already in the correct sn-*-mac-* format
    if re.match(r"^sn-[^-]+-mac-[A-F0-9-]+$", user_input, re.IGNORECASE):
        return user_input

    # Try to find it in a URL or other string
    match = DEVICE_ID_PATTERN.search(user_input)
    if match:
        return match.group(1)

    return None


class DimplexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dimplex."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._devices: dict[str, dict] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - choose auth method."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["credentials", "token"],
            description_placeholders={},
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle login with username and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Login with username/password
                access_token, refresh_token = await login_with_credentials(
                    user_input["username"],
                    user_input["password"],
                )

                self._access_token = access_token
                self._refresh_token = refresh_token

                # Fetch available devices
                try:
                    self._devices = await get_devices(access_token)
                    _LOGGER.debug("Found %d devices", len(self._devices))
                except DimplexApiError as err:
                    _LOGGER.warning("Could not fetch devices: %s", err)
                    self._devices = None

                # Proceed to device selection step
                return await self.async_step_device()

            except DimplexLoginError as err:
                _LOGGER.error("Login failed: %s", err)
                if "Invalid credentials" in str(err) or "password" in str(err).lower():
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during login")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual token entry (fallback method)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Extract and validate device ID
            device_id = extract_device_id(user_input["device_id"])
            if device_id is None:
                errors["device_id"] = "invalid_device_id"
            else:
                # Validate refresh token
                try:
                    session = async_get_clientsession(self.hass)
                    access_token, refresh_token = await validate_credentials(
                        user_input["refresh_token"],
                        session,
                    )

                    # Test connection with the device
                    client = DimplexApiClient(
                        device_id=device_id,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        session=session,
                    )

                    if not await client.test_connection():
                        errors["base"] = "cannot_connect"
                    else:
                        # Create unique ID based on device ID
                        await self.async_set_unique_id(device_id)
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"Dimplex {device_id[-8:]}",
                            data={
                                "device_id": device_id,
                                "access_token": access_token,
                                "refresh_token": refresh_token,
                            },
                        )

                except DimplexAuthError:
                    errors["refresh_token"] = "invalid_auth"
                except aiohttp.ClientError:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="token",
            data_schema=vol.Schema(
                {
                    vol.Required("device_id"): str,
                    vol.Required("refresh_token"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "device_id_hint": "z.B. sn-UHI-mac-B8-27-FA-63-38-4A",
            },
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection after successful login."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Get device ID from dropdown or manual input
            device_id = user_input.get("device_id") or user_input.get("device_id_manual")

            if device_id:
                # If manual input, try to extract proper format
                if not re.match(r"^sn-[^-]+-mac-[A-F0-9-]+$", device_id, re.IGNORECASE):
                    device_id = extract_device_id(device_id)

                if device_id is None:
                    errors["device_id_manual"] = "invalid_device_id"
                else:
                    # Get display name for the title
                    title = f"Dimplex {device_id[-8:]}"
                    if self._devices and device_id in self._devices:
                        dev_info = self._devices[device_id]
                        title = f"{dev_info['display_name']} ({dev_info['type_name']})"

                    # Create unique ID based on device ID
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=title,
                        data={
                            "device_id": device_id,
                            "access_token": self._access_token,
                            "refresh_token": self._refresh_token,
                        },
                    )
            else:
                errors["base"] = "no_device_selected"

        # Build the form schema based on available devices
        if self._devices and len(self._devices) > 0:
            # Create dropdown with device options
            device_options = {
                device_id: f"{info['display_name']} ({info['type_name']}) - {info['connection_status']}"
                for device_id, info in self._devices.items()
            }

            data_schema = vol.Schema(
                {
                    vol.Required("device_id"): vol.In(device_options),
                }
            )
        else:
            # No devices found, fall back to manual input
            data_schema = vol.Schema(
                {
                    vol.Required("device_id_manual"): str,
                }
            )

        return self.async_show_form(
            step_id="device",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle reauthorization."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauthorization - choose method."""
        return self.async_show_menu(
            step_id="reauth_confirm",
            menu_options=["reauth_credentials", "reauth_token"],
        )

    async def async_step_reauth_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauth with username/password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                access_token, refresh_token = await login_with_credentials(
                    user_input["username"],
                    user_input["password"],
                )

                # Update the config entry
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            **entry.data,
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                        },
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

            except DimplexLoginError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_credentials",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauth with manual token entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                access_token, refresh_token = await validate_credentials(
                    user_input["refresh_token"],
                    session,
                )

                # Update the config entry
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            **entry.data,
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                        },
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

            except DimplexAuthError:
                errors["refresh_token"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_token",
            data_schema=vol.Schema(
                {
                    vol.Required("refresh_token"): str,
                }
            ),
            errors=errors,
        )
