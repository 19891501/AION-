"""AION Web API — surface HTTP minimale pour déploiement Render."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aion import __version__
from aion.audit import auditer, resume_audit
from aion.behavior import Situation, selectionner
from aion.bench.cases import CAS, LEDGER_SEED, MONDE
from aion.ledger import Ledger
from aion.preenregistrement import charger as charger_pre, empreinte
from aion.veritas import Evidence, check

app = FastAPI(
    title="AION",
    description="Kernel de confiance déterministe. La preuve décide, pas l'intention.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ledger() -> Ledger:
    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    return led


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "AION",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "endpoints": ["/status", "/audit", "/decide", "/preenreg"],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/status")
def status() -> dict[str, Any]:
    pre = charger_pre()
    rapport = auditer(CAS, MONDE, _ledger())
    return {
        "version": __version__,
        "preenregistrement": {
            "version": pre["version"],
            "date_gel": pre["date_gel"],
            "empreinte": empreinte(),
            "entree_reference": pre["entree_de_reference"],
            "ecart_aion_raw_minimum": pre["criteres"]["ecart_aion_raw_minimum"],
        },
        "audit": {
            "verdict": rapport.verdict,
            "cas": rapport.cas,
            "corpus_hash": rapport.corpus_hash,
            "bloquants": len(rapport.bloquants),
            "alertes": len(rapport.alertes),
        },
        "env": {
            "provider_default": os.environ.get("AION_PROVIDER", "local"),
            "render": bool(os.environ.get("RENDER")),
        },
    }


@app.get("/preenreg")
def preenreg() -> dict[str, Any]:
    pre = charger_pre()
    return {"empreinte": empreinte(), "contenu": pre}


@app.get("/audit")
def audit() -> dict[str, Any]:
    return resume_audit(CAS, MONDE, _ledger())


class DecideIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    premisse_fausse: bool = False
    ambigu: bool = False
    consequence_reelle: bool = False
    connaissance_datee: bool = False
    age_connaissance_jours: int = 0
    source_externe_possible: bool = True
    sources_divergentes: bool = False
    autorite_utilisateur: bool = False
    hors_domaine: bool = False
    fait_cle: str = ""


@app.post("/decide")
def decide(body: DecideIn) -> dict[str, Any]:
    sit = Situation(
        question=body.question,
        premisse_fausse=body.premisse_fausse,
        ambigu=body.ambigu,
        consequence_reelle=body.consequence_reelle,
        connaissance_datee=body.connaissance_datee,
        age_connaissance_jours=body.age_connaissance_jours,
        source_externe_possible=body.source_externe_possible,
        sources_divergentes=body.sources_divergentes,
        autorite_utilisateur=body.autorite_utilisateur,
        hors_domaine=body.hors_domaine,
        fait_cle=body.fait_cle,
    )
    choix = selectionner(sit, _ledger())
    return {
        "action": choix.action.value,
        "regle": choix.regle,
        "justification": choix.motif,
        "question": body.question,
    }


class VeritasIn(BaseModel):
    claim: str = Field(..., min_length=1)
    evidences: list[dict[str, Any]] = Field(default_factory=list)
    max_age_days: int = 180


@app.post("/veritas")
def veritas(body: VeritasIn) -> dict[str, Any]:
    evs = []
    for e in body.evidences:
        try:
            evs.append(
                Evidence(
                    source=str(e.get("source", "")),
                    supports=bool(e.get("supports", True)),
                    age_days=int(e.get("age_days", 0)),
                    trusted=bool(e.get("trusted", True)),
                )
            )
        except Exception as exc:
            raise HTTPException(400, f"evidence invalide: {exc}") from exc
    ruling = check(body.claim, evs, max_age_days=body.max_age_days)
    return {
        "claim": body.claim,
        "verdict": ruling.verdict.value,
        "reason": ruling.reason,
    }
