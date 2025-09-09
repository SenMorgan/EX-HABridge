"""Number platform for EX-CommandStation speed control."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE

from .const import DOMAIN, LOGGER
from .entity import EXCSRosterEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import LocoUpdateCoordinator
    from .excs_client import EXCSClient
    from .roster import EXCSRosterEntry

from .excs_client import EXCSError


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation number platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinators = data["coordinators"]

    # Add locomotive speed number entities
    entities = []
    for loco in client.roster_entries:
        coordinator = coordinators[loco.id]
        entities.append(LocoSpeedNumber(client, coordinator, loco))
    if entities:
        async_add_entities(entities)


class LocoSpeedNumber(EXCSRosterEntity, NumberEntity):
    """Representation of a locomotive speed control."""

    def __init__(
        self,
        client: EXCSClient,
        coordinator: LocoUpdateCoordinator,
        loco: EXCSRosterEntry,
    ) -> None:
        """Initialize the locomotive speed number entity."""
        super().__init__(client, coordinator, loco)
        self._attr_name = "Speed"

        # Set entity properties
        self.entity_description = NumberEntityDescription(
            key=f"speed_{loco.id}",
            icon="mdi:speedometer",
            native_min_value=0,
            native_max_value=100,
            native_step=1,
            native_unit_of_measurement=PERCENTAGE,
            mode=NumberMode.AUTO,
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

    @property
    def native_value(self) -> float:
        """Return the current speed as a percentage."""
        return self._loco.speed_pct

    async def async_set_native_value(self, value: float) -> None:
        """Set the locomotive speed using percentage."""
        try:
            await self._client.send_command(self._loco.set_speed_pct_cmd(value))
        except EXCSError:
            # Handle the error if needed
            LOGGER.exception(
                "Failed to set speed to %.1f%% for loco %d", value, self._loco.id
            )
