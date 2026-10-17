"""Provider-neutral LLM interface used by the ReAct agent.

The agent only depends on the small ``LLMClient`` protocol below, so tests can
inject a scripted fake and other providers can be added without touching the
reasoning loop. The Anthropic implementation is imported lazily so the backend
still starts (and the deterministic fallback still works) when the optional
``anthropic`` package or an API key is not available.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import get_settings


class LLMError(RuntimeError):
    """Raised when the model provider cannot produce a usable turn."""


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMTurn:
    """One model response: optional text plus zero or more tool calls."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

    def as_assistant_content(self) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        if self.text:
            blocks.append({"type": "text", "text": self.text})
        for call in self.tool_calls:
            blocks.append(
                {"type": "tool_use", "id": call.id, "name": call.name, "input": call.input}
            )
        return blocks


class LLMClient(Protocol):
    def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMTurn: ...


class AnthropicLLMClient:
    def __init__(self, api_key: str, model: str, max_tokens: int, timeout_seconds: float) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise LLMError("The 'anthropic' package is required for the agent engine") from exc
        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds)
        self._model = model
        self._max_tokens = max_tokens

    def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMTurn:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                tools=tools,
                messages=messages,
            )
        except self._anthropic.APIError as exc:
            raise LLMError(f"Model provider error: {exc.__class__.__name__}") from exc

        turn = LLMTurn()
        text_parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                turn.tool_calls.append(
                    ToolCall(id=block.id, name=block.name, input=dict(block.input or {}))
                )
        turn.text = "\n".join(part for part in text_parts if part).strip()
        return turn


def get_llm_client() -> LLMClient | None:
    """Return a configured client, or None when the agent engine is unavailable."""
    settings = get_settings()
    if not settings.agent_enabled or not settings.anthropic_api_key:
        return None
    try:
        return AnthropicLLMClient(
            api_key=settings.anthropic_api_key,
            model=settings.agent_model,
            max_tokens=settings.agent_max_tokens,
            timeout_seconds=settings.agent_timeout_seconds,
        )
    except LLMError:
        return None
