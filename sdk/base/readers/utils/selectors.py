# 3rd party libraries
from eth_utils import keccak


def selector_from_sig(signature: str) -> bytes:
    """
    Hashes the signature to get the selector.

    Args:
        signature: The function signature.
    Returns:
        The bytes4 fucntion selector.
    """
    result: bytes = keccak(text=signature)[:4]
    return result
