# Standard libraries
from typing import Optional
import asyncio

# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.lib.numbers import Number, LongShortNumbers
from sdk.base.readers.constants import POSITION_DECIMALS, PRICE_DECIMALS
from sdk.base.readers.structs import (
    PositionsDict,
    PricedNetPosition,
    PricedPosition,
    PricedPositionsDict,
)
from sdk.base.readers.utils.calls import (
    make_eth_call,
    encode_calldata,
    decode_result,
)
from sdk.base.readers.utils.multicall import (
    encode_multicall_inputs,
    decode_multicall_result,
)
from sdk.base.readers.prices import IPriceResolver
from sdk.base.readers.utils.selectors import selector_from_sig
from sdk.chains.bsc.configs import BscConfig
from .types import (
    PancakeswapLpDetails,
    PancakeswapDetails,
    PancakeswapLpPricedDetails,
    PancakeswapPricedDetails,
    IPancakeswapReportReader,
    PancakeswapReport,
    PancakeswapPricedReport,
)

# -----------
# Constants
# -----------
# Pair.token0
TOKEN_0_OUTPUT_TYPES = ["address"]
TOKEN_0_SELECTOR = selector_from_sig("token0()")
# Pair.pendingCake
PAIR_PENDING_CAKE_INPUT_TYPES = ["uint256", "address"]
PAIR_PENDING_CAKE_OUTPUT_TYPES = ["uint256"]
PAIR_PENDING_CAKE_SELECTOR = selector_from_sig("pendingCake(uint256,address)")
# Pair.getReserves
PAIR_GET_RESERVES_OUTPUT_TYPES = ["uint256", "uint256", "uint256"]
PAIR_GET_RESERVES_SELECTOR = selector_from_sig("getReserves()")
# Pair.totalSupply
PAIR_TOTAL_SUPPLY_OUTPUT_TYPES = ["uint256"]
PAIR_TOTAL_SUPPLY_SELECTOR = selector_from_sig("totalSupply()")
# Pair.balanceOf
PAIR_BALANCE_OF_INPUT_TYPES = ["address"]
PAIR_BALANCE_OF_OUTPUT_TYPES = ["uint256"]
PAIR_BALANCE_OF_SELECTOR = selector_from_sig("balanceOf(address)")
# MasterChefV2.userInfo
MASTER_CHEF_V2_USER_INFO_INPUT_TYPES = ["uint256", "address"]
MASTER_CHEF_V2_USER_INFO_OUTPUT_TYPES = ["uint256", "uint256", "uint256"]
MASTER_CHEF_V2_USER_INFO_SELECTOR = selector_from_sig("userInfo(uint256,address)")
# SmartChef.userInfo
SMART_CHEF_USER_INFO_INPUT_TYPES = ["address"]
SMART_CHEF_USER_INFO_OUTPUT_TYPES = ["uint256", "uint256"]
SMART_CHEF_USER_INFO_SELECTOR = selector_from_sig("userInfo(address)")


class PancakeswapReportReader(IPancakeswapReportReader):
    """
    Reads the positions held and value in the pancakeswap protocol.
    """

    def __init__(self, config: BscConfig):
        self.config = config

        # For convenience
        self.protocol = config.protocols.pancakeswap
        self.tokens = config.tokens
        self.ETH = config.ETH

    # --------
    # Report
    # --------
    async def get_report(self, session: ClientSession) -> PancakeswapReport:
        """
        Gets the pancakeswap protocol report.

        Args:
            session: The async http client session.
        Returns:
            The pancakeswap protocol report.
        """
        combined_positions = PositionsDict()
        combined_details = PancakeswapDetails(lps={}, smart_chefs={})

        # Start fetching lps details
        pair_symbols = self.protocol.pairs.keys()
        lp_tasks = asyncio.gather(
            *[
                self.__fetch_lp_snapshot(pair_symbol, session)
                for pair_symbol in pair_symbols
            ]
        )

        # Start fetching smart chefs details
        smart_chef_symbols = self.protocol.smart_chefs.keys()
        smart_chef_tasks = asyncio.gather(
            *[
                self.__fetch_smart_chef_snapshot(smart_chef_symbol, session)
                for smart_chef_symbol in smart_chef_symbols
            ]
        )

        # Record the lp results
        lp_results = await lp_tasks
        for symbol, lp_result in zip(pair_symbols, lp_results):
            positions, lp_details = lp_result
            if lp_details is None:
                continue
            combined_positions += positions
            combined_details.lps[symbol] = lp_details

        # Record the smart chef results
        smart_chef_results = await smart_chef_tasks
        for symbol, positions in zip(smart_chef_symbols, smart_chef_results):
            if not positions:
                continue
            combined_positions += positions
            combined_details.smart_chefs[symbol] = positions

        return PancakeswapReport(positions=combined_positions, details=combined_details)

    async def __fetch_lp_snapshot(
        self, pair_symbol: str, session: ClientSession
    ) -> tuple[PositionsDict, Optional[PancakeswapLpDetails]]:
        # Parse the symbols
        symbol_0, symbol_1 = pair_symbol.split("-")

        # Retrieve the decimals
        decimals_0 = self.tokens[symbol_0].decimals if symbol_0 != self.ETH else 18
        decimals_1 = self.tokens[symbol_1].decimals if symbol_1 != self.ETH else 18

        # Retrieve the pair
        pair = self.protocol.pairs[pair_symbol]

        # Encode the arguments into a multicall
        multicall_calldata = encode_multicall_inputs(
            [
                # Token 0
                (pair.address, TOKEN_0_SELECTOR),
                # Cake rewards
                (
                    self.protocol.master_chef_v2,
                    encode_calldata(
                        PAIR_PENDING_CAKE_SELECTOR,
                        PAIR_PENDING_CAKE_INPUT_TYPES,
                        [pair.pid, self.config.fund_address],
                    ),
                ),
                # Reserves
                (pair.address, PAIR_GET_RESERVES_SELECTOR),
                # Total supply
                (pair.address, PAIR_TOTAL_SUPPLY_SELECTOR),
                # Holding balance
                (
                    pair.address,
                    encode_calldata(
                        PAIR_BALANCE_OF_SELECTOR,
                        PAIR_BALANCE_OF_INPUT_TYPES,
                        [self.config.fund_address],
                    ),
                ),
                # Farming balance
                (
                    self.protocol.master_chef_v2,
                    encode_calldata(
                        MASTER_CHEF_V2_USER_INFO_SELECTOR,
                        MASTER_CHEF_V2_USER_INFO_INPUT_TYPES,
                        [pair.pid, self.config.fund_address],
                    ),
                ),
            ]
        )

        # Make the call and decode the multicall outputs
        result = await make_eth_call(
            session,
            self.config.rpc_uri,
            self.config.multicall_address,
            multicall_calldata,
        )
        _, outputs = decode_multicall_result(result)

        # Decode the individual outputs
        token_0_address: str
        cake_accrued_rewards_int: int
        reserve_0_int: int
        reserve_1_int: int
        total_supply_int: int
        holding_balance_int: int
        farming_balance_int: int
        (token_0_address,) = decode_result(TOKEN_0_OUTPUT_TYPES, outputs[0])
        (cake_accrued_rewards_int,) = decode_result(
            PAIR_PENDING_CAKE_OUTPUT_TYPES, outputs[1]
        )
        (reserve_0_int, reserve_1_int, _) = decode_result(
            PAIR_GET_RESERVES_OUTPUT_TYPES, outputs[2]
        )
        (total_supply_int,) = decode_result(PAIR_TOTAL_SUPPLY_OUTPUT_TYPES, outputs[3])
        (holding_balance_int,) = decode_result(PAIR_BALANCE_OF_OUTPUT_TYPES, outputs[4])
        (farming_balance_int, *_) = decode_result(
            MASTER_CHEF_V2_USER_INFO_OUTPUT_TYPES, outputs[5]
        )

        # Return None since there is nothing to compute/structure
        if holding_balance_int == 0 and farming_balance_int == 0:
            return PositionsDict(), None

        # Flip the symbols and decimals if in wrong order before computing
        if self.tokens[symbol_0].address != token_0_address:
            symbol_0, symbol_1 = symbol_1, symbol_0
            decimals_0, decimals_1 = decimals_1, decimals_0

        # Parse the outputs into the `Number` struct
        cake_accrued_rewards = Number(
            value=cake_accrued_rewards_int, decimals=self.tokens["CAKE"].decimals
        )
        reserve_0 = Number(value=reserve_0_int, decimals=decimals_0)
        reserve_1 = Number(value=reserve_1_int, decimals=decimals_1)
        # Pancakeswap uses 18 decimals for PancakePair
        total_supply = Number(value=total_supply_int, decimals=18)
        holding_balance = Number(value=holding_balance_int, decimals=18)
        farming_balance = Number(value=farming_balance_int, decimals=18)

        # Computations (NOTE: order matters to preserve the relevent decimals value)
        holding_share = holding_balance // total_supply
        farming_share = farming_balance // total_supply
        holding_balance_0 = reserve_0 * holding_share
        holding_balance_1 = reserve_1 * holding_share
        farming_balance_0 = reserve_0 * farming_share
        farming_balance_1 = reserve_1 * farming_share

        # Aggregations
        total_balance = holding_balance + farming_balance
        total_balance_0 = holding_balance_0 + farming_balance_0
        total_balance_1 = holding_balance_1 + farming_balance_1

        # Structuring
        positions_dict = PositionsDict(
            {
                "CAKE": LongShortNumbers(
                    net=cake_accrued_rewards, long=cake_accrued_rewards
                ),
                symbol_0: LongShortNumbers(net=total_balance_0, long=total_balance_0),
                symbol_1: LongShortNumbers(net=total_balance_1, long=total_balance_1),
            }
        )

        report = PancakeswapLpDetails(
            cake_accrued_rewards=cake_accrued_rewards,
            holding={
                "lp_token": holding_balance,
                symbol_0: holding_balance_0,
                symbol_1: holding_balance_1,
            },
            farming={
                "lp_token": farming_balance,
                symbol_0: farming_balance_0,
                symbol_1: farming_balance_1,
            },
            total={
                "lp_token": total_balance,
                symbol_0: total_balance_0,
                symbol_1: total_balance_1,
            },
        )

        return positions_dict, report

    async def __fetch_smart_chef_snapshot(
        self, smart_chef_symbol: str, session: ClientSession
    ) -> PositionsDict:
        """
        Makes a single call to a smart chef to get the balance.
        """
        # Parse the symbols
        staked_symbol, reward_symbol = smart_chef_symbol.split("-")

        # Retrieve the decimals
        staked_decimals = self.tokens[staked_symbol].decimals
        reward_decimals = self.tokens[reward_symbol].decimals

        # Retrieve the smart chef address
        smart_chef_address = self.protocol.smart_chefs[smart_chef_symbol]

        # Encode the arguments and form the calldata
        calldata = encode_calldata(
            SMART_CHEF_USER_INFO_SELECTOR,
            SMART_CHEF_USER_INFO_INPUT_TYPES,
            [self.config.fund_address],
        )

        # Await the result
        result = await make_eth_call(
            session, self.config.rpc_uri, smart_chef_address, calldata
        )

        # Decode the result
        staked_amount_int: int
        reward_amount_int: int
        staked_amount_int, reward_amount_int = decode_result(
            SMART_CHEF_USER_INFO_OUTPUT_TYPES, result
        )

        # Return None since there is nothing to compute/structure
        if staked_amount_int == 0 and reward_amount_int == 0:
            return PositionsDict()

        # Parse the outputs into the `Value` struct
        staked_amount = Number(value=staked_amount_int, decimals=staked_decimals)
        reward_amount = Number(value=reward_amount_int, decimals=reward_decimals)

        # Structuring and returning
        return PositionsDict(
            {
                staked_symbol: LongShortNumbers(net=staked_amount, long=staked_amount),
                reward_symbol: LongShortNumbers(net=reward_amount, long=reward_amount),
            }
        )

    # ---------------
    # Priced report
    # ---------------
    async def get_priced_report(
        self, price_resolver: IPriceResolver, session: ClientSession
    ) -> PancakeswapPricedReport:
        """
        Gets the pancakeswap protocol priced report.

        Args:
            price_resolver: The resolver to read prices from.
            session: The async http client session.
        Returns:
            The pancakeswap protocol priced report.
        """
        report = await self.get_report(session)

        price_resolver.update_positions(report.positions)
        prices = await price_resolver.resolve_prices(report.positions.keys(), session)

        # Price the positions
        priced_positions_dict = PricedPositionsDict()
        total_value = LongShortNumbers()
        for symbol in report.positions.keys():
            priced_positions_dict[symbol] = PricedPosition(
                amount=report.positions[symbol],
                value=report.positions[symbol].broadcast_mul(prices[symbol]),
            )
            total_value += priced_positions_dict[symbol].value

        # Price the lp details
        lp_priced_details_dict: dict[str, PancakeswapLpPricedDetails] = {}
        for symbol, lp_details in report.details.lps.items():
            lp_priced_details_dict[symbol] = PancakeswapLpPricedDetails(
                cake_accrued_rewards=PricedNetPosition(
                    amount=lp_details.cake_accrued_rewards,
                    value=lp_details.cake_accrued_rewards * prices["CAKE"],
                ),
                holding=self.__tag_prices_on_lp_details(lp_details.holding, prices),
                farming=self.__tag_prices_on_lp_details(lp_details.farming, prices),
                total=self.__tag_prices_on_lp_details(lp_details.total, prices),
            )

        # Price the smart chef details
        smart_chef_priced_details_dict: dict[str, dict[str, PricedNetPosition]] = {}
        for symbol, smart_chef_details in report.details.smart_chefs.items():
            smart_chef_priced_details_dict[
                symbol
            ] = self.__tag_prices_on_smart_chef_details(smart_chef_details, prices)

        return PancakeswapPricedReport(
            value=total_value,
            positions=priced_positions_dict,
            details=PancakeswapPricedDetails(
                lps=lp_priced_details_dict, smart_chefs=smart_chef_priced_details_dict
            ),
        )

    def __tag_prices_on_lp_details(
        self, sub_details_dict: dict[str, Number], prices: dict[str, Number]
    ) -> dict[str, PricedNetPosition]:
        output: dict[str, PricedNetPosition] = {}
        lp_token_value = Number()
        for symbol in sub_details_dict.keys() - {"lp_token"}:
            current_amount = sub_details_dict[symbol].set_decimals(POSITION_DECIMALS)
            current_value = current_amount * prices[symbol]
            current_value.set_decimals(PRICE_DECIMALS)

            output[symbol] = PricedNetPosition(
                amount=sub_details_dict[symbol], value=current_value
            )
            lp_token_value += output[symbol].value

        output["lp_token"] = PricedNetPosition(
            amount=sub_details_dict["lp_token"], value=lp_token_value
        )
        return output

    def __tag_prices_on_smart_chef_details(
        self, details_dict: dict[str, Number], prices: dict[str, Number]
    ) -> dict[str, PricedNetPosition]:
        output: dict[str, PricedNetPosition] = {}
        for symbol in details_dict.keys():
            current_amount = details_dict[symbol].set_decimals(POSITION_DECIMALS)
            current_value = current_amount * prices[symbol]
            current_value.set_decimals(PRICE_DECIMALS)

            output[symbol] = PricedNetPosition(
                amount=details_dict[symbol], value=current_value
            )

        return output
