"""EX-CommandStation Client with configuration and data retrieval capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .commands import (
    CMD_EXCS_SYS_INFO,
    RESP_EXCS_SYS_INFO_PREFIX,
    RESP_EXCS_SYS_INFO_REGEX,
    RESP_TRACKS_OFF,
    RESP_TRACKS_ON,
)
from .const import LOGGER, MIN_SUPPORTED_VERSION, SIGNAL_DATA_PUSHED
from .excs_base import EXCSBaseClient
from .excs_exceptions import (
    EXCSConnectionError,
    EXCSError,
    EXCSInvalidResponseError,
    EXCSVersionError,
)
from .roster_manager import EXCSRosterManager
from .routes_manager import EXCSRoutesManager
from .turnouts_manager import EXCSTurnoutsManager

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from route import EXCSRoute

    from .roster import EXCSRosterEntry
    from .turnout import EXCSTurnout


@dataclass
class EXCSSystemInfo:
    """
    Data class to hold system information of the EX-CommandStation.

    See: https://dcc-ex.com/reference/software/command-summary-consolidated.html#s-request-the-dcc-ex-version-and-hardware-info-along-with-listing-defined-turnouts
    """

    version: str = ""
    processor_type: str = ""
    motor_controller: str = ""
    build_number: str = ""
    version_parsed: tuple[int, ...] = field(default_factory=tuple)


class EXCSConfigClient(EXCSBaseClient):
    """EX-CommandStation Client with configuration and data retrieval capabilities."""

    def __init__(
        self, hass: HomeAssistant, host: str, port: int, entry_id: str = ""
    ) -> None:
        """Initialize the configuration client."""
        super().__init__(hass, host, port, entry_id)
        self.system_info = EXCSSystemInfo()
        self.roster_manager = EXCSRosterManager(self)
        self.routes_manager = EXCSRoutesManager(self)
        self.turnouts_manager = EXCSTurnoutsManager(self)
        self.initial_tracks_state: bool = False

    @property
    def roster_entries(self) -> list[EXCSRosterEntry]:
        """Return the list of roster entries."""
        return self.roster_manager.entries

    @property
    def routes(self) -> list[EXCSRoute]:
        """Return the list of routes."""
        return self.routes_manager.routes

    @property
    def turnouts(self) -> list[EXCSTurnout]:
        """Return the list of turnouts."""
        return self.turnouts_manager.turnouts

    @classmethod
    def parse_version(cls, version_str: str) -> tuple[int, ...]:
        """Parse a version string into a tuple of integers."""
        return tuple(int(part) for part in version_str.split("."))

    async def get_roster_entries(self) -> None:
        """Request the list of roster entries from the EX-CommandStation."""
        await self.roster_manager.get_roster_entries()

    async def get_routes(self) -> None:
        """Request the list of routes from the EX-CommandStation."""
        await self.routes_manager.get_routes()

    async def get_turnouts(self) -> None:
        """Request the list of turnouts from the EX-CommandStation."""
        await self.turnouts_manager.get_turnouts()

    async def _create_initial_tracks_state_handler(self) -> None:
        """Create a one-time signal handler for the initial tracks state."""
        unsub_callback: Callable[..., Any]

        def one_time_track_state_handler(message: str) -> None:
            """Handle the initial tracks state message."""
            nonlocal unsub_callback

            if message == RESP_TRACKS_ON:
                LOGGER.debug("Initial tracks state: ON")
                self.initial_tracks_state = True
                unsub_callback()
            elif message == RESP_TRACKS_OFF:
                LOGGER.debug("Initial tracks state: OFF")
                self.initial_tracks_state = False
                unsub_callback()

        # Register a one-time signal handler for the initial track state
        unsub_callback = self.register_signal_handler(
            SIGNAL_DATA_PUSHED, one_time_track_state_handler
        )
        self.register_signal_handler(SIGNAL_DATA_PUSHED, one_time_track_state_handler)

    async def get_excs_system_info(self) -> None:
        """Request system information from the EX-CommandStation."""
        if not self.connected:
            msg = "Not connected to EX-CommandStation"
            raise EXCSConnectionError(msg)

        # Create a one-time signal handler for the initial tracks state
        await self._create_initial_tracks_state_handler()

        LOGGER.debug("Requesting EX-CommandStation system info")
        try:
            response = await self.await_command_response(
                CMD_EXCS_SYS_INFO, RESP_EXCS_SYS_INFO_PREFIX
            )
        except TimeoutError as err:
            msg = "Timeout waiting for system info response from EX-CommandStation"
            LOGGER.error(msg)
            raise EXCSConnectionError(msg) from err
        except EXCSError:
            LOGGER.exception("Error while getting system info: %s")
            raise
        except Exception:
            LOGGER.exception("Unexpected error while getting system info")
            raise

        # Parse the response and extract system information
        if match := RESP_EXCS_SYS_INFO_REGEX.match(response):
            self.system_info.version = match.group("version")
            self.system_info.version_parsed = self.parse_version(match.group("version"))
            self.system_info.processor_type = match.group("microprocessor")
            self.system_info.motor_controller = match.group("motor_controller")
            self.system_info.build_number = match.group("build_number") or "unknown"

            LOGGER.info(
                "EX-CommandStation version: %s, processor: %s, motor controller: %s",
                self.system_info.version,
                self.system_info.processor_type,
                self.system_info.motor_controller,
            )
        else:
            msg = f"Invalid response from EX-CommandStation on system info: {response}"
            LOGGER.error(msg)
            raise EXCSInvalidResponseError(msg)

    async def validate_excs_version(self) -> None:
        """Check the version of the EX-CommandStation."""
        # Check if the version is parsed
        if not self.system_info.version_parsed:
            msg = "EX-CommandStation version has not been retrieved yet"
            LOGGER.error(msg)
            raise EXCSVersionError(msg)

        # Check if the version is supported
        if self.system_info.version_parsed < MIN_SUPPORTED_VERSION:
            min_ver_str = ".".join(str(x) for x in MIN_SUPPORTED_VERSION)
            msg = (
                f"Unsupported EX-CommandStation version: {self.system_info.version}. "
                f"Min supported: {min_ver_str}"
            )
            LOGGER.error(msg)
            raise EXCSVersionError(msg)
