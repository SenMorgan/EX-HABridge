"""Track representation for EX-CommandStation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from .excs_exceptions import EXCSInvalidResponseError


class TrackConsts:
    """Constants for EX-CommandStation tracks."""

    # Command to list all tracks
    CMD_LIST_TRACKS: Final[str] = "="

    # Command to get track current
    CMD_GET_CURRENT: Final[str] = "c"

    # Command to toggle track power (individually)
    CMD_TOGGLE_TRACK_POWER_FMT: Final[str] = "p{track_letter} {state}"

    # Response format for track list
    RESP_TRACK_LIST_PREFIX: Final[str] = "="
    RESP_TRACK_LIST_REGEX: Final[re.Pattern] = re.compile(
        r"=\s+(?P<track_letter>[A-Z])\s+(?P<mode>[a-zA-Z]+)(?:\s+(?P<cab>\d+))?"
    )

    # Response format for track current
    RESP_TRACK_CURRENT_PREFIX: Final[str] = "c"
    RESP_TRACK_CURRENT_REGEX: Final[re.Pattern] = re.compile(
        r'c\s+"(?P<name>[^"]+)"\s+(?P<current>\d+)\s+(?P<type>[CV])\s+'
        r'"(?P<unit>[^"]+)"\s+"(?P<param1>[^"]+)"\s+(?P<max_ma>\d+)\s+'
        r'"(?P<param2>[^"]+)"\s+(?P<trip_ma>\d+)'
    )

    # Track power responses
    RESP_TRACK_POWER_ON_FMT: Final[str] = "p{track_letter}1"
    RESP_TRACK_POWER_OFF_FMT: Final[str] = "p{track_letter}0"


@dataclass
class EXCSTrack:
    """Representation of a track in the EX-CommandStation."""

    letter: str  # Track letter identifier (A, B, C, etc.)
    mode: str  # Track mode (MAIN, PROG, etc.)
    cab: int = 0  # Cab number (if any)
    current: int = 0  # Current in mA
    max_ma: int = 0  # Maximum current handling
    trip_ma: int = 0  # Current trip threshold
    is_powered: bool = False  # Power state

    def __init__(self, letter: str, mode: str, cab: int = 0) -> None:
        """Initialize the track."""
        self.letter = letter
        self.mode = mode
        self.cab = cab

    @classmethod
    def parse_track_list_response(cls, response: str) -> list[EXCSTrack]:
        """Parse the track list from a response string."""
        tracks = []
        for line in response.strip().split("\n"):
            if match := TrackConsts.RESP_TRACK_LIST_REGEX.match(line):
                track_letter = match.group("track_letter")
                mode = match.group("mode")
                cab = int(match.group("cab")) if match.group("cab") else 0
                tracks.append(cls(track_letter, mode, cab))
            else:
                # Skip lines that don't match the expected format
                continue

        return tracks

    @classmethod
    def parse_track_current_response(cls, response: str) -> tuple[str, int, int, int]:
        """Parse the track current from a response string."""
        if match := TrackConsts.RESP_TRACK_CURRENT_REGEX.match(response):
            name = match.group("name")
            current = int(match.group("current"))
            max_ma = int(match.group("max_ma"))
            trip_ma = int(match.group("trip_ma"))

            # Extract track letter from the name (format: "CurrentMAIN", "CurrentPROG", etc.)
            # The track letter should be in the name, typically the last character
            track_letter = name.replace("Current", "")

            return track_letter, current, max_ma, trip_ma

        msg = f"Invalid track current response: {response}"
        raise EXCSInvalidResponseError(msg)

    @staticmethod
    def toggle_track_power_cmd(track_letter: str, state: bool) -> str:
        """Create command to toggle power for a specific track."""
        return TrackConsts.CMD_TOGGLE_TRACK_POWER_FMT.format(
            track_letter=track_letter, state="1" if state else "0"
        )
