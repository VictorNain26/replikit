# Cahier des charges — replikit

Ce que l'outillage d'un *Replication Engineer* doit faire, établi à partir d'une offre de
référence et de rien d'autre.

Ce document porte le **quoi** : le texte des exigences, ce que chacune mesure, et le
standard que sa sortie doit respecter quand il en existe un. Le *comment* est dans
`docs/architecture.md`, le *quand* dans `docs/plan.md`, l'*état mesuré* dans
`docs/couverture.md`. Il définit l'espace de noms `XXX-NN` et les ancres `O1` à `O9`,
`M1`, `M2`, `S1`, `S2` : aucun autre document ne crée ni ne reformule une exigence, il ne
peut que la citer. Les numéros de section sont des ancres — on ne renumérote jamais.

## 1. Objet

Une chaîne de production qui prend en entrée un logiciel tiers accessible seulement de
l'extérieur, ou son code source quand il est libre, et rend un clone exécutable,
réinitialisable, interactif, dont un agent IA ne distingue pas le comportement de celui de
l'original — livré vite, sans trou qu'un agent puisse exploiter ou apprendre.

## 2. Ce que dit l'offre

Chaque exigence de ce document cite une des lignes ci-dessous. Une exigence qui n'en cite
aucune n'entre pas. Les citations sont textuelles.

| Ancre | Phrase de l'offre |
|---|---|
| **O1** | « *ship a complete, behaviorally faithful clone: fully interactive, resettable, and free of gaps or bugs that an agent could exploit or learn from* » ; « *behaviorally faithful down to the edge cases: every workflow, every state transition, every quirk of the original, reproduced and verified* » ; « *you ship it fast, complete, with no gaps and no bugs* » |
| **O2** | « *Drop into a completely unfamiliar system, understand its vitals, and reverse engineer its data model, state machine, and UI behavior in hours rather than weeks* » ; « *inferring data models, APIs, and behavior from the outside, with whatever combination of inspection, scraping, and experimentation the target demands* » |
| **O3** | « *Build and run verification harnesses that hammer the clone against the original, surfacing discrepancies before delivery. You treat "no known gaps" as the floor, not the goal, and you hunt for the unknown ones* » ; « *if it has a gap, an agent will find it, and a model will learn the wrong thing* » |
| **O4** | « *Push AI-coding tools (like custom LLM agents) to their breaking point, using them to write the scripts, scrapers, and tests that compound your output — achieving many times the output of a traditional developer without sacrificing correctness* » ; « *drive them to produce correct, verifiable code, not just plausible-looking code* » |
| **O5** | « *moving off ad hoc JSON flat files onto a proper relational/SQL foundation, improving query performance at enterprise data volumes, and designing connectors robust enough not to degrade task quality on the client side* » |
| **O6** | « *Identify opportunities to build the scripts, workflow recorders, LLM scaffolds, and diffing tools that make the clone faster and more reliable than the last* » |
| **O7** | « *scale our capacity by shipping multiple environments in parallel* » ; « *Exposure to cloud, deployment and Infrastructure as Code / DevOps practices is expected* » |
| **O8** | « *Work in a tight loop with Curriculum Engineers to ensure your clones are technically robust, faithful to the original system, and ready to be trained against immediately* » ; « *we sell training "tasks" built on top of these application environments* » |
| **O9** | « *You will operate without traditional PM or PO support, requiring you to proactively analyze and deeply understand the core value of a software system to prioritize and replicate its most critical features* » |
| **M1** | « *Computer use: the model operates a browser the way a person would — clicking, scrolling, with a visible cursor* » |
| **M2** | « *Tool use: there is no interface; the model makes API/MCP calls behind the scenes and the result is delivered directly* » |
| **S1** | « *open source software, where we work directly from the source code* » |
| **S2** | « *proprietary software (Slack, HubSpot, and the like), which we clone from the outside to reproduce its features and UX faithfully* » |
| **R** | « *a resettable, interactive simulation environment that an AI agent cannot tell apart from the real thing* » |

L'offre nomme trois familles de cibles — « *a legacy enterprise app, a modern SaaS, a niche
desktop tool* » — et un seul ordre de grandeur de délai, « *in hours rather than weeks* ».
Elle ne chiffre rien d'autre.

## 3. Périmètre et échelle

**replikit est un démonstrateur** de l'outillage que l'offre décrit, pas cet outillage en
production. Conséquence sur les rangs du §5 : ce qui relève de la flotte, de la volumétrie
d'entreprise et du portefeuille de cibles est nommé, mesuré quand c'est possible, et ne
conditionne pas la livraison d'un clone.

**Cibles web seulement.** Les outils de bureau, nommés par l'offre, n'ont ni trafic HTTP,
ni arbre d'accessibilité web, ni surface API observable de l'extérieur ; leur
rétro-ingénierie relève d'autres méthodes. Ils sont hors périmètre déclaré, et y entreraient
comme un périmètre distinct avec ses propres exigences, jamais par analogie.

**Deux cibles au minimum**, parce que l'offre nomme deux origines : une cible libre traitée
depuis sa source (S1) et une cible propriétaire clonée de l'extérieur (S2). Un outillage
démontré sur une seule origine n'a démontré que la moitié du métier.

**Les tâches d'entraînement sont hors périmètre.** L'offre les vend « *built on top of
these application environments* » et les confie aux Curriculum Engineers. Ce cahier couvre
ce qui rend un clone **prêt** à en porter (O8), pas les tâches elles-mêmes.

## 4. Vocabulaire

| Terme | Définition |
|---|---|
| **Cible** | Le logiciel d'origine. Observé de l'extérieur (S2) ou depuis sa source (S1). Jamais modifié ni instrumenté. |
| **Clone** | L'application produite, comportementalement indiscernable de la cible sur le périmètre déclaré. |
| **Spécification de clone** | Description explicite et versionnée de la cible — surface, entités, transitions, écrans, règles — que la génération consomme. |
| **Trace** | Enregistrement horodaté d'un parcours : actions, requêtes et réponses, messages des canaux temps réel, états de l'interface, captures. Unité de capture et unité de vérification. |
| **Écart** | Divergence observable entre clone et cible pour une même séquence d'entrées, une fois le bruit neutralisé selon la politique d'équivalence. |
| **Périmètre déclaré** | Sous-ensemble de la cible que le clone s'engage à reproduire, arrêté et versionné avant toute campagne de vérification. Les critères du §14 s'y rapportent. |
| **Environnement** | Instance déployée du clone, isolée, réinitialisable, attribuée à une session d'agent. |
| **Tâche** | Ce qu'Originator vend : un exercice construit sur un environnement, avec sa récompense. Hors périmètre, voir §3. |
| ***Computer use*** / ***tool use*** | Les deux modes d'interaction de l'agent, M1 et M2. |

## 5. Règles de ce cahier

**Aucun seuil inventé.** L'offre ne chiffre que « *hours rather than weeks* ». Chaque
exigence dit donc ce qu'elle **mesure** ; un seuil n'apparaît que là où l'offre le donne —
« *no gaps* », « *complete* » — ou après une première mesure, consignée dans
`docs/couverture.md`. Un seuil fixé avant toute mesure est un chiffre qu'on négociera après.

**Un standard quand il en existe un.** La colonne *Standard* nomme le format que la sortie
de l'exigence doit respecter, pour que chaque maillon soit remplaçable par un outil du
marché. « — » signifie qu'aucun standard ne s'applique, pas qu'on a oublié de chercher.
Chaque standard nommé a été lu à la source le 02/09/2026, et sa réserve est écrite à côté
de lui quand il en a une. Le choix des outils, lui, est dans `docs/architecture.md`, avec
les citations.

**Trois rangs.**
- **L** — *livraison* : conditionne l'acceptation d'un clone au sens du §14.
- **O** — *outillage* : conditionne la chaîne, pas un clone donné. Une chaîne qui ne
  l'a pas produit des clones plus lents ou moins fiables, pas des clones faux.
- **N** — *nommée par l'offre, hors démonstrateur* : mesurée si possible, jamais
  conditionnante ici (§3).

## 6. Capture (CAP)

Le seul contact avec la cible. Tout le reste travaille sur ses sorties.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| CAP-01 | Enregistrer un parcours humain ou agentique sur la cible sans rien y modifier ni installer : actions, requêtes et réponses, messages temps réel, états de l'interface, captures d'écran, horodatage relatif. | O6, O2 | familles présentes dans chaque trace | HAR 1.2 pour le réseau — format de fait, le brouillon W3C est abandonné | L |
| CAP-02 | Rejouer un parcours sur la cible et relever ce qui varie d'une exécution à l'autre — identifiants, horodatages, ordre. Ce relevé est le plancher de bruit sans lequel un écart ne se distingue pas d'une variation. | O3 | relevé des champs variables par parcours | — | L |
| CAP-03 | Explorer automatiquement la surface accessible et produire un inventaire d'écrans : route, éléments interactifs, appels déclenchés, préconditions. | O2 | écrans inventoriés ; écrans découverts après coup par la vérification | — | L |
| CAP-04 | Sonder chaque champ de formulaire inventorié avec des entrées limites — vide, hors bornes, doublon, caractères spéciaux — et enregistrer la réponse. Les règles de validation et leurs messages sont la partie la plus souvent manquée d'un clone. | O1 | part des champs sondés | — | L |
| CAP-05 | Respecter un budget de requêtes et un débit par cible avec arrêt d'urgence ; détecter les protections anti-robot et les ruptures de session, s'arrêter, préserver l'état partiel, alerter. Aucun contournement. | S2 | requêtes émises contre budget ; incidents journalisés | — | L |
| CAP-06 | Expurger des traces les secrets et données personnelles avant stockage, sans les rendre inutilisables comme référence de comparaison. | S2 | secrets détectés dans les traces stockées | — | L |
| CAP-07 | Stocker les traces adressables par identifiant stable, versionnées, avec la version de la cible observée. | O6, O3 | traces sans version de cible | — | L |
| CAP-08 | Quand la cible est libre, ingérer son dépôt source pour dériver schéma, migrations et routes directement plutôt que par inférence. | S1 | éléments de spécification dérivés de la source contre inférés | — | L |
| CAP-09 | Enregistrer plusieurs sessions simultanées sur une même trace, avec l'ordre relatif des événements entre acteurs. | O1, S2 | ordre relatif préservé | — | L |
| CAP-10 | Capturer les canaux temps réel — WebSocket, SSE, sondage long — comme événements typés et horodatés, décrits comme des canaux, pas comme du trafic opaque. | S2, O1 | événements typés contre trames brutes | AsyncAPI 3 pour décrire les canaux — liaison WebSocket normée, SSE sans liaison | L |

## 7. Inférence (INF)

De la trace à une spécification explicite, relue, versionnée.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| INF-01 | Proposer la surface API observée : chemins, opérations, paramètres, schémas de requête et de réponse. | O2, M2 | opérations observées non décrites | OpenAPI 3.1 | L |
| INF-02 | Proposer le modèle de données : entités, types, clés, relations, cardinalités, depuis les charges utiles observées. | O2 | entités sans clé, relations sans cardinalité | JSON Schema 2020-12 | L |
| INF-03 | Dériver la machine à états de chaque entité depuis les séquences de transitions observées. | O2 | transitions observées non représentées | format sérialisé, tranché en architecture | L |
| INF-04 | Rattacher chaque élément de la spécification aux traces qui le fondent, et marquer *non observé* ce qui relève de la conjecture : remonté comme dette de capture, jamais comblé en silence. | O3, O1 | éléments *non observé* | — | L |
| INF-05 | Spécification lisible, éditable à la main, validée par schéma, versionnée ; de nouvelles traces l'enrichissent sans écraser les amendements humains. | O6, O2 | amendements perdus après enrichissement | JSON Schema pour la validation | L |
| INF-06 | Signaler les contradictions entre traces — deux observations impliquant des règles incompatibles — au lieu d'arbitrer seul. | O4 | contradictions signalées contre arbitrées | — | L |
| INF-07 | Classer écrans et opérations par fréquence d'usage observée et proposer un périmètre hiérarchisé. C'est l'outillage de la priorisation sans PM. | O9 | proposition de périmètre produite | — | O |

## 8. Génération (GEN)

De la spécification à une application exécutable.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| GEN-01 | Persistance relationnelle générée depuis la spécification, schéma et migrations versionnées. Les fichiers JSON à plat sont proscrits comme couche de stockage. | O5 | stockage hors base détecté | SQL, PostgreSQL | L |
| GEN-02 | Contraintes d'intégrité appliquées par la base elle-même, pas seulement par le code. | O5, O1 | contraintes violables par la surface d'administration | SQL | L |
| GEN-03 | Règles de validation et messages d'erreur reproduits au caractère près. | O1 | écarts sur les messages | — | L |
| GEN-04 | Écrans générés fidèles en structure et en contenu, réutilisant d'une cible à l'autre ce qui est commun sans empêcher la spécialisation. | S2, O6 | écarts de structure d'accessibilité | arbre d'accessibilité WAI-ARIA | L |
| GEN-05 | Rôles et règles d'autorisation reproduits, y compris les fuites d'information par différence de message d'erreur. | O1 | écarts sur les parcours par rôle | — | L |
| GEN-06 | Comportements asynchrones et temps réel reproduits : traitement différé, notifications, événements poussés, destinataires, ordre, reconnexion. | S2, O1 | écarts sur les événements | AsyncAPI 3 | L |
| GEN-07 | Recherche, tri, filtrage et pagination reproduits, ordre des résultats et tolérance à l'approximation compris. | O1, O5 | écarts d'ordre | — | L |
| GEN-08 | Données de départ conformes aux distributions spécifiées, reproductibles à paramétrage identique, cas limites déclarés compris, jusqu'à une volumétrie d'entreprise. | O8, O5 | volume atteint ; même paramétrage → même jeu | — | L pour la reproductibilité, N pour la volumétrie |
| GEN-09 | Régénérer sans détruire les ajustements écrits à la main, la non-destruction étant vérifiée automatiquement. | O6, O4 | test de non-destruction | — | O |
| GEN-10 | Migrer un environnement existant construit sur fichiers JSON à plat vers la persistance relationnelle, avec vérification différentielle de l'environnement migré contre l'origine. | O5 | écarts origine ↔ migré | SQL | N — aucun environnement d'origine n'existe dans ce dépôt |
| GEN-11 | Ce qui est commun à tous les clones est partagé ; ce qui est propre à une cible vit dans son espace et nulle part ailleurs. | O6 | lignes propres à la cible contre lignes partagées | — | O |

## 9. Exécution (RUN)

Ce qui fait d'une application un terrain d'entraînement.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| RUN-01 | Ramener un environnement à un état de départ nommé ; capturer l'état complet à tout instant et le restaurer comme point de départ. | R, O1 | cycles reset → état identique à la référence | — | L |
| RUN-02 | Isolation stricte entre environnements simultanés — aucune donnée, cache ou compteur partagé — et plusieurs environnements par cible en parallèle. | O7, R | environnements simultanés mesurés ; coût marginal par environnement | — | L pour l'isolation, N pour le nombre |
| RUN-03 | Horloge et sources d'aléa contrôlables ; au même point de départ et aux mêmes entrées, deux exécutions produisent le même état. | O4, O3 | états divergents à entrées identiques | — | L |
| RUN-04 | Aucune dépendance sortante en session ; les effets de bord externes de la cible — courriel, webhook, authentification déléguée, fichiers — sont simulés localement avec une surface d'inspection. | O1, O8 | connexions sortantes observées ; parcours inaccessibles faute de double | — | L |
| RUN-05 | Surface d'administration hors trace de l'agent : lire l'état, forcer une transition, injecter une donnée. C'est ce qui permet de construire une tâche et de calculer sa récompense. | O8 | opérations d'administration visibles par l'agent | — | L |
| RUN-06 | Journalisation intégrale des interactions de l'agent, exportable. | O8 | interactions absentes du journal | — | L |
| RUN-07 | Provisionnement et destruction à la demande, infrastructure décrite comme code, image épinglée. | O7 | environnements orphelins ; dérive entre code et déployé | Compose Specification, images OCI | O |
| RUN-08 | Faire agir de façon reproductible au moins un second utilisateur dont les actions ont les mêmes effets qu'un humain. | S2, O1 | effets du second acteur contre effets humains | — | L |
| RUN-09 | Aucun indice ne révèle la simulation : en-têtes techniques, traces de pile, identifiants de framework, messages non traduits. | R | indices détectés | — | L |

## 10. Surface *tool use* (API)

Les mêmes capacités que l'interface, appelables sans interface, sans que la qualité des
tâches en dépende.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| API-01 | Toute action de l'interface a une opération équivalente et réciproquement, hors surface d'administration RUN-05. La parité est vérifiée automatiquement, pas déclarée. | M1, M2 | actions sans équivalent | OpenAPI 3.1 | L |
| API-02 | Interface et API partagent la même couche de règles : une validation ne peut exister que d'un côté. | M2, O1 | états finaux divergents pour une même tâche par les deux surfaces | — | L |
| API-03 | Descripteurs d'outils générés depuis la spécification, avec schémas d'entrée et de sortie et description exploitable par un modèle, exposés par MCP en plus de HTTP. | M2 | opérations sans descripteur | MCP (révision 2026-07-28), JSON Schema 2020-12 pour `inputSchema` et `outputSchema` | L |
| API-04 | Erreurs structurées et stables : un refus métier se distingue d'une panne technique. | O5 | erreurs non classées | — | L |
| API-05 | Connecteur robuste : délais et reprises bornés, comportement défini si l'environnement est indisponible, diagnostic distinguant une panne du connecteur d'un échec de la tâche. | O5 | échecs de tâche imputables au connecteur | — | L |
| API-06 | Temps de réponse des lectures courantes mesuré à la volumétrie GEN-08 et joint à la livraison. | O5 | centile 95 des lectures courantes | — | N |

## 11. Vérification (VER)

Les exigences les plus déterminantes : sans elles, la génération assistée par modèle
accélère la production d'erreurs. Elles produisent, avant livraison, la liste chiffrée des
écarts entre clone et cible.

Le rejeu sur la cible réelle est borné par CAP-05 et par les effets de bord non
annulables : l'oracle principal est un corpus de traces figées, et le rejeu réel sert à
l'étalonnage.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| VER-01 | Rejouer une trace sur cible et clone et produire un différentiel structuré : réponses, état persistant, contenu d'écran, événements temps réel, messages d'erreur. | O3 | écarts par famille | — | L |
| VER-02 | Politique d'équivalence explicite, versionnée, relue : chaque neutralisation cite le relevé CAP-02 qui la justifie. Une neutralisation sans relevé est refusée. | O3, O4 | neutralisations sans relevé | — | L |
| VER-03 | Exploration adversariale automatique dont l'objectif explicite est de trouver un comportement divergent que le corpus n'exerce pas. | O3 | écarts trouvés hors corpus | — | L |
| VER-04 | Cas limites générés depuis la spécification : bornes, nullité, unicité, encodage, ordre d'opérations, concurrence. | O1 | opérations sans cas limite | OpenAPI 3.1 comme source | L |
| VER-05 | Couverture : part des écrans, transitions et opérations du périmètre déclaré effectivement exercés par la campagne. | O1, O3 | couverture | — | L |
| VER-06 | Rapport d'écarts hiérarchisé, produit automatiquement, chaque écart portant sa trace de reproduction. | O3 | écarts sans reproduction | — | L |
| VER-07 | Tout écart corrigé devient un test permanent du clone concerné. | O1, O6 | écarts corrigés sans test | — | L |
| VER-08 | Publier, pour chaque campagne, le taux de détection de l'oracle sur un jeu de fautes semées que le générateur ne voit jamais. Un compte d'écarts sans son taux de détection n'est pas un résultat. | O3 — par indispensabilité : « *surfacing discrepancies* » ne dit rien sans la mesure de ce que le harnais laisse passer | taux de détection | — | L |
| VER-09 | Comparaison d'écran par structure d'accessibilité, position relative et contenu textuel, jamais par pixel. En *computer use*, ce que l'agent perçoit est l'écran. | M1 | écarts de structure et de contenu | WAI-ARIA | L |
| VER-10 | Indiscernabilité mesurée directement : le même agent, la même tâche, sur cible et sur clone ; trajectoires et résultats comparés. Le compte d'écarts est un diagnostic, cette mesure est le pronostic. | R | différence de trajectoires et de taux de succès | — | L |
| o VER-11 | Rejeu périodique contre la cible pour détecter sa dérive et signaler les clones obsolètes, sous budget CAP-05. | — extension : l'offre parle de livraison, pas de maintenance | clones signalés obsolètes | — | E |

## 12. Orchestration d'agents (LLM)

Où les modèles interviennent, et sous quel contrôle.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| LLM-01 | Boucle génération → vérification déterministe → correction : une sortie de modèle n'est acceptée qu'après passage d'un vérificateur qui n'est pas un modèle, avec plafond de tentatives et escalade humaine. | O4 | itérations avant convergence ; escalades | — | L |
| LLM-02 | Sorties structurées validées par schéma à chaque frontière ; jamais d'analyse de texte libre entre deux étapes. | O4 | frontières sans schéma | JSON Schema | L |
| LLM-03 | Journal intégral des appels — entrées, sorties, coût, latence, verdict — rejouable. | O4, O6 | appels absents du journal | conventions sémantiques GenAI d'OpenTelemetry — statut *Development*, attributs encore mouvants | O |
| LLM-04 | Budget par tâche et par cible, fixé avant lancement, interruption au dépassement. | O4, O1 | dépassements | — | O |
| LLM-05 | Prompts et scaffolds versionnés comme du code, avec un jeu d'évaluation construit depuis des écarts réels constatés, jamais fabriqué. | O6 | régressions détectées avant déploiement | — | O |
| LLM-06 | Parallélisation des tâches indépendantes — un écran, une entité, un cas — avec agrégation. | O4, O7 | tâches séquentielles évitables | — | O |

## 13. Outillage et cadence (OUT)

Ce que l'offre demande de la chaîne elle-même.

| Réf. | Exigence | Source | Mesure | Standard | Rang |
|---|---|---|---|---|---|
| OUT-01 | Délai de bout en bout mesuré par cible — heures de calendrier, jetons consommés, décisions humaines bloquantes — publié, et en baisse d'une cible à la suivante. | O1, O2, O6 | les trois mesures, par cible | — | O |
| OUT-02 | La chaîne complète rejoue en intégration continue, cible éteinte, à chaque modification du clone ou de l'outillage. | O3, O7 | exécutions manuelles requises | — | O |
| OUT-03 | Espaces de travail isolés par cible, sans ressource partagée bloquante, avec une vue d'avancement et d'écarts ouverts par clone. | O7 | chantiers bloqués l'un par l'autre | — | N |

## 14. Acceptation d'un clone (ACC)

Un clone n'est livrable que si chaque condition est vérifiée automatiquement et consignée
dans un rapport joint. Les conditions relatives au périmètre déclaré ne valent que si
celui-ci a été arrêté et versionné **avant** la campagne : sinon « zéro écart » et
« 100 % » s'obtiennent en rétrécissant le périmètre.

| Réf. | Condition | Source | Seuil |
|---|---|---|---|
| ACC-01 | Écarts ouverts sur le périmètre déclaré, accompagnés du taux de détection VER-08 de la même campagne. | O1 « *no gaps* » | 0 écart ; taux publié, jamais inférieur à la campagne précédente |
| ACC-02 | Couverture VER-05 du périmètre déclaré. | O1 « *complete* » | 100 % |
| ACC-03 | Parité API-01 sur les actions du périmètre. | M1, M2 | 100 % |
| ACC-04 | Campagne adversariale VER-03 menée jusqu'à son critère d'arrêt déclaré avant lancement, écarts trouvés corrigés et couverts par VER-07. | O3 | requis |
| ACC-05 | Réinitialisation RUN-01 : cycles consécutifs sans résidu, état complet comparé à la référence. Nombre de cycles déclaré avant la campagne. | R | requis |
| ACC-06 | Éléments *non observé* (INF-04) restés non résolus. | O1 | 0 |
| ACC-07 | Indices de simulation RUN-09 détectés, et mesure VER-10 jointe. | R | 0 indice ; mesure publiée |
| ACC-08 | Rapport de données et de performance joint : volumétrie GEN-08 atteinte, mesures API-06 effectives. | O5 | requis à l'échelle du démonstrateur (§3) |
| ACC-09 | Pour une cible collaborative : parcours multi-acteurs vérifié avec un acteur synthétique RUN-08, événements temps réel comparés. | S2 | requis |
| ACC-10 | Revue par un Curriculum Engineer : le clone est prêt à être entraîné. | O8 | requis — personne ne tient ce rôle sur ce dépôt ; consigné en échec, jamais retiré |

**Ce que ces critères ne bornent pas.** ACC-01 compte ce qui a été trouvé ; l'offre demande
de chasser ce qui ne l'a pas été. VER-10 est la seule mesure agrégée de ce document, et son
seuil viendra de sa première valeur, pas d'ici.

## 15. Ce qui a été retiré, et pourquoi

Une version antérieure de ce document comptait 91 exigences et six seuils chiffrés que
l'offre ne donne pas — dix jours-homme, 10⁶ lignes, 300 ms, 5 s, 5 %, 100 environnements.
Ils sont retirés : un seuil sans mesure fondatrice se négocie après coup. Ont été fusionnées
ou retirées les exigences qui ne citaient aucune phrase de l'offre et n'étaient
indispensables à aucune qui en cite : injection de fautes pilotable, confinement du bac à
sable, supervision de flotte, contrat de connecteur versionné, exposition MCP séparée de la
génération des descripteurs, tests de non-régression côté consommateur. La détection de
dérive reste, comme extension. La mesure d'indiscernabilité par classifieur est remplacée
par la mesure directe, VER-10, qui est ce que l'offre dit mot pour mot.
