# Standard libraries
from typing import Any, Type

# 3rd party libraries
from web3.contract import Contract
import web3

# Code
from sdk.lib.utils import load_abi


class BaseContractEncoder:
    """
    Base encoder class to represent a smart contract,
    for the purpose of encoding transactions without maintaining a connection.
    """

    _contract: Type[Contract]

    def __init__(self, dir_path: str, abi_path: str = ""):
        # Load the ABI from the file's directory
        abi = load_abi(dir_path, abi_path)

        # Load the address-less contract object
        self._contract = web3.Web3().eth.contract(abi=abi)

    def encode_abi(
        self, fn_name: str, *args: tuple[Any], **kwargs: dict[str, Any]
    ) -> str:
        """
        Encodes a function's call with its selector and the encoded arguments

        Args:
            fn_name: The name of the function.
            args: The tuple of arguments to encode.
        Returns:
            The the hexadecimal string representation of the encoded calldata.
        """
        result: str = self._contract.encodeABI(fn_name, args=args, kwargs=kwargs)
        return result
