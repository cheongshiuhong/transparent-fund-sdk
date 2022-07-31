# Standard libraries
from typing import Literal

# Code
from sdk.lib.models import FrozenModel


class ChainlinkPricingConfig(FrozenModel):
    """
    The config type for the chainlink oracle pricing strategy.
    """

    id: Literal["chainlink"]
    address: str
