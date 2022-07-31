# Standard libraries
from typing import Optional
import asyncio

# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.lib.numbers import Number, LongShortNumbers
from sdk.base.configs import BaseConfig
from sdk.base.readers.constants import POSITION_DECIMALS
from sdk.base.readers.structs import PositionsDict, PricedPosition, PricedPositionsDict
from sdk.base.readers.utils.calls import (
    call_eth_method,
    make_eth_call,
    encode_calldata,
    decode_result,
)
from sdk.base.readers.utils.selectors import selector_from_sig
from sdk.base.readers.prices import IPriceResolver
from .interfaces import IHoldingsReader

# -----------
# Constants
# -----------
# Erc20.balanceOf
ERC20_BALANCE_OF_INPUT_TYPES = ["address"]
ERC20_BALANCE_OF_OUTPUT_TYPES = ["uint256"]
ERC20_BALANCE_OF_SELECTOR = selector_from_sig("balanceOf(address)")


class HoldingsReader(IHoldingsReader):
    """
    Reads the holdings positions.
    """

    def __init__(self, config: BaseConfig):
        self.config = config

    # -----------
    # Positions
    # -----------
    async def get_positions(self, session: ClientSession) -> PositionsDict:
        """
        Gets the holdings positions.

        Args:
            session: The async http client session.
        Returns:
            The holdings positions dictionary.
        """
        positions_dict = PositionsDict()

        # Start fetching token positions
        symbols = self.config.tokens.keys()
        token_tasks = asyncio.gather(
            *[self.__fetch_token_snapshot(symbol, session) for symbol in symbols]
        )

        # Start fetching eth position
        eth_task = asyncio.create_task(self.__fetch_eth_snapshot(session))

        # Record the positions
        token_results = await token_tasks
        for positions in token_results:
            positions_dict += positions

        positions_dict += await eth_task

        return positions_dict

    async def __fetch_eth_snapshot(self, session: ClientSession) -> PositionsDict:
        result = await call_eth_method(
            session,
            self.config.rpc_uri,
            "eth_getBalance",
            [self.config.fund_address, "latest"],
        )

        eth_value = Number(value=int(result, 16), decimals=18)
        eth_value.set_decimals(POSITION_DECIMALS)

        return PositionsDict(
            {self.config.ETH: LongShortNumbers(net=eth_value, long=eth_value)}
        )

    async def __fetch_token_snapshot(
        self, symbol: str, session: ClientSession
    ) -> PositionsDict:
        token = self.config.tokens[symbol]

        # Encode the arguments and form the calldata
        calldata = encode_calldata(
            ERC20_BALANCE_OF_SELECTOR,
            ERC20_BALANCE_OF_INPUT_TYPES,
            [self.config.fund_address],
        )

        # Await the result
        result = await make_eth_call(
            session, self.config.rpc_uri, token.address, calldata
        )

        # Decode the result
        balance_int: int
        (balance_int,) = decode_result(ERC20_BALANCE_OF_OUTPUT_TYPES, result)

        # Return an empty position if balance is 0
        if balance_int == 0:
            return PositionsDict()

        # Parse the result into the `Value` struct
        balance = Number(value=balance_int, decimals=token.decimals)

        # Structuring and returning
        return PositionsDict({symbol: LongShortNumbers(net=balance, long=balance)})

    # ------------------
    # Priced positions
    # ------------------
    async def get_priced_positions(
        self, price_resolver: IPriceResolver, session: ClientSession
    ) -> PricedPositionsDict:
        """
        Positions readers should implement
        the method to retrieve the priced positions.

        Args:
            price_resolver: The resolver to read prices from.
            session: The async http client session.
        Returns:
            The priced positions dictionary.
        """
        positions = await self.get_positions(session)

        price_resolver.update_positions(positions)
        prices = await price_resolver.resolve_prices(positions.keys(), session)

        priced_positions_dict = PricedPositionsDict()
        for symbol in positions.keys():
            priced_positions_dict[symbol] = PricedPosition(
                amount=positions[symbol],
                value=positions[symbol].broadcast_mul(prices[symbol]),
            )

        return priced_positions_dict
