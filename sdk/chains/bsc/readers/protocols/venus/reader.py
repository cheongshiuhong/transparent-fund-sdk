# Standard libraries
from typing import Sequence, Optional
import asyncio

# 3rd party libraries
from aiohttp import ClientSession
from eth_utils import to_checksum_address

# Code
from sdk.lib.numbers import Number, LongShortNumbers
from sdk.base.readers.constants import PERCENT_DECIMALS, PRICE_DECIMALS
from sdk.base.readers.structs import PositionsDict, PricedPosition, PricedPositionsDict
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
    VenusPoolSnapshot,
    VenusPoolDetails,
    VenusDetails,
    VenusPoolPricedDetails,
    VenusPricedDetails,
    IVenusReportReader,
    VenusReport,
    VenusPricedReport,
)

# -----------
# Constants
# -----------
# Unitroller.getAssetsIn
UNITROLLER_GET_ASSETS_IN_INPUT_TYPES = ["address"]
UNITROLLER_GET_ASSETS_IN_OUTPUT_TYPES = ["address[]"]
UNITROLLER_GET_ASSETS_IN_SELECTOR = selector_from_sig("getAssetsIn(address)")
# Unitroller.markets
UNITROLLER_MARKETS_INPUT_TYPES = ["address"]
UNITROLLER_MARKETS_OUTPUT_TYPES = ["bool", "uint256", "bool"]
UNITROLLER_MARKETS_SELECTOR = selector_from_sig("markets(address)")
# Pool.balanceOfUnderlying
POOL_BALANCE_OF_UNDERLYING_INPUT_TYPES = ["address"]
POOL_BALANCE_OF_UNDERLYING_OUTPUT_TYPES = ["uint256"]
POOL_BALANCE_OF_UNDERLYING_SELECTOR = selector_from_sig("balanceOfUnderlying(address)")
# Pool.borrowBalanceStored
POOL_BORROW_BALANCE_STORED_INPUT_TYPES = ["address"]
POOL_BORROW_BALANCE_STORED_OUTPUT_TYPES = ["uint256"]
POOL_BORROW_BALANCE_STORED_SELECTOR = selector_from_sig("borrowBalanceStored(address)")
# Pool.supplyRatePerBlock
POOL_SUPPLY_RATE_PER_BLOCK_OUTPUT_TYPES = ["uint256"]
POOL_SUPPLY_RATE_PER_BLOCK_SELECTOR = selector_from_sig("supplyRatePerBlock()")
# Pool.borrowRatePerBlock
POOL_BORROW_RATE_PER_BLOCK_OUTPUT_TYPES = ["uint256"]
POOL_BORROW_RATE_PER_BLOCK_SELECTOR = selector_from_sig("borrowRatePerBlock()")
# Lens.XVSBalance
LENS_XVS_BALANCE_INPUT_TYPES = ["address", "address", "address"]
LENS_XVS_BALANCE_OUTPUT_TYPES = ["(uint256,uint256,address,uint256)"]
LENS_XVS_BALANCE_SELECTOR = selector_from_sig(
    "getXVSBalanceMetadataExt(address,address,address)"
)


class VenusReportReader(IVenusReportReader):
    """
    Reads the positions held and value in the venus protocol.
    """

    def __init__(self, config: BscConfig):
        self.config = config

        # For convenience
        self.protocol = config.protocols.venus
        self.tokens = config.tokens
        self.ETH = config.ETH

    # --------
    # Report
    # --------
    async def get_report(self, session: ClientSession) -> VenusReport:
        """
        Gets the venus protocol report.

        Args:
            session: The async http client session.
        Returns:
            The venus protocol report.
        """
        combined_positions = PositionsDict()

        # Get rewards accrued
        rewards_accrued_task = asyncio.create_task(
            self.__fetch_rewards_accrued(session)
        )

        # Get assets in (markets in)
        assets_in_task = asyncio.create_task(self.__fetch_assets_in(session))

        # Start fetching pool details
        underlying_symbols = self.protocol.pools.keys()
        pool_tasks = asyncio.gather(
            *[
                self.__fetch_pool_snapshot(session, underlying_symbol)
                for underlying_symbol in underlying_symbols
            ]
        )

        # Record the rewards accrued
        rewards_accrued = await rewards_accrued_task
        if rewards_accrued:
            combined_positions["XVS"] = rewards_accrued

        # Instantiate the combiend details with the rewards accrued
        combined_details = VenusDetails(xvs_accrued_rewards=rewards_accrued)

        # Record the pool details and assets in
        assets_in_results = await assets_in_task
        pool_results = await pool_tasks
        for symbol, pool_result in zip(underlying_symbols, pool_results):
            positions, pool_snapshot = pool_result
            if pool_snapshot is not None:
                combined_positions += positions
                pool_details = VenusPoolDetails(
                    **pool_snapshot.dict(),
                    is_collateral=self.protocol.pools[symbol] in assets_in_results,
                )
                combined_details.pools[symbol] = pool_details

        return VenusReport(positions=combined_positions, details=combined_details)

    async def __fetch_assets_in(self, session: ClientSession) -> set[str]:
        calldata = encode_calldata(
            UNITROLLER_GET_ASSETS_IN_SELECTOR,
            UNITROLLER_GET_ASSETS_IN_INPUT_TYPES,
            [self.config.fund_address],
        )

        result = await make_eth_call(
            session, self.config.rpc_uri, self.protocol.unitroller, calldata
        )

        markets_entered: Sequence[str]
        (markets_entered,) = decode_result(
            UNITROLLER_GET_ASSETS_IN_OUTPUT_TYPES, result
        )
        return set(to_checksum_address(address) for address in markets_entered)

    async def __fetch_rewards_accrued(self, session: ClientSession) -> LongShortNumbers:
        xvs = self.tokens["XVS"]
        calldata = encode_calldata(
            LENS_XVS_BALANCE_SELECTOR,
            LENS_XVS_BALANCE_INPUT_TYPES,
            [
                xvs.address,
                self.protocol.unitroller,
                self.config.fund_address,
            ],
        )

        result = await make_eth_call(
            session, self.config.rpc_uri, self.protocol.lens, calldata
        )

        allocated: int
        ((*_, allocated),) = decode_result(LENS_XVS_BALANCE_OUTPUT_TYPES, result)

        xvs_value = Number(value=allocated, decimals=xvs.decimals)
        return LongShortNumbers(net=xvs_value, long=xvs_value)

    async def __fetch_pool_snapshot(
        self, session: ClientSession, underlying_symbol: str
    ) -> tuple[PositionsDict, Optional[VenusPoolSnapshot]]:
        # Retrieve the pool address
        pool_address = self.protocol.pools[underlying_symbol]

        # Retrieve the decimals
        token_decimals = (
            self.tokens[underlying_symbol].decimals
            if underlying_symbol != self.ETH
            else 18
        )

        # Form the multicall calldata
        multicall_calldata = encode_multicall_inputs(
            [
                # Collateral factor
                (
                    self.protocol.unitroller,
                    encode_calldata(
                        UNITROLLER_MARKETS_SELECTOR,
                        UNITROLLER_MARKETS_INPUT_TYPES,
                        [pool_address],
                    ),
                ),
                # Supply balance
                (
                    pool_address,
                    encode_calldata(
                        POOL_BALANCE_OF_UNDERLYING_SELECTOR,
                        POOL_BALANCE_OF_UNDERLYING_INPUT_TYPES,
                        [self.config.fund_address],
                    ),
                ),
                # Borrow balance
                (
                    pool_address,
                    encode_calldata(
                        POOL_BORROW_BALANCE_STORED_SELECTOR,
                        POOL_BORROW_BALANCE_STORED_INPUT_TYPES,
                        [self.config.fund_address],
                    ),
                ),
                # Supply rate per block
                (pool_address, POOL_SUPPLY_RATE_PER_BLOCK_SELECTOR),
                # Borrow rate per block
                (pool_address, POOL_BORROW_RATE_PER_BLOCK_SELECTOR),
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

        # Decode the indvidual outputs
        collateral_factor_int: int
        supply_balance_int: int
        borrow_balance_int: int
        supply_rate_per_block_int: int
        borrow_rate_per_block_int: int

        (_, collateral_factor_int, _) = decode_result(
            UNITROLLER_MARKETS_OUTPUT_TYPES, outputs[0]
        )
        (supply_balance_int,) = decode_result(
            POOL_BALANCE_OF_UNDERLYING_OUTPUT_TYPES, outputs[1]
        )
        (borrow_balance_int,) = decode_result(
            POOL_BORROW_BALANCE_STORED_OUTPUT_TYPES, outputs[2]
        )
        (supply_rate_per_block_int,) = decode_result(
            POOL_SUPPLY_RATE_PER_BLOCK_OUTPUT_TYPES, outputs[3]
        )
        (borrow_rate_per_block_int,) = decode_result(
            POOL_BORROW_RATE_PER_BLOCK_OUTPUT_TYPES, outputs[4]
        )

        # Return None since there is nothing to compute/structure
        if supply_balance_int == 0 and borrow_balance_int == 0:
            return PositionsDict(), None

        # Structuring
        positions_dict = PositionsDict(
            {
                underlying_symbol: LongShortNumbers(
                    net=Number(
                        value=supply_balance_int - borrow_balance_int,
                        decimals=token_decimals,
                    ),
                    long=Number(value=supply_balance_int, decimals=token_decimals),
                    short=Number(value=borrow_balance_int, decimals=token_decimals),
                )
            }
        )

        pool_snapshot = VenusPoolSnapshot(
            supply_balance=Number(value=supply_balance_int, decimals=token_decimals),
            borrow_balance=Number(value=borrow_balance_int, decimals=token_decimals),
            # Venus uses 18 decimals for these values
            supply_rate_per_block=Number(value=supply_rate_per_block_int, decimals=18),
            borrow_rate_per_block=Number(value=borrow_rate_per_block_int, decimals=18),
            # Reduce the collateral factor's decimals
            collateral_factor=Number(
                value=collateral_factor_int, decimals=18
            ).set_decimals(4),
        )

        return positions_dict, pool_snapshot

    # ---------------
    # Priced report
    # ---------------
    async def get_priced_report(
        self, price_resolver: IPriceResolver, session: ClientSession
    ) -> VenusPricedReport:
        """
        Gets the venus protocol priced report.

        Args:
            price_resolver: The resolver to read prices from.
            session: The async http client session.
        Returns:
            The venus protocol priced report.
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

        # Price the details
        priced_details = self.__tag_details_with_prices(report.details, prices)

        return VenusPricedReport(
            value=total_value, positions=priced_positions_dict, details=priced_details
        )

    def __tag_details_with_prices(
        self, details: VenusDetails, prices: dict[str, Number]
    ) -> VenusPricedDetails:
        # Guard clause against empty pools input
        if not details.pools:
            # All other fields default to Value(0, 0)
            return VenusPricedDetails(xvs_accrued_rewards=details.xvs_accrued_rewards)

        # Compute the details values (work in 18 decimals)
        total_supply_value = Number(value=0, decimals=18)
        total_borrow_value = Number(value=0, decimals=18)
        total_collateral_value = Number(value=0, decimals=18)
        pools_with_values: dict[str, VenusPoolPricedDetails] = {}
        borrow_limit = Number(value=0, decimals=18)

        for symbol, pool in details.pools.items():
            # Make a copy of the values for computations
            supply_balance = pool.supply_balance.copy().set_decimals(18)
            borrow_balance = pool.borrow_balance.copy().set_decimals(18)
            collateral_factor = pool.collateral_factor.copy().set_decimals(18)

            # Track the supply and borrow values
            supply_value = supply_balance * prices[symbol]
            borrow_value = borrow_balance * prices[symbol]
            total_supply_value += supply_value
            total_borrow_value += borrow_value

            # Update collateral details if enabled as collateral
            if pool.is_collateral:
                collateral_value = supply_value
                borrow_limit += collateral_value * collateral_factor
                total_collateral_value += collateral_value

            # Track the detailed pools
            pools_with_values[symbol] = VenusPoolPricedDetails(
                **pool.dict(),
                supply_value=supply_value,
                borrow_value=borrow_value,
            )

        max_loan_to_collateral_percent = borrow_limit // total_collateral_value
        loan_to_value_percent = total_borrow_value // total_supply_value
        loan_to_liquidation_percent = total_borrow_value // borrow_limit

        # Set the values to price decimals
        total_supply_value.set_decimals(PRICE_DECIMALS)
        total_borrow_value.set_decimals(PRICE_DECIMALS)
        total_collateral_value.set_decimals(PRICE_DECIMALS)
        borrow_limit.set_decimals(PRICE_DECIMALS)

        # Set percents to precent decimals
        max_loan_to_collateral_percent.set_decimals(PERCENT_DECIMALS)
        loan_to_value_percent.set_decimals(PERCENT_DECIMALS)
        loan_to_liquidation_percent.set_decimals(PERCENT_DECIMALS)

        return VenusPricedDetails(
            xvs_accrued_rewards=details.xvs_accrued_rewards,
            total_supply_value=total_supply_value,
            total_borrow_value=total_borrow_value,
            total_collateral_value=total_collateral_value,
            borrow_limit=borrow_limit,
            max_loan_to_collateral_percent=max_loan_to_collateral_percent,
            loan_to_collateral_percent=loan_to_value_percent,
            loan_to_liquidation_percent=loan_to_liquidation_percent,
            pools=pools_with_values,
        )
