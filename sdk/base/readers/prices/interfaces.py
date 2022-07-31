# Standard libraries
from abc import ABC, abstractmethod
from typing import Protocol, Iterable, Callable, Coroutine, Any

# Third party libraries
from aiohttp import ClientSession

# Code
from sdk.lib.numbers import LongShortNumbers, Number
from sdk.base.readers.structs import PositionsDict


GetPricesFunction = Callable[[PositionsDict], Coroutine[Any, Any, dict[str, Number]]]


class IPriceResolver(Protocol):
    """
    Forward-declared interface for the price resolver.
    """

    def update_positions(self, positions: PositionsDict) -> None:
        ...

    async def resolve_price(self, symbol: str, session: ClientSession) -> Number:
        ...

    async def resolve_prices(
        self, symbols: Iterable[str], session: ClientSession
    ) -> dict[str, Number]:
        ...


class IPriceReader(ABC):
    """
    Interface for the price reader.
    """

    id: str

    @abstractmethod
    async def get_price(
        self,
        symbol: str,
        position: LongShortNumbers,
        resolver: IPriceResolver,
        session: ClientSession,
    ) -> Number:
        """
        Price readers should implement the method to get the price for a symbol.
        """
