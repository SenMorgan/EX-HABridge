"""DCC sensor class for EX-CommandStation."""

from __future__ import annotations

import re
from typing import Final

from .excs_exceptions import EXCSInvalidResponseError


class EXCSSensorConsts:
    """Constants for EX-CommandStation DCC sensors."""

    # <S> (no args) lists all defined sensors.
    # Response format: "Q id pin active"  e.g. "Q 164 164 1"
    CMD_LIST_SENSORS: Final[str] = "S"

    # <S> list response regex — uppercase Q, three numbers
    RESP_LIST_REGEX: Final[re.Pattern] = re.compile(
        r"Q\s+(?P<id>\d+)\s+(?P<pin>\d+)\s+(?P<active>[01])"
    )

    # Push state change format:
    #   "Q id"  (uppercase Q) → sensor ACTIVE
    #   "q id"  (lowercase q) → sensor INACTIVE
    # Only one number (the sensor id) follows the letter.
    RESP_PUSH_REGEX: Final[re.Pattern] = re.compile(
        r"[Qq]\s+(?P<id>\d+)$"
    )


class EXCSSensor:
    """Representation of a DCC sensor in the EX-CommandStation."""

    def __init__(self, sensor_id: int, pin: int = 0) -> None:
        """Initialize the sensor."""
        self.id = sensor_id
        self.pin = pin
        self.active: bool = False
        self.description: str = f"Sensor {sensor_id}"
        self._id_str: str = str(sensor_id)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<EXCSSensor id={self.id} pin={self.pin} active={self.active}>"

    def matches_push(self, message: str) -> bool:
        """Return True if this push message belongs to this sensor."""
        if not message or message[0] not in ("Q", "q"):
            return False
        parts = message.split()
        return len(parts) == 2 and parts[1] == self._id_str

    @classmethod
    def parse_push(cls, message: str) -> tuple[int, bool]:
        """Parse a push message and return (id, active).

        Uppercase Q = active, lowercase q = inactive.
        """
        match = EXCSSensorConsts.RESP_PUSH_REGEX.match(message)
        if not match:
            msg = f"Invalid sensor push message: {message}"
            raise EXCSInvalidResponseError(msg)
        sensor_id = int(match.group("id"))
        active = message[0] == "Q"
        return sensor_id, active

    @classmethod
    def from_list_response(cls, message: str) -> EXCSSensor:
        """Create a sensor instance from a <S> list response line."""
        match = EXCSSensorConsts.RESP_LIST_REGEX.match(message)
        if not match:
            msg = f"Invalid sensor list response: {message}"
            raise EXCSInvalidResponseError(msg)
        sensor = cls(
            sensor_id=int(match.group("id")),
            pin=int(match.group("pin")),
        )
        sensor.active = bool(int(match.group("active")))
        return sensor
