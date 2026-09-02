# Plan d'exécution

Dans quel ordre construire les étapes de `docs/architecture.md`, et à quel critère
falsifiable chaque lot s'arrête.

Ce document ne contient ni décision de conception, ni comparatif d'outils : tout cela vit
dans `docs/architecture.md`. Il définit l'espace de noms `lot n` : aucun autre document ne
crée ni ne renumérote un lot, il ne peut que le citer. Les numéros de section sont des
ancres — on ne renumérote jamais.

## 1. Le problème

Répliquer un logiciel n'est pas difficile. Prouver qu'une réplique est indiscernable de
son original l'est : c'est un problème d'oracle. `VER-01` — rejouer une trace sur cible et
clone et produire un différentiel — est l'exigence dont sept des dix critères
d'acceptation dépendent. L'état de l'art publié revendique des répliques haute fidélité
sans décrire de protocole de fidélité (VeriEnv, InfiniteWeb, vérifiés dans
`docs/architecture.md` §9) : leurs récompenses vérifient qu'une **tâche** est accomplie,
jamais que l'environnement ressemble à l'original.

D'où l'ordre : un générateur que rien ne contredit produit du plausible et faux à grande
échelle, et c'est vrai d'un agent comme d'un humain pressé.

## 2. L'ordre, et pourquoi

- **L'oracle devant, l'agent dès le premier lot.** Olausson et al. (ICLR 2024, vérifié) :
  l'auto-réparation gagne peu quand le modèle produit son propre retour, nettement plus
  quand le retour est meilleur. `judge/diff` est ce retour : la boucle a du sens dès qu'il
  existe.
- **Le taux de détection avec le premier compte.** Une liste d'écarts sans taux ne vaut
  rien (D4), y compris la nôtre. Le lot 1 publie trois chiffres ou aucun.
- **La deuxième cible avant la surface et la flotte.** Une chaîne démontrée sur une cible
  libre, locale, réinitialisable a démontré la moitié facile du métier (S1). La cible
  propriétaire (S2) retire une à une ces facilités, et c'est elle qui dit si les étapes
  connaissent leur cible.

## 3. Les lots ne sont pas chiffrés en jours

Le code est écrit par des agents, et une charge d'écriture ne borne rien. Ce qui borne un
lot, c'est ce qui ne se parallélise pas, et chaque lot en porte le relevé sous *Charge* :

- les **décisions humaines bloquantes** — périmètre, ratification d'une décision de spec,
  choix d'une cible ;
- les **exécutions à durée machine** que le critère de sortie exige — cycles de reset,
  campagne jusqu'à son critère d'arrêt, rejeux sous le budget `CAP-05`, qui est une borne
  de calendrier par construction ;
- le **plafond de jetons**, fixé avant lancement et publié avec les chiffres de sortie,
  lu dans `orchestrate/trace` — la pratique de `LLM-04` dès le lot 1 ;
- le **nombre d'itérations de réparation**, publié au lot 1 et comparé ensuite.

Tant que l'oracle n'existe pas, le seul critique des agents qui l'écrivent est la
spécification gelée et son relecteur humain : le débit du lot 1 est celui de la relecture.
`OUT-01` mesure tout cela par cible, en heures de calendrier, jetons et décisions.

## 4. Les cibles

### 4.1 Première cible — Mattermost, l'étalon (S1)

Déployée localement par le compose officiel, image épinglée par *digest* relevé par nous.
Ses propriétés utiles — API OpenAPI, PostgreSQL, source disponible, licence, forme des
identifiants — sont vérifiées dans `docs/architecture.md` §9 et ne sont pas répétées ici.
Marque protégée : toute démonstration publique rebrande.

*Ce que cette justification vaut.* Ce qui fait gagner Mattermost — API documentée, source
disponible, reset par base modèle, ni anti-robot ni budget — est exactement ce qu'une cible
propriétaire n'a pas. « L'oracle marche sur Mattermost » est une information faible sur
« l'oracle marchera ». Mattermost est un étalon : on y voit l'état des deux côtés, ce qui
sert à étalonner (P4), jamais à juger.

*Périmètre proposé*, à arrêter et versionner dans `targets/mattermost/scope.yaml` avant
toute campagne — c'est ce fichier qui fait foi, pas ce tableau :

| Écran | Entités |
|---|---|
| A. Connexion | `users` |
| B. Barre latérale équipes et canaux | `teams`, `channels`, `channelmembers` |
| C. Canal et envoi de message | `posts` |

Recherche, fichiers, réactions, fils hors périmètre au premier tour. Le temps réel entre au
lot 5, et l'écran C en dépend : Mattermost livre les messages par WebSocket. Tant que le
lot 5 n'est pas tenu, la famille *événements* est absente des traces de l'écran C, et le
rapport la nomme comme non comparée (`docs/architecture.md` §4).

*Première mesure, avant tout diff* : rejouer deux fois le même scénario et compter les
opérations exercées. Si le nombre varie, le dénominateur de `VER-05` varie avec lui.

### 4.2 Deuxième cible — choisie pour ce qu'elle retire (S2)

Pas de code source, donc `CAP-08` inopérante ; pas de reset, donc le run A/A a la forme
que `docs/architecture.md` §7.1 n'a pas encore ; budget de requêtes réel et protections
anti-robot, donc `CAP-05` exerçable ; identifiants et horodatages d'une autre forme que le
z-base-32 et l'epoch-ms, pour éprouver le lieur de D3. Le choix est une décision bloquante
du lot 3, prise sur ces quatre critères et consignée ici.

## 5. Lots

Chaque lot a un critère de sortie **falsifiable**, une commande qui sort en erreur tant
qu'il n'est pas tenu, et un relevé de charge. Ce dépôt part vide : **rien n'est fait.**

### Lot 1 — Le vertical : connexion, clone par agent, trois chiffres

Un écran, la connexion, parcouru de bout en bout ; le clone écrit par l'agent de code sur
la pile D7 ; l'oracle validé par ses premières fautes semées.

*Étapes* : `observe/record`, `observe/aa`, `infer/surface`, `infer/entities`,
`build/generate`, `run/env`, `run/reset`, `judge/replay`, `judge/policy`, `judge/diff`,
`judge/mutate`, `orchestrate/loop`, `orchestrate/trace`.

*Exigences* : `CAP-01`, `CAP-02`, `CAP-07`, `INF-01`, `INF-02`, `GEN-01`, `GEN-02`,
`RUN-01`, `RUN-03`, `VER-01`, `VER-02`, `VER-08`, `LLM-01`, `LLM-03`, `LLM-04`.

*Première expérience, avant tout le reste* : un HAR de la connexion enregistré par
Playwright, passé à mitmproxy2swagger, servi par Prism. Prism est le **témoin** — ce que
l'OpenAPI inféré porte à lui seul, sans état — et l'écart entre le témoin et le clone
agentique est l'apport mesuré de l'agent. Si l'OpenAPI ne sert rien d'utile,
`infer/surface` change de nature et le lot avec.

*Ordre des treize étapes*, dicté par ce que la spécification gelée peut juger sans cible.
D'abord le **squelette** : les treize répondent à `--in` et `--out` et ne font rien encore,
ce qui rend `tests/spec/lot1/test_contrat.py` vert et donne sa forme au reste. Puis
**l'oracle sur fixtures** — `judge/diff`, `judge/policy`, `judge/mutate` — qui n'a besoin
ni de cible, ni de clone, ni de conteneur, et referme `test_oracle.py`. Puis **l'inférence
sur fixtures** — `infer/surface`, `infer/entities` — qui referme `test_inference.py`. À ce
point la spécification est verte hors ligne et le critique sain existe avant qu'un agent
n'écrive une ligne de clone : c'est D6 pris au mot, et c'est pourquoi l'oracle ne vient pas
après. Viennent ensuite **la capture sur cible vivante** — `observe/record`, `observe/aa` —
puis **le clone et son environnement** — `build/generate`, `run/env`, `run/reset` — enfin
**la boucle** — `judge/replay`, `orchestrate/loop`, `orchestrate/trace` — qui produit les
trois chiffres. Une étape par commit, les tests qu'elle doit rendre verts nommés avant
qu'elle soit écrite.

*Charge* — décisions bloquantes : les fixtures de la spec ratifiées (`tests/spec/README.md`),
`scope.yaml` arrêté, le *digest* de l'image relevé, le plafond de jetons fixé. Exécutions :
deux captures A/A, puis un rejeu sur le clone par itération de réparation.

*Commande* : `make lot1` — la spec du lot, puis cinq artefacts sous
`targets/mattermost/rapports/lot1/` : `ecarts.json`, `taux.json`, `iterations.json`,
`jetons.json`, `decisions.json`. Elle échoue si l'un manque ou est vide, et imprime les
trois chiffres sinon. Aucun `exit 1` écrit d'avance.

*Critère de sortie* : trois chiffres publiés ensemble ou pas du tout — la liste d'écarts
cible↔clone, chaque écart portant sa trace de reproduction ; le taux de détection sur le
jeu de fautes initial ; le nombre d'itérations de réparation avant convergence — plus les
jetons consommés et les décisions prises, pour `OUT-01`.

### Lot 2 — L'oracle opposable

Durcir ce que le lot 1 a produit vite, sur des écarts réels.

*Étapes* : `observe/redact`, `infer/states`, `infer/provenance`, `infer/rank`,
`judge/screen`, `judge/leaks`, `judge/coverage`, `judge/report`.

*Exigences* : `CAP-06`, `INF-03`, `INF-04`, `INF-05`, `INF-06`, `INF-07`, `VER-05`,
`VER-06`, `VER-07`, `VER-09`, `OUT-02`.

`GEN-03`, `GEN-04` et `RUN-09` se **jugent** ici — `judge/diff`, `judge/screen`,
`judge/leaks` — mais ne se **tiennent** qu'en changeant le clone, ce que ce lot s'interdit :
elles sont portées par le lot 4.

- `observe/redact` et `judge/screen` entrent avec la forme que `docs/architecture.md` §4
  leur donne : expurgation liante, gabarit produit depuis la cible.
- `judge/report` produit les dix critères `ACC`, et dit lesquels sont tenus.

*Charge* — décisions bloquantes : le format de `equivalence.yaml` et du relevé A/A ratifié
(D3). Exécutions : une campagne complète en intégration continue cible éteinte par
candidat de comparateur, une par faute semée. Pas de boucle de réparation dans ce lot : le
clone n'y change pas.

*Commande* : `make lot2` — la spec du lot, puis `targets/mattermost/rapports/lot2/acceptation.json`,
le rapport de `judge/report` ; elle échoue s'il manque ou si le taux de détection qu'il
porte n'est pas 1.

*Critère de sortie* : le taux de détection vaut **100 %** sur le jeu initial ; la campagne
tourne en intégration continue cible éteinte ; aucune trace stockée ne contient de secret,
vérifié par un test ; la politique est lue par le code et chaque entrée cite un relevé ;
les écrans du périmètre sont comparés ; le rapport d'acceptation existe et consigne ses
échecs.

*Échec du lot* : un taux inférieur à 100 % sur des fautes aussi grossières signifie que
le comparateur est à reprendre avant tout élargissement.

### Lot 3 — La deuxième cible, et la source de la première

**Le lot qui décide si replikit est un outil ou un banc.**

*Étapes* : `observe/explore`, `observe/probe`, `observe/ingest`.

*Exigences* : `CAP-03`, `CAP-04`, `CAP-05`, `CAP-08`, `GEN-11`, `OUT-01`.

`CAP-08` entre ici : c'est le contraste entre une cible libre dont on dérive le schéma
depuis la source et une cible propriétaire dont on ne dérive rien qui donne à l'exigence
son sens.

*Charge* — décisions bloquantes : le choix de la cible 2 (§4.2), la forme du run A/A sans
reset (`docs/architecture.md` §7.1) avant toute politique, le budget `CAP-05` de la cible.
Exécutions : c'est ce budget qui borne le lot — chaque capture, chaque rejeu A/A le
consomme. Premier lot dont la durée est dictée par la cible.

*Commande* : `make lot3` — la spec du lot, puis `ecarts.json`, `taux.json` et
`lignes_cible.json` sous `targets/<cible2>/rapports/lot3/` ; elle échoue si l'un manque.

*Critère de sortie* : la même chaîne, **sans ligne propre à la cible sous les sept
paquets**, produit une liste d'écarts et un taux de détection sur une cible sans source,
sans reset et sous budget ; le nombre de lignes sous `targets/<cible2>/` est publié
(`GEN-11`) ; `OUT-01` est mesuré sur les deux cibles.

*Échec du lot* : toute ligne ajoutée sous les paquets pour faire passer la cible 2 est
un aveu que l'étape connaissait la cible 1.

### Lot 4 — La surface *tool use* et l'environnement complet

*Étapes* : `build/seed`, `build/preserve`, `run/admin`, `run/journal`, `serve/mcp`,
`serve/parity`, `orchestrate/evalset`.

*Exigences* : `GEN-03`, `GEN-04`, `GEN-05`, `GEN-07`, `GEN-08`, `GEN-09`, `RUN-04`,
`RUN-05`, `RUN-06`, `RUN-07`, `RUN-09`, `API-01`, `API-02`, `API-03`, `API-04`, `API-05`,
`LLM-02`, `LLM-05`, `LLM-06`.

`RUN-04` et l'isolation de `RUN-02` se « démontrent » facilement par lecture de code, ce
qui ne démontre rien : leur critère exige une exécution réseau coupé.

*Charge* — décisions bloquantes : la volumétrie du démonstrateur (`docs/architecture.md`
§7.5). Exécutions : le protocole `ACC-05` — cycles déclarés, état complet comparé — et une
tâche par les deux surfaces. Plafond de jetons : le plus élevé du plan, la boucle tourne
sur deux cibles.

*Commande* : `make lot4` — la spec du lot, puis `parite.json`, `reset.json`, `ecarts.json`,
`taux.json` et `iterations.json` sous `rapports/lot4/` de chaque cible ; elle échoue si l'un
manque.

*Critère de sortie* : un environnement sert son périmètre **réseau sortant coupé** ; la
parité UI↔API est **mesurée** par `judge/diff`, pas déclarée ; les mêmes opérations sont
servies en MCP ; `ACC-05` est exécuté et consigné ; les trois chiffres du lot 1 sont
republiés sur les deux cibles, itérations en baisse ou expliquées.

### Lot 5 — Collaboratif, adversarial, indiscernabilité, acceptation

*Étapes* : `judge/edge`, `judge/adversary`, `observe/agent`, `serve/load`.

*Exigences* : `CAP-09`, `CAP-10`, `GEN-06`, `RUN-02`, `RUN-08`, `VER-03`, `VER-04`,
`VER-10`.

Mattermost est collaborative : `CAP-09`, `CAP-10`, `GEN-06`, `RUN-08` et `ACC-09` sont
bloquantes pour elle. **Aucun clone produit avant ce lot n'est livrable au sens du §14 du
cahier.** C'est acceptable pour un banc, à condition de ne pas le confondre avec une
livraison.

*Charge* — le lot le plus lourd. Décisions bloquantes : le critère d'arrêt de la campagne
adversariale, la tâche de `VER-10` et le modèle qui pilote l'agent, le nombre
d'environnements à mesurer pour `RUN-02`. Exécutions : la campagne adversariale jusqu'à son
critère, `VER-10` répétée jusqu'à une distribution, la charge k6 à la volumétrie déclarée.

*Commande* : `make lot5` — `acceptation.json`, `indiscernabilite.json` et
`environnements.json` sous `rapports/lot5/` ; elle échoue si l'un manque.

*Critère de sortie* : `judge/report` produit les **dix** critères `ACC` et dit lesquels
sont tenus ; `VER-10` est publiée comme distribution ; `RUN-02` est mesurée. Un lot 5
réussi n'est pas un lot où tout passe : c'est un lot où chaque critère porte un verdict
produit par une commande. `ACC-10` y figure en échec tant que personne ne tient le rôle.

## 6. Couverture — étapes et exigences par lot

Ce tableau est la carte que `tools/check_plan_coverage.py` recompte dans les deux sens :
une exigence de rang L ou O sans lot est une erreur, une étape de `docs/architecture.md`
§4 sans lot en est une aussi, et aucune exigence n'est due avant une étape qui la porte.
Une exigence citée dans une prose n'est pas portée pour autant.

| Lot | Commande | Étapes livrées | Exigences portées |
|---|---|---|---|
| **lot 1 — vertical** | `make lot1` | `observe/record` `observe/aa` `infer/surface` `infer/entities` `build/generate` `run/env` `run/reset` `judge/replay` `judge/policy` `judge/diff` `judge/mutate` `orchestrate/loop` `orchestrate/trace` | `CAP-01`, `CAP-02`, `CAP-07`, `INF-01`, `INF-02`, `GEN-01`, `GEN-02`, `RUN-01`, `RUN-03`, `VER-01`, `VER-02`, `VER-08`, `LLM-01`, `LLM-03`, `LLM-04` |
| **lot 2 — oracle opposable** | `make lot2` | `observe/redact` `infer/states` `infer/provenance` `infer/rank` `judge/screen` `judge/leaks` `judge/coverage` `judge/report` | `CAP-06`, `INF-03`, `INF-04`, `INF-05`, `INF-06`, `INF-07`, `VER-05`, `VER-06`, `VER-07`, `VER-09`, `OUT-02` |
| **lot 3 — deuxième cible** | `make lot3` | `observe/explore` `observe/probe` `observe/ingest` | `CAP-03`, `CAP-04`, `CAP-05`, `CAP-08`, `GEN-11`, `OUT-01` |
| **lot 4 — surface et environnement** | `make lot4` | `build/seed` `build/preserve` `run/admin` `run/journal` `serve/mcp` `serve/parity` `orchestrate/evalset` | `GEN-03`, `GEN-04`, `GEN-05`, `GEN-07`, `GEN-08`, `GEN-09`, `RUN-04`, `RUN-05`, `RUN-06`, `RUN-07`, `RUN-09`, `API-01`, `API-02`, `API-03`, `API-04`, `API-05`, `LLM-02`, `LLM-05`, `LLM-06` |
| **lot 5 — acceptation** | `make lot5` | `judge/edge` `judge/adversary` `observe/agent` `serve/load` | `CAP-09`, `CAP-10`, `GEN-06`, `RUN-02`, `RUN-08`, `VER-03`, `VER-04`, `VER-10` |

**Ce que ce tableau ne porte pas, et le dit.** Les exigences de rang N — `GEN-10`,
`API-06`, `OUT-03`, la volumétrie de `GEN-08` et le nombre de `RUN-02` — sont mesurées
quand une exécution le permet et ne conditionnent rien (§3 du cahier). L'extension
`VER-11` n'est pas ordonnancée. Les dix `ACC` sont des sorties de `judge/report`, lot 2,
et portent leur verdict à partir du lot 5.

## 7. Décisions en attente, et deux échecs assumés

**La licence de replikit.** Ce n'est pas un livrable commercial ; les dépendances copyleft
ne sont pas écartées (k6 est AGPL-3.0). La licence que replikit porte lui-même reste à
choisir.

**`ACC-10` est en échec, et le reste.** Le critère exige une revue par un Curriculum
Engineer. Personne ne tient ce rôle sur ce dépôt. Il est consigné en échec, et aucun clone
produit ici n'est livrable au sens du §14 tant qu'un relecteur qualifié distinct de
l'auteur n'a pas rendu son avis.

**`GEN-10` n'a pas d'objet ici.** Aucun environnement d'origine sur fichiers JSON n'existe
dans ce dépôt ; en fabriquer un contredirait `GEN-01`. Consignée en échec, pas retirée.
