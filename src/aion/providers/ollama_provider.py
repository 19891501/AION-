"""Provider Ollama — local, sans clé API.

Parle à l'API OpenAI-compatible d'Ollama :
  http://127.0.0.1:11434/v1

Prérequis :
  1. Installer Ollama : https://ollama.com
  2. ollama pull llama3.2   (ou autre modèle)
  3. ollama serve           (souvent déjà démarré)

Usage :
  aion bench --provider ollama --micro --entree paraphrase --extracteur llm
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import Reponse

DEFAULT_BASE = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"


class OllamaProvider:
    """Appels locaux via l'API chat d'Ollama (aucune clé API)."""

    nom = "ollama"

    def __init__(
        self,
        modele: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.modele = modele or os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)
        self.base_url = (base_url or os.environ.get("OLLAMA_HOST", DEFAULT_BASE)).rstrip("/")
        self.timeout = timeout
        self._ping()

    def _ping(self) -> None:
        """Échoue vite si Ollama n'est pas joignable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                resp.read()
        except Exception as exc:
            raise RuntimeError(
                f"Ollama inaccessible sur {self.base_url}.\n"
                "  1. Installe : https://ollama.com\n"
                "  2. Lance   : ollama serve\n"
                f"  3. Tire    : ollama pull {self.modele}\n"
                f"Détail : {exc}"
            ) from exc

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.modele,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0},
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Échec appel Ollama ({self.modele}): {exc}") from exc

        message = body.get("message") or {}
        texte = (message.get("content") or "").strip()
        # Ollama ne renvoie pas toujours des compteurs de tokens fiables
        return Reponse(
            texte=texte,
            modele=self.modele,
            tokens_entree=int(body.get("prompt_eval_count") or 0),
            tokens_sortie=int(body.get("eval_count") or 0),
        )
