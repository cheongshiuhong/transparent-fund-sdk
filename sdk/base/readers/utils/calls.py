# Standard libraries
from typing import Any, Sequence, Union
import json

# 3rd party libraries
from aiohttp import ClientSession
import eth_abi
import eth_utils


def encode_calldata(
    selector: bytes, types: Sequence[str], values: Sequence[Union[int, str, bytes]]
) -> bytes:
    """
    Encodes the selector and arguments into the calldata bytes.

    Args:
        selector: The selector bytes (first 4 bytes in keccak of signature).
        types: The list of types of the arguemnts to be encoded.
        types: The list of values of the arguemnts to be encoded.

    Returns:
        The bytes of the encoded calldata.
    """
    calldata: bytes = selector + eth_abi.encode_abi(types, values)
    return calldata


def decode_result(types: list[str], result: bytes) -> Sequence[Any]:
    """
    Decodes the result based on the types.

    Args:
        types: The list of types for the result to be decoded.
        result: The bytes of the result.

    Returns:
        The list of the decoded result values.
    """
    decoded_result: Sequence[Any]
    decoded_result = eth_abi.decode_abi(types, result)
    return decoded_result


async def call_eth_method(
    session: ClientSession,
    rpc_uri: str,
    method: str,
    params: Union[tuple[Union[str, dict[str, str]], ...], list[Union[str, dict[str, str]]]],
) -> str:
    """
    Performs an rpc call to the node provider for a given method and params.

    Args:
        session: The async client session.
        rpc_uri: The node provider's rpc endpoint.
        method: The eth method to call.
        params: The params for the rpc call.
    Returns:
        The raw hexadecimal result string.
    """
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    response = await session.post(rpc_uri, data=json.dumps(body))
    json_response = await response.json()
    result: str = json_response["result"]
    return result


async def make_eth_call(
    session: ClientSession, rpc_uri: str, to: str, data: bytes
) -> bytes:
    """
    Makes an eth_call to the node provider to perform
    a smart contract call to read the state.

    Args:
        session: The async client session.
        rpc_uri: The node provider's rpc endpoint.
        to: The contract to call.
        data: The encoded selector and arguments to make the call with.

    Returns:
        The response bytes.
    """
    params: list[Union[str, dict[str, str]]]
    params = [{"to": to, "data": eth_utils.encode_hex(data)}, "latest"]

    result = await call_eth_method(session, rpc_uri, "eth_call", params)
    result_bytes: bytes = eth_utils.decode_hex(result)

    return result_bytes


async def make_eth_storage_call(
    session: ClientSession, rpc_uri: str, to: str, slot: str
) -> bytes:
    """
    Makes an eth_getStorageAt call to the node porvider to perform
    a direct read from a contract's storage slot.

    Args:
        session: The async client session.
        rpc_uri: The node provider's rpc endpoint.
        to: The contract to read the storage of.
        slot: The slot identifer to read from.

    Returns:
        The response bytes.
    """
    params: tuple[str, str, str]
    params = (to, slot, "latest")

    result = await call_eth_method(session, rpc_uri, "eth_getStorageAt", params)
    result_bytes: bytes = eth_utils.decode_hex(result)

    return result_bytes
