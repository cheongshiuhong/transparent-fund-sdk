# Standard libraries
from typing import Optional
import time

# Code
from sdk.lib.shortest_path_resolver import ShortestPathResolver
from sdk.fund.types import CallType, FundTxn, FundTxns
from sdk.base.encoders import BaseProtocolEncoder
from sdk.base.encoders.general.erc20 import Erc20Encoder
from sdk.chains.bsc.configs import BscConfig
from sdk.chains.bsc.configs.protocols.pancakeswap import PancakeswapPairConfig
from .helpers.swap import PancakeswapSwapHelper
from .helpers.lp import PancakeswapLpHelper


# Constants
SECONDS_TO_DEADLINE = 86400  # seconds (=1 day)


class PancakeswapEncoder(BaseProtocolEncoder):
    """
    Composed encoder for the pancakeswap protocol
    """

    def __init__(self, config: BscConfig):
        super().__init__(config)

        # For convenience
        self.protocol = config.protocols.pancakeswap
        self.tokens = config.tokens
        self.cake_address = self._get_token_address("CAKE")

        # Contract encoders
        get_contract_encoder = self._get_contract_encoder_partial(__file__)
        self.router = get_contract_encoder("abis/router.json")
        self.master_chef_v2 = get_contract_encoder("abis/master_chef_v2.json")
        self.cake_pool = get_contract_encoder("abis/cake_pool.json")
        self.smart_chef = get_contract_encoder("abis/smart_chef.json")
        self.erc20 = Erc20Encoder()

        # Helpers
        self.swap_helper = PancakeswapSwapHelper(self.protocol, self.router, self.erc20)
        self.lp_helper = PancakeswapLpHelper(
            self.protocol, self.router, self.master_chef_v2, self.erc20
        )

        # Utils
        self.path_resolver = ShortestPathResolver(
            pair.split("-") for pair in self.protocol.pairs.keys()
        )

    # --------------
    # Main methods
    # --------------
    def swap_with_exact(
        self,
        from_token: str,
        to_token: str,
        exact_amount_to_send: int,
        min_amount_to_receive: int,
        seconds_to_deadline: int = 0,
        path: list[str] = [],
    ) -> FundTxns:
        """
        Perform a swap where the the amount to send is exact and the amount to
        receive is set as a minimum that is required for the swap to succeed.

        Args:
            from_token: The symbol of the token to send.
            to_token: The symbol of the token to receive.
            exact_amount_to_send: The exact amount of tokens to send.
            min_amount_to_receive: The minimum amount of tokens to receive
                for the transactio to succeed.
            seconds_to_deadline: The seconds to add to the current time
                for the deadline (e.g. time.time() + 60 seconds).
            path: The path for the swap to take, will automatically be resolved
                if not specified.

        Returns:
            The list of encoded fund transactions.
        """
        deadline = self.__get_deadline(seconds_to_deadline)

        # if sending eth, from_token is WBNB
        if self._is_eth(from_token):
            return self.swap_helper.swap_exact_eth_for_tokens(
                amount_eth_exact=exact_amount_to_send,
                amount_token_min=min_amount_to_receive,
                path=path or self.__resolve_path(self.config.ETH, to_token),
                to=self.config.fund_address,
                deadline=deadline,
            )

        # if receiving eth, to_token is WBNB
        if self._is_eth(to_token):
            return self.swap_helper.swap_exact_tokens_for_eth(
                amount_token_exact=exact_amount_to_send,
                amount_eth_min=min_amount_to_receive,
                path=path or self.__resolve_path(from_token, self.config.ETH),
                to=self.config.fund_address,
                deadline=deadline,
            )

        # both are tokens
        return self.swap_helper.swap_exact_tokens_for_tokens(
            amount_token_0_exact=exact_amount_to_send,
            amount_token_1_min=min_amount_to_receive,
            path=path or self.__resolve_path(from_token, to_token),
            to=self.config.fund_address,
            deadline=deadline,
        )

    def swap_for_exact(
        self,
        from_token: str,
        to_token: str,
        max_amount_to_send: int,
        exact_amount_to_receive: int,
        seconds_to_deadline: int = 0,
        path: list[str] = [],
    ) -> FundTxns:
        """
        Perform a swap where the the amount to send is set as the maximum
        willing to be sent to receive the exact amount of tokens to receive
        in order to for the swap to succeed.

        Args:
            from_token: The symbol of the token to send.
            to_token: The symbol of the token to receive.
            max_amount_to_send: The maximum amount of tokens to send.
            exact_amount_to_receive: The exact amount of tokens to receive
                for the transactio to succeed.
            seconds_to_deadline: The seconds to add to the current time
                for the deadline (e.g. time.time() + 60 seconds).
            path: The path for the swap to take, will automatically be resolved
                if not specified.

        Returns:
            The list of encoded fund transactions.
        """
        deadline = self.__get_deadline(seconds_to_deadline)

        # if sending eth, from_token is WBNB
        if self._is_eth(from_token):
            return self.swap_helper.swap_eth_for_exact_tokens(
                amount_eth_max=max_amount_to_send,
                amount_token_exact=exact_amount_to_receive,
                path=path or self.__resolve_path(self.config.ETH, to_token),
                to=self.config.fund_address,
                deadline=deadline,
            )

        # if receiving eth, to_token is WBNB
        if self._is_eth(to_token):
            return self.swap_helper.swap_tokens_for_exact_eth(
                amount_token_max=max_amount_to_send,
                amount_eth_exact=exact_amount_to_receive,
                path=path or self.__resolve_path(from_token, self.config.ETH),
                to=self.config.fund_address,
                deadline=deadline,
            )

        # both tokens
        return self.swap_helper.swap_tokens_for_exact_tokens(
            amount_token_0_max=max_amount_to_send,
            amount_token_1_exact=exact_amount_to_receive,
            path=path or self.__resolve_path(from_token, to_token),
            to=self.config.fund_address,
            deadline=deadline,
        )

    def add_liquidity(
        self,
        token_0: str,
        token_1: str,
        amount_token_0: int,
        amount_token_1: int,
        amount_token_0_min: int = 0,
        amount_token_1_min: int = 0,
        seconds_to_deadline: int = 0,
    ) -> FundTxns:
        """
        Add liquidity to a liqudity pool.

        Args:
            token_0: The symbol of the first token of the lp pair.
            token_1: The symbol of the second token of the lp pair.
            amount_token_0: The amount of the first token to add.
            amount_token_1: The amount of the second token to add.
            amount_token_0_min: The minimum amount for the txn to succeed.
            amount_token_1_min: The minimum amount for the txn to succeed.
            seconds_to_deadline: The seconds to add to the current time
                for the deadline (e.g. time.time() + 60 seconds).

        Returns:
            The list of encoded fund transactions.
        """
        deadline = self.__get_deadline(seconds_to_deadline)
        pair = self.__get_pair_if_exists(token_0, token_1)

        if not pair:
            raise ValueError("Liqudity pool for input pair does not exist")

        # Token 0 is ETH
        if self._is_eth(token_0):
            return self.lp_helper.add_liquidity_eth(
                token=self._get_token_address(token_1),
                amount_token=amount_token_1,
                amount_eth=amount_token_0,
                amount_token_min=amount_token_1_min,
                amount_eth_min=amount_token_0_min,
                to=self.config.fund_address,
                deadline=deadline,
            )

        # Token 1 is ETH
        if self._is_eth(token_1):
            return self.lp_helper.add_liquidity_eth(
                token=self._get_token_address(token_0),
                amount_token=amount_token_0,
                amount_eth=amount_token_1,
                amount_token_min=amount_token_0_min,
                amount_eth_min=amount_token_1_min,
                to=self.config.fund_address,
                deadline=deadline,
            )

        # Both are tokens
        return self.lp_helper.add_liquidity(
            token_0=self._get_token_address(token_0),
            token_1=self._get_token_address(token_1),
            amount_token_0=amount_token_0,
            amount_token_1=amount_token_1,
            amount_token_0_min=amount_token_0_min,
            amount_token_1_min=amount_token_1_min,
            to=self.config.fund_address,
            deadline=deadline,
        )

    def remove_liquidity(
        self,
        token_0: str,
        token_1: str,
        amount_lp_token: int,
        amount_token_0_min: int,
        amount_token_1_min: int,
        seconds_to_deadline: int = 0,
    ) -> FundTxns:
        """
        Removes liquidity from a liquidity pool.

        Args:
            token_0: The symbol of the first token of the lp pair.
            token_1: The symbol of the second token of the lp pair.
            amount_lp_token: The amount of the lp token to change back.
            amount_token_0_min: The minimum amount for the txn to succeed.
            amount_token_1_min: The minimum amount for the txn to succeed.
            seconds_to_deadline: The seconds to add to the current time
                for the deadline (e.g. time.time() + 60 seconds).

        Returns:
            The list of encoded fund transactions.
        """
        deadline = self.__get_deadline(seconds_to_deadline)
        pair = self.__get_pair_if_exists(token_0, token_1)

        if not pair:
            raise ValueError("Liqudity pool for input pair does not exist")

        # Token 0 is ETH
        if self._is_eth(token_0):
            return self.lp_helper.remove_liquidity_eth(
                lp_token=pair.address,
                token=self._get_token_address(token_1),
                amount_lp_token=amount_lp_token,
                amount_token_min=amount_token_1_min,
                amount_eth_min=amount_token_0_min,
                to=self.config.fund_address,
                deadline=deadline,
            )

        # Token 1 is ETH
        if self._is_eth(token_1):
            return self.lp_helper.remove_liquidity_eth(
                lp_token=pair.address,
                token=self._get_token_address(token_1),
                amount_lp_token=amount_lp_token,
                amount_token_min=amount_token_0_min,
                amount_eth_min=amount_token_1_min,
                to=self.config.fund_address,
                deadline=deadline,
            )

        # Both are tokens
        return self.lp_helper.remove_liquidity(
            lp_token=pair.address,
            token_0=self._get_token_address(token_0),
            token_1=self._get_token_address(token_1),
            amount_lp_token=amount_lp_token,
            amount_token_0_min=amount_token_0_min,
            amount_token_1_min=amount_token_1_min,
            to=self.config.fund_address,
            deadline=deadline,
        )

    def lp_farm(self, token_0: str, token_1: str, amount_lp_token: int) -> FundTxns:
        """
        Deposits the lp tokens to farm.

        Args:
            token_0: The symbol of the first token of the lp pair.
            token_1: The symbol of the second token of the lp pair.
            amount_lp_token: The amount of the lp tokens to farm with.

        Returns:
            The list of encoded fund transactions.
        """
        pair = self.__get_pair_if_exists(token_0, token_1)

        if not pair:
            raise ValueError("Liqudity pool for input pair does not exist")

        return self.lp_helper.farm(pair.pid, pair.address, amount_lp_token)

    def lp_unfarm(self, token_0: str, token_1: str, amount_lp_token: int) -> FundTxns:
        """
        Withdraws the lp tokens to stop farming.

        Args:
            token_0: The symbol of the first token of the lp pair.
            token_1: The symbol of the second token of the lp pair.
            amount_lp_token: The amount of the lp tokens to unfarm.

        Returns:
            The list of encoded fund transactions.
        """
        pair = self.__get_pair_if_exists(token_0, token_1)

        if not pair:
            raise ValueError("Liqudity pool for input pair does not exist")

        return self.lp_helper.unfarm(pair.pid, amount_lp_token)

    def single_farm_cake(self, amount: int, duration: int) -> FundTxns:
        """
        Farms for CAKE in the single pool.

        Args:
            amount: The amount of CAKE to deposit.
            duration: The lock duration in seconds.

        Returns:
            The list of encoded fund transactions.
        """
        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", self.protocol.cake_pool, amount
        )
        call_data = self.cake_pool.encode_abi("deposit", amount, duration)
        unapprove_data = self.erc20.encode_abi("approve", self.protocol.cake_pool, 0)

        return [
            FundTxn(CallType.TOKEN, self.cake_address, allowance_data),
            FundTxn(CallType.PROTOCOL, self.protocol.cake_pool, call_data),
            FundTxn(CallType.TOKEN, self.cake_address, unapprove_data),
        ]

    def single_unfarm_cake(self, amount: int = 0) -> FundTxns:
        """
        Withdraws the deposited CAKE and harvests the rewards.

        Args:
            amount: The amount of CAKE to withdraw (all if 0)

        Returns:
            The list of encoded fund transactions.
        """
        if amount == 0:
            call_data = self.cake_pool.enbode_abi("withdrawAll")
        else:
            call_data = self.cake_pool.enbode_abi("withdrawByAmount", amount)

        return [FundTxn(CallType.PROTOCOL, self.cake_address, call_data, 0)]

    def single_farm(
        self, staked_token: str, reward_token: str, amount: int
    ) -> FundTxns:
        """
        Farms for other tokens in the single smart chef pool.

        Args:
            token: The symbol of the reward token to farm for.
            amount: The amount to deposit and farm.

        Returns:
            The list of encoded fund transactions.
        """
        staked_token_address = self._get_token_address(staked_token)
        smart_chef_address = self.__get_smart_chef_address(staked_token, reward_token)

        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", smart_chef_address, amount
        )
        call_data = self.smart_chef.encode_abi("deposit", amount)
        unapprove_data = self.erc20.encode_abi("approve", smart_chef_address, 0)

        return [
            FundTxn(CallType.TOKEN, staked_token_address, allowance_data),
            FundTxn(CallType.PROTOCOL, smart_chef_address, call_data),
            FundTxn(CallType.TOKEN, staked_token_address, unapprove_data),
        ]

    def single_unfarm(
        self, staked_token: str, reward_token: str, amount: int
    ) -> FundTxns:
        """
        Withdraws the staked token and harvests the reward tokens.

        Args:
            token: The symbol of the reward token farming for.
            amount: The amount to withdraw.

        Returns:
            The list of encoded fund transactions.
        """
        smart_chef_address = self.__get_smart_chef_address(staked_token, reward_token)

        call_data = self.smart_chef.encode_abi("withdraw", amount)

        return [FundTxn(CallType.PROTOCOL, smart_chef_address, call_data, 0)]

    # -----------------
    # Private methods
    # -----------------
    @staticmethod
    def __get_deadline(seconds_to_deadline: int = 0) -> int:
        """
        Computes the deadline timestamp based on the current time.

        Args:
            seconds_to_deadline The seconds delta to add to the current timestamp.

        Returns:
            The deadline timestamp.
        """
        return int(time.time()) + (seconds_to_deadline or SECONDS_TO_DEADLINE)

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
        if self.protocol.pairs.get(f"{symbol_0}-{symbol_1}"):
            result = self.protocol.pairs[f"{symbol_0}-{symbol_1}"]
            return result
        if self.protocol.pairs.get(f"{symbol_1}-{symbol_0}"):
            result = self.protocol.pairs[f"{symbol_1}-{symbol_0}"]
            return result

        return None

    def __get_smart_chef_address(self, staked_symbol: str, reward_symbol: str) -> str:
        """
        Retrieves a smart chef address.

        Args:
            staked_symbol: The symbol of the staked token.
            reward_symbol: The symbol of the reward token.

        Raises:
            ValueError: if smart chef not found.

        Returns:
            The smart chef address.
        """
        try:
            result: str = self.protocol.smart_chefs[f"{staked_symbol}-{reward_symbol}"]
            return result
        except KeyError:
            raise ValueError(
                f"{staked_symbol}-{reward_symbol} does not have a smart chef."
            )

    def __resolve_path(self, from_symbol: str, to_symbol: str) -> list[str]:
        """
        Find path between two inputs by either:
            1) Finding a pool with the two directly.
            2) Finding their corresponding BNB pools to bridge the swap.
            3) Use the shortest path from the path resolver.

        Args:
            from_symbol: The symbol of the from token.
            to_symbol: The symbol of the to token.

        Returns:
            The path reprsented by the list of pair addresses.
        """
        # Check if pair exists (if one is WETH, we would have found it if they exist)
        if self.__get_pair_if_exists(from_symbol, to_symbol):
            return [
                self._get_token_address(from_symbol),
                self._get_token_address(to_symbol),
            ]

        # Check if bnb pair exists for both tokens
        if self.__get_pair_if_exists(
            from_symbol, self.config.ETH
        ) and self.__get_pair_if_exists(to_symbol, self.config.ETH):
            return [
                self._get_token_address(from_symbol),
                self._get_token_address(self.config.WETH),
                self._get_token_address(to_symbol),
            ]

        # Check if path resolver had found a path
        resolved_path = self.path_resolver.get(from_symbol, to_symbol)
        if resolved_path is not None:
            return [self._get_token_address(symbol) for symbol in resolved_path]

        raise ValueError(
            f"Unable to resolve the token swap path for {from_symbol} > {to_symbol}."
        )
