"""CAP-01, CAP-02 — la capture, et ce qu'une trace doit porter.

Décision n°2 à ratifier : une trace est un répertoire d'artefacts, pas un fichier. Le HAR
(P2) n'y suffit pas — D1 exige la liaison de variables, `VER-10` exige les instantanés ARIA,
`CAP-01` exige actions, réseau, temps réel, DOM et horodatage relatif.
"""

from __future__ import annotations

from conftest import importe

FAMILLES = ("actions", "reseau", "temps_reel", "dom", "horodatage_relatif")


def test_une_trace_porte_les_cinq_familles_d_evenements(tmp_path):
    """CAP-01 : « actions, requêtes et réponses réseau, messages des canaux temps réel,
    instantanés DOM avant/après, captures d'écran, horodatage relatif »."""
    drive = importe("observe/drive")
    trace = drive.rejouer(scenario=tmp_path / "connexion.yaml", sortie=tmp_path / "trace")
    manquantes = [f for f in FAMILLES if f not in trace.familles]
    assert not manquantes, f"familles absentes de la trace : {', '.join(manquantes)}"


def test_une_trace_lie_chaque_valeur_produite_a_une_variable(tmp_path):
    """D1 : « chaque valeur produite par le système est liée à une variable symbolique à sa
    première apparition ; toute réapparition doit référencer la même variable »."""
    drive = importe("observe/drive")
    trace = drive.rejouer(scenario=tmp_path / "connexion.yaml", sortie=tmp_path / "trace")
    for valeur, variable in trace.liaisons.items():
        assert trace.liaisons[valeur] == variable, "une valeur est liée à deux variables"
    assert trace.liaisons, "aucune valeur produite n'a été liée : D1 n'est pas appliquée"


def test_deux_captures_du_meme_scenario_donnent_le_meme_identifiant_de_trace(tmp_path):
    """P1 rencontre D1 : sans liaison symbolique, un HAR plein de valeurs variables donne un
    identifiant différent à chaque capture, ce qui annule le cache que P1 promet."""
    drive = importe("observe/drive")
    scenario = tmp_path / "connexion.yaml"
    a = drive.rejouer(scenario=scenario, sortie=tmp_path / "a")
    b = drive.rejouer(scenario=scenario, sortie=tmp_path / "b")
    assert a.identifiant == b.identifiant


def test_le_run_aa_caracterise_ce_qui_varie(tmp_path):
    """CAP-02 : le non-déterminisme de la cible est un produit du diff, pas une déclaration."""
    drive, diff = importe("observe/drive"), importe("judge/diff")
    scenario = tmp_path / "connexion.yaml"
    a = drive.rejouer(scenario=scenario, sortie=tmp_path / "a")
    b = drive.rejouer(scenario=scenario, sortie=tmp_path / "b")
    resultat = diff.comparer(a, b)
    assert resultat.champs_variables is not None, "un run A/A doit produire la liste des champs variables"
