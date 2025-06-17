"""Button platform for EX-CommandStation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .commands import EMERGENCY_STOP, REBOOT
from .const import DOMAIN, LOGGER
from .entity import EXCSEntity
from .excs_client import EXCSError
from .route import EXCSRoute, EXCSRouteConsts, EXCSRouteType

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .excs_client import EXCSClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation button platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]

    # Create core buttons
    entities = [
        EXCSRebootButton(client),
        EXCSEmergencyStopButton(client),
    ]

    # Add route/automation buttons
    if client.routes:
        routes_buttons = [RouteButton(client, route) for route in client.routes]
        entities.extend(routes_buttons)

    async_add_entities(entities)


class EXCSButtonEntity(EXCSEntity, ButtonEntity):
    """Base class for EX-CommandStation button entities."""


class EXCSRebootButton(EXCSButtonEntity, ButtonEntity):
    """Representation of the EX-CommandStation reboot button."""

    def __init__(self, client: EXCSClient) -> None:
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

    def __init__(self, client: EXCSClient) -> None:
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


class RouteButton(EXCSButtonEntity, ButtonEntity):
    """Representation of a route or automation button in the EX-CommandStation."""

    def __init__(self, client: EXCSClient, route: EXCSRoute) -> None:
        """Initialize the route button."""
        super().__init__(client)
        self._route = route

        # Set entity properties
        self._attr_name = route.description
        self.entity_description = ButtonEntityDescription(
            key=f"route_{route.id}",
            icon="mdi:play-circle-outline"
            if route.type == EXCSRouteType.ROUTE
            else "mdi:robot",
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

    async def async_press(self) -> None:
        """Send the start command for the route/automation."""
        try:
            await self._client.send_command(
                EXCSRouteConsts.CMD_START_ROUTE_FMT.format(id=self._route.id)
            )
        except EXCSError:
            LOGGER.exception("Failed to start route %s", self._route.id)
