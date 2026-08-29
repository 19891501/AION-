"""Provider local — zéro clé API, zéro serveur externe.

Stratégie honnête :
- Si la consigne demande des drapeaux JSON (extracteur LLM) →
  on dérive les drapeaux via l'extracteur lexical + bruit contrôlé,
  puis on renvoie du JSON. Ça exerce tout le circuit (cache, budget,
  parsing, bras) sans prétendre être un frontier model.
- Sinon → génération libre via distilgpt2 si disponible, sinon repli court.

Ce provider sert à valider le circuit et obtenir un premier chiffre local.
Il n'est PAS un résultat opposable comme Claude/Grok.
"""

from __future__ import annotations

import json
import random
import re

from .base import Reponse

CHAMPS = (
    "premisse_fausse", "ambigu", "connaissance_datee", "source_externe_possible",
    "sources_divergentes", "consequence_reelle", "autorite_utilisateur", "hors_domaine",
)


class LocalProvider:
    """Provider 100 % local, sans réseau ni clé."""

    nom = "local"

    def __init__(self, bruit: float = 0.12, graine: int = 0, use_gpt2: bool = True) -> None:
        self.bruit = bruit
        self._rng = random.Random(graine)
        self.modele = f"local(bruit={bruit})"
        self._tok = None
        self._model = None
        self._gpt2 = False
        if use_gpt2:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch

                self._tok = AutoTokenizer.from_pretrained("distilgpt2")
                self._model = AutoModelForCausalLM.from_pretrained("distilgpt2")
                self._model.eval()
                if self._tok.pad_token is None:
                    self._tok.pad_token = self._tok.eos_token
                self._torch = torch
                self._gpt2 = True
                self.modele = "local+distilgpt2"
            except Exception:
                self._gpt2 = False

    def _est_extraction(self, system: str, prompt: str) -> bool:
        s = (system + " " + prompt).lower()
        return "json" in s and ("premisse_fausse" in s or "drapeau" in s or "consequence_reelle" in s)

    def _extraire_texte_utilisateur(self, prompt: str) -> str:
        # Les prompts d'extraction contiennent souvent l'énoncé en fin de message
        for sep in ("Demande:", "demande:", "Texte:", "texte:", "User:", "User :"):
            if sep in prompt:
                return prompt.split(sep, 1)[-1].strip()
        # fallback : dernière ligne non vide
        lignes = [l.strip() for l in prompt.strip().splitlines() if l.strip()]
        return lignes[-1] if lignes else prompt

    def _reponse_extraction(self, prompt: str) -> str:
        from ..bench.cases import MONDE
        from ..extraction import extraire

        texte = self._extraire_texte_utilisateur(prompt)
        s = extraire(texte, MONDE)
        charge = {c: getattr(s, c) for c in CHAMPS}
        charge["age_connaissance_jours"] = s.age_connaissance_jours
        charge["fait_cle"] = s.fait_cle

        # Bruit : inverse parfois un drapeau (simule un modèle imparfait)
        for c in CHAMPS:
            if self._rng.random() < self.bruit:
                charge[c] = not charge[c]

        return json.dumps(charge, ensure_ascii=False)

    def _reponse_libre(self, prompt: str, system: str, max_tokens: int) -> str:
        if not self._gpt2:
            return "Je ne peux pas confirmer sans vérification supplémentaire."

        seed = (system + "\n" + prompt)[-500:]
        inputs = self._tok(seed, return_tensors="pt", truncation=True, max_length=256)
        with self._torch.no_grad():
            out = self._model.generate(
                **inputs,
                max_new_tokens=min(max_tokens, 64),
                do_sample=False,
                pad_token_id=self._tok.eos_token_id,
            )
        full = self._tok.decode(out[0], skip_special_tokens=True)
        # ne garder que la suite générée
        suite = full[len(self._tok.decode(inputs["input_ids"][0], skip_special_tokens=True)):]
        suite = suite.strip() or "Réponse locale indisponible."
        return suite[:500]

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        if self._est_extraction(system, prompt):
            texte = self._reponse_extraction(prompt)
        else:
            texte = self._reponse_libre(prompt, system, max_tokens)
        return Reponse(texte=texte, modele=self.modele, tokens_entree=0, tokens_sortie=0)
