"""
Declaration of the report details types for the venus protocol.
"""

# Code
from sdk.lib.models import FrozenModel
from sdk.base.readers.structs import Number
from sdk.base.readers.protocols import IProtocolReportReader
from sdk.base.readers.structs import ProtocolReport, ProtocolPricedReport


class VenusPoolSnapshot(FrozenModel):
    supply_balance: Number
    borrow_balance: Number
    borrow_principal_balance: Number
    borrow_interest_balance: Number
    supply_rate_per_block: Number
    borrow_rate_per_block: Number
    collateral_factor: Number


class VenusPoolDetails(VenusPoolSnapshot):
    is_collateral: bool


class VenusDetails(FrozenModel):
    xvs_accrued_rewards: Number = Number()
    pools: dict[str, VenusPoolDetails] = {}


# --------
# Priced
# --------
class VenusPoolPricedDetails(VenusPoolDetails):
    supply_value: Number
    borrow_value: Number
    borrow_principal_value: Number
    borrow_interest_value: Number


class VenusPricedDetails(FrozenModel):
    xvs_accrued_rewards: Number
    total_supply_value: Number = Number()
    total_borrow_value: Number = Number()
    total_collateral_value: Number = Number()
    borrow_limit: Number = Number()
    max_loan_to_collateral_percent: Number = Number()
    loan_to_collateral_percent: Number = Number()
    loan_to_liquidation_percent: Number = Number()
    pools: dict[str, VenusPoolPricedDetails] = {}


IVenusReportReader = IProtocolReportReader[VenusDetails, VenusPricedDetails]
VenusReport = ProtocolReport[VenusDetails]
VenusPricedReport = ProtocolPricedReport[VenusPricedDetails]
