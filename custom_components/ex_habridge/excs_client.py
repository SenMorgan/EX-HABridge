"""EX-CommandStation Client for Home Assistant integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .commands import command_write_cv
from .const import LOGGER
from .excs_config import EXCSConfigClient
from .excs_exceptions import EXCSError, EXCSValueError

if TYPE_CHECKING:
    from homeassistant.core import ServiceCall


class EXCSClient(EXCSConfigClient):
    """Client for communicating with the EX-CommandStation."""

    async def async_validate_config(self) -> None:
        """Validate the configuration of the EX-CommandStation client."""
        if not self.connected:
            await self.connect()

        # Validate system info
        LOGGER.debug("Validating EX-CommandStation client configuration")
        await self.get_excs_system_info()
        await self.validate_excs_version()

    async def async_setup(self) -> None:
        """Set up the EX-CommandStation client."""
        if not self.connected:
            await self.connect()

        # Fetch EX-CommandStation system info and validate version
        LOGGER.debug("Configuring EX-CommandStation client")
        await self.get_excs_system_info()
        await self.validate_excs_version()
        # Fetch the list of roster entries
        await self.get_roster_entries()
        # Fetch the list of routes
        await self.get_routes()
        # Fetch the list of turnouts
        await self.get_turnouts()

    async def async_shutdown(self) -> None:
        """Shutdown the EX-CommandStation client."""
        LOGGER.debug("Shutting down EX-CommandStation client")
        try:
            await self.disconnect()
        except EXCSError:
            LOGGER.exception("Error during shutdown of EX-CommandStation client")

    async def handle_write_cv(self, call: ServiceCall) -> None:
        """Handle the write CV service call."""
        try:
            address = int(call.data["address"])
            cv = int(call.data["cv"])
            value = int(call.data["value"])
            command = command_write_cv(address, cv, value)
            LOGGER.debug("Writing CV: address=%d, cv=%d, value=%d", address, cv, value)
            await self.send_command(command)
        except ValueError as err:
            msg = "Invalid CV write parameters: %s", err
            LOGGER.error(msg)
            raise EXCSValueError(msg) from err
        except EXCSError as err:
            LOGGER.error("Error writing CV: %s", err)
            raise
