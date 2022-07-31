# Standard libraries
from typing import Optional

# Code
from sdk.fund.types import CallType, FundTxn, FundTxns
from sdk.chains.bsc.configs import BscConfig
from sdk.chains.bsc.configs.protocols.pancakeswap import PancakeswapPairConfig
from sdk.base.encoders import BaseProtocolEncoder


class PancakeswapLpFarmingUtilEncoder(BaseProtocolEncoder):
    """
    Encoder for the Pancakeswap LP Farming utility contract.
    """

    def __init__(self, config: BscConfig):
        super().__init__(config)

        # For convenience
        self.pancakeswap = config.protocols.pancakeswap
        self.address = config.fund_utils["pancakeswap_lp_farming_util"]

        # Util Contract
        self.contract = self._get_contract_encoder(__file__)

    def lp_farm(
        self,
        token_0: str,
        token_1: str,
        amount_token_0: str,
        amount_token_1: str,
        amount_token_0_min: str,
        amount_token_1_min: str,
        farm_all_balance: bool = False,
    ) -> FundTxns:
        """
        Adds liquidity and deposits the lp tokens received to farm.

        Args:
            token_0: The symbol of the first token of the lp pair.
            token_1: The symbol of the second token of the lp pair.
            amount_token_0: The amount of the first token to add.
            amount_token_1: The amount of the second token to add.
            amount_token_0_min: The minimum amount for the txn to succeed.
            amount_token_1_min: The minimum amount for the txn to succeed.
            farm_all_balance: Whether to farm all of the holding balance.

        Returns:
            The list of encoded fund transactions.
        """
        pair = self.__get_pair_if_exists(token_0, token_1)

        if not pair:
            raise ValueError("Liquidity pool for input pair does not exist")

        # Token 0 is ETH
        if self._is_eth(token_0):
            call_data = self.contract.encode_abi(
                "farmTokenAndETH",
                (
                    self._get_token_address(token_1),
                    amount_token_1,
                    amount_token_0,
                    amount_token_1_min,
                    amount_token_0_min,
                    pair.pid,
                    farm_all_balance,
                ),
            )

            return [FundTxn(CallType.UTIL, self.address, call_data)]

        # Token 1 is ETH
        if self._is_eth(token_1):
            self.contract.encode_abi(
                "farmTokenAndETH",
                (
                    self._get_token_address(token_0),
                    amount_token_0,
                    amount_token_1,
                    amount_token_0_min,
                    amount_token_1_min,
                    pair.pid,
                    farm_all_balance,
                ),
            )

            return [FundTxn(CallType.UTIL, self.address, call_data)]

        # Both are tokens
        call_data = self.contract.encode_abi(
            "farmTokens",
            (
                self._get_token_address(token_0),
                self._get_token_address(token_1),
                amount_token_0,
                amount_token_1,
                amount_token_0_min,
                amount_token_1_min,
                pair.pid,
                farm_all_balance,
            ),
        )

        return [FundTxn(CallType.UTIL, self.address, call_data)]

    def lp_unfarm(
        self,
        token_0: str,
        token_1: str,
        amount_lp_token: str,
        amount_token_0_min: str,
        amount_token_1_min: str,
    ) -> FundTxns:
        """
        Withdraws the lp tokens from farming and removes liquidity.

        Args:
            token_0: The symbol of the first token of the lp pair.
            token_1: The symbol of the second token of the lp pair.
            amount_lp_token: The amount of the lp tokens to unfarm.
            amount_token_0_min: The minimum amount for the txn to succeed.
            amount_token_1_min: The minimum amount for the txn to succeed.

        Returns:
            The list of encoded fund transactions.
        """
        pair = self.__get_pair_if_exists(token_0, token_1)

        if not pair:
            raise ValueError("Liquidity pool for input pair does not exist")

        # Token 0 is ETH
        if self._is_eth(token_0):
            call_data = self.contract.encode_abi(
                "unfarmTokenAndETH",
                (
                    self._get_token_address(token_1),
                    amount_lp_token,
                    amount_token_1_min,
                    amount_token_0_min,
                    pair.pid,
                ),
            )

            return [FundTxn(CallType.UTIL, self.address, call_data)]

        # Token 1 is ETH
        if self._is_eth(token_1):
            self.contract.encode_abi(
                "unfarmTokenAndETH",
                (
                    self._get_token_address(token_0),
                    amount_lp_token,
                    amount_token_0_min,
                    amount_token_1_min,
                    pair.pid,
                ),
            )

            return [FundTxn(CallType.UTIL, self.address, call_data)]

        # Both are tokens
        call_data = self.contract.encode_abi(
            "unfarmTokens",
            (
                self._get_token_address(token_0),
                self._get_token_address(token_1),
                amount_lp_token,
                amount_token_0_min,
                amount_token_1_min,
                pair.pid,
            ),
        )

        return [FundTxn(CallType.UTIL, self.address, call_data)]

    # -----------------
    # Private methods
    # -----------------
    def __get_pair_if_exists(
        self, symbol_0: str, symbol_1: str
    ) -> Optional[PancakeswapPairConfig]:
        """
        Returns the pair for two input tokens if they exist.

        Args:
            symbol_0: The symbol of the first token of the pair.
            symbol_1: The symbol of the second token of the pair.

        Returns:
            The address of the pair.
        """
        result: PancakeswapPairConfig
        if self.pancakeswap.pairs.get(f"{symbol_0}-{symbol_1}"):
            result = self.pancakeswap.pairs[f"{symbol_0}-{symbol_1}"]
            return result
        if self.pancakeswap.pairs.get(f"{symbol_1}-{symbol_0}"):
            result = self.pancakeswap.pairs[f"{symbol_1}-{symbol_0}"]
            return result

        return None
