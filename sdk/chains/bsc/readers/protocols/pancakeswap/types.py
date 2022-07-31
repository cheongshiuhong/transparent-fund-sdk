# Code
from sdk.lib.models import FrozenModel
from sdk.lib.numbers import Number
from sdk.base.readers.protocols import IProtocolReportReader
from sdk.base.readers.structs import (
    PricedNetPosition,
    ProtocolReport,
    ProtocolPricedReport,
)


class PancakeswapLpDetails(FrozenModel):
    holding: dict[str, Number]
    farming: dict[str, Number]
    total: dict[str, Number]


class PancakeswapDetails(FrozenModel):
    lps: dict[str, PancakeswapLpDetails]
    smart_chefs: dict[str, dict[str, Number]]


class PancakeswapLpPricedDetails(FrozenModel):
    holding: dict[str, PricedNetPosition]
    farming: dict[str, PricedNetPosition]
    total: dict[str, PricedNetPosition]


class PancakeswapPricedDetails(FrozenModel):
    lps: dict[str, PancakeswapLpPricedDetails]
    smart_chefs: dict[str, dict[str, PricedNetPosition]]


IPancakeswapReportReader = IProtocolReportReader[
    PancakeswapDetails, PancakeswapPricedDetails
]
PancakeswapReport = ProtocolReport[PancakeswapDetails]
PancakeswapPricedReport = ProtocolPricedReport[PancakeswapPricedDetails]
