"""
Pytest configuration file for UavNetSim tests

This file is automatically loaded by pytest.
"""

import sys
import os

# Add project root to Python path for all pytest tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def pytest_configure(config):
    """Configure pytest"""
    print("\n" + "="*70)
    print("UavNetSim Test Suite (pytest)")
    print("="*70)

