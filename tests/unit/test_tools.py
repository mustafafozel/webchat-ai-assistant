"""Unit tests for the standalone mock tools."""

from backend import tools


def test_check_order_status_known_id():
    response = tools.check_order_status("12345")
    assert "12345" in response
    assert "kargoya" in response.lower()


def test_check_order_status_unknown_id():
    response = tools.check_order_status("99999")
    assert "bulunamadı" in response.lower()


def test_calculate_shipping_known_city():
    response = tools.calculate_shipping("istanbul")
    assert "İstanbul" in response
    assert response.endswith("25 TL")


def test_calculate_shipping_unknown_city():
    response = tools.calculate_shipping("kars")
    assert response.endswith("40 TL")


def test_policy_lookup_falls_back():
    response = tools.policy_lookup("bilinmeyen")
    assert "bulunamadı" in response.lower()
