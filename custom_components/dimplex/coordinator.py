"""DataUpdateCoordinator for Dimplex integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import DimplexApiClient, DimplexApiError, DimplexAuthError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DimplexCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Dimplex data updates."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: DimplexApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.config_entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            data = await self.client.read_variables()
            _LOGGER.debug("Received data: %s", data)
            
            # Check if tokens have been refreshed and update config entry
            if (
                self.client.refresh_token
                != self.config_entry.data.get("refresh_token")
            ):
                _LOGGER.debug("Updating stored refresh token")
                new_data = {
                    **self.config_entry.data,
                    "refresh_token": self.client.refresh_token,
                    "access_token": self.client.access_token,
                }
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )

            return data

        except DimplexAuthError as err:
            _LOGGER.error("Authentication error: %s", err)
            raise UpdateFailed(f"Authentication error: {err}") from err
        except DimplexApiError as err:
            _LOGGER.error("API error: %s", err)
            raise UpdateFailed(f"API error: {err}") from err

    def get_value(
        self,
        variable_id: str,
        scale: float = 1.0,
        default: Any = None,
    ) -> Any:
        """Get a value from the coordinator data."""
        if self.data is None:
            return default

        try:
            raw_value = self.data.get(variable_id, {}).get("value")
            if raw_value is None:
                return default
            
            if scale != 1.0:
                return float(raw_value) * scale
            return raw_value
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.debug(
                "Error getting value for %s: %s",
                variable_id,
                err,
            )
            return default

    def get_combined_value(
        self,
        low_variable_id: str,
        high_variable_id: str,
        scale: float = 1.0,
        default: Any = None,
    ) -> Any:
        """Return a counter split across a low word (0-9999) and a high word.

        Some energy/heat meters store the value across two registers: a low
        word counting 0-9999 and a separate high word counting the x10000
        steps. The real value is ``high * 10000 + low``. A missing high word is
        treated as 0, so it stays correct for counters still below 10000.
        """
        low = self.get_value(low_variable_id)
        if low is None:
            return default

        high = self.get_value(high_variable_id) or 0
        try:
            combined = int(high) * 10000 + int(low)
        except (TypeError, ValueError) as err:
            _LOGGER.debug(
                "Error combining values for %s/%s: %s",
                low_variable_id,
                high_variable_id,
                err,
            )
            return default

        if scale != 1.0:
            return combined * scale
        return combined

    def get_mapped_value(
        self,
        variable_id: str,
        mapping: dict[str, str],
        default: str = "Unknown",
    ) -> str:
        """Get a mapped value from the coordinator data."""
        raw_value = self.get_value(variable_id)
        if raw_value is None:
            return default
        return mapping.get(str(raw_value), str(raw_value))
