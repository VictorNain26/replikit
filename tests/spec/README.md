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

Tant qu'elles ne sont pas ratifiées, ces tests sont des propositions rouges, pas un contrat.
