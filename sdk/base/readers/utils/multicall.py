# 3rd party libraries
from eth_abi import encode_abi, decode_abi
from eth_utils import keccak

# Code
from .selectors import selector_from_sig

# Constants
MULTICALL_AGGREGATE_SELECTOR = selector_from_sig("aggregate((address,bytes)[])")
MULTICALL_AGGREGATE_INPUT_TYPES = ["(address,bytes)[]"]
MULTICALL_AGGREAGTE_OUTPUT_TYPES = ["uint256", "bytes[]"]


def encode_multicall_inputs(calls: list[tuple[str, bytes]]) -> bytes:
    """
    Encodes the list of calls into a single multicall.

    Args:
        calls: The list of tuple of each call's address and calldata
    Returns:
        The combined calldata for a multicall.
    """
    calldata: bytes = MULTICALL_AGGREGATE_SELECTOR + encode_abi(
        MULTICALL_AGGREGATE_INPUT_TYPES, [calls]
    )
    return calldata


def decode_multicall_result(output: bytes) -> tuple[int, list[bytes]]:
    """
    Decodes the output bytes into the block number
    and a list of individual call output bytes.

    Args:
        output: The multicall output.

    Returns:
        The block number and list of the individual call's output bytes.
    """
    decoded_result: tuple[int, list[bytes]] = decode_abi(
        MULTICALL_AGGREAGTE_OUTPUT_TYPES, output
    )
    return decoded_result
