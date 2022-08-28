# Standard libraries
from typing import Union

# 3rd party libraries
from web3 import Web3
import eth_abi


def get_map_storage_address(
    key_type: str, key: Union[str, int], slot_number: int
) -> str:
    """
    Gets the storage address of a `mapping` in a contract.

    Args:
        key_type: The type of the mapping's key to encode.
        key: The value of the mapping's key to encode.
        slot_number: The slot of the mapping in the contract's storage layout.
    """
    encoded_key = eth_abi.encode_single(key_type, key)
    encoded_slot_number = eth_abi.encode_single("uint32", slot_number)
    result: str = Web3.sha3(encoded_key + encoded_slot_number).hex()
    return result


def increment_storage_address(storage_address: str, steps: int = 1) -> str:
    """
    Increments the storage address to the next 32 bytes slot.

    Args:
        storage_address: The address to increment.
        steps: The number of steps to increment by.

    Returns:
        The incremented storage address.
    """
    integer_address_value = int(storage_address, 16)
    result: str = Web3.toHex(integer_address_value + steps).to_bytes(32, "big")
    return result
