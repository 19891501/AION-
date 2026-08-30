"""AION Web API + interface décision."""

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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from aion import __version__
    from aion.audit import auditer, resume_audit
    from aion.behavior import Situation, selectionner
    from aion.bench.cases import CAS, LEDGER_SEED, MONDE
    from aion.ledger import Ledger
    from aion.preenregistrement import charger as charger_pre, empreinte
    from aion.veritas import Evidence, check
    from aion.pipeline import run_pipeline

    AION_OK = True
    _IMPORT_ERROR = ""
except ImportError as exc:
    __version__ = "0.1.0-partial"
    AION_OK = False
    _IMPORT_ERROR = str(exc)

app = FastAPI(title="AION", description="La preuve décide, pas l'intention.", version=__version__)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
_STATIC = Path(__file__).resolve().parent / "static"
if _STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


def _require_aion() -> None:
    if not AION_OK:
        raise HTTPException(503, f"package aion incomplet: {_IMPORT_ERROR}")


def _ledger():
    _require_aion()
    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    return led


@app.get("/")
def root():
    index = _STATIC / "index.html"
    if index.is_file():
        return FileResponse(index)
    return {"service": "AION", "version": __version__, "docs": "/docs"}


@app.get("/api")
def api_info() -> dict[str, Any]:
    return {
        "service": "AION",
        "version": __version__,
        "aion_package": "ok" if AION_OK else f"missing: {_IMPORT_ERROR}",
        "docs": "/docs",
        "endpoints": ["/status", "/audit", "/decide", "/veritas", "/pipeline"],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok" if AION_OK else "degraded",
        "version": __version__,
        "aion_package": "ok" if AION_OK else f"missing: {_IMPORT_ERROR}",
    }


@app.get("/status")
def status() -> dict[str, Any]:
    _require_aion()
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
        "env": {"render": bool(os.environ.get("RENDER"))},
    }


@app.get("/preenreg")
def preenreg() -> dict[str, Any]:
    _require_aion()
    return {"empreinte": empreinte(), "contenu": charger_pre()}


@app.get("/audit")
def audit() -> dict[str, Any]:
    _require_aion()
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
    _require_aion()
    sit = Situation(**body.model_dump())
    choix = selectionner(sit, _ledger())
    return {"action": choix.action.value, "regle": choix.regle, "justification": choix.motif, "question": body.question}


class VeritasIn(BaseModel):
    claim: str = Field(..., min_length=1)
    evidences: list[dict[str, Any]] = Field(default_factory=list)
    max_age_days: int = 180


@app.post("/veritas")
def veritas(body: VeritasIn) -> dict[str, Any]:
    _require_aion()
    evs = [Evidence(source=str(e.get("source", "")), supports=bool(e.get("supports", True)), age_days=int(e.get("age_days", 0)), trusted=bool(e.get("trusted", True))) for e in body.evidences]
    ruling = check(body.claim, evs, max_age_days=body.max_age_days)
    return {"claim": body.claim, "verdict": ruling.verdict.value, "reason": ruling.reason}


class PipelineIn(BaseModel):
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
    claim: str | None = None
    evidences: list[dict] = Field(default_factory=list)
    stake: dict | None = None


@app.post("/pipeline")
def pipeline(body: PipelineIn) -> dict:
    _require_aion()
    flags = body.model_dump(exclude={"claim", "evidences", "stake", "question"})
    return run_pipeline(question=body.question, flags=flags, claim=body.claim, evidences=body.evidences or None, stake=body.stake).to_dict()
