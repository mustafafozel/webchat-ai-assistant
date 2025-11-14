"""
Tool fonksiyonlarını test eder
"""
import pytest
import json
from backend.graph import check_order_status, calculate_shipping, policy_lookup


def test_check_order_status_known():
    """Bilinen sipariş ID'si"""
    result = check_order_status.invoke({"order_id": "12345"})
    data = json.loads(result)
    assert data["order_id"] == "12345"
    assert "kargoya verildi" in data["status"].lower()


def test_check_order_status_unknown():
    """Bilinmeyen sipariş ID'si"""
    result = check_order_status.invoke({"order_id": "99999"})
    data = json.loads(result)
    assert "bulunamadı" in data["status"].lower()


def test_calculate_shipping_istanbul():
    """İstanbul kargo ücreti"""
    result = calculate_shipping.invoke({"city": "istanbul"})
    data = json.loads(result)
    assert data["city"] == "istanbul"
    assert data["shipping_cost"] == 25


def test_calculate_shipping_ankara():
    """Ankara kargo ücreti"""
    result = calculate_shipping.invoke({"city": "ankara"})
    data = json.loads(result)
    assert data["shipping_cost"] == 30


def test_calculate_shipping_unknown_city():
    """Bilinmeyen şehir - default fiyat"""
    result = calculate_shipping.invoke({"city": "BilinmeyenSehir"})
    data = json.loads(result)
    assert data["shipping_cost"] == 40


def test_policy_lookup():
    """Politika arama"""
    result = policy_lookup.invoke({"topic": "iade"})
    assert "iade" in result.lower()
    assert len(result) > 0

