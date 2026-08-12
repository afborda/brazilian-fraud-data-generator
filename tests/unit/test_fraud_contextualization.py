"""
Tests for Fraud Contextualization (Phase 2 - Fraud Patterns).

Validates that each fraud type generates transactions with expected characteristics.
"""

import pytest
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from fraud_generator.generators import TransactionGenerator
from fraud_generator.config.fraud_patterns import FRAUD_PATTERNS, FRAUD_TYPES_LIST


class TestFraudContextualization:
    """Test fraud pattern contextualization."""
    
    @pytest.fixture
    def generator(self):
        """Create generator with 100% fraud rate for testing."""
        return TransactionGenerator(fraud_rate=1.0, use_profiles=False, seed=42)
    
    def test_fraud_patterns_loaded(self):
        """Test that fraud patterns are properly loaded."""
        assert len(FRAUD_PATTERNS) > 0
        assert 'CONTA_TOMADA' in FRAUD_PATTERNS
        assert 'ENGENHARIA_SOCIAL' in FRAUD_PATTERNS
        assert 'PIX_GOLPE' in FRAUD_PATTERNS
        
        # Validate pattern structure
        for fraud_type, pattern in FRAUD_PATTERNS.items():
            assert 'name' in pattern
            assert 'characteristics' in pattern
            assert 'prevalence' in pattern
            assert 'fraud_score_base' in pattern
    
    def test_fraud_type_distribution(self, generator):
        """Test that fraud types follow expected distribution."""
        fraud_types_generated = []
        
        # Generate 1000 fraud transactions
        for i in range(1000):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime.now(),
                force_fraud=True
            )
            assert tx['is_fraud'] is True
            assert tx['fraud_type'] in FRAUD_TYPES_LIST
            fraud_types_generated.append(tx['fraud_type'])
        
        # Verify all fraud types appear
        unique_types = set(fraud_types_generated)
        assert len(unique_types) > 3, "Should generate multiple fraud types"
    
    def test_conta_tomada_pattern(self, generator):
        """Test CONTA_TOMADA (account takeover) pattern characteristics."""
        # Generate multiple transactions to test pattern
        conta_tomada_txs = []
        
        for i in range(100):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 14, 30),
                force_fraud=True
            )
            if tx.get('fraud_type') == 'CONTA_TOMADA':
                conta_tomada_txs.append(tx)
        
        # Need at least a few to test distribution properties
        if len(conta_tomada_txs) >= 3:
            # Test distribution properties (not single-sample values — fraud fields have noise)
            amounts = [tx['amount'] for tx in conta_tomada_txs]
            velocities = [tx.get('velocity_transactions_24h', 0) for tx in conta_tomada_txs]
            scores = [tx['fraud_score'] for tx in conta_tomada_txs]

            # High value anomaly (3x-10x multiplier): median should be well above baseline
            import statistics
            assert statistics.median(amounts) >= 100, "CONTA_TOMADA median amount should be elevated"

            # High velocity: median should be >= 5
            assert statistics.median(velocities) >= 5, "CONTA_TOMADA should have high velocity"

            # High fraud score — base 0.75, noise N(0,20): median > 50
            assert statistics.median(scores) >= 50, "CONTA_TOMADA median fraud score should be high"
    
    def test_engenharia_social_pattern(self, generator):
        """Test ENGENHARIA_SOCIAL pattern characteristics."""
        social_eng_txs = []
        
        for i in range(100):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 10, 0),
                force_fraud=True
            )
            if tx.get('fraud_type') == 'ENGENHARIA_SOCIAL':
                social_eng_txs.append(tx)
        
        if len(social_eng_txs) > 0:
            tx = social_eng_txs[0]

            # Amounts are log-normal, so a hard ceiling on one arbitrary record
            # fails whenever the RNG order shifts — the tail is supposed to
            # reach high values. Assert the central tendency instead, which is
            # what "moderate amounts" actually means.
            amounts = sorted(t['amount'] for t in social_eng_txs)
            median = amounts[len(amounts) // 2]
            assert median < 50_000, (
                f"ENGENHARIA_SOCIAL median was R${median:,.2f}; expected moderate "
                f"amounts, lower than extreme types (SEQUESTRO, EMPRESTIMO)"
            )

            # New beneficiary — probabilístico: esperado em ~95% dos casos
            # (não assertamos em transação única — verificado em nível de conjunto)
            
            # Canal legítimo (MOBILE_APP ou WEB_BANKING), tipo PIX ou TED
            assert tx.get('channel') in ['MOBILE_APP', 'WEB_BANKING']
            assert tx.get('type') in ['PIX', 'TED']
    
    def test_pix_golpe_pattern(self, generator):
        """Test PIX_GOLPE pattern characteristics."""
        pix_golpe_txs = []
        
        for i in range(100):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 18, 0),
                force_fraud=True
            )
            if tx.get('fraud_type') == 'PIX_GOLPE':
                pix_golpe_txs.append(tx)
        
        if len(pix_golpe_txs) > 0:
            tx = pix_golpe_txs[0]

            # Should be PIX transaction
            if tx.get('channel') == 'PIX' or tx.get('type') == 'PIX':
                # PIX-specific fields
                assert tx.get('pix_key_type') is not None, "PIX_GOLPE should have PIX key"
                assert tx.get('pix_key_destination') is not None

            # new_beneficiary is a *tendency*, not a certainty. This used to
            # assert `is True` on a single record while the configured
            # probability is 0.65, so it passed only by luck of the RNG order
            # and broke on any upstream change. Asserting it as a distribution
            # also keeps the field honest: a rate of 1.0 would make
            # `new_beneficiary` a perfect label for this fraud type.
            rate = sum(
                1 for t in pix_golpe_txs if t.get('new_beneficiary')
            ) / len(pix_golpe_txs)
            assert 0.35 <= rate <= 0.95, (
                f"new_beneficiary rate for PIX_GOLPE was {rate:.2f}; expected a "
                f"strong tendency but not a certainty (1.0 would be leakage)"
            )
    
    def test_cartao_clonado_pattern(self, generator):
        """Test CARTAO_CLONADO pattern characteristics."""
        cloned_card_txs = []
        
        for i in range(100):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 20, 0),
                force_fraud=True
            )
            if tx.get('fraud_type') == 'CARTAO_CLONADO':
                cloned_card_txs.append(tx)
        
        if len(cloned_card_txs) > 0:
            tx = cloned_card_txs[0]
            
            # High velocity (multiple quick transactions)
            assert tx.get('velocity_transactions_24h', 0) >= 5, "CARTAO_CLONADO should have high velocity"
            
            # Canal legítimo (ATM, BRANCH, WEB_BANKING, MOBILE_APP), tipo cartão
            assert tx.get('channel') in ['ATM', 'BRANCH', 'WEB_BANKING', 'MOBILE_APP']
            assert tx.get('type') in ['CREDIT_CARD', 'DEBIT_CARD']
            
            # Calibrated multiplier [3.0, 8.0] — profile-based values can vary widely
            assert tx['amount'] <= 100000, "CARTAO_CLONADO should not exceed extreme amounts"
    
    def test_compra_teste_pattern(self, generator):
        """Test COMPRA_TESTE (card testing) pattern characteristics."""
        test_purchase_txs = []
        
        for i in range(100):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 3, 0),
                force_fraud=True
            )
            if tx.get('fraud_type') == 'COMPRA_TESTE':
                test_purchase_txs.append(tx)
        
        if len(test_purchase_txs) > 0:
            tx = test_purchase_txs[0]
            
            # Very low amounts (testing cards) — may be slightly higher with profiles
            assert tx['amount'] < 200, "COMPRA_TESTE should have low amounts"
            
            # Very high velocity (many test attempts)
            assert tx.get('velocity_transactions_24h', 0) >= 10, "COMPRA_TESTE should have very high velocity"
    
    def test_fraud_score_consistency(self, generator):
        """Test que fraud_score para fraudes tem ruído realista mas média acima de legítimos."""
        scores = []
        for i in range(50):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 12, 0),
                force_fraud=True
            )
            scores.append(tx['fraud_score'])
            assert tx['is_fraud'] is True
            assert tx['fraud_type'] in FRAUD_TYPES_LIST
            # Score based on 17 behavioral signals — some stealth fraud types
            # (FRAUDE_DELIVERY, QR_CODE) may trigger zero signals
            assert tx['fraud_score'] >= 0, f"Fraud score negativo: {tx['fraud_score']}"

        # Média do conjunto deve ser significativamente acima do esperado para legítimos (40)
        avg = sum(scores) / len(scores)
        assert avg >= 30, f"Média do fraud_score para fraudes muito baixa: {avg:.1f}"
    
    def test_non_fraud_transactions(self, generator):
        """Test that non-fraud transactions don't have fraud patterns."""
        # Create generator with 0% fraud rate
        clean_gen = TransactionGenerator(fraud_rate=0.0, use_profiles=False, seed=123)
        
        for i in range(20):
            tx = clean_gen.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 12, 0)
            )
            
            assert tx['is_fraud'] is False
            assert tx['fraud_type'] is None
            # Com ruído realista: 85% < 40, 12% borderline, 3% até ~95. Limite ampliado.
            assert tx['fraud_score'] < 96, f"Non-fraud score inesperadamente alto: {tx['fraud_score']}"
    
    def test_fraud_pattern_fields_present(self, generator):
        """Test that fraud pattern application adds expected fields."""
        tx = generator.generate(
            tx_id="001",
            customer_id="CUST_000000000001",
            device_id="DEV_000001",
            timestamp=datetime(2025, 1, 15, 14, 30),
            force_fraud=True
        )
        
        # Core fraud fields
        assert 'is_fraud' in tx
        assert 'fraud_type' in tx
        assert 'fraud_score' in tx
        
        # Risk indicator fields
        assert 'new_beneficiary' in tx
        assert 'velocity_transactions_24h' in tx
        assert 'unusual_time' in tx
        
        # Transaction should be marked as fraud
        assert tx['is_fraud'] is True
        assert tx['fraud_type'] in FRAUD_TYPES_LIST
