"""Manager for interacting with EX-CommandStation routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import LOGGER
from .excs_exceptions import (
    EXCSConnectionError,
    EXCSError,
    EXCSInvalidResponseError,
)
from .route import EXCSRoute, EXCSRouteConsts, EXCSRouteType

if TYPE_CHECKING:
    from .excs_base import EXCSBaseClient


class EXCSRoutesManager:
    """Manager for EX-CommandStation routes."""

    def __init__(self, client: EXCSBaseClient) -> None:
        """Initialize the routes manager with the EX-CommandStation client."""
        self.client = client
        self.routes: list[EXCSRoute] = []

    async def get_routes(self) -> list[EXCSRoute]:
        """Request and return list of routes from the EX-CommandStation."""
        if not self.client.connected:
            msg = "Not connected to EX-CommandStation"
            raise EXCSConnectionError(msg)

        LOGGER.debug("Requesting list of routes from EX-CommandStation")

        # Clear existing routes
        self.routes.clear()

        # Get list of route IDs
        route_ids = await self._get_routes_list()

        if not route_ids:
            LOGGER.debug("No routes found")
            return self.routes

        LOGGER.debug("Found route IDs: %s", " ".join(route_ids))

        # Get details for each route ID
        for route_id in route_ids:
            route = await self._get_route_details(route_id)
            # Ignore if type is X (unknown/undefined)
            if route.type != EXCSRouteType.UNKNOWN:
                self.routes.append(route)
            LOGGER.debug("Route detail: %s", route)

        return self.routes

    async def _get_routes_list(self) -> list[str]:
        """Get the list of route IDs from the EX-CommandStation."""
        response_text = None
        try:
            response_text = await self.client.await_command_response(
                EXCSRouteConsts.CMD_LIST_ROUTES,
                EXCSRouteConsts.RESP_LIST_PREFIX,
            )
            return self.parse_route_ids(response_text)
        except TimeoutError:
            msg = "Timeout waiting for route list response"
            LOGGER.error(msg)
            raise EXCSConnectionError(msg) from None
        except EXCSError as err:
            msg = f"Error getting route list: {err}"
            LOGGER.error(msg)
            raise
        except Exception:
            LOGGER.exception("Unexpected error while getting route list")
            raise

    def parse_route_ids(self, response: str) -> list[str]:
        """Parse route IDs from a list routes response."""
        if match := EXCSRouteConsts.RESP_LIST_REGEX.match(response):
            route_ids = match.group("ids")
            if route_ids:
                return route_ids.split()
            return []

        msg = f"Invalid response for route list: {response}"
        raise EXCSInvalidResponseError(msg)

    async def _get_route_details(self, route_id: str) -> EXCSRoute:
        """Get details for a specific route ID."""
        try:
            response = await self.client.await_command_response(
                EXCSRouteConsts.CMD_GET_ROUTE_DETAILS_FMT.format(id=route_id),
                EXCSRouteConsts.RESP_DETAILS_PREFIX_FMT.format(id=route_id),
            )
            return EXCSRoute.from_detail_response(response)
        except TimeoutError:
            msg = f"Timeout waiting for route detail response for ID {route_id}"
            LOGGER.error(msg)
            raise EXCSConnectionError(msg) from None
        except EXCSError as err:
            msg = f"Error getting route detail for ID {route_id}: {err}"
            LOGGER.error(msg)
            raise
        except Exception:
            LOGGER.exception(
                "Unexpected error while getting route details for ID %s", route_id
            )
            raise
