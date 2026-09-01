"""Outils communs à la spécification exécutable.

Aucun import de production ici : les étapes n'existent pas encore, et un import en tête
de fichier transformerait des échecs lisibles en une seule erreur de collecte. Une étape
s'observe par ses fichiers, jamais par ses fonctions (`docs/architecture.md` §4).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PAQUETS = ("observe", "infer", "build", "run", "serve", "judge", "orchestrate")

FAMILLES_DIFF = ("reponses", "etat_persistant", "contenu_ecran", "evenements_temps_reel", "messages_erreur")

IMPORT_LLM = re.compile(
    r"^\s*(?:(?:from|import)\s+(?:anthropic|openai|litellm|langchain\w*|mistralai|cohere|ollama"
    r"|google\.gener\w*|google\.genai|vertexai|groq|together|pydantic_ai|instructor|dspy"
    r"|llama_index|smolagents|autogen\w*|crewai|transformers|huggingface_hub|vllm)\b"
    r"|from\s+google\s+import\s+genai\b)",
    re.M,
)

# P1, lu strictement : aucun module des sept paquets n'importe un module des sept paquets,
# le sien compris. Le code commun vit hors des paquets.
IMPORT_PAQUET = re.compile(
    r"^\s*(?:from\s+(?:%(p)s)(?:\.\w+)*\s+import\b|import\s+(?:%(p)s)(?:\.\w+)*\b)" % {"p": "|".join(PAQUETS)},
    re.M,
)


def sources(paquet: str) -> list[Path]:
    return sorted((RACINE / paquet).rglob("*.py"))


def etapes_declarees() -> list[str]:
    """Les étapes du tableau §4 de docs/architecture.md, dans l'ordre."""
    texte = (RACINE / "docs" / "architecture.md").read_text(encoding="utf-8")
    section = texte.split("## 4. Les étapes", 1)[1].split("\n## 5.", 1)[0]
    return re.findall(r"^\| `((?:%s)/[a-z]+)` \|" % "|".join(PAQUETS), section, re.M)


def etape(nom: str, entree: Path, sortie: Path, *args: str, attendu: int | None = 0) -> subprocess.CompletedProcess[str]:
    """Lance `python -m paquet.etape --in entree --out sortie`.

    Échoue avec le nom de l'étape manquante plutôt qu'une trace : c'est ce qui rend le rouge
    lisible tant que les étapes n'existent pas.
    """
    module = nom.replace("/", ".")
    try:
        present = importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        present = False
    if not present:
        pytest.fail(f"l'étape `{nom}` n'existe pas encore", pytrace=False)
    sortie.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, "-m", module, "--in", str(entree), "--out", str(sortie), *args],
        cwd=RACINE, capture_output=True, text=True,
    )
    if attendu is not None and proc.returncode != attendu:
        pytest.fail(f"`{nom}` a rendu {proc.returncode}, attendu {attendu}\n{proc.stderr}", pytrace=False)
    return proc


def copie_trace(destination: Path) -> Path:
    shutil.copytree(FIXTURES / "trace", destination)
    return destination


def lire_json(chemin: Path):
    return json.loads(chemin.read_text(encoding="utf-8"))


def ecrire_json(chemin: Path, valeur) -> None:
    chemin.write_text(json.dumps(valeur, ensure_ascii=False, indent=1), encoding="utf-8")


def _variable(nom: str) -> str:
    valeur = os.environ.get(nom)
    if not valeur:
        pytest.fail(f"{nom} n'est pas définie : ce test exige une cible ou un environnement vivant, "
                    "et ne se saute jamais (tests/spec/README.md)", pytrace=False)
    return valeur


@pytest.fixture
def cible() -> dict[str, str]:
    """Une cible vivante. `REPLIKIT_TARGET` nomme `targets/<cible>/`, `REPLIKIT_TARGET_URL` son adresse."""
    nom, url = _variable("REPLIKIT_TARGET"), _variable("REPLIKIT_TARGET_URL")
    scenario = RACINE / "targets" / nom / "scenarios" / "connexion.py"
    if not scenario.exists():
        pytest.fail(f"aucun scénario de connexion sous targets/{nom}/scenarios/", pytrace=False)
    return {"nom": nom, "url": url, "scenario": str(scenario)}


@pytest.fixture
def environnement() -> dict[str, str]:
    """Un environnement du clone qui tourne. `REPLIKIT_ENV_URL` son adresse, `REPLIKIT_ENV_DSN` sa base."""
    return {"url": _variable("REPLIKIT_ENV_URL"), "dsn": _variable("REPLIKIT_ENV_DSN")}
