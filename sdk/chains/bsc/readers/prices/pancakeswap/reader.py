# Standard libraries
import asyncio

# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.lib.numbers import Number, LongShortNumbers
from sdk.base.configs import GenericTokenConfig
from sdk.base.readers.constants import POSITION_DECIMALS, PRICE_DECIMALS
from sdk.base.readers.prices import IPriceReader, IPriceResolver
from sdk.base.readers.structs import PositionsDict
from sdk.base.readers.utils.calls import make_eth_call, decode_result
from sdk.base.readers.utils.selectors import selector_from_sig
from sdk.chains.bsc.configs import BscConfig
from sdk.chains.bsc.configs.prices import PancakeswapPricingConfig

# -----------
# Constants
# -----------
# Pair.getReserves
PAIR_GET_RESERVES_OUTPUT_TYPES = ["uint256", "uint256", "uint256"]
PAIR_GET_RESERVES_SELECTOR = selector_from_sig("getReserves()")


class PancakeswapPriceReader(IPriceReader):
    """
    Reads the effective prices from liquidity pools based on the amount held.

    Note: price is estimated on the value if we were to liquidate
    all our position in a token if we hold a given token.
    Otherwise, it will be trivially approximated on the ratio of the pool.
    """

    id = "pancakeswap"

    def __init__(self, config: BscConfig):
        self.config = config
        self.ETH = config.ETH
        self.WETH = config.WETH
        self.tokens: dict[str, GenericTokenConfig[PancakeswapPricingConfig]] = {}

        # Only track those whose pricing strategy matches
        for symbol, token in config.tokens.items():
            if token.pricing.id == self.id:
                self.tokens[symbol] = token

    def get_upstream_dependencies(self, upstream_positions: PositionsDict) -> set[str]:
        """
        Resolves the upstream dependencies that need to be included.
        """
        symbols_to_price = self.tokens.keys() & upstream_positions.keys()
        return {self.tokens[symbol].price.quote for symbol in symbols_to_price}

    async def get_price(
        self,
        symbol: str,
        position: LongShortNumbers,
        price_resolver: IPriceResolver,
        session: ClientSession,
    ) -> Number:
        """
        Gets the prices from pancakeswap's liquidity pool's ratio.

        Args:
            symbol: The symbol to get the price for.
            positions: The position of the symbol to price.
            price_resolver: The resolver for reading upstream price dependencies.
            session: The async http client session.
        Returns:
            The price for the symbol.
        """
        token = self.tokens[symbol]
        token_net_position = position.net
        quote_symbol = token.pricing.quote
        quote_price = await price_resolver.resolve_price(quote_symbol, session)
        quote_decimals = (
            self.config.tokens[quote_symbol].decimals
            if quote_symbol != self.config.ETH
            else 18
        )

        # Make the call
        result = await make_eth_call(
            session,
            self.config.rpc_uri,
            token.pricing.address,
            PAIR_GET_RESERVES_SELECTOR,
        )

        # Decode the result
        reserve_x_int: int
        reserve_y_int: int
        reserve_x_int, reserve_y_int, _ = decode_result(
            PAIR_GET_RESERVES_OUTPUT_TYPES, result
        )

        # We are finding how much `y` can we get for our position of `x`
        # `x` is the token of interest and `y` is the quote currency
        # Flip `x` and `y` if the index is 1 to make x the token of interest
        if token.pricing.index == 1:
            reserve_x_int, reserve_y_int = reserve_y_int, reserve_x_int

        # Form them into the `Number` struct
        reserve_x = Number(value=reserve_x_int, decimals=token.decimals)
        reserve_x.set_decimals(POSITION_DECIMALS)
        reserve_y = Number(value=reserve_y_int, decimals=quote_decimals)
        reserve_y.set_decimals(POSITION_DECIMALS)

        # If no positions held, simply take the ratio as the price
        # as it is unimportant to us since we have no position.
        effective_price: Number
        if token_net_position.value == 0:
            effective_price = (reserve_y // reserve_x).set_decimals(PRICE_DECIMALS)

        # Otherwise compute the effective liquidation price for entire holding
        else:
            # Find the units of `y` we would get from selling all of our `x`
            # Our position in `x` being `delta_x`
            constant_k = reserve_x * reserve_y
            units_y = reserve_y - constant_k // (reserve_x + token_net_position)

            # Estimate token of interest's effective price in the quote currency
            effective_price = (units_y // token_net_position).set_decimals(
                PRICE_DECIMALS
            )

        # Estimate the denominated effective price (preserve the price decimals)
        effective_price = effective_price * quote_price

        return effective_price
