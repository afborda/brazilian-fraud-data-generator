"""
Data model for Customer entity using dataclasses.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, Dict, Any
import json


@dataclass
class Address:
    """Brazilian address data."""
    logradouro: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    numero: Optional[str] = None
    complemento: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Customer:
    """
    Customer data model for Brazilian financial transactions.
    
    Attributes:
        customer_id: Unique identifier for the customer
        nome: Full name
        cpf: CPF number (with valid check digits)
        email: Email address
        telefone: Phone number in Brazilian format
        data_nascimento: Date of birth
        endereco: Brazilian address
        renda_mensal: Monthly income in BRL
        profissao: Profession/occupation
        conta_criada_em: Account creation date
        tipo_conta: Account type (CORRENTE, POUPANCA, DIGITAL)
        status_conta: Account status (ATIVA, BLOQUEADA, INATIVA)
        limite_credito: Credit limit in BRL
        score_credito: Credit score (300-900)
        nivel_risco: Risk level (BAIXO, MEDIO, ALTO)
        banco_codigo: Bank code (COMPE)
        banco_nome: Bank name
        agencia: Branch number
        numero_conta: Account number
        perfil_comportamental: Behavioral profile (young_digital, traditional_senior, etc.)
    """
    customer_id: str
    nome: str
    cpf: str
    email: str
    telefone: str
    data_nascimento: date
    endereco: Address
    renda_mensal: float
    profissao: str
    conta_criada_em: datetime
    tipo_conta: str
    status_conta: str
    limite_credito: float
    score_credito: int
    nivel_risco: str
    banco_codigo: str
    banco_nome: str
    agencia: str
    numero_conta: str
    perfil_comportamental: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        data = {
            'customer_id': self.customer_id,
            'nome': self.nome,
            'cpf': self.cpf,
            'email': self.email,
            'telefone': self.telefone,
            'data_nascimento': self.data_nascimento.isoformat() if isinstance(self.data_nascimento, date) else self.data_nascimento,
            'endereco': self.endereco.to_dict() if isinstance(self.endereco, Address) else self.endereco,
            'renda_mensal': self.renda_mensal,
            'profissao': self.profissao,
            'conta_criada_em': self.conta_criada_em.isoformat() if isinstance(self.conta_criada_em, datetime) else self.conta_criada_em,
            'tipo_conta': self.tipo_conta,
            'status_conta': self.status_conta,
            'limite_credito': self.limite_credito,
            'score_credito': self.score_credito,
            'nivel_risco': self.nivel_risco,
            'banco_codigo': self.banco_codigo,
            'banco_nome': self.banco_nome,
            'agencia': self.agencia,
            'numero_conta': self.numero_conta,
        }
        if self.perfil_comportamental:
            data['perfil_comportamental'] = self.perfil_comportamental
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        """Create Customer from dictionary."""
        # Handle nested Address
        endereco_data = data.get('endereco', {})
        if isinstance(endereco_data, dict):
            endereco = Address(**endereco_data)
        else:
            endereco = endereco_data
        
        # Handle date conversions
        data_nascimento = data.get('data_nascimento')
        if isinstance(data_nascimento, str):
            data_nascimento = date.fromisoformat(data_nascimento)
        
        conta_criada_em = data.get('conta_criada_em')
        if isinstance(conta_criada_em, str):
            conta_criada_em = datetime.fromisoformat(conta_criada_em)
        
        return cls(
            customer_id=data['customer_id'],
            nome=data['nome'],
            cpf=data['cpf'],
            email=data['email'],
            telefone=data['telefone'],
            data_nascimento=data_nascimento,
            endereco=endereco,
            renda_mensal=data['renda_mensal'],
            profissao=data['profissao'],
            conta_criada_em=conta_criada_em,
            tipo_conta=data['tipo_conta'],
            status_conta=data['status_conta'],
            limite_credito=data['limite_credito'],
            score_credito=data['score_credito'],
            nivel_risco=data['nivel_risco'],
            banco_codigo=data['banco_codigo'],
            banco_nome=data['banco_nome'],
            agencia=data['agencia'],
            numero_conta=data['numero_conta'],
            perfil_comportamental=data.get('perfil_comportamental'),
        )


@dataclass
class CustomerIndex:
    """
    Lightweight customer index for memory-efficient processing.
    
    This is used to maintain a reference to customers without loading
    all customer data into memory. Only essential fields are kept.
    
    Memory usage: ~50-80 bytes per customer vs ~800+ bytes for full Customer
    """
    customer_id: str
    estado: str
    perfil_comportamental: Optional[str] = None
    banco_codigo: Optional[str] = None
    nivel_risco: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"CustomerIndex({self.customer_id}, {self.estado}, {self.perfil_comportamental})"
