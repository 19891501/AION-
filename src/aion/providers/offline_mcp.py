"""Offline MCP — remplace Ollama/cloud pour le circuit de mesure.

Provider direct: charger("offline") | charger("mcp")
Serveur HTTP: mime API Ollama /api/tags /api/chat (port 11434)

Honnêteté: PAS un frontier model. opposable_s2=false obligatoire.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

from .base import Reponse

CHAMPS = (
    "premisse_fausse", "ambigu", "connaissance_datee", "source_externe_possible",
    "sources_divergentes", "consequence_reelle", "autorite_utilisateur", "hors_domaine",
)

_VERBES = (
    "envoie", "envoyer", "supprime", "supprimer", "applique", "publie",
    "lance", "desactive", "rembourse", "facture", "commande",
)
_VAGUE = ("optimise", "améliore", "ameliore", "aide-moi", "compare", "revois")
_HORS = ("bombe", "pirater", "malware", "hors périmètre", "hors perimetre")


def _norm(t: str) -> str:
    t = t.lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ù", "u"), ("€", "euros")):
        t = t.replace(a, b)
    return t


def _drapeaux_depuis_texte(texte: str) -> dict[str, Any]:
    t = _norm(texte)
    words = t.split()
    head = words[0] if words else ""
    charge: dict[str, Any] = {c: False for c in CHAMPS}
    charge["age_connaissance_jours"] = 0
    charge["fait_cle"] = ""
    if any(h in t for h in _HORS):
        charge["hors_domaine"] = True
    if any(x in t for x in ("puisque", "etant donne que", "étant donné")) and any(
        x in t for x in ("allemagne", "plat", "terre est plate", "paris est en")
    ):
        charge["premisse_fausse"] = True
    if any(v in t for v in _VAGUE):
        charge["ambigu"] = True
    if any(p in f" {t} " for p in (" ma ", " mon ", " mes ", " notre ")):
        charge["autorite_utilisateur"] = True
    if head in _VERBES or any(v in t for v in ("virement", "10000", "supprime", "suppression")):
        charge["consequence_reelle"] = True
    if any(x in t for x in ("prix", "bitcoin", "cours", "aujourd'hui", "maintenant")):
        charge["connaissance_datee"] = True
        charge["age_connaissance_jours"] = 200
        charge["source_externe_possible"] = True
    if "source" in t and any(x in t for x in ("diverg", "oppos", "contradic")):
        charge["sources_divergentes"] = True
    return charge


def _action_scaffold(texte: str) -> str:
    d = _drapeaux_depuis_texte(texte)
    if d["hors_domaine"]:
        return "REFUSE"
    if d["premisse_fausse"]:
        return "CLARIFY"
    if d["consequence_reelle"]:
        if "10000" in _norm(texte) or "virement" in _norm(texte):
            return "VERIFY"
        return "ANSWER"
    if d["connaissance_datee"]:
        return "SEARCH"
    if d["ambigu"] and d["autorite_utilisateur"]:
        return "ASK"
    if d["ambigu"]:
        return "CLARIFY"
    if d["sources_divergentes"]:
        return "COMPARE"
    return "ANSWER"


def _est_extraction(system: str, prompt: str) -> bool:
    s = (system + " " + prompt).lower()
    return "json" in s and any(c in s for c in ("premisse_fausse", "drapeau", "consequence_reelle"))


def _est_scaffold(system: str) -> bool:
    s = system.upper()
    return "ANSWER" in s and "VERIFY" in s and ("CHOIS" in s or "ACTION" in s or "MOT-CLE" in s or "MOT CLE" in s)


def _texte_utilisateur(prompt: str) -> str:
    for sep in ("Demande:", "demande:", "Texte:", "User:", "Question:"):
        if sep in prompt:
            return prompt.split(sep, 1)[-1].strip()
    lignes = [l.strip() for l in prompt.strip().splitlines() if l.strip()]
    return lignes[-1] if lignes else prompt


class OfflineMCPProvider:
    nom = "offline_mcp"

    def __init__(self, modele: str = "offline-mcp-v1") -> None:
        self.modele = modele

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        if _est_extraction(system, prompt):
            texte = _texte_utilisateur(prompt)
            charge = _drapeaux_depuis_texte(texte)
            out = json.dumps(charge, ensure_ascii=False)
            return Reponse(texte=out, modele=self.modele, tokens_sortie=len(out.split()))
        if _est_scaffold(system):
            texte = _texte_utilisateur(prompt) or prompt
            return Reponse(texte=_action_scaffold(texte), modele=self.modele, tokens_sortie=1)
        return Reponse(texte="[offline-mcp] reponse locale — non frontier.", modele=self.modele, tokens_sortie=6)


_PROVIDER = OfflineMCPProvider()


class _OllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path in ("/api/tags", "/api/version"):
            self._json(200, {"models": [{"name": "offline-mcp-v1", "model": "offline-mcp-v1"}], "version": "offline-mcp-0.1"})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            data = {}
        if path == "/api/chat":
            messages = data.get("messages") or []
            system = ""
            prompt = ""
            for m in messages:
                if m.get("role") == "system":
                    system = str(m.get("content") or "")
                elif m.get("role") == "user":
                    prompt = str(m.get("content") or "")
            rep = _PROVIDER.complete(prompt, system=system)
            self._json(200, {"model": rep.modele, "message": {"role": "assistant", "content": rep.texte}, "done": True, "eval_count": rep.tokens_sortie})
            return
        if path == "/v1/chat/completions":
            messages = data.get("messages") or []
            system = next((m["content"] for m in messages if m.get("role") == "system"), "")
            prompt = next((m["content"] for m in messages if m.get("role") == "user"), "")
            rep = _PROVIDER.complete(str(prompt), system=str(system))
            self._json(200, {"choices": [{"message": {"role": "assistant", "content": rep.texte}}], "model": rep.modele})
            return
        self._json(404, {"error": f"unknown path {path}"})


def servir(host: str = "127.0.0.1", port: int = 11434, bloquant: bool = True) -> HTTPServer:
    server = HTTPServer((host, port), _OllamaHandler)
    if bloquant:
        server.serve_forever()
    else:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
