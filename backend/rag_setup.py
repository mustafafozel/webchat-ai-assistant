"""Lightweight knowledge base helpers used by the LangGraph agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence


def load_knowledge_base(path: Path | str) -> List[str]:
    """Load mini FAQ data from JSON; fallback to defaults when missing."""
    kb_path = Path(path)
    if kb_path.exists():
        with kb_path.open("r", encoding="utf-8") as handler:
            data = json.load(handler)
        if isinstance(data, dict):
            return [f"{key}: {value}" for key, value in data.items()]
        if isinstance(data, list):
            return [str(item) for item in data]

    # Fallback FAQ items (matches technical brief)
    return [
        "İade politikası: 14 gün içinde iade hakkınız bulunmaktadır.",
        "Kargo süresi: Ortalama teslimat 2-4 iş günüdür.",
        "Ödeme seçenekleri: Kredi kartı, banka kartı veya kapıda ödeme.",
        "Politikalarımız müşteri memnuniyeti odaklıdır.",
    ]


def _score_document(query_tokens: Iterable[str], document: str) -> int:
    tokens = document.lower().split()
    return sum(1 for token in query_tokens if token in tokens)


def mini_rag_search(query: str, knowledge_base: Sequence[str], k: int = 2) -> List[str]:
    """Return the top-k FAQ entries that roughly match the query."""
    normalized = query.lower().split()
    ranked = [(_score_document(normalized, doc), doc) for doc in knowledge_base]
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [doc for score, doc in ranked[:k] if score > 0]
