"""
Customer generator for Brazilian Fraud Data Generator.
"""

import random
from datetime import datetime, date
from typing import Dict, Any, Optional, Iterator
from faker import Faker

from ..models.customer import Customer, Address, CustomerIndex
from ..validators.cpf import generate_valid_cpf, generate_cpf_from_state
from ..config.banks import BANKS, BANK_CODES, BANK_WEIGHTS
from ..config.geography import ESTADOS_LIST, ESTADOS_WEIGHTS, ESTADOS_BR
from ..profiles.behavioral import (
    assign_random_profile,
    get_profile,
    PROFILES,
)


class CustomerGenerator:
    """
    Generator for realistic Brazilian customer data.
    
    Features:
    - Valid CPF with check digits
    - Behavioral profiles
    - State-weighted distribution
    - Realistic income and credit scores
    """
    
    def __init__(
        self,
        use_profiles: bool = True,
        locale: str = 'pt_BR',
        seed: Optional[int] = None
    ):
        """
        Initialize customer generator.
        
        Args:
            use_profiles: If True, assign behavioral profiles
            locale: Faker locale
            seed: Random seed for reproducibility
        """
        self.use_profiles = use_profiles
        self.fake = Faker(locale)
        
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
    
    def generate(self, customer_id: str) -> Dict[str, Any]:
        """
        Generate a single customer.
        
        Args:
            customer_id: Unique identifier for the customer
        
        Returns:
            Customer data as dictionary
        """
        # Assign profile first (affects other attributes)
        perfil = assign_random_profile() if self.use_profiles else None
        profile_config = get_profile(perfil) if perfil else None
        
        # Age based on profile
        if profile_config:
            min_age, max_age = profile_config.age_range
            idade = random.randint(min_age, max_age)
        else:
            idade = random.randint(18, 80)
        
        # Calculate birth date from age
        today = date.today()
        birth_year = today.year - idade
        data_nascimento = self.fake.date_of_birth(
            minimum_age=idade,
            maximum_age=idade
        )
        
        # State selection weighted by population
        estado = random.choices(ESTADOS_LIST, weights=ESTADOS_WEIGHTS)[0]
        
        # Generate valid CPF for the state
        cpf = generate_cpf_from_state(estado, formatted=True)
        
        # Account creation date (older accounts for traditional profiles)
        if profile_config and perfil == 'traditional_senior':
            created_date = self.fake.date_time_between(start_date='-10y', end_date='-2y')
        else:
            created_date = self.fake.date_time_between(start_date='-5y', end_date='-1m')
        
        # Risk profile based on account age and profile
        account_age_days = (datetime.now() - created_date).days
        nivel_risco = self._calculate_risk_level(account_age_days, perfil)
        
        # Income based on profile
        renda = self._calculate_income(profile_config)
        
        # Credit score correlates with income and account age
        score = self._calculate_credit_score(renda, account_age_days)
        
        # Bank selection weighted
        banco_codigo = random.choices(BANK_CODES, weights=BANK_WEIGHTS)[0]
        
        # Account type based on profile
        if profile_config and perfil in ['young_digital', 'subscription_heavy']:
            tipo_conta = random.choices(
                ['DIGITAL', 'CORRENTE', 'POUPANCA'],
                weights=[70, 25, 5]
            )[0]
        else:
            tipo_conta = random.choices(
                ['CORRENTE', 'POUPANCA', 'DIGITAL'],
                weights=[40, 20, 40]
            )[0]
        
        customer_data = {
            'customer_id': customer_id,
            'nome': self.fake.name(),
            'cpf': cpf,
            'email': self.fake.email(),
            'telefone': self.fake.phone_number(),
            'data_nascimento': data_nascimento.isoformat(),
            'endereco': {
                'logradouro': self.fake.street_address(),
                'bairro': self.fake.bairro(),
                'cidade': self.fake.city(),
                'estado': estado,
                'cep': self.fake.postcode(),
            },
            'renda_mensal': renda,
            'profissao': self.fake.job(),
            'conta_criada_em': created_date.isoformat(),
            'tipo_conta': tipo_conta,
            'status_conta': random.choices(
                ['ATIVA', 'BLOQUEADA', 'INATIVA'],
                weights=[95, 3, 2]
            )[0],
            'limite_credito': round(renda * random.uniform(2, 8), 2),
            'score_credito': score,
            'nivel_risco': nivel_risco,
            'banco_codigo': banco_codigo,
            'banco_nome': BANKS[banco_codigo]['nome'],
            'agencia': f'{random.randint(1, 9999):04d}',
            'numero_conta': f'{random.randint(10000, 999999)}-{random.randint(0, 9)}',
        }
        
        if self.use_profiles and perfil:
            customer_data['perfil_comportamental'] = perfil
        
        return customer_data
    
    def generate_batch(
        self,
        count: int,
        start_id: int = 1
    ) -> Iterator[Dict[str, Any]]:
        """
        Generate multiple customers.
        
        Args:
            count: Number of customers to generate
            start_id: Starting ID number
        
        Yields:
            Customer data dictionaries
        """
        for i in range(count):
            customer_id = f"CUST_{start_id + i:012d}"
            yield self.generate(customer_id)
    
    def generate_index(self, customer_data: Dict[str, Any]) -> CustomerIndex:
        """Create a lightweight index from customer data."""
        return CustomerIndex(
            customer_id=customer_data['customer_id'],
            estado=customer_data['endereco']['estado'],
            perfil=customer_data.get('perfil_comportamental'),
            banco_codigo=customer_data.get('banco_codigo'),
            nivel_risco=customer_data.get('nivel_risco'),
        )
    
    def _calculate_risk_level(
        self,
        account_age_days: int,
        perfil: Optional[str]
    ) -> str:
        """Calculate risk level based on account age and profile."""
        if account_age_days < 30:
            weights = [30, 50, 20]
        elif account_age_days < 180:
            weights = [10, 40, 50]
        else:
            weights = [5, 25, 70]
        
        # Adjust for profile
        if perfil == 'high_spender':
            weights = [15, 35, 50]  # Higher value = higher target
        elif perfil == 'traditional_senior':
            weights = [20, 40, 40]  # More susceptible to scams
        
        return random.choices(['ALTO', 'MEDIO', 'BAIXO'], weights=weights)[0]
    
    def _calculate_income(self, profile_config) -> float:
        """Calculate monthly income based on profile."""
        # Base income distribution (realistic for Brazil)
        base_ranges = [
            (1500, 3000, 40),
            (3000, 7000, 35),
            (7000, 15000, 18),
            (15000, 50000, 7),
        ]
        
        # Select base range
        ranges, weights = zip(*[(r[:2], r[2]) for r in base_ranges])
        selected_range = random.choices(ranges, weights=weights)[0]
        base_income = random.uniform(*selected_range)
        
        # Apply profile multiplier
        if profile_config:
            min_mult, max_mult = profile_config.income_multiplier
            multiplier = random.uniform(min_mult, max_mult)
            base_income *= multiplier
        
        return round(base_income, 2)
    
    def _calculate_credit_score(self, renda: float, account_age_days: int) -> int:
        """Calculate credit score based on income and account age."""
        base_score = 300 + (account_age_days / 30) * 5
        
        if renda > 10000:
            base_score += 100
        elif renda > 5000:
            base_score += 50
        
        score = int(base_score + random.gauss(100, 50))
        return min(900, max(300, score))
