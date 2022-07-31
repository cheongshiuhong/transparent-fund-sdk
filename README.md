# Transparent Fund Python SDK

Facilitates transactions with the fund and reading of states from the blockchain.

- [Transaction](#transacting)
    - [Encoders](#encoders)
    - [The Fund](#the-fund)
- [Reading](#reading)
    - [The Aggregator Interface](#the-aggregator-interface)
    - [Data](#data)
    - [Caveat](#caveat)
    - [How it works](#how-it-works)

<br><br>

# Transacting

Transactions are first encoded by encoders before being sent to the fund to execute atomically.

Example can be found in [`examples/local/transacting.py`](./examples/local/transacting.py)

<br>

## Encoders

Encoder classes provides protocol-level and util-level abstraction for each protocol.

E.g.,:
- PancakeswapEncoder
- VenusEncoder
- PancakeswapLpFarmingUtilEncoder

Transactions are first encoded into the `FunxTxn` struct by encoders, comprising:
- `call_type: CallType` - Enum to let the fund know how to call (0=TOKEN, 1=PROTOCOL, UTIL=2).
- `call_address: str` - The address for the fund to call.
- `call_data: bytes` - The encoded bytes calldata (selector + encoded arguments)
- `value: int` - The amount of `ETH` to be sent by the fund in the transaction.

Due to the nature of almost always requiring multiple calls, encoders return a list of `FundTxn`, labelled as type `FundTxns: list[FundTxn]`.

These calls can then be intuitively combined for high-level operations:

```python
borrowing_txns = borrowing_encoder.borrow(args)
selling_txns = selling_encoder.sell(args)
shorting_txns = borrowing_txns + selling_txns
```

<br>

## The Fund

The fund is the only component in this module that connects to the chain. It simply gathers the list of encoded transactions and sends them to the chain for atomic execution, handling the lower-level details like signing the transactions.

While we expect that most transactions will comprise multiple inner transactions as `FundTxns` instead of a single `FundTxn`, we provide both methods anyway:

1. `call(txn: FundTxn, gas_limit: int = DEFAULT_CONSTANT, gas_price: int = 5 gwei)`
2. `multi_call(txns: FundTxns, gas_limit: int = DEFAULT_CONSTANT, gas_price: int = 5 gwei, name_in_logs: str = "No Name")`



<br><br>

# Reading

Reading from the chain should be performed through the aggregator class (e.g., BscAggregator).

Example can be found in [`examples/bsc/reading.py`](./examples/bsc/reading.py)

<br>

## The Aggregator Interface

### Methods:
- 3 types of reports: `Holdings`, `Protocol`, and `Chain`
- 2 variations: `Unpriced` and `Priced`
- 2 call types: `Synchronous` and `Asynchronous`

<br>

### Yielding us 12 methods:

1. `get_holdings_report_sync() -> PositionsDict`
2. `get_holdings_report_async() -> PositionsDict`
3. `get_protocol_report_sync(name: str) -> ProtocolReport[TDetails]`
4. `get_protocol_report_async(name: str) -> ProtocolReport[TDetails]`
5. `get_chain_report_sync() -> ChainReport[TDetails]`
6. `get_chain_report_async() -> ChainReport[TDetails]`
7. `get_holdings_priced_report_sync() -> PricedPositionsDict`
8. `get_holdings_priced_report_async() -> PricedPositionsDict`
9. `get_protocol_priced_report_sync(name: str) -> ProtocolPricedReport[TPricedDetails]`
10. `get_protocol_priced_report_async(name: str) -> ProtocolPricedReport[TPricedDetails]`
11. `get_chain_priced_report_sync() -> ChainPricedReport[TPricedDetails]`
12. `get_chain_priced_report_async() -> ChainPricedReport[TPricedDetails]`

<br>

## Data

### The fundamental building blocks of the data are two number types:

1. `Number: {value: int, decimals: int}`
    - Can be casted to float:
        - `float(number)` where `number: Number`
    - Or in numpy arrays:
        - `np.array(numbers, dtype=np.double)` where `numbers: Sequence[Number]`
2. `LongShortNumbers: {net: Number, long: Number, short: Number}`
    - Can have its individual numbers casted to floats:
        - `float(ls_num.net)` where `ls_num: LongShortNumber`
    - Or in numpy arrays:
        - `np.array([ls_num.net for ls_num in ls_nums], dtype=np.double)` where `ls_nums: Sequence[LongShortNumbers]`

### From them, we construct:

1. `PositionsDict: dict[str, LongShortNumbers]`
    - `{"ABC": LongShortNumbers}`
2. `ProtocolReport[TDetails]`
    - `{positions: PositionsDict, details: TDetails}`
    - Note: `TDetails` is a generic protocol-specific type, e.g., `PancakeswapDetails`
3. `ChainReport[TDetails]`
    - `{total: PositionsDict, holdings: PositionsDict, protocols: dict[str, ProtocolReport[TDetails]]}`
    - Note: `TDetails` is a union of protocol-specific types e.g., `Union[PancakeswapDeatils, VenusDetails]`
4. `PricedPositionsDict: dict[str, PricedPosition]`
    - `{"ABC": {amount: LongShortNumbers, value: LongShortNumbers}}`
5. `ProtocolPricedReport[TPricedDetails]`
    - `{value: LongShortNumbers, postions: PricedPositionsDict, details: TPricedDetails}`
    - Note: `TPricedDetails` is a generic protoocl-specific type, e.g., `PancakeswapPricedDetails`
6. `ChainPricedReport[TPricedDetails]`
    - `{total: {value: LongShortNumbers, postions: PricedPositionsDict}, holdings: {value: LongShortNumbers, positions: PricedPositionsDict}, protocols: dict[str, ProtocolPricedReport[TPricedDetails]]`
    - Note: `TPricedDetails` is a union of protocol-specific types, e.g., `Union[PancakeswapPricedDetails, VenusPricedDetails]`

<br>

## Caveat

Synchronous calls will not work directly in Jupyter Notebook due to it already running an event loop. There is a workaround but it has to be implemented inside the notebook as it doesn't work when imported for some reason:

```python
def await_coroutine(coroutine):
    future = asyncio.run_coroutine_threadsafe(coroutine, asyncio.get_event_loop())
    return future.result() # Synchronously blocks when waiting for result

holdings_report = await_coroutine(aggregator.get_holdings_report_async())
```

## How it works

- Aggregator composes holdings and protocol readers.
- Aggregator routes the calls to the respective readers and aggregates the results.
- Individual readers simply reads and returns positions [and details for protocols] for unpriced reports.
- Individual readers reads and returns priced positions [and priced details for protocols] for priced reports.
- A `LazyPriceReader` is used for synchronization across readers to ensure all have loaded positions before starting to read prices on-demand to the individual price readers, caching results to prevent duplicate price calls.

Diagram TBD
