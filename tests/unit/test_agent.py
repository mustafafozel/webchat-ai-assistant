"""Unit tests covering the LangGraph agent orchestration."""

from backend.graph import run_agent


def test_faq_route_returns_kb_snippet():
    result = run_agent(session_id="sess-faq", user_input="İade politikası nedir?")
    assert result["metadata"]["intent"] == "faq"
    assert "iade" in result["response"].lower()


def test_tool_route_invokes_order_status():
    result = run_agent(session_id="sess-tool", user_input="12345 sipariş durumum ne?")
    assert result["metadata"]["intent"] == "tool"
    assert "12345" in result["response"]
