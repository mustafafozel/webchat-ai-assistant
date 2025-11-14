# -------------- PATCH PACKAGE FOR WECHAT-AI-ASSISTANT --------------
# 1️⃣  Create new LangGraph agent pipeline
cat > backend/agent.py <<'PY'
from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from .tools import check_order_status, calculate_shipping, policy_lookup
from .rag_setup import mini_rag_search

class AgentState(BaseModel):
    session_id: str
    user_message: str
    intent: Literal["faq", "tool", "general"] | None = None
    context: Dict[str, Any] = {}
    answer: str | None = None

def intent_router_node(state: AgentState) -> AgentState:
    m = state.user_message.lower()
    if any(k in m for k in ["iade", "kargo", "ödeme", "policy", "faq"]):
        state.intent = "faq"
    elif any(k in m for k in ["sipariş", "order", "shipping", "ücret"]):
        state.intent = "tool"
    else:
        state.intent = "general"
    return state

def retriever_node(state: AgentState) -> AgentState:
    state.context["kb"] = mini_rag_search(state.user_message)
    return state

def tool_caller_node(state: AgentState) -> AgentState:
    m = state.user_message.lower()
    if "sipariş" in m:
        state.context["tool"] = check_order_status("ABC123")
    elif "kargo" in m and "ücret" in m:
        state.context["tool"] = calculate_shipping("İstanbul")
    else:
        topic = "iade" if "iade" in m else ("kargo" if "kargo" in m else "ödeme")
        state.context["tool"] = policy_lookup(topic)
    return state

def response_builder_node(state: AgentState) -> AgentState:
    if state.intent == "faq":
        kb = state.context.get("kb") or []
        state.answer = kb[0] if kb else "Bu konuda bilgi bulamadım."
    elif state.intent == "tool":
        state.answer = str(state.context.get("tool"))
    else:
        state.answer = "Sorunuzu aldım, nasıl yardımcı olabilirim?"
    return state

def memory_manager_node(state: AgentState) -> AgentState:
    return state

def compile_graph():
    g = StateGraph(AgentState)
    g.add_node("intent_router", intent_router_node)
    g.add_node("retriever", retriever_node)
    g.add_node("tool_caller", tool_caller_node)
    g.add_node("response_builder", response_builder_node)
    g.add_node("memory_manager", memory_manager_node)

    g.set_entry_point("intent_router")

    def route_decision(state: AgentState):
        return state.intent or "general"

    g.add_conditional_edges("intent_router", route_decision,
        {"faq": "retriever", "tool": "tool_caller", "general": "response_builder"})
    g.add_edge("retriever", "response_builder")
    g.add_edge("tool_caller", "response_builder")
    g.add_edge("response_builder", "memory_manager")
    g.add_edge("memory_manager", END)
    return g.compile()

graph = compile_graph()

def run_agent(session_id: str, message: str) -> str:
    out = graph.invoke(AgentState(session_id=session_id, user_message=message))
    return out.answer or "Bir cevap üretemedim."
PY

# 2️⃣ Mini RAG KB function
cat > backend/rag_setup.py <<'PY'
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
PY

# 3️⃣ CI Pipeline
mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<'YAML'
name: CI
on:
  push:
    branches: [ main, "feature/**" ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Lint
        run: pip install ruff && ruff check .
      - name: Test
        run: |
          pip install pytest pytest-asyncio
          pytest -q
YAML

# 4️⃣ GitHub Templates
mkdir -p .github/ISSUE_TEMPLATE
cat > .github/pull_request_template.md <<'MD'
## Öz Summary
<!-- Kısa açıklama -->

## Tür
- [ ] feat
- [ ] fix
- [ ] docs
- [ ] refactor
- [ ] test
- [ ] chore

## Test Planı
- [ ] WS mesaj akışı
- [ ] API testleri
- [ ] RAG doğrulama
MD

cat > .github/ISSUE_TEMPLATE/bug_report.md <<'MD'
---
name: Bug Report
about: Hata bildirimi
---

**Sorun Özeti**

**Adımlar**
1. ...
2. ...

**Beklenen**
...

**Ekran Görüntüsü veya Log**
...
MD

# 5️⃣ Tests
mkdir -p tests
cat > tests/test_agent.py <<'PY'
from backend.agent import run_agent

def test_faq_intent():
    resp = run_agent("sess-1", "iade politikası nedir?")
    assert "iade" in resp.lower()

def test_tool_intent():
    resp = run_agent("sess-2", "sipariş durumum ne?")
    assert "sipariş" in resp.lower() or "durum" in resp.lower()
PY

echo '✅ Patch dosyaları hazır: agent, RAG, CI, Templates, Tests'
