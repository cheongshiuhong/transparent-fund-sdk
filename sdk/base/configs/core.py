# Standard libraries
from typing import TypeVar, Generic, Mapping
from pathlib import Path
import os

# 3rd party libraries
import yaml

# Code
from sdk.lib.models import FrozenGenericModel
from .tokens import BasePricingConfig, TPricingConfig, GenericTokenConfig


class BaseConfig(FrozenGenericModel):
    """
    The base config of fields that should be present regardless of chain.

    NOTE: Should only be used as a type in non-chain specific code.
          Use the `GenericChainConfig` class for chain-specific specializations.
    """

    # Environments
    rpc_uri: str
    wss_uri: str
    # Specialized by child config class
    ETH: str
    WETH: str
    # Core config
    multicall_address: str
    fund_address: str
    fund_utils: dict[str, str]
    # Tokens config (mapping allows covariance)
    tokens: Mapping[str, GenericTokenConfig[BasePricingConfig]]


TProtocolsConfig = TypeVar("TProtocolsConfig")


class GenericChainConfig(BaseConfig, Generic[TPricingConfig, TProtocolsConfig]):
    """
    The generic chain config that allows the token and protocol
    fields types to be specialized for a specific chain.
    """

    tokens: Mapping[str, GenericTokenConfig[TPricingConfig]]
    protocols: TProtocolsConfig

    def __init__(
        self, config_path: str, rpc_uri: str, wss_uri: str, ETH: str, WETH: str
    ):
        config_path_obj = Path(config_path)

        with open(config_path_obj / "core.yaml", "r") as f:
            core_config = yaml.load(f, yaml.Loader)

        with open(config_path_obj / "tokens.yaml", "r") as f:
            tokens_config = yaml.load(f, yaml.Loader)

        # Map the ETH token to WETH
        tokens_config[ETH] = tokens_config[WETH]

        protocols_configs = {}
        for file_name in os.listdir(config_path_obj / "protocols"):
            split_file_name = file_name.split(".")

            # Skip if not a yaml file
            if split_file_name[-1] != "yaml":
                continue

            protocol_name = split_file_name[0]
            with open(config_path_obj / "protocols" / file_name, "r") as f:
                protocols_configs[protocol_name] = yaml.load(f, yaml.Loader)

        super().__init__(
            rpc_uri=rpc_uri,
            wss_uri=wss_uri,
            ETH=ETH,
            WETH=WETH,
            **core_config,
            tokens=tokens_config,
            protocols=protocols_configs,
        )
