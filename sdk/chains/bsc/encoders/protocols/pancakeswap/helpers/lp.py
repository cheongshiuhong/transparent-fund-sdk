# Types
from sdk.fund.types import CallType, FundTxn, FundTxns
from sdk.base.encoders import BaseContractEncoder
from sdk.base.encoders.general.erc20 import Erc20Encoder
from sdk.chains.bsc.configs.protocols.pancakeswap import PancakeswapConfig


class PancakeswapLpHelper:
    """
    Helper for pancakeswap calls regarding liquidity pools.
    """

    def __init__(
        self,
        config: PancakeswapConfig,
        router: BaseContractEncoder,
        master_chef_v2: BaseContractEncoder,
        erc20: Erc20Encoder,
    ):
        self.config = config
        self.router = router
        self.master_chef_v2 = master_chef_v2
        self.erc20 = erc20

    def add_liquidity_eth(
        self,
        token: str,
        amount_token: int,
        amount_eth: int,
        amount_token_min: int,
        amount_eth_min: int,
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Add liquidity to a liquidity pool where ETH is one of the underlying.

        Args:
            token: The address of the token to add, along with ETH.
            amount_token: The amonut of the token to add.
            amount_eth: The amount of eth to add.
            amount_token_min: The minimum amount of token to add.
            amount_eth_min: The minimum amount of eth to add.
            to: The recipient of the lp tokens.
            deadline: The deadline before the transaction is voided.

        Returns:
            The list of encoded fund transactions.
        """
        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_token
        )
        call_data = self.router.encode_abi(
            "addLiquidityETH",
            token,
            amount_token,
            amount_token_min,
            amount_eth_min,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.TOKEN, self.config.router, allowance_data),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data, value=amount_eth),
            FundTxn(CallType.TOKEN, self.config.router, unapprove_data),
        ]

    def add_liquidity(
        self,
        token_0: str,
        token_1: str,
        amount_token_0: int,
        amount_token_1: int,
        amount_token_0_min: int,
        amount_token_1_min: int,
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Add liquidity to a liquidity pool where both underlyings are tokens.

        Args:
            token_0: The address of the first token to add.
            token_1: The address of the second token to add.
            amount_token_0: The amonut of the first token to add.
            amount_token_1: The amount of the second token to add.
            amount_token_0_min: The minimum amount of the first token to add.
            amount_token_1_min: The minimum amount of the second token to add.
            to: The recipient of the lp tokens.
            deadline: The deadline before the transaction is voided.

        Returns:
            The list of encoded fund transactions.
        """
        allowance_data_0 = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_token_0
        )
        allowance_data_1 = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_token_1
        )
        call_data = self.router.encode_abi(
            "addLiquidity",
            token_0,
            token_1,
            amount_token_0,
            amount_token_1,
            amount_token_0_min,
            amount_token_1_min,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.TOKEN, token_0, allowance_data_0),
            FundTxn(CallType.TOKEN, token_1, allowance_data_1),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data),
            FundTxn(CallType.TOKEN, token_0, unapprove_data),
            FundTxn(CallType.TOKEN, token_1, unapprove_data),
        ]

    def remove_liquidity_eth(
        self,
        lp_token: str,
        token: str,
        amount_lp_token: int,
        amount_token_min: int,
        amount_eth_min: int,
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Removes liquidity from a liquidity pool where ETH is one of the underlying.

        Args:
            lp_token: The lp token to be returned to redeem the underlyings.
            token: The address of the token to remove.
            amount_lp_token: The amount of the lp token to return.
            amount_token_min: The minimum amount of the token to remove.
            amount_eth_min: The minimum amount of eth to remove.
            to: The recipient of the lp tokens.
            deadline: The deadline before the transaction is voided.

        Returns:
            The list of encoded fund transactions.
        """
        approve_data = self.erc20.encode_abi(
            "approve", self.config.router, amount_lp_token
        )
        call_data = self.router.encode_abi(
            "removeLiquidityETH",
            token,
            amount_lp_token,
            amount_token_min,
            amount_eth_min,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.PROTOCOL, lp_token, approve_data),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data),
            FundTxn(CallType.PROTOCOL, lp_token, unapprove_data),
        ]

    def remove_liquidity(
        self,
        lp_token: str,
        token_0: str,
        token_1: str,
        amount_lp_token: int,
        amount_token_0_min: int,
        amount_token_1_min: int,
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Removes liquidity from a liquidity pool where both underlyings are tokens.

        Args:
            lp_token: The lp token to be returned to redeem the underlyings.
            token_0: The address of the first token to remove.
            token_1: The address of the second token to remove.
            amount_lp_token: The amount of the lp token to return.
            amount_token_0_min: The minimum amount of the first token to get back.
            amount_token_1_min: The minimum amount of the second token to get back.
            to: The recipient of the underlying tokens.
            deadline: The deadline before the transaction is voided.

        Returns:
            The list of encoded fund transactions.
        """
        approve_data = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_lp_token
        )
        call_data = self.router.encode_abi(
            "removeLiquidity",
            token_0,
            token_1,
            amount_lp_token,
            amount_token_0_min,
            amount_token_1_min,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.PROTOCOL, lp_token, approve_data),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data),
            FundTxn(CallType.PROTOCOL, lp_token, unapprove_data),
        ]

    def farm(self, pid: int, lp_token: str, amount_lp_token: int) -> FundTxns:
        """
        Deposits the lp tokens to farm.

        Args:
            pid: The id of the pair recorded in the masterchef.
            lp_token: The address of the lp token to farm.
            amount_lp_token: The amount of lp tokens to farm.

        Returns:
            The list of encoded fund transactions.
        """
        approve_data = self.erc20.encode_abi(
            "approve", self.config.master_chef_v2, amount_lp_token
        )
        call_data = self.master_chef_v2.encode_abi("deposit", pid, amount_lp_token)
        unapprove_data = self.erc20.encode_abi("approve", self.config.master_chef_v2, 0)

        return [
            FundTxn(CallType.PROTOCOL, lp_token, approve_data),
            FundTxn(CallType.PROTOCOL, self.config.master_chef_v2, call_data),
            FundTxn(CallType.PROTOCOL, lp_token, unapprove_data),
        ]

    def unfarm(self, pid: int, amount_lp_token: int) -> FundTxns:
        """
        Withdraws the lp tokens to stop farming.

        Args:
            pid: The id of the pair recorded in the masterchef.
            amount_lp_token: The amount of lp tokens to unfarm.

        Returns:
            The list of encoded fund transactions.
        """
        call_data = self.master_chef_v2.encode_abi("withdraw", pid, amount_lp_token)

        return [FundTxn(CallType.PROTOCOL, self.config.master_chef_v2, call_data, 0)]
