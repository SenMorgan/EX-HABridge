"""Sensor platform for EX-CommandStation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import callback

from .const import DOMAIN, LOGGER
from .entity import EXCSEntity
from .excs_exceptions import EXCSError
from .track import EXCSTrack, TrackConsts

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .excs_client import EXCommandStationClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EX-CommandStation sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]

    # Add track current sensors
    if client.tracks:
        track_sensors = []
        for track in client.tracks:
            track_sensors.append(TrackCurrentSensor(client, track))
        async_add_entities(track_sensors)


class TrackCurrentSensor(EXCSEntity, SensorEntity):
    """Representation of a track current sensor."""

    def __init__(self, client: EXCommandStationClient, track: EXCSTrack) -> None:
        """Initialize the sensor."""
        super().__init__(client)
        self._track = track

        # Set entity properties
        self._attr_name = f"Track {track.letter} Current"
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.MILLIAMPERE

        self.entity_description = SensorEntityDescription(
            key=f"track_{track.letter}_current",
            icon="mdi:lightning-bolt",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        )
        self._attr_unique_id = f"{client.entry_id}_{self.entity_description.key}"
        self._attr_native_value = track.current

        # Extra state attributes
        self._attr_extra_state_attributes = {
            "max_current": track.max_ma,
            "trip_current": track.trip_ma,
            "track_mode": track.mode,
        }

    @property
    def native_value(self) -> int:
        """Return the current value."""
        return self._track.current

    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Send command to get current
            current_response = await self._client.await_command_response(
                TrackConsts.CMD_GET_CURRENT, TrackConsts.RESP_TRACK_CURRENT_PREFIX
            )

            # Parse current response
            track_letter, current, max_ma, trip_ma = (
                EXCSTrack.parse_track_current_response(current_response)
            )

            # Update track if it matches the letter
            if self._track.letter == track_letter:
                self._track.current = current
                self._track.max_ma = max_ma
                self._track.trip_ma = trip_ma

                # Update attributes
                self._attr_extra_state_attributes = {
                    "max_current": max_ma,
                    "trip_current": trip_ma,
                    "track_mode": self._track.mode,
                }
        except EXCSError:
            LOGGER.exception(
                "Failed to update current for track %s", self._track.letter
            )
