"""Sensor platform for EX-CommandStation speed and direction feedback."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE

from .const import DOMAIN, LOGGER
from .entity import EXCSRosterEntity
from .roster import EXCSLocoDirection, EXCSRosterEntry

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import LocoUpdateCoordinator
    from .excs_client import EXCSClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinators = data["coordinators"]
    entities = []

    # Add locomotive speed/direction sensor entities
    for loco in client.roster_entries:
        coordinator = coordinators[loco.id]
        entities.append(LocoSpeedSensor(client, coordinator, loco))
    if entities:
        async_add_entities(entities)


class LocoSpeedSensor(EXCSRosterEntity, SensorEntity):
    """Representation of a locomotive speed/direction sensor."""

    def __init__(
        self,
        client: EXCSClient,
        coordinator: LocoUpdateCoordinator,
        loco: EXCSRosterEntry,
    ) -> None:
        """Initialize the locomotive speed sensor entity."""
        super().__init__(client, coordinator, loco)
        self._attr_name = "Speed Status"

        # Set entity properties
        self.entity_description = SensorEntityDescription(
            key=f"speed_status_{loco.id}",
            icon="mdi:speedometer",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"

    @property
    def native_value(self) -> int:
        """Return the current speed as the state."""
        return round(self._loco.speed_pct)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the sensor."""
        return {
            "direction": str(self._loco.direction),
            "loco_id": self._loco.id,
            "description": self._loco.description,
        }
