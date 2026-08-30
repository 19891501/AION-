"""Provider compatible OpenAI / Grok / OpenRouter."""

from __future__ import annotations

import os

from .base import Reponse


class OpenAIProvider:
    nom = "openai"

    def __init__(
        self,
        modele: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("pip install openai requis") from exc

        key = (
            api_key
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GROK_API_KEY")
        )
        if not key:
            raise RuntimeError("Aucune clé API (OPENAI_API_KEY ou GROK_API_KEY).")

        kwargs: dict = {"api_key": key}
        url = base_url or os.environ.get("OPENAI_BASE_URL")
        if url:
            kwargs["base_url"] = url
        self.modele = modele
        self._client = OpenAI(**kwargs)

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=self.modele,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0,
        )
        texte = (resp.choices[0].message.content or "").strip()
        usage = resp.usage
        return Reponse(
            texte=texte,
            modele=self.modele,
            tokens_entree=int(getattr(usage, "prompt_tokens", 0) or 0),
            tokens_sortie=int(getattr(usage, "completion_tokens", 0) or 0),
        )
