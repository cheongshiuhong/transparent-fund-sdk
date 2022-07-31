# Standard libraries
from __future__ import annotations
from typing import TypeVar, Generic, Any
from copy import deepcopy

# Code
from sdk.lib.models import FrozenModel, FrozenGenericModel
from sdk.lib.numbers import Number, LongShortNumbers


class PositionsDict(dict[str, LongShortNumbers]):
    """
    Extended dictionary that facilitates adding positions together.
    """

    def __iadd__(self, other: PositionsDict) -> PositionsDict:
        for symbol, amount in other.items():
            self[symbol] = self.get(symbol) + amount
        return self

    def __add__(self, other: PositionsDict) -> PositionsDict:
        copy = PositionsDict(self)
        copy += other
        return copy

    def get(self, key: str) -> LongShortNumbers:  # type: ignore[override]
        return super().get(key, LongShortNumbers())

    def dict(self) -> dict[str, Any]:
        return {key: value.dict() for key, value in self.items()}


class PricedNetPosition(FrozenModel):
    """
    Priced position with the amount and value as the net scalar number.
    """

    amount: Number = Number()
    value: Number = Number()


class PricedPosition(FrozenModel):
    """
    Priced position with the amount and value as detailed long-short numbers.
    """

    amount: LongShortNumbers = LongShortNumbers()
    value: LongShortNumbers = LongShortNumbers()

    def __add__(self, other: PricedPosition) -> PricedPosition:
        return PricedPosition(
            amount=self.amount + other.amount, value=self.value + other.value
        )


class PricedPositionsDict(dict[str, PricedPosition]):
    """
    Dictionary of priced positions.
    """

    """
    Extended dictionary that facilitates adding positions together.
    """

    def deepcopy(self) -> PricedPositionsDict:
        return deepcopy(self)

    def __iadd__(self, other: PricedPositionsDict) -> PricedPositionsDict:
        for symbol, amount in other.items():
            self[symbol] = self.get(symbol, PricedPosition()) + amount
        return self

    def __add__(self, other: PricedPositionsDict) -> PricedPositionsDict:
        copy = self.deepcopy()
        copy += other
        return copy

    def dict(self) -> dict[str, Any]:
        return {key: value.dict() for key, value in self.items()}


TDetails = TypeVar("TDetails", bound=FrozenModel)


class ProtocolReport(FrozenGenericModel, Generic[TDetails]):
    """
    Extended positions report to include generic protocol-specific details.
    """

    positions: PositionsDict
    details: TDetails


class ChainReport(FrozenGenericModel, Generic[TDetails]):
    """
    Composed positions report for an entire chain.
    """

    total: PositionsDict
    holdings: PositionsDict
    protocols: dict[str, ProtocolReport[TDetails]]


class PricedReport(FrozenGenericModel):
    """
    Aggregated priced positions with the aggregated value across positions.
    """

    value: LongShortNumbers
    positions: PricedPositionsDict


TPricedDetails = TypeVar("TPricedDetails")


class ProtocolPricedReport(PricedReport, Generic[TPricedDetails]):
    """
    Extended positions report to include generic protocol-specific details.
    """

    details: TPricedDetails


class ChainPricedReport(FrozenGenericModel, Generic[TPricedDetails]):
    """
    Composed positions report for an entire chain.
    """

    total: PricedReport
    holdings: PricedReport
    protocols: dict[str, ProtocolPricedReport[TPricedDetails]]
