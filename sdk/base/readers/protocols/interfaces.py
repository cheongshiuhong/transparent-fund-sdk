# Standard libraries
from abc import ABC, abstractmethod
from typing import Generic

# 3rd party libraries
from aiohttp import ClientSession

# Code
from sdk.base.readers.structs import (
    TDetails,
    TPricedDetails,
    ProtocolReport,
    ProtocolPricedReport,
)
from sdk.base.readers.prices.interfaces import IPriceResolver


class IProtocolReportReader(ABC, Generic[TDetails, TPricedDetails]):
    """
    Interface for the protocol report reader.
    """

    @abstractmethod
    async def get_report(self, session: ClientSession) -> ProtocolReport[TDetails]:
        """
        Protocol report readers should implement
        the method to retrieve the report.
        """

    @abstractmethod
    async def get_priced_report(
        self, price_resolver: IPriceResolver, session: ClientSession
    ) -> ProtocolPricedReport[TPricedDetails]:
        """
        Protocol report readers should implement
        the method to retrieve the priced report.
        """
