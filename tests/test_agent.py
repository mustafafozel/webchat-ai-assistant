from backend.agent import run_agent

def test_faq_intent():
    resp = run_agent("sess-1", "iade politikası nedir?")
    assert "iade" in resp.lower()

def test_tool_intent():
    resp = run_agent("sess-2", "sipariş durumum ne?")
    assert "sipariş" in resp.lower() or "durum" in resp.lower()
