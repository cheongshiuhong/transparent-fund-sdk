# Standard libraries
from typing import Literal, Union

# Code
from sdk.lib.models import FrozenModel


class PancakeswapPricingConfig(FrozenModel):
    id: Literal["pancakeswap"]
    address: str
    index: Union[Literal[0], Literal[1]]
    quote: str
