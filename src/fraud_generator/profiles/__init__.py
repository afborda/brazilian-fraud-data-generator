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

from .ride_behavioral import (
    RideProfileType,
    RideBehavioralProfile,
    RIDE_PROFILES,
    CUSTOMER_TO_RIDE_PROFILE,
    get_ride_profile,
    get_ride_profile_for_customer,
    assign_random_ride_profile,
    get_preferred_app_for_profile,
    get_preferred_category_for_profile,
    get_preferred_hour_for_profile,
    should_tip_for_profile,
    get_tip_percentage_for_profile,
    should_accept_surge_for_profile,
)

__all__ = [
    # Transaction profiles
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
    # Ride profiles
    'RideProfileType',
    'RideBehavioralProfile',
    'RIDE_PROFILES',
    'CUSTOMER_TO_RIDE_PROFILE',
    'get_ride_profile',
    'get_ride_profile_for_customer',
    'assign_random_ride_profile',
    'get_preferred_app_for_profile',
    'get_preferred_category_for_profile',
    'get_preferred_hour_for_profile',
    'should_tip_for_profile',
    'get_tip_percentage_for_profile',
    'should_accept_surge_for_profile',
]
