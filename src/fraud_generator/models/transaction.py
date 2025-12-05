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
        tipo: Transaction type (PIX, CARTAO_CREDITO, etc.)
        valor: Transaction value in BRL
        moeda: Currency (always BRL)
        canal: Channel (APP_MOBILE, WEB_BANKING, etc.)
        ip_address: IP address
        geolocalizacao_lat: Latitude
        geolocalizacao_lon: Longitude
        merchant_id: Merchant identifier
        merchant_name: Merchant name
        merchant_category: Merchant category
        mcc_code: MCC code
        mcc_risk_level: MCC risk level
        
        # Card-specific fields
        numero_cartao_hash: Hashed card number
        bandeira: Card brand
        tipo_cartao: Card type (CREDITO, DEBITO)
        parcelas: Installments
        entrada_cartao: Card entry method
        cvv_validado: Whether CVV was validated
        autenticacao_3ds: Whether 3DS authentication was used
        
        # PIX-specific fields
        chave_pix_tipo: PIX key type
        chave_pix_destino: Destination PIX key hash
        banco_destino: Destination bank code
        
        # Risk indicators
        distancia_ultima_transacao_km: Distance from last transaction
        tempo_desde_ultima_transacao_min: Time since last transaction
        transacoes_ultimas_24h: Transactions in last 24h
        valor_acumulado_24h: Accumulated value in last 24h
        horario_incomum: Whether time is unusual
        novo_beneficiario: Whether beneficiary is new
        
        # Status and fraud
        status: Transaction status
        motivo_recusa: Refusal reason
        fraud_score: Fraud score
        is_fraud: Whether transaction is fraudulent
        fraud_type: Type of fraud
    """
    transaction_id: str
    customer_id: str
    session_id: str
    device_id: str
    timestamp: datetime
    tipo: str
    valor: float
    moeda: str
    canal: str
    ip_address: str
    geolocalizacao_lat: float
    geolocalizacao_lon: float
    merchant_id: str
    merchant_name: str
    merchant_category: str
    mcc_code: str
    mcc_risk_level: str
    
    # Card fields (optional)
    numero_cartao_hash: Optional[str] = None
    bandeira: Optional[str] = None
    tipo_cartao: Optional[str] = None
    parcelas: Optional[int] = None
    entrada_cartao: Optional[str] = None
    cvv_validado: Optional[bool] = None
    autenticacao_3ds: Optional[bool] = None
    
    # PIX fields (optional)
    chave_pix_tipo: Optional[str] = None
    chave_pix_destino: Optional[str] = None
    banco_destino: Optional[str] = None
    
    # Risk indicators
    distancia_ultima_transacao_km: Optional[float] = None
    tempo_desde_ultima_transacao_min: Optional[int] = None
    transacoes_ultimas_24h: int = 1
    valor_acumulado_24h: float = 0.0
    horario_incomum: bool = False
    novo_beneficiario: bool = False
    
    # Status and fraud
    status: str = 'APROVADA'
    motivo_recusa: Optional[str] = None
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
            'tipo': self.tipo,
            'valor': self.valor,
            'moeda': self.moeda,
            'canal': self.canal,
            'ip_address': self.ip_address,
            'geolocalizacao_lat': self.geolocalizacao_lat,
            'geolocalizacao_lon': self.geolocalizacao_lon,
            'merchant_id': self.merchant_id,
            'merchant_name': self.merchant_name,
            'merchant_category': self.merchant_category,
            'mcc_code': self.mcc_code,
            'mcc_risk_level': self.mcc_risk_level,
            'numero_cartao_hash': self.numero_cartao_hash,
            'bandeira': self.bandeira,
            'tipo_cartao': self.tipo_cartao,
            'parcelas': self.parcelas,
            'entrada_cartao': self.entrada_cartao,
            'cvv_validado': self.cvv_validado,
            'autenticacao_3ds': self.autenticacao_3ds,
            'chave_pix_tipo': self.chave_pix_tipo,
            'chave_pix_destino': self.chave_pix_destino,
            'banco_destino': self.banco_destino,
            'distancia_ultima_transacao_km': self.distancia_ultima_transacao_km,
            'tempo_desde_ultima_transacao_min': self.tempo_desde_ultima_transacao_min,
            'transacoes_ultimas_24h': self.transacoes_ultimas_24h,
            'valor_acumulado_24h': self.valor_acumulado_24h,
            'horario_incomum': self.horario_incomum,
            'novo_beneficiario': self.novo_beneficiario,
            'status': self.status,
            'motivo_recusa': self.motivo_recusa,
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
            tipo=data['tipo'],
            valor=data['valor'],
            moeda=data.get('moeda', 'BRL'),
            canal=data['canal'],
            ip_address=data['ip_address'],
            geolocalizacao_lat=data['geolocalizacao_lat'],
            geolocalizacao_lon=data['geolocalizacao_lon'],
            merchant_id=data['merchant_id'],
            merchant_name=data['merchant_name'],
            merchant_category=data['merchant_category'],
            mcc_code=data['mcc_code'],
            mcc_risk_level=data['mcc_risk_level'],
            numero_cartao_hash=data.get('numero_cartao_hash'),
            bandeira=data.get('bandeira'),
            tipo_cartao=data.get('tipo_cartao'),
            parcelas=data.get('parcelas'),
            entrada_cartao=data.get('entrada_cartao'),
            cvv_validado=data.get('cvv_validado'),
            autenticacao_3ds=data.get('autenticacao_3ds'),
            chave_pix_tipo=data.get('chave_pix_tipo'),
            chave_pix_destino=data.get('chave_pix_destino'),
            banco_destino=data.get('banco_destino'),
            distancia_ultima_transacao_km=data.get('distancia_ultima_transacao_km'),
            tempo_desde_ultima_transacao_min=data.get('tempo_desde_ultima_transacao_min'),
            transacoes_ultimas_24h=data.get('transacoes_ultimas_24h', 1),
            valor_acumulado_24h=data.get('valor_acumulado_24h', 0.0),
            horario_incomum=data.get('horario_incomum', False),
            novo_beneficiario=data.get('novo_beneficiario', False),
            status=data.get('status', 'APROVADA'),
            motivo_recusa=data.get('motivo_recusa'),
            fraud_score=data.get('fraud_score', 0.0),
            is_fraud=data.get('is_fraud', False),
            fraud_type=data.get('fraud_type'),
        )
