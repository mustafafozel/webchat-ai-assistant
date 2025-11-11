# backend/rag_setup.py
from typing import List

FAQ = [
  "İade politikası: 14 gün içinde iade hakkı vardır.",
  "Kargo süresi: Ortalama 2–4 iş günü.",
  "Ödeme seçenekleri: Kredi kartı veya kapıda ödeme."
]

def mini_rag_search(query: str, k: int = 1) -> List[str]:
    q = query.lower()
    scored = []
    for doc in FAQ:
        score = sum(1 for w in q.split() if w in doc.lower())
        scored.append((score, doc))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [d for s,d in scored[:k] if s > 0]

