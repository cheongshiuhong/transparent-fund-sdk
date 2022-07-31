# Standard libraries
from __future__ import annotations
from copy import deepcopy
from typing import TypedDict

# 3rd party libraries
from pydantic import BaseModel


class NumberDict(TypedDict):
    """
    The return type upon calling `.dict()` on the struct.
    """

    value: str
    decimals: int


class Number(BaseModel):
    """
    Core struct that performs operations on integers
    with decimals separately tracked.

    NOTE:
        For addition/subtraction operations, decimals of the
        higher precision input will be retained.
        For multiplication/division, decimals of the
        FIRST value will be retained (self).
    """

    # Pydantic ensures these are non-static
    value: int = 0
    decimals: int = 0

    def set_decimals(self, target: int) -> Number:
        """
        Scale the value up or down by the target decimals.

        NOTE: Value will be rounded when scaling down.
        """
        # Scale down
        if self.decimals >= target:
            # e.g., (18_888, 3) --> (189, 1)
            rounded = round(self.value, target - self.decimals)
            self.value = rounded // 10 ** (self.decimals - target)
        # Scale up
        else:
            self.value = self.value * 10 ** (target - self.decimals)

        # Update the decimals
        self.decimals = target

        # Make chainable
        return self

    def __add(self, value: int, decimals: int) -> None:
        """
        Private method to facilitate both addition and subtractions,
        preserving the higher decimals precision of
        the current instance and the input decimals.
        """
        if self.decimals >= decimals:
            adjusted_other_value = value * 10 ** (self.decimals - decimals)
            self.value += adjusted_other_value
            return

        adjusted_self_value = self.value * 10 ** (decimals - self.decimals)
        self.value = adjusted_self_value + value
        self.decimals = decimals

    def __add__(self, other: Number) -> Number:
        copy = self.copy()
        copy += other
        return copy

    def __iadd__(self, other: Number) -> Number:
        self.__add(other.value, other.decimals)
        return self

    def __sub__(self, other: Number) -> Number:
        copy = self.copy()
        copy -= other
        return copy

    def __isub__(self, other: Number) -> Number:
        self.__add(-other.value, other.decimals)
        return self

    def __mul__(self, other: Number) -> Number:
        """
        Multiplies with the other number, preserving the
        current value's decimals precision.
        """
        copy = self.copy()
        copy *= other
        return copy

    def __imul__(self, other: Number) -> Number:
        """
        Multiplies with the other number, preserving the
        current value's decimals precision.
        """
        self.value = self.value * other.value // 10**other.decimals
        return self

    def __floordiv__(self, other: Number) -> Number:
        """
        Divides with the other value, preserving the
        current value's decimals precision
        """
        return Number(
            value=self.value * 10**other.decimals // other.value,
            decimals=self.decimals,
        )

    def __bool__(self) -> bool:
        return bool(self.value)

    def __float__(self) -> float:
        result: float = self.value / 10**self.decimals
        return result


class LongShortNumbers(BaseModel):
    # Pydantic ensures these are non-static
    net: Number = Number()
    long: Number = Number()
    short: Number = Number()

    def deepcopy(self) -> LongShortNumbers:
        return deepcopy(self)

    def __add__(self, other: LongShortNumbers) -> LongShortNumbers:
        copy = self.deepcopy()
        copy += other
        return copy

    def __iadd__(self, other: LongShortNumbers) -> LongShortNumbers:
        self.net += other.net
        self.long += other.long
        self.short += other.short
        return self

    def broadcast_mul(self, price: Number) -> LongShortNumbers:
        copy = self.deepcopy()
        copy.net *= price
        copy.long *= price
        copy.short *= price

        # Make chainable
        return copy
