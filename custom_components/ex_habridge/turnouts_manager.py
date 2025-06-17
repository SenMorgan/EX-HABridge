"""Manager for interacting with EX-CommandStation turnouts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import LOGGER
from .excs_exceptions import EXCSConnectionError, EXCSError, EXCSInvalidResponseError
from .turnout import EXCSTurnout, EXCSTurnoutConsts

if TYPE_CHECKING:
    from .excs_base import EXCSBaseClient


class EXCSTurnoutsManager:
    """Manager for EX-CommandStation turnouts."""

    def __init__(self, client: EXCSBaseClient) -> None:
        """Initialize the turnouts manager with the EX-CommandStation client."""
        self.client = client
        self.turnouts: list[EXCSTurnout] = []

    async def get_turnouts(self) -> list[EXCSTurnout]:
        """Request and return list of turnouts from the EX-CommandStation."""
        if not self.client.connected:
            msg = "Not connected to EX-CommandStation"
            raise EXCSConnectionError(msg)

        LOGGER.debug("Requesting list of turnouts from EX-CommandStation")

        # Clear existing turnouts
        self.turnouts.clear()

        # Get list of turnout IDs
        turnout_ids = await self._get_turnouts_list()

        if not turnout_ids:
            LOGGER.debug("No turnouts found")
            return self.turnouts

        LOGGER.debug("Found turnout IDs: %s", " ".join(turnout_ids))

        # Get details for each turnout ID
        for turnout_id in turnout_ids:
            turnout = await self._get_turnout_details(turnout_id)
            self.turnouts.append(turnout)
            LOGGER.debug("Turnout detail: %s", turnout)

        return self.turnouts

    async def _get_turnouts_list(self) -> list[str]:
        """Get the list of turnout IDs from the EX-CommandStation."""
        try:
            response = await self.client.await_command_response(
                EXCSTurnoutConsts.CMD_LIST_TURNOUTS,
                EXCSTurnoutConsts.RESP_LIST_PREFIX,
            )
            return self._parse_turnout_ids(response)
        except TimeoutError:
            msg = "Timeout waiting for turnout list response"
            LOGGER.error(msg)
            raise EXCSConnectionError(msg) from None
        except EXCSError as err:
            LOGGER.error("Error getting turnout list: %s", err)
            raise
        except Exception:
            LOGGER.exception("Unexpected error while getting turnout list")
            raise

    def _parse_turnout_ids(self, response: str) -> list[str]:
        """Parse turnout IDs from a list turnouts response."""
        # Check for empty turnout list
        if not response.removeprefix(EXCSTurnoutConsts.RESP_LIST_PREFIX):
            return []

        # Check for valid turnout list response
        if match := EXCSTurnoutConsts.RESP_LIST_REGEX.match(response):
            turnout_ids = match.group("ids")
            if turnout_ids:
                return turnout_ids.split()
            return []

        msg = f"Invalid response for turnout list: {response}"
        raise EXCSInvalidResponseError(msg)

    async def _get_turnout_details(self, turnout_id: str) -> EXCSTurnout:
        """Get details for a specific turnout ID."""
        try:
            response = await self.client.await_command_response(
                EXCSTurnoutConsts.CMD_GET_TURNOUT_DETAILS_FMT.format(id=turnout_id),
                EXCSTurnoutConsts.RESP_DETAILS_PREFIX_FMT.format(id=turnout_id),
            )
            return EXCSTurnout.from_detail_response(response)
        except TimeoutError:
            msg = f"Timeout waiting for turnout details for ID {turnout_id}"
            LOGGER.error(msg)
            raise EXCSConnectionError(msg) from None
        except EXCSError as err:
            LOGGER.error("Error getting turnout detail: %s", err)
            raise
        except Exception:
            LOGGER.exception(
                "Unexpected error while getting turnout details for ID %s", turnout_id
            )
            raise
