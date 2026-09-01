"""D2 — aucune neutralisation sans mesure préalable.

La règle 2 de `CLAUDE.md`, et la seule qui protège l'oracle d'être négocié : un champ ne peut
être neutralisé que si un run A/A a démontré qu'il varie. Ces deux tests sont ceux dont
l'échec doit faire arrêter la campagne, pas ajuster le seuil.
"""

from __future__ import annotations

import pytest

from conftest import importe


def test_neutralisation_sans_run_aa_est_refusee(tmp_path):
    """Une entrée de politique qui ne cite aucun run A/A est rejetée à la compilation."""
    policy = importe("judge/policy")
    fichier = tmp_path / "equivalence.yaml"
    fichier.write_text(
        "neutralisations:\n"
        "  - champ: reponse.body.created_at\n"
        "    motif: horodatage\n",  # aucun run A/A cité
        encoding="utf-8",
    )
    with pytest.raises(policy.NeutralisationNonJustifiee):
        policy.compile(fichier)


def test_neutralisation_citant_un_run_aa_ou_le_champ_ne_varie_pas_est_refusee(tmp_path):
    """Citer un run ne suffit pas : le run doit montrer que le champ varie effectivement."""
    policy = importe("judge/policy")
    aa = tmp_path / "aa.json"
    aa.write_text('{"champs_variables": ["reponse.body.id"]}', encoding="utf-8")
    fichier = tmp_path / "equivalence.yaml"
    fichier.write_text(
        "neutralisations:\n"
        "  - champ: reponse.body.created_at\n"
        "    motif: horodatage\n"
        f"    run_aa: {aa}\n",
        encoding="utf-8",
    )
    with pytest.raises(policy.NeutralisationNonJustifiee):
        policy.compile(fichier)


def test_politique_est_lue_par_le_code_pas_seulement_relue(tmp_path):
    """« Une politique que rien ne parse est un document, pas une politique » — plan, lot 2.

    Le test qui l'établit : modifier une entrée du fichier doit changer le comparateur.
    """
    policy = importe("judge/policy")
    aa = tmp_path / "aa.json"
    aa.write_text('{"champs_variables": ["reponse.body.id"]}', encoding="utf-8")
    vide = tmp_path / "vide.yaml"
    vide.write_text("neutralisations: []\n", encoding="utf-8")
    une = tmp_path / "une.yaml"
    une.write_text(
        "neutralisations:\n"
        "  - champ: reponse.body.id\n"
        "    motif: identifiant aléatoire\n"
        f"    run_aa: {aa}\n",
        encoding="utf-8",
    )
    assert policy.compile(vide) != policy.compile(une)
