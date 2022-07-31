# Standard libraries
from typing import Callable, Any

# Code
from ..configs import BaseConfig, BaseTokenConfig
from .contract import BaseContractEncoder


class BaseProtocolEncoder:
    """
    Base encoder class to represent a procotol, composing its smart contract(s),
    for the purpose of encoding high-level transactions.
    """

    config: BaseConfig

    def __init__(self, config: BaseConfig):
        self.config = config

    def _get_contract_encoder_partial(
        self, dir_path: str
    ) -> Callable[[Any], BaseContractEncoder]:
        return lambda *args, **kwargs: self._get_contract_encoder(
            dir_path, *args, **kwargs
        )

    def _get_contract_encoder(
        self, dir_path: str, abi_path: str = ""
    ) -> BaseContractEncoder:
        return BaseContractEncoder(dir_path=dir_path, abi_path=abi_path)

    def _is_eth(self, symbol: str) -> bool:
        result: bool = symbol == self.config.ETH or symbol == self.config.WETH
        return result

    def _get_token(self, symbol: str) -> BaseTokenConfig:
        # Guard against calls for ETH directly
        if symbol == self.config.ETH:
            return self.config.tokens[self.config.WETH]

        try:
            return self.config.tokens[symbol]
        except KeyError:
            raise ValueError(f"{symbol} is not a known token.")

    def _get_token_address(self, symbol: str) -> str:
        result: str = self._get_token(symbol).address
        return result
