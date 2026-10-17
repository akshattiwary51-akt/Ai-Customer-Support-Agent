import pytest


@pytest.fixture(autouse=True)
def no_live_llm(monkeypatch):
    """Tests never call a real model, even if ANTHROPIC_API_KEY is set locally.

    Agent tests override this with a scripted fake (see test_agent.py).
    """
    monkeypatch.setattr("app.services.chat_service.get_llm_client", lambda: None)
