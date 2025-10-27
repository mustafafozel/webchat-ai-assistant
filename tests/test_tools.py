import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.tools import check_order_status, calculate_shipping, policy_lookup

def test_check_order_status():
    result = check_order_status.invoke({"order_id": "12345"})
    assert "Kargoya verildi" in result

def test_calculate_shipping():
    result = calculate_shipping.invoke({"city": "istanbul"})
    assert "25 TL" in result

def test_policy_lookup():
    result = policy_lookup.invoke({"topic": "iade"})
    assert "14 gün" in result
