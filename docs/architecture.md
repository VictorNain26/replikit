# Architecture

Comment les 73 exigences de `docs/cahier-des-charges.md` sont portées, chacune par un outil
maintenu ou un standard lu à la source, et par du code maison seulement là où le substitut
cherché est nommé et manque.

Ce document porte le **comment** : limites, principes, décisions, étapes, outils, ce qui
reste maison, ce qui n'est pas résolu, ce qui a été écarté, et le statut de vérification de
chaque référence. Le **quoi** est dans `docs/cahier-des-charges.md`, le **quand** dans
`docs/plan.md`, l'**état mesuré** dans `docs/couverture.md`.

Il définit l'espace de noms `Pn`, `Dn` et les noms d'étapes `paquet/etape` : aucun autre
document ne crée ni ne reformule un principe, une décision ou une étape, il ne peut que
les citer. Les numéros de section sont des ancres — on ne renumérote jamais.

## 1. Limites

Trois limites qu'aucune méthode ne franchit ; les écrire évite de promettre.

**L'oracle est négatif.** Une divergence est un candidat défaut ; l'accord ne prouve rien
(McKeeman 1998, non vérifié, §9). Le clone étant dérivé de l'observation de la cible,
l'oracle est aveugle exactement là où le clone est le plus faux : hors de l'observé.

**L'équivalence est échantillonnée.** « Zéro écart » signifie « aucun écart sur ce qui a
été sondé ». C'est pourquoi le cahier exige un taux de détection à côté de chaque compte
(VER-08) et une mesure directe d'indiscernabilité (VER-10) : la première borne ce que
l'oracle rate, la seconde borne ce que le compte ne dit pas.

**La couverture est circulaire.** Le dénominateur est inféré des traces : « 100 % » veut
dire « 100 % de l'observé ». Böhme et al. (FSE 2021, vérifié, §9) montrent que les
estimateurs de risque résiduel conçus pour le boîte-noire, appliqués à une campagne
adaptative, « *systematically and substantially under-estimate the true risk* ». Le
périmètre déclaré est une décision datée, pas une propriété.

## 2. Principes

**P1 — Un seul objet circule : l'artefact sur disque, adressé par son contenu.** Chaque
étape lit des artefacts et en écrit. Aucune étape n'en appelle une autre : `make` les
enchaîne. Le cache, la reprise, la campagne hors ligne (OUT-02) et la reproductibilité
(RUN-03) en découlent.

**P2 — Les formats entre étapes sont ceux du marché.** HAR et trace Playwright pour
l'observation, OpenAPI pour la surface, JSON Schema pour les entités, AsyncAPI pour les
canaux, YAML d'instantané d'accessibilité pour les écrans, OpenTelemetry pour les appels de
modèle. Un format maison est une étape qu'on ne peut plus remplacer.

**P3 — Un modèle propose, le code prononce.** Aucun import de client de modèle sous
`judge/`. Vérifiable par `grep`, vérifié par `tests/spec/`.

**P4 — Aucun privilège sur la cible ne porte un verdict.** Ce qu'une cible tierce ne
donne pas — sa base, son reset, son code — sert à étalonner l'oracle, jamais à juger. Le
code source alimente l'inférence (CAP-08), pas le juge. Les privilèges sur le **clone**
nous appartiennent (RUN-01, RUN-05).

**P5 — Rien sous les sept paquets ne connaît une cible.** Tout ce qui est propre à une
cible vit sous `targets/<cible>/` : scénarios, `scope.yaml`, `equivalence.yaml`,
composition, clone généré. Une condition sur un nom de cible dans une étape est le défaut
que GEN-11 mesure.

## 3. Décisions

Chacune nomme l'outil qui la porte, la source lue, et ce qu'elle coûte.

### D1 — Playwright est l'enregistreur ; il n'y a pas de format de trace maison

Une trace est ce que Playwright produit : `context.tracing.start(screenshots=True,
snapshots=True)` capture « *DOM snapshot on every action* » et « *network activity* »,
`tracing.start_har()` — « *Added in: v1.60* » — écrit le HAR à côté, et
`page.route_web_socket()` (1.48) observe les trames. Les instantanés d'accessibilité
viennent de `aria_snapshot(boxes=True)` (1.60). Tout est vérifié, §9.

*Ce que ça coûte* : le HAR n'est pas un standard — le brouillon W3C « *has been
abandoned* » — mais c'est le format que Playwright, mitmproxy2swagger et Chrome
partagent. `observe/record` n'écrit rien de plus qu'un index qui range ces fichiers dans
le dépôt d'artefacts.

### D2 — Le scénario est un script Playwright sur localisateurs de rôle, et un clone fidèle le rejoue tel quel

`playwright codegen` génère des scripts « *prioritizing role, text and test id locators* ».
Un localisateur de rôle s'adresse à l'arbre d'accessibilité, et VER-09 exige du clone le
même arbre. Donc un scénario enregistré sur la cible pilote le clone sans traduction, et un
localisateur qui échoue sur le clone **est un écart d'écran**, pas une panne de rejeu.

*Fondement* : Hammoudi, Rothermel & Tonella (ICST 2016, vérifié, §9) : 73,62 % des
1 065 ruptures de rejeu relevées sur 453 versions viennent de localisateurs obsolètes. Le
localisateur de rôle est celui qui casse quand l'écran change de sens, pas quand il change
de forme.

*Ce que ça coûte* : aucun modèle dans la boucle de rejeu, ce qui est ce que P3 voulait.
Stagehand est écarté (§8). La cible peut avoir des écrans sans rôles ARIA corrects ; le
script tombe alors sur le texte, et c'est une dette de capture visible.

### D3 — Lier d'abord, neutraliser ensuite, et seulement sur relevé

Chaque valeur produite par le système — identifiant, horodatage — est liée à une variable
à sa première apparition ; toute réapparition doit référencer la même variable. C'est une
vérification de cohérence référentielle, plus forte qu'ignorer le champ : un clone qui rend
deux identifiants pour un même objet échoue.

Ce qui varie entre deux rejeux sans jamais réapparaître — un en-tête `Date`, une latence,
un ordre non garanti — est neutralisé, et seulement si le relevé A/A de CAP-02 le montre.
La politique (`targets/<cible>/equivalence.yaml`) est un fichier déclaratif dont chaque
entrée cite ce relevé ; `judge/policy` refuse une entrée absente du relevé et compile le
reste en `exclude_regex_paths` et `ignore_order` de DeepDiff (vérifié, §9).

*Fondement* : le plancher de bruit de Diffy — comparer un système à lui-même pour rendre
interprétable sa comparaison à un candidat. Le code est écarté (§8), l'idée reste.

*Ce que ça coûte* : le lieur est maison (§6). Aucun outil de cassette ne le fait.

### D4 — L'oracle est validé par fautes semées sur le corpus figé, et le jeu de fautes est hors du chemin de l'agent

`judge/mutate` applique des opérateurs de mutation aux traces figées — valeur changée,
champ retiré, ordre inversé, message d'erreur altéré — et `judge/diff` doit les voir. Le
taux est publié avec chaque compte d'écarts (VER-08). Jahangirova et al. (ISSTA 2016,
vérifié, §9) : « *mutation testing to reveal false negatives* » d'un oracle.

Le jeu initial est semé avant que l'agent n'écrive une ligne, et il vit sous
`judge/faults/`, chemin refusé en lecture à l'agent de code par une règle
`Read(./judge/faults/**)` de ses permissions (vérifié, §9) — avec la réserve documentée
que la règle ne s'applique pas aux sous-processus, donc l'agent ne reçoit pas non plus de
droit d'exécution sur ce chemin. Les fautes que VER-07 ajoute viennent d'écarts que
l'agent a reçus en retour : pour celles-là le secret est levé par construction, et le taux
publié distingue les deux sous-ensembles.

*Sur quoi porte la faute* : la trace figée, jamais la cible (P4).

### D5 — L'écran se compare par structure d'accessibilité, jamais par pixel

`aria_snapshot(boxes=True)` rend l'arbre en YAML avec `[box=x,y,width,height]` par nœud ;
`expect(locator).to_match_aria_snapshot()` compare à un gabarit produit depuis la cible.
La géométrie est ramenée aux voisins immédiats — les `box` sont absolus — et c'est la
seule partie maison. X-PERT (ICSE 2013, vérifié, §9) : 76 % de précision et 95 % de rappel
avec une comparaison de dispositions relatives, et les incompatibilités de structure
dominent.

`ariaSnapshotJSON`, qui rendrait l'arbre en JSON, est documenté « *Added in: v1.63* », en
JavaScript seulement : `judge/screen` analyse le YAML jusqu'à ce que l'API Python le rende.

*Ce que ça coûte* : on renonce aux régressions purement visuelles. Pour un agent qui lit
la structure, c'est le bon arbitrage.

### D6 — Un modèle propose, le code juge, et la boucle vaut ce que vaut le juge

Kambhampati et al. (ICML 2024, vérifié, §9) : « *auto-regressive LLMs cannot, by
themselves, do planning or self-verification* » ; la solidité vient des « *external sound
critics* ». Olausson et al. (ICLR 2024, vérifié) : gains « *often modest […] sometimes not
present at all* » quand le modèle produit son propre retour, « *substantially larger* »
quand le retour est de meilleure qualité. TOGLL (vérifié) : 7 % de faux positifs sur les
oracles d'exception, 25 % sur les oracles d'assertion, et c'est l'état de l'art des oracles
générés.

*Corollaire* : le clone est écrit par un agent de code, jugé par `judge/diff`. La liste
d'écarts **est** le retour de réparation (LLM-01), et son rendement est une fonction du
juge, pas du modèle.

### D7 — Le clone est généré sur une pile fixe, déterministe par construction

L'agent de code n'invente pas de pile : l'API est FastAPI 0.141, dont `/openapi.json`
commence par `"openapi": "3.1.0"` (vérifié, §9) — le clone publie donc du 3.1 même si la
surface inférée est du 3.0 (§7.2) —, la persistance SQLAlchemy 2.0 + Alembic 1.19 +
PostgreSQL, les erreurs au format RFC 9457 (*Standards Track*, remplace 7807, vérifié),
l'interface React + TypeScript comme l'offre le suggère. `FastMCP.from_fastapi()` (vérifié, v4.0.0) expose les mêmes opérations
en MCP : API-03 est une ligne, pas un bloc.

L'horloge, l'aléa et les identifiants sont des fournisseurs injectés, pilotés par la
surface d'administration RUN-05. C'est ce qui remplace `libfaketime` : on n'intercepte pas
`getrandom()` dans un binaire qu'on a écrit soi-même. Côté navigateur, `page.clock` de
Playwright (« *Added in: v1.45* », vérifié) fige `Date` dans l'agent qui rejoue.

*Ce que ça coûte* : un clone en deux langages. C'est le coût de « *React background is a
plus* » et de l'écosystème Python de vérification (§3.1).

### D8 — Un environnement est une composition Compose et une base modèle PostgreSQL

`targets/<cible>/compose.yaml` suit la Compose Specification (Apache-2.0, vérifiée), image
épinglée par *digest* — « `image: redis@sha256:…` » y est l'exemple documenté. Le réseau du
clone est interne (RUN-04) ; Mailpit, WireMock et mock-oauth2-server (vérifiés) sont les
doubles des effets de bord ; les fichiers vont sur un volume local.

La réinitialisation est `DROP DATABASE` puis `CREATE DATABASE … TEMPLATE etat_nomme`
(PostgreSQL 18, vérifié) : « *no other sessions can be connected to the template database
while it is being copied* », donc l'état de départ est une base que personne n'ouvre.
L'instantané à un instant quelconque est `pg_dump -Fc` (vérifié).

*Ce que ça coûte* : le nombre d'environnements simultanés et le coût marginal par
environnement (RUN-02, rang N) se mesurent, ils ne se déduisent pas. Firecracker, ZFS et
le partage de blocs sont écartés pour le démonstrateur (§8) ; ils reviendraient avec la
première mesure qui les exige.

### D9 — L'indiscernabilité se mesure avec un agent du marché

VER-10 : le même agent, la même tâche, sur cible et sur clone. L'agent est Playwright MCP
(Microsoft, 0.0.80, Apache-2.0, vérifié, §9) piloté par un modèle ; il « *interact[s] with
web pages through structured accessibility snapshots* », ce qui est exactement M1 vu par
un modèle. `judge/agent`
enregistre ses deux trajectoires — suite d'outils appelés, instantanés, résultat — et
`judge/diff` les compare sous la même politique qu'une trace. Le modèle est dans la mesure,
pas dans le verdict.

*Ce que ça coûte* : le seuil de VER-10 n'existe pas avant sa première valeur, et la mesure
est bruitée par le modèle lui-même. On la répète, on publie la distribution.

### 3.1 — Langage : Python pour la chaîne

La cartographie (§9) tranche : Schemathesis, mitmproxy2swagger, genson, DeepDiff, Crawlee,
Alembic, Testcontainers, MLflow sont Python, les quatre premiers sans équivalent TypeScript
maintenu trouvé. Tout ce qui n'est pas Python est en ligne de commande — k6, Prism, la CLI
AsyncAPI, Playwright MCP — et se pilote depuis `make`. Le clone, lui, suit D7.

## 4. Les étapes

Sept paquets, un par famille du cahier ; OUT est portée par `make` et l'intégration
continue, pas par un paquet. **Un nom d'étape est une commande, pas une promesse de
module** : les frontières de modules naissent du premier vertical, et une étape dont
l'outil fait tout le travail est un appel de sous-processus.

**Toute étape s'invoque de la même façon** : `python -m paquet.etape --in <répertoire>
--out <répertoire>`. Elle lit ses artefacts et ses paramètres dans `--in`, écrit ses
artefacts dans `--out`, et rien d'autre. C'est P1 pris au mot, et c'est le seul contrat que
`tests/spec/` fige : la spec observe des fichiers, jamais des fonctions.

```
observe/       cible          -> traces            (CAP)
infer/         traces         -> spécification     (INF)
build/         spécification  -> clone             (GEN)
run/           clone          -> environnements    (RUN)
serve/         clone          -> surface agent     (API)
judge/         cible x clone  -> écarts, mesures   (VER, ACC)   -- sans modèle
orchestrate/   la boucle                           (LLM)
targets/<t>/   le seul endroit propre à une cible
```

| Étape | Entrée → sortie | Outil | Maison |
|---|---|---|---|
| `observe/record` | scénario → HAR, `trace.zip`, instantanés ARIA, index | Playwright tracing, `start_har`, `aria_snapshot`, `route_web_socket` | index seul |
| `observe/explore` | URL de départ → inventaire d'écrans | Crawlee `PlaywrightCrawler` (1.10.0, Apache-2.0) | extraction des éléments interactifs |
| `observe/probe` | inventaire → sondes de formulaire et leurs réponses | scénarios Playwright générés depuis l'inventaire | générateur de sondes (§6) |
| `observe/aa` | scénario → deux traces, relevé des champs variables | `observe/record` deux fois, `judge/diff` | — |
| `observe/redact` | trace → trace expurgée, dictionnaire de liaison | detect-secrets en garde-fou (v1.5.0, hors ligne) | expurgation liante (§6) |
| `observe/ingest` | dépôt source → schéma, migrations, OpenAPI publiés | les artefacts du dépôt cible eux-mêmes | — |
| `infer/surface` | HAR → OpenAPI | mitmproxy2swagger 0.15.0 (HAR en entrée, OpenAPI 3.0 en sortie) | — |
| `infer/entities` | charges utiles → JSON Schema, relations, cardinalités | genson 1.4.0 | relations et cardinalités (§6) |
| `infer/states` | traces → machine à états par entité | comptage des transitions observées | format YAML validé par JSON Schema (§6) |
| `infer/provenance` | spécification → spécification annotée, dette *non observé* | `jsonschema` (Draft 2020-12) pour la validation | annotation (§6) |
| `infer/rank` | traces → périmètre hiérarchisé | comptage depuis le HAR | — |
| `build/generate` | spécification, écarts → clone | agent de code en ligne de commande, pile D7 | prompts et scaffolds versionnés |
| `build/seed` | distributions déclarées → données de départ | Faker 40.38 avec graine, version épinglée | — |
| `build/preserve` | clone régénéré → ajustements manuels conservés | fichiers `*.custom.*` jamais régénérés, test d'empreinte | ~20 lignes |
| `run/env` | composition → environnement | Compose Specification, images par digest | — |
| `run/reset` | environnement, état nommé → environnement réinitialisé | `CREATE DATABASE … TEMPLATE`, `pg_dump -Fc` | — |
| `run/admin` | — | routeur FastAPI sur un réseau que l'agent ne voit pas | dans le gabarit du clone |
| `run/journal` | session → journal exportable | intergiciel FastAPI + trace Playwright de l'agent | dans le gabarit du clone |
| `serve/mcp` | clone → serveur MCP | `FastMCP.from_fastapi()` 4.0.0 | — |
| `serve/parity` | tâche → états finaux par UI et par API, différence | `judge/replay` deux fois, `judge/diff` | — |
| `serve/load` | environnement à volumétrie GEN-08 → centiles | k6 2.2.0 (AGPL-3.0), `thresholds` | scripts k6 |
| `judge/replay` | scénario, environnement → trace du clone | Playwright, mêmes scripts que la capture (D2) | — |
| `judge/policy` | `equivalence.yaml`, relevé A/A → paramètres DeepDiff | — | compilateur, ~50 lignes (§6) |
| `judge/diff` | deux traces, paramètres → écarts par famille | DeepDiff 9.1.0 (`exclude_regex_paths`, `ignore_order`, `verbose_level=2`) | liaison D3 (§6) |
| `judge/screen` | deux instantanés ARIA → écarts de structure et de géométrie | `to_match_aria_snapshot`, gabarit depuis la cible | géométrie relative (§6) |
| `judge/edge` | OpenAPI → cas limites et verdicts | Schemathesis 4.25.2, mode négatif et *stateful* | — |
| `judge/adversary` | environnement, corpus → écarts hors corpus | Schemathesis *stateful* côté API ; Crawlee en marche aléatoire côté UI, sur cible et clone, comparés | stratégie de marche |
| `judge/coverage` | traces de campagne, `scope.yaml` → couverture | opérations et routes du HAR contre le périmètre | dénominateur (§6) |
| `judge/mutate` | corpus figé → fautes semées, taux de détection | — | opérateurs de mutation (§6) |
| `judge/leaks` | traces du clone → indices de simulation | — | liste d'indices (§6) |
| `judge/agent` | tâche, cible, clone → deux trajectoires, différence | Playwright MCP + modèle, `judge/diff` | enregistrement des trajectoires |
| `judge/report` | tout ce qui précède → rapport d'acceptation | — | mise en forme des dix critères |
| `orchestrate/loop` | spécification → clone convergé, itérations | `make` ; l'agent de `build/generate` ; `judge/diff` en retour | enchaînement |
| `orchestrate/trace` | appels de modèle → traces, coût, budget | MLflow Tracing 3.15.2 (Apache-2.0, compatible OpenTelemetry) | interruption au dépassement |
| `orchestrate/evalset` | écarts corrigés → jeu d'évaluation des scaffolds | — | sélection |

## 5. Couverture des 73 exigences

Une ligne par exigence. La colonne *Maison* dit ce qu'aucun outil ne fait ; « — » signifie
que l'outil fait tout.

### Capture (CAP)

| Réf | Étape | Outil | Maison |
|---|---|---|---|
| CAP-01 | `observe/record` | Playwright tracing + HAR + ARIA + WebSocket | index |
| CAP-02 | `observe/aa` | Playwright, DeepDiff | — |
| CAP-03 | `observe/explore` | Crawlee | extraction des interactifs |
| CAP-04 | `observe/probe` | Playwright | générateur de sondes |
| CAP-05 | `observe/record` | compteur sur `page.route`, détection 403/429/interstitiel | budget et détection |
| CAP-06 | `observe/redact` | detect-secrets | expurgation liante |
| CAP-07 | dépôt d'artefacts | répertoire adressé par SHA-256, version de cible dans l'index | ~30 lignes |
| CAP-08 | `observe/ingest` | artefacts du dépôt source | — |
| CAP-09 | `observe/record` | N contextes Playwright, horloge commune | — |
| CAP-10 | `observe/record` | `route_web_socket`, description AsyncAPI 3 générée | générateur AsyncAPI ; SSE sans liaison normée |

### Inférence (INF)

| Réf | Étape | Outil | Maison |
|---|---|---|---|
| INF-01 | `infer/surface` | mitmproxy2swagger | — |
| INF-02 | `infer/entities` | genson | relations, cardinalités |
| INF-03 | `infer/states` | — | comptage, format YAML |
| INF-04 | `infer/provenance` | jsonschema | annotation |
| INF-05 | format de spécification | OpenAPI + JSON Schema + AsyncAPI + YAML validé ; git | fusion avec amendements |
| INF-06 | `infer/provenance` | — | détection de règles incompatibles |
| INF-07 | `infer/rank` | comptage HAR | — |

### Génération (GEN)

| Réf | Étape | Outil | Maison |
|---|---|---|---|
| GEN-01 | `build/generate` | SQLAlchemy 2, Alembic, PostgreSQL (D7) | — |
| GEN-02 | `build/generate` | contraintes SQL ; vérifiées par insertion interdite via RUN-05 | — |
| GEN-03 | `build/generate` | agent ; jugé par `judge/diff` | — |
| GEN-04 | `build/generate` | React + TypeScript ; jugé par `judge/screen` | — |
| GEN-05 | `build/generate` | agent ; jugé par `judge/diff` par rôle | — |
| GEN-06 | `build/generate` | WebSocket FastAPI ; jugé sur les événements | — |
| GEN-07 | `build/generate` | agent ; jugé par `judge/diff` (ordre) | — |
| GEN-08 | `build/seed` | Faker avec graine | — |
| GEN-09 | `build/preserve` | test d'empreinte | ~20 lignes |
| GEN-10 | `build/migrate`, non livrée | SQLAlchemy, `judge/diff` | rang N, sans objet ici |
| GEN-11 | `targets/<t>/` | mesure : lignes sous `targets/` contre lignes sous les paquets | — |

### Exécution (RUN)

| Réf | Étape | Outil | Maison |
|---|---|---|---|
| RUN-01 | `run/reset` | PostgreSQL TEMPLATE, `pg_dump -Fc` | — |
| RUN-02 | `run/env` | une composition par environnement, bases séparées | mesure du nombre et du coût |
| RUN-03 | gabarit du clone (D7) | fournisseurs d'horloge, d'aléa, d'identifiants ; `page.clock` | dans le gabarit |
| RUN-04 | `run/env` | réseau Compose interne ; Mailpit, WireMock, mock-oauth2-server | — |
| RUN-05 | `run/admin` | routeur FastAPI sur réseau séparé | dans le gabarit |
| RUN-06 | `run/journal` | intergiciel + trace Playwright | dans le gabarit |
| RUN-07 | `run/env` | Compose Specification, digests | — |
| RUN-08 | `judge/replay` | un scénario Playwright rejoué comme second acteur | — |
| RUN-09 | `judge/leaks` | — | liste d'indices |

### Surface tool use (API)

| Réf | Étape | Outil | Maison |
|---|---|---|---|
| API-01 | `serve/parity` | OpenAPI du clone contre actions du HAR ; `judge/diff` | — |
| API-02 | gabarit du clone | l'interface consomme l'API du clone, une seule couche | — |
| API-03 | `serve/mcp` | FastMCP `from_fastapi` | — |
| API-04 | gabarit du clone | RFC 9457 | — |
| API-05 | gabarit du clone | client MCP avec délais bornés ; diagnostic par classe d'erreur | client |
| API-06 | `serve/load` | k6 | scripts |

### Vérification (VER)

| Réf | Étape | Outil | Maison |
|---|---|---|---|
| VER-01 | `judge/replay` + `judge/diff` | Playwright, DeepDiff | liaison D3 |
| VER-02 | `judge/policy` | — | compilateur |
| VER-03 | `judge/adversary` | Schemathesis *stateful*, Crawlee | stratégie |
| VER-04 | `judge/edge` | Schemathesis mode négatif | — |
| VER-05 | `judge/coverage` | HAR contre `scope.yaml` | dénominateur |
| VER-06 | `judge/report` | — | mise en forme |
| VER-07 | `judge/mutate` + corpus | — | opérateurs |
| VER-08 | `judge/mutate` | — | opérateurs, séparation initial / VER-07 |
| VER-09 | `judge/screen` | `to_match_aria_snapshot` | géométrie relative |
| VER-10 | `judge/agent` | Playwright MCP + modèle, DeepDiff | trajectoires |
| o VER-11 | `observe/aa` périodique | Playwright sous budget CAP-05 | extension, non livrée |

### Orchestration (LLM)

| Réf | Étape | Outil | Maison |
|---|---|---|---|
| LLM-01 | `orchestrate/loop` | `make`, agent de code, `judge/diff` | enchaînement |
| LLM-02 | frontières | pydantic, jsonschema | — |
| LLM-03 | `orchestrate/trace` | MLflow Tracing | — |
| LLM-04 | `orchestrate/trace` | jetons lus dans la trace | interruption |
| LLM-05 | `orchestrate/evalset` | git ; écarts corrigés comme cas | sélection |
| LLM-06 | `make -j` | — | — |

### Outillage (OUT)

| Réf | Porté par | Outil | Maison |
|---|---|---|---|
| OUT-01 | `make` | heures, jetons (MLflow), décisions consignées dans `docs/couverture.md` | — |
| OUT-02 | intégration continue | GitHub Actions, corpus figé, cible éteinte | — |
| OUT-03 | `targets/<t>/` | un répertoire par cible | rang N, vue non livrée |

### Acceptation (ACC)

Aucun critère n'est une étape : chacun est une sortie de `judge/report`.

| Réf | Produit par | Condition d'existence |
|---|---|---|
| ACC-01 | `judge/diff` + `judge/mutate` | `scope.yaml` arrêté avant la campagne |
| ACC-02 | `judge/coverage` | idem |
| ACC-03 | `serve/parity` | idem |
| ACC-04 | `judge/adversary` | critère d'arrêt déclaré avant lancement |
| ACC-05 | `run/reset` + `judge/diff` | nombre de cycles déclaré avant la campagne |
| ACC-06 | `infer/provenance` | — |
| ACC-07 | `judge/leaks` + `judge/agent` | — |
| ACC-08 | `build/seed` + `serve/load` | volumétrie du démonstrateur déclarée |
| ACC-09 | `observe/record` multi-contextes + `judge/diff` | cible collaborative |
| ACC-10 | humain | personne ne tient le rôle ; en échec, jamais retiré |

## 6. Ce qui reste maison, et le substitut cherché

- **Le lieur de variables (D3).** Cherché : Keploy détecte les champs bruités mais
  s'installe sur l'hôte de l'application (`sudo -E keploy record -c …`), ce que CAP-01
  interdit ; les cassettes VCR/betamax ne voient qu'un client HTTP Python. Aucun outil ne
  lie un identifiant à sa première apparition dans un HAR. Quelques dizaines de lignes.
- **L'expurgation liante (CAP-06).** detect-secrets trouve, il ne remplace pas de façon
  cohérente. Le remplacement par variable réutilise le lieur.
- **Le budget et la détection anti-robot (CAP-05).** Un compteur sur `page.route` et une
  détection de 403, 429 et pages interstitielles. Aucun outil de capture n'a de budget.
- **Le générateur de sondes de formulaire (CAP-04).** Schemathesis sonde une API, pas un
  formulaire. Les sondes sont des scénarios Playwright générés depuis l'inventaire.
- **Relations et cardinalités (INF-02).** genson infère les types, pas les liens. Heuristique
  par nom et par valeur partagée entre charges utiles.
- **La machine à états (INF-03).** Comptage des transitions observées, YAML validé par un
  JSON Schema du dépôt. SCXML (W3C) existe mais n'a pas été lu ; il se rediscutera si le
  YAML ne suffit plus.
- **Le compilateur de politique (VER-02).** YAML → paramètres DeepDiff, ~50 lignes.
- **La géométrie relative (VER-09).** Les `box` de Playwright sont absolus.
- **Les opérateurs de mutation (VER-08).** Aucun outil de mutation ne travaille sur des
  traces HAR.
- **La liste d'indices de simulation (RUN-09).** En-têtes `Server`, `X-Powered-By`, traces
  de pile, identifiants de framework.
- **Le dénominateur de couverture (VER-05).** `scope.yaml` est une décision datée (§1).
- **`tools/check_plan_coverage.py`.** StrictDoc impose son format `.sdoc`, OpenFastTrace
  exige Java 17 (vérifiés, §9). La question se rouvre quand la traçabilité devra atteindre
  du code source.

## 7. Ce qui n'est pas résolu

**7.1 — Le run A/A sur une cible sans reset.** D3 exige un relevé A/A, et la cible
propriétaire (S2) ne se réinitialise pas. Deux rejeux consécutifs sur une cible à état
diffèrent aussi par l'état accumulé, qu'un `diff(cible, cible)` prendrait pour du bruit.
Pistes non mesurées : comptes jetables par rejeu, scénario d'étalonnage borné aux lectures,
relevé qui sépare ce qui varie *entre* rejeux de ce qui varie *avec* l'état.

**7.2 — OpenAPI 3.0 contre 3.1.** mitmproxy2swagger émet du 3.0 — `"openapi": "3.0.0"`
dans sa source, vérifié, §9 ; le cahier nomme 3.1 pour ses schémas 2020-12. L'écart se règle par conversion ou par
acceptation du 3.0 en entrée ; ce n'est pas tranché.

**7.3 — SSE.** AsyncAPI 3 n'a pas de liaison SSE. Les événements SSE sont capturés comme
des réponses HTTP en flux et décrits sous la liaison HTTP, ce qui perd leur sémantique
de canal.

**7.4 — Le seuil de VER-10.** Il n'existe pas avant la première mesure, et la mesure dépend
du modèle qui pilote l'agent. On publie une distribution, pas un chiffre.

**7.5 — La volumétrie du démonstrateur.** GEN-08 et API-06 se mesurent à une volumétrie
déclarée par cible ; laquelle, et sur quel matériel, n'est pas fixé.

**7.6 — L'environnement d'origine de GEN-10.** Aucun ici ; l'exigence est consignée en
échec tant qu'il n'est pas fourni.

## 8. Outils écartés, avec leur motif

Consignés plutôt que supprimés : un motif effacé se répète.

- **Stagehand** — un modèle dans la boucle de rejeu ; D2 le rend inutile.
- **Firecracker, ZFS, btrfs, `pg_branch`** — pour le démonstrateur, la base modèle
  PostgreSQL suffit ; ils reviendraient avec une mesure de RUN-02 qui les exige.
  `pg_branch` était de toute façon abandonné en octobre 2023.
- **libfaketime** — l'interception de `getrandom()` exige une compilation `FAKE_RANDOM`
  (vérifié) ; inutile sur un clone dont on écrit les fournisseurs d'horloge et d'aléa (D7).
- **Porcupine, Elle** — vérifient la linéarisabilité et les anomalies d'isolation ; le
  besoin est de comparer des séquences d'événements avec tolérance d'ordre, ce que DeepDiff
  `ignore_order` fait sur la famille *événements*.
- **AALpy, LearnLib, ALEX** — apprentissage actif d'automates ; les transitions d'un SaaS
  courant se lisent dans les traces, et l'apprentissage actif dépense le budget CAP-05.
- **Classifier Two-Sample Test, SandPrint** — remplacés par la mesure directe VER-10 ; ils
  reviendraient si la mesure directe se révélait trop bruitée.
- **Greenmask** — transforme et sous-échantillonne des dumps existants ; le besoin est de
  générer depuis des distributions, ce que Faker avec graine fait.
- **MinIO** — dépôt archivé le 25/04/2026, « *THIS REPOSITORY IS NO LONGER MAINTAINED* »
  (vérifié). Les fichiers vont sur un volume local.
- **Keploy** — s'installe sur l'hôte de l'application observée, interdit par CAP-01 côté
  cible. Reste un candidat côté clone.
- **Chrome DevTools Recorder** — exporte en JSON et Puppeteer, pas en Playwright sans
  extension tierce (vérifié) ; `playwright codegen` fait la même chose nativement.
- **Diffy** — licence CC-BY-NC-ND, clause ND. L'idée du plancher de bruit reste.
- **VCR.py, betamax, pytest-recording, responses, respx** — aveugles au trafic d'un
  Chromium.
- **Prism comme clone** — aucune persistance d'état, « *Data Persistence* » est en feuille
  de route (vérifié) ; retenu comme **témoin** de ce que l'OpenAPI inféré porte à lui seul.
- **Meticulous** — propriétaire, et exige d'injecter du JavaScript dans l'application
  observée.
- **APIClarity** — reconstruit l'OpenAPI depuis le trafic mais exige Kubernetes et un
  service mesh.
- **OpenHands, SWE-agent** — le besoin est un enchaînement d'appels sous `make`, pas une
  interface agent-ordinateur.
- **Comparaison par pixels** (BackstopJS, Percy, Chromatic) — écartée par D5.
- **trufflehog, ggshield** — envoient les candidats à des API tierces ; detect-secrets
  travaille hors ligne.
- **Crawljax** — dormant depuis 2023 ; Crawlee est actif. **WebExplor, WebRLED** — code
  de recherche ; Schemathesis et Crawlee couvrent l'adversarial du démonstrateur.
- **StrictDoc, OpenFastTrace** — motifs au §6.
- **Terraform** — BUSL 1.1 ; OpenTofu (MPL-2.0) le remplacerait, et ni l'un ni l'autre
  n'est nécessaire à un démonstrateur local sous Compose.

## 9. Références, avec leur statut de vérification

Une référence citée sans avoir été lue est une affirmation de mémoire. Chaque entrée porte
son statut ; une entrée ne remonte d'un cran qu'en citant l'URL et le passage.

### Outils vérifiés le 02/09/2026 — version, licence, passage

| Outil | Vérifié |
|---|---|
| Playwright Python 1.62.0, Apache-2.0 — [tracing](https://playwright.dev/python/docs/api/class-tracing), [codegen](https://playwright.dev/python/docs/codegen), [locator](https://playwright.dev/python/docs/api/class-locator), [mock](https://playwright.dev/python/docs/mock#websockets), [clock](https://playwright.dev/python/docs/clock), [notes de version](https://playwright.dev/python/docs/release-notes) | `tracing.start(screenshots=, snapshots=)` : « *tracing will capture DOM snapshot on every action* » et « *record network activity* » ; `start_har` « *Added in: v1.60* » ; `record_har_path` sur `new_context` ; codegen « *prioritizing role, text and test id locators* » ; `aria_snapshot` v1.49, `boxes` v1.60, `mode="ai"` v1.59 ; `route_web_socket` v1.48 : « *intercept WebSocket connections and mock entire communication* » ; `page.clock.install` / `set_fixed_time` v1.45 ; `ariaSnapshotJSON` « *Added in: v1.63* », `langs: js` |
| [mitmproxy2swagger](https://github.com/alufers/mitmproxy2swagger) 0.15.0 (25/05/2026), MIT | « *converting mitmproxy captures to OpenAPI 3.0 specifications* » ; entrée « *HAR (HTTP Archive) files exported from browser DevTools* » |
| [Schemathesis](https://schemathesis.readthedocs.io/en/stable/) 4.25.2 (24/08/2026), MIT | *stateful* : « *chains API calls together using real data from responses* », liens OpenAPI ; négatif : « *deliberately invalid according to your schema* », `--mode=negative` ; entrée : tout OpenAPI 2.0 à 3.2 par fichier ou URL |
| [DeepDiff](https://zepworks.com/deepdiff/current/diff.html) 9.1.0, MIT, dépôt `qlustered/deepdiff` | `exclude_regex_paths` « *regex paths […] to exclude from the report* » ; `ignore_order` ; `verbose_level` 2 « *shows the value of the items* » ; `Delta` |
| [Crawlee Python](https://crawlee.dev/python/) 1.10.0 (31/08/2026), Apache-2.0 | `PlaywrightCrawler`, extra `crawlee[playwright]` |
| [genson](https://pypi.org/pypi/genson/json) 1.4.0 (06/07/2026), MIT | « *JSON Schema generator built in Python* » |
| [detect-secrets](https://github.com/Yelp/detect-secrets) 1.5.0 (06/05/2024), Apache-2.0 | détection locale ; `--no-verify` « *Disables additional verification of secrets via network call* » |
| [Prism](https://github.com/stoplightio/prism) 5.16.0 (17/07/2026), Apache-2.0 | mode dynamique `-d` ; « *Data Persistence (allow Prism act like a sandbox)* » en feuille de route, donc sans état |
| [FastMCP](https://github.com/PrefectHQ/fastmcp) 4.0.0 (31/08/2026), Apache-2.0 | `from_openapi()` et `from_fastapi()` lus dans `fastmcp/server/server.py` |
| [MCP](https://modelcontextprotocol.io/specification/versioning) révision 2026-07-28 | `tools/list`, `tools/call` ; `inputSchema` « *MUST be a valid JSON Schema object* », 2020-12 par défaut ; `outputSchema` depuis 2025-06-18 ; SDK Python et TypeScript de niveau 1 |
| [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1) | « *Schema Object, which is a superset of the JSON Schema Specification Draft 2020-12* » |
| [AsyncAPI 3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0), [liaisons](https://github.com/asyncapi/bindings) | *Channel Object*, `messages` ; liaison WebSockets v0.1.0 ; **aucune liaison SSE** ; CLI `@asyncapi/cli` 6.0.2 Apache-2.0, `asyncapi validate` ; Python : `pydantic-asyncapi` 0.3.2 |
| [HAR 1.2](https://w3c.github.io/web-performance/specs/HAR/Overview.html) | « *This document was never published by the W3C Web Performance Working Group and has been abandoned* » |
| [PostgreSQL 18 `CREATE DATABASE`](https://www.postgresql.org/docs/18/sql-createdatabase.html), [`pg_dump`](https://www.postgresql.org/docs/18/app-pgdump.html) | TEMPLATE : « *no other sessions can be connected to the template database while it is being copied* » ; `STRATEGY` WAL_LOG par défaut, FILE_COPY ; `-Fc` « *custom-format archive suitable for input into pg_restore* » |
| [Compose Specification](https://github.com/compose-spec/compose-spec), Apache-2.0 | « *a standard for the definition of multi-container platform-agnostic applications* » ; `image` « *[:<tag>\|@<digest>]* » |
| [Testcontainers Python](https://testcontainers-python.readthedocs.io/) 4.15.0 (24/07/2026), Apache-2.0 | `PostgresContainer` |
| [k6](https://grafana.com/docs/k6/latest/) 2.2.0 (10/08/2026), AGPL-3.0 | « *Thresholds are the pass/fail criteria* », `p(95)<200` ; modules `http` et `k6/websockets` |
| [MLflow Tracing](https://mlflow.org/docs/latest/genai/tracing/) 3.15.2 (26/08/2026), Apache-2.0 | « *fully OpenTelemetry-compatible* », « *natively supports GenAI Semantic Conventions* » |
| [Langfuse](https://langfuse.com/docs/opentelemetry/get-started) 4.27.0, MIT hors `ee/` | OTLP sur `/api/public/otel` ; auto-hébergeable. Non retenu : MLflow suffit et n'a pas de dossier `ee/` |
| [OpenTelemetry GenAI](https://github.com/open-telemetry/semantic-conventions-genai) | déplacé dans son propre dépôt ; statut « *Development* » ; `gen_ai.request.model` stable, `gen_ai.usage.input_tokens` en développement, `gen_ai.system` remplacé par `gen_ai.provider.name` |
| [Mailpit](https://github.com/axllent/mailpit) 1.31.0 (22/08/2026), MIT | « *email testing tool & API* », API REST pour lire les messages |
| [WireMock](https://wiremock.org) 3.13.2, Apache-2.0 · [mock-oauth2-server](https://github.com/navikt/mock-oauth2-server) 6.0.2, MIT | bouchon HTTP ; serveur OAuth2/OIDC scriptable pour Docker Compose |
| [MinIO](https://github.com/minio/minio) | archivé le 25/04/2026, AGPL-3.0, « *THIS REPOSITORY IS NO LONGER MAINTAINED* » |
| [Alembic](https://alembic.sqlalchemy.org/) 1.19.1 (08/08/2026), MIT · [Atlas](https://atlasgo.io/) 1.3.0, Apache-2.0 en édition communautaire | Alembic retenu : Python, SQLAlchemy |
| [OpenTofu](https://github.com/opentofu/opentofu) 1.12.6, MPL-2.0 · Terraform 1.16.0, BUSL 1.1 | ni l'un ni l'autre nécessaire (§8) |
| [OpenZFS](https://openzfs.github.io/openzfs-docs/man/master/7/zfsconcepts.7.html) · [btrfs](https://btrfs.readthedocs.io/en/latest/Subvolumes.html) | instantanés « *created extremely quickly* » / « *instantaneous* » ; écartés (§8) |
| [Keploy](https://keploy.io/docs/server/linux/installation/) 3.6.30, Apache-2.0 | « *uses eBPF* » ; `sudo -E keploy record -c "CMD_TO_RUN_APP"` : s'installe sur l'hôte de l'app |
| [Chrome DevTools Recorder](https://developer.chrome.com/docs/devtools/recorder/reference) | exports JSON, Puppeteer ; Playwright seulement par extension tierce |
| [StrictDoc](https://github.com/strictdoc-project/strictdoc) · [OpenFastTrace](https://github.com/itsallcode/openfasttrace) | Apache-2.0, Python, format `.sdoc` / GPL-3.0, Java 17 |
| [libfaketime](https://raw.githubusercontent.com/wolfcw/libfaketime/master/README) 0.9.13 | `FAKERANDOM_SEED` seulement « *compiled with the CFLAG FAKE_RANDOM* », Linux ; écarté (§8) |
| Mattermost — [API](https://github.com/mattermost/mattermost/tree/master/api), [prérequis](https://docs.mattermost.com/deployment-guide/software-hardware-requirements.html), [`LICENSE.txt`](https://github.com/mattermost/mattermost/blob/master/LICENSE.txt), [`utils.go`](https://github.com/mattermost/mattermost/blob/master/server/public/model/utils.go), [docker](https://github.com/mattermost/docker) | `openapi: 3.0.0` ; PostgreSQL 14+, MySQL retiré en v11 ; binaires MIT, sources AGPL-3.0 ou commerciale, parties Apache-2.0 ; `NewId` 26 caractères z-base-32 ; compose officiel épinglé par étiquette |
| [Faker](https://github.com/joke2k/faker/blob/master/README.rst) 40.38.0 (01/09/2026), MIT | « *A Seed produces the same result when the same methods with the same version of faker are called* » ; « *results are not guaranteed to be consistent across patch versions* », d'où la version épinglée |
| [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.txt), juillet 2023 | « *Obsoletes: 7807* », *Standards Track* ; membres `type`, `title`, `status`, `detail`, `instance` |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) 0.0.80 (01/09/2026), Apache-2.0 | « *interact with web pages through structured accessibility snapshots, bypassing the need for screenshots* » ; outils `browser_snapshot`, `browser_click` ; `npx @playwright/mcp@latest` |
| [Permissions de l'agent de code](https://code.claude.com/docs/en/permissions) | « *add a `Read` deny rule for its path, such as `Read(./.env)` or `Read(./secrets/**)`* » ; « *deny rules don't apply to arbitrary subprocesses* » |
| [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/) 0.141.1, MIT · SQLAlchemy 2.0.52, MIT · Alembic 1.19.1, MIT | `/openapi.json` : « *a JSON starting with something like: { "openapi": "3.1.0"* » |
| [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/) 4.26.0, MIT · [openapi-spec-validator](https://github.com/python-openapi/openapi-spec-validator) 0.9.0, Apache-2.0 | « *Full support for Draft 2020-12* » ; « *validates OpenAPI Specs against the OpenAPI 2.0 […] 3.0 […] 3.1 and OpenAPI 3.2* » |
| [pytest-playwright](https://playwright.dev/python/docs/test-runners) 0.9.0, Apache-2.0 | fixtures `page`, `context`, `browser` ; `--tracing on` |
| [Instantanés ARIA](https://playwright.dev/python/docs/aria-snapshots) | `expect(page).to_match_aria_snapshot(...)` ; `/children`: « *contain (default) […] equal […] deep-equal* » |

### Travaux vérifiés le 01/09/2026, passage à l'appui

| Référence | Vérifié |
|---|---|
| Hammoudi, Rothermel & Tonella, *Why do Record/Replay Tests of Web Applications Break?*, ICST 2016 — [résumé](https://digitalcommons.unl.edu/computerscidiss/100), [auto-citation FSE 2016](https://tsigalko18.github.io/assets/pdf/2016-Hammoudi-FSE.pdf) | « *453 versions […] 1065 individual test breakages* » ; « *73.62% of them were related to obsolete locators* » |
| X-PERT, Roy Choudhary, Prasad & Orso, ICSE 2013, [PDF](http://shauvik.com/public/pubs/roychoudhary13icse_cr.pdf) | « *precision (76%) and recall (95%)* » |
| TOGLL, Hossain & Dwyer, [arXiv 2405.03786](https://arxiv.org/pdf/2405.03786) | « *7% false positive rate for exception oracles and a 25% rate for assertion oracles* » |
| Kambhampati et al., ICML 2024, [arXiv 2402.01817](https://arxiv.org/abs/2402.01817) | « *cannot, by themselves, do planning or self-verification* » ; « *external sound critics* » |
| Olausson et al., ICLR 2024, [arXiv 2306.09896](https://arxiv.org/abs/2306.09896) | « *performance gains are often modest […] sometimes not present at all* » ; « *substantially larger* » avec un meilleur retour ; i.i.d. parfois aussi bon à petit budget |
| Böhme, Liyanage & Wüstholz, ESEC/FSE 2021, [PDF](https://mboehme.github.io/paper/FSE21.pdf) | « *estimators for blackbox fuzzing systematically and substantially under-estimate the true risk* » |
| Jahangirova, Clark, Harman & Tonella, ISSTA 2016, [PDF](http://www0.cs.ucl.ac.uk/staff/D.Clark/pubs/toaai2016.pdf) | « *test case generation to reveal false positives and mutation testing to reveal false negatives* » |
| *The Verification Horizon*, [arXiv 2606.26300](https://arxiv.org/abs/2606.26300) | « *verification must co-evolve with the generator* » |
| *Before the Model Learns the Bug*, J. Ray, [arXiv 2606.01066](https://arxiv.org/abs/2606.01066) | existence, auteur, date |
| VeriEnv, [arXiv 2603.10505](https://arxiv.org/abs/2603.10505) · InfiniteWeb, [arXiv 2601.04126](https://arxiv.org/abs/2601.04126) | récompenses de tâche vérifiables ; **aucun protocole de fidélité à l'original** |
| *Understanding Automated Web GUI Testing*, [arXiv 2606.16650](https://arxiv.org/abs/2606.16650) | table 3 : Crawljax 49,12 %, WebExplor 52,45 %, WebRLED 57,60 %, GPTWeb 49,39 % ; 33 défaillances uniques WebExplor contre 24 GPTWeb — les familles sont complémentaires |

### Non vérifié — cité de seconde main

McKeeman, *Differential Testing for Software*, DTJ 1998 · Just et al., FSE 2014
(corrélation mutants-fautes réelles) · SCXML, W3C 2015 · Diffy (Twitter), plancher de bruit.
