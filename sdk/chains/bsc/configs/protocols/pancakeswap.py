# Code
from sdk.lib.models import FrozenModel


class PancakeswapPairConfig(FrozenModel):
    address: str
    pid: int


class PancakeswapConfig(FrozenModel):
    cake_pool: str
    smart_chefs: dict[str, str]
    master_chef_v2: str
    router: str
    pairs: dict[str, PancakeswapPairConfig]
