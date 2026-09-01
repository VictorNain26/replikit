# Spécification exécutable

Ces tests **sont** les exigences. Ils ne testent pas une implémentation : ils décrivent ce
qu'elle devra faire, et ils sont rouges jusqu'à ce qu'elle le fasse.

## Ce que ce répertoire n'est pas

Ce ne sont pas des tests unitaires. Les tests unitaires d'un bloc vivent à côté de lui, ils
sont jetables, et ils suivent la conception. Ceux-ci ne suivent rien : ils précèdent.

## La règle de gel

**Un commit ne peut pas toucher à la fois `tests/spec/` et un des sept paquets.** Le hook
`.githooks/pre-commit` le refuse. Ce n'est pas une interdiction de modifier la spec — c'est
l'impossibilité de la modifier *discrètement*, au milieu d'un commit qui prétend corriger
autre chose.

`tools/check_spec_frozen.py` complète le dispositif : il compare chaque fichier à son
empreinte dans `MANIFEST` et sort en erreur si l'une a bougé. Mettre le manifeste à jour est
donc un geste explicite, isolé, et visible dans l'historique.

## Quand une correction de spec est légitime

Une seule condition, et elle est exigeante : **démontrer que le test échouait pour la
mauvaise raison.** Pas que le code n'y arrivait pas — que le test se trompait sur ce qu'il
vérifiait. Le commit qui corrige la spec porte cette démonstration dans son message.

C'est la frontière exacte entre corriger une erreur et affaiblir un critère, et c'est ce qui
empêche la règle 1 de `CLAUDE.md` de se transformer en « on ne corrige jamais une erreur ».

## Décisions que ces tests tranchent, et qui doivent être ratifiées

Écrire un test force à décider ce que la prose laissait ouvert. Ces trois-là attendent leur
inscription dans `docs/architecture.md` :

1. **Le contrat d'artefact** — un module `artefacts` expose `put()` et `get()`, l'identifiant
   est le SHA-256 du contenu canonique. `docs/architecture.md` P1 pose l'invariant sans le
   spécifier.
2. **La forme d'une trace** — un répertoire d'artefacts portant le HAR, la liaison de
   variables de D1, les instantanés ARIA et les captures. P2 nomme le HAR, D1 nomme les
   variables, `VER-10` nomme l'ARIA, rien ne dit comment ils tiennent ensemble.
3. **`scope.yaml`** — le dénominateur de `VER-05` et la condition d'`ACC-01`/`ACC-02`. Cité
   six fois, jamais décrit.
4. **La forme physique d'un bloc** — un bloc est le module `paquet/bloc.py`, et P1 se lit
   strictement : aucun module des sept paquets n'importe un module des sept paquets, le sien
   compris. Le code commun vit hors des paquets, comme `artefacts`. Une version antérieure de
   `test_aucun_bloc_n_importe_un_autre_bloc` ne regardait que les imports *entre* paquets et
   passait sur `observe/normalise` important `observe/drive`.
5. **Le format de la politique et du relevé A/A** — `equivalence.yaml` porte des
   `neutralisations` citant chacune un `run_aa` ; le relevé A/A est un JSON à
   `champs_variables`. Ni l'un ni l'autre ne distingue encore ce que D1 **lie** de ce que D2
   **neutralise** ; `docs/architecture.md` D2 dit désormais lequel décide de quoi.
6. **Le lieu du jeu de fautes** — `test_le_jeu_de_fautes_n_est_pas_accessible_au_generateur`
   ne vérifie qu'une absence d'import. `docs/architecture.md` §10.8 dit pourquoi ça ne
   suffit pas ; le test suivra la décision.

Tant qu'elles ne sont pas ratifiées, ces tests sont des propositions rouges, pas un contrat.

## Ce que ces tests n'ont pas encore : des entrées

Les tests de `test_lot1_*.py` passent à chaque bloc des chemins qui n'existent pas —
`tmp_path / "connexion.yaml"` n'est jamais écrit, `tmp_path / "trace"` n'est jamais rempli.
Tels quels, ils ne peuvent être satisfaits que par un bloc qui **fabrique une sortie sans
lire son entrée**, ce qui est le comportement qu'ils existent pour interdire. Et plusieurs
n'observent qu'une auto-déclaration — `clone.contraintes_en_base`, `resultat.familles` — là
où l'exigence parle d'un comportement : `GEN-02` dit « effectivement appliquées par la
base », donc le test doit insérer une ligne interdite et voir la base la refuser.

La correction demande une décision, pas une retouche : d'où viennent les entrées de la spec.

- Les blocs qui lisent une trace (`infer/`, `build/`, `judge/`) consommeront une **trace
  figée sous `tests/spec/fixtures/`**, enregistrée sur la cible une fois `observe/drive` et
  `observe/normalise` livrés, puis gelée dans `MANIFEST` par un commit isolé.
- Les blocs qui touchent la cible (`observe/drive`) exigent une cible vivante, désignée par
  une variable d'environnement, et **échouent explicitement** en son absence — jamais
  `skip`, qui rendrait vert ce qui n'a pas tourné.

Jusqu'à cette décision, ces tests sont rouges pour une raison lisible mais **pas pour la
bonne** : « le bloc n'existe pas » masque « le test n'a pas d'entrée ».
