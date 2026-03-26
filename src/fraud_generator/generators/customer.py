"""
Customer generator for synthfin-data.
"""

import random
from datetime import datetime, date
from typing import Dict, Any, Optional, Iterator
from faker import Faker

from ..models.customer import Customer, Address, CustomerIndex
from ..validators.cpf import generate_valid_cpf, generate_cpf_from_state
from ..config.banks import BANKS, BANK_CODES, BANK_WEIGHTS
from ..config.geography import ESTADOS_LIST, ESTADOS_WEIGHTS, ESTADOS_BR
from ..config.municipios import pick_municipio, cep_for_municipio
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
        
        # State selection weighted by population; municipality within it
        estado    = random.choices(ESTADOS_LIST, weights=ESTADOS_WEIGHTS)[0]
        municipio = pick_municipio(estado, random)

        # Generate valid CPF for the state
        cpf = generate_cpf_from_state(estado, formatted=True)
        
        # Account creation date (older accounts for traditional profiles)
        if profile_config and perfil == 'traditional_senior':
            created_date = self.fake.date_time_between(start_date='-10y', end_date='-2y')
        else:
            created_date = self.fake.date_time_between(start_date='-5y', end_date='-1m')
        
        # Risk profile based on account age and profile
        account_age_days = (datetime.now() - created_date).days
        risk_level = self._calculate_risk_level(account_age_days, perfil)
        
        # Income based on profile and state (V6-M9: conditional on UF)
        renda = self._calculate_income(profile_config, estado)
        
        # Credit score correlates with income and account age
        score = self._calculate_credit_score(renda, account_age_days)
        
        # Bank selection weighted
        banco_codigo = random.choices(BANK_CODES, weights=BANK_WEIGHTS)[0]
        
        # Account type based on profile
        if profile_config and perfil in ['young_digital', 'subscription_heavy']:
            account_type = random.choices(
                ['DIGITAL', 'CHECKING', 'SAVINGS'],
                weights=[70, 25, 5]
            )[0]
        else:
            account_type = random.choices(
                ['CHECKING', 'SAVINGS', 'DIGITAL'],
                weights=[40, 20, 40]
            )[0]
        
        customer_data = {
            'customer_id': customer_id,
            'name': self.fake.name(),
            'cpf': cpf,
            'email': self.fake.email(),
            'phone': self.fake.phone_number(),
            'birth_date': data_nascimento.isoformat(),
            'address': {
                'street':       self.fake.street_address(),
                'neighborhood': self.fake.bairro(),
                'city':         municipio.name,
                'state':        estado,
                'postal_code':  cep_for_municipio(municipio, random),
                'codigo_ibge':  municipio.ibge,
            },
            'monthly_income': renda,
            'profession': self.fake.job(),
            'account_created_at': created_date.isoformat(),
            'account_type': account_type,
            'account_status': random.choices(
                ['ACTIVE', 'BLOCKED', 'INACTIVE'],
                weights=[95, 3, 2]
            )[0],
            'credit_limit': round(renda * random.uniform(2, 8), 2),
            'credit_score': score,
            'risk_level': risk_level,
            'bank_code': banco_codigo,
            'bank_name': BANKS[banco_codigo]['name'],
            'branch': f'{random.randint(1, 9999):04d}',
            'account_number': f'{random.randint(10000, 999999)}-{random.randint(0, 9)}',
        }
        
        if self.use_profiles and perfil:
            customer_data['behavioral_profile'] = perfil

        # ── V6-M5: Cadastral stability (Pacheco FGV 2019) ────────────────
        # Correlated with risk_level: HIGH → recent/unstable, LOW → stable
        if risk_level == 'HIGH':
            customer_data['address_age_days'] = random.randint(5, 120)
            customer_data['phone_age_days'] = random.randint(3, 90)
            customer_data['address_change_count_1y'] = random.choices([2, 3, 4, 5], weights=[30, 40, 20, 10])[0]
            customer_data['phone_change_count_1y'] = random.choices([2, 3, 4, 5, 6], weights=[20, 30, 30, 15, 5])[0]
        elif risk_level == 'MEDIUM':
            customer_data['address_age_days'] = random.randint(60, 730)
            customer_data['phone_age_days'] = random.randint(30, 365)
            customer_data['address_change_count_1y'] = random.choices([0, 1, 2], weights=[40, 40, 20])[0]
            customer_data['phone_change_count_1y'] = random.choices([0, 1, 2], weights=[30, 50, 20])[0]
        else:  # LOW
            customer_data['address_age_days'] = random.randint(365, 3650)
            customer_data['phone_age_days'] = random.randint(180, 2555)
            customer_data['address_change_count_1y'] = random.choices([0, 1], weights=[80, 20])[0]
            customer_data['phone_change_count_1y'] = random.choices([0, 1], weights=[70, 30])[0]

        # ── V6-M6: Bureau queries (Pacheco FGV 2019 — top predictor) ─────
        # VQt_ConsTOD_10d highest beta (0.206) in fraud models
        if risk_level == 'HIGH':
            customer_data['credit_bureau_queries_10d'] = random.choices(range(0, 12), weights=[5, 5, 10, 15, 20, 15, 10, 8, 5, 3, 2, 2])[0]
            customer_data['credit_bureau_queries_30d'] = customer_data['credit_bureau_queries_10d'] + random.randint(2, 15)
            customer_data['credit_bureau_queries_180d'] = customer_data['credit_bureau_queries_30d'] + random.randint(5, 40)
            customer_data['active_restrictions_count'] = random.choices([0, 1, 2, 3, 4, 5], weights=[20, 25, 25, 15, 10, 5])[0]
            customer_data['restrictions_resolved_1y'] = random.randint(0, 3)
        elif risk_level == 'MEDIUM':
            customer_data['credit_bureau_queries_10d'] = random.choices(range(0, 6), weights=[30, 30, 20, 10, 7, 3])[0]
            customer_data['credit_bureau_queries_30d'] = customer_data['credit_bureau_queries_10d'] + random.randint(0, 5)
            customer_data['credit_bureau_queries_180d'] = customer_data['credit_bureau_queries_30d'] + random.randint(1, 15)
            customer_data['active_restrictions_count'] = random.choices([0, 1, 2], weights=[60, 30, 10])[0]
            customer_data['restrictions_resolved_1y'] = random.choices([0, 1], weights=[70, 30])[0]
        else:  # LOW
            customer_data['credit_bureau_queries_10d'] = random.choices([0, 1, 2], weights=[60, 30, 10])[0]
            customer_data['credit_bureau_queries_30d'] = customer_data['credit_bureau_queries_10d'] + random.randint(0, 2)
            customer_data['credit_bureau_queries_180d'] = customer_data['credit_bureau_queries_30d'] + random.randint(0, 5)
            customer_data['active_restrictions_count'] = random.choices([0, 1], weights=[90, 10])[0]
            customer_data['restrictions_resolved_1y'] = 0

        # Credit score category (A-E)
        if score >= 750:
            customer_data['credit_score_category'] = 'A'
        elif score >= 600:
            customer_data['credit_score_category'] = 'B'
        elif score >= 450:
            customer_data['credit_score_category'] = 'C'
        elif score >= 350:
            customer_data['credit_score_category'] = 'D'
        else:
            customer_data['credit_score_category'] = 'E'
        
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
            state=customer_data['address']['state'],
            behavioral_profile=customer_data.get('behavioral_profile'),
            bank_code=customer_data.get('bank_code'),
            risk_level=customer_data.get('risk_level'),
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
        
        return random.choices(['HIGH', 'MEDIUM', 'LOW'], weights=weights)[0]
    
    def _calculate_income(self, profile_config, estado: str = 'SP') -> float:
        """Calculate monthly income based on profile and state (V6-M9)."""
        # IBGE PNAD 2023 — renda média por UF relative to national average
        _STATE_INCOME_MULT = {
            'DF': 1.75, 'SP': 1.25, 'RJ': 1.15, 'SC': 1.12, 'PR': 1.08,
            'RS': 1.05, 'ES': 0.95, 'MG': 0.95, 'GO': 0.92, 'MT': 1.00,
            'MS': 0.98, 'RO': 0.85, 'TO': 0.80, 'AC': 0.78, 'AM': 0.82,
            'RR': 0.80, 'AP': 0.78, 'PA': 0.75, 'MA': 0.62, 'PI': 0.65,
            'CE': 0.72, 'RN': 0.73, 'PB': 0.68, 'PE': 0.75, 'AL': 0.65,
            'SE': 0.72, 'BA': 0.73,
        }
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
        
        # V6-M9: Modulate by state median income
        state_mult = _STATE_INCOME_MULT.get(estado, 1.0)
        base_income *= state_mult
        
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
