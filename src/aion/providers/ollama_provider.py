"""Provider Ollama — local ou cloud (clé optionnelle)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import Reponse

DEFAULT_BASE = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"


class OllamaProvider:
    nom = "ollama"

    def __init__(
        self,
        modele: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.modele = modele or os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)
        self.base_url = (base_url or os.environ.get("OLLAMA_HOST", DEFAULT_BASE)).rstrip("/")
        self.api_key = (
            api_key
            or os.environ.get("OLLAMA_API_KEY")
            or os.environ.get("OLLAMA_KEY")
            or ""
        )
        self.timeout = timeout
        self._ping()

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _ping(self) -> None:
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags", method="GET", headers=self._headers()
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception as exc:
            raise RuntimeError(
                f"Ollama inaccessible sur {self.base_url}.\n"
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
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Échec Ollama ({self.modele}): {exc}") from exc
        message = body.get("message") or {}
        texte = (message.get("content") or "").strip()
        return Reponse(
            texte=texte,
            modele=self.modele,
            tokens_entree=int(body.get("prompt_eval_count") or 0),
            tokens_sortie=int(body.get("eval_count") or 0),
        )
