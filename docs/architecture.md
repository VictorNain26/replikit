# Architecture

Comment les 91 exigences de `docs/cahier-des-charges.md` sont portées par des blocs
composables, chacun adossé à un outil maintenu ou à un résultat publié.

Ce document porte le **comment** : limites assumées, décisions, blocs, outils. Le
**quoi** est dans `docs/cahier-des-charges.md`, le **quand** dans `docs/plan.md`, l'**état
mesuré** dans `docs/couverture.md`. Aucune de ces quatre matières n'est répétée ailleurs.

Il définit l'espace de noms `Dn`, `Pn` et les noms de blocs : aucun autre document ne crée
ni ne reformule une décision, un principe ou un bloc, il ne peut que les citer. Les numéros
de section sont des ancres — on ne renumérote jamais.

## 1. Limites assumées

Trois limites ne seront pas franchies. Les inscrire évite de promettre ce qu'aucune
méthode ne donne.

**L'oracle est négatif.** Une divergence est un candidat défaut ; l'accord ne prouve
rien (McKeeman 1998). S'y ajoute une défaillance en mode commun : le clone étant dérivé
de l'observation de la cible, l'oracle est aveugle exactement là où le clone est le plus
faux — hors du périmètre observé.

**L'équivalence est échantillonnée.** Bisimulation et équivalence de traces supposent un
système de transitions connu et pleinement observable. En boîte noire on ne dispose que
de deux traces concrètes par sonde. « Zéro écart » signifiera toujours « aucun écart sur
ce qui a été sondé » — c'est ce que D8 rend chiffrable au lieu de le laisser implicite.

**La couverture est circulaire.** Le modèle de référence est inféré des traces : « 100 %
de couverture » veut dire « 100 % de l'observé ». La W-method de Chow (1978) n'est
complète que sous une borne connue sur le nombre d'états, qu'aucun tiers ne fournit.
Böhme et al. (FSE 2021) montrent que les estimateurs de risque résiduel en campagne
adaptative sous-estiment systématiquement le risque réel.

## 2. Principes

**P1 — Un seul objet circule : l'artefact sur disque, adressé par son contenu.**
Chaque bloc est une fonction `artefacts -> artefacts`. Aucun bloc n'en appelle un autre.
Le cache, la reprise, la campagne hors ligne (`NF-06`) et la reproductibilité (`NF-05`)
en découlent au lieu d'être construits.

**P2 — Les formats entre blocs sont des standards.** HAR pour les traces, OpenAPI pour
la surface, JSON Schema pour les entités, un automate sérialisé pour le comportement, le
format d'historique de Jepsen pour la concurrence. Un format maison est un bloc qu'on ne
peut plus remplacer.

Précision qui a déjà coûté une décision : écarter `routeFromHAR` comme **moteur de
rejeu** ne dit rien du HAR comme **format**. Le HAR porte même les trames WebSocket, via
`_webSocketMessages` (Chrome) et `_messages` (Firefox) — extensions non normalisées, avec
une inadéquation structurelle réelle : un message WebSocket n'est pas une paire
requête/réponse.

**P3 — Une seule frontière de confiance, vérifiable par `grep`.** Les blocs qui
**proposent** peuvent appeler un modèle. Les blocs qui **prononcent** ne le peuvent pas.
Aucun import de client LLM sous `judge/`.

**P4 — Tout bloc a un substitut tiers nommé.** Là où je n'en trouve pas, la ligne le dit,
et c'est là seulement qu'on écrit du code.

## 3. Décisions

Huit décisions engagent l'architecture. Chacune est fondée sur un travail existant et a
un coût.

### D1 — Une trace est un scénario paramétré, jamais un flux d'octets

Chaque valeur produite par le système est liée à une **variable symbolique** à sa
première apparition ; toute réapparition doit référencer la même variable.

*Fondement* : Hammoudi, Rothermel, Tonella (ICST 2016) mesurent 722 ruptures de rejeu sur
300 versions, dont plus de 73 % dues aux ancrages — **la part de 73 % n'est pas vérifiée**, §13.

*Ce que ça apporte* : ce n'est pas un masquage mais une **vérification de cohérence
référentielle**, strictement plus forte qu'ignorer le champ. Un clone qui renverrait deux
identifiants différents pour le même objet échoue ; un masquage le laisserait passer.

*Coût* : le lieur de variables est maison. Aucun outil de cassette ne le fait.

### D2 — Aucune neutralisation sans mesure préalable

**Un champ ne peut être neutralisé que si un run A/A a démontré qu'il varie.** Tout le
reste doit correspondre exactement.

*Fondement* : Diffy (Twitter) fait tourner une instance *secondary* copie du *primary* ;
le désaccord primary↔secondary mesure le bruit pur et rend interprétable le désaccord
primary↔candidate. Le code de Diffy est écarté (CC-BY-NC-ND), l'idée est conservée.

*La forme que prend la violation* : elle ne se présente jamais comme un affaiblissement.
Elle se présente comme un opérateur qui rend le diff moins bruyant — `eq` aliasé sur une
recherche de sous-chaîne, un seuil de similarité fixé à une valeur plausible et jamais
déclarée. Chacune est défendable prise isolément, aucune n'est mesurée, et ensemble elles
transforment l'oracle en tampon. C'est pourquoi D2 ne porte pas sur l'intention mais sur la
preuve : **une neutralisation sans run A/A qui la justifie est refusée, même si elle a
l'air juste.**

*Mise en œuvre* : `diff(cible, cible)` — la politique est **dérivée** d'un appel, pas
déclarée à vue.

### D3 — Déterminiser à la source, plutôt que masquer à la comparaison

Toute neutralisation inscrite dans la politique doit être justifiée comme un **échec de
déterminisation**, pas comme une variation constatée.

*Fondement* : le `deterministic.js` de Web Page Replay réécrit `Math.random` en
générateur à graine fixe et fait avancer `Date` de 50 ms toutes les 25 constructions.
C'est `RUN-04`, et `libfaketime` le fait aujourd'hui sans toucher au code.

### D4 — Valider l'oracle par injection de fautes

Un jeu de fautes semées, et un **taux de détection publié à côté du nombre d'écarts**.
« 0 écart » sans taux de détection ne veut rien dire.

*Fondement* : Jahangirova et al. (ISSTA 2016) utilisent le test pour révéler les faux
positifs d'un oracle et la mutation pour révéler ses faux négatifs. Just et al. (FSE 2014)
établissent la corrélation entre mutants et fautes réelles.

*Ce que 2026 y ajoute, et qui devient `VER-11`* : le taux de détection n'est pas une mesure
qu'on prend une fois. Dès lors que la liste d'écarts sert de retour à un agent qui écrit le
clone, elle devient sa fonction de récompense — et une récompense fixe se fait optimiser.
*The Verification Horizon* (arXiv 2606.26300) l'énonce pour les agents de code : « *no fixed
reward function can remain effective as policy capability continues to grow ; verification
must co-evolve with the generator* ». D'où deux règles, portées par `VER-11` : le taux est
republié à chaque campagne, et **le jeu de fautes n'est jamais exposé au générateur**. Un
générateur qui voit les fautes semées apprend les fautes. *Before the Model Learns the Bug :
Fuzzing RLVR Verifiers* (arXiv 2606.01066) construit sa méthode sur exactement ce risque.

*Mise en œuvre* : `diff(cible, mutate(cible))` — encore un appel du même bloc.

### D5 — Oracle d'écran structurel, pas pixel

Comparaison par instantanés ARIA et géométrie **relative aux voisins immédiats** ; le
pixel n'est qu'un signal secondaire, jamais un critère d'échec.

*Fondement* : X-PERT (ICSE 2013) obtient 76 % de précision et 95 % de rappel avec
`diffRelativeLayouts` — **chiffres non vérifiés**, §13 —, et montre que les incompatibilités de structure dominent. Les
seuils par défaut des outils d'image sont des aveux : pixelmatch 0,1, Playwright 0,2,
Chromatic 0,063 « pour équilibrer contre les artefacts comme l'antialiasing ».

*Ce que Playwright 1.59/1.60 change* : `ariaSnapshotJSON` rend l'arbre comme objet JSON, avec
`box` en propriété, et `mode: "ai"` produit un instantané pensé pour la consommation par un
modèle, références d'éléments comprises. La conséquence est que `judge/screen` n'a pas à
analyser le YAML `[box=…]` : il consomme une structure. Ce qui reste maison est la **géométrie
relative** — les `box` sont exprimés par rapport à la fenêtre, jamais aux voisins — et c'est
tout ce qui reste maison.

*Coût* : on renonce à détecter les régressions purement visuelles. Pour un environnement
d'agents, c'est le bon arbitrage : l'agent lit la structure.

### D6 — Aucun privilège sur la cible ne porte un verdict

**Un accès qu'une cible tierce ne donnera pas — sa base, son reset, son code source — ne
peut pas porter une comparaison qui sert de verdict. Il sert à étalonner cette
comparaison et à borner ce qu'elle laisse passer.** Les privilèges sur le **clone** nous
appartiennent : `RUN-02` et `RUN-06` les exigent.

*Fondement* : `docs/cahier-des-charges.md` §9.1 — l'oracle principal est un corpus de traces
figées, le rejeu réel est réservé à la validation et à la détection de dérive. `NF-06`
rend cette lecture impérative : la campagne doit tourner à chaque modification sans accès
à la cible.

*Frontière utile* : le code source alimente l'**inférence** — `CAP-08` l'exige — jamais
l'**oracle**, qui rend son verdict sur ce qu'un navigateur observe.

### D7 — Un modèle propose, il ne prononce jamais

*Fondement* : Kambhampati et al. (ICML 2024) établissent que la solidité d'une boucle
générer-tester-critiquer vient des **critiques sains**, et qu'un modèle auto-régressif ne
s'auto-vérifie pas. Côté oracles de test : TOGLL rapporte 7 % de faux positifs sur
les oracles d'exception et 25 % sur les oracles d'assertion — **chiffres non vérifiés**, §13 —
et c'est l'état de l'art.
Un `ACC-01` à « 0 écart » adossé à un juge faux une fois sur quatre ne mesure rien.

*Corollaire* : le clone est écrit par un agent, jugé par du code. La liste d'écarts **est**
le retour de réparation de l'agent — c'est la boucle `LLM-01`, et son critique sain est
`judge/diff`.

*Ce qui fixe le rendement de cette boucle* : Olausson et al. (ICLR 2024) mesurent que
l'auto-réparation apporte des gains modestes voire nuls quand le modèle produit lui-même son
retour, et « substantially larger » quand la qualité du retour est relevée par un critique
plus fort. Le rendement de `LLM-01` est donc une fonction de `judge/diff`, pas du modèle.
Même papier, réserve à retenir pour `LLM-04` : à petit budget, l'échantillonnage i.i.d. sans
réparation fait parfois aussi bien.

*Forme du pipeline, pas cadriciel* : `Agentless` montre qu'un pipeline étagé localiser →
réparer → valider dépasse beaucoup d'agents sur SWE-bench pour un coût inférieur d'un ordre
de grandeur. `orchestrate/loop` est donc un enchaînement d'appels sous `make`, et OpenHands
comme SWE-agent sont écartés au §12.

*Ce que la rétro-ingénierie assistée par IA confirme* : `LLM4Decompile` et
`Decompile-Bench` (NeurIPS 2025) notent par **recompilabilité et ré-exécutabilité**,
jamais par similarité de code — 64,94 % de ré-exécutabilité pour `LLM4Decompile-9B-v2`,
39,48 % sur `DCBench` contre 46,79 % pour Claude. Le sous-domaine le plus mûr de l'IA
appliquée à la rétro-ingénierie juge par l'exécution et tourne autour de la moitié. Il
faut dimensionner pour un générateur qui a raison une fois sur deux : **la qualité vient
de la boucle, pas du modèle.**

### D8 — L'indiscernabilité se mesure, elle ne se compte pas

Le compte d'écarts est un oracle **négatif** : il trouve des défauts, il ne borne rien.
À côté de lui, la propriété que le §1 du cahier demande — « un agent ne doit pas pouvoir
distinguer le clone de la cible » — est un **test à deux échantillons**.

*Fondement* : le Classifier Two-Sample Test (Lopez-Paz & Oquab, ICLR 2017). On entraîne
un classifieur à séparer les observations issues de la cible de celles issues du clone.
Si son exactitude en test ne dépasse pas le hasard, les deux sont indiscernables **pour
ce classifieur, ce jeu de traits et cette taille d'échantillon**. La statistique a une
distribution asymptotique connue, donc une valeur-p. SandPrint (RAID 2016) applique
exactement ce schéma pour séparer un bac à sable d'un système réel.

*Ce que ça change* : deux critères d'acceptation aujourd'hui invérifiables deviennent des
mesures avec intervalle de confiance. `ACC-01` (« 0 écart ») garde son sens de liste de
défauts ouverts, et gagne une borne agrégée. `ACC-08` (« 0 fuite de simulation ») cesse
d'être un compte de ce qu'on n'a pas cherché.

*Ce que ça ne remplace pas* : le classifieur ne dit pas **quoi** corriger. Les deux
oracles sont complémentaires — la liste d'écarts est le diagnostic, le C2ST est le
pronostic.

*Décision produit en attente* : reformuler `ACC-08` en pouvoir discriminant borné exige
de modifier le cahier des charges. Ce n'est pas un affaiblissement — un seuil mesurable
remplace un compte incomptable — mais c'est une décision de périmètre, pas une décision
technique. Elle n'est pas prise ici.

## 4. Les sept paquets

Un paquet par section du cahier des charges. Ce n'est pas une coquetterie : c'est ce qui
rend la couverture recomptable.

```
observe/       cible          -> traces            (CAP)
infer/         traces         -> spécification     (INF)
build/         spécification  -> clone             (GEN)
run/           clone          -> environnements    (RUN, NF)
serve/         clone          -> surface agent     (API)
judge/         cible x clone  -> écarts            (VER, ACC)   -- zone sans LLM
orchestrate/   la boucle                           (LLM)
```

`targets/<cible>/` reste le seul endroit spécifique à une cible : déploiement, amorçage,
scénario, `scope.yaml`, `equivalence.yaml`. Rien sous les sept paquets ne connaît une
cible.

## 5. Les trois réutilisations qui font l'architecture

La modularité utile n'est pas dans les interfaces, elle est dans les blocs qui reviennent.

**`judge/diff` s'applique cinq fois à la même signature.**

| Appel | Ce qu'il donne | Exigence |
|---|---|---|
| `diff(cible, cible)` | le plancher de bruit, dont la politique est **dérivée** | `CAP-02`, `VER-02`, D2 |
| `diff(cible, mutate(cible))` | le taux de détection de l'oracle | D4, `VER-07` |
| `diff(cible, clone)` | le verdict | `VER-01` |
| `diff(état après UI, état après API)` | la parité de surface | `API-06` |
| `diff(origine JSON, migré SQL)` | la migration vérifiée | `GEN-12` |

Deux des huit décisions cessent d'être des règles de discipline pour devenir des appels
de fonction.

**`observe/drive` s'applique trois fois.** Capturer sur la cible, rejouer sur le clone,
et faire agir un second acteur (`RUN-11`) : le même bloc, pointé ailleurs.

**`infer/surface` alimente quatre consommateurs.** L'OpenAPI inféré sert à générer le
squelette du clone, les descripteurs d'outils, les cas limites et les séquences
d'exploration.

## 6. Le rejeu, tranché

Un script Playwright câblé sur les sélecteurs DOM de la cible ne pilotera jamais un clone,
sauf à exiger que le clone copie ces sélecteurs — l'outil de vérification dicterait alors
l'implémentation.

**Le scénario est écrit en intentions.** Stagehand (`act` / `observe` / `extract`) résout
une intention en action concrète par implémentation. Réserve dirimante : un modèle dans la
boucle de rejeu réinjecte du non-déterminisme dans l'oracle, ce que P3 interdit. Forme
retenue : **résoudre l'intention une fois par implémentation, figer le sélecteur obtenu
dans le scénario, rejouer en déterministe.** Le modèle écrit le scénario, il ne l'exécute
jamais.

## 7. L'inférence, tranchée

L'apprentissage actif d'automates a besoin d'un **alphabet** d'actions abstraites, d'un
**mapper** du symbole vers l'exécution concrète, et d'un **oracle**.

Le modèle est bon pour les deux premiers, mauvais pour le troisième. *Can LLM Agents Infer
World Models?* (arXiv 2606.16576) met des agents en situation d'apprentissage actif : la
performance s'effondre quand l'automate grossit, et les agents restent « far less robust
and efficient than classic algorithms ». Modes d'échec nommés : planification des requêtes,
intégration des preuves, construction d'hypothèses.

**L'agent fournit l'alphabet et le mapper ; L* apprend ; l'exécution tranche.** AALpy
(TU Graz) porte L*, KV et RPNI en Python. ALEX (TU Dortmund, sur LearnLib) fait déjà
« inférer des modèles d'automates d'applications web et de services web JSON » en mode
mixte REST + Selenium, mais en JVM — et **son dépôt est figé depuis le 05/08/2024**, alors que
LearnLib lui-même reste actif. On lit ALEX comme un précédent de méthode, pas comme une
dépendance disponible.

Même principe pour l'exploration. Une étude empirique de 2026 (arXiv 2606.16650) mesure, à
budget égal sur six applications : couverture de code RL 57,60 %, model-based ~49-50 %,
LLM (GPTWeb) 49,39 % ; défaillances uniques 33 pour WebExplor contre 24 pour GPTWeb.
L'agent exécute trois à quatre fois moins d'actions à cause du coût d'inférence, et les
familles trouvent des défauts **complémentaires**. L'agent complète l'exploration — il
atteint les états qu'un crawler ne sait pas ouvrir — il ne la remplace pas.

## 8. La concurrence, tranchée

Le temps réel et le multi-acteurs étaient le trou principal. Ils se comblent par des outils
existants, à condition de séparer trois questions qu'on confondait.

**Capturer et rejouer les trames.** `page.route_web_socket()` existe dans Playwright depuis
la 1.48 : interception, modification, blocage, et `connect_to_server()` pour laisser passer.
On capture les trames en observation, on les sert en rejeu. Le HAR les porte en extension
(P2).

**Ordonner les acteurs.** N contextes navigateur pilotés par `observe/drive`, horloge
commune fournie par `run/determinism`. L'ordre relatif entre acteurs est un produit de
l'horloge, pas une reconstruction.

**Rendre le verdict.** C'est ici que la formalisation compte, et elle a des outils.
Une exécution concurrente ne se compare pas trame à trame : elle se vérifie contre un
**modèle séquentiel**. Porcupine (Go, MIT) prend un modèle exécutable et un historique et
décide la linéarisabilité — mesuré 1000 à 10 000 fois plus rapide que Knossos sur les
données Jepsen. Elle (Jepsen, VLDB 2021) vérifie les anomalies d'isolation par détection
de cycles sur des centaines de milliers de transactions en dizaines de secondes, et se
consomme hors JVM en écrivant l'historique dans un fichier lu par un programme enveloppe.

*Ce qui reste vrai* : le modèle séquentiel est écrit à la main, une fois par cible, et la
décision est NP-complète dans le cas général. Ce qui change, c'est que ce n'était pas
« hors d'atteinte » — c'est un modèle à écrire et deux bibliothèques à brancher.

## 9. Couverture des 91 exigences

Une ligne par exigence. `o` marque une extension. Une case *maison* signale l'absence de
substitut tiers trouvé.

### Capture (CAP)

| Réf | Bloc | Outil / fondement |
|---|---|---|
| CAP-01 | `observe/drive` | Playwright >= 1.60 ; scénario en intentions figées (§6) |
| CAP-02 | `judge/diff` | l'appel A/A ; le non-déterminisme est un produit du diff, pas une capture |
| CAP-03 | `observe/redact` | expurgation **liante** (placeholders betamax) ; `detect-secrets` en garde-fou |
| CAP-04 | `observe/explore` | parcours : Crawlee (Playwright, actif) ; le graphe d'états de Crawljax reste la référence de méthode mais l'outil est **dormant depuis la 5.2.3, 01/06/2023** ; agent en complément (arXiv 2606.16650) |
| CAP-05 | `observe/budget` | jeton de débit, arrêt d'urgence — **maison**, ~60 lignes |
| CAP-06 | `observe/probe` | Schemathesis depuis l'OpenAPI inféré, + sondes de formulaire |
| CAP-07 | `observe/store` | HAR adressé par contenu, estampillé version de cible ; `syrupy` en CI |
| CAP-08 | `observe/ingest` | dépôt source -> migrations et schéma ; alimente `infer`, jamais `judge` (D6) |
| CAP-09 | `observe/budget` | détection anti-robot, arrêt, état partiel préservé, alerte opérateur |
| CAP-10 | `observe/drive` | `page.route_web_socket()` (Playwright 1.48+) ; trames en extension HAR |
| CAP-11 | `observe/drive` | N contextes navigateur, horloge commune `run/determinism` (§8) |

### Inférence (INF)

| Réf | Bloc | Outil / fondement |
|---|---|---|
| INF-01 | `infer/surface`, `infer/entities` | `mitmproxy2swagger` (HAR -> OpenAPI) ; `genson` (payloads -> JSON Schema) |
| INF-02 | `infer/provenance` | chaque assertion porte l'identifiant de la trace qui la fonde |
| INF-03 | `infer/provenance` | marquage *non observé* ; remonte en dette de capture, jamais comblé |
| INF-04 | format de spécification | OpenAPI + JSON Schema + automate, validés par schéma (P2) |
| INF-05 | `infer/behavior` | AALpy : RPNI passif sur le corpus, puis L* actif sous budget `CAP-05` |
| INF-06 | `infer/behavior` | contradiction = contre-exemple qui ne stabilise pas l'hypothèse ; signalée |
| INF-07 | `infer/merge` | fusion à trois branches ; les amendements humains sont une branche |
| INF-08 | `infer/rank` | fréquence observée -> périmètre hiérarchisé ; produit le candidat `scope.yaml` |

### Génération (GEN)

| Réf | Bloc | Outil / fondement |
|---|---|---|
| GEN-01 | `build/scaffold` | schéma SQL + migrations dérivés de `infer/entities` |
| GEN-02 | `build/scaffold` | couche d'accès typée dérivée de `infer/entities` ; contraintes appliquées par la base. Prism ou Microcks servent l'OpenAPI comme **témoin**, jamais comme clone (`docs/plan.md` lot 1) |
| GEN-03 | `build/implement` | agent : messages d'erreur au caractère près ; vérifié par `judge/diff` |
| GEN-04 | `build/implement` | écrans communs réutilisés, spécialisation par cible |
| GEN-05 | `build/seed` | Greenmask, moteur `hash` = déterministe à paramétrage identique |
| GEN-06 | `build/preserve` | ajustements manuels en fichiers séparés ; non-destruction testée |
| GEN-07 | `build/implement` | comportements asynchrones observés, délais compris |
| GEN-08 | `build/implement` | rôles et autorisations, y compris fuites par différence de message |
| GEN-09 | `build/seed` | Greenmask : sous-ensemble et génération à l'échelle du tenant |
| GEN-10 | `build/realtime` | canaux servis ; vérifiés par Porcupine / Elle contre un modèle séquentiel (§8) |
| GEN-11 | `build/implement` | ordre de tri ; détecté par `judge/diff` (DeepDiff `verbose_level=2`) |
| GEN-12 | `build/migrate` | JSON à plat -> relationnel, vérifié par `diff(origine, migré)` |

### Exécution (RUN)

| Réf | Bloc | Outil / fondement |
|---|---|---|
| RUN-01 | `run/sandbox` | Firecracker : restauration d'instantané annoncée en 5-30 ms — **non mesurée ici**, §13 |
| RUN-02 | `run/sandbox` | instantané à un instant quelconque, réamorçable |
| RUN-03 | `run/branch` | partage de blocs : instantanés btrfs/ZFS, ou PostgreSQL 18 `CREATE DATABASE … STRATEGY = FILE_COPY` **avec `file_copy_method = CLONE`** — réserve au §10.5 |
| RUN-04 | `run/determinism` | `libfaketime` : `FAKETIME` **et** interception de `getrandom()` par graine, en LD_PRELOAD |
| RUN-05 | `run/sideeffects` | aucune sortie réseau ; tout effet de bord a un double local |
| RUN-06 | `run/admin` | surface d'administration hors trace de l'agent |
| RUN-07 | `run/journal` | journalisation intégrale exportable |
| RUN-08 | `run/fleet` | provisionnement à la demande, destruction automatique |
| o RUN-09 | `run/faults` | Toxiproxy : lenteur, erreur, coupure |
| RUN-10 | `run/sideeffects` | Mailpit (SMTP + API d'inspection), WireMock ou smocker, `mock-oauth2-server`, MinIO |
| RUN-11 | `observe/drive` | second acteur = un scénario rejoué ; **même bloc** |
| o RUN-12 | `run/sandbox` | Firecracker donne un noyau par bac à sable ; incidents journalisés |
| RUN-13 | `run/branch` | le partage de blocs rend le coût marginal proportionnel aux écritures, pas au tenant — **si le système de fichiers le permet effectivement** (§10.5) |
| o RUN-14 | `run/fleet` | santé, instances bloquées ou orphelines, alerte et destruction |

### Surface tool use (API)

| Réf | Bloc | Outil / fondement |
|---|---|---|
| API-01 | `serve/parity` | couverture UI <-> API **mesurée** par `judge/diff`, pas déclarée |
| API-02 | `build/scaffold` | une seule couche de règles ; l'UI consomme l'API du clone |
| API-03 | `serve/mcp` | FastMCP `from_openapi()` / `from_fastapi()` : descripteurs générés |
| API-04 | `serve/errors` | refus métier et panne technique distincts et stables |
| API-05 | `build/scaffold` | pagination, tri, filtrage ; comparés par `judge/diff` |
| API-06 | `judge/diff` | même tâche par les deux surfaces, états comparés sous la politique |
| API-07 | `serve/mcp` | FastMCP, en plus de l'interface HTTP |
| o API-08 | `serve/contract` | versions de descripteurs immuables ; migration ouverte |
| API-09 | `serve/client` | délais et reprises bornés ; panne de connecteur distinguée d'un échec de tâche |
| API-10 | `serve/client` | tests consommateur sur la même chaîne d'intégration |

### Vérification (VER) — zone sans LLM

| Réf | Bloc | Outil / fondement |
|---|---|---|
| VER-01 | `judge/replay` + `judge/diff` | `diff(cible, clone)` |
| VER-02 | `judge/policy` | politique **compilée** depuis `diff(cible, cible)` ; lue par le code |
| VER-03 | `judge/adversary` | agent adversarial ; la famille RL est représentée par WebExplor, dont le code (`deepexplorer-web/WebExplor`) est **figé depuis le 05/09/2020** — le résultat de complémentarité (arXiv 2606.16650) reste, l'outil est à remplacer avant le lot 6 |
| VER-04 | `judge/edge` | Schemathesis (bornes, nullité, encodage) ; ordre d'opérations depuis `infer/deps` (RESTler, Morest) ; concurrence par Porcupine / Elle |
| VER-05 | `judge/coverage` | dénominateur = `targets/<cible>/scope.yaml`, arrêté avant campagne |
| VER-06 | `judge/diff` | rapport hiérarchisé, trace de reproduction jointe |
| VER-07 | `judge/mutate` | tout écart corrigé devient une faute semée permanente |
| VER-08 | `judge/distinguish` | Classifier Two-Sample Test (D8) ; méthode SandPrint (RAID 2016) |
| VER-09 | `judge/drift` | rejeu périodique sous budget `CAP-05` ; dette assumée du corpus figé |
| VER-10 | `judge/screen` | `aria_snapshot(boxes=True)` (Playwright 1.60) ; gabarit `toMatchAriaSnapshot` **produit depuis la cible**, `/children: equal` ; géométrie relative (X-PERT) |
| VER-11 | `judge/mutate` | taux de détection republié à chaque campagne ; jeu de fautes hors de portée du générateur (D4). `judge/accept` ne fait que le joindre au rapport de livraison |

### Orchestration LLM

| Réf | Bloc | Outil / fondement |
|---|---|---|
| LLM-01 | `orchestrate/loop` | générer -> `judge/diff` -> réparer ; la liste d'écarts **est** le retour (D7) |
| LLM-02 | `orchestrate/schema` | sorties structurées validées à chaque frontière ; jamais de texte libre entre étapes |
| LLM-03 | `orchestrate/trace` | MLflow ou Langfuse : entrées, sorties, coût, latence, verdict, rejouabilité |
| LLM-04 | `orchestrate/budget` | plafond par tâche et par cible, interruption au dépassement |
| LLM-05 | `orchestrate/evalset` | jeu d'évaluation **construit depuis les écarts constatés** par `judge/`, jamais fabriqué — c'est la réserve du §10 du cahier, et `judge/` est ce qui la rend tenable |
| LLM-06 | `orchestrate/parallel` | un écran, une entité, un cas de test : indépendants par construction (P1) |

### Non fonctionnel (NF)

| Réf | Bloc | Outil / fondement |
|---|---|---|
| NF-01 | mesure | chronométré sur trois cibles consécutives ; **rien ne le garantit par construction** |
| NF-02 | `build/seed` | Greenmask à 10^6 lignes sur les entités principales |
| NF-03 | mesure | 95e centile sous 300 ms à la volumétrie NF-02 |
| NF-04 | `run/sandbox` | restauration d'instantané annoncée en 5-30 ms contre 5 s exigées — **le chiffre est à mesurer**, §13 |
| NF-05 | `run/determinism` | `libfaketime` + graines ; artefacts adressés par contenu (P1) |
| NF-06 | `observe/store` | corpus figé, campagne en CI cible éteinte |
| NF-07 | `run/sandbox` + `run/branch` | 100 environnements ; coût marginal borné par le CoW |
| NF-08 | `targets/<cible>/` | espaces de travail isolés ; vue de portefeuille dans `run/fleet` |

### Acceptation (ACC)

Aucun critère n'est un bloc : chacun est une **sortie** de `judge/accept`, produite
automatiquement et jointe à la livraison.

| Réf | Produit par | Condition d'existence |
|---|---|---|
| ACC-01 | `judge/diff` + `judge/coverage` | `scope.yaml` arrêté et versionné avant la campagne |
| ACC-02 | `judge/coverage` | idem — sans quoi 100 % s'obtient en rétrécissant le dénominateur |
| ACC-03 | `judge/diff` | parité mesurée par `API-06` |
| ACC-04 | `judge/adversary` | critère d'arrêt déclaré avant lancement |
| ACC-05 | `run/sandbox` | 100 cycles, état complet comparé à l'état de départ |
| ACC-06 | `judge/accept` | mesures effectives à la volumétrie NF-02, opposables |
| ACC-07 | `infer/provenance` | compte des éléments *non observé* non résolus |
| ACC-08 | `judge/distinguish` | **reformulation en attente** : pouvoir discriminant borné (D8) au lieu d'un compte |
| ACC-09 | `observe/drive` + Porcupine / Elle | modèle séquentiel écrit à la main, une fois par cible (§8) |
| ACC-10 | humain | revue croisée par un Curriculum Engineer ; non automatisable, assumé |
| ACC-11 | `judge/screen` | écrans du périmètre déclaré |

## 10. Ce qui n'est pas résolu

**10.1 — `NF-01`, dix jours-homme par cible.** Aucun élément de cette architecture ne le
garantit. C'est une mesure à faire sur trois cibles consécutives, et le premier chiffre la
réfutera peut-être.

**10.2 — L'état persistant vu par la seule projection UI/API.** Sur une cible locale on lit
sa base ; sur une cible tierce, non. Rien dans la littérature consultée ne dit comment
quantifier ce que la projection laisse passer. Réponse partielle disponible : comparer, sur
la cible locale, `diff` avec accès base et `diff` sans — l'écart entre les deux **mesure**
l'angle mort. Instrument d'étalonnage, jamais verdict (D6).

**10.3 — Le dénominateur de la couverture n'a pas de définition stable.** L'équivalence
d'écrans par distance-seuil (Crawljax) n'est pas transitive, donc n'est pas une relation
d'équivalence. `scope.yaml` tranche par décision datée plutôt que par propriété.

**10.4 — Vieillissement du corpus figé.** Aucune littérature exploitable sur la détection
de dérive d'une cible en boîte noire. C'est la dette assumée que `VER-09` porte.

**10.5 — Le mécanisme de partage de blocs n'est pas garanti par sa documentation.**
`RUN-13` plafonne le coût marginal d'un environnement à 5 % du tenant, et `run/branch` le
tient par le partage de blocs. Or la documentation PostgreSQL 18 est prudente :
`file_copy_method` accepte « `COPY` (default) and `CLONE` (if operating support is
available) », et `CLONE` « uses the `copy_file_range()` (Linux, FreeBSD) or `copyfile`
(macOS) system calls, **giving the kernel the opportunity to share disk blocks** or push work
down to lower layers **on some file systems** ». Une opportunité sur certains systèmes de
fichiers n'est pas une garantie, et aucun système n'est nommé. Le plafond de 5 % reste donc
une **mesure à faire sur le système de fichiers retenu**, jamais une propriété déduite de
l'outil. `pg_branch`, cité dans une version antérieure de ce document, était une extension
expérimentale abandonnée en octobre 2023 : elle est retirée.

## 11. Ce qu'on n'écrit pas

Pas de registre de cibles, pas de système de plugins, pas de moteur de graphe de tâches —
`make` suffit. Pas d'abstraction sur les fournisseurs de modèles. Pas de format de trace
maison tant que le HAR tient. Pas de support d'une deuxième cible avant qu'une deuxième
cible existe. Les blocs sont des modules Python avec une interface en ligne de commande,
pas un cadriciel.

**`edist` (GPLv3) est disponible.** Il était écarté comme contaminant pour un livrable
commercial ; le projet n'en est pas un. C'est le seul calculateur de distance d'édition
d'arbre maintenu, et le besoin se pose à `judge/screen` si la comparaison structurelle
demande mieux qu'un appariement de sous-arbres. À reprendre quand le besoin sera réel —
pas avant, et sans écrire de Zhang-Shasha en attendant.

Restent **maison**, faute de substitut trouvé : la liaison symbolique de D1 et son
dictionnaire valeur -> variable stable entre deux captures ; la canonicalisation JCS ; le
compilateur de la politique d'équivalence vers les paramètres DeepDiff (~50 lignes) ; la
géométrie relative entre voisins, les `box` de Playwright étant absolus ; le jeton de débit
de `CAP-05` ; le modèle séquentiel par cible qu'exigent Porcupine et Elle.

Deux entrées s'y ajoutent, avec le substitut qui a été cherché :

- **OpenAPI -> schéma SQL.** La chaîne est outillée jusqu'au modèle typé :
  `datamodel-code-generator` produit du Pydantic v2 depuis un OpenAPI 3, et ses types de
  sortie documentés sont `pydantic_v2.BaseModel`, `dataclasses.dataclass`,
  `typing.TypedDict`, `msgspec.Struct` — **pas SQLModel**. Le passage au schéma relationnel
  et à ses migrations n'a donc pas de générateur : c'est `build/scaffold`, assisté par
  l'agent, puis Alembic pour les migrations. C'est le seul maillon non outillé du lot 1.
- **`tools/check_plan_coverage.py`.** C'est un traceur d'exigences miniature, et le domaine
  a des outils maintenus : **StrictDoc** (Apache-2.0, Python, actif) impose son format natif
  `.sdoc`, ce qui ferait sortir 91 exigences argumentées du Markdown ; **OpenFastTrace**
  (GPL-3.0) lit le Markdown *et le code source* par balises de couverture, mais exige un
  runtime **Java 17** — le motif qui a déjà écarté ALEX/LearnLib. Aucun des deux aujourd'hui.
  La question se rouvre au lot 4, quand la traçabilité devra atteindre du code source : c'est
  exactement le cas d'usage d'OpenFastTrace, et le JVM se discutera alors contre un bénéfice
  réel plutôt que contre un script de 95 lignes.

## 12. Outils écartés, avec leur motif

Consignés plutôt que supprimés : une erreur de motif se répète si on efface sa trace.

- **HAR et `route_from_har` en rejeu** — le code compare l'URL entière en égalité de chaîne ;
  un identifiant dans le chemin casse l'appariement avant que le corps soit regardé. Le
  **format** HAR reste retenu (P2).
- **mitmproxy en rejeu** — `serverplayback` apparie sur schéma, méthode, chemin, corps, hôte,
  port et query filtrée, avec six options d'ignorance. Les vraies limites sont le chemin en
  égalité stricte sans gabarit, et l'absence de WebSocket.
- **Diffy** — licence CC-BY-NC-ND, y compris sur le fork `opendiffy` toujours actif. Le
  projet n'étant pas un livrable commercial, la clause **NC** ne mord pas ; c'est la clause
  **ND**, sans dérivés, qui interdit de l'adapter. Motif corrigé le 01/09/2026 : le motif
  précédent invoquait le caractère commercial, qui n'était pas le bon. On garde l'idée du
  plancher de bruit, pas le logiciel.
- **VCR.py, betamax, pytest-recording, responses, respx** — ne patchent que des clients HTTP
  Python : aveugles au trafic d'un Chromium. betamax reste un modèle de placeholders.
- **Bouchons comme oracle** (WireMock, Hoverfly en substitution de cible) — un bouchon n'a pas
  de machine à états : il rend la réponse enregistrée quoi qu'on lui poste, sans exercer une
  ligne du clone. Retenus en revanche comme doubles d'effets de bord (`RUN-10`).
- **`DeepDiff.deep_distance` et `difflib.ratio()`** comme socle de seuil — le premier parce que
  sa documentation prévient que l'algorithme peut changer entre versions ; le second parce que
  `autojunk` écarte par défaut tout élément valant plus de 1 % d'une séquence de 200 ou plus,
  soit exactement les rôles ARIA répétitifs. C'est le piège du seuil 0,78 consigné en D2.
- **Comparaison visuelle par pixels** (BackstopJS, Percy, Chromatic) — écartée par D5. Le mode
  `Layout` d'Applitools vise « structure et position relative » mais **ignore le texte**.
- **trufflehog** et **ggshield** — écartés parce que leur méthode envoie le contenu ou les
  candidats à des API tierces : inacceptable pour un outil dont l'objet est la
  confidentialité (`CAP-03`). L'AGPL de trufflehog n'entre plus en compte, le projet n'étant
  pas un livrable commercial ; le motif restant est le bon et suffit.
- **GoReplay** (ne compare rien, licence mixte) ; **Daikon** (suppose l'accès au code) ;
  **overlayfs** pour l'isolation (copie le fichier entier, interaction documentée comme
  dangereuse avec le WAL de SQLite).
- **Un juge LLM comme oracle** — écarté par D7, chiffré par TOGLL.
- **Keploy** (Apache-2.0, eBPF) — enregistre et rejoue le trafic au niveau des appels système
  et **détecte seul les champs bruités en comparant les rejeux**, ce qui est le plancher de
  bruit de D2 industrialisé. Écarté sur la cible : il s'installe sur l'hôte de l'application
  observée, ce que `CAP-01` interdit et que D6 range du côté des privilèges. Reste un candidat
  légitime **côté clone**, où les privilèges nous appartiennent.
- **APIClarity** (OpenClarity, Apache-2.0) — reconstruit l'OpenAPI depuis le trafic et fait du
  *spec diff*, détectant les endpoints observés mais non documentés (« shadow ») et les
  documentés mais morts (« zombie »). C'est littéralement la dérive de `VER-09` et le signal
  « opération observée hors périmètre » du plan. Écarté pour son coût de déploiement —
  Kubernetes plus service mesh ou passerelle — sans commune mesure avec `mitmproxy2swagger`.
  L'idée du *spec diff* est reprise, le logiciel non.
- **Meticulous** — rejoue des sessions réelles enregistrées sur deux versions et compare les
  captures sans qu'aucune assertion soit écrite : la forme industrielle de `judge/diff`.
  Écarté deux fois : propriétaire, et il exige l'injection d'un extrait JavaScript dans
  l'application observée, impossible sur une cible tierce (`CAP-01`).
- **OpenHands, SWE-agent** comme socle de `orchestrate/loop` — écartés par le résultat
  d'`Agentless` : un pipeline étagé fait mieux pour un coût inférieur d'un ordre de grandeur.
  Le besoin est un enchaînement d'appels, pas une interface agent-ordinateur.
- **StrictDoc, OpenFastTrace** comme socle de traçabilité — motifs au §11, et la décision est
  datée : elle se rouvre au lot 4.
- **`pg_branch`** — extension PostgreSQL expérimentale, abandonnée en octobre 2023. Elle a
  figuré dans une version antérieure de ce document comme une option pour `RUN-13`, une
  exigence bloquante et chiffrée. Citer un prototype mort pour tenir un plafond est
  exactement l'erreur que le §11 existe pour empêcher. Motif consigné le 01/09/2026.

## 13. Références, avec leur statut de vérification

Une référence citée sans avoir été lue est une affirmation de mémoire, ce que ce dépôt
interdit. Chaque entrée porte donc son statut. **« Non vérifié » ne signifie pas douteux :
il signifie que personne ici ne l'a ouvert et cité page en main.** Une entrée ne remonte
d'un cran qu'en citant l'URL et le passage.

### Outils, avec leur fraîcheur mesurée le 01/09/2026

Un outil cité sans que sa maintenance ait été regardée est une dépendance sur laquelle on
n'a pas d'avis. La mesure est la date du dernier push sur son dépôt, relevée le 01/09/2026.

**Actifs — dernier push en avril, août ou septembre 2026.** Stagehand · mitmproxy2swagger ·
Prism (Stoplight) · Microcks (CNCF) · Schemathesis (MIT) · syrupy (MIT) · genson ·
AALpy (TU Graz) · LearnLib (TU Dortmund) · RESTler · Greenmask · Firecracker · libfaketime ·
Mailpit · mock-oauth2-server · WireMock · Toxiproxy · MLflow · Langfuse · Porcupine (MIT) ·
Elle (Jepsen) · Crawlee · MinIO (24/04) · detect-secrets (02/04).

**Non mesurés, à regarder avant de s'y adosser** : Playwright et
datamodel-code-generator, dont seule la documentation a été lue ; Morest ; Alembic ; `edist`.

**Datés, changés de main, ou retirés.**

| Outil | Mesure | Conséquence |
|---|---|---|
| **`pg_branch`** | extension « experimental », dernier push **06/10/2023** ; l'autre dépôt du même nom est un [WIP] de 2022 | **Retiré** de `run/branch` (§10.5) |
| **Crawljax** | dernière release `crawljax-5.2.3` le **01/06/2023**, dernier push 18/09/2023 | Référence de méthode pour le graphe d'états ; le parcours passe à Crawlee |
| **WebExplor** | `deepexplorer-web/WebExplor`, figé depuis le **05/09/2020** | Le résultat de complémentarité tient, l'outil est à remplacer avant le lot 6 |
| **ALEX** | `LearnLib/alex`, figé depuis le **05/08/2024** — LearnLib lui-même actif au 16/08/2026 | Précédent de méthode (§7), pas une dépendance |
| **DeepDiff** | dépôt passé de `seperman` à `qlustered` | La version 9.1 et la licence MIT sont **à revérifier** sous le nouveau propriétaire |
| **FastMCP** | dépôt passé de `jlowin` à `PrefectHQ` | `from_openapi()` et `from_fastapi()` **existent toujours** en 4.x, adossés à `OpenAPIProvider` ; migration 2.x → 4.x documentée. La revendication tient, l'adresse a changé |

### Vérifié le 01/09/2026, source à l'appui

| Référence | Ce qui a été vérifié |
|---|---|
| VeriEnv — *Safe and Scalable Web Agent Learning via Recreated Websites*, Chae, Park & Ritter, [arXiv 2603.10505](https://arxiv.org/abs/2603.10505), 11/03/2026 | Titre, auteurs, date, résumé. Le système clone des sites réels en environnements exécutables avec récompenses « deterministic, programmatically verifiable », via un SDK à accès interne contrôlé. **Aucun protocole de fidélité à l'original n'y figure** |
| *The Verification Horizon: No Silver Bullet for Coding Agent Rewards*, [arXiv 2606.26300](https://arxiv.org/abs/2606.26300), 24/06/2026 | Titre, 13 auteurs, résumé. « *verification must co-evolve with the generator* » ; aucune fonction de récompense fixe ne reste efficace. Fonde `VER-11` |
| *Before the Model Learns the Bug: Fuzzing RLVR Verifiers*, J. Ray, [arXiv 2606.01066](https://arxiv.org/abs/2606.01066), 31/05/2026 | Titre, auteur, date, méthode : fuzzer le vérificateur avant que le modèle n'en apprenne le défaut. Chiffres non lus |
| *InfiniteWeb: Scalable Web Environment Synthesis for GUI Agent Training*, [arXiv 2601.04126](https://arxiv.org/abs/2601.04126), ACL 2026 | Spécification unifiée puis développement piloté par les tests ; évaluateurs vérifiables. Même patron que `infer/surface` -> `build/scaffold`, **sans oracle de fidélité** |
| Olausson et al., *Is Self-Repair a Silver Bullet for Code Generation?*, ICLR 2024, [arXiv 2306.09896](https://arxiv.org/pdf/2306.09896) | Conclusions : gains modestes ou nuls avec un retour auto-produit, « substantially larger » avec un retour de meilleure qualité ; à petit budget l'échantillonnage i.i.d. fait parfois aussi bien |
| Playwright, `boxes` de `ariaSnapshot` | Documenté « since v1.60 » (Context7, `docs/src/api/class-page.md`). **Bonus non exploité dans ce document** : `ariaSnapshotJSON` rend l'arbre en JSON avec `box` comme propriété, ce qui évite d'analyser le YAML `[box=…]` |
| datamodel-code-generator | Types de sortie documentés : `pydantic_v2.BaseModel`, `dataclasses.dataclass`, `typing.TypedDict`, `msgspec.Struct`. **Pas de SQLModel** (§11) |
| [StrictDoc](https://github.com/strictdoc-project/strictdoc) · [OpenFastTrace](https://github.com/itsallcode/openfasttrace) | Apache-2.0, Python, actif / GPL-3.0, Java 17, lit Markdown et code source (§11) |
| [Keploy](https://keploy.io/docs/keploy-explained/introduction/) · [APIClarity](https://github.com/openclarity/apiclarity) | Capture au niveau syscall avec détection de champs bruités / reconstruction OpenAPI et *spec diff*, Apache-2.0, Kubernetes requis (§12) |

### Référence vérifiée, chiffre non vérifié

| Référence | Vérifié | Non vérifié |
|---|---|---|
| X-PERT, Roy Choudhary, Prasad & Orso, ICSE 2013, p. 702-711 | Existence, auteurs, objet (détection d'incompatibilités inter-navigateurs) | **Les 76 % de précision et 95 % de rappel** cités en D5 |
| Hammoudi, Rothermel & Tonella, *Why do Record/Replay Tests of Web Applications Break?*, ICST 2016 | **300 versions, 722 ruptures**, et la cause dominante « the information used to locate page elements » | **La part de plus de 73 %** citée en D1 |
| TOGLL, Hossain & Dwyer, [arXiv 2405.03786](https://arxiv.org/abs/2405.03786) | Existence, auteurs, objet | **Les 7 % et 25 % de faux positifs** cités en D7 |
| Agentless | Le résultat — pipeline étagé supérieur à beaucoup d'agents pour un coût inférieur d'un ordre de grandeur — lu dans une revue de littérature, **pas dans le papier** | Les chiffres exacts |

### Non vérifié — cité de seconde main, à lire avant d'en tirer une décision

McKeeman, *Differential Testing for Software*, DTJ 1998 · Chow, W-method, TSE 1978 ·
Böhme et al., *Estimating Residual Risk*, FSE 2021 · Angluin, L*, 1987 · Jahangirova et al.,
ISSTA 2016 · Just et al., FSE 2014 · SandPrint, RAID 2016 · Lopez-Paz & Oquab, *Revisiting
Classifier Two-Sample Tests*, ICLR 2017 · Kambhampati et al., ICML 2024 · *Can LLM Agents
Infer World Models?*, arXiv 2606.16576 · *Understanding Automated Web GUI Testing*,
arXiv 2606.16650 · *Do LLMs Generate Useful Test Oracles?*, ASE 2025 · LLM4Decompile et
Decompile-Bench, NeurIPS 2025 · ProtocolGPT, IWQoS 2025 · *Active inference of protocol state
machines*, FITEE 2025 · Design2Code, arXiv 2403.03163 · REAL, arXiv 2504.11543 · Elle,
VLDB 2021 · RFC 8785 (JCS).

Trois d'entre elles portent une décision entière et sont donc les premières à lire :
**Lopez-Paz & Oquab** fonde D8, **Kambhampati** fonde D7, **Böhme** fonde la limite de
couverture du §1.

### Affirmations non vérifiées — à ne pas promouvoir en fait

- La portabilité de Stagehand entre deux implémentations distinctes est une affirmation de
  son éditeur, pas une mesure.
- L'API d'AALpy n'a pas été lue ; seules sa publication et sa page projet l'ont été.
- **La fidélité de l'OpenAPI produit par `mitmproxy2swagger` n'a pas été éprouvée, et c'est
  le premier test du lot 1.**
- Les 5-30 ms de restauration Firecracker viennent de sources secondaires, pas d'un banc
  exécuté ici.
- Les gains de Porcupine sur Knossos sont ceux annoncés par son auteur.
- REAL revendique des répliques haute fidélité **sans décrire aucun protocole de
  validation** — c'est le vide que `judge/` occupe, et VeriEnv, vérifié plus haut, est dans
  le même cas. La formulation « aucun protocole » vient d'une lecture de résumé, pas du
  texte intégral.
- `libfaketime` intercepterait `getrandom()` par graine en LD_PRELOAD (porte `RUN-04` et
  `NF-05`) : sa fraîcheur est mesurée, ses capacités ne le sont pas.
- Web Page Replay ferait avancer `Date` de 50 ms toutes les 25 constructions — fondement
  unique de D3, et l'outil n'a pas été ouvert.
- `route_web_socket()` « depuis la 1.48 » (`CAP-10`) : seul `boxes` « since v1.60 » a été
  vérifié dans la documentation Playwright. Or `docs/plan.md` §6 fait de ces **deux**
  versions un motif de ne rien réutiliser.
- Les seuils par défaut pixelmatch 0,1 / Playwright 0,2 / Chromatic 0,063, et le comportement
  d'`autojunk` de `difflib` au-delà de 1 % d'une séquence de 200.
- Greenmask, moteur `hash` « déterministe à paramétrage identique » (porte `GEN-05`, `NF-05`).
- **Tout le §3.1 de `docs/plan.md`** : l'API `/api/v4` documentée en OpenAPI, PostgreSQL, le
  dépôt source disponible, les « 5 tables sur 95 », les identifiants de 26 caractères, la
  licence. La cible sur laquelle repose l'intégralité du lot 1 n'a aucune entrée ici, et le
  plan n'a pas de mécanisme de statut. C'est à vérifier au premier contact avec la cible.
