# Spécification exécutable

Ces tests **sont** les exigences, un répertoire par lot. Ils ne testent pas une
implémentation : ils décrivent ce qu'elle devra faire, par ses fichiers, et ils sont
rouges jusqu'à ce qu'elle le fasse.

## Ce que ces tests observent

Une étape s'invoque `python -m paquet.etape --in <dir> --out <dir>` (`docs/architecture.md`
§4) ; les tests lisent ce qu'elle écrit. Aucun test n'importe une fonction de production —
la présence d'une étape se constate par son fichier, jamais par un import. Les agents
restructurent le code librement, la spec mord toujours.

Chaque test nomme sa **casse** dans sa docstring — le changement de code qui le ferait
échouer. Un test qui n'en a pas est un détecteur de changement, pas une exigence.

## Un répertoire par lot

`lot1/` porte les exigences du lot 1 de `docs/plan.md`, `lot2/` celles du lot 2, et ainsi
de suite. `make lotN` lance les répertoires 1 à N ; `make spec` lance tout. Un test du
lot 2 qui échoue n'empêche pas le lot 1 de sortir, et le lot 1 n'exige que ses propres
étapes — `test_contrat.py` lit le tableau §6 du plan jusqu'à son lot. Les lots suivants
ajoutent leurs tests **quand ils s'ouvrent**, un par exigence, vus échouer avant gel ;
`lot3/` et `lot4/` ne contiennent aujourd'hui que ce que le lot 1 a dû en écarter.

## Trois familles, trois rouges

- **Contrat et structure** (`lot1/test_contrat.py`) — greps et `--help`. Sans entrée,
  toujours en intégration continue.
- **Fixtures** (`lot1/test_inference.py`, `lot1/test_oracle.py`, `lot2/`) — une trace écrite
  à la main sous `fixtures/trace/`, mutée dans le test sur une seule famille à la fois. Ce
  que l'inférence et l'oracle doivent y voir est connu d'avance ; c'est ce qui rend les
  assertions falsifiables. L'inférence la reçoit **sans `etat.json`** : c'est le cas S2, où
  seul le trafic est visible. Toujours en intégration continue, cible éteinte.
- **Cible ou environnement vivant** (`lot1/test_capture.py`, `lot1/test_generation.py`,
  `lot1/test_execution.py`, `lot3/`, `lot4/`) — marqueurs `cible` et `environnement`,
  variables `REPLIKIT_TARGET`, `REPLIKIT_TARGET_URL`, `REPLIKIT_ENV_URL`, `REPLIKIT_ENV_DSN`.
  Sans elles, le test **échoue** avec le nom de la variable ; il ne se saute jamais.
  L'intégration continue les écarte visiblement, par `-m "not cible and not environnement"`.

## La règle de gel

**Un commit ne peut pas toucher à la fois `tests/spec/` et du code** — les sept paquets,
`commun/`, `targets/`. Le hook `.githooks/pre-commit` le refuse. `tools/check_spec_frozen.py`
compare chaque fichier — fixtures comprises — à son empreinte dans `MANIFEST`. Une fixture
est de la spec : la changer est un commit isolé avec sa démonstration.

**Quand une correction est légitime** : quand le test échouait, ou passait, pour la
mauvaise raison — pas quand le code n'y arrivait pas. La démonstration est reproductible,
sur un arbre factice dans un répertoire temporaire, et le commit la porte.

**Avant de geler un test, le voir échouer et lire le message.** Un test qui passe pour la
mauvaise raison est le pire, et une fois gelé il est invisible.

## Ce que ces tests fixent, au-delà de `docs/architecture.md`

1. **La forme d'une trace sur disque** : `reseau.har`, `ecrans/*.yaml`, `etat.json`,
   `evenements.jsonl`, `index.json` avec `version_cible`, et `trace.zip` en capture vivante —
   absent des fixtures, qui sont écrites à la main. `etat.json` et `evenements.jsonl` sont ce
   que `observe/record` ajoute à ce que Playwright produit (D1), par les lectures du
   scénario et les trames WebSocket. Les cinq familles du différentiel et leur partage de
   la trace sont écrits en §4 de l'architecture.
2. **Les sorties de l'oracle** : `ecarts.json` avec `ecarts[].famille`, `chemin`,
   `reproduction.scenario` ; `releve_aa.json` avec `identifiants`, `horodatages`, `ordre`,
   `champs_variables` ; `politique.json` compilée ; `fautes.json` avec `famille`, `origine`
   (`initial` ou `ver07`), `chemin` ; `arret.json` avec `motif`.
3. **Le nom des chemins dans la politique et le relevé** : `reponse.headers.date`,
   `reponse.body.user.created_at`. La convention est la même des deux côtés ; le reste est
   à l'étape.
4. **Le nom des entités inférées** : la collection du chemin — `/api/users/me` donne
   `users`, `/api/teams` donne `teams`. C'est une heuristique, et elle est la seule que la
   spec impose à l'inférence.
5. **L'état de départ nommé** `depart` (RUN-01), et un environnement dont l'état de départ
   contient au moins une ligne par table à clé étrangère (GEN-02).

Ces conventions valent tant qu'un lot ne les contredit pas ; les contredire est une
correction de spec, avec sa démonstration.
