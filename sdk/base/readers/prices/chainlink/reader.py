# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.lib.numbers import LongShortNumbers, Number
from sdk.base.configs import BaseConfig, GenericTokenConfig
from sdk.base.configs.prices import ChainlinkPricingConfig
from sdk.base.readers.constants import PRICE_DECIMALS
from sdk.base.readers.utils.calls import make_eth_call, decode_result
from sdk.base.readers.utils.multicall import (
    encode_multicall_inputs,
    decode_multicall_result,
)
from sdk.base.readers.utils.selectors import selector_from_sig
from ..interfaces import IPriceReader, IPriceResolver

# -----------
# Constants
# -----------
# Chainlink.decimals
CHAINLINK_DECIMALS_OUTPUT_TYPES = ["uint8"]
CHAINLINK_DECIMALS_SELECTOR = selector_from_sig("decimals()")
# Chainlink.latestRoundData
CHAINLINK_LATEST_ROUND_OUTPUT_TYPES = [
    "uint80",
    "int256",
    "uint256",
    "uint256",
    "uint80",
]
CHAINLINK_LATEST_ROUND_SELECTOR = selector_from_sig("latestRoundData()")


class ChainlinkPriceReader(IPriceReader):
    """
    Reads prices from chainlink oracles.
    """

    id = "chainlink"

    def __init__(self, config: BaseConfig):
        self.config = config
        self.tokens: dict[str, GenericTokenConfig[ChainlinkPricingConfig]] = {}

        # Only track those whose pricing strategy matches
        for symbol, token in config.tokens.items():
            if token.pricing.id == self.id:
                self.tokens[symbol] = token

    async def get_price(
        self,
        symbol: str,
        position: LongShortNumbers,
        price_resolver: IPriceResolver,
        session: ClientSession,
    ) -> Number:
        """
        Gets the prices from chainlink oracles.

        Args:
            symbol: The symbol to get the price for.
            position: The position of the symbol to price for.
            price_resolver: The resolver for reading upstream price dependencies.
            session: The async http client session.
        Returns:
            The price for the symbol.
        """
        oracle_address = self.tokens[symbol].pricing.address

        multicall_calldata = encode_multicall_inputs(
            [
                (oracle_address, CHAINLINK_DECIMALS_SELECTOR),
                (oracle_address, CHAINLINK_LATEST_ROUND_SELECTOR),
            ]
        )

        result = await make_eth_call(
            session,
            self.config.rpc_uri,
            self.config.multicall_address,
            multicall_calldata,
        )

        _, outputs = decode_multicall_result(result)

        (decimals,) = decode_result(CHAINLINK_DECIMALS_OUTPUT_TYPES, outputs[0])
        _, answer, *_ = decode_result(CHAINLINK_LATEST_ROUND_OUTPUT_TYPES, outputs[1])

        return Number(value=answer, decimals=decimals).set_decimals(PRICE_DECIMALS)
