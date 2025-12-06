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
    
    def generate(
        self,
        tx_id: str,
        customer_id: str,
        device_id: str,
        timestamp: datetime,
        customer_state: Optional[str] = None,
        customer_profile: Optional[str] = None,
        force_fraud: Optional[bool] = None
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
            fraud_type = random.choices(
                FRAUD_TYPES_LIST,
                weights=FRAUD_TYPES_WEIGHTS
            )[0]
        
        # Select transaction type (profile-aware)
        if self.use_profiles and customer_profile:
            tx_type = get_transaction_type_for_profile(customer_profile)
        else:
            tx_type = random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)[0]
        
        # Select MCC (profile-aware)
        if self.use_profiles and customer_profile:
            mcc_code = get_mcc_for_profile(customer_profile)
        else:
            mcc_code = random.choices(MCC_LIST, weights=MCC_WEIGHTS)[0]
        
        mcc_info = get_mcc_info(mcc_code)
        
        # Calculate value
        valor = self._calculate_value(
            is_fraud,
            fraud_type,
            mcc_info,
            customer_profile
        )
        
        # Get merchant
        merchants = get_merchants_for_mcc(mcc_code)
        merchant_name = random.choice(merchants)
        
        # Geolocation
        lat, lon = self._get_geolocation(customer_state, is_fraud)
        
        # Channel (profile-aware)
        if self.use_profiles and customer_profile:
            canal = get_channel_for_profile(customer_profile)
        else:
            canal = random.choices(CHANNELS_LIST, weights=CHANNELS_WEIGHTS)[0]
        
        # Bank destination
        banco_destino = random.choices(BANK_CODES, weights=BANK_WEIGHTS)[0]
        
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
        
        # Add risk indicators
        self._add_risk_indicators(tx, timestamp, is_fraud, fraud_type)
        
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
            card_brand = random.choices(BRANDS_LIST, weights=BRANDS_WEIGHTS)[0]
            tx.update({
                'card_number_hash': generate_random_hash(16),
                'card_brand': card_brand,
                'card_type': 'CREDIT' if tx_type == 'CREDIT_CARD' else 'DEBIT',
                'installments': random.choices(INSTALLMENT_LIST, weights=INSTALLMENT_WEIGHTS)[0] if tx_type == 'CREDIT_CARD' else 1,
                'card_entry': random.choices(CARD_ENTRY_LIST, weights=CARD_ENTRY_WEIGHTS)[0],
                'cvv_validated': random.choices([True, False], weights=[95, 5])[0],
                'auth_3ds': random.choices([True, False], weights=[70, 30])[0],
                'pix_key_type': None,
                'pix_key_destination': None,
                'destination_bank': None,
            })
        elif tx_type == 'PIX':
            pix_key_type = random.choices(PIX_TYPES_LIST, weights=PIX_TYPES_WEIGHTS)[0]
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
    
    def _add_risk_indicators(
        self,
        tx: dict,
        timestamp: datetime,
        is_fraud: bool,
        fraud_type: Optional[str]
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
            transactions_24h = random.randint(5, 50)
            accumulated_amount = round(random.uniform(2000, 50000), 2)
        else:
            status = random.choices(
                ['APPROVED', 'DECLINED', 'PENDING'],
                weights=[96, 3, 1]
            )[0]
            fraud_score = round(random.uniform(0, 35), 2)
            transactions_24h = random.randint(1, 15)
            accumulated_amount = round(random.uniform(50, 5000), 2)
        
        tx.update({
            'distance_from_last_txn_km': round(random.uniform(0, 100), 2) if random.random() > 0.5 else None,
            'time_since_last_txn_min': random.randint(1, 1440) if random.random() > 0.3 else None,
            'transactions_last_24h': transactions_24h,
            'accumulated_amount_24h': accumulated_amount,
            'unusual_time': unusual_time,
            'new_beneficiary': random.random() < (0.7 if is_fraud else 0.15),
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
