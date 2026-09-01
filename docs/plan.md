# Plan d'exécution

Dans quel ordre construire les blocs de `docs/architecture.md`, et à quel critère
falsifiable chaque lot s'arrête.

Ce document ne contient ni décision de conception, ni comparatif d'outils, ni limite
théorique : tout cela vit dans `docs/architecture.md` et n'est pas répété ici. Il définit
l'espace de noms `lot n` : aucun autre document ne crée ni ne renumérote un lot, il ne peut
que le citer. Les numéros de section sont des ancres — on ne renumérote jamais.

## 1. Le problème, énoncé précisément

Répliquer un logiciel n'est pas difficile. **Prouver qu'une réplique est indiscernable de
son original l'est.** C'est un problème d'oracle : décider, de façon reproductible et
automatisée, que deux systèmes se comportent identiquement pour une même séquence
d'entrées.

`VER-01` — rejouer une trace sur la cible et sur le clone, puis produire un différentiel —
est l'exigence dont sept des onze critères d'acceptation dépendent — `ACC-01`, `ACC-02`,
`ACC-03`, `ACC-04`, `ACC-08`, `ACC-09`, `ACC-11` ; `ACC-05`, `ACC-06`, `ACC-07` et `ACC-10`
n'en dépendent pas. Et l'état de l'art publié
revendique des répliques haute fidélité sans décrire aucun protocole de validation. Ce n'est
pas une lecture de notre part : VeriEnv, vérifié dans `docs/architecture.md` §13, clone des
sites réels en environnements « programmatically verifiable » — vérifiables sur
l'accomplissement d'une **tâche**, jamais sur la fidélité à l'original.

D'où l'ordre des lots : un générateur que rien ne contredit produit des résultats plausibles
et faux, à grande échelle. C'est vrai d'un modèle comme d'un humain pressé, et ça ne dépend
d'aucun précédent particulier.

## 2. L'ordre, et pourquoi celui-là

Deux versions antérieures de ce plan ont été écartées, et les deux motifs se répondent.

**La première construisait l'oracle sur cinq étapes d'outillage avant de le confronter à un
clone.** Toutes les décisions de conception étaient alors anticipatoires : le banc comparait
une cible à elle-même, le cas le plus facile.

**La seconde fermait bien la boucle sur un écran, mais avec un clone écrit à la main et une
deuxième cible renvoyée à un lot « à cadrer ».** Deux défauts qui se tiennent : l'agent
n'entrait qu'au troisième lot, donc le chiffre qui dit si l'outil généralise — *combien
d'itérations de réparation avant convergence* — n'arrivait qu'au jour 14 ; et tant que la
deuxième cible n'a pas de date, « l'oracle marche sur Mattermost » reste l'information
faible que le §3 décrit lui-même.

**L'ordre retenu corrige les deux. L'agent écrit le clone dès le lot 1, et la deuxième cible
est le lot 3.** C'est le déplacement de l'agent qui libère la place de la deuxième cible.

Trois raisons, chacune adossée à une source vérifiée dans `docs/architecture.md` §13 :

- **L'agent au lot 1.** Olausson et al. (ICLR 2024) mesurent que l'auto-réparation apporte
  des gains modestes voire nuls quand le modèle produit son propre retour, et nettement plus
  grands quand la qualité du retour est relevée. `judge/diff` **est** ce retour de meilleure
  qualité : la boucle a donc du sens dès qu'il existe, pas plus tard.
- **L'oracle reste devant.** Ce que le lot 1 gagne en réalisme, il le paie en fiabilité : une
  liste d'écarts sans taux de détection ne vaut rien (D4), y compris la nôtre. Le lot 1 ne
  publie donc pas un chiffre mais **trois**, et le troisième est le taux de détection.
- **La récompense doit co-évoluer.** Dès que `judge/diff` devient le retour d'un agent, il
  devient sa fonction de récompense, et une récompense fixe se fait optimiser plutôt que
  satisfaire (*The Verification Horizon*, arXiv 2606.26300). C'est `VER-11`, et c'est
  pourquoi le jeu de fautes semées n'est jamais exposé au générateur.

## 3. Les cibles

### 3.1 Première cible — Mattermost, l'étalon

**Mattermost**, déployé localement en Docker. SPA sur API REST `/api/v4` documentée en
OpenAPI, PostgreSQL, dépôt source disponible — donc `CAP-08` exerçable.

*Ce que cette justification vaut.* Les critères qui ont fait gagner Mattermost sont
exactement ceux qu'une cible propriétaire n'a pas : API documentée, migrations publiques,
déploiement local, reset par volume, ni anti-robot ni budget de requêtes. « L'oracle
fonctionne sur Mattermost » est donc une information faible sur « l'oracle fonctionnera ».
Mattermost est un **étalon**, choisi parce qu'on y voit l'état des deux côtés.

*Ce que le déploiement local change.* `CAP-05` (budget de requêtes) et `CAP-09` (anti-robot)
ne sont pas **exerçables** sur une cible locale — elles restent bloquantes et de socle, et
redeviennent actives au lot 3. Une exigence ne tombe pas parce que la cible choisie ne la
sollicite pas. On obtient en revanche un reset fiable par instantané de volume, qui rend le
run A/A de D2 gratuit, donc obligatoire.

*Périmètre déclaré*, arrêté et versionné **avant toute campagne**, dans
`targets/mattermost/scope.yaml` — sans quoi « zéro écart » et « 100 % » s'obtiennent en
rétrécissant le périmètre (`docs/cahier-des-charges.md` §12) :

| Écran | Entités |
|---|---|
| A. Connexion | `users` |
| B. Sidebar équipes/canaux | `teams`, `channels`, `channelmembers` |
| C. Canal et envoi de message | `posts` |

Soit **5 tables sur 95**. Hors périmètre au premier tour : recherche, fichiers, réactions,
fils de discussion. Le temps réel entre au lot 6.

La liste n'est pas produite par la capture : la capture la **vérifie**. Une opération
observée hors périmètre est un signal à traiter — élargir est une décision datée, en commit,
jamais un effet de bord d'un run.

**Première mesure du lot 1, avant même le premier diff** : rejouer deux fois le même scénario
et compter les endpoints exercés. Si le nombre varie, le dénominateur de `VER-05` varie avec
lui, et « 100 % de couverture » ne veut rien dire tant que cette variation n'est pas
expliquée. Un périmètre arrêté est un périmètre dont le décompte est stable.

*La cible est épinglée avant la première capture.* `CAP-07` exige que la trace porte « la
version de la cible observée » : une image Docker par *digest*, pas par étiquette, et la
configuration générée au premier démarrage figée et versionnée. Sans cela, le run A/A compare
deux exécutions dont rien ne garantit qu'elles ont observé la même cible, et le plancher de
bruit qu'il établit ne veut rien dire.

*Risques connus* : identifiants aléatoires de 26 caractères en z-base-32 et horodatages en
epoch ms (traités par D1) ; sources sous AGPL-3.0 ou licence commerciale, binaires sous MIT,
parties sous Apache-2.0 (`docs/architecture.md` §13) et **marque protégée — toute
démonstration publique devra rebrander** ; configuration générée au premier démarrage, à
figer et versionner ; le compose officiel épingle par étiquette, le *digest* est à relever.

### 3.2 Deuxième cible — choisie pour ce qu'elle casse

Elle n'est pas choisie pour être facile. Elle doit retirer, une par une, les facilités de
l'étalon : **pas de code source**, donc `CAP-08` inopérante ; **pas de reset**, donc pas de
run A/A gratuit ; **budget de requêtes réel et protections anti-robot**, donc `CAP-05` et
`CAP-09` exerçables ; **identifiants et horodatages de forme différente**, pour éprouver la
liaison symbolique de D1 sur autre chose que du z-base-32 et de l'epoch-ms.

### 3.3 Troisième cible — la seule qui rende `NF-01` mesurable

`NF-01` exige un délai de bout en bout mesuré **sur trois cibles consécutives**. Deux ne
suffisent pas : le critère resterait inatteignable, ce qui est le défaut qu'on corrige ici.
La troisième cible est donc au lot 6, et c'est elle qui clôt le chronomètre.

## 4. Lots

Chaque lot a un critère de sortie **falsifiable**. Ce dépôt part vide : **rien n'est fait.**

**Les lots ne sont pas chiffrés en jours.** Le code est écrit par des agents, et une charge
d'écriture ne borne plus rien. Ce qui borne un lot, c'est ce qui ne se parallélise pas, et
chaque lot en porte le relevé sous *Charge* :

- les **décisions humaines bloquantes**, points de synchronisation que personne d'autre ne
  prend — périmètre, ratification d'une décision de spec, choix d'une cible ;
- les **exécutions à durée machine** que le critère de sortie exige — cycles de reset,
  environnements simultanés, campagne jusqu'à son critère d'arrêt, rejeux sous le budget
  `CAP-05`, qui est une borne de calendrier par construction ;
- le **plafond de jetons**, fixé avant le lancement du lot et publié avec ses chiffres de
  sortie — la pratique de `LLM-04` dès le lot 1, sans attendre le bloc qui la porte ;
- le **nombre d'itérations de réparation**, que le lot 1 publie et que chaque lot suivant
  compare au précédent.

Tant que l'oracle n'existe pas — lots 1 et 2 —, le seul critique des agents qui l'écrivent
est la spécification gelée et son relecteur humain. Le débit de ces deux lots est donc celui
de la relecture, quel que soit le nombre d'agents. Une version antérieure de ce plan
libellait les lots en jours-homme, ≈28 pour les cinq premiers ; ces chiffres mesuraient un
auteur qui n'est plus celui du code.

### Lot 1 — Le vertical agentique

Un seul écran — la connexion — parcouru de bout en bout, et **le clone est écrit par
l'agent**, pas à la main.

*Blocs livrés* : `observe/drive`, `observe/normalise`, `observe/store`, `infer/surface`,
`infer/entities`, `build/scaffold`, `orchestrate/loop`, `judge/replay`, `judge/diff`,
`judge/mutate`.

`infer/entities` est ici et non plus tard : `GEN-01` demande un schéma SQL, et un schéma SQL
ne se dérive pas d'un OpenAPI sans passer par les entités.

*Exigences* : `CAP-01`, `CAP-02`, `INF-01`, `GEN-01`, `GEN-02`, `VER-01`, `VER-11`.

Premier test à faire, avant tout le reste : **`mitmproxy2swagger` produit-il un OpenAPI
assez fidèle pour que Prism serve quelque chose d'utile ?** Une heure. Si non,
`infer/surface` change de nature et le lot avec.

*Prism ne disparaît pas, il change de rôle.* Il n'est plus le clone : il est le **témoin**,
l'implémentation à coût nul qui mesure ce que l'OpenAPI inféré porte à lui seul. L'écart
entre le témoin et le clone agentique est l'apport mesuré de l'agent.

*La chaîne outillée, et son seul maillon nu* : HAR → `mitmproxy2swagger` → OpenAPI →
`datamodel-code-generator` (`--output-model-type pydantic_v2.BaseModel`) → **schéma SQL :
aucun générateur, l'agent écrit** → Alembic. Ce maillon est inscrit au §11 de l'architecture.

*Charge* — décisions bloquantes : les entrées de la spec (`tests/spec/README.md`, fixtures
contre cible vivante) et la ratification des décisions n°1 à 4 de ce même fichier, toutes
avant la première ligne de bloc ; `scope.yaml` arrêté ; le *digest* de l'image épinglé.
Exécutions : deux captures A/A, puis autant de rejeux sur le clone que d'itérations de
réparation. Plafond de jetons fixé avant lancement. Mesure : les itérations elles-mêmes.

*Commande* : `make lot1` — elle sort en erreur tant que le critère n'est pas tenu.

*Critère de sortie* : **trois chiffres**, publiés ensemble ou pas du tout.

1. La liste d'écarts cible↔clone, reproductible, chaque écart portant la trace qui le produit.
2. Le taux de détection de l'oracle sur le jeu de fautes semées initial (`VER-11`).
3. **Le nombre d'itérations de réparation avant convergence** — le seul chiffre qui dise si
   l'outil généralise, et la raison d'être de ce lot.

*Ce que ce lot ne prétend pas* : le premier chiffre ne vaut que ce que vaut le deuxième, et
le deuxième n'est pas encore durci — c'est le lot 2.

### Lot 2 — L'oracle opposable

Durcir ce que le lot 1 a produit à la va-vite, en le dimensionnant sur des écarts réels.

*Blocs livrés* : `observe/redact`, `judge/policy`, `judge/screen`.

*Exigences* : `CAP-03`, `CAP-07`, `VER-02`, `VER-06`, `VER-07`, `VER-10`, `NF-06`.

- `observe/redact` — purger en **liant**, pas en supprimant : un secret remplacé par une
  constante casse la trace comme référence de comparaison. Deux pièges à éviter par
  construction : une liste de *rétention* d'en-têtes se comporte comme une passoire dès qu'un
  en-tête inattendu apparaît, là où une liste de purge échoue du bon côté ; et un secret peut
  voyager dans un corps de requête aussi bien que dans un en-tête.
- `judge/policy` — la politique d'équivalence est un fichier **lu par le code**, compilé
  vers les paramètres DeepDiff. Une politique que rien ne parse est un document, pas une
  politique. Le test qui l'établit : modifier une entrée du fichier doit changer le verdict.
- `judge/screen` — comparaison d'écran par instantané ARIA, gabarit produit depuis la cible.

*Charge* — décisions bloquantes : le format de la politique et du relevé A/A (décision n°5
de la spec) et le lieu du jeu de fautes (`docs/architecture.md` §10.8). Exécutions : une
campagne complète en CI cible éteinte par candidat de comparateur, et une par faute semée.
Plafond de jetons : celui de l'écriture des blocs seulement — aucune boucle de réparation ne
tourne dans ce lot, le clone n'y change pas.

*Commande* : `make lot2` — elle sort en erreur tant que le critère n'est pas tenu.

*Critère de sortie* : le taux de détection vaut **100 %** ; la campagne tourne en CI cible
éteinte ; aucune trace ne contient de secret, vérifié par un test ; la politique est lue par
le code, chaque entrée citant un run A/A reproductible ; et **un test établit que le jeu de
fautes semées n'est pas accessible au générateur** (`VER-11`).

*Échec du lot* : un taux inférieur à 100 % sur des fautes aussi grossières signifie que
l'oracle est une passoire, et que le comparateur est à reprendre avant tout élargissement.

### Lot 3 — La deuxième cible

**Le lot qui décide si replikit est un outil ou un banc.** Il vient avant le runtime, parce
qu'un runtime construit pour une seule cible est un runtime pour une seule cible.

*Blocs livrés* : `observe/budget`, `observe/ingest`, `infer/provenance`.

*Exigences* : `CAP-05`, `CAP-08`, `CAP-09`, `INF-02`, `INF-03`, `INF-04`.

`CAP-08` entre ici et non plus tôt : c'est le contraste entre une cible libre, dont on dérive
le schéma depuis la source, et une cible propriétaire, dont on ne dérive rien, qui donne à
l'exigence son sens. Elle alimente `infer`, jamais `judge` (D6).

*Charge* — décisions bloquantes : le choix de la cible 2 (§3.2), la forme du run A/A sans
reset (`docs/architecture.md` §10.6) avant toute politique, et le budget `CAP-05` de la
cible, qui fixe le nombre de rejeux par jour. Exécutions : c'est ce budget qui borne le lot,
pas les agents — chaque rejeu A/A, chaque capture et chaque rejeu de dérive le consomment.
Ce lot est le premier dont la durée est dictée par la cible.

*Commande* : `make lot3` — elle sort en erreur tant que le critère n'est pas tenu.

*Critère de sortie* : la même chaîne, **sans modification propre à la cible sous les sept
paquets**, produit une liste d'écarts et un taux de détection sur une cible sans code source,
sans reset et sous budget de requêtes ; et **le nombre de lignes ajoutées sous
`targets/<cible2>/` est publié** — c'est la mesure de généricité, et la seule.

*Échec du lot* : toute ligne ajoutée sous `observe/`, `infer/`, `build/` ou `judge/` pour
faire passer la cible 2 est un aveu que le bloc connaissait la cible 1.

### Lot 4 — L'inférence et la boucle industrialisées

*Blocs livrés* : `infer/behavior`, `infer/merge`, `infer/rank`, `infer/deps`,
`build/implement`, `build/preserve`, `build/seed`, `run/determinism`, `orchestrate/schema`,
`orchestrate/trace`, `orchestrate/budget`, `orchestrate/parallel`, `orchestrate/evalset`.

`run/determinism` est ici parce que `NF-05` l'exige, et que `NF-05` est ce qui rend les deux
chiffres de ce lot comparables d'une itération à l'autre.

*Exigences* : `INF-05`, `INF-06`, `INF-07`, `INF-08`, `GEN-03`, `GEN-04`, `GEN-05`, `GEN-06`,
`GEN-07`, `GEN-08`, `GEN-11`, `LLM-01`, `LLM-02`, `LLM-03`, `LLM-04`, `LLM-05`, `LLM-06`,
`NF-05`.

`orchestrate/loop` existe depuis le lot 1 sous sa forme minimale ; ce lot lui ajoute ce que
`LLM-02` à `LLM-06` exigent — schémas aux frontières, journalisation, budget, parallélisme,
jeu d'évaluation — et rien de plus. Le pipeline reste étagé : pas de cadriciel d'agents
(`docs/architecture.md` §12).

*Charge* — décisions bloquantes : aucune nouvelle ; les amendements humains de `INF-07`
sont un flux, pas un point de synchronisation. Exécutions : L* actif sous budget `CAP-05`
sur la cible 2, et les trois chiffres du lot 1 sur les deux cibles. Plafond de jetons : le
plus élevé du plan, puisque ce lot fait tourner la boucle sur deux cibles ; `LLM-04` en fait
un bloc, il était une pratique depuis le lot 1.

*Commande* : `make lot4` — elle sort en erreur tant que le critère n'est pas tenu.

*Critère de sortie* : les trois chiffres du lot 1, **sur les deux cibles**, avec le nombre
d'itérations en baisse ou expliqué.

### Lot 5 — Le runtime et la surface

*Blocs livrés* : `run/sandbox`, `run/branch`, `run/admin`, `run/sideeffects`, `run/journal`,
`run/fleet`, `run/faults`, `serve/parity`, `serve/mcp`, `serve/errors`, `serve/client`,
`serve/contract`.

*Exigences* : `RUN-01` à `RUN-08`, `RUN-10`, `RUN-13`, `GEN-09`, `API-01` à `API-07`,
`API-09`, `API-10`, `NF-02`, `NF-03`, `NF-04`, `NF-07`, `NF-08`.

`run/faults` et `serve/contract` ne servent que `RUN-09` et `API-08`, qui sont des
extensions : ces deux blocs ne sont livrés que si l'extension correspondante est retenue.
`run/fleet` est livré dans tous les cas — il porte `RUN-08` et la vue de portefeuille de
`NF-08` — et `RUN-14` ne lui ajoute la supervision que si elle est retenue. Le reste du lot ne
dépend d'aucune extension.

Trois exigences de ce lot se ratent de la même façon, et il faut le dire avant de les
écrire. `RUN-03` (isolation) et `RUN-05` (hors ligne) se « démontrent » facilement par une
lecture de code, ce qui ne démontre rien : leur critère de sortie exige une exécution.
`RUN-13` se viole **arithmétiquement** dès qu'un environnement copie la base entière — le
coût marginal vaut alors 100 % contre un plafond de 5 %, quel que soit le soin apporté au
reste. Le partage de blocs de `run/branch` est ce qui la rend atteignable, sous la réserve
du §10.5 de l'architecture.

*Charge* — décisions bloquantes : le système de fichiers de `run/branch`, choisi avant la
première mesure puisque le plafond de 5 % n'est une propriété d'aucun outil
(`docs/architecture.md` §10.5), et le sort des trois extensions. Exécutions : ce lot est
presque entièrement à durée machine — 100 cycles de reset, 100 environnements simultanés,
une charge à la volumétrie `NF-02`, une réinitialisation chronométrée au 95e centile. Les
agents écrivent le banc, le banc prend le temps qu'il prend.

*Commande* : `make lot5` — elle sort en erreur tant que le critère n'est pas tenu.

*Critère de sortie* : un environnement démarre et sert son périmètre **réseau sortant
coupé** ; 100 environnements simultanés mesurés ; coût de stockage marginal mesuré sous 5 % ;
réinitialisation chronométrée sous 5 s au 95e centile à la volumétrie `NF-02` ; parité
UI↔API **mesurée** par `diff`, pas déclarée ; et le protocole `ACC-05` — 100 cycles, état
complet comparé — exécuté et consigné.

### Lot 6 — Concurrence, adversarial, acceptation, troisième cible

*Blocs livrés* : `observe/explore`, `observe/probe`, `build/realtime`, `build/migrate`,
`judge/adversary`, `judge/coverage`, `judge/distinguish`, `judge/drift`, `judge/edge`,
`judge/accept`.

*Exigences* : `CAP-04`, `CAP-06`, `CAP-10`, `CAP-11`, `GEN-10`, `GEN-12`, `RUN-11`, `VER-03`,
`VER-04`, `VER-05`, `VER-08`, `VER-09`, `NF-01`.

Concurrence et temps réel (modèle séquentiel + Porcupine/Elle), exploration adversariale,
couverture, indiscernabilité mesurée (D8), la **troisième cible**, et `judge/accept` — le
bloc qui produit les onze critères `ACC` et sans lequel aucun clone n'est livrable.

*Charge* — le lot le plus lourd, et le seul dont chaque forme de charge est présente.
Décisions bloquantes : la cible 3, le modèle séquentiel écrit à la main pour chaque cible
collaborative (`docs/architecture.md` §8), la reformulation d'`ACC-08` (D8), l'environnement
d'origine de `GEN-12`, et le relecteur d'`ACC-10` (§7). Exécutions : la campagne adversariale
jusqu'à son critère d'arrêt, le rejeu de dérive `VER-09` sous budget `CAP-05` sur trois
cibles, le C2ST à taille d'échantillon suffisante pour une valeur-p, et le chronomètre
`NF-01` sur la troisième cible. Un lot « à cadrer » dans une version antérieure : c'est ici
que se trouvait la moitié du travail que le libellé en jours ne montrait pas.

*Commande* : `make lot6` — elle sort en erreur tant que le critère n'est pas tenu.

*Critère de sortie* : `judge/accept` produit les **onze** critères `ACC` automatiquement et
les joint à la livraison ; `NF-01` est chronométré sur les **trois** cibles ; et le rapport
dit lesquels des onze sont tenus et lesquels ne le sont pas. Un lot 6 réussi n'est pas un lot
où tout passe : c'est un lot où chaque critère porte un verdict produit par une commande.
`ACC-10` y figurera en échec tant que personne ne tient le rôle qu'il exige (§7).

*Conséquence à écrire plutôt qu'à découvrir* : Mattermost est une cible collaborative, donc
`CAP-11`, `GEN-10`, `RUN-11` et `ACC-09` sont bloquantes pour elle. Tant que le temps réel et
le multi-acteur sont ici, **aucun clone produit avant n'est livrable au sens du §12**. C'est
acceptable pour un banc, à condition de ne pas le confondre avec une livraison.

*Une exigence de ce lot n'a pas d'objet dans ce dépôt.* `GEN-12` migre « les environnements
existants construits sur fichiers JSON à plat », et ce dépôt part de zéro (§6) : aucun
environnement d'origine n'existe ici, et en fabriquer un pour l'occasion contredirait
`GEN-01`. L'exigence reste bloquante et de socle — elle ne tombe pas parce que ce dépôt ne la
sollicite pas, même règle que `CAP-05` au lot 1 — et son critère ne s'exécute que sur un
environnement d'origine fourni de l'extérieur. Tant qu'il ne l'est pas, `make lot6` la
consigne en échec, au même titre qu'`ACC-10` (§7).

## 5. Couverture — blocs et exigences bloquantes par lot

Ce tableau est la carte que `tools/check_plan_coverage.py` recompte dans les deux sens : une
exigence bloquante sans lot est une erreur, un bloc de `docs/architecture.md` sans lot en est
une aussi. Une exigence citée dans une prose de justification n'est pas portée pour autant.

Une affectation « lot 6 » n'est pas un renvoi aux calendes : c'est un engagement à ne pas
déclarer un clone livrable avant, puisque le §12 du cahier conditionne les onze critères
`ACC` à ces exigences-là.

| Lot | Commande | Blocs livrés | Exigences bloquantes portées |
|---|---|---|---|
| **lot 1 — vertical agentique** | `make lot1` | `observe/drive` `observe/normalise` `observe/store` `infer/surface` `infer/entities` `build/scaffold` `orchestrate/loop` `judge/replay` `judge/diff` `judge/mutate` | `CAP-01`, `CAP-02`, `INF-01`, `GEN-01`, `GEN-02`, `VER-01`, `VER-11` |
| **lot 2 — oracle opposable** | `make lot2` | `observe/redact` `judge/policy` `judge/screen` | `CAP-03`, `VER-02`, `VER-06`, `VER-07`, `VER-10`, `NF-06` |
| **lot 3 — deuxième cible** | `make lot3` | `observe/budget` `observe/ingest` `infer/provenance` | `CAP-05`, `CAP-08`, `CAP-09`, `INF-02`, `INF-03`, `INF-04` |
| **lot 4 — inférence et boucle** | `make lot4` | `infer/behavior` `infer/merge` `infer/rank` `infer/deps` `build/implement` `build/preserve` `build/seed` `run/determinism` `orchestrate/schema` `orchestrate/trace` `orchestrate/budget` `orchestrate/parallel` `orchestrate/evalset` | `INF-05`, `GEN-03`, `GEN-04`, `GEN-05`, `GEN-06`, `GEN-07`, `GEN-08`, `GEN-11`, `LLM-01`, `LLM-02`, `LLM-03`, `NF-05` |
| **lot 5 — runtime et surface** | `make lot5` | `run/sandbox` `run/branch` `run/admin` `run/sideeffects` `run/journal` `run/fleet` `run/faults` `serve/parity` `serve/mcp` `serve/errors` `serve/client` `serve/contract` | `RUN-01`, `RUN-02`, `RUN-03`, `RUN-04`, `RUN-05`, `RUN-06`, `RUN-10`, `RUN-13`, `GEN-09`, `API-01`, `API-02`, `API-03`, `API-04`, `API-05`, `API-06`, `API-09`, `NF-02`, `NF-03`, `NF-04`, `NF-07` |
| **lot 6 — élargissement et acceptation** | `make lot6` | `observe/explore` `observe/probe` `build/realtime` `build/migrate` `judge/adversary` `judge/coverage` `judge/distinguish` `judge/drift` `judge/edge` `judge/accept` | `CAP-04`, `CAP-06`, `CAP-10`, `CAP-11`, `GEN-10`, `GEN-12`, `RUN-11`, `VER-03`, `VER-04`, `VER-05`, `VER-08`, `VER-09`, `NF-01` |

**Ce que ce tableau ne porte pas, et le dit.** Les exigences de priorité *Élevée* — `CAP-07`,
`INF-06` à `INF-08`, `RUN-07`, `RUN-08`, `API-07`, `API-10`, `LLM-04` à `LLM-06`, `NF-08` —
sont nommées dans le lot où elles tombent naturellement mais **ne conditionnent aucun critère
de sortie**. Les quatre extensions — `RUN-09`, `RUN-12`, `RUN-14`, `API-08` — ne sont pas
ordonnancées tant qu'elles n'ont pas été retenues, leur priorité étant conditionnelle
(`docs/cahier-des-charges.md` §3).

## 6. Ce dépôt part de zéro

**Aucun code n'est repris de nulle part.** Ce n'est pas une posture : trois contraintes de
l'architecture excluent la quasi-totalité de ce qui existe.

- **Les versions.** `VER-10` a besoin de Playwright **1.60** pour `aria_snapshot(boxes=True)`
  et `CAP-10` de la **1.48** pour `route_web_socket()`. Toute base épinglée en deçà rend deux
  exigences bloquantes inaccessibles sans migration.
- **D6.** Un banc qui appelle `docker exec … psql` pour lire l'état ne s'exécute sur aucune
  cible tierce : son régime par défaut est le régime privilégié, celui qui ne peut pas porter
  un verdict. C'est une propriété d'architecture, pas un détail d'implémentation, et elle se
  vérifie avant d'emprunter quoi que ce soit.
- **L'objet de la mesure.** Un harnais qui juge des **tâches contre l'environnement** ne se
  convertit pas en harnais qui juge l'**environnement contre la cible**. Ce n'est pas la même
  mesure ; les artefacts publics de ce domaine font le premier, `judge/` fait le second.

Ce qui compte est la connaissance, et elle est dans ces quatre documents.

## 7. Décisions en attente, et un échec assumé

**Reformuler `ACC-08`** en pouvoir discriminant borné plutôt qu'en compte de fuites (D8).
Ce n'est pas un affaiblissement — un seuil mesurable remplace un compte incomptable — mais
c'est une modification du cahier des charges, donc une décision de périmètre.

**Choisir la licence du projet.** Tranché le 01/09/2026 : **ce n'est pas un livrable
commercial**, ce qui lève la contrainte sur les dépendances copyleft — `edist` (GPLv3)
redevient disponible, l'AGPL cesse d'être un motif d'écartement, et OpenFastTrace (GPL-3.0)
redevient discutable au lot 4. Reste à choisir la licence que *replikit* porte lui-même.

**Fournir un environnement d'origine pour `GEN-12`.** L'exigence migre un existant que ce
dépôt n'a pas (lot 6). Qui le fournit, et sous quelle forme — un jeu de fichiers JSON et les
traces capturées dessus — est une décision de périmètre. Sans lui, `GEN-12` est consignée en
échec, pas retirée.

**Le jeu de fautes a besoin d'un lieu** hors du chemin de l'agent (`docs/architecture.md`
§10.8), et le run A/A d'une forme sur une cible sans reset (§10.6) avant le lot 3. Deux
décisions techniques, à prendre dans l'architecture, sans lesquelles les critères de sortie
des lots 2 et 3 reposent sur des tests qui ne vérifient qu'un import.

**`ACC-10` est en échec, et le reste.** Le critère exige une revue croisée par un Curriculum
Engineer. Personne ne tient ce rôle sur ce projet. La règle 1 interdit de détendre le critère
ou de le déclarer sans objet : il est donc **consigné en échec**, et aucun clone produit ici
n'est livrable au sens du §12 tant qu'un relecteur qualifié distinct de l'auteur du clone
n'a pas rendu son avis. C'est un échec honnête, préféré à un vert négocié.
