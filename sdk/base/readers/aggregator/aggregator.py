# Standard libraries
from typing import Generic, Coroutine, Any, TypeVar
import asyncio

# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.lib.numbers import Number, LongShortNumbers
from sdk.base.configs import BaseConfig
from sdk.base.readers.constants import POSITION_DECIMALS
from sdk.base.readers.prices.lazy_resolver import LazyPriceResolver
from sdk.base.readers.structs import (
    PositionsDict,
    PricedPositionsDict,
    TDetails,
    TPricedDetails,
    PricedReport,
    ProtocolReport,
    ProtocolPricedReport,
    ChainReport,
    ChainPricedReport,
)
from sdk.base.readers.holdings import HoldingsReader
from sdk.base.readers.prices import IPriceReader
from sdk.base.readers.protocols import IProtocolReportReader


class BaseAggregator(Generic[TDetails, TPricedDetails]):
    """
    Aggregates the readers on one chain to offer a common interface.

    NOTE: No docstrings here for conciseness with aggregator pattern.
    """

    def __init__(
        self,
        config: BaseConfig,
        protocol_report_readers: dict[
            str, IProtocolReportReader[TDetails, TPricedDetails]
        ],
        price_readers: dict[str, IPriceReader],
    ):
        self.config = config

        # Readers
        self.holdings_reader = HoldingsReader(config)
        self.protocol_report_readers = protocol_report_readers

        # Resolve tokens mapping to pricers
        self.price_readers: dict[str, IPriceReader] = {}
        for symbol, token in config.tokens.items():
            # Key error if config has pricing id that doesn't exist
            self.price_readers[symbol] = price_readers[token.pricing.id]

    async def convert_units_async(
        self,
        amount: Number,
        from_symbol: str,
        to_symbol: str
    ) -> Number:
        async with ClientSession() as session:
            # So we just set the position to 0
            price_resolver = LazyPriceResolver(self.price_readers)
            price_resolver.update_positions(PositionsDict())            

            # Get the exchange ratio
            from_price: Number
            to_price: Number
            from_price, to_price = await asyncio.gather(*[
                price_resolver.resolve_price(from_symbol, session),
                price_resolver.resolve_price(to_symbol, session)
            ])

            return amount * from_price // to_price

    async def get_price_async(self, symbol: str) -> Number:
        async with ClientSession() as session:
            # Getting the raw price does not depend on our current positions
            # So we just set the position to 0
            price_resolver = LazyPriceResolver(self.price_readers)
            price_resolver.update_positions(PositionsDict({symbol: LongShortNumbers()}))
            result: Number = await price_resolver.resolve_price(symbol, session)
            return result

    def convert_units_sync(
        self,
        amount: Number,
        from_symbol: str,
        to_symbol: str,
        is_background: bool = False
    ) -> Number:
        result: Number = self.__async_to_sync(
            self.convert_units_async(amount, from_symbol, to_symbol), is_background
        )
        return result

    def get_price_sync(self, symbol: str, is_background: bool = False) -> Number:
        result: Number = self.__async_to_sync(
            self.get_price_async(symbol), is_background
        )
        return result

    # -----------------
    # Holdings report
    # -----------------
    async def get_holdings_report_async(self) -> PositionsDict:
        async with ClientSession() as session:
            result: PositionsDict = await self.holdings_reader.get_positions(session)
            return result

    async def get_holdings_priced_report_async(self) -> PricedPositionsDict:
        async with ClientSession() as session:
            result: PricedPositionsDict
            result = await self.holdings_reader.get_priced_positions(
                LazyPriceResolver(self.price_readers), session
            )
            return result

    def get_holdings_report_sync(self, is_background: bool = False) -> PositionsDict:
        result: PositionsDict = self.__async_to_sync(
            self.get_holdings_report_async(), is_background
        )
        return result

    def get_holdings_priced_report_sync(
        self, is_background: bool = False
    ) -> PricedPositionsDict:
        result: PricedPositionsDict = self.__async_to_sync(
            self.get_holdings_priced_report_async(), is_background
        )
        return result

    # -----------------
    # Protocol report
    # -----------------
    async def get_protocol_report_async(self, name: str) -> ProtocolReport[TDetails]:
        async with ClientSession() as session:
            result: ProtocolReport[TDetails]
            result = await self.protocol_report_readers[name].get_report(session)
            return result

    async def get_protocol_priced_report_async(
        self, name: str
    ) -> ProtocolPricedReport[TPricedDetails]:
        async with ClientSession() as session:
            result: ProtocolPricedReport[TPricedDetails]
            result = await self.protocol_report_readers[name].get_priced_report(
                LazyPriceResolver(self.price_readers), session
            )
            return result

    def get_protocol_report_sync(
        self, name: str, is_background: bool = False
    ) -> ProtocolReport[TDetails]:
        result: ProtocolReport[TDetails]
        result = self.__async_to_sync(
            self.get_protocol_report_async(name), is_background
        )
        return result

    def get_protocol_priced_report_sync(
        self, name: str, is_background: bool = False
    ) -> ProtocolPricedReport[TPricedDetails]:
        result: ProtocolPricedReport[TPricedDetails] = self.__async_to_sync(
            self.get_protocol_priced_report_async(name), is_background
        )
        return result

    # -------------
    # Full report
    # -------------
    async def get_chain_report_async(self) -> ChainReport[TDetails]:
        async with ClientSession() as session:
            holdings = await self.holdings_reader.get_positions(session)

            protocol_names = self.protocol_report_readers.keys()
            protocol_reports: list[ProtocolReport[TDetails]]
            protocol_reports = await asyncio.gather(
                *[
                    self.protocol_report_readers[name].get_report(session)
                    for name in protocol_names
                ]
            )

            total = PositionsDict() + holdings
            protocols: dict[str, ProtocolReport[TDetails]] = {}
            for name, report in zip(protocol_names, protocol_reports):
                protocols[name] = report
                total += report.positions

            return ChainReport[TDetails](
                total=total,
                holdings=holdings,
                protocols=protocols,
            )

    async def get_chain_priced_report_async(self) -> ChainPricedReport[TPricedDetails]:
        price_resolver = LazyPriceResolver(
            self.price_readers, num_coroutines=len(self.protocol_report_readers) + 1
        )

        async with ClientSession() as session:
            holdings: PricedPositionsDict
            protocol_reports: list[ProtocolPricedReport[TPricedDetails]]
            protocol_names = self.protocol_report_readers.keys()

            holdings, *protocol_reports = await asyncio.gather(
                self.holdings_reader.get_priced_positions(price_resolver, session),
                *[
                    self.protocol_report_readers[name].get_priced_report(
                        price_resolver, session
                    )
                    for name in protocol_names
                ]
            )

            # Aggregate holdings
            holdings_value = LongShortNumbers()
            for position in holdings.values():
                holdings_value += position.value

            # Aggregate protocols into total (and convert reports to dict)
            protocols_dict: dict[str, ProtocolPricedReport[TPricedDetails]] = {}
            total = PricedPositionsDict() + holdings
            total_value = holdings_value.deepcopy()
            for name, report in zip(protocol_names, protocol_reports):
                protocols_dict[name] = report
                total += report.positions
                for position in report.positions.values():
                    total_value += position.value

            return ChainPricedReport[TPricedDetails](
                total=PricedReport(value=total_value, positions=total),
                holdings=PricedReport(value=holdings_value, positions=holdings),
                protocols=protocols_dict,
            )

    def get_chain_report_sync(
        self, is_background: bool = False
    ) -> ChainReport[TDetails]:
        result: ChainReport[TDetails]
        result = self.__async_to_sync(self.get_chain_report_async(), is_background)
        return result

    def get_chain_priced_report_sync(
        self, is_background: bool = False
    ) -> ChainPricedReport[TPricedDetails]:
        result: ChainPricedReport[TPricedDetails]
        result = self.__async_to_sync(
            self.get_chain_priced_report_async(), is_background
        )
        return result

    TReturn = TypeVar("TReturn")

    @staticmethod
    def __async_to_sync(
        coroutine: Coroutine[Any, Any, TReturn], is_background: bool
    ) -> TReturn:
        # When using as background task
        if is_background:
            return asyncio.run_coroutine_threadsafe(
                coroutine, asyncio.get_event_loop()
            ).result()

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coroutine)
