# Standard libraries
from typing import Union

# Code
from sdk.chains.bsc.readers.protocols.pancakeswap.types import (
    PancakeswapDetails,
    PancakeswapPricedDetails,
)
from sdk.chains.bsc.readers.protocols.venus.types import (
    VenusDetails,
    VenusPricedDetails,
)
from sdk.base.readers.aggregator import BaseAggregator


BscDetails = Union[PancakeswapDetails, VenusDetails]
BscPricedDetails = Union[PancakeswapPricedDetails, VenusPricedDetails]
IBscAggregator = BaseAggregator[BscDetails, BscPricedDetails]
