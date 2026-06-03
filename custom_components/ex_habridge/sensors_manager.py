"""Manager for interacting with EX-CommandStation DCC sensors."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .const import LOGGER, SIGNAL_DATA_PUSHED
from .excs_exceptions import EXCSConnectionError, EXCSError, EXCSInvalidResponseError
from .sensor_dcc import EXCSSensor, EXCSSensorConsts

if TYPE_CHECKING:
    from .excs_base import EXCSBaseClient

# How long to wait for <Q> responses before considering the list complete
_COLLECTION_WINDOW = 1.0


class EXCSSensorsManager:
    """Manager for EX-CommandStation DCC sensors."""

    def __init__(self, client: EXCSBaseClient) -> None:
        """Initialize the sensors manager."""
        self.client = client
        self.sensors: list[EXCSSensor] = []

    async def get_sensors(self) -> list[EXCSSensor]:
        """Query all DCC sensors via <Q> and return the discovered list.

        The CommandStation pushes one "Q id active" line per defined sensor.
        We collect all such lines within a short time window after sending <Q>.
        """
        if not self.client.connected:
            msg = "Not connected to EX-CommandStation"
            raise EXCSConnectionError(msg)

        LOGGER.debug("Querying DCC sensor states from EX-CommandStation")
        self.sensors.clear()

        collected: list[str] = []

        def _on_push(message: str) -> None:
            # <S> responses always start with uppercase "Q " followed by 3 numbers
            if message.startswith("Q "):
                collected.append(message)

        unsub = self.client.register_signal_handler(SIGNAL_DATA_PUSHED, _on_push)

        try:
            await self.client.send_command(EXCSSensorConsts.CMD_LIST_SENSORS)
            await asyncio.sleep(_COLLECTION_WINDOW)
        except EXCSError as err:
            LOGGER.warning("Error sending sensor list command: %s", err)
        finally:
            unsub()

        if not collected:
            LOGGER.debug("No DCC sensors found")
            return self.sensors

        for message in collected:
            try:
                sensor = EXCSSensor.from_list_response(message)
                self.sensors.append(sensor)
                LOGGER.debug("Found sensor: %s", sensor)
            except EXCSInvalidResponseError as err:
                LOGGER.warning("Could not parse sensor response '%s': %s", message, err)

        LOGGER.debug("Discovered %d DCC sensor(s)", len(self.sensors))
        return self.sensors
