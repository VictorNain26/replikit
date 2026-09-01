"""CAP-01, CAP-02 — la capture, et ce qu'une trace doit porter.

La source de vérité est `docs/cahier-des-charges.md`. Les familles ci-dessous sont celles de
son §2, qui définit le mot *Trace* — « enregistrement horodaté d'un parcours : actions,
requêtes réseau, messages des canaux temps réel, états DOM, réponses ». Son §4.1 ajoute ce
que l'enregistreur capture en plus : captures d'écran et horodatage relatif.

Décision n°2 à ratifier : une trace est un répertoire d'artefacts produit par
`observe/normalise`, et non la sortie brute de `observe/drive` — le cahier §4.1 fait de la
normalisation une fonction de capture à part entière, « seul contrat consommé par
l'inférence et la vérification ».
"""

from __future__ import annotations

from conftest import importe

# §2 du cahier, mot pour mot.
FAMILLES_VOCABULAIRE = ("actions", "requetes_reseau", "messages_temps_reel", "etats_dom", "reponses")
# §4.1, ce que l'enregistrement de parcours capture en plus.
FAMILLES_ENREGISTREMENT = ("captures_ecran", "horodatage_relatif")


def _trace(tmp_path):
    drive, normalise = importe("observe/drive"), importe("observe/normalise")
    brut = drive.capturer(scenario=tmp_path / "connexion.yaml", sortie=tmp_path / "brut")
    return normalise.trace(brut)


def test_une_trace_porte_les_familles_du_vocabulaire(tmp_path):
    """§2 : ces cinq familles *sont* la définition d'une trace dans ce cahier."""
    trace = _trace(tmp_path)
    manquantes = [f for f in FAMILLES_VOCABULAIRE if f not in trace.familles]
    assert not manquantes, f"familles absentes de la trace : {', '.join(manquantes)}"


def test_l_enregistrement_capture_aussi_ecran_et_horodatage_relatif(tmp_path):
    """§4.1 : « instantanés DOM avant/après, captures d'écran, horodatage relatif »."""
    trace = _trace(tmp_path)
    manquantes = [f for f in FAMILLES_ENREGISTREMENT if f not in trace.familles]
    assert not manquantes, f"non capturé : {', '.join(manquantes)}"


def test_la_normalisation_lie_chaque_valeur_produite_a_une_variable(tmp_path):
    """D1 : « chaque valeur produite par le système est liée à une variable symbolique à sa
    première apparition ; toute réapparition doit référencer la même variable »."""
    trace = _trace(tmp_path)
    assert trace.liaisons, "aucune valeur produite n'a été liée : D1 n'est pas appliquée"
    for valeur, variables in trace.liaisons_brutes.items():
        assert len(set(variables)) == 1, f"la valeur {valeur!r} est liée à {len(set(variables))} variables"


def test_deux_captures_du_meme_scenario_donnent_le_meme_identifiant(tmp_path):
    """P1 rencontre D1 : sans liaison symbolique, deux captures du même parcours n'ont pas le
    même contenu, donc pas le même identifiant, et le cache promis par P1 ne fonctionne pas."""
    drive, normalise = importe("observe/drive"), importe("observe/normalise")
    scenario = tmp_path / "connexion.yaml"
    a = normalise.trace(drive.capturer(scenario=scenario, sortie=tmp_path / "a"))
    b = normalise.trace(drive.capturer(scenario=scenario, sortie=tmp_path / "b"))
    assert a.identifiant == b.identifiant


def test_le_run_aa_caracterise_les_trois_axes_nommes_par_cap_02(tmp_path):
    """CAP-02 : « caractériser ce qui varie d'une exécution à l'autre — identifiants,
    horodatages, ordre ». Le rejeu A/A se fait **sur la cible** : c'est `observe/drive`."""
    drive, normalise, diff = importe("observe/drive"), importe("observe/normalise"), importe("judge/diff")
    scenario = tmp_path / "connexion.yaml"
    a = normalise.trace(drive.rejouer_sur_cible(scenario=scenario, sortie=tmp_path / "a"))
    b = normalise.trace(drive.rejouer_sur_cible(scenario=scenario, sortie=tmp_path / "b"))
    releve = diff.comparer(a, b).non_determinisme
    manquants = [axe for axe in ("identifiants", "horodatages", "ordre") if axe not in releve]
    assert not manquants, f"axes de non-déterminisme non caractérisés : {', '.join(manquants)}"


def test_la_trace_porte_la_version_de_la_cible_observee(tmp_path):
    """CAP-07 : « versionnées, avec la version de la cible observée ». Sans ça, un run A/A
    compare deux exécutions dont rien ne garantit qu'elles ont vu la même cible."""
    trace = _trace(tmp_path)
    assert trace.version_cible, "la trace ne dit pas quelle version de la cible elle a observée"
