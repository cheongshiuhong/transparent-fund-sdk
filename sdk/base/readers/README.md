
Positions readers should offer two methods:
1. `get_positions`
2. `tag_with_prices`

Prices readers should offer two methods:
1. `get_tokens_responsible` -> set
3. `get_subset_prices` -- only input tokens are priced
2. `get_all_prices` -- all prices are retrieved (i.e., get_subset_prices(get_tokens_responsible())

Aggregator will then offer the interface:
1. `get_holdings` -> PositionsDict
2. `get_priced_holdings` -> PricedPositionsDict

2. `get_protocol_report` -> ProtocolReport[SpecializedDetails]
3. `get_protocols_reports` -> dict[str, ProtocolReport[SpecializedDetails]]
3. `get_aggregated_report` -> { holdings: PositionsWithPrices, protocols: ProtocolReport[SpecializedDetails] }

For the sake of terminology, `report` refers to positions tagged with value + protocl-specific breakdown details


Positions will break down long, short, and net positions and their values
{
    total: ({
        value: ({ long: xxx, short: xxx, net: xxx }),
        positions: {
            ABC: {
                amount: ({ long: xxx, short: xxx, net: xxx })
                value: ({ long: xxx, short: xxx, net: xxx })
            },
            DEF: {
                amount: ({ long: xxx, short: xxx, net: xxx })
                value: ({ long: xxx, short: xxx, net: xxx })
            },
        },
    }),
    holdings: ({
        value: ({ long: xxx, short: xxx, net: xxx }),
        positions: {
            ABC: {
                amount: ({ long: xxx, short: xxx, net: xxx })
                value: ({ long: xxx, short: xxx, net: xxx })
            },
            DEF: {
                amount: ({ long: xxx, short: xxx, net: xxx })
                value: ({ long: xxx, short: xxx, net: xxx })
            },
        },
    }),
    protocols: {
        pancakeswap: ({
            value: ({ long: xxx, short: xxx, net: xxx }),
            positions: {
                ABC: {
                    amount: ({ long: xxx, short: xxx, net: xxx })
                    value: ({ long: xxx, short: xxx, net: xxx })
                },
            },
            details: {...}
        })
    },
}
