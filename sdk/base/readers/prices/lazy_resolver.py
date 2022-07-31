# Standard libraries
from typing import Iterable
import asyncio

# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.lib.numbers import Number
from sdk.base.readers.structs import PositionsDict
from .interfaces import IPriceReader


class LazyPriceResolver:
    """
    Lazy price resolver that reads prices from the price readers on demand.

    Synchronizes by tracking and accumulating the positions from each coroutine
    before starting to fetch the prices from the price readers.

    NOTE: Please ensure that configurations are properly configured such that
          there are not circular dependencies in pricing, which will cause
          the reading to wait forever (like a deadlock).
          e.g., Pricing CAKE with Pancakeswap quoting on USDT
          but pricing USDT also with Pancakeswap quoting on CAKE.
          We have put in place a 10-second timeout before throwing an exception.
    """

    price_readers: dict[str, IPriceReader]
    num_coroutines: int
    counter: int
    is_ready_to_fetch_prices: asyncio.Event
    positions: PositionsDict
    tasks: dict[str, asyncio.Task[Number]]
    results: dict[str, Number]

    def __init__(self, price_readers: dict[str, IPriceReader], num_coroutines: int = 1):
        self.price_readers = price_readers
        self.num_coroutines = num_coroutines
        self.counter = 0
        self.is_ready_to_fetch_prices = asyncio.Event()
        self.positions = PositionsDict()
        self.tasks = {}
        self.results = {}

    def update_positions(self, positions: PositionsDict) -> None:
        """
        Tracks the positions to facilitate downstream pricing
        """
        self.positions += positions
        # Increment counter and set event if all updated
        self.counter += 1
        if self.counter == self.num_coroutines:
            self.is_ready_to_fetch_prices.set()

    async def resolve_price(
        self,
        symbol: str,
        session: ClientSession,
    ) -> Number:
        """
        Allows multiple coroutines to resolve a price on-demand
        e.g., in different protocols.
        """
        # Wait for all coroutines to update positions before starting
        await self.is_ready_to_fetch_prices.wait()

        # Start the task if not already started
        if symbol not in self.tasks.keys():
            self.tasks[symbol] = asyncio.create_task(
                self.price_readers[symbol].get_price(
                    symbol, self.positions.get(symbol), self, session
                )
            )

        # Wait for the response (instant if already previously awaited)
        # We use asyncio to raise TimeoutError if more than 10 seconds
        # Guards against circular dependencies in pricing.
        self.results[symbol] = await asyncio.wait_for(self.tasks[symbol], 10)
        return self.results[symbol]

    async def resolve_prices(
        self,
        symbols: Iterable[str],
        session: ClientSession,
    ) -> dict[str, Number]:
        """
        Allows multiple coroutines to resolve a price on-demand
        e.g., in different protocols.
        """
        prices = await asyncio.gather(
            *[self.resolve_price(symbol, session) for symbol in symbols]
        )
        return {symbol: price for symbol, price in zip(symbols, prices)}
