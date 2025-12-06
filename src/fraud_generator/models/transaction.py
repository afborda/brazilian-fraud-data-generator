"""
Data model for Transaction entity using dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class Transaction:
    """
    Transaction data model for Brazilian financial transactions.
    
    Attributes:
        transaction_id: Unique identifier for the transaction
        customer_id: Associated customer ID
        session_id: Session identifier
        device_id: Device used for the transaction
        timestamp: Transaction timestamp
        type: Transaction type (PIX, CREDIT_CARD, etc.)
        amount: Transaction value in BRL
        currency: Currency (always BRL)
        channel: Channel (MOBILE_APP, WEB_BANKING, etc.)
        ip_address: IP address
        geolocation_lat: Latitude
        geolocation_lon: Longitude
        merchant_id: Merchant identifier
        merchant_name: Merchant name
        merchant_category: Merchant category
        mcc_code: MCC code
        mcc_risk_level: MCC risk level
        
        # Card-specific fields
        card_number_hash: Hashed card number
        card_brand: Card brand
        card_type: Card type (CREDIT, DEBIT)
        installments: Number of installments
        card_entry: Card entry method
        cvv_validated: Whether CVV was validated
        auth_3ds: Whether 3DS authentication was used
        
        # PIX-specific fields
        pix_key_type: PIX key type
        pix_key_destination: Destination PIX key hash
        destination_bank: Destination bank code
        
        # Risk indicators
        distance_from_last_txn_km: Distance from last transaction
        time_since_last_txn_min: Time since last transaction
        transactions_last_24h: Transactions in last 24h
        accumulated_amount_24h: Accumulated value in last 24h
        unusual_time: Whether time is unusual
        new_beneficiary: Whether beneficiary is new
        
        # Status and fraud
        status: Transaction status
        refusal_reason: Refusal reason
        fraud_score: Fraud score
        is_fraud: Whether transaction is fraudulent
        fraud_type: Type of fraud
    """
    transaction_id: str
    customer_id: str
    session_id: str
    device_id: str
    timestamp: datetime
    type: str  # tipo
    amount: float  # valor
    currency: str  # moeda
    channel: str  # canal
    ip_address: str
    geolocation_lat: float  # geolocalizacao_lat
    geolocation_lon: float  # geolocalizacao_lon
    merchant_id: str
    merchant_name: str
    merchant_category: str
    mcc_code: str
    mcc_risk_level: str
    
    # Card fields (optional)
    card_number_hash: Optional[str] = None  # numero_cartao_hash
    card_brand: Optional[str] = None  # bandeira
    card_type: Optional[str] = None  # tipo_cartao
    installments: Optional[int] = None  # parcelas
    card_entry: Optional[str] = None  # entrada_cartao
    cvv_validated: Optional[bool] = None  # cvv_validado
    auth_3ds: Optional[bool] = None  # autenticacao_3ds
    
    # PIX fields (optional)
    pix_key_type: Optional[str] = None  # chave_pix_tipo
    pix_key_destination: Optional[str] = None  # chave_pix_destino
    destination_bank: Optional[str] = None  # banco_destino
    
    # Risk indicators
    distance_from_last_txn_km: Optional[float] = None  # distancia_ultima_transacao_km
    time_since_last_txn_min: Optional[int] = None  # tempo_desde_ultima_transacao_min
    transactions_last_24h: int = 1  # transacoes_ultimas_24h
    accumulated_amount_24h: float = 0.0  # valor_acumulado_24h
    unusual_time: bool = False  # horario_incomum
    new_beneficiary: bool = False  # novo_beneficiario
    
    # Status and fraud
    status: str = 'APPROVED'  # APROVADA
    refusal_reason: Optional[str] = None  # motivo_recusa
    fraud_score: float = 0.0
    is_fraud: bool = False
    fraud_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        data = {
            'transaction_id': self.transaction_id,
            'customer_id': self.customer_id,
            'session_id': self.session_id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'type': self.type,
            'amount': self.amount,
            'currency': self.currency,
            'channel': self.channel,
            'ip_address': self.ip_address,
            'geolocation_lat': self.geolocation_lat,
            'geolocation_lon': self.geolocation_lon,
            'merchant_id': self.merchant_id,
            'merchant_name': self.merchant_name,
            'merchant_category': self.merchant_category,
            'mcc_code': self.mcc_code,
            'mcc_risk_level': self.mcc_risk_level,
            'card_number_hash': self.card_number_hash,
            'card_brand': self.card_brand,
            'card_type': self.card_type,
            'installments': self.installments,
            'card_entry': self.card_entry,
            'cvv_validated': self.cvv_validated,
            'auth_3ds': self.auth_3ds,
            'pix_key_type': self.pix_key_type,
            'pix_key_destination': self.pix_key_destination,
            'destination_bank': self.destination_bank,
            'distance_from_last_txn_km': self.distance_from_last_txn_km,
            'time_since_last_txn_min': self.time_since_last_txn_min,
            'transactions_last_24h': self.transactions_last_24h,
            'accumulated_amount_24h': self.accumulated_amount_24h,
            'unusual_time': self.unusual_time,
            'new_beneficiary': self.new_beneficiary,
            'status': self.status,
            'refusal_reason': self.refusal_reason,
            'fraud_score': self.fraud_score,
            'is_fraud': self.is_fraud,
            'fraud_type': self.fraud_type,
        }
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create Transaction from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            transaction_id=data['transaction_id'],
            customer_id=data['customer_id'],
            session_id=data['session_id'],
            device_id=data['device_id'],
            timestamp=timestamp,
            type=data['type'],
            amount=data['amount'],
            currency=data.get('currency', 'BRL'),
            channel=data['channel'],
            ip_address=data['ip_address'],
            geolocation_lat=data['geolocation_lat'],
            geolocation_lon=data['geolocation_lon'],
            merchant_id=data['merchant_id'],
            merchant_name=data['merchant_name'],
            merchant_category=data['merchant_category'],
            mcc_code=data['mcc_code'],
            mcc_risk_level=data['mcc_risk_level'],
            card_number_hash=data.get('card_number_hash'),
            card_brand=data.get('card_brand'),
            card_type=data.get('card_type'),
            installments=data.get('installments'),
            card_entry=data.get('card_entry'),
            cvv_validated=data.get('cvv_validated'),
            auth_3ds=data.get('auth_3ds'),
            pix_key_type=data.get('pix_key_type'),
            pix_key_destination=data.get('pix_key_destination'),
            destination_bank=data.get('destination_bank'),
            distance_from_last_txn_km=data.get('distance_from_last_txn_km'),
            time_since_last_txn_min=data.get('time_since_last_txn_min'),
            transactions_last_24h=data.get('transactions_last_24h', 1),
            accumulated_amount_24h=data.get('accumulated_amount_24h', 0.0),
            unusual_time=data.get('unusual_time', False),
            new_beneficiary=data.get('new_beneficiary', False),
            status=data.get('status', 'APPROVED'),
            refusal_reason=data.get('refusal_reason'),
            fraud_score=data.get('fraud_score', 0.0),
            is_fraud=data.get('is_fraud', False),
            fraud_type=data.get('fraud_type'),
        )
