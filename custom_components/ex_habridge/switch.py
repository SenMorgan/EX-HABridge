"""Switch platform for EX-CommandStation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import callback

from .const import DOMAIN, LOGGER, SIGNAL_DATA_PUSHED
from .entity import EXCSEntity, EXCSRosterEntity
from .icons_helper import get_function_icon
from .roster import LocoFunction, LocoFunctionCmd, RosterEntry
from .turnout import EXCSTurnout, TurnoutState

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import LocoUpdateCoordinator
    from .excs_client import EXCSClient


from .commands import (
    CMD_TRACKS_OFF,
    CMD_TRACKS_ON,
    RESP_TRACKS_OFF,
    RESP_TRACKS_ON,
)
from .excs_client import EXCSError


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation switch platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinators = data["coordinators"]

    # Add tracks power switch
    async_add_entities([TracksPowerSwitch(client)])

    # Add turnout switches
    if client.turnouts:
        turnout_switches = [
            TurnoutSwitch(client, turnout) for turnout in client.turnouts
        ]
        async_add_entities(turnout_switches)

    # Add locomotive function switches
    function_switches = []
    for loco in client.roster_entries:
        coordinator = coordinators[loco.id]
        function_switches.extend(
            [
                LocoFunctionSwitch(client, coordinator, loco, function)
                for function in loco.functions.values()
            ]
        )

    if function_switches:
        async_add_entities(function_switches)


class EXCSSwitchEntity(EXCSEntity, SwitchEntity):
    """Base class for EX-CommandStation switch entities."""

    @callback
    def _handle_push(self, message: str) -> None:
        """Abstract method to handle incoming messages from the EX-CommandStation."""
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        """Register data push callbacks."""
        await super().async_added_to_hass()
        self._unsub_callbacks.append(
            self._client.register_signal_handler(SIGNAL_DATA_PUSHED, self._handle_push)
        )


class TracksPowerSwitch(EXCSSwitchEntity, SwitchEntity):
    """Representation of the EX-CommandStation tracks power switch."""

    def __init__(self, client: EXCSClient) -> None:
        """Initialize the switch."""
        super().__init__(client)

        # Set entity properties
        self._attr_name = "Tracks Power"
        self.entity_description = SwitchEntityDescription(
            key="tracks_power",
            icon="mdi:power",
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

        # Set initial state based on the client's initial tracks state
        self._attr_is_on = client.initial_tracks_state

    @callback
    def _handle_push(self, message: str) -> None:
        """Handle incoming messages from the EX-CommandStation."""
        if message == RESP_TRACKS_ON:
            LOGGER.debug("Tracks power ON")
            self._attr_is_on = True
            self.async_write_ha_state()
        elif message == RESP_TRACKS_OFF:
            LOGGER.debug("Tracks power OFF")
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        try:
            await self._client.send_command(CMD_TRACKS_ON)
        except EXCSError:
            LOGGER.exception("Failed to turn ON tracks power")

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        try:
            await self._client.send_command(CMD_TRACKS_OFF)
        except EXCSError:
            # Handle the error if needed
            LOGGER.exception("Failed to turn OFF tracks power")


class TurnoutSwitch(EXCSSwitchEntity, SwitchEntity):
    """Representation of a turnout switch."""

    def __init__(self, client: EXCSClient, turnout: EXCSTurnout) -> None:
        """Initialize the switch."""
        super().__init__(client)
        self._turnout = turnout

        # Set entity properties
        self._attr_name = turnout.description
        self.entity_description = SwitchEntityDescription(
            key=f"turnout_{turnout.id}",
            icon="mdi:source-branch",
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

        # Assuming THROWN means the switch is on
        self._attr_is_on = turnout.state == TurnoutState.THROWN

    @callback
    def _handle_push(self, message: str) -> None:
        """Handle incoming messages from the EX-CommandStation."""
        if message.startswith(self._turnout.recv_prefix):
            turnout_id, state = EXCSTurnout.parse_turnout_state(message)
            if turnout_id == self._turnout.id:  # Double-check the turnout ID
                LOGGER.debug("Turnout %d %s", turnout_id, state.name)
                # Update the state of the switch
                self._attr_is_on = state == TurnoutState.THROWN
                self.async_write_ha_state()

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch (set turnout to THROWN)."""
        try:
            await self._client.send_command(
                EXCSTurnout.toggle_turnout_cmd(self._turnout.id, TurnoutState.THROWN)
            )
        except EXCSError:
            # Handle the error if needed
            LOGGER.exception("Failed to turn THROW turnout %d", self._turnout.id)

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch (set turnout to CLOSED)."""
        try:
            await self._client.send_command(
                EXCSTurnout.toggle_turnout_cmd(self._turnout.id, TurnoutState.CLOSED)
            )
        except EXCSError:
            # Handle the error if needed
            LOGGER.exception("Failed to turn CLOSE turnout %d", self._turnout.id)


class LocoFunctionSwitch(EXCSRosterEntity, SwitchEntity):
    """Representation of a locomotive function switch."""

    def __init__(
        self,
        client: EXCSClient,
        coordinator: LocoUpdateCoordinator,
        loco: RosterEntry,
        function: LocoFunction,
    ) -> None:
        """Initialize the switch."""
        super().__init__(client, coordinator, loco)
        self._function_id = function.id

        # Set entity properties
        self._attr_name = function.label
        self.entity_description = SwitchEntityDescription(
            key=f"function_{loco.id}_{function.id}",
            icon=get_function_icon(function.label),  # Set icon based on function label
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

        # Set initial state based on function state
        self._attr_is_on = function.state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data is not None:
            function = self.coordinator.data.functions.get(self._function_id)
            self._attr_is_on = function.state if function else None
        else:
            self._attr_is_on = None
        self.async_write_ha_state()

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the function."""
        try:
            await self._client.send_command(
                self._loco.toggle_function_cmd(self._function_id, LocoFunctionCmd.ON)
            )
        except EXCSError:
            # Handle the error if needed
            LOGGER.exception(
                "Failed to turn ON function %d for loco %d",
                self._function_id,
                self._loco.id,
            )

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the function."""
        try:
            await self._client.send_command(
                self._loco.toggle_function_cmd(self._function_id, LocoFunctionCmd.OFF)
            )
        except EXCSError:
            # Handle the error if needed
            LOGGER.exception(
                "Failed to turn OFF function %d for loco %d",
                self._function_id,
                self._loco.id,
            )
