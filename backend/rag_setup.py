<<<<<<< HEAD
import math

class SimpleRAG:
    def __init__(self):
        self.docs = []

    def add_document(self, text: str):
        self.docs.append(text)

    def cosine_sim(self, a, b):
        a, b = a.lower(), b.lower()
        common = len(set(a.split()) & set(b.split()))
        return common / math.sqrt(len(a.split()) * len(b.split()))

    def search(self, query: str):
        if not self.docs:
            return None
        sims = [self.cosine_sim(query, d) for d in self.docs]
        return self.docs[sims.index(max(sims))] if sims else None

=======
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
    return [d for s, d in scored[:k] if s > 0]
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
