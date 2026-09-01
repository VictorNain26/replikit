# Spécification exécutable

Ces tests **sont** les exigences du lot en cours. Ils ne testent pas une implémentation :
ils décrivent ce qu'elle devra faire, par ses fichiers, et ils sont rouges jusqu'à ce
qu'elle le fasse.

## Ce que ces tests observent

Une étape s'invoque `python -m paquet.etape --in <dir> --out <dir>` (`docs/architecture.md`
§4) ; les tests lisent ce qu'elle écrit. Aucun test n'importe une fonction de production :
les agents restructurent le code librement, la spec mord toujours.

Chaque test nomme sa **casse** dans sa docstring — le changement de code qui le ferait
échouer. Un test qui n'en a pas est un détecteur de changement, pas une exigence.

## Trois familles, trois rouges

- **Contrat et structure** (`test_contrat.py`) — greps et `--help`. Sans entrée, toujours
  en intégration continue.
- **Fixtures** (`test_inference.py`, `test_oracle.py`) — une trace écrite à la main sous
  `fixtures/trace/`, mutée dans le test sur une seule famille à la fois. Ce que
  l'inférence et l'oracle doivent y voir est connu d'avance ; c'est ce qui rend les
  assertions falsifiables. Toujours en intégration continue, cible éteinte.
- **Cible ou environnement vivant** (`test_capture.py`, `test_generation.py`,
  `test_execution.py`) — marqueurs `cible` et `environnement`, variables
  `REPLIKIT_TARGET`, `REPLIKIT_TARGET_URL`, `REPLIKIT_ENV_URL`, `REPLIKIT_ENV_DSN`. Sans
  elles, le test **échoue** avec le nom de la variable ; il ne se saute jamais. L'intégration
  continue les écarte visiblement, par `-m "not cible and not environnement"`.

## La règle de gel

**Un commit ne peut pas toucher à la fois `tests/spec/` et un des sept paquets.** Le hook
`.githooks/pre-commit` le refuse. `tools/check_spec_frozen.py` compare chaque fichier —
fixtures comprises — à son empreinte dans `MANIFEST`. Une fixture est de la spec : la
changer est un commit isolé avec sa démonstration.

**Quand une correction est légitime** : quand le test échouait, ou passait, pour la
mauvaise raison — pas quand le code n'y arrivait pas. La démonstration est reproductible,
sur un arbre factice dans un répertoire temporaire, et le commit la porte.

**Avant de geler un test, le voir échouer et lire le message.** Un test qui passe pour la
mauvaise raison est le pire, et une fois gelé il est invisible.

## Ce que ces tests fixent, et qui est à ratifier dans `docs/architecture.md`

1. **La forme d'une trace sur disque** : `reseau.har`, `trace.zip`, `ecrans/*.yaml`,
   `etat.json`, `evenements.jsonl`, `index.json` avec `version_cible`. D1 dit que la trace
   est ce que Playwright produit ; `etat.json` et `evenements.jsonl` sont ce que
   `observe/record` y ajoute par les lectures du scénario et les trames WebSocket.
2. **Les sorties de l'oracle** : `ecarts.json` avec `ecarts[].famille`, `chemin`,
   `reproduction.scenario` ; `releve_aa.json` avec `identifiants`, `horodatages`, `ordre`,
   `champs_variables` ; `politique.json` compilée ; `fautes.json` avec `famille`, `origine`
   (`initial` ou `ver07`), `chemin`.
3. **Le nom des chemins dans la politique et le relevé** : `reponse.headers.date`,
   `reponse.body.user.created_at`. La convention est la même des deux côtés ; le reste est
   à l'étape.
4. **Le lieu du jeu de fautes** : `judge/faults/`, refusé à l'agent par
   `Read(./judge/faults/**)` dans `.claude/settings.json`.

Tant qu'elles ne sont pas ratifiées, ces tests sont des propositions rouges, pas un contrat.

## Ce qui n'est pas encore couvert

Les lots 2 à 5 ajouteront leurs tests **quand ils s'ouvrent**, un par exigence, vus
échouer avant gel. Écrire aujourd'hui les tests du lot 5 produirait des signatures
inventées.
