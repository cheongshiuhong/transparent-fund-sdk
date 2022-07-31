from typing import NamedTuple


class CallType:
    TOKEN = 0
    PROTOCOL = 1
    UTIL = 2


class FundTxn(NamedTuple):
    call_type: int
    call_address: str
    call_data: bytes
    value: int = 0


FundTxns = list[FundTxn]
