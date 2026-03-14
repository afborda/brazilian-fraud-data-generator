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
        
        # Need at least a few to test
        if len(conta_tomada_txs) > 0:
            tx = conta_tomada_txs[0]
            
            # High value anomaly (3x-10x multiplier)
            assert tx['amount'] >= 300, "CONTA_TOMADA should have high amounts"
            
            # High velocity
            assert tx.get('velocity_transactions_24h', 0) >= 5, "CONTA_TOMADA should have high velocity"
            
            # High fraud score
            assert tx['fraud_score'] >= 60, "CONTA_TOMADA should have high fraud score"
            
            # New beneficiary
            assert tx.get('new_beneficiary') is True, "CONTA_TOMADA should have new beneficiary"
    
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
            
            # Normal to low value anomaly (1x-2.5x)
            # Should be lower than account takeover
            assert tx['amount'] < 10000, "ENGENHARIA_SOCIAL should have moderate amounts"
            
            # New beneficiary
            assert tx.get('new_beneficiary') is True, "ENGENHARIA_SOCIAL should have new beneficiary"
            
            # Should prefer PIX/TED
            assert tx.get('channel') in ['PIX', 'TED', 'ONLINE', 'MOBILE_APP']
    
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
                
            # New beneficiary (always for PIX golpe)
            assert tx.get('new_beneficiary') is True
    
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
            
            # Prefer POS/ECOMMERCE channels
            assert tx.get('channel') in ['POS', 'ECOMMERCE', 'MOBILE_APP', 'ONLINE']
            
            # Medium value (1.5x-4x of fraud base 500-10000 → up to 40000)
            assert 100 <= tx['amount'] <= 40000, "CARTAO_CLONADO should have medium amounts"
    
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
            
            # Very low amounts (testing cards)
            assert tx['amount'] < 50, "COMPRA_TESTE should have very low amounts"
            
            # Very high velocity (many test attempts)
            assert tx.get('velocity_transactions_24h', 0) >= 10, "COMPRA_TESTE should have very high velocity"
    
    def test_fraud_score_consistency(self, generator):
        """Test that fraud scores are consistently high for fraud transactions."""
        for i in range(50):
            tx = generator.generate(
                tx_id=str(i),
                customer_id=f"CUST_{i:012d}",
                device_id=f"DEV_{i:06d}",
                timestamp=datetime(2025, 1, 15, 12, 0),
                force_fraud=True
            )
            
            # All fraud should have fraud_score > 35 (most > 50)
            assert tx['fraud_score'] >= 35, f"Fraud score too low: {tx['fraud_score']}"
            assert tx['is_fraud'] is True
            assert tx['fraud_type'] in FRAUD_TYPES_LIST
    
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
            assert tx['fraud_score'] < 40, "Non-fraud should have low fraud score"
    
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
