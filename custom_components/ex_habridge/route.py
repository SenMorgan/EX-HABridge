"""Route class for EX-CommandStation."""

from __future__ import annotations

import re
from enum import Enum
from typing import Final

from .excs_exceptions import EXCSInvalidResponseError, EXCSValueError


class EXCSRouteConsts:
    """Constants for EX-CommandStation route."""

    # Commands
    CMD_LIST_ROUTES: Final[str] = "J A"
    CMD_GET_ROUTE_DETAILS_FMT: Final[str] = "J A {id}"
    CMD_START_ROUTE_FMT: Final[str] = "/ START {id}"

    # Regular expressions and corresponding prefixes for parsing responses
    RESP_LIST_PREFIX: Final[str] = "jA"
    # Regex to capture space-separated IDs. Handles "jA.", "jA", and "jA id1 id2..."
    RESP_LIST_REGEX: Final[re.Pattern] = re.compile(
        r"jA\s*(?:\.\s*)?(?P<ids>(?:\d+(?:\s+\d+)*))?"
    )

    RESP_DETAILS_PREFIX_FMT: Final[str] = "jA {id}"
    # Regex to capture route ID, type (R, A, or X), and optional description
    RESP_DETAILS_REGEX: Final[re.Pattern] = re.compile(
        r'jA\s+(?P<id>\d+)\s+(?P<type>[RAX])(?:\s+"(?P<desc>[^"]*)")?'
    )


class EXCSRouteType(Enum):
    """Enum representing route types."""

    ROUTE = "R"
    AUTOMATION = "A"
    UNKNOWN = "X"

    @classmethod
    def from_char(cls, value: str) -> EXCSRouteType:
        """Convert a character value (R, A, or X) to an EXCSRouteType enum."""
        try:
            return cls(value)
        except ValueError as err:
            # If no match found, raise an error
            msg = f"Invalid route type: {value}"
            raise EXCSValueError(msg) from err

    def as_string(self) -> str:
        """Return a human-readable string representation of the route type."""
        match self:
            case EXCSRouteType.ROUTE:
                return "Route"
            case EXCSRouteType.AUTOMATION:
                return "Automation"
            case EXCSRouteType.UNKNOWN:
                return "Unknown"


class EXCSRoute:
    """Representation of a route in the EX-CommandStation."""

    def __init__(self, route_id: int, route_type: str, description: str) -> None:
        """Initialize the route."""
        self.id = route_id
        self.type = EXCSRouteType.from_char(route_type)
        self.description = description or f"{self.type.as_string()} {route_id}"

    def __repr__(self) -> str:
        """Return a string representation of the route."""
        return (
            f"EXCSRoute(id={self.id}, type={self.type.as_string()}, "
            f"description='{self.description}')"
        )

    @classmethod
    def from_detail_response(cls, response: str) -> EXCSRoute:
        """Create a route instance from a detail response."""
        if match := EXCSRouteConsts.RESP_DETAILS_REGEX.match(response):
            try:
                return cls(
                    route_id=int(match.group("id")),
                    route_type=match.group("type"),
                    description=match.group("desc").strip('"')
                    if match.group("desc")
                    else "",
                )
            except EXCSValueError as err:
                msg = f"Error parsing route detail: {err}"
                raise EXCSValueError(msg) from err

        msg = f"Invalid response for route detail: {response}"
        raise EXCSInvalidResponseError(msg)
