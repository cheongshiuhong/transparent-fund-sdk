# Standard libraries
from typing import Union
import os

# Code
from sdk.lib.models import FrozenModel
from sdk.base.configs import GenericChainConfig
from sdk.base.configs.prices import ChainlinkPricingConfig
from .prices.pancakeswap import PancakeswapPricingConfig
from .protocols.pancakeswap import PancakeswapConfig
from .protocols.venus import VenusConfig


BscPricingConfig = Union[ChainlinkPricingConfig, PancakeswapPricingConfig]


class BscProtocolsConfig(FrozenModel):
    pancakeswap: PancakeswapConfig
    venus: VenusConfig


class BscConfig(GenericChainConfig[BscPricingConfig, BscProtocolsConfig]):
    def __init__(
        self, config_path: str = "configs/bsc", rpc_uri: str = "", wss_uri: str = ""
    ):
        super().__init__(config_path, rpc_uri, wss_uri, "BNB", "WBNB")
