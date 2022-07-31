# Standard libraries
import os

# Add the current path since this is in the examples directory
import sys
sys.path.insert(1, os.getcwd())

# 3rd party libraries
from dotenv import load_dotenv

# Code
from sdk.chains.bsc.configs import BscConfig
from sdk.chains.bsc.connector import BscConnector
from sdk.fund import Fund
from web3 import Web3


# Load the environment variables
load_dotenv(".env.local")

# Constants
ETH = 'BNB'
TKN1 = 'TKN1'
TKN2 = 'TKN2'
CAKE = 'CAKE'


########################
## Setup (local node) ##
########################
bsc_config = BscConfig(config_path="configs/bsc-local")
bsc_connector = BscConnector(os.environ.get("BSC_RPC_URI"))
bsc_fund = Fund(bsc_config, bsc_connector, os.environ.get("BSC_OPERATOR_PK"))


#################
## PancakeSwap ##
#################
# ----------------------------------
# Swapping on PancakeSwap directly
# ----------------------------------
from sdk.chains.bsc.encoders import PancakeswapEncoder

# Instantiate the pancakeswap encoder
pcs_encoder = PancakeswapEncoder(bsc_config)

# Build the transactions (List[FundTxns])
txns = pcs_encoder.swap_with_exact(
    TKN1,                  # From token
    ETH,                   # To token
    Web3.toWei(1, 'ether'),  # exact amount of TKN1 to be sent
    0                        # 0 minimum amt of BNB to be received
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    txns,
    gas_limit=300_000,              # optional
    gas_price=Web3.toWei(5, 'gwei') # optional
)

# Build the transactions (List[FundTxns])
txns = pcs_encoder.swap_for_exact(
    TKN1,                   # From token
    ETH,                    # To token
    Web3.toWei(5, 'ether'),   # max amount of TKN1 to be sent
    Web3.toWei(1, 'ether')    # exact amt of BNB to be received
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    txns,
    gas_limit=300_000,               # optional
    gas_price=Web3.toWei(5, 'gwei'), # optional
    name_in_logs="PCS swapping"      # optional
)


# ---------------------------------------------
# Single-Farming CAKE on PancakeSwap directly
# ---------------------------------------------
from sdk.chains.bsc.encoders import PancakeswapEncoder

# Instantiate the pancakeswap encoder
pcs_encoder = PancakeswapEncoder(bsc_config)

# Build the transactions for single-farming cake (List[FundTxn])
single_farm_cake_txns = pcs_encoder.single_farm_cake(
    Web3.toWei(1, 'ether'),  # amount to deposit and farm
    86400 * 7   # duration of the farm in seconds = 1 week
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    single_farm_cake_txns,
    gas_limit=500_000,                     # optional
    gas_price=Web3.toWei(5, 'gwei'),       # optional
    name_in_logs="PCS single-farming cake" # optional
)


# ----------------------------------------------
# Single-Farming Token on PancakeSwap directly
# ----------------------------------------------
from sdk.chains.bsc.encoders import PancakeswapEncoder

# Instantiate the pancakeswap encoder
pcs_encoder = PancakeswapEncoder(bsc_config)

# Build the transactions for single-farming token (List[FundTxn])
single_farm_txns = pcs_encoder.single_farm(
    CAKE,                    # the token to farm with
    TKN1,                    # the token to farm for    
    Web3.toWei(1, 'ether'),  # amount to deposit and farm
)

single_unfarm_txns = pcs_encoder.single_unfarm(
    CAKE,                   # the token to farm with
    TKN1,                   # the token to withdraw
    Web3.toWei(1, 'ether'), # the amount to withdraw deposit
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    single_farm_txns + single_unfarm_txns,
    gas_limit=500_000,                # optional
    gas_price=Web3.toWei(5, 'gwei'),  # optional
    name_in_logs="PCS single-farming" # optional
)


# ------------------------------------
# LP-Farming on PancakeSwap directly
# ------------------------------------
from sdk.chains.bsc.encoders import PancakeswapEncoder

# Instantiate the pancakeswap encoder
pcs_encoder = PancakeswapEncoder(bsc_config)

# Build the transactions for adding liqudity (List[FundTxn])
add_liquidity_txns = pcs_encoder.add_liquidity( # See `remove_liquidity` as well
    TKN1,                    # token 0
    TKN2,                    # token 1
    Web3.toWei(1, 'ether'),  # exact amount of token 0 to add
    Web3.toWei(1, 'ether')   # exact amount of token 1 to add
)
# Build the transactions for farming the lp tokens (List[FundTxn])
lp_farming_txns = pcs_encoder.lp_farm( # See `unfarm`` as well
    TKN1,                  # token 0
    'TKN2',                  # token 1
    Web3.toWei(1, 'ether')   # Amount of LP tokens to farm
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    add_liquidity_txns + lp_farming_txns, # Adding the txn lists together
    gas_limit=500_000,               # optional
    gas_price=Web3.toWei(5, 'gwei'), # optional
    name_in_logs="PCS lp-farming"    # optional
)


# --------------------------------------------
# LP-Farming on PancakeSwap via Utils
#
# Combines `add_liquidity` and `lp_farm``
#
# This helps to atomically find out on-chain
# how many lp tokens were issued,
# and farm that number of lp tokens.
# --------------------------------------------
from sdk.chains.bsc.encoders import PancakeswapLpFarmingUtilEncoder

# # Instantiate the pancakeswap lp farming utils
pcs_lp_util_encoder = PancakeswapLpFarmingUtilEncoder(bsc_config)

# Build the transactions for lp farming via the utils (List[FundTxn])
lp_utils_txns = pcs_lp_util_encoder.lp_farm(
    TKN1,                    # token 0
    TKN2,                    # token 1
    Web3.toWei(1, 'ether'),  # exact amount of token 0 to add
    Web3.toWei(1, 'ether'),  # exact amount of token 1 to add
    0,                       # min amount of token 0 to add
    0,                       # min amount of token 1 to add
    False                    # whether to farm all the lp token balance or only what was issued
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    lp_utils_txns,
    gas_limit=500_000,                 # optional
    gas_price=Web3.toWei(5, 'gwei'),   # optional
    name_in_logs="PCS lp-farming util" # optional
)


###########
## Venus ##
###########
# ----------------------------
# Lending/Borrowing on Venus
# ----------------------------
from sdk.chains.bsc.encoders import VenusEncoder

# Instantiate the venus encoder
venus_encoder = VenusEncoder(bsc_config)

# Build the transaction to enable a market and supply
venus_txns = (
    # Enable these BNB as a collateral
    venus_encoder.enter_markets([ETH])
    # Supply BNB
    + venus_encoder.supply(ETH, Web3.toWei(5, 'ether'))
    # Borrow TKN1
    + venus_encoder.borrow(TKN1, Web3.toWei(1, 'ether'))
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    venus_txns,
    gas_limit=600_000,                     # optional
    gas_price=Web3.toWei(5, 'gwei'),       # optional
    name_in_logs="Venus lending borrowing" # optional
)


# -------------------
# Claim XVS rewards
# -------------------
from sdk.chains.bsc.encoders import VenusEncoder

# Instantiate the venus encoder
venus_encoder = VenusEncoder(bsc_config)

# Build the transaction to enable a market and supply
venus_txns = venus_encoder.claim_rewards()

# Call through the fund via multi_call
bsc_fund.multi_call(
    venus_txns,
    gas_limit=400_000,               # optional
    gas_price=Web3.toWei(5, 'gwei'), # optional
    name_in_logs="Claim XVS rewards" # optional
)


##############################
## PancakeSwap-Venus Combos ##
##############################
# -------------------
# Borrow to lp-farm
# -------------------
from sdk.chains.bsc.encoders import VenusEncoder, PancakeswapLpFarmingUtilEncoder

# Instantiate the encoders
venus_encoder = VenusEncoder(bsc_config)
pcs_lp_utils_encoder = PancakeswapLpFarmingUtilEncoder(bsc_config)


# Build the transaction to enable a market and supply
venus_txns = (
    venus_encoder.enter_markets([ETH])
    + venus_encoder.supply(ETH, Web3.toWei(5, 'ether'))
    + venus_encoder.borrow(TKN1, Web3.toWei(1, 'ether'))
    + venus_encoder.borrow(TKN2, Web3.toWei(1, 'ether'))
    + pcs_lp_utils_encoder.lp_farm(TKN1, TKN2, Web3.toWei(1, 'ether'), Web3.toWei(1, 'ether'), 0, 0)
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    venus_txns,
    gas_limit=1_000_000,             # optional
    gas_price=Web3.toWei(5, 'gwei'), # optional
    name_in_logs="Borrow to lp-farm" # optional
)


# ------------------------
# Leverage up a position
# ------------------------
from sdk.chains.bsc.encoders import VenusEncoder, PancakeswapEncoder

# Instantiate the encoders
venus_encoder = VenusEncoder(bsc_config)
pcs_encoder = PancakeswapEncoder(bsc_config)

# Build the transaction to enable a market and supply
leverage_up_txns = (
    venus_encoder.enter_markets([ETH])
    + venus_encoder.supply(ETH, Web3.toWei(2, 'ether'))
    + venus_encoder.borrow(TKN1, Web3.toWei(1, 'ether'))
    + pcs_encoder.swap_for_exact(TKN1, ETH, Web3.toWei(1, 'ether'), Web3.toWei(0.1, 'ether'))
    + venus_encoder.supply(ETH, Web3.toWei(0.1, 'ether'))
)

# Call through the fund via multi_call
bsc_fund.multi_call(
    leverage_up_txns,
    gas_limit=800_000,                    # optional
    gas_price=Web3.toWei(5, 'gwei'),      # optional
    name_in_logs="Leverage up a position" # optional
)
