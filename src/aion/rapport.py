"""Rapport de campagne lisible (markdown) à côté du JSON technique.

Le JSON reste la source de vérité. Le markdown sert à la lecture humaine.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _bar(r: dict) -> float:
    return float(r.get("bar_moyen", 0))


def generer_markdown(campagne: dict[str, Any]) -> str:
    """Produit un résumé markdown à partir d'un JSON de campagne."""
    rapports = campagne.get("rapports", {})
    micro = bool(campagne.get("micro_campagne"))
    empreinte = campagne.get("preenregistrement_empreinte", "")[:16]
    cas_total = campagne.get("cas_total", "?")
    avertissement = campagne.get("avertissement", "")

    lignes: list[str] = []
    lignes.append("# Rapport de campagne AION")
    lignes.append("")
    if micro:
        lignes.append("> **MICRO-CAMPAGNE** — résultat non opposable au pré-enregistrement S2.")
        lignes.append("")
    lignes.append(f"- Date : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lignes.append(f"- Cas (corpus) : {cas_total}")
    lignes.append(f"- Empreinte pré-enregistrement : `{empreinte}…`")
    lignes.append(f"- Corpus externe : {campagne.get('corpus_externe', False)}")
    lignes.append("")

    # Tableau principal
    lignes.append("## Résultats par bras")
    lignes.append("")
    lignes.append("| Bras | BAR moy | Écart-type | Min | Max | 20/20 | Parse KO | Appels |")
    lignes.append("|------|---------|------------|-----|-----|-------|----------|--------|")
    for nom in ("RAW", "SCAFFOLD", "AION"):
        r = rapports.get(nom, {})
        if not r:
            continue
        lignes.append(
            f"| {nom} "
            f"| {r.get('bar_moyen', 0):.3f} "
            f"| {r.get('bar_ecart_type', 0):.3f} "
            f"| {r.get('bar_min', 0):.2f} "
            f"| {r.get('bar_max', 0):.2f} "
            f"| {r.get('pass_20_controles', False)} "
            f"| {r.get('echecs_parse', 0)} "
            f"| {r.get('appels_extraction', 0)} |"
        )
    lignes.append("")

    # Écarts
    if "AION" in rapports and "RAW" in rapports:
        ecart_raw = _bar(rapports["AION"]) - _bar(rapports["RAW"])
        ecart_sca = _bar(rapports["AION"]) - _bar(rapports.get("SCAFFOLD", {}))
        lignes.append("## Écarts")
        lignes.append("")
        lignes.append(f"- AION − RAW : **{ecart_raw:+.3f}**")
        lignes.append(f"- AION − SCAFFOLD : **{ecart_sca:+.3f}**")
        lignes.append("")

    # Faux succès
    aion = rapports.get("AION", {})
    resume = aion.get("resume") or {}
    if resume:
        lignes.append("## AION — détail")
        lignes.append("")
        lignes.append(f"- Faux succès : {resume.get('taux_faux_succes', '?')}")
        lignes.append(f"- Cas évalués : {resume.get('cas_evalues', '?')}")
        bpf = resume.get("bar_par_famille") or {}
        if bpf:
            lignes.append("- BAR par famille :")
            for f, v in sorted(bpf.items()):
                lignes.append(f"  - {f}: {v:.3f}")
        lignes.append("")

    # Échecs (première répétition)
    echecs = aion.get("echecs") or []
    if echecs:
        lignes.append("## Échecs (1re répétition)")
        lignes.append("")
        lignes.append("| Cas | Famille | Attendu | Obtenu |")
        lignes.append("|-----|---------|---------|--------|")
        for e in echecs[:20]:
            lignes.append(
                f"| {e.get('cas')} | {e.get('famille')} | {e.get('attendu')} | {e.get('obtenu')} |"
            )
        if len(echecs) > 20:
            lignes.append(f"| … | ({len(echecs) - 20} de plus) | | |")
        lignes.append("")

    if avertissement:
        lignes.append("## Avertissement")
        lignes.append("")
        lignes.append(avertissement)
        lignes.append("")

    lignes.append("---")
    lignes.append("*Source de vérité : le fichier JSON associé. Ce markdown est un résumé.*")
    return "\n".join(lignes)


def ecrire_markdown(campagne: dict[str, Any], chemin_json: Path) -> Path:
    """Écrit le .md à côté du .json."""
    md = generer_markdown(campagne)
    chemin_md = chemin_json.with_suffix(".md")
    chemin_md.write_text(md, encoding="utf-8")
    return chemin_md


def charger_campagne(chemin: str | Path) -> dict[str, Any]:
    return json.loads(Path(chemin).read_text(encoding="utf-8"))
