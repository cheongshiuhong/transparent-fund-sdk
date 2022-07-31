# Code
from sdk.lib.models import FrozenModel


class VenusConfig(FrozenModel):
    unitroller: str
    lens: str
    pools: dict[str, str]
