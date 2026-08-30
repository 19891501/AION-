"""Provider Anthropic. Necessite anthropic + ANTHROPIC_API_KEY."""

from __future__ import annotations

import os

from .base import Reponse

# ID API 2026 — pas d'alias fantôme type claude-3-5-haiku-latest
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicProvider:
    nom = "anthropic"

    def __init__(self, modele: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("pip install anthropic requis") from exc
        from anthropic import Anthropic

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY absent de l'environnement")
        self.modele = modele or DEFAULT_MODEL
        self._client = Anthropic(api_key=key)

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        msg = self._client.messages.create(
            model=self.modele,
            max_tokens=max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        texte = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return Reponse(
            texte=texte,
            modele=self.modele,
            tokens_entree=msg.usage.input_tokens,
            tokens_sortie=msg.usage.output_tokens,
        )
