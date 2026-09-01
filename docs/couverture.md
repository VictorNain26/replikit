# Couverture du cahier des charges

Ce document porte **le compte**, et il est le seul à le porter. Un chiffre de couverture
recopié ailleurs se périme sans que personne le voie. Il définit l'espace de noms des
statuts : aucun autre document ne chiffre une couverture, il ne peut que citer celle-ci.
Les numéros de section sont des ancres — on ne renumérote jamais.

Statuts : **✅** couvert · **🟡** partiel · **❌** absent · **❔** non mesuré

## 1. replikit

**0 exigence sur 91.** Ce dépôt ne contient que de la documentation et le vérificateur qui
la recompte. C'est l'état honnête d'un projet qui commence, et le lot 1 de `docs/plan.md`
est ce qui produira ses trois premiers chiffres : la liste d'écarts, le taux de détection de
l'oracle, et le nombre d'itérations de réparation avant convergence.

| Section | ✅ | 🟡 | ❌ | Total | Premier lot qui la touche |
|---|---|---|---|---|---|
| 4. Capture (CAP) | 0 | 0 | 11 | 11 | lot 1 |
| 5. Inférence (INF) | 0 | 0 | 8 | 8 | lot 1 |
| 6. Génération (GEN) | 0 | 0 | 12 | 12 | lot 1 |
| 7. Exécution (RUN) | 0 | 0 | 14 | 14 | lot 5 |
| 8. Tool use (API) | 0 | 0 | 10 | 10 | lot 5 |
| 9. Vérification (VER) | 0 | 0 | 11 | 11 | lot 1 |
| 10. Orchestration LLM | 0 | 0 | 6 | 6 | lot 1 |
| 11. Non fonctionnel (NF) | 0 | 0 | 8 | 8 | lot 2 |
| 12. Acceptation (ACC) | 0 | 0 | 11 | 11 | lot 6 |
| **Total** | **0** | **0** | **91** | **91** | |

Ce tableau se remplira lot par lot. Une exigence n'y passera pas à ✅ sur une lecture de
code : il faudra une exécution, et le critère de sortie de son lot. `docs/plan.md` §5 dit
quel lot porte quoi ; cette colonne ne fait que le refléter et ne l'établit pas.

## 2. Ce que ce document ne contient pas

Aucun relevé d'un autre dépôt. Une version antérieure de ce document mesurait une
implémentation tierce contre ces mêmes exigences, pour établir ce qui était difficile et
où se trouvaient les pièges. Ce relevé a fait son office : les leçons qu'il portait sont
devenues des décisions dans `docs/architecture.md` et des critères de sortie dans
`docs/plan.md`, où elles se défendent seules. Le tenir plus longtemps aurait fait de ce
document le compte d'un autre projet.

**Ce qui reste vrai, et qui n'a besoin d'aucun précédent pour l'être** :

1. **Comparer une cible à elle-même est le cas facile.** Le run A/A mesure le bruit ; il ne
   dit rien de la fidélité d'un clone. C'est pourquoi le lot 1 va jusqu'au clone.
2. **Un compte d'écarts sans taux de détection ne vaut rien** (D4), y compris celui qu'on
   produira. C'est `VER-11`, et c'est pourquoi le lot 1 publie trois chiffres ou aucun.
3. **Un critère de sortie qui n'a pas été exécuté n'est pas un critère de sortie.** Une
   exigence tenue pour acquise sur une lecture de code est une exigence non mesurée. C'est
   pourquoi chaque lot de `docs/plan.md` s'arrête sur une commande et un code de sortie.
