# Code
from sdk.fund.types import CallType, FundTxn, FundTxns
from sdk.base.encoders import BaseContractEncoder
from sdk.base.encoders.general.erc20 import Erc20Encoder
from sdk.chains.bsc.configs.protocols.pancakeswap import PancakeswapConfig


class PancakeswapSwapHelper:
    """
    Helper for pancakeswap calls regarding swaps.
    """

    def __init__(
        self,
        config: PancakeswapConfig,
        router: BaseContractEncoder,
        erc20: Erc20Encoder,
    ):
        self.config = config
        self.router = router
        self.erc20 = erc20

    def swap_eth_for_exact_tokens(
        self,
        amount_eth_max: int,
        amount_token_exact: int,
        path: list[str],
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Swaps eth for tokens where token amount is exact.

        Args:
            amount_eth_max: The max amount of eth to be used in the swap.
            amount_token_exact: The exact amount of token to be received.
            path: The token swap path.
            to: The recipient of the output tokens.
            deadline: The deadline before the transaction is voided.

        Returns:
            The list of encoded fund transactions.
        """
        call_data = self.router.encode_abi(
            "swapETHForExactTokens", amount_token_exact, path, to, deadline
        )

        return [
            FundTxn(
                CallType.PROTOCOL, self.config.router, call_data, value=amount_eth_max
            )
        ]

    def swap_exact_eth_for_tokens(
        self,
        amount_eth_exact: int,
        amount_token_min: int,
        path: list[str],
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Swaps eth for tokens where eth amount is exact.

        Args:
            amount_eth_exact: The exact amount of eth to be used in the swap.
            amount_token_min: The min amount of token to be received.
            path: The token swap path.
            to: The recipient of the output tokens.
            deadline: The deadline before the transaction is voided.

        Returns:
            The list of encoded fund transactions.
        """
        call_data = self.router.encode_abi(
            "swapExactETHForTokens", amount_token_min, path, to, deadline
        )
        return [
            FundTxn(
                CallType.PROTOCOL, self.config.router, call_data, value=amount_eth_exact
            )
        ]

    def swap_tokens_for_exact_eth(
        self,
        amount_token_max: int,
        amount_eth_exact: int,
        path: list[str],
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Swaps tokens for eth where eth amount is exact.

        Args:
            amount_token_max: The max amount of tokens to be used in the swap.
            amount_eth_exact: The exact amount of eth to be received.
            path: The token swap path.
            to: The recipient of the output token.
            deadline: The deadline before the transactions is voided.

        Returns:
            The list of encoded fund transactions.
        """
        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_token_max
        )
        call_data = self.router.encode_abi(
            "swapTokensForExactETH",
            amount_eth_exact,
            amount_token_max,
            path,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.TOKEN, path[0], allowance_data),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data),
            FundTxn(CallType.TOKEN, path[0], unapprove_data),
        ]

    def swap_exact_tokens_for_eth(
        self,
        amount_token_exact: int,
        amount_eth_min: int,
        path: list[str],
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Swaps tokens for eth where token amount is exact.

        Args:
            amount_token_exact: The exact amount of tokens to be used in the swap.
            amount_eth_min: The min amount of eth to be received.
            path: The token swap path.
            to: The recipient of the output token.
            deadline: The deadline before the transactions is voided.

        Returns:
            The list of encoded fund transactions.
        """
        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_token_exact
        )
        call_data = self.router.encode_abi(
            "swapExactTokensForETH",
            amount_token_exact,
            amount_eth_min,
            path,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.TOKEN, path[0], allowance_data),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data),
            FundTxn(CallType.TOKEN, path[0], unapprove_data),
        ]

    def swap_tokens_for_exact_tokens(
        self,
        amount_token_0_max: int,
        amount_token_1_exact: int,
        path: list[str],
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Swaps tokens for tokens where token amount received is exact.

        Args:
            amount_token_0_max: The max amount of token 0 to be used in the swap.
            amount_token_1_exact: The exact amount of token 1 to be received.
            path: The token swap path.
            to: The recipient of the output token.
            deadline: The deadline before the transactions is voided.

        Returns:
            The list of encoded fund transactions.
        """
        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_token_0_max
        )
        call_data = self.router.encode_abi(
            "swapTokensForExactTokens",
            amount_token_1_exact,
            amount_token_0_max,
            path,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.TOKEN, path[0], allowance_data),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data),
            FundTxn(CallType.TOKEN, path[0], unapprove_data),
        ]

    def swap_exact_tokens_for_tokens(
        self,
        amount_token_0_exact: int,
        amount_token_1_min: int,
        path: list[str],
        to: str,
        deadline: int,
    ) -> FundTxns:
        """
        Swaps tokens for eth where token amount sent is exact.

        Args:
            amount_token_0_exact: The exact amount of token 0 to be used in the swap.
            amount_token_1_min: The min amount of token 1 to be received.
            path: The token swap path.
            to: The recipient of the output token.
            deadline: The deadline before the transactions is voided.

        Returns:
            The list of encoded fund transactions.
        """
        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", self.config.router, amount_token_0_exact
        )
        call_data = self.router.encode_abi(
            "swapExactTokensForTokens",
            amount_token_0_exact,
            amount_token_1_min,
            path,
            to,
            deadline,
        )
        unapprove_data = self.erc20.encode_abi("approve", self.config.router, 0)

        return [
            FundTxn(CallType.TOKEN, path[0], allowance_data),
            FundTxn(CallType.PROTOCOL, self.config.router, call_data),
            FundTxn(CallType.TOKEN, path[0], unapprove_data),
        ]
