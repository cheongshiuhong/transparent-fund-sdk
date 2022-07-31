# 3rd party libraries
from eth_account.account import LocalAccount, SignedTransaction
from web3 import Web3
from web3.contract import Contract, ChecksumAddress
from hexbytes import HexBytes

# Code
from sdk.lib.utils import load_abi
from sdk.lib.logger import SdkLogger
from sdk.base.configs import BaseConfig
from sdk.base.connector import BaseConnector
from .types import FundTxn


# Constants
DEFAULT_GAS_PER_TXN = 180_000


class Fund:
    """
    Facilitates the transactions with the fund via call/multi_call
    """

    config: BaseConfig
    connector: BaseConnector
    __operator: LocalAccount
    __contract: Contract
    __logger: SdkLogger

    def __init__(self, config: BaseConfig, connector: BaseConnector, operator_key: str):
        self.config = config
        self.connector = connector
        self.__operator = connector.connection.eth.account.from_key(operator_key)
        self.__contract = connector.connection.eth.contract(
            address=config.fund_address, abi=load_abi(__file__)
        )
        self.__logger = SdkLogger(f"{self.__class__.__name__}")

        assert self.connector.is_connected()

    @property
    def address(self) -> ChecksumAddress:
        return self.__contract.address

    def call(
        self, txn: FundTxn, gas_limit: int = 0, gas_price: int = Web3.toWei(5, "gwei")
    ) -> HexBytes:
        """
        Sends a transction via call

        Args:
            txn: The encoded transaction to send.
            gas_limit: The maximum gas to consume.
            gas_price: The cost per unit of gas in gwei.
        Returns:
            The transaction hash.
        """
        # If gas limit is not set, overquote with {DEFAULT_GAS_PER_TXN} * num txns
        if gas_limit == 0:
            gas_limit = DEFAULT_GAS_PER_TXN

        # Convert the struct back to a regular tuple for a single txn
        call_data = self.__contract.encodeABI("call", tuple(txn))
        signed_txn = self.__sign(call_data, gas_limit, gas_price)

        self.__logger.info(f"Sending [call] transaction to {txn.call_address}")
        self.__logger.debug("Call Data: {!r}".format(txn.call_data))
        self.__logger.debug(f"Value: {txn.value}")

        return self.connector.connection.eth.send_raw_transaction(
            signed_txn.rawTransaction
        )

    def multi_call(
        self,
        txns: list[FundTxn],
        gas_limit: int = 0,
        gas_price: int = Web3.toWei(5, "gwei"),
        name_in_logs: str = "No Name",
    ) -> HexBytes:
        """
        Sends the list of transactions via multi call

         Args:
            txns: The list of encoded transctions to send.
            gas_limit: The maximum gas to consume.
            gas_price: The cost per unit of gas in gwei.
            name_in_logs: The name of this group of calls to show in the logs.
         Returns:
            The transaction hash.
        """
        # If gas limit is not set, overquote with {DEFAULT_GAS_PER_TXN} * num txns
        if gas_limit == 0:
            gas_limit = DEFAULT_GAS_PER_TXN * len(txns)

        call_data = self.__contract.encodeABI("multiCall", [txns])
        signed_txn = self.__sign(call_data, gas_limit, gas_price)

        self.__logger.info(f"Name of Call: {name_in_logs}")
        self.__logger.info(
            f"Sending [multiCall] transaction to {[txn.call_address for txn in txns]}"
        )
        self.__logger.debug(f"Call Datas: {[txn.call_data for txn in txns]}")
        self.__logger.debug(f"Values: {[txn.value for txn in txns]}")

        return self.connector.connection.eth.send_raw_transaction(
            signed_txn.rawTransaction
        )

    # -----------------
    # Private methods
    # -----------------
    def __sign(
        self, call_data: bytes, gas_limit: int, gas_price: int
    ) -> SignedTransaction:
        return self.__operator.sign_transaction(
            {
                "nonce": self.connector.connection.eth.get_transaction_count(
                    self.__operator.address
                ),
                "from": self.__operator.address,
                "to": self.address,
                "data": call_data,
                "gas": gas_limit,
                "gasPrice": gas_price,
            }
        )
