"""
Seasonality configuration for synthfin-data.

Provides realistic temporal weights for:
  - Hour of day (trimodal distribution: 10h, 14h, 19h peaks — BCB PIX 2024)
  - Hour of day per fraud category (commercial, delivery, ATO)
  - Day of week (Friday peak, weekend reduction)
  - Monthly fraud multiplier (STL decomposition — NB06 calibration)
  - Annual events (Black Friday, Christmas, 13th salary, Carnaval)
"""

import random
from datetime import date, timedelta
from functools import lru_cache
from typing import Dict, List, Tuple


# ─── Hourly weights — trimodal realista (Brasil 2024, fonte: BCB PIX) ─────────
# Pico 1 → 10h-11h  (abertura do comércio / inicio de pagamentos)
# Pico 2 → 14h-15h  (pós-almoço / movimentação comercial da tarde)
# Pico 3 → 19h-20h  (saída do trabalho / compras/pagamentos noturnos)
# Valle  → 01h-05h  (mínimo)
# 12h-13h: vale relativo (almoço — menos transações digitais)
# Fonte: pix.bcb.gov.br/estatisticas — série histórica horária 2023-2024

HORA_WEIGHTS_PADRAO: List[int] = [
    # 00  01  02  03  04  05  06  07  08  09  10  11
      2,  1,  1,  1,  1,  2,  5,  9, 14, 18, 26, 24,
    # 12  13  14  15  16  17  18  19  20  21  22  23
     14, 16, 26, 24, 18, 20, 22, 28, 26, 18, 12,  7,
]
HORA_LIST_PADRAO: List[int] = list(range(24))

# Versão mais quieta (madrugada) para fraudes de ATO/CONTA_TOMADA
HORA_WEIGHTS_FRAUD_ATO: List[int] = [
    # 00  01  02  03  04  05  06  07  08  09  10  11
      8, 25, 30, 25, 12,  5,  3,  2,  2,  2,  2,  2,
    # 12  13  14  15  16  17  18  19  20  21  22  23
      2,  2,  2,  2,  2,  3,  5,  6,  8, 12, 15, 10,
]

# Perfil horário comercial — falsa central, golpe investimento
HORA_WEIGHTS_COMERCIAL: List[int] = [
    # 00  01  02  03  04  05  06  07  08  09  10  11
      1,  1,  1,  1,  1,  2,  5, 10, 18, 22, 25, 20,
    # 12  13  14  15  16  17  18  19  20  21  22  23
     15, 18, 22, 20, 18, 12,  5,  3,  2,  1,  1,  1,
]

# Perfil horário delivery — almoço e jantar
HORA_WEIGHTS_DELIVERY: List[int] = [
    # 00  01  02  03  04  05  06  07  08  09  10  11
      3,  2,  1,  1,  1,  1,  2,  3,  5,  8, 12, 18,
    # 12  13  14  15  16  17  18  19  20  21  22  23
     22, 15, 10,  8,  8, 12, 20, 25, 22, 15, 10,  5,
]

# Mapeamento tipo de fraude → perfil horário
FRAUD_TYPE_HOUR_PROFILE: Dict[str, List[int]] = {
    'CONTA_TOMADA': HORA_WEIGHTS_FRAUD_ATO,
    'CREDENTIAL_STUFFING': HORA_WEIGHTS_FRAUD_ATO,
    'MAO_FANTASMA': HORA_WEIGHTS_FRAUD_ATO,
    'SIM_SWAP': HORA_WEIGHTS_FRAUD_ATO,
    'FALSA_CENTRAL_TELEFONICA': HORA_WEIGHTS_COMERCIAL,
    'GOLPE_INVESTIMENTO': HORA_WEIGHTS_COMERCIAL,
    'EMPRESTIMO_FRAUDULENTO': HORA_WEIGHTS_COMERCIAL,
    'FRAUDE_DELIVERY_APP': HORA_WEIGHTS_DELIVERY,
    # Todos os outros usam HORA_WEIGHTS_PADRAO via get default
}


def get_hour_weights_for_fraud(fraud_type: str) -> List[int]:
    """Retorna o perfil horário adequado para o tipo de fraude."""
    return FRAUD_TYPE_HOUR_PROFILE.get(fraud_type, HORA_WEIGHTS_PADRAO)


# ─── Pesos por dia da semana ──────────────────────────────────────────────────
# 0=Seg 1=Ter 2=Qua 3=Qui 4=Sex 5=Sab 6=Dom
DOW_WEIGHTS: List[int] = [10, 11, 11, 11, 14, 8, 6]
DOW_LIST: List[int] = list(range(7))


# ─── Sazonalidade mensal (calibrada via STL — NB06) ──────────────────────────
# Pico: Out-Nov (pré-Black Friday, 13º salário)
# Vale: Fev-Mar (Carnaval, menor atividade digital)
MONTHLY_FRAUD_MULTIPLIER: Dict[int, float] = {
    1: 0.85,   # Pós-festas
    2: 0.80,   # Carnaval — menor atividade digital
    3: 0.90,   # Vale sazonal
    4: 0.95,
    5: 1.00,   # Dia das Mães
    6: 1.05,   # Dia dos Namorados
    7: 0.95,
    8: 1.00,   # Dia dos Pais
    9: 1.05,
    10: 1.15,  # Pré-Black Friday
    11: 1.30,  # Black Friday + 13º 1ª parcela
    12: 1.20,  # Natal + 13º 2ª parcela
}


def get_monthly_multiplier(month: int) -> float:
    """Retorna multiplicador sazonal mensal (1.0 = média)."""
    return MONTHLY_FRAUD_MULTIPLIER.get(month, 1.0)


# ─── Eventos sazonais ─────────────────────────────────────────────────────────

@lru_cache(maxsize=10)
def _last_friday_of_november(year: int) -> date:
    """Retorna a última sexta-feira de novembro (Black Friday)."""
    d = date(year, 11, 30)
    while d.weekday() != 4:  # 4 = sexta
        d -= timedelta(days=1)
    return d


@lru_cache(maxsize=512)
def get_day_multiplier(d: date) -> float:
    """
    Retorna multiplicador de volume de transações para uma data específica.
    1.0 = dia normal. > 1 = mais transações esperadas.
    """
    month, day, dow = d.month, d.day, d.weekday()

    # Black Friday — última sexta de novembro
    bf = _last_friday_of_november(d.year)
    if d == bf:
        return 3.0
    if abs((d - bf).days) <= 2:   # BF e black weekend
        return 2.2

    # Christmas week (20–31 Dez)
    if month == 12 and day >= 20:
        return 2.0

    # 13º salário — 1ª parcela pagável em novembro, 2ª em dezembro
    if month == 11 and 5 <= day <= 20:
        return 1.5
    if month == 12 and 1 <= day <= 20:
        return 1.5

    # Dia dos Namorados (12/jun)
    if month == 6 and day == 12:
        return 1.6

    # Dia das Mães (2º domingo de maio)
    second_sunday = _nth_weekday_of_month(d.year, 5, 6, 2)
    if d == second_sunday:
        return 1.8

    # Dia dos Pais (2º domingo de agosto)
    second_sunday_aug = _nth_weekday_of_month(d.year, 8, 6, 2)
    if d == second_sunday_aug:
        return 1.6

    # Carnaval — aprox. 47 dias antes da Páscoa
    carnaval = _carnaval_monday(d.year)
    if carnaval and abs((d - carnaval).days) <= 3:
        return 0.7

    # Feriados nacionais fixos (volume reduzido = menos staff, mais oportunidade p/ fraude)
    feriados = {
        (1,  1): 0.6,   # Ano Novo
        (4,  21): 0.7,  # Tiradentes
        (5,  1): 0.7,   # Trabalhador
        (9,  7): 0.7,   # Independência
        (10, 12): 0.8,  # N. Sra. Aparecida
        (11, 2): 0.7,   # Finados
        (11, 15): 0.7,  # Proclamação
        (12, 25): 1.8,  # Natal
    }
    mult = feriados.get((month, day))
    if mult:
        return mult

    # Dia da semana base
    if dow == 4:    # Sexta
        return 1.15
    if dow == 5:    # Sábado
        return 0.75
    if dow == 6:    # Domingo
        return 0.60

    return 1.0


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Retorna a n-ésima ocorrência de weekday (0=Seg..6=Dom) em month/year."""
    d = date(year, month, 1)
    count = 0
    while True:
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
        d += timedelta(days=1)
        if d.month != month:
            return date(year, month, 1)  # fallback


def _carnaval_monday(year: int) -> date | None:
    """Calcula a segunda de carnaval (48 dias antes da Páscoa)."""
    easter = _easter(year)
    if easter is None:
        return None
    return easter - timedelta(days=48)


def _easter(year: int) -> date | None:
    """Algoritmo de Butcher para Páscoa."""
    try:
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)
    except Exception:
        return None


# ─── Seleção de data com pesos ────────────────────────────────────────────────

def pick_weighted_date(start: date, end: date) -> date:
    """
    Seleciona uma data entre start e end usando pesos de DOW × sazonalidade.
    
    Para ranges longos (> 180 dias) usa amostragem estocástica para manter
    performance O(1) amortizado em vez de construir lista de N datas.
    """
    total_days = (end - start).days
    if total_days <= 0:
        return start

    if total_days > 180:
        # Reservoir sampling: tenta até 15 candidatos com aceitação proporcional ao peso
        best_date = start + timedelta(days=random.randint(0, total_days))
        best_w = _date_weight(best_date)
        for _ in range(14):
            candidate = start + timedelta(days=random.randint(0, total_days))
            w = _date_weight(candidate)
            if random.random() < w / (best_w + w):
                best_date, best_w = candidate, w
        return best_date

    # Para ranges curtos, constrói a lista e faz choices ponderado
    days = [start + timedelta(days=i) for i in range(total_days + 1)]
    weights = [_date_weight(d) for d in days]
    return random.choices(days, weights=weights, k=1)[0]


def _date_weight(d: date) -> float:
    """Peso combinado: DOW × sazonalidade diária × sazonalidade mensal."""
    return DOW_WEIGHTS[d.weekday()] * get_day_multiplier(d) * get_monthly_multiplier(d.month)


def pick_hour(weights: List[int] = HORA_WEIGHTS_PADRAO) -> int:
    """Sorteia hora do dia usando os pesos fornecidos."""
    return random.choices(HORA_LIST_PADRAO, weights=weights, k=1)[0]
