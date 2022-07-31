# Standard libraries
import json
import os

# Add the current path since this is in the examples directory
import sys
sys.path.insert(1, os.getcwd())

# 3rd party libraries
from dotenv import load_dotenv

# Code
from sdk.chains.bsc.configs import BscConfig
from sdk.chains.bsc.readers.aggregator import BscAggregator


load_dotenv(".env.mainnet")


#####################
## Setup (mainnet) ##
#####################
bsc_config = BscConfig(
    config_path="configs/bsc-mainnet",
    rpc_uri=os.environ.get("BSC_RPC_URI")
)
bsc_aggregator = BscAggregator(bsc_config)

##################
## Read reports ##
##################
holdings_report = bsc_aggregator.get_holdings_report_sync()
holdings_priced_report = bsc_aggregator.get_holdings_priced_report_sync()
pcs_report = bsc_aggregator.get_protocol_report_sync('pancakeswap')
pcs_priced_report = bsc_aggregator.get_protocol_priced_report_sync('pancakeswap')
venus_report = bsc_aggregator.get_protocol_report_sync('venus')
venus_priced_report = bsc_aggregator.get_protocol_priced_report_sync('venus')
chain_report = bsc_aggregator.get_chain_report_sync()
chain_priced_report = bsc_aggregator.get_chain_priced_report_sync()

##################
## Save reports ##
##################
def save(data, filename):
    if not os.path.exists('reader-outputs'):
        os.mkdir('reader-outputs')

    with open(f'reader-outputs/{filename}.json', 'w') as f:
        json.dump(data, f, indent=2)

save(holdings_report.dict(), 'holdings_report')
save(holdings_priced_report.dict(), 'holdings_priced_report')
save(pcs_report.dict(), 'pcs_report')
save(pcs_priced_report.dict(), 'pcs_priced_report')
save(venus_report.dict(), 'venus_report')
save(venus_priced_report.dict(), 'venus_priced_report')
save(chain_report.dict(), 'chain_report')
save(chain_priced_report.dict(), 'chain_priced_report')
