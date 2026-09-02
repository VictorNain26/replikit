# Chaque lot de docs/plan.md nomme sa commande. Elle sort en erreur tant que les artefacts
# que son critère de sortie exige n'existent pas — jamais par un `exit 1` écrit d'avance.

PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
CIBLE ?= mattermost
RAPPORTS := targets/$(CIBLE)/rapports

.PHONY: check spec lot1 lot2 lot3 lot4 lot5

## Cohérence des quatre documents, preuve que la vérification n'est pas vide, gel de la spec.
check:
	$(PY) tools/check_plan_coverage.py
	$(PY) tools/check_plan_coverage.py --self-test
	$(PY) tools/check_spec_frozen.py

## La spécification exécutable, tous lots. Rouge tant que les étapes n'existent pas.
spec:
	$(PY) -m pytest tests/spec -q

## Lot 1 : la spec du lot, puis les trois chiffres publiés ensemble ou pas du tout.
lot1: check
	$(PY) -m pytest tests/spec/lot1 -q
	@for f in ecarts.json taux.json iterations.json jetons.json decisions.json; do \
	  test -s $(RAPPORTS)/lot1/$$f || { echo "lot 1 : $(RAPPORTS)/lot1/$$f absent — voir docs/plan.md lot 1"; exit 1; }; \
	done
	@$(PY) -c "import json;r='$(RAPPORTS)/lot1/';e=json.load(open(r+'ecarts.json'));t=json.load(open(r+'taux.json'));i=json.load(open(r+'iterations.json'));print('écarts :',len(e['ecarts']),'| taux de détection :',t['taux'],'| itérations :',i['iterations'])"

lot2: lot1
	$(PY) -m pytest tests/spec/lot2 -q
	@echo "lot 2 : critère de sortie non outillé — voir docs/plan.md."; exit 1

lot3: lot2
	$(PY) -m pytest tests/spec/lot3 -q
	@echo "lot 3 : critère de sortie non outillé — voir docs/plan.md."; exit 1

lot4: lot3
	$(PY) -m pytest tests/spec/lot4 -q
	@echo "lot 4 : critère de sortie non outillé — voir docs/plan.md."; exit 1

lot5: lot4
	@echo "lot 5 : critère de sortie non outillé — voir docs/plan.md."; exit 1
