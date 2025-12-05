"""
Profiles package for Brazilian Fraud Data Generator.
Contains behavioral profiles for realistic transaction patterns.
"""

from .behavioral import (
    ProfileType,
    BehavioralProfile,
    PROFILES,
    PROFILE_DISTRIBUTION,
    PROFILE_LIST,
    PROFILE_WEIGHTS,
    get_profile,
    assign_random_profile,
    get_transaction_type_for_profile,
    get_mcc_for_profile,
    get_channel_for_profile,
    get_transaction_hour_for_profile,
    get_transaction_value_for_profile,
    get_monthly_transactions_for_profile,
    should_transact_on_weekend,
)

__all__ = [
    'ProfileType',
    'BehavioralProfile',
    'PROFILES',
    'PROFILE_DISTRIBUTION',
    'PROFILE_LIST',
    'PROFILE_WEIGHTS',
    'get_profile',
    'assign_random_profile',
    'get_transaction_type_for_profile',
    'get_mcc_for_profile',
    'get_channel_for_profile',
    'get_transaction_hour_for_profile',
    'get_transaction_value_for_profile',
    'get_monthly_transactions_for_profile',
    'should_transact_on_weekend',
]
