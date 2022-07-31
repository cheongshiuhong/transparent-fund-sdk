# Code
from sdk.fund.types import CallType, FundTxn, FundTxns
from sdk.base.encoders import BaseProtocolEncoder
from sdk.chains.bsc.configs import BscConfig
from sdk.base.encoders.general.erc20 import Erc20Encoder


class VenusEncoder(BaseProtocolEncoder):
    """
    Composed encoder for the venus protocol.
    """

    def __init__(self, config: BscConfig):
        super().__init__(config)

        # For convenience
        self.protocol = config.protocols.venus
        self.tokens = config.tokens
        self.xvs_address = self._get_token_address("XVS")

        # Contract encoders
        get_contract_encoder = self._get_contract_encoder_partial(__file__)
        self.unitroller = get_contract_encoder("abis/unitroller.json")
        self.comptroller_g5 = get_contract_encoder("abis/comptroller_g5.json")
        self.vbnb = get_contract_encoder("abis/vbnb.json")
        self.vbep20 = get_contract_encoder("abis/vbep20.json")
        self.erc20 = Erc20Encoder()

    # --------------
    # Main methods
    # --------------
    def claim_rewards(self) -> FundTxns:
        """
        Claims the accurued XVS rewards.

        Returns:
            The list of encoded fund transactions.
        """
        call_data = self.comptroller_g5.encode_abi(
            "claimVenus", self.config.fund_address
        )
        return [FundTxn(CallType.PROTOCOL, self.protocol.unitroller, call_data)]

    def enter_markets(self, token_symbols: list[str]) -> FundTxns:
        """
        Enters the markets for the input list of tokens.

        Args:
            token_symbols: The list of token symbols to enter markets for.

        Returns:
            The list of encoded fund transactions.
        """
        # Lookup pool addresses
        addresses = [self.__get_pool_address(symbol) for symbol in token_symbols]

        call_data = self.comptroller_g5.encode_abi("enterMarkets", addresses)

        return [FundTxn(CallType.PROTOCOL, self.protocol.unitroller, call_data)]

    def exit_markets(self, token_symbols: list[str]) -> FundTxns:
        """
        Exits the markets for the input list of tokens.

        Args:
            token_symbols: The list of token symbols to enter markets for.

        Returns:
            The list of encoded fund transactions.
        """
        # Lookup pool addresses
        addresses = [self.__get_pool_address(symbol) for symbol in token_symbols]

        return [
            FundTxn(
                CallType.PROTOCOL,
                self.protocol.unitroller,
                self.comptroller_g5.encode_abi("exitMarket", address),
            )
            for address in addresses
        ]

    def supply(self, token_symbol: str, amount: int) -> FundTxns:
        """
        Supplies/lends a token.

        Args:
            token_symbol: The symbol of the token to supply/lend.
            amount: The amonut to supply/lend.

        Returns:
            The list of encoded fund transactions.
        """
        if self._is_eth(token_symbol):
            call_data = self.vbnb.encode_abi("mint")
            return [
                FundTxn(
                    CallType.PROTOCOL,
                    self.__get_pool_address(self.config.ETH),
                    call_data,
                    amount,
                )
            ]

        pool_address = self.__get_pool_address(token_symbol)
        token_address = self._get_token_address(token_symbol)

        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", pool_address, amount
        )
        call_data = self.vbep20.encode_abi("mint", amount)
        unapprove_data = self.erc20.encode_abi("approve", pool_address, 0)

        return [
            FundTxn(CallType.TOKEN, token_address, allowance_data),
            FundTxn(CallType.PROTOCOL, pool_address, call_data),
            FundTxn(CallType.TOKEN, token_address, unapprove_data),
        ]

    def redeem(self, token_symbol: str, amount: int) -> FundTxns:
        """
        Redeems a supplied/lent token.

        Args:
            token_symbol: The symbol of the token to redeem.
            amount: The amonut to redeem.

        Returns:
            The list of encoded fund transactions.
        """
        contract = self.vbnb if self._is_eth(token_symbol) else self.vbep20
        call_data = contract.encode_abi("redeemUnderlying", amount)

        return [
            FundTxn(CallType.PROTOCOL, self.__get_pool_address(token_symbol), call_data)
        ]

    def borrow(self, token_symbol: str, amount: int) -> FundTxns:
        """
        Borrows a token.

        Args:
            token_symbol: The symbol of the token to borrow.
            amount: The amonut to borrow.

        Returns:
            The list of encoded fund transactions.
        """
        contract = self.vbnb if self._is_eth(token_symbol) else self.vbep20
        call_data = contract.encode_abi("borrow", amount)

        return [
            FundTxn(CallType.PROTOCOL, self.__get_pool_address(token_symbol), call_data)
        ]

    def repay(self, token_symbol: str, amount: int) -> FundTxns:
        """
        Repays a borrowed token.

        Args:
            token_symbol: The symbol of the token to repay.
            amount: The amonut to repay.

        Returns:
            The list of encoded fund transactions.
        """
        if self._is_eth(token_symbol):
            call_data = self.vbnb.encode_abi("repayBorrow")
            return [
                FundTxn(
                    CallType.PROTOCOL,
                    self.__get_pool_address(self.config.ETH),
                    call_data,
                    amount,
                )
            ]

        pool_address = self.__get_pool_address(token_symbol)
        token_address = self._get_token_address(token_symbol)

        allowance_data = self.erc20.encode_abi(
            "increaseAllowance", pool_address, amount
        )
        call_data = self.vbep20.encode_abi("repayBorrow", amount)
        unapprove_data = self.erc20.encode_abi("approve", pool_address, 0)

        return [
            FundTxn(CallType.TOKEN, token_address, allowance_data),
            FundTxn(CallType.PROTOCOL, pool_address, call_data),
            FundTxn(CallType.TOKEN, token_address, unapprove_data),
        ]

    # -----------------
    # Private methods
    # -----------------
    def __get_pool_address(self, symbol: str) -> str:
        try:
            result: str = self.protocol.pools[symbol]
            return result
        except KeyError:
            raise ValueError(f"{symbol} does not have a lending pool")
