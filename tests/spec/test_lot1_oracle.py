"""VER-01, VER-11 — le différentiel, et ce qui l'empêche d'être un tampon.

Décision n°3 à ratifier : `scope.yaml` porte les écrans, les entités et les opérations du
périmètre déclaré, et une campagne refuse de tourner s'il n'a pas été arrêté avant elle.
"""

from __future__ import annotations

import pytest

from conftest import importe

FAMILLES_DIFF = ("reponses", "etat_persistant", "contenu_ecran", "evenements_temps_reel", "messages_erreur")


def test_le_differentiel_couvre_les_cinq_familles(tmp_path):
    """VER-01 : « réponses, état persistant, contenu d'écran, événements temps réel,
    messages d'erreur »."""
    diff = importe("judge/diff")
    resultat = diff.comparer(tmp_path / "cible", tmp_path / "clone")
    manquantes = [f for f in FAMILLES_DIFF if f not in resultat.familles]
    assert not manquantes, f"familles non comparées : {', '.join(manquantes)}"


def test_chaque_ecart_porte_sa_trace_de_reproduction(tmp_path):
    """Critère de sortie du lot 1 : « chaque écart portant la trace qui le produit »."""
    diff = importe("judge/diff")
    resultat = diff.comparer(tmp_path / "cible", tmp_path / "clone")
    orphelins = [e for e in resultat.ecarts if not e.trace]
    assert not orphelins, f"{len(orphelins)} écart(s) sans trace de reproduction"


def test_un_rapport_sans_taux_de_detection_est_refuse(tmp_path):
    """VER-11 : « un compte d'écarts non accompagné de son taux de détection n'est pas un
    résultat ». Le rapport refuse de s'écrire, il ne se contente pas d'avertir."""
    diff = importe("judge/diff")
    resultat = diff.comparer(tmp_path / "cible", tmp_path / "clone")
    with pytest.raises(diff.TauxDeDetectionManquant):
        resultat.publier(sortie=tmp_path / "rapport.json")


def test_le_taux_de_detection_est_mesure_sur_le_jeu_de_fautes(tmp_path):
    """VER-11 : le taux est le rapport des fautes semées détectées sur les fautes semées."""
    mutate, diff = importe("judge/mutate"), importe("judge/diff")
    jeu = mutate.jeu_initial(trace=tmp_path / "trace")
    assert jeu.fautes, "le jeu de fautes initial est vide : le taux ne veut rien dire"
    taux = diff.taux_de_detection(jeu)
    assert 0.0 <= taux <= 1.0


def test_le_jeu_de_fautes_n_est_pas_accessible_au_generateur():
    """VER-11 : « le jeu de fautes n'est pas exposé au générateur ».

    Un générateur qui voit les fautes semées apprend les fautes, pas la fidélité. La
    protection est structurelle : aucun bloc qui produit du clone n'importe `judge/mutate`.
    """
    from conftest import RACINE, sources

    producteurs = [f for p in ("build", "orchestrate") for f in sources(p)]
    assert producteurs, "les paquets `build` et `orchestrate` n'existent pas encore"
    fautifs = [
        str(f.relative_to(RACINE))
        for f in producteurs
        if "judge.mutate" in f.read_text(encoding="utf-8") or "judge/mutate" in f.read_text(encoding="utf-8")
    ]
    assert not fautifs, "le générateur voit le jeu de fautes :\n" + "\n".join(fautifs)


def test_une_campagne_refuse_de_tourner_sans_perimetre_arrete(tmp_path):
    """`docs/cahier-des-charges.md` §12 : sans périmètre arrêté et versionné avant la
    campagne, « zéro écart » et « 100 % » s'obtiennent en rétrécissant le périmètre."""
    diff = importe("judge/diff")
    with pytest.raises(diff.PerimetreNonArrete):
        diff.campagne(cible=tmp_path / "cible", clone=tmp_path / "clone", scope=None)
