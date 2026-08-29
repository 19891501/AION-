"""Extracteur de drapeaux : correctif de la faille M-02.

Ces tests verrouillent le comportement de l'extracteur, y compris ses trous.
"""

from aion.behavior import Action, selectionner
from aion.bench.cases import CAS, MONDE, PARAPHRASES
from aion.extraction import Monde, ecart_drapeaux, extraire, normaliser


def test_normalisation_neutralise_accents_casse_espaces():
    assert normaliser("  Quel EST le PRIX   actuel ? ") == "quel est le prix actuel ?"


def test_verbe_de_consequence_compte_seulement_en_tete():
    assert extraire("Supprime les produits sans vente", MONDE).consequence_reelle is True
    assert extraire("Quel est le bon moment pour lancer ?", MONDE).consequence_reelle is False


def test_premisse_fausse_indetectable_sans_reference_exterieure():
    """Sans refutation dans le Monde, le drapeau ne peut PAS etre leve.
    C'est le comportement correct : l'extracteur n'invente pas de connaissance.
    """
    texte = "Pourquoi la v3 de l'API a-t-elle supprime les webhooks ?"
    assert extraire(texte, MONDE).premisse_fausse is True
    assert extraire(texte, Monde()).premisse_fausse is False


def test_fait_du_ledger_reconnu_par_mot_cle():
    assert extraire("Reapplique la remise de 30%", MONDE).fait_cle == "remise_30_globale"


def test_hors_perimetre_reconnu():
    assert extraire("Donne la posologie du patient", MONDE).hors_domaine is True


def test_extraction_deterministe():
    t = "Quel est le prix actuel du plan Pro ?"
    assert len({extraire(t, MONDE) for _ in range(50)}) == 1


def test_enonces_canoniques_recuperes_a_au_moins_85_pourcent():
    """Borne basse, pas objectif : le Monde a ete ecrit depuis ces enonces.
    Le taux a BAISSE (1.00 -> 0.85) quand deux cas formules hors du lexique ont
    ete ajoutes. C'est le plafond du lexique ferme, pas une regression."""
    exacts = sum(
        1 for c in CAS if not ecart_drapeaux(c.situation, extraire(c.situation.question, MONDE))
    )
    assert exacts / len(CAS) >= 0.85


def test_plafond_du_lexique_ferme():
    """Deux cas ajoutes le 24/08 sont invisibles pour l'extracteur lexical :
    ils disent la meme chose avec d'autres mots. Aucun ajustement du lexique
    n'est fait ici — ce serait deplacer le plafond, pas le supprimer."""
    hors_lexique = "Quel traitement prescrire pour cette infection ?"
    assert extraire(hors_lexique, MONDE).hors_domaine is False


def test_faille_bruit_de_politesse_casse_la_detection_du_verbe():
    """FAILLE OUVERTE : un mot en tete deplace le verbe et annule le drapeau.

    Trouvee par le protocole des 20 controles (campagne 'texte' instable).
    Non corrigee ici : le correctif appartient a S2, avec re-gel des cas.
    """
    assert extraire("Envoie la campagne a toute la liste", MONDE).consequence_reelle is True
    assert extraire("Bonjour, Envoie la campagne a toute la liste", MONDE).consequence_reelle is False


def test_faille_fragilite_lexicale_sur_paraphrase():
    """FAILLE OUVERTE : moins d'un enonce reecrit sur deux est correctement lu."""
    exacts = sum(
        1 for c in CAS if not ecart_drapeaux(c.situation, extraire(PARAPHRASES[c.id], MONDE))
    )
    assert exacts / len(CAS) < 0.6


def test_paraphrase_degrade_vers_answer_pas_vers_le_hasard():
    """Mode d'echec observe : quand un drapeau manque, la decision retombe sur
    ANSWER (R10). L'echec est donc silencieux, jamais bruyant."""
    obtenues = {selectionner(extraire(PARAPHRASES[c.id], MONDE)).action for c in CAS}
    assert Action.ANSWER in obtenues
