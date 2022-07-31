# Code
from sdk.base.readers.prices import ChainlinkPriceReader
from sdk.chains.bsc.configs import BscConfig
from sdk.chains.bsc.readers.prices.pancakeswap.reader import PancakeswapPriceReader
from sdk.chains.bsc.readers.protocols.pancakeswap.reader import PancakeswapReportReader
from sdk.chains.bsc.readers.protocols.venus.reader import VenusReportReader
from .types import IBscAggregator


class BscAggregator(IBscAggregator):
    """
    Specialized aggregator for bsc.
    """

    def __init__(self, config: BscConfig) -> None:
        protocol_report_readers = {
            "pancakeswap": PancakeswapReportReader(config),
            "venus": VenusReportReader(config),
        }
        price_readers = [ChainlinkPriceReader(config), PancakeswapPriceReader(config)]
        super().__init__(
            config=config,
            protocol_report_readers=protocol_report_readers,
            price_readers={reader.id: reader for reader in price_readers},
        )
