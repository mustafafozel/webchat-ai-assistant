"""Mock tool implementations used by the LangGraph agent and unit tests."""

from __future__ import annotations

from langchain_core.tools import StructuredTool

ORDER_STATUS = {
    "12345": "Siparişiniz kargoya verildi.",
    "67890": "Siparişiniz hazırlanıyor.",
    "11111": "Siparişiniz teslim edildi.",
}

SHIPPING_PRICES = {
    "istanbul": 25,
    "ankara": 30,
    "izmir": 28,
    "antalya": 35,
}

POLICY_TEXTS = {
    "iade": "İade politikası: 14 gün içinde koşulsuz iade hakkı bulunur.",
    "kargo": "Kargo politikası: 2-4 iş günü içinde teslimat yapılır.",
    "ödeme": "Ödeme politikası: Kredi kartı, banka kartı veya kapıda ödeme kabul edilir.",
}


def check_order_status(order_id: str) -> str:
    """Return a mock shipping status for a given order id."""
    status = ORDER_STATUS.get(order_id, "Bu numaraya ait sipariş bulunamadı.")
    return f"{order_id} numaralı sipariş durumu: {status}"


def calculate_shipping(city: str) -> str:
    """Return a mock shipping price."""
    price = SHIPPING_PRICES.get(city.lower(), 40)
    return f"{city.title()} için tahmini kargo ücreti: {price} TL"


def policy_lookup(topic: str) -> str:
    """Return a short FAQ/policy snippet."""
    normalized = topic.lower()
    return POLICY_TEXTS.get(normalized, "Bu konu hakkında kayıtlı politikamız bulunamadı.")


TOOL_REGISTRY = [
    StructuredTool.from_function(
        func=check_order_status,
        name="check_order_status",
        description="Sipariş durumunu sorgular",
    ),
    StructuredTool.from_function(
        func=calculate_shipping,
        name="calculate_shipping",
        description="Şehre göre kargo ücretini hesaplar",
    ),
    StructuredTool.from_function(
        func=policy_lookup,
        name="policy_lookup",
        description="Politika ve prosedürleri listeler",
    ),
]
