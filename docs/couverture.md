# Couverture du cahier des charges

Ce document porte **le compte**, et il est le seul à le porter. Il définit l'espace de noms
des statuts et des seuils mesurés : aucun autre document ne chiffre une couverture ni ne
fixe un seuil, il ne peut que citer celui-ci. Les numéros de section sont des ancres — on
ne renumérote jamais.

Statuts : **✅** tenu par une exécution · **🟡** partiel · **❌** absent

## 1. replikit

**0 exigence sur 73.** Ce dépôt ne contient que de la documentation, une spécification
exécutable rouge et le vérificateur qui recompte les documents. Le lot 1 de `docs/plan.md`
produira les trois premiers chiffres : la liste d'écarts, le taux de détection de l'oracle,
le nombre d'itérations de réparation avant convergence.

| Section | ✅ | 🟡 | ❌ | Total | Premier lot |
|---|---|---|---|---|---|
| 6. Capture (CAP) | 0 | 0 | 10 | 10 | lot 1 |
| 7. Inférence (INF) | 0 | 0 | 7 | 7 | lot 1 |
| 8. Génération (GEN) | 0 | 0 | 11 | 11 | lot 1 |
| 9. Exécution (RUN) | 0 | 0 | 9 | 9 | lot 1 |
| 10. Tool use (API) | 0 | 0 | 6 | 6 | lot 4 |
| 11. Vérification (VER) | 0 | 0 | 11 | 11 | lot 1 |
| 12. Orchestration (LLM) | 0 | 0 | 6 | 6 | lot 1 |
| 13. Outillage (OUT) | 0 | 0 | 3 | 3 | lot 2 |
| 14. Acceptation (ACC) | 0 | 0 | 10 | 10 | lot 2 |
| **Total** | **0** | **0** | **73** | **73** | |

Une exigence ne passe à ✅ que sur une exécution et le critère de sortie de son lot, jamais
sur une lecture de code. La colonne *Premier lot* reflète `docs/plan.md` §6 et ne
l'établit pas.

## 2. Seuils fixés après première mesure

Le cahier n'invente aucun seuil (§5). Chaque seuil naît ici, avec la mesure qui le fonde,
et n'est jamais abaissé ensuite.

| Exigence | Première mesure | Date, cible | Seuil retenu |
|---|---|---|---|
| — | aucune encore | | |

## 3. Mesures d'OUT-01, par cible

| Cible | Heures de calendrier | Jetons | Décisions bloquantes | Itérations de réparation |
|---|---|---|---|---|
| — | | | | |

## 4. Ce que ce document ne contient pas

Aucun relevé d'un autre dépôt, aucune estimation. Une version antérieure de ce dépôt
comptait 91 exigences ; elle est étiquetée `docs-v0` dans l'historique, et
`docs/cahier-des-charges.md` §15 dit ce qui en a été retiré et pourquoi.
