"""
Transaction generator for Brazilian Fraud Data Generator.
"""

import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Iterator, Tuple

from ..config.transactions import (
    TX_TYPES_LIST, TX_TYPES_WEIGHTS,
    CHANNELS_LIST, CHANNELS_WEIGHTS,
    FRAUD_TYPES_LIST, FRAUD_TYPES_WEIGHTS,
    PIX_TYPES_LIST, PIX_TYPES_WEIGHTS,
    BRANDS_LIST, BRANDS_WEIGHTS,
    CARD_ENTRY_LIST, CARD_ENTRY_WEIGHTS,
    INSTALLMENT_LIST, INSTALLMENT_WEIGHTS,
    REFUSAL_REASONS,
)
from ..config.fraud_patterns import (
    FRAUD_PATTERNS,
    get_fraud_pattern,
    get_anomaly_multiplier,
    get_time_window_for_anomaly,
)
from ..config.merchants import (
    MCC_LIST, MCC_WEIGHTS, MCC_CODES,
    get_merchants_for_mcc, get_mcc_info,
)
from ..config.banks import BANK_CODES, BANK_WEIGHTS
from ..config.geography import ESTADOS_BR, ESTADOS_LIST, ESTADOS_WEIGHTS
from ..profiles.behavioral import (
    get_profile,
    get_transaction_type_for_profile,
    get_mcc_for_profile,
    get_channel_for_profile,
    get_transaction_hour_for_profile,
    get_transaction_value_for_profile,
)
from ..utils.helpers import generate_ip_brazil, generate_random_hash
from ..utils.streaming import CustomerSessionState
from ..utils.weight_cache import WeightCache  # OTIMIZAÇÃO 1.1


class TransactionGenerator:
    """
    Generator for realistic Brazilian financial transactions.
    
    Features:
    - Behavioral profile-aware generation
    - Configurable fraud rate
    - Realistic value distributions
    - Proper PIX, card, and other transaction types
    """
    
    def __init__(
        self,
        fraud_rate: float = 0.02,
        use_profiles: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize transaction generator.
        
        Args:
            fraud_rate: Fraction of transactions that are fraudulent (0.0-1.0)
            use_profiles: If True, use behavioral profiles
            seed: Random seed for reproducibility
        """
        self.fraud_rate = fraud_rate
        self.use_profiles = use_profiles
        
        if seed is not None:
            random.seed(seed)
        
        # OTIMIZAÇÃO 1.1: Pre-compute weight caches (created once, reused for all transactions)
        self._tx_type_cache = WeightCache(TX_TYPES_LIST, TX_TYPES_WEIGHTS)
        self._fraud_type_cache = WeightCache(FRAUD_TYPES_LIST, FRAUD_TYPES_WEIGHTS)
        self._mcc_cache = WeightCache(MCC_LIST, MCC_WEIGHTS)
        self._channel_cache = WeightCache(CHANNELS_LIST, CHANNELS_WEIGHTS)
        self._bank_cache = WeightCache(BANK_CODES, BANK_WEIGHTS)
        self._estado_cache = WeightCache(ESTADOS_LIST, ESTADOS_WEIGHTS)
        self._brand_cache = WeightCache(BRANDS_LIST, BRANDS_WEIGHTS)
        self._installment_cache = WeightCache(INSTALLMENT_LIST, INSTALLMENT_WEIGHTS)
        self._card_entry_cache = WeightCache(CARD_ENTRY_LIST, CARD_ENTRY_WEIGHTS)
        self._pix_type_cache = WeightCache(PIX_TYPES_LIST, PIX_TYPES_WEIGHTS)
        
        # OTIMIZAÇÃO 1.2: Cache merchant lists by MCC (avoid repeated dict lookups)
        from ..config.merchants import MERCHANTS_BY_MCC
        self._merchants_cache = MERCHANTS_BY_MCC
        
        # OTIMIZAÇÃO 2: Fraud pattern cache for contextualized fraud
        self._fraud_patterns = FRAUD_PATTERNS
    
    def generate(
        self,
        tx_id: str,
        customer_id: str,
        device_id: str,
        timestamp: datetime,
        customer_state: Optional[str] = None,
        customer_profile: Optional[str] = None,
        force_fraud: Optional[bool] = None,
        session_state: Optional[CustomerSessionState] = None
    ) -> Dict[str, Any]:
        """
        Generate a single transaction.
        
        Args:
            tx_id: Transaction identifier
            customer_id: Customer identifier
            device_id: Device identifier
            timestamp: Transaction timestamp
            customer_state: Customer's state (for geolocation)
            customer_profile: Customer's behavioral profile
            force_fraud: If set, override random fraud determination
        
        Returns:
            Transaction data as dictionary
        """
        # Determine if fraud
        if force_fraud is not None:
            is_fraud = force_fraud
        else:
            is_fraud = random.random() < self.fraud_rate
        
        fraud_type = None
        if is_fraud:
            fraud_type = self._fraud_type_cache.sample()
        
        # Select transaction type (profile-aware)
        if self.use_profiles and customer_profile:
            tx_type = get_transaction_type_for_profile(customer_profile)
        else:
            tx_type = self._tx_type_cache.sample()
        
        # Select MCC (profile-aware)
        if self.use_profiles and customer_profile:
            mcc_code = get_mcc_for_profile(customer_profile)
        else:
            mcc_code = self._mcc_cache.sample()
        
        mcc_info = get_mcc_info(mcc_code)
        
        # Calculate value
        valor = self._calculate_value(
            is_fraud,
            fraud_type,
            mcc_info,
            customer_profile
        )
        
        # Get merchant
        merchants = self._merchants_cache.get(mcc_code, ['Local Merchant'])  # OTIMIZAÇÃO 1.2: Local cache lookup
        merchant_name = random.choice(merchants)
        
        # Geolocation
        lat, lon = self._get_geolocation(customer_state, is_fraud)
        
        # Channel (profile-aware)
        if self.use_profiles and customer_profile:
            canal = get_channel_for_profile(customer_profile)
        else:
            canal = self._channel_cache.sample()
        
        # Bank destination
        banco_destino = self._bank_cache.sample()
        
        # Build base transaction
        tx = {
            'transaction_id': f'TXN_{tx_id}',
            'customer_id': customer_id,
            'session_id': f'SESS_{tx_id}',
            'device_id': device_id,
            'timestamp': timestamp.isoformat(),
            'type': tx_type,
            'amount': valor,
            'currency': 'BRL',
            'channel': canal,
            'ip_address': generate_ip_brazil(),
            'geolocation_lat': lat,
            'geolocation_lon': lon,
            'merchant_id': f'MERCH_{random.randint(1, 100000):06d}',
            'merchant_name': merchant_name,
            'merchant_category': mcc_info['category'],
            'mcc_code': mcc_code,
            'mcc_risk_level': mcc_info['risk'],
        }
        
        # Add type-specific fields
        self._add_type_specific_fields(tx, tx_type, banco_destino)
        
        # OTIMIZAÇÃO 2: Apply fraud pattern characteristics if fraud
        if is_fraud and fraud_type:
            tx = self._apply_fraud_pattern(tx, fraud_type, customer_profile, timestamp)
        
        # Add risk indicators
        self._add_risk_indicators(tx, timestamp, is_fraud, fraud_type, session_state)
        
        return tx
    
    def generate_batch(
        self,
        count: int,
        customer_device_pairs: list,
        start_date: datetime,
        end_date: datetime,
        start_tx_id: int = 1
    ) -> Iterator[Dict[str, Any]]:
        """
        Generate multiple transactions.
        
        Args:
            count: Number of transactions to generate
            customer_device_pairs: List of (customer_index, device_index) tuples
            start_date: Start of time range
            end_date: End of time range
            start_tx_id: Starting transaction ID number
        
        Yields:
            Transaction data dictionaries
        """
        for i in range(count):
            # Select random customer/device pair
            customer_idx, device_idx = random.choice(customer_device_pairs)
            
            # Generate timestamp
            timestamp = self._generate_timestamp(
                start_date,
                end_date,
                getattr(customer_idx, 'behavioral_profile', None)
            )
            
            tx_id = f"{start_tx_id + i:015d}"
            
            yield self.generate(
                tx_id=tx_id,
                customer_id=customer_idx.customer_id,
                device_id=device_idx.device_id,
                timestamp=timestamp,
                customer_state=getattr(customer_idx, 'state', None),
                customer_profile=getattr(customer_idx, 'behavioral_profile', None),
            )
    
    def _calculate_value(
        self,
        is_fraud: bool,
        fraud_type: Optional[str],
        mcc_info: dict,
        customer_profile: Optional[str]
    ) -> float:
        """Calculate transaction value."""
        if is_fraud:
            return self._calculate_fraud_value(fraud_type)
        
        mcc_range = (mcc_info['min_value'], mcc_info['max_value'])
        
        if self.use_profiles and customer_profile:
            return get_transaction_value_for_profile(customer_profile, mcc_range)
        
        # Default value calculation
        min_value, max_value = mcc_range
        mean = (min_value + max_value) / 3
        value = random.gauss(mean, mean / 2)
        return round(min(max(value, min_value), max_value), 2)
    
    def _calculate_fraud_value(self, fraud_type: Optional[str]) -> float:
        """Calculate fraud transaction value."""
        if fraud_type in ['LAVAGEM_DINHEIRO', 'TRIANGULACAO']:
            return round(random.uniform(5000, 50000), 2)
        elif fraud_type in ['CARTAO_CLONADO', 'CONTA_TOMADA']:
            return round(random.uniform(500, 10000), 2)
        else:
            return round(random.uniform(200, 5000), 2)
    
    def _get_geolocation(
        self,
        customer_state: Optional[str],
        is_fraud: bool
    ) -> Tuple[float, float]:
        """Get geolocation for transaction."""
        # Fraud sometimes happens in different states
        if is_fraud and random.random() < 0.3:
            estado = random.choices(ESTADOS_LIST, weights=ESTADOS_WEIGHTS)[0]
        elif customer_state and customer_state in ESTADOS_BR:
            estado = customer_state
        else:
            estado = random.choices(ESTADOS_LIST, weights=ESTADOS_WEIGHTS)[0]
        
        estado_info = ESTADOS_BR[estado]
        base_lat, base_lon = estado_info['lat'], estado_info['lon']
        
        # Add random offset (within ~50km)
        lat = round(base_lat + random.uniform(-0.5, 0.5), 6)
        lon = round(base_lon + random.uniform(-0.5, 0.5), 6)
        
        return lat, lon
    
    def _add_type_specific_fields(
        self,
        tx: dict,
        tx_type: str,
        banco_destino: str
    ) -> None:
        """Add transaction type-specific fields."""
        if tx_type in ['CREDIT_CARD', 'DEBIT_CARD']:
            card_brand = self._brand_cache.sample()
            tx.update({
                'card_number_hash': generate_random_hash(16),
                'card_brand': card_brand,
                'card_type': 'CREDIT' if tx_type == 'CREDIT_CARD' else 'DEBIT',
                'installments': self._installment_cache.sample() if tx_type == 'CREDIT_CARD' else 1,
                'card_entry': self._card_entry_cache.sample(),
                'cvv_validated': random.random() < 0.95,
                'auth_3ds': random.random() < 0.70,
                'pix_key_type': None,
                'pix_key_destination': None,
                'destination_bank': None,
            })
        elif tx_type == 'PIX':
            pix_key_type = self._pix_type_cache.sample()
            tx.update({
                'card_number_hash': None,
                'card_brand': None,
                'card_type': None,
                'installments': None,
                'card_entry': None,
                'cvv_validated': None,
                'auth_3ds': None,
                'pix_key_type': pix_key_type,
                'pix_key_destination': generate_random_hash(32),
                'destination_bank': banco_destino,
            })
        else:
            tx.update({
                'card_number_hash': None,
                'card_brand': None,
                'card_type': None,
                'installments': None,
                'card_entry': None,
                'cvv_validated': None,
                'auth_3ds': None,
                'pix_key_type': None,
                'pix_key_destination': None,
                'destination_bank': banco_destino if tx_type in ['TED', 'BOLETO', 'DOC'] else None,
            })
    
    def _apply_fraud_pattern(
        self,
        tx: Dict[str, Any],
        fraud_type: str,
        customer_profile: Optional[str],
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Apply fraud-specific characteristics to transaction (OTIMIZAÇÃO 2: Fraud Contextualization).
        
        Each fraud type has specific patterns that make it detectável by ML models:
        - ENGENHARIA_SOCIAL: Normal device/location, new beneficiary
        - CONTA_TOMADA: New device, unusual time, high velocity
        - CARTAO_CLONADO: Multiple small transactions, different location
        - PIX_GOLPE: PIX-only, new PIX key, medium amounts
        - etc.
        
        Args:
            tx: Base transaction dict
            fraud_type: Type of fraud
            customer_profile: Customer behavioral profile
            timestamp: Original timestamp
            
        Returns:
            Modified transaction with fraud-specific characteristics
        """
        pattern = get_fraud_pattern(fraud_type)
        characteristics = pattern['characteristics']
        
        # VALUE ANOMALY: Adjust amount based on fraud pattern
        if 'amount_override' in characteristics:
            # Force specific amount range (e.g., for card testing)
            min_amt, max_amt = characteristics['amount_override']
            tx['amount'] = round(random.uniform(min_amt, max_amt), 2)
        elif 'amount_multiplier' in characteristics:
            min_mult, max_mult = characteristics['amount_multiplier']
            current_amount = tx.get('amount', 100.0)
            
            # Get base value for profile
            if self.use_profiles and customer_profile:
                profile_avg = get_transaction_value_for_profile(customer_profile)
            else:
                profile_avg = current_amount
            
            # Apply multiplier
            new_amount = profile_avg * random.uniform(min_mult, max_mult)
            tx['amount'] = round(new_amount, 2)
        
        # NEW BENEFICIARY: Always for certain fraud types
        if characteristics.get('new_beneficiary', False):
            tx['new_beneficiary'] = True
            # Different destination bank for transfers
            if tx.get('destination_bank'):
                tx['destination_bank'] = self._bank_cache.sample()
        
        # VELOCITY: Transaction burst pattern
        if characteristics.get('velocity') == 'HIGH':
            if 'transaction_burst' in characteristics:
                min_burst, max_burst = characteristics['transaction_burst']
                tx['transactions_last_24h'] = random.randint(min_burst, max_burst)
            else:
                tx['transactions_last_24h'] = random.randint(10, 30)
            
            # High accumulated amount
            tx['accumulated_amount_24h'] = round(tx['amount'] * tx['transactions_last_24h'] * random.uniform(0.6, 0.9), 2)
        elif characteristics.get('velocity') == 'MEDIUM':
            tx['transactions_last_24h'] = random.randint(5, 12)
            tx['accumulated_amount_24h'] = round(tx['amount'] * tx['transactions_last_24h'] * 0.7, 2)
        
        # TIME ANOMALY: Unusual hours (madrugada for account takeover)
        time_anomaly = characteristics.get('time_anomaly', 'NONE')
        if time_anomaly != 'NONE':
            valid_hours = get_time_window_for_anomaly(time_anomaly)
            new_hour = random.choice(valid_hours)
            new_timestamp = timestamp.replace(hour=new_hour, minute=random.randint(0, 59))
            tx['timestamp'] = new_timestamp.isoformat()
            tx['unusual_time'] = new_hour < 6 or new_hour > 22
        
        # LOCATION ANOMALY: Different state/geo
        location_anomaly = characteristics.get('location_anomaly', 'NONE')
        if location_anomaly == 'HIGH':
            # Completely different state
            different_state = random.choice([s for s in ESTADOS_LIST if s != tx.get('customer_state', 'SP')])
            estado_info = ESTADOS_BR.get(different_state, ESTADOS_BR['SP'])
            base_lat, base_lon = estado_info['lat'], estado_info['lon']
            tx['geolocation_lat'] = round(base_lat + random.uniform(-0.5, 0.5), 6)
            tx['geolocation_lon'] = round(base_lon + random.uniform(-0.5, 0.5), 6)
        elif location_anomaly == 'MEDIUM':
            # Same state but far from usual (50-200km offset)
            tx['geolocation_lat'] += random.uniform(-2.0, 2.0)
            tx['geolocation_lon'] += random.uniform(-2.0, 2.0)
            tx['distance_from_last_txn_km'] = round(random.uniform(50, 200), 2)
        
        # DEVICE ANOMALY: New/suspicious device
        device_anomaly = characteristics.get('device_anomaly', 'NONE')
        if device_anomaly == 'HIGH':
            # Completely different device
            tx['device_id'] = f"DEV_FRAUD_{random.randint(100000, 999999):06d}"
        
        # CHANNEL PREFERENCE: Force specific channels
        if 'channel_preference' in characteristics:
            preferred_channels = characteristics['channel_preference']
            tx['channel'] = random.choice(preferred_channels)
            
            # Update PIX fields if PIX fraud
            if 'PIX' in preferred_channels and tx['channel'] == 'PIX':
                tx['type'] = 'PIX'
                pix_key_type = random.choice(characteristics.get('pix_key_type', ['CPF', 'PHONE', 'EMAIL']))
                tx['pix_key_type'] = pix_key_type
                tx['pix_key_destination'] = generate_random_hash(32)
                tx['destination_bank'] = self._bank_cache.sample()
                # Clear card fields
                tx['card_number_hash'] = None
                tx['card_brand'] = None
                tx['card_type'] = None
        
        # MCC PREFERENCE: Common MCCs for fraud type
        if 'mcc_preference' in characteristics:
            mcc_codes = characteristics['mcc_preference']
            new_mcc = random.choice(mcc_codes)
            tx['mcc_code'] = new_mcc
            mcc_info = get_mcc_info(new_mcc)
            tx['merchant_category'] = mcc_info['category']
            tx['mcc_risk_level'] = mcc_info['risk']
            # Update merchant
            merchants = self._merchants_cache.get(new_mcc, ['Suspicious Merchant'])
            tx['merchant_name'] = random.choice(merchants)
        
        # FRAUD SCORE: Higher base score for pattern
        base_score = pattern.get('fraud_score_base', 0.5)
        tx['fraud_score'] = round(random.uniform(base_score * 100, 95), 2)
        
        return tx
    
    def _add_risk_indicators(
        self,
        tx: dict,
        timestamp: datetime,
        is_fraud: bool,
        fraud_type: Optional[str],
        session_state: Optional[CustomerSessionState] = None
    ) -> None:
        """Add risk indicators to transaction."""
        hour = timestamp.hour
        unusual_time = hour < 6 or hour > 23
        
        if is_fraud:
            status = random.choices(
                ['APPROVED', 'DECLINED', 'PENDING', 'BLOCKED'],
                weights=[60, 25, 10, 5]
            )[0]
            fraud_score = round(random.uniform(65, 100), 2)
            default_transactions_24h = random.randint(5, 50)
            default_accumulated_amount = round(random.uniform(2000, 50000), 2)
        else:
            status = random.choices(
                ['APPROVED', 'DECLINED', 'PENDING'],
                weights=[96, 3, 1]
            )[0]
            fraud_score = round(random.uniform(0, 35), 2)
            default_transactions_24h = random.randint(1, 15)
            default_accumulated_amount = round(random.uniform(50, 5000), 2)

        # Improved risk indicators with session state (OTIMIZAÇÃO 2.2/2.3)
        if session_state:
            # Velocity / accumulated (use session unless fraud pattern already set)
            if tx.get('transactions_last_24h') is None:
                tx['transactions_last_24h'] = session_state.get_velocity(timestamp) + 1
            if tx.get('accumulated_amount_24h') is None:
                tx['accumulated_amount_24h'] = round(
                    session_state.get_accumulated_24h(timestamp) + float(tx.get('amount', 0.0)),
                    2
                )

            # New beneficiary (merchant novelty)
            if tx.get('new_beneficiary') is None:
                tx['new_beneficiary'] = session_state.is_new_merchant(tx.get('merchant_id'))

            # Time since last transaction
            if tx.get('time_since_last_txn_min') is None:
                tx['time_since_last_txn_min'] = session_state.get_last_transaction_minutes_ago(timestamp)

            # Distance from last transaction
            if tx.get('distance_from_last_txn_km') is None:
                tx['distance_from_last_txn_km'] = session_state.get_distance_from_last_txn_km(
                    tx.get('geolocation_lat'),
                    tx.get('geolocation_lon')
                )
        else:
            # Fallback to random indicators
            if tx.get('distance_from_last_txn_km') is None:
                tx['distance_from_last_txn_km'] = round(random.uniform(0, 100), 2) if random.random() > 0.5 else None
            if tx.get('time_since_last_txn_min') is None:
                tx['time_since_last_txn_min'] = random.randint(1, 1440) if random.random() > 0.3 else None
            if tx.get('transactions_last_24h') is None:
                tx['transactions_last_24h'] = default_transactions_24h
            if tx.get('accumulated_amount_24h') is None:
                tx['accumulated_amount_24h'] = default_accumulated_amount
            if tx.get('new_beneficiary') is None:
                tx['new_beneficiary'] = random.random() < (0.7 if is_fraud else 0.15)
        
        tx.update({
            'unusual_time': unusual_time,
            'status': status,
            'refusal_reason': random.choice(REFUSAL_REASONS) if status == 'DECLINED' else None,
            'fraud_score': fraud_score,
            'is_fraud': is_fraud,
            'fraud_type': fraud_type,
        })
    
    def _generate_timestamp(
        self,
        start_date: datetime,
        end_date: datetime,
        customer_profile: Optional[str]
    ) -> datetime:
        """Generate realistic timestamp."""
        # Random day
        days_between = (end_date - start_date).days
        random_day = start_date + timedelta(days=random.randint(0, days_between))
        
        # Hour based on profile
        if self.use_profiles and customer_profile:
            is_weekend = random_day.weekday() >= 5
            hour = get_transaction_hour_for_profile(customer_profile, is_weekend)
        else:
            # Default hour distribution
            hour_weights = {
                0: 2, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2,
                6: 4, 7: 6, 8: 10, 9: 12, 10: 14, 11: 14,
                12: 15, 13: 14, 14: 13, 15: 12, 16: 12, 17: 13,
                18: 14, 19: 15, 20: 14, 21: 12, 22: 8, 23: 4
            }
            hours = list(hour_weights.keys())
            weights = list(hour_weights.values())
            hour = random.choices(hours, weights=weights)[0]
        
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        microsecond = random.randint(0, 999999)
        
        return random_day.replace(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond
        )
