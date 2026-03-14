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
from ..config.seasonality import (
    pick_weighted_date,
    pick_hour,
    HORA_WEIGHTS_PADRAO,
    HORA_WEIGHTS_FRAUD_ATO,
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
from ..utils.precompute import PrecomputeBuffers  # OTIMIZAÇÃO 3: RAM pre-compute
from .session_context import build_context_for_fraud
from .correlations import match_fraud_rule
from .score import compute_fraud_risk_score, score_breakdown
from ..config.distributions import get_income_class
from ..config.pix import (
    MODALIDADE_INICIACAO_LIST, MODALIDADE_INICIACAO_WEIGHTS,
    TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS,
    HOLDER_TYPE_LIST, HOLDER_TYPE_WEIGHTS,
    ISPB_LIST,
    generate_end_to_end_id,
    MOTIVO_DEVOLUCAO_LIST, MOTIVO_DEVOLUCAO_WEIGHTS,
)
from ..validators.cpf import generate_valid_cpf

# Profile → social class mapping (used when customer income is not available)
_PROFILE_CLASSE = {
    'high_spender':        'A',
    'business_owner':      'B1',
    'subscription_heavy':  'B2',
    'young_digital':       'C1',
    'traditional_senior':  'C2',
    'family_provider':     'C2',
    # fraud victim profiles
    'ato_victim':          'C2',
    'falsa_central_victim': 'D',
    'malware_ats_victim':  'C1',
}

def _profile_to_classe_social(profile: Optional[str]) -> Optional[str]:
    return _PROFILE_CLASSE.get(profile) if profile else None


# T4: velocity baseline (mean txns/24h, std) per behavioral profile
# Used to compute customer_velocity_z_score; ATO fraud deviates 5-10× from baseline
_PROFILE_VELOCITY_BASELINE: dict = {
    'high_spender':         (15, 5.0),
    'business_owner':       (20, 7.0),
    'subscription_heavy':    (8, 3.0),
    'young_digital':        (10, 4.0),
    'traditional_senior':    (5, 2.0),
    'family_provider':       (7, 2.5),
    'ato_victim':            (8, 3.5),
    'falsa_central_victim':  (6, 2.5),
    'malware_ats_victim':    (9, 3.5),
}
_PROFILE_VELOCITY_DEFAULT = (8, 3.0)  # fallback when profile unknown


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
        self._ispb_list = ISPB_LIST
        
        # OTIMIZAÇÃO 1.2: Cache merchant lists by MCC (avoid repeated dict lookups)
        from ..config.merchants import MERCHANTS_BY_MCC
        self._merchants_cache = MERCHANTS_BY_MCC
        
        # OTIMIZAÇÃO 2: Fraud pattern cache for contextualized fraud
        self._fraud_patterns = FRAUD_PATTERNS

        # OTIMIZAÇÃO 3: RAM pre-compute buffers
        self._buf = PrecomputeBuffers(seed=seed)
    
    def generate(
        self,
        tx_id: str,
        customer_id: str,
        device_id: str,
        timestamp: datetime,
        customer_state: Optional[str] = None,
        customer_profile: Optional[str] = None,
        force_fraud: Optional[bool] = None,
        session_state: Optional[CustomerSessionState] = None,
        location_cluster: Optional[tuple] = None,
        customer_cpf: Optional[str] = None,
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
        
        # T4: merchant clustering — reuse a favourite for legit transactions 70% of the time.
        # Builds stable per-customer patterns so anomalous merchants become a real signal.
        _fav_merchant_id: Optional[str] = None
        _fav_from_session = (
            not is_fraud
            and session_state is not None
            and random.random() < 0.70
        )
        if _fav_from_session:
            _fav = session_state.get_favorite_merchant()  # type: ignore[union-attr]
            if _fav is not None:
                _fav_merchant_id, _fav_name, _fav_mcc = _fav
                mcc_code = _fav_mcc if _fav_mcc else (
                    get_mcc_for_profile(customer_profile)
                    if (self.use_profiles and customer_profile)
                    else self._mcc_cache.sample()
                )
                mcc_info = get_mcc_info(mcc_code)
                merchant_name = _fav_name
            else:
                _fav_from_session = False  # no favourite yet, fall through

        if not _fav_from_session:
            # Normal MCC selection (profile-aware)
            if self.use_profiles and customer_profile:
                mcc_code = get_mcc_for_profile(customer_profile)
            else:
                mcc_code = self._mcc_cache.sample()
            mcc_info = get_mcc_info(mcc_code)
            merchants = self._merchants_cache.get(mcc_code, ['Local Merchant'])  # OTIMIZAÇÃO 1.2
            merchant_name = random.choice(merchants)

        # Calculate value (uses mcc_info; resolved above regardless of path)
        valor = self._calculate_value(
            is_fraud,
            fraud_type,
            mcc_info,
            customer_profile
        )

        # Geolocation
        lat, lon = self._get_geolocation(customer_state, is_fraud, location_cluster)
        
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
            'ip_address': self._buf.next_ip(),
            'geolocation_lat': lat,
            'geolocation_lon': lon,
            'merchant_id': _fav_merchant_id or self._buf.next_merchant_id(),
            'merchant_name': merchant_name,
            'merchant_category': mcc_info['category'],
            'mcc_code': mcc_code,
            'mcc_risk_level': mcc_info['risk'],
            # Profile / demographics
            'cliente_perfil': customer_profile,
            'classe_social': _profile_to_classe_social(customer_profile),
            # T3 — velocity / card-testing fields (set by _apply_fraud_pattern)
            'card_test_phase': None,
            'velocity_burst_id': None,
            'distributed_attack_group': None,
        }
        
        # Add type-specific fields (uses pre-computed buffers)
        self._add_type_specific_fields(tx, tx_type, banco_destino, customer_id, customer_cpf)
        
        # OTIMIZAÇÃO 2: Apply fraud pattern characteristics if fraud
        if is_fraud and fraud_type:
            tx = self._apply_fraud_pattern(tx, fraud_type, customer_profile, timestamp)
        
        # Add risk indicators
        self._add_risk_indicators(tx, timestamp, is_fraud, fraud_type, session_state, customer_profile)
        
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
            return round(self._buf.next_uniform(5000, 50000), 2)
        elif fraud_type in ['CARTAO_CLONADO', 'CONTA_TOMADA']:
            return round(self._buf.next_uniform(500, 10000), 2)
        else:
            return round(self._buf.next_uniform(200, 5000), 2)
    
    def _get_geolocation(
        self,
        customer_state: Optional[str],
        is_fraud: bool,
        location_cluster: Optional[tuple] = None,
    ) -> Tuple[float, float]:
        """Get geolocation for transaction.

        Legitimate transactions (~95%) are drawn from the customer's habitual
        location cluster (home/work/shopping/other).  Fraud with HIGH location
        anomaly is placed in a random *different* state to enable impossible-
        travel detection; MEDIUM anomaly offsets the cluster by 1-3°.
        """
        # ── Fraud: HIGH location anomaly → completely different state
        if is_fraud and self._buf.next_float() < 0.3:
            diff_state = self._estado_cache.sample()
            info = ESTADOS_BR[diff_state]
            lat = round(info['lat'] + self._buf.next_uniform(-0.5, 0.5), 6)
            lon = round(info['lon'] + self._buf.next_uniform(-0.5, 0.5), 6)
            return lat, lon

        # ── Legitimate (or fraud without location anomaly): use cluster
        if location_cluster:
            lats   = [p[0] for p in location_cluster]
            lons   = [p[1] for p in location_cluster]
            wts    = [p[2] for p in location_cluster]
            idx    = random.choices(range(len(location_cluster)), weights=wts, k=1)[0]
            # small jitter within ~1km so the same "home" isn't one pixel
            lat = round(lats[idx] + self._buf.next_uniform(-0.01, 0.01), 6)
            lon = round(lons[idx] + self._buf.next_uniform(-0.01, 0.01), 6)
            return lat, lon

        # ── Fallback: state-level random (backward compat)
        if customer_state and customer_state in ESTADOS_BR:
            estado = customer_state
        else:
            estado = self._estado_cache.sample()
        info = ESTADOS_BR[estado]
        lat = round(info['lat'] + self._buf.next_uniform(-0.5, 0.5), 6)
        lon = round(info['lon'] + self._buf.next_uniform(-0.5, 0.5), 6)
        return lat, lon
    
    def _add_type_specific_fields(
        self,
        tx: dict,
        tx_type: str,
        banco_destino: str,
        customer_id: str = '',
        customer_cpf: Optional[str] = None,
    ) -> None:
        """Add transaction type-specific fields."""
        if tx_type in ['CREDIT_CARD', 'DEBIT_CARD']:
            card_brand = self._brand_cache.sample()
            tx.update({
                'card_number_hash': self._buf.next_hash16(),
                'card_brand': card_brand,
                'card_type': 'CREDIT' if tx_type == 'CREDIT_CARD' else 'DEBIT',
                'installments': self._installment_cache.sample() if tx_type == 'CREDIT_CARD' else 1,
                'card_entry': self._card_entry_cache.sample(),
                'cvv_validated': self._buf.next_bool(0.95),
                'auth_3ds': self._buf.next_bool(0.70),
                'pix_key_type': None,
                'pix_key_destination': None,
                'destination_bank': None,
                # PIX/BACEN fields — null for card transactions
                'end_to_end_id': None,
                'ispb_pagador': None,
                'ispb_recebedor': None,
                'tipo_conta_pagador': None,
                'tipo_conta_recebedor': None,
                'holder_type_recebedor': None,
                'modalidade_iniciacao': None,
                # TPRD3 PIX Fase 2 — null for card transactions
                'cpf_hash_pagador': None,
                'cpf_hash_recebedor': None,
                'pacs_status': None,
                'is_devolucao': None,
                'motivo_devolucao_med': None,
            })
        elif tx_type == 'PIX':
            pix_key_type = self._pix_type_cache.sample()
            ispb_pagador = self._buf.next_choice(self._ispb_list)
            ispb_recebedor = self._buf.next_choice(self._ispb_list)
            modalidade = self._buf.next_weighted('modalidade', MODALIDADE_INICIACAO_LIST, MODALIDADE_INICIACAO_WEIGHTS)
            ts_str = tx.get('timestamp', '')[:14].replace('-', '').replace('T', '').replace(':', '')
            seq = self._buf.next_hash16()[:10]
            e2e_id = generate_end_to_end_id(ispb_pagador, ts_str, seq)
            tx.update({
                'card_number_hash': None,
                'card_brand': None,
                'card_type': None,
                'installments': None,
                'card_entry': None,
                'cvv_validated': None,
                'auth_3ds': None,
                'pix_key_type': pix_key_type,
                'pix_key_destination': self._buf.next_hash32(),
                'destination_bank': banco_destino,
                # PIX/BACEN fields
                'end_to_end_id': e2e_id,
                'ispb_pagador': ispb_pagador,
                'ispb_recebedor': ispb_recebedor,
                'tipo_conta_pagador': self._buf.next_weighted('tipo_conta', TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS),
                'tipo_conta_recebedor': self._buf.next_weighted('tipo_conta', TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS),
                'holder_type_recebedor': self._buf.next_weighted('holder', HOLDER_TYPE_LIST, HOLDER_TYPE_WEIGHTS),
                'modalidade_iniciacao': modalidade,
                # TPRD3-LGPD: hashed CPFs (no plaintext CPF in output)
                'cpf_hash_pagador': hashlib.sha256(
                    (customer_cpf or customer_id).encode()
                ).hexdigest(),
                'cpf_hash_recebedor': hashlib.sha256(
                    generate_valid_cpf().encode()
                ).hexdigest(),
                # TPRD3: pacs.008 status and MED devolution fields
                'pacs_status': self._buf.next_weighted(
                    'pacs_status', ['ACSC', 'RJCT', 'PDNG'], [92, 6, 2]
                ),
                'is_devolucao': False,
                'motivo_devolucao_med': None,
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
                # PIX/BACEN fields — null for non-PIX transactions
                'end_to_end_id': None,
                'ispb_pagador': None,
                'ispb_recebedor': None,
                'tipo_conta_pagador': None,
                'tipo_conta_recebedor': None,
                'holder_type_recebedor': None,
                'modalidade_iniciacao': None,
                # TPRD3 PIX Fase 2 — null for non-PIX
                'cpf_hash_pagador': None,
                'cpf_hash_recebedor': None,
                'pacs_status': None,
                'is_devolucao': None,
                'motivo_devolucao_med': None,
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
                tx['velocity_transactions_24h'] = random.randint(min_burst, max_burst)
            else:
                tx['velocity_transactions_24h'] = random.randint(10, 30)
            
            # High accumulated amount
            tx['accumulated_amount_24h'] = round(tx['amount'] * tx['velocity_transactions_24h'] * random.uniform(0.6, 0.9), 2)
        elif characteristics.get('velocity') == 'MEDIUM':
            tx['velocity_transactions_24h'] = random.randint(5, 12)
            tx['accumulated_amount_24h'] = round(tx['amount'] * tx['velocity_transactions_24h'] * 0.7, 2)
        
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
                # Add PIX/BACEN fields that were not set (fraud pattern changed type to PIX)
                if not tx.get('end_to_end_id'):
                    ispb_pag = self._buf.next_choice(self._ispb_list)
                    ispb_rec = self._buf.next_choice(self._ispb_list)
                    ts_str = tx.get('timestamp', '')[:14].replace('-', '').replace('T', '').replace(':', '')
                    seq = self._buf.next_hash16()[:10]
                    tx['end_to_end_id'] = generate_end_to_end_id(ispb_pag, ts_str, seq)
                    tx['ispb_pagador'] = ispb_pag
                    tx['ispb_recebedor'] = ispb_rec
                    tx['tipo_conta_pagador'] = self._buf.next_weighted('tipo_conta', TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS)
                    tx['tipo_conta_recebedor'] = self._buf.next_weighted('tipo_conta', TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS)
                    tx['holder_type_recebedor'] = self._buf.next_weighted('holder', HOLDER_TYPE_LIST, HOLDER_TYPE_WEIGHTS)
                    tx['modalidade_iniciacao'] = self._buf.next_weighted('modalidade', MODALIDADE_INICIACAO_LIST, MODALIDADE_INICIACAO_WEIGHTS)
        
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
        
        # ---- T3: Card Testing phases ------------------------------------ #
        if fraud_type == 'CARD_TESTING':
            chars = characteristics
            if random.random() < 0.65:
                # Phase 1: micro-transactions
                lo, hi = chars.get('card_test_phase_1_amount', (0.01, 1.00))
                tx['amount'] = round(random.uniform(lo, hi), 2)
                tx['card_test_phase'] = 1
                # Multiple small merchants
                burst_min, burst_max = chars.get('transaction_burst', (3, 8))
                tx['velocity_transactions_24h'] = random.randint(burst_min, burst_max)
            else:
                # Phase 3: large transaction
                lo, hi = chars.get('card_test_phase_3_amount', (3000.0, 15000.0))
                tx['amount'] = round(random.uniform(lo, hi), 2)
                tx['card_test_phase'] = 3
                tx['velocity_transactions_24h'] = random.randint(1, 2)

        # ---- T3: Micro-Burst Velocity ------------------------------------ #
        elif fraud_type == 'MICRO_BURST_VELOCITY':
            import uuid as _uuid
            tx['velocity_burst_id'] = str(_uuid.uuid4())
            burst_min, burst_max = characteristics.get('transaction_burst', (10, 50))
            tx['velocity_transactions_24h'] = random.randint(burst_min, burst_max)
            window_min, window_max = characteristics.get('burst_window_minutes', (5, 15))
            # Compress timestamp into the burst window
            window_seconds = random.randint(window_min, window_max) * 60
            offset_s = random.randint(0, window_seconds)
            burst_ts = timestamp.replace(second=0, microsecond=0)
            from datetime import timedelta as _td
            burst_ts = burst_ts + _td(seconds=offset_s)
            tx['timestamp'] = burst_ts.isoformat()
            tx['accumulated_amount_24h'] = round(
                tx['amount'] * tx['velocity_transactions_24h'] * random.uniform(0.7, 0.9), 2
            )

        # ---- T3: Distributed Velocity ------------------------------------ #
        elif fraud_type == 'DISTRIBUTED_VELOCITY':
            import uuid as _uuid
            group_id = str(_uuid.uuid4())
            tx['distributed_attack_group'] = group_id
            per_min, per_max = characteristics.get('transactions_per_device', (2, 3))
            tx['velocity_transactions_24h'] = random.randint(per_min, per_max)  # Per device
            # Rotate device on each hit
            tx['device_id'] = f"DEV_DIST_{random.randint(100000, 999999):06d}"
            tx['ip_address'] = self._buf.next_ip()  # Fresh IP each time

        # FRAUD SCORE: Higher base score for pattern
        base_score = pattern.get('fraud_score_base', 0.5)
        tx['fraud_score'] = int(random.uniform(base_score * 100, 95))
        
        return tx
    
    def _add_risk_indicators(
        self,
        tx: dict,
        timestamp: datetime,
        is_fraud: bool,
        fraud_type: Optional[str],
        session_state: Optional[CustomerSessionState] = None,
        customer_profile: Optional[str] = None,
    ) -> None:
        """Add risk indicators to transaction."""
        hour = timestamp.hour
        unusual_time = hour < 6 or hour > 23
        
        if is_fraud:
            status = self._buf.next_weighted(
                'status_fraud',
                ['APPROVED', 'DECLINED', 'PENDING', 'BLOCKED'],
                [60, 25, 10, 5]
            )
            fraud_score = int(self._buf.next_uniform(65, 100))
            default_transactions_24h = self._buf.next_int(5, 50)
            default_accumulated_amount = round(self._buf.next_uniform(2000, 50000), 2)
        else:
            status = self._buf.next_weighted(
                'status_normal',
                ['APPROVED', 'DECLINED', 'PENDING'],
                [96, 3, 1]
            )
            fraud_score = int(self._buf.next_uniform(0, 35))
            default_transactions_24h = self._buf.next_int(1, 15)
            default_accumulated_amount = round(self._buf.next_uniform(50, 5000), 2)

        # Improved risk indicators with session state (OTIMIZAÇÃO 2.2/2.3)
        if session_state:
            # Velocity / accumulated (use session unless fraud pattern already set)
            if tx.get('velocity_transactions_24h') is None:
                tx['velocity_transactions_24h'] = session_state.get_velocity(timestamp) + 1
            if tx.get('accumulated_amount_24h') is None:
                tx['accumulated_amount_24h'] = round(
                    session_state.get_accumulated_24h(timestamp) + float(tx.get('amount', 0.0)),
                    2
                )

            # New beneficiary (merchant novelty)
            if tx.get('new_beneficiary') is None:
                tx['new_beneficiary'] = session_state.is_new_merchant(tx.get('merchant_id'))

            # T4: customer_velocity_z_score — deviation from profile baseline
            current_v = tx.get('velocity_transactions_24h') or 0
            v_mean, v_std = _PROFILE_VELOCITY_BASELINE.get(
                customer_profile, _PROFILE_VELOCITY_DEFAULT  # type: ignore[arg-type]
            )
            tx['customer_velocity_z_score'] = round(
                (current_v - v_mean) / max(v_std, 0.1), 2
            )

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
                tx['distance_from_last_txn_km'] = round(self._buf.next_uniform(0, 100), 2) if self._buf.next_float() > 0.5 else None
            if tx.get('time_since_last_txn_min') is None:
                tx['time_since_last_txn_min'] = self._buf.next_int(1, 1440) if self._buf.next_float() > 0.3 else None
            if tx.get('velocity_transactions_24h') is None:
                tx['velocity_transactions_24h'] = default_transactions_24h
            if tx.get('accumulated_amount_24h') is None:
                tx['accumulated_amount_24h'] = default_accumulated_amount
            if tx.get('new_beneficiary') is None:
                tx['new_beneficiary'] = self._buf.next_float() < (0.7 if is_fraud else 0.15)
        
        tx.update({
            'unusual_time': unusual_time,
            'status': status,
            'refusal_reason': self._buf.next_choice(REFUSAL_REASONS) if status == 'DECLINED' else None,
            'fraud_score': fraud_score,
            'is_fraud': is_fraud,
            'fraud_type': fraud_type,
        })

        # ── Context fields used by score pipeline ────────────────────────────
        # sim_swap_recent: higher for identity-takeover fraud types
        if tx.get('sim_swap_recent') is None:
            if is_fraud and fraud_type in ('CONTA_TOMADA', 'SIM_SWAP', 'ATO'):
                tx['sim_swap_recent'] = self._buf.next_float() < 0.65
            elif is_fraud:
                tx['sim_swap_recent'] = self._buf.next_float() < 0.10
            else:
                tx['sim_swap_recent'] = self._buf.next_float() < 0.01

        # ip_location_matches_account: geographic IP coherence
        if tx.get('ip_location_matches_account') is None:
            if is_fraud:
                tx['ip_location_matches_account'] = self._buf.next_float() < 0.35
            else:
                tx['ip_location_matches_account'] = self._buf.next_float() < 0.94

        # hours_inactive: coarse version of time_since_last_txn_min
        _tslt = tx.get('time_since_last_txn_min')
        tx['hours_inactive'] = int(_tslt / 60) if _tslt is not None else 0

        # new_merchant mirrors new_beneficiary (schema has both field names)
        if tx.get('new_merchant') is None:
            tx['new_merchant'] = tx.get('new_beneficiary')

        # TPRD3: MED devolution — confirmed fraud PIX transactions occasionally
        # trigger a devolution request (FR01/MD06). ~30% of fraud PIX events.
        if (
            is_fraud
            and tx.get('type') == 'PIX'
            and tx.get('is_devolucao') is False   # only override if PIX block set it
            and self._buf.next_float() < 0.30
        ):
            tx['is_devolucao'] = True
            tx['motivo_devolucao_med'] = self._buf.next_weighted(
                'motivo_devolucao', MOTIVO_DEVOLUCAO_LIST, MOTIVO_DEVOLUCAO_WEIGHTS
            )

        # ── Compute fraud_risk_score via the 17-signal pipeline ───────────────
        ctx = build_context_for_fraud(tx, is_fraud, fraud_type, rng=self._buf._rng)
        match_fraud_rule(ctx)
        tx['fraud_risk_score'] = compute_fraud_risk_score(ctx)

        # fraud_signals: human-readable list of active signals (non-zero)
        breakdown = score_breakdown(ctx)
        tx['fraud_signals'] = [
            sig for sig, val in breakdown.items()
            if sig != 'total' and val > 0
        ] or None
    
    def _generate_timestamp(
        self,
        start_date: datetime,
        end_date: datetime,
        customer_profile: Optional[str]
    ) -> datetime:
        """Generate realistic timestamp with DOW + seasonality weighting."""
        # ── T1: dia ponderado por dia-da-semana + sazonalidade ─────────────────
        random_day = pick_weighted_date(start_date.date(), end_date.date())

        # ── T1: hora com distribuição trimodal (picos 12h, 18h, 21h) ──────────
        if self.use_profiles and customer_profile:
            is_weekend = random_day.weekday() >= 5
            hour = get_transaction_hour_for_profile(customer_profile, is_weekend)
        else:
            hour = pick_hour(HORA_WEIGHTS_PADRAO)

        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        microsecond = random.randint(0, 999999)

        return datetime(
            random_day.year, random_day.month, random_day.day,
            hour, minute, second, microsecond
        )
