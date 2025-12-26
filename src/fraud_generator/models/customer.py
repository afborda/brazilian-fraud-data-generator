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
    street: str  # logradouro
    neighborhood: str  # bairro
    city: str  # cidade
    state: str  # estado
    postal_code: str  # cep
    number: Optional[str] = None  # numero
    complement: Optional[str] = None  # complemento
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Customer:
    """
    Customer data model for Brazilian financial transactions.
    
    Attributes:
        customer_id: Unique identifier for the customer
        name: Full name
        cpf: CPF number (with valid check digits)
        email: Email address
        phone: Phone number in Brazilian format
        birth_date: Date of birth
        address: Brazilian address
        monthly_income: Monthly income in BRL
        profession: Profession/occupation
        account_created_at: Account creation date
        account_type: Account type (CHECKING, SAVINGS, DIGITAL)
        account_status: Account status (ACTIVE, BLOCKED, INACTIVE)
        credit_limit: Credit limit in BRL
        credit_score: Credit score (300-900)
        risk_level: Risk level (LOW, MEDIUM, HIGH)
        bank_code: Bank code (COMPE)
        bank_name: Bank name
        branch: Branch number
        account_number: Account number
        behavioral_profile: Behavioral profile (young_digital, traditional_senior, etc.)
    """
    customer_id: str
    name: str  # nome
    cpf: str
    email: str
    phone: str  # telefone
    birth_date: date  # data_nascimento
    address: Address  # endereco
    monthly_income: float  # renda_mensal
    profession: str  # profissao
    account_created_at: datetime  # conta_criada_em
    account_type: str  # tipo_conta
    account_status: str  # status_conta
    credit_limit: float  # limite_credito
    credit_score: int  # score_credito
    risk_level: str  # nivel_risco
    bank_code: str  # banco_codigo
    bank_name: str  # banco_nome
    branch: str  # agencia
    account_number: str  # numero_conta
    behavioral_profile: Optional[str] = None  # perfil_comportamental
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        data = {
            'customer_id': self.customer_id,
            'name': self.name,
            'cpf': self.cpf,
            'email': self.email,
            'phone': self.phone,
            'birth_date': self.birth_date.isoformat() if isinstance(self.birth_date, date) else self.birth_date,
            'address': self.address.to_dict() if isinstance(self.address, Address) else self.address,
            'monthly_income': self.monthly_income,
            'profession': self.profession,
            'account_created_at': self.account_created_at.isoformat() if isinstance(self.account_created_at, datetime) else self.account_created_at,
            'account_type': self.account_type,
            'account_status': self.account_status,
            'credit_limit': self.credit_limit,
            'credit_score': self.credit_score,
            'risk_level': self.risk_level,
            'bank_code': self.bank_code,
            'bank_name': self.bank_name,
            'branch': self.branch,
            'account_number': self.account_number,
        }
        if self.behavioral_profile:
            data['behavioral_profile'] = self.behavioral_profile
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        """Create Customer from dictionary."""
        # Handle nested Address
        address_data = data.get('address', {})
        if isinstance(address_data, dict):
            address = Address(**address_data)
        else:
            address = address_data
        
        # Handle date conversions
        birth_date = data.get('birth_date')
        if isinstance(birth_date, str):
            birth_date = date.fromisoformat(birth_date)
        
        account_created_at = data.get('account_created_at')
        if isinstance(account_created_at, str):
            account_created_at = datetime.fromisoformat(account_created_at)
        
        return cls(
            customer_id=data['customer_id'],
            name=data['name'],
            cpf=data['cpf'],
            email=data['email'],
            phone=data['phone'],
            birth_date=birth_date,
            address=address,
            monthly_income=data['monthly_income'],
            profession=data['profession'],
            account_created_at=account_created_at,
            account_type=data['account_type'],
            account_status=data['account_status'],
            credit_limit=data['credit_limit'],
            credit_score=data['credit_score'],
            risk_level=data['risk_level'],
            bank_code=data['bank_code'],
            bank_name=data['bank_name'],
            branch=data['branch'],
            account_number=data['account_number'],
            behavioral_profile=data.get('behavioral_profile'),
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
    state: str  # estado
    behavioral_profile: Optional[str] = None  # perfil_comportamental
    bank_code: Optional[str] = None  # banco_codigo
    risk_level: Optional[str] = None  # nivel_risco
    
    def __repr__(self) -> str:
        return f"CustomerIndex({self.customer_id}, {self.state}, {self.behavioral_profile})"
