# Code
from sdk.base.encoders.contract import BaseContractEncoder


class WEthEncoder(BaseContractEncoder):
    """
    Specialized encoder for the WETH interface.
    """

    def __init__(self) -> None:
        super().__init__(dir_path=__file__)
