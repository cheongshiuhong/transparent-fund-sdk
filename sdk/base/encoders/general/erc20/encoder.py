# Code
from sdk.base.encoders.contract import BaseContractEncoder


class Erc20Encoder(BaseContractEncoder):
    """
    Specialized encoder for the ERC-20 interface.
    """

    def __init__(self) -> None:
        super().__init__(dir_path=__file__)
