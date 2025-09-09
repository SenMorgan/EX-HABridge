"""Select platform for EX-CommandStation direction control."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .const import DOMAIN, LOGGER
from .entity import EXCSRosterEntity
from .roster import EXCSLocoDirection, EXCSRosterEntry

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import LocoUpdateCoordinator
    from .excs_client import EXCSClient

from .excs_client import EXCSError

DIRECTION_FORWARD: Final[str] = str(EXCSLocoDirection.FORWARD)
DIRECTION_REVERSE: Final[str] = str(EXCSLocoDirection.REVERSE)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation select platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinators = data["coordinators"]

    # Add locomotive direction select entities
    entities = []
    for loco in client.roster_entries:
        coordinator = coordinators[loco.id]
        entities.append(LocoDirectionSelect(client, coordinator, loco))
    if entities:
        async_add_entities(entities)


class LocoDirectionSelect(EXCSRosterEntity, SelectEntity):
    """Representation of a locomotive direction control."""

    def __init__(
        self,
        client: EXCSClient,
        coordinator: LocoUpdateCoordinator,
        loco: EXCSRosterEntry,
    ) -> None:
        """Initialize the locomotive direction select entity."""
        super().__init__(client, coordinator, loco)
        self._attr_name = "Direction"

        # Set entity properties
        self.entity_description = SelectEntityDescription(
            key=f"direction_{loco.id}",
            icon="mdi:swap-horizontal-bold",
        )
        self._attr_unique_id = f"{client.entry_id}_direction_{loco.id}"

        # Define available options
        self._attr_options = [DIRECTION_FORWARD, DIRECTION_REVERSE]

    @property
    def current_option(self) -> str:
        """Return the current direction as a string."""
        return str(self._loco.direction)

    async def async_select_option(self, option: str) -> None:
        """Set the locomotive direction."""
        try:
            if option == DIRECTION_FORWARD:
                await self._client.send_command(
                    self._loco.set_direction_cmd(EXCSLocoDirection.FORWARD)
                )
            elif option == DIRECTION_REVERSE:
                await self._client.send_command(
                    self._loco.set_direction_cmd(EXCSLocoDirection.REVERSE)
                )
            else:
                LOGGER.error("Invalid direction option: %s", option)
        except EXCSError:
            # Handle the error if needed
            LOGGER.exception(
                "Failed to set direction %s for loco %d", option, self._loco.id
            )
