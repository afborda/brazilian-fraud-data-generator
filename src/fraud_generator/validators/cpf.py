"""
CPF Validator and Generator for Brazilian Fraud Data Generator.

Implements the official CPF validation algorithm from Receita Federal do Brasil.
CPF format: XXX.XXX.XXX-DD (11 digits total, last 2 are check digits)

The algorithm uses modulo 11 calculation with weighted sums.
"""

from typing import Tuple
import random


def calculate_check_digits(cpf_base: str) -> Tuple[int, int]:
    """
    Calculate the two check digits for a 9-digit CPF base.
    
    Args:
        cpf_base: First 9 digits of the CPF (without check digits)
    
    Returns:
        Tuple of (first_digit, second_digit)
    
    Raises:
        ValueError: If cpf_base is not exactly 9 digits
    """
    if len(cpf_base) != 9 or not cpf_base.isdigit():
        raise ValueError("CPF base must be exactly 9 digits")
    
    # Calculate first check digit (10th digit)
    # Multiply each of the 9 digits by weights 10, 9, 8, 7, 6, 5, 4, 3, 2
    weights_first = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_first = sum(int(d) * w for d, w in zip(cpf_base, weights_first))
    remainder_first = sum_first % 11
    first_digit = 0 if remainder_first < 2 else 11 - remainder_first
    
    # Calculate second check digit (11th digit)
    # Multiply each of the 10 digits (9 base + first check) by weights 11, 10, 9, 8, 7, 6, 5, 4, 3, 2
    cpf_with_first = cpf_base + str(first_digit)
    weights_second = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_second = sum(int(d) * w for d, w in zip(cpf_with_first, weights_second))
    remainder_second = sum_second % 11
    second_digit = 0 if remainder_second < 2 else 11 - remainder_second
    
    return first_digit, second_digit


def generate_valid_cpf(formatted: bool = False) -> str:
    """
    Generate a random CPF with valid check digits.
    
    Args:
        formatted: If True, return CPF in format XXX.XXX.XXX-DD
                  If False, return as 11 digits without formatting
    
    Returns:
        Valid CPF string
    
    Example:
        >>> cpf = generate_valid_cpf()
        >>> len(cpf)
        11
        >>> validate_cpf(cpf)
        True
        
        >>> cpf_formatted = generate_valid_cpf(formatted=True)
        >>> len(cpf_formatted)
        14
        >>> cpf_formatted[3]
        '.'
    """
    # Generate random 9-digit base (avoiding all same digits like 000000000)
    while True:
        cpf_base = ''.join(str(random.randint(0, 9)) for _ in range(9))
        # Avoid invalid patterns (all same digits)
        if len(set(cpf_base)) > 1:
            break
    
    # Calculate valid check digits
    first_digit, second_digit = calculate_check_digits(cpf_base)
    
    # Build complete CPF
    cpf = cpf_base + str(first_digit) + str(second_digit)
    
    if formatted:
        return format_cpf(cpf)
    
    return cpf


def format_cpf(cpf: str) -> str:
    """
    Format a CPF string to XXX.XXX.XXX-DD format.
    
    Args:
        cpf: 11-digit CPF string (unformatted)
    
    Returns:
        Formatted CPF string
    """
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    if len(cpf_clean) != 11:
        raise ValueError("CPF must have exactly 11 digits")
    
    return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"


def unformat_cpf(cpf: str) -> str:
    """
    Remove formatting from a CPF string.
    
    Args:
        cpf: CPF string (formatted or unformatted)
    
    Returns:
        11-digit CPF string without formatting
    """
    return ''.join(filter(str.isdigit, cpf))


def validate_cpf(cpf: str) -> bool:
    """
    Validate a CPF using the official algorithm.
    
    Args:
        cpf: CPF string (can be formatted or unformatted)
    
    Returns:
        True if CPF is valid, False otherwise
    
    Example:
        >>> validate_cpf("123.456.789-09")
        True
        >>> validate_cpf("12345678909")
        True
        >>> validate_cpf("111.111.111-11")
        False
        >>> validate_cpf("12345678900")
        False
    """
    # Remove formatting
    cpf_clean = unformat_cpf(cpf)
    
    # Check length
    if len(cpf_clean) != 11:
        return False
    
    # Check if all digits are the same (invalid)
    if len(set(cpf_clean)) == 1:
        return False
    
    # Check if only digits
    if not cpf_clean.isdigit():
        return False
    
    # Extract base and check digits
    cpf_base = cpf_clean[:9]
    provided_check = cpf_clean[9:]
    
    # Calculate expected check digits
    first_digit, second_digit = calculate_check_digits(cpf_base)
    expected_check = str(first_digit) + str(second_digit)
    
    return provided_check == expected_check


def generate_cpf_from_state(state_code: str, formatted: bool = False) -> str:
    """
    Generate a CPF with the 9th digit corresponding to a Brazilian state.
    
    The 9th digit of a CPF indicates the Receita Federal region:
    0 - RS
    1 - DF, GO, MT, MS, TO
    2 - AM, AC, AP, PA, RO, RR
    3 - CE, MA, PI
    4 - AL, PB, PE, RN
    5 - BA, SE
    6 - MG
    7 - ES, RJ
    8 - SP
    9 - PR, SC
    
    Args:
        state_code: Two-letter Brazilian state code (e.g., 'SP', 'RJ')
        formatted: If True, return formatted CPF
    
    Returns:
        Valid CPF string for the specified state
    """
    STATE_TO_REGION = {
        'RS': 0,
        'DF': 1, 'GO': 1, 'MT': 1, 'MS': 1, 'TO': 1,
        'AM': 2, 'AC': 2, 'AP': 2, 'PA': 2, 'RO': 2, 'RR': 2,
        'CE': 3, 'MA': 3, 'PI': 3,
        'AL': 4, 'PB': 4, 'PE': 4, 'RN': 4,
        'BA': 5, 'SE': 5,
        'MG': 6,
        'ES': 7, 'RJ': 7,
        'SP': 8,
        'PR': 9, 'SC': 9,
    }
    
    region_digit = STATE_TO_REGION.get(state_code.upper(), random.randint(0, 9))
    
    # Generate first 8 random digits
    while True:
        first_8 = ''.join(str(random.randint(0, 9)) for _ in range(8))
        cpf_base = first_8 + str(region_digit)
        # Avoid invalid patterns
        if len(set(cpf_base)) > 1:
            break
    
    # Calculate valid check digits
    first_digit, second_digit = calculate_check_digits(cpf_base)
    cpf = cpf_base + str(first_digit) + str(second_digit)
    
    if formatted:
        return format_cpf(cpf)
    
    return cpf


# Known test CPFs (used in examples and documentation)
TEST_CPFS = [
    '12345678909',  # Valid test CPF
    '98765432100',  # Another valid test CPF
]


if __name__ == '__main__':
    # Quick validation test
    print("🔍 CPF Validator Test")
    print("=" * 40)
    
    # Generate and validate random CPFs
    for i in range(5):
        cpf = generate_valid_cpf()
        cpf_formatted = format_cpf(cpf)
        is_valid = validate_cpf(cpf)
        print(f"Generated: {cpf_formatted} | Valid: {is_valid}")
    
    print()
    
    # Test state-specific CPFs
    print("State-specific CPFs:")
    for state in ['SP', 'RJ', 'MG', 'RS', 'BA']:
        cpf = generate_cpf_from_state(state, formatted=True)
        print(f"  {state}: {cpf}")
    
    print()
    
    # Test invalid CPFs
    print("Invalid CPF tests:")
    invalid_cpfs = ['11111111111', '12345678900', '00000000000', 'invalid']
    for cpf in invalid_cpfs:
        is_valid = validate_cpf(cpf)
        print(f"  {cpf}: Valid = {is_valid}")
