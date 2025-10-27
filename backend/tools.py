# LangChain tools for order tracking, shipping calculation, and policy lookup

import json
import os

def tool(func):
    """Simple tool decorator"""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.invoke = lambda x: func(**x)
    return wrapper

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
    # Farklı olası KB dosya yollarını dene
    possible_paths = [
        "knowledge/kb.json",
        "../knowledge/kb.json",
        os.path.join(os.path.dirname(__file__), "..", "knowledge", "kb.json"),
        os.path.join(os.getcwd(), "knowledge", "kb.json")
    ]
    
    # Default knowledge base (dosya bulunamazsa)
    default_kb = {
        "iade": "İade politikası: Ürünlerinizi 14 gün içinde iade edebilirsiniz.",
        "kargo": "Kargo süresi: Ortalama 2-4 iş günü içinde teslim edilir.",
        "ödeme": "Ödeme seçenekleri: Kredi kartı, banka kartı veya kapıda ödeme.",
        "politika": "Tüm politikalarımız müşteri memnuniyeti odaklıdır.",
        "garanti": "Ürünlerimiz 2 yıl garanti kapsamındadır."
    }
    
    kb = None
    for path in possible_paths:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
                break
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    
    # Eğer dosya bulunamazsa, default KB kullan
    if kb is None:
        kb = default_kb
    
    return kb.get(topic, "Bu konuda bilgi bulunamadı.")

# Tool listesi
tools = [check_order_status, calculate_shipping, policy_lookup]
