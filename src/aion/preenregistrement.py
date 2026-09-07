"""Pre-enregistrement : figer les criteres AVANT la campagne, et le prouver.

Le fichier `preenregistrement.json` contient les hypotheses, les seuils et la
regle de decision go / simplifier / no-go. Son empreinte SHA-256 est ecrite dans
chaque rapport de campagne. Modifier un seuil apres coup change l'empreinte et
rend toutes les campagnes anterieures NON CONFORMES — la triche devient visible
dans un diff au lieu d'etre invisible dans une intention.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

CHEMIN_DEFAUT = "preenregistrement.json"


@dataclass(frozen=True)
class Verdict:
    critere: str
    conforme: bool
    detail: str


def charger(chemin: str | Path = CHEMIN_DEFAUT) -> dict:
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def empreinte(chemin: str | Path = CHEMIN_DEFAUT) -> str:
    """Empreinte du contenu normalise : insensible a la mise en forme, pas aux valeurs."""
    charge = charger(chemin)
    canonique = json.dumps(charge, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonique.encode()).hexdigest()


def _bar(rapports: dict, bras: str) -> float:
    return float(rapports[bras]["bar_moyen"])


def verifier(campagne: dict, pre: dict | None = None) -> list[Verdict]:
    """Confronte une campagne (JSON ecrit par `aion bench`) au pre-enregistrement."""
    pre = pre or charger()
    c = pre["criteres"]
    rapports = campagne["rapports"]
    aion = rapports["AION"]
    verdicts: list[Verdict] = []

    attendue = campagne.get("preenregistrement_empreinte", "")
    verdicts.append(
        Verdict(
            "empreinte",
            attendue == empreinte(),
            "criteres inchanges depuis la campagne" if attendue == empreinte()
            else f"criteres modifies depuis la campagne (rapport: {attendue[:12] or 'absent'})",
        )
    )

    if aion["entree"] != pre["entree_de_reference"]:
        verdicts.append(
            Verdict("entree", False, f"entree {aion['entree']}, reference {pre['entree_de_reference']}")
        )

    ecart_raw = _bar(rapports, "AION") - _bar(rapports, "RAW")
    ecart_sca = _bar(rapports, "AION") - _bar(rapports, "SCAFFOLD")
    verdicts.append(Verdict("ecart AION-RAW", ecart_raw >= c["ecart_aion_raw_minimum"],
                            f"{ecart_raw:+.3f} (seuil {c['ecart_aion_raw_minimum']})"))
    verdicts.append(Verdict("ecart AION-SCAFFOLD", ecart_sca >= c["ecart_aion_scaffold_minimum"],
                            f"{ecart_sca:+.3f} (seuil {c['ecart_aion_scaffold_minimum']})"))

    fs = float(aion["resume"]["taux_faux_succes"])
    verdicts.append(Verdict("faux succes", fs <= c["faux_succes_aion_maximum"],
                            f"{fs:.3f} (max {c['faux_succes_aion_maximum']})"))

    resume = aion.get("resume") or {}
    if "faux_refus_aion_maximum" in c and resume.get("taux_faux_refus") is not None:
        fr = float(resume["taux_faux_refus"])
        verdicts.append(Verdict(
            "faux refus", fr <= c["faux_refus_aion_maximum"],
            f"{fr:.3f} (max {c['faux_refus_aion_maximum']})",
        ))
    if "surblocage_aion_maximum" in c and resume.get("taux_surblocage") is not None:
        sb = float(resume["taux_surblocage"])
        verdicts.append(Verdict(
            "surblocage", sb <= c["surblocage_aion_maximum"],
            f"{sb:.3f} (max {c['surblocage_aion_maximum']})",
        ))

    # Gain par famille (H1)
    fam_req = c.get("familles_gain_requises") or []
    fam_min = int(c.get("familles_gain_minimum") or 0)
    if fam_min or fam_req:
        aion_f = (resume.get("bar_par_famille") or {})
        raw_f = ((rapports.get("RAW") or {}).get("resume") or {}).get("bar_par_famille") or {}
        gains = [f for f, v in aion_f.items() if float(v) > float(raw_f.get(f, 0))]
        ok_n = len(gains) >= fam_min if fam_min else True
        ok_req = all(f in gains for f in fam_req)
        verdicts.append(Verdict(
            "gain familles",
            ok_n and ok_req,
            f"gains={gains} (min {fam_min}, requises {fam_req})",
        ))

    modele = aion["extracteur"] == "llm"
    seuil_et = c["ecart_type_bar_maximum_modele"] if modele else c["ecart_type_bar_maximum_deterministe"]
    et = float(aion["bar_ecart_type"])
    verdicts.append(Verdict("stabilite (ecart-type)", et <= seuil_et,
                            f"{et:.3f} (max {seuil_et}, extracteur {aion['extracteur']})"))

    if modele:
        amplitude = float(aion["bar_max"]) - float(aion["bar_min"])
        verdicts.append(Verdict("amplitude", amplitude <= c["amplitude_bar_maximum_modele"],
                                f"{amplitude:.3f} (max {c['amplitude_bar_maximum_modele']})"))
        verdicts.append(Verdict("sorties illisibles",
                                aion["echecs_parse"] <= c["echecs_parse_maximum_par_campagne"],
                                f"{aion['echecs_parse']} (max {c['echecs_parse_maximum_par_campagne']})"))
        verdicts.append(Verdict("appels", aion["appels_extraction"] <= c["appels_maximum_par_campagne"],
                                f"{aion['appels_extraction']} (max {c['appels_maximum_par_campagne']})"))

    corpus = pre["conditions_de_validite_du_corpus"]
    assez = campagne.get("cas_total", 0) >= corpus["cas_minimum"]
    verdicts.append(Verdict("taille du corpus", assez,
                            f"{campagne.get('cas_total', 0)} cas (minimum {corpus['cas_minimum']})"))
    verdicts.append(Verdict("corpus externe", bool(campagne.get("corpus_externe", False)),
                            "redige par une personne exterieure" if campagne.get("corpus_externe")
                            else "redige par l'auteur du systeme"))
    return verdicts


def decision(campagne: dict, pre: dict | None = None) -> str:
    """Applique la regle go / simplifier / no-go, sans interpretation."""
    pre = pre or charger()
    c = pre["criteres"]
    rapports = campagne["rapports"]
    ecart = _bar(rapports, "AION") - _bar(rapports, "RAW")
    if ecart < c["ecart_aion_scaffold_minimum"]:
        return "NO_GO"
    if ecart < c["ecart_aion_raw_minimum"]:
        return "SIMPLIFIER"
    return "GO"
