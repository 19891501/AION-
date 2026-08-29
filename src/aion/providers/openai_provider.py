"""Provider compatible OpenAI (fonctionne aussi avec Grok, OpenRouter, etc.).

Nécessite `pip install openai` et une clé API.
Variables d'environnement supportées :
  - OPENAI_API_KEY
  - GROK_API_KEY (alias)
  - OPENAI_BASE_URL (pour pointer vers api.x.ai ou un autre endpoint)
"""

from __future__ import annotations

import os

from .base import Reponse


class OpenAIProvider:
    """Provider générique compatible avec l'API OpenAI.

    Exemples :
        # OpenAI classique
        OpenAIProvider(modele="gpt-4o-mini")

        # Grok via xAI
        OpenAIProvider(
            modele="grok-3",
            api_key=os.environ["GROK_API_KEY"],
            base_url="https://api.x.ai/v1",
        )
    """

    nom = "openai"

    def __init__(
        self,
        modele: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pip install openai requis") from exc

        key = (
            api_key
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GROK_API_KEY")
        )
        if not key:
            raise RuntimeError(
                "Aucune clé API trouvée. Définis OPENAI_API_KEY ou GROK_API_KEY."
            )

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
        choix = resp.choices[0]
        texte = (choix.message.content or "").strip()
        usage = resp.usage

        return Reponse(
            texte=texte,
            modele=self.modele,
            tokens_entree=getattr(usage, "prompt_tokens", 0) or 0,
            tokens_sortie=getattr(usage, "completion_tokens", 0) or 0,
        )
