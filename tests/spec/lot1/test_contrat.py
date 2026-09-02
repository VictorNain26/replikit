"""P1, P3, P5 et le contrat d'invocation — ce que toute étape doit respecter avant d'exister.

`docs/architecture.md` §2 et §4. Ces tests lisent des fichiers ; aucun ne peut être
satisfait par une étape qui fabrique sa sortie sans lire son entrée.
"""

from __future__ import annotations

import subprocess
import sys

from conftest import IMPORT_LLM, IMPORT_PAQUET, PAQUETS, RACINE, etapes_du_lot, sources

LOT = 1


def test_les_sept_paquets_existent():
    manquants = [p for p in PAQUETS if not (RACINE / p).is_dir()]
    assert not manquants, f"paquets absents : {', '.join(manquants)}"


def test_chaque_etape_du_lot_repond_a_in_et_out():
    """§4 : « toute étape s'invoque de la même façon ». Casse : une étape du lot absente du
    dépôt, ou qui n'accepte pas `--in` et `--out`. Le lot 2 relance ce test avec `LOT = 2`."""
    etapes = etapes_du_lot(LOT)
    assert etapes, "aucune étape trouvée pour ce lot dans le tableau §6 de docs/plan.md"
    fautives = []
    for nom in etapes:
        proc = subprocess.run([sys.executable, "-m", nom.replace("/", "."), "--help"],
                              cwd=RACINE, capture_output=True, text=True)
        if proc.returncode != 0:
            fautives.append(f"{nom} : n'existe pas encore")
        elif "--in" not in proc.stdout or "--out" not in proc.stdout:
            fautives.append(f"{nom} : n'accepte pas --in et --out")
    assert not fautives, "\n".join(fautives)


def test_aucun_module_des_paquets_n_importe_un_paquet():
    """P1 : « aucune étape n'en appelle une autre » — ni d'un autre paquet, ni du sien.
    Casse : un `from observe.record import …` dans `observe/aa.py`."""
    fichiers = [f for p in PAQUETS for f in sources(p)]
    assert fichiers, "aucun des sept paquets n'a de code"
    fautifs = [
        f"{f.relative_to(RACINE)} : {m.group(0).strip()}"
        for f in fichiers
        for m in IMPORT_PAQUET.finditer(f.read_text(encoding="utf-8"))
    ]
    assert not fautifs, "une étape en importe une autre :\n" + "\n".join(fautifs)


def test_aucun_import_de_client_de_modele_sous_judge():
    """P3. Casse : n'importe quel SDK de modèle importé sous `judge/`."""
    fichiers = sources("judge")
    assert fichiers, "le paquet `judge` n'a pas de code"
    fautifs = [
        f"{f.relative_to(RACINE)} : {m.group(0).strip()}"
        for f in fichiers
        for m in IMPORT_LLM.finditer(f.read_text(encoding="utf-8"))
    ]
    assert not fautifs, "une étape qui prononce appelle un modèle :\n" + "\n".join(fautifs)


def test_aucun_paquet_ne_nomme_une_cible():
    """P5. Casse : le nom d'un répertoire de `targets/` apparaît sous un paquet."""
    fichiers = [f for p in PAQUETS for f in sources(p)]
    assert fichiers, "aucun des sept paquets n'a de code"
    cibles = [d.name for d in (RACINE / "targets").iterdir() if d.is_dir()] if (RACINE / "targets").is_dir() else []
    assert cibles, "aucune cible déclarée sous targets/"
    fautifs = [
        f"{f.relative_to(RACINE)} nomme la cible {c}"
        for f in fichiers
        for c in cibles
        if c in f.read_text(encoding="utf-8")
    ]
    assert not fautifs, "\n".join(fautifs)
