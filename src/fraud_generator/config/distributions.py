"""
Brazilian demographic & financial distributions for realistic data generation.

Sources:
  - IBGE PNAD Contínua 2023 (renda, escolaridade)
  - IBGE Censo 2022 (faixa etária, distribuição geográfica)
  - BACEN Relatório de Inclusão Financeira 2023 (perfil bancário)
  - Febraban 2023 (canais, tipos de conta)
"""

# ── Renda Mensal (BRL) ────────────────────────────────────────────────────────
# Baseado em quintis de renda PNAD 2023
# SM 2024 = R$1.412,00
INCOME_BRACKETS = [
    # (min, max, weight, label)
    (    0,  1_412, 25, "E"),       # Classe E — até 1 SM
    (1_412,  4_236, 30, "D"),       # Classe D — 1-3 SM
    (4_236,  8_472, 22, "C2"),      # Classe C2 — 3-6 SM
    (8_472, 14_120, 12, "C1"),      # Classe C1 — 6-10 SM
    (14_120, 35_300,  8, "B2"),     # Classe B2 — 10-25 SM
    (35_300, 84_720,  2, "B1"),     # Classe B1 — 25-60 SM
    (84_720, 300_000,  1, "A"),     # Classe A — acima 60 SM
]

INCOME_WEIGHTS = [b[2] for b in INCOME_BRACKETS]

def sample_monthly_income(rng=None) -> float:
    """Sample a monthly income from Brazilian distribution."""
    import random
    r = rng or random
    bracket = r.choices(INCOME_BRACKETS, weights=INCOME_WEIGHTS, k=1)[0]
    return round(r.uniform(bracket[0], bracket[1]), 2)

def get_income_class(income: float) -> str:
    """Return social class label for a given income."""
    for min_v, max_v, _, label in INCOME_BRACKETS:
        if min_v <= income < max_v:
            return label
    return "A"


# ── Faixa Etária ──────────────────────────────────────────────────────────────
# Distribuição da população bancarizada BACEN 2023 (18+ anos)
AGE_BRACKETS = [
    # (min_age, max_age, weight)
    (18, 24, 14),   # Jovens adultos
    (25, 34, 22),   # Adultos jovens
    (35, 44, 20),   # Adultos
    (45, 54, 18),   # Meia-idade
    (55, 64, 14),   # Pré-aposentadoria
    (65, 80,  9),   # Idosos
    (81, 95,  3),   # Longevos
]

AGE_WEIGHTS = [b[2] for b in AGE_BRACKETS]

def sample_age(rng=None) -> int:
    """Sample an age from Brazilian banked population distribution."""
    import random
    r = rng or random
    bracket = r.choices(AGE_BRACKETS, weights=AGE_WEIGHTS, k=1)[0]
    return r.randint(bracket[0], bracket[1])


# ── Escolaridade ──────────────────────────────────────────────────────────────
# PNAD Contínua 2023 — população 25+ anos
EDUCATION_LEVELS = [
    # (level, weight)
    ("sem_instrucao",           5),
    ("fundamental_incompleto", 18),
    ("fundamental_completo",   10),
    ("medio_incompleto",        8),
    ("medio_completo",         29),
    ("superior_incompleto",     8),
    ("superior_completo",      16),
    ("pos_graduacao",           6),
]

EDUCATION_WEIGHTS = [e[1] for e in EDUCATION_LEVELS]
EDUCATION_LIST    = [e[0] for e in EDUCATION_LEVELS]

def sample_education(rng=None) -> str:
    """Sample education level from Brazilian distribution."""
    import random
    r = rng or random
    return r.choices(EDUCATION_LIST, weights=EDUCATION_WEIGHTS, k=1)[0]


# ── Tipo de Conta Bancária ────────────────────────────────────────────────────
# Febraban 2023
ACCOUNT_TYPES = [
    ("CHECKING",  45),   # Conta corrente
    ("SAVINGS",   20),   # Poupança
    ("DIGITAL",   30),   # Conta digital (Nubank, Inter, etc.)
    ("SALARY",     5),   # Conta salário
]

ACCOUNT_TYPE_WEIGHTS = [a[1] for a in ACCOUNT_TYPES]
ACCOUNT_TYPE_LIST    = [a[0] for a in ACCOUNT_TYPES]

def sample_account_type(rng=None) -> str:
    import random
    r = rng or random
    return r.choices(ACCOUNT_TYPE_LIST, weights=ACCOUNT_TYPE_WEIGHTS, k=1)[0]


# ── Profissões por Classe Social ─────────────────────────────────────────────
PROFESSIONS_BY_CLASS: dict = {
    "E": [
        "Auxiliar de limpeza", "Catador de recicláveis", "Trabalhador rural",
        "Doméstica", "Feirante", "Motoboy", "Vendedor ambulante",
    ],
    "D": [
        "Operador de caixa", "Atendente de loja", "Motorista de ônibus",
        "Pedreiro", "Eletricista", "Cozinheiro", "Vendedor",
        "Auxiliar administrativo", "Técnico em informática",
    ],
    "C2": [
        "Professor", "Técnico de enfermagem", "Policial militar",
        "Comerciante", "Microempreendedor individual", "Contador",
        "Analista de suporte", "Corretor de imóveis",
    ],
    "C1": [
        "Engenheiro júnior", "Analista financeiro", "Gerente de loja",
        "Professor universitário", "Enfermeiro", "Advogado júnior",
        "Nutricionista", "Arquiteto",
    ],
    "B2": [
        "Gerente de banco", "Médico clínico geral", "Engenheiro sênior",
        "Diretor de empresa", "Dentista", "Farmacêutico proprietário",
        "Consultor", "Analista sênior",
    ],
    "B1": [
        "Médico especialista", "Juiz", "Dentista proprietário",
        "Sócio de empresa", "Diretor executivo", "Piloto comercial",
    ],
    "A": [
        "Empresário", "Diretor-CEO", "Investidor", "Médico renomado",
        "Juiz federal", "Desembargador",
    ],
}

def sample_profession(income_class: str, rng=None) -> str:
    """Sample a realistic profession for the given income class."""
    import random
    r = rng or random
    options = PROFESSIONS_BY_CLASS.get(income_class, PROFESSIONS_BY_CLASS["C2"])
    return r.choice(options)


# ── Score de Crédito (Serasa/Boa Vista) ──────────────────────────────────────
# Distribuição aproximada — 300 a 1000
CREDIT_SCORE_BY_CLASS: dict = {
    "E":  (300, 450),
    "D":  (370, 550),
    "C2": (450, 650),
    "C1": (550, 750),
    "B2": (650, 850),
    "B1": (750, 950),
    "A":  (800, 1000),
}

def sample_credit_score(income_class: str, rng=None) -> int:
    """Sample a credit score realistic for the income class."""
    import random
    r = rng or random
    lo, hi = CREDIT_SCORE_BY_CLASS.get(income_class, (400, 700))
    return r.randint(lo, hi)


# ── Limite de Crédito por Classe ──────────────────────────────────────────────

CREDIT_LIMIT_BY_CLASS: dict = {
    "E":  (0,      500),
    "D":  (0,    2_000),
    "C2": (500,  5_000),
    "C1": (2_000, 15_000),
    "B2": (5_000, 50_000),
    "B1": (20_000, 150_000),
    "A":  (50_000, 500_000),
}

def sample_credit_limit(income_class: str, rng=None) -> float:
    """Sample a credit limit realistic for the income class."""
    import random
    r = rng or random
    lo, hi = CREDIT_LIMIT_BY_CLASS.get(income_class, (0, 5_000))
    return round(r.uniform(lo, hi), 2)
