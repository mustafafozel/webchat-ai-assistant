# LangChain tools for order tracking, shipping calculation, and policy lookup

import json
from langchain.tools import tool

@tool
def check_order_status(order_id: str) -> str:
    """Sipariş durumunu kontrol eder."""
    mock_data = {
        "12345": "Kargoya verildi",
        "67890": "Hazırlanıyor",
        "11111": "Teslim edildi"
    }
    status = mock_data.get(order_id, "Sipariş bulunamadı")
    return f"Sipariş {order_id}: {status}"

@tool
def calculate_shipping(city: str) -> str:
    """Kargo ücretini hesaplar."""
    prices = {
        "istanbul": 25,
        "ankara": 30,
        "izmir": 28,
        "antalya": 35
    }
    price = prices.get(city.lower(), 40)
    return f"{city} için kargo ücreti: {price} TL"

@tool
def policy_lookup(topic: str) -> str:
    """Politika bilgilerini döndürür."""
    with open("knowledge/kb.json", "r", encoding="utf-8") as f:
        kb = json.load(f)
    return kb.get(topic, "Bu konuda bilgi bulunamadı.")

# Tool listesi
tools = [check_order_status, calculate_shipping, policy_lookup]
