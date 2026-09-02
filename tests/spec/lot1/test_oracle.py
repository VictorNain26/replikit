"""VER-01, VER-02, VER-06, VER-08, D3, D4 — l'oracle, et ce qui l'empêche
d'être un tampon.

Entrée : la trace de `fixtures/trace/`, mutée dans le test sur une seule famille à la fois.
Un différentiel qui rate la famille mutée, ou en signale une autre, échoue.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import FAMILLES_DIFF, FIXTURES, RACINE, copie_trace, ecrire_json, etape, lire_json


def _paire(tmp_path: Path) -> tuple[Path, Path, Path]:
    entree = tmp_path / "in"
    entree.mkdir()
    a = copie_trace(entree / "a")
    b = copie_trace(entree / "b")
    return entree, a, b


def _muter(trace: Path, famille: str) -> None:
    if famille == "reponses":
        har = lire_json(trace / "reseau.har")
        corps = json.loads(har["log"]["entries"][1]["response"]["content"]["text"])
        corps["email"] = "eve@example.test"
        har["log"]["entries"][1]["response"]["content"]["text"] = json.dumps(corps)
        ecrire_json(trace / "reseau.har", har)
    elif famille == "etat_persistant":
        etat = lire_json(trace / "etat.json")
        etat["teams"].pop()
        ecrire_json(trace / "etat.json", etat)
    elif famille == "contenu_ecran":
        shutil.copy(FIXTURES / "ecrans" / "role.yaml", trace / "ecrans" / "connexion.yaml")
    elif famille == "evenements_temps_reel":
        lignes = (trace / "evenements.jsonl").read_text(encoding="utf-8").splitlines()
        (trace / "evenements.jsonl").write_text(lignes[0] + "\n", encoding="utf-8")
    elif famille == "messages_erreur":
        har = lire_json(trace / "reseau.har")
        corps = json.loads(har["log"]["entries"][3]["response"]["content"]["text"])
        corps["detail"] = "Incorrect email or password."
        har["log"]["entries"][3]["response"]["content"]["text"] = json.dumps(corps)
        ecrire_json(trace / "reseau.har", har)


def _ecarts(sortie: Path) -> list[dict]:
    return lire_json(sortie / "ecarts.json")["ecarts"]


def test_deux_traces_identiques_donnent_zero_ecart(tmp_path):
    """Casse : un différentiel qui invente un écart, ou qui compare des horodatages de fichiers."""
    entree, _, _ = _paire(tmp_path)
    etape("judge/diff", entree, tmp_path / "out")
    assert _ecarts(tmp_path / "out") == []


@pytest.mark.parametrize("famille", FAMILLES_DIFF)
def test_le_differentiel_isole_la_famille_modifiee(tmp_path, famille):
    """VER-01 : « réponses, état persistant, contenu d'écran, événements temps réel,
    messages d'erreur ». Une mutation sur une famille produit un écart dans cette famille
    et aucune autre. Casse : une famille non comparée, ou un écart mal classé."""
    entree, _, b = _paire(tmp_path)
    _muter(b, famille)
    etape("judge/diff", entree, tmp_path / "out")
    familles = {e["famille"] for e in _ecarts(tmp_path / "out")}
    assert familles == {famille}, f"mutation sur {famille}, écarts signalés dans {sorted(familles) or 'aucune famille'}"


def test_chaque_ecart_porte_sa_reproduction(tmp_path):
    """VER-06 : « chaque écart portant sa trace de reproduction ». Casse : un écart sans
    scénario ni chemin dans la trace."""
    entree, _, b = _paire(tmp_path)
    _muter(b, "reponses")
    etape("judge/diff", entree, tmp_path / "out")
    for ecart in _ecarts(tmp_path / "out"):
        assert ecart.get("reproduction", {}).get("scenario"), f"écart sans scénario de reproduction : {ecart}"
        assert ecart.get("chemin"), f"écart sans chemin dans la trace : {ecart}"


def test_un_identifiant_lie_ne_produit_pas_d_ecart(tmp_path):
    """D3 : un identifiant est lié à sa première apparition. Deux traces où `u_01HZX4K`
    est partout remplacé par `u_02QQQ9Z` sont équivalentes. Casse : un comparateur qui
    compare les identifiants à la lettre — ou qui les ignore, voir le test suivant."""
    entree, _, b = _paire(tmp_path)
    for fichier in (b / "reseau.har", b / "etat.json", b / "evenements.jsonl"):
        fichier.write_text(fichier.read_text(encoding="utf-8").replace("u_01HZX4K", "u_02QQQ9Z"), encoding="utf-8")
    etape("judge/diff", entree, tmp_path / "out")
    assert _ecarts(tmp_path / "out") == [], "un identifiant renommé de façon cohérente n'est pas un écart"


def test_un_identifiant_incoherent_produit_un_ecart(tmp_path):
    """D3, l'autre moitié : une réapparition doit référencer la même variable. Si `/api/me`
    rend un autre identifiant que la connexion, c'est un écart, qu'un masquage laisserait
    passer. Casse : un comparateur qui neutralise les identifiants au lieu de les lier."""
    entree, _, b = _paire(tmp_path)
    har = lire_json(b / "reseau.har")
    har["log"]["entries"][1]["response"]["content"]["text"] = har["log"]["entries"][1]["response"]["content"]["text"].replace("u_01HZX4K", "u_02QQQ9Z")
    ecrire_json(b / "reseau.har", har)
    etape("judge/diff", entree, tmp_path / "out")
    assert _ecarts(tmp_path / "out"), "deux identifiants pour le même objet sont passés"


def test_une_politique_sans_releve_est_refusee(tmp_path):
    """VER-02, D3 : « une neutralisation sans relevé est refusée ». Casse : une politique
    acceptée sur sa seule bonne foi."""
    entree = tmp_path / "in"
    shutil.copytree(FIXTURES / "politique", entree)
    shutil.copy(entree / "sans_releve.yaml", entree / "equivalence.yaml")
    proc = etape("judge/policy", entree, tmp_path / "out", attendu=None)
    assert proc.returncode != 0, "une neutralisation sans relevé A/A a été acceptée"


def test_une_politique_hors_releve_est_refusee(tmp_path):
    """Citer un relevé ne suffit pas : le champ doit y figurer comme variable."""
    entree = tmp_path / "in"
    shutil.copytree(FIXTURES / "politique", entree)
    shutil.copy(entree / "hors_releve.yaml", entree / "equivalence.yaml")
    proc = etape("judge/policy", entree, tmp_path / "out", attendu=None)
    assert proc.returncode != 0, "un champ absent du relevé A/A a été neutralisé"


def test_la_politique_change_le_verdict(tmp_path):
    """« Une politique que rien ne parse est un document, pas une politique. » Sans
    politique, un en-tête Date différent est un écart ; avec la politique qui le
    neutralise sur relevé, il n'en est plus un. Casse : une politique lue mais sans effet."""
    entree, _, b = _paire(tmp_path)
    har = lire_json(b / "reseau.har")
    har["log"]["entries"][0]["response"]["headers"][1]["value"] = "Tue, 01 Sep 2026 11:30:00 GMT"
    ecrire_json(b / "reseau.har", har)
    etape("judge/diff", entree, tmp_path / "sans")
    assert _ecarts(tmp_path / "sans"), "un en-tête Date différent devrait être un écart sans politique"

    politique_in = tmp_path / "politique"
    shutil.copytree(FIXTURES / "politique", politique_in)
    shutil.copy(politique_in / "date.yaml", politique_in / "equivalence.yaml")
    etape("judge/policy", politique_in, tmp_path / "politique_out")
    shutil.copy(tmp_path / "politique_out" / "politique.json", entree / "politique.json")
    etape("judge/diff", entree, tmp_path / "avec")
    assert _ecarts(tmp_path / "avec") == [], "la politique compilée n'a pas changé le verdict"


def test_les_fautes_semees_couvrent_chaque_famille_et_sont_detectees(tmp_path):
    """VER-08, D4 : le taux est le rapport des fautes détectées sur les fautes semées, et le
    test le calcule lui-même en rejouant le différentiel sur chaque faute. Casse : un jeu
    qui ne mute qu'une famille, ou une faute que le différentiel ne voit pas."""
    entree = tmp_path / "in"
    entree.mkdir()
    copie_trace(entree / "trace")
    sortie = tmp_path / "fautes"
    etape("judge/mutate", entree, sortie)
    fautes = lire_json(sortie / "fautes.json")["fautes"]
    assert fautes, "aucune faute semée"
    assert {f["famille"] for f in fautes} >= set(FAMILLES_DIFF), "des familles n'ont aucune faute semée"
    assert {f["origine"] for f in fautes} <= {"initial", "ver07"}, "chaque faute dit d'où elle vient (D4)"
    ratees = []
    for faute in fautes:
        paire = tmp_path / f"paire_{faute['id']}"
        paire.mkdir()
        copie_trace(paire / "a")
        shutil.copytree(sortie / faute["chemin"], paire / "b")
        etape("judge/diff", paire, tmp_path / f"diff_{faute['id']}")
        if not _ecarts(tmp_path / f"diff_{faute['id']}"):
            ratees.append(faute["id"])
    taux = 1 - len(ratees) / len(fautes)
    assert 0.0 <= taux <= 1.0
    assert not ratees, f"fautes semées non détectées ({taux:.0%} détectées) : {', '.join(ratees)}"
