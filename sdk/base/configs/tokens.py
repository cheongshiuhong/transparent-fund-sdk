# Standard libraries
from typing import Generic, TypeVar

# Code
from sdk.lib.models import FrozenModel, FrozenGenericModel


class BasePricingConfig(FrozenModel):
    """
    Base pricing config with an id to specify
    which pricing strategy to adopt.
    """

    id: str


TPricingConfig = TypeVar("TPricingConfig", bound=BasePricingConfig, covariant=True)


class GenericTokenConfig(FrozenGenericModel, Generic[TPricingConfig]):
    """
    Generic token config whose pricing field is of generic type
    depending on the strategy used to price the token.
    """

    address: str
    decimals: int
    pricing: TPricingConfig


BaseTokenConfig = GenericTokenConfig[BasePricingConfig]
