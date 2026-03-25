"""
Brazilian municipalities — IBGE codes, centroids, population weights
and representative CEP prefix ranges.

Data sources:
  - Código IBGE: IBGE (ibge.gov.br/geociencias/organizacao-do-territorio)
  - Centróides:  IBGE malha municipal 2022
  - População:   IBGE Censo 2022
  - Faixas CEP:  Correios / geoBR
"""

from __future__ import annotations

import csv
import logging
import os
import random
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

logger = logging.getLogger(__name__)


class Municipio(NamedTuple):
    ibge:    int    # 7-digit IBGE municipality code
    name:    str    # Municipality name
    uf:      str    # 2-letter state code
    lat:     float  # Centroid latitude  (decimal degrees)
    lon:     float  # Centroid longitude (decimal degrees)
    pop:     int    # 2022 census population (approx.)
    cep_min: int    # Min 5-digit CEP prefix  e.g. 1000 → "01000"
    cep_max: int    # Max 5-digit CEP prefix  e.g. 9999 → "09999"


# fmt: off
MUNICIPIOS: list[Municipio] = [
    # ── São Paulo ─────────────────────────────────────────────────────────────
    Municipio(3550308, "São Paulo",               "SP", -23.5505, -46.6333, 12325232,  1000,  9999),
    Municipio(3518800, "Guarulhos",               "SP", -23.4628, -46.5330,  1392121,  7000,  7399),
    Municipio(3509502, "Campinas",                "SP", -22.9099, -47.0626,  1213792, 13000, 13139),
    Municipio(3548708, "São Bernardo do Campo",   "SP", -23.6914, -46.5646,   844483,  9600,  9939),
    Municipio(3547809, "Santo André",             "SP", -23.6639, -46.5383,   748919,  9000,  9299),
    Municipio(3534401, "Osasco",                  "SP", -23.5324, -46.7920,   737399,  6000,  6279),
    Municipio(3549904, "São José dos Campos",     "SP", -23.1794, -45.8869,   729737, 12200, 12249),
    Municipio(3543402, "Ribeirão Preto",          "SP", -21.1775, -47.8103,   718069, 14000, 14110),
    Municipio(3552205, "Sorocaba",                "SP", -23.5015, -47.4526,   687357, 18000, 18115),
    Municipio(3530607, "Mogi das Cruzes",         "SP", -23.5225, -46.1878,   449611,  8700,  8799),
    Municipio(3548500, "Santos",                  "SP", -23.9608, -46.3342,   433966, 11000, 11099),
    Municipio(3529401, "Mauá",                    "SP", -23.6678, -46.4606,   478077,  9300,  9399),
    Municipio(3543303, "Ribeirão das Neves",      "SP", -23.2833, -47.0333,   327651, 18155, 18185),
    # ── Rio de Janeiro ────────────────────────────────────────────────────────
    Municipio(3304557, "Rio de Janeiro",          "RJ", -22.9068, -43.1729,  6747815, 20000, 26599),
    Municipio(3304904, "São Gonçalo",             "RJ", -22.8263, -43.0539,  1084839, 24400, 24470),
    Municipio(3301702, "Duque de Caxias",         "RJ", -22.7869, -43.3119,   924624, 25000, 25285),
    Municipio(3303500, "Nova Iguaçu",             "RJ", -22.7556, -43.4611,   821128, 26200, 26390),
    Municipio(3303302, "Niterói",                 "RJ", -22.8832, -43.1036,   502696, 24000, 24130),
    Municipio(3300456, "Belford Roxo",            "RJ", -22.7644, -43.3975,   524534, 26100, 26185),
    Municipio(3301900, "Campos dos Goytacazes",   "RJ", -21.7508, -41.3244,   497118, 28000, 28099),
    # ── Minas Gerais ──────────────────────────────────────────────────────────
    Municipio(3106200, "Belo Horizonte",          "MG", -19.9167, -43.9345,  2530701, 30000, 31999),
    Municipio(3170206, "Uberlândia",              "MG", -18.9186, -48.2772,   699097, 38400, 38411),
    Municipio(3118601, "Contagem",                "MG", -19.9317, -44.0536,   668838, 32000, 32380),
    Municipio(3136702, "Juiz de Fora",            "MG", -21.7604, -43.3503,   563769, 36000, 36081),
    Municipio(3106705, "Betim",                   "MG", -19.9680, -44.1986,   434058, 32600, 32680),
    Municipio(3143302, "Montes Claros",           "MG", -16.7286, -43.8617,   413487, 39400, 39409),
    Municipio(3170107, "Uberaba",                 "MG", -19.7472, -47.9317,   337092, 38000, 38099),
    # ── Bahia ─────────────────────────────────────────────────────────────────
    Municipio(2927408, "Salvador",                "BA", -12.9714, -38.5014,  2900319, 40000, 42499),
    Municipio(2910800, "Feira de Santana",        "BA", -12.2663, -38.9663,   641677, 44000, 44099),
    Municipio(2933307, "Vitória da Conquista",    "BA", -14.8661, -40.8444,   343230, 45000, 45059),
    Municipio(2905701, "Camaçari",                "BA", -12.6997, -38.3253,   376597, 42700, 42809),
    Municipio(2919207, "Lauro de Freitas",        "BA", -12.8989, -38.3300,   208196, 42700, 42729),
    # ── Rio Grande do Sul ─────────────────────────────────────────────────────
    Municipio(4314902, "Porto Alegre",            "RS", -30.0346, -51.2177,  1488252, 90000, 91999),
    Municipio(4305108, "Caxias do Sul",           "RS", -29.1634, -51.1797,   569682, 95000, 95099),
    Municipio(4304606, "Canoas",                  "RS", -29.9178, -51.1839,   350804, 92000, 92425),
    Municipio(4314100, "Pelotas",                 "RS", -31.7699, -52.3413,   342873, 96000, 96099),
    Municipio(4319901, "Santa Maria",             "RS", -29.6914, -53.8008,   287109, 97000, 97119),
    Municipio(4309209, "Gravataí",                "RS", -29.9444, -50.9911,   282783, 94000, 94099),
    Municipio(4314423, "Novo Hamburgo",           "RS", -29.6783, -51.1306,   248599, 93300, 93349),
    # ── Paraná ────────────────────────────────────────────────────────────────
    Municipio(4106902, "Curitiba",                "PR", -25.4284, -49.2733,  1948626, 80000, 82999),
    Municipio(4113700, "Londrina",                "PR", -23.3045, -51.1696,   585055, 86000, 86099),
    Municipio(4115200, "Maringá",                 "PR", -23.4273, -51.9375,   436123, 87000, 87099),
    Municipio(4119905, "Ponta Grossa",            "PR", -25.0939, -50.1609,   352198, 84000, 84099),
    Municipio(4125506, "São José dos Pinhais",    "PR", -25.5318, -49.2077,   354251, 83000, 83070),
    Municipio(4104808, "Cascavel",                "PR", -24.9578, -53.4553,   347397, 85800, 85819),
    Municipio(4108304, "Foz do Iguaçu",           "PR", -25.5478, -54.5882,   258543, 85850, 85869),
    # ── Pernambuco ────────────────────────────────────────────────────────────
    Municipio(2611606, "Recife",                  "PE",  -8.0539, -34.8811,  1661017, 50000, 52999),
    Municipio(2607901, "Jaboatão dos Guararapes", "PE",  -8.1136, -35.0089,   719261, 54000, 54420),
    Municipio(2609600, "Olinda",                  "PE",  -7.9997, -34.8448,   392430, 53000, 53430),
    Municipio(2604106, "Caruaru",                 "PE",  -8.2839, -35.9753,   366544, 55000, 55040),
    Municipio(2610707, "Petrolina",               "PE",  -9.3989, -40.5003,   354317, 56300, 56329),
    # ── Ceará ─────────────────────────────────────────────────────────────────
    Municipio(2304400, "Fortaleza",               "CE",  -3.7172, -38.5433,  2703391, 60000, 60999),
    Municipio(2303709, "Caucaia",                 "CE",  -3.7361, -38.6539,   370617, 61600, 61649),
    Municipio(2307304, "Juazeiro do Norte",       "CE",  -7.2133, -39.3148,   281973, 63000, 63048),
    Municipio(2304236, "Maracanaú",               "CE",  -3.8714, -38.6244,   231903, 61900, 61939),
    Municipio(2312908, "Sobral",                  "CE",  -3.6886, -40.3500,   221728, 62000, 62059),
    # ── Pará ──────────────────────────────────────────────────────────────────
    Municipio(1501402, "Belém",                   "PA",  -1.4558, -48.5044,  1499641, 66000, 66999),
    Municipio(1500800, "Ananindeua",              "PA",  -1.3656, -48.3728,   540410, 67000, 67135),
    Municipio(1507408, "Santarém",                "PA",  -2.4402, -54.7081,   325059, 68000, 68059),
    Municipio(1504208, "Marabá",                  "PA",  -5.3686, -49.1178,   281012, 68500, 68509),
    # ── Santa Catarina ────────────────────────────────────────────────────────
    Municipio(4205407, "Florianópolis",           "SC", -27.5954, -48.5480,   537211, 88000, 88139),
    Municipio(4209102, "Joinville",               "SC", -26.3044, -48.8487,   616622, 89200, 89239),
    Municipio(4202404, "Blumenau",                "SC", -26.9194, -49.0661,   361855, 89000, 89069),
    Municipio(4216602, "São José",                "SC", -27.5944, -48.6353,   262413, 88100, 88119),
    Municipio(4204202, "Chapecó",                 "SC", -27.1003, -52.6157,   224013, 89800, 89819),
    Municipio(4208203, "Itajaí",                  "SC", -26.9078, -48.6619,   228688, 88300, 88319),
    # ── Goiás ─────────────────────────────────────────────────────────────────
    Municipio(5208707, "Goiânia",                 "GO", -16.6869, -49.2648,  1536097, 74000, 74999),
    Municipio(5201405, "Aparecida de Goiânia",    "GO", -16.8232, -49.2464,   590908, 74900, 74995),
    Municipio(5201108, "Anápolis",                "GO", -16.3281, -48.9530,   391772, 75000, 75135),
    Municipio(5218805, "Rio Verde",               "GO", -17.7992, -50.9278,   234937, 75900, 75929),
    # ── Maranhão ──────────────────────────────────────────────────────────────
    Municipio(2111300, "São Luís",                "MA",  -2.5364, -44.3066,  1108975, 65000, 65139),
    Municipio(2105302, "Imperatriz",              "MA",  -5.5257, -47.4795,   258016, 65900, 65919),
    Municipio(2111532, "São José de Ribamar",     "MA",  -2.5600, -44.0561,   176017, 65100, 65119),
    # ── Paraíba ───────────────────────────────────────────────────────────────
    Municipio(2507507, "João Pessoa",             "PB",  -7.1195, -34.8450,   817511, 58000, 58099),
    Municipio(2504009, "Campina Grande",          "PB",  -7.2306, -35.8811,   416110, 58100, 58115),
    # ── Espírito Santo ────────────────────────────────────────────────────────
    Municipio(3205309, "Vitória",                 "ES", -20.3155, -40.3128,   365855, 29000, 29099),
    Municipio(3205200, "Vila Velha",              "ES", -20.3297, -40.2920,   501325, 29100, 29135),
    Municipio(3205010, "Serra",                   "ES", -20.1297, -40.3089,   527240, 29160, 29177),
    Municipio(3201308, "Cariacica",               "ES", -20.2633, -40.4172,   398269, 29140, 29159),
    # ── Amazonas ──────────────────────────────────────────────────────────────
    Municipio(1302603, "Manaus",                  "AM",  -3.1019, -60.0250,  2255903, 69000, 69099),
    Municipio(1301902, "Itacoatiara",             "AM",  -3.1433, -58.4444,   107975, 69100, 69109),
    # ── Rio Grande do Norte ───────────────────────────────────────────────────
    Municipio(2408102, "Natal",                   "RN",  -5.7945, -35.2110,   890786, 59000, 59099),
    Municipio(2408003, "Mossoró",                 "RN",  -5.1877, -37.3440,   301604, 59600, 59629),
    Municipio(2403251, "Parnamirim",              "RN",  -5.9139, -35.2636,   267642, 59140, 59169),
    # ── Piauí ─────────────────────────────────────────────────────────────────
    Municipio(2211001, "Teresina",                "PI",  -5.0892, -42.8019,   868075, 64000, 64099),
    Municipio(2209104, "Parnaíba",                "PI",  -2.9044, -41.7769,   153580, 64200, 64219),
    # ── Alagoas ───────────────────────────────────────────────────────────────
    Municipio(2704302, "Maceió",                  "AL",  -9.6658, -35.7350,  1025360, 57000, 57099),
    Municipio(2700300, "Arapiraca",               "AL",  -9.7525, -36.6611,   235659, 57300, 57319),
    # ── Mato Grosso ───────────────────────────────────────────────────────────
    Municipio(5103403, "Cuiabá",                  "MT", -15.5989, -56.0949,   655989, 78000, 78099),
    Municipio(5108402, "Várzea Grande",           "MT", -15.6467, -56.1319,   287526, 78100, 78125),
    Municipio(5107602, "Rondonópolis",            "MT", -16.4694, -54.6351,   232828, 78700, 78729),
    Municipio(5107925, "Sinop",                   "MT", -11.8642, -55.5044,   154163, 78550, 78559),
    # ── Mato Grosso do Sul ────────────────────────────────────────────────────
    Municipio(5002704, "Campo Grande",            "MS", -20.4428, -54.6462,   906092, 79000, 79149),
    Municipio(5003702, "Dourados",                "MS", -22.2211, -54.8117,   225495, 79800, 79829),
    # ── Distrito Federal ──────────────────────────────────────────────────────
    Municipio(5300108, "Brasília",                "DF", -15.7797, -47.9297,  3055149, 70000, 72999),
    # ── Sergipe ───────────────────────────────────────────────────────────────
    Municipio(2800308, "Aracaju",                 "SE", -10.9472, -37.0731,   664908, 49000, 49099),
    Municipio(2806701, "Nossa Senhora do Socorro","SE", -10.8528, -37.1242,   190842, 49160, 49179),
    # ── Rondônia ──────────────────────────────────────────────────────────────
    Municipio(1100205, "Porto Velho",             "RO",  -8.7612, -63.9039,   548952, 76800, 76869),
    Municipio(1100379, "Ji-Paraná",               "RO", -10.8786, -61.9508,   138391, 76900, 76919),
    # ── Tocantins ─────────────────────────────────────────────────────────────
    Municipio(1721000, "Palmas",                  "TO", -10.2491, -48.3243,   313588, 77000, 77099),
    Municipio(1702109, "Araguaína",               "TO",  -7.1928, -48.2041,   183382, 77800, 77829),
    # ── Acre ──────────────────────────────────────────────────────────────────
    Municipio(1200401, "Rio Branco",              "AC",  -9.9754, -67.8243,   413418, 69900, 69928),
    # ── Amapá ─────────────────────────────────────────────────────────────────
    Municipio(1600303, "Macapá",                  "AP",   0.0356, -51.0705,   503327, 68900, 68929),
    # ── Roraima ───────────────────────────────────────────────────────────────
    Municipio(1400100, "Boa Vista",               "RR",   2.8235, -60.6758,   419652, 69300, 69339),
]
# fmt: on

# ── Lookup helpers ────────────────────────────────────────────────────────────

_BY_UF:      dict[str, list[Municipio]] = {}
_WEIGHTS_BY_UF: dict[str, list[int]]   = {}

for _m in MUNICIPIOS:
    _BY_UF.setdefault(_m.uf, []).append(_m)

for _uf, _lst in _BY_UF.items():
    _WEIGHTS_BY_UF[_uf] = [m.pop for m in _lst]


def pick_municipio(uf: str, rng: random.Random) -> Municipio:
    """Return a population-weighted random municipality for the given UF."""
    candidates = _BY_UF.get(uf)
    if not candidates:
        return _BY_UF["SP"][0]  # safe fallback
    return rng.choices(candidates, weights=_WEIGHTS_BY_UF[uf], k=1)[0]


def cep_for_municipio(m: Municipio, rng: random.Random) -> str:
    """Return a verified real CEP for *m* when available, else a synthetic one.

    On the first call the pool is lazily loaded from
      $CEPS_REAIS_PATH  (env var, optional)
      <workspace>/data/ceps/ceps_reais.csv  (default)

    If the CSV is absent or has no entries for the municipality the function
    falls back to generating a plausible-but-unverified CEP from the numeric
    range stored in the Municipio tuple — exactly the previous behaviour.
    """
    return _real_cep_pool.pick(m, rng)


# ── Real CEP pool ─────────────────────────────────────────────────────────────

_DEFAULT_CEPS_CSV = (
    Path(__file__).resolve().parents[4] / "data" / "ceps" / "ceps_reais.csv"
)


class _RealCepPool:
    """Lazy-loading pool of verified CEPs grouped by IBGE city name + UF.

    Thread-safety is not required — the generator runs in a single thread.
    """

    def __init__(self) -> None:
        self._loaded = False
        # city_key → list[str]  where city_key = (municipio_nome.lower(), uf)
        self._by_city: Dict[tuple, List[str]] = {}
        # uf → list[str]  fallback when city not found
        self._by_uf: Dict[str, List[str]] = {}

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        csv_path = Path(os.environ.get("CEPS_REAIS_PATH", str(_DEFAULT_CEPS_CSV)))
        if not csv_path.is_file():
            logger.debug("ceps_reais.csv not found at %s — using synthetic CEPs.", csv_path)
            return

        try:
            with csv_path.open(encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    cep = row.get("cep", "").replace("-", "").strip()
                    if not cep or len(cep) != 8:
                        continue
                    city = (row.get("municipio", "").lower().strip(), row.get("uf", "").upper().strip())
                    uf   = row.get("uf", "").upper().strip()
                    formatted = f"{cep[:5]}-{cep[5:]}"
                    self._by_city.setdefault(city, []).append(formatted)
                    if uf:
                        self._by_uf.setdefault(uf, []).append(formatted)
            total = sum(len(v) for v in self._by_city.values())
            logger.info("RealCepPool: loaded %d CEPs from %s", total, csv_path)
        except Exception as exc:
            logger.warning("RealCepPool: failed to load %s — %s", csv_path, exc)

    def pick(self, m: Municipio, rng: random.Random) -> str:
        self._load()
        # 1. Exact city match
        city_key = (m.name.lower(), m.uf)
        pool = self._by_city.get(city_key)
        if pool:
            return rng.choice(pool)
        # 2. State-level fallback
        pool = self._by_uf.get(m.uf)
        if pool:
            return rng.choice(pool)
        # 3. Synthetic (unchanged legacy behaviour)
        prefix = rng.randint(m.cep_min, m.cep_max)
        suffix = rng.randint(0, 999)
        return f"{prefix:05d}-{suffix:03d}"


_real_cep_pool = _RealCepPool()

