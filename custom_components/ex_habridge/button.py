"""Button platform for EX-CommandStation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .commands import EMERGENCY_STOP, REBOOT
from .const import DOMAIN, LOGGER
from .entity import EXCSEntity
from .excs_client import EXCSError

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .excs_client import EXCommandStationClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation switch platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]

    # Create buttons
    async_add_entities(
        [
            EXCSRebootButton(client),
            EXCSEmergencyStopButton(client),
        ]
    )


class EXCSButtonEntity(EXCSEntity, ButtonEntity):
    """Base class for EX-CommandStation button entities."""


class EXCSRebootButton(EXCSButtonEntity, ButtonEntity):
    """Representation of the EX-CommandStation reboot button."""

    def __init__(self, client: EXCommandStationClient) -> None:
        """Initialize the button."""
        super().__init__(client)

        # Set entity properties
        self._attr_name = "Reboot"
        self.entity_description = ButtonEntityDescription(
            key="reboot",
            icon="mdi:restart",
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

    async def async_press(self) -> None:
        """Send the reboot command to the EX-CommandStation."""
        try:
            await self._client.send_command(REBOOT)
        except EXCSError:
            LOGGER.exception("Failed to reboot EX-CommandStation")


class EXCSEmergencyStopButton(EXCSButtonEntity, ButtonEntity):
    """Representation of the EX-CommandStation emergency stop button."""

    def __init__(self, client: EXCommandStationClient) -> None:
        """Initialize the button."""
        super().__init__(client)

        # Set entity properties
        self._attr_name = "Emergency Stop"
        self.entity_description = ButtonEntityDescription(
            key="emergency_stop",
            icon="mdi:car-brake-alert",
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

    async def async_press(self) -> None:
        """Send the emergency stop command to the EX-CommandStation."""
        try:
            await self._client.send_command(EMERGENCY_STOP)
        except EXCSError:
            LOGGER.exception("Failed to send emergency stop command")
