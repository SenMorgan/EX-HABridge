"""Manager for interacting with EX-CommandStation roster entries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import LOGGER
from .excs_exceptions import EXCSConnectionError, EXCSError, EXCSInvalidResponseError
from .roster import EXCSRosterConsts, EXCSRosterEntry

if TYPE_CHECKING:
    from .excs_base import EXCSBaseClient


class EXCSRosterManager:
    """Manager for EX-CommandStation roster entries."""

    def __init__(self, client: EXCSBaseClient) -> None:
        """Initialize the roster manager with the EX-CommandStation client."""
        self.client = client
        self.entries: list[EXCSRosterEntry] = []

    async def get_roster_entries(self) -> list[EXCSRosterEntry]:
        """Request and return list of roster entries from the EX-CommandStation."""
        if not self.client.connected:
            msg = "Not connected to EX-CommandStation"
            raise EXCSConnectionError(msg)

        LOGGER.debug("Requesting list of roster entries from EX-CommandStation")

        # Clear existing roster entries
        self.entries.clear()

        # Get list of roster entry IDs
        roster_ids = await self._get_roster_ids()

        if not roster_ids:
            LOGGER.debug("No roster entries found")
            return self.entries

        LOGGER.debug("Found roster entry IDs: %s", ",".join(roster_ids))

        # Get details for each roster entry ID
        for raw_roster_id in roster_ids:
            roster_id = raw_roster_id.strip()
            if not roster_id:
                LOGGER.warning("Empty roster ID found, skipping")
                continue

            # Get details for the roster entry
            entry = await self._get_roster_entry_details(roster_id)
            self.entries.append(entry)
            LOGGER.debug("Roster entry detail: %s", entry)

        return self.entries

    async def _get_roster_ids(self) -> list[str]:
        """Get the list of roster entry IDs from the EX-CommandStation."""
        try:
            response = await self.client.await_command_response(
                EXCSRosterConsts.CMD_LIST_ROSTER_ENTRIES,
                EXCSRosterConsts.RESP_LIST_PREFIX,
            )
            return self.parse_roster_ids(response)
        except TimeoutError:
            msg = "Timeout waiting for roster list response"
            LOGGER.error(msg)
            raise EXCSConnectionError(msg) from None
        except EXCSError as err:
            LOGGER.error("Error getting roster list: %s", err)
            raise
        except Exception:
            LOGGER.exception("Unexpected error while getting roster list")
            raise

    def parse_roster_ids(self, response: str) -> list[str]:
        """Parse roster IDs from a list roster response."""
        # Check for empty roster list
        if not response.removeprefix(EXCSRosterConsts.RESP_LIST_PREFIX):
            return []

        # Check for valid roster list response
        if match := EXCSRosterConsts.RESP_LIST_REGEX.match(response):
            roster_ids = match.group("ids")
            if roster_ids:
                return roster_ids.split()
            return []

        msg = f"Invalid response for roster list: {response}"
        raise EXCSInvalidResponseError(msg)

    async def _get_roster_entry_details(self, roster_id: str) -> EXCSRosterEntry:
        """Get details for a specific roster entry ID."""
        try:
            response = await self.client.await_command_response(
                EXCSRosterConsts.CMD_GET_ROSTER_DETAILS_FMT.format(cab_id=roster_id),
                EXCSRosterConsts.RESP_DETAILS_PREFIX_FMT.format(cab_id=roster_id),
            )
            return EXCSRosterEntry.from_detail_response(response)
        except TimeoutError:
            msg = f"Timeout waiting for roster details for ID {roster_id}"
            LOGGER.error(msg)
            raise EXCSConnectionError(msg) from None
        except EXCSError as err:
            LOGGER.error("Error getting roster detail: %s", err)
            raise
        except Exception:
            LOGGER.exception(
                "Unexpected error while getting roster details for ID %s", roster_id
            )
            raise
