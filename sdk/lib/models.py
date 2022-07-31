# 3rd party libraries
from pydantic import BaseModel
from pydantic.generics import GenericModel


class FrozenModel(BaseModel):
    """
    Pydantic base model set to frozen.
    """

    class Config:
        frozen = True


class FrozenGenericModel(GenericModel):
    """
    Pydantic generic model set to frozen.
    """

    class Config:
        frozen = True
