# Standard libraries
from abc import ABC, abstractmethod

# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.base.readers.prices.interfaces import IPriceResolver
from sdk.base.readers.structs import PositionsDict, PricedPositionsDict


class IHoldingsReader(ABC):
    @abstractmethod
    async def get_positions(self, session: ClientSession) -> PositionsDict:
        """
        Positions readers should implement
        the method to retrieve the positions.
        """

    @abstractmethod
    async def get_priced_positions(
        self,
        price_resolver: IPriceResolver,
        session: ClientSession,
    ) -> PricedPositionsDict:
        """
        Positions readers should implement
        the method to retrieve the priced positions.
        """
