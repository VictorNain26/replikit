# Chaque lot de docs/plan.md nomme sa commande. Tant qu'elle sort en erreur, le lot n'est
# pas tenu — c'est ce qui rend « critère falsifiable » vérifiable plutôt qu'affirmé.

PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: check spec lot1 lot2 lot3 lot4 lot5 lot6

## Cohérence des quatre documents, et preuve que la vérification n'est pas vide.
check:
	$(PY) tools/check_plan_coverage.py
	$(PY) tools/check_plan_coverage.py --self-test
	$(PY) tools/check_spec_frozen.py

## La spécification exécutable. Rouge tant que les blocs n'existent pas.
spec:
	$(PY) -m pytest tests/spec -q

lot1: check spec
	@echo
	@echo "Le lot 1 exige trois chiffres publiés ensemble ou pas du tout :"
	@echo "  1. la liste d'écarts cible<->clone, chaque écart portant sa trace"
	@echo "  2. le taux de détection sur le jeu de fautes initial (VER-11)"
	@echo "  3. le nombre d'itérations de réparation avant convergence"
	@echo "Aucun n'est produit. Voir docs/plan.md lot 1."
	@exit 1

lot2 lot3 lot4 lot5 lot6:
	@echo "$@ : critère de sortie non outillé — voir docs/plan.md."
	@exit 1
