"""Binary sensor platform for EX-CommandStation DCC sensors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback

from .const import DOMAIN, LOGGER, SIGNAL_DATA_PUSHED
from .entity import EXCSEntity
from .excs_exceptions import EXCSError
from .sensor_dcc import EXCSSensor

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .excs_client import EXCSClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation binary sensor platform."""
    client: EXCSClient = hass.data[DOMAIN][entry.entry_id]["client"]
    if client.sensors:
        async_add_entities(
            DccSensorBinaryEntity(client, sensor) for sensor in client.sensors
        )


class DccSensorBinaryEntity(EXCSEntity, BinarySensorEntity):
    """Binary sensor entity representing a DCC input sensor."""

    def __init__(self, client: EXCSClient, sensor: EXCSSensor) -> None:
        """Initialize the DCC sensor entity."""
        super().__init__(client)
        self._sensor = sensor
        self.entity_description = BinarySensorEntityDescription(
            key=f"sensor_{sensor.id}",
            device_class=BinarySensorDeviceClass.OCCUPANCY,
        )
        self._attr_name = sensor.description
        self._attr_unique_id = f"{client.entry_id}_sensor_{sensor.id}"
        self._attr_extra_state_attributes = {"dcc_id": sensor.id, "pin": sensor.pin}

    @property
    def is_on(self) -> bool:
        """Return True when the sensor is active."""
        return self._sensor.active

    @callback
    def _handle_push(self, message: str) -> None:
        """Handle a push message from the EX-CommandStation.

        Uppercase Q = sensor active, lowercase q = sensor inactive.
        """
        if not self._sensor.matches_push(message):
            return
        try:
            _, active = EXCSSensor.parse_push(message)
            self._sensor.active = active
            self.async_write_ha_state()
        except EXCSError as err:
            LOGGER.error("Error parsing sensor push for id %s: %s", self._sensor.id, err)

    async def async_added_to_hass(self) -> None:
        """Register push callback once added to HA."""
        await super().async_added_to_hass()
        self._unsub_callbacks.append(
            self._client.register_signal_handler(SIGNAL_DATA_PUSHED, self._handle_push)
        )
