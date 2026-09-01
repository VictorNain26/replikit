# Cahier des charges — Plateforme de réplication logicielle

Périmètre et exigences de l'outillage de réplication logicielle visé par ce dépôt.

Ce document porte le **quoi** : le texte des exigences et leurs seuils. Le *comment* est
dans `docs/architecture.md`, le *quand* dans `docs/plan.md`, l'*état mesuré* dans
`docs/couverture.md`. Il définit l'espace de noms `XXX-NN` : aucun autre document ne crée
ni ne reformule une exigence, il ne peut que la citer. Les numéros de section sont des
ancres — on ne renumérote jamais.

Marqueurs : une exigence sans marque appartient au **socle** (ancrée dans le besoin de référence, ou indispensable à une exigence qui l'est) ; `o` signale une **extension** hors périmètre de la source, qui ne conditionne pas l'acceptation d'un clone — sa priorité est donc *conditionnelle* (§3).

## 1. Objet et objectifs

L’outil à construire est une chaîne de production : elle prend en entrée un logiciel tiers accessible uniquement de l’extérieur, et rend en sortie un clone exécutable dont un agent IA ne doit pas pouvoir distinguer le comportement de celui de l’original — livré en jours, pas en semaines, et sans trou fonctionnel exploitable.

## 2. Vocabulaire

| Terme | Définition retenue dans ce document |
|---|---|
| **Cible** | Le logiciel d’origine, observé de l’extérieur (pas d’accès au code source). |
| **Clone** | L’application produite, censée être comportementalement indiscernable de la cible sur le périmètre retenu. |
| **Spécification de clone** | Description explicite et versionnée de la cible : entités, transitions, écrans, règles. Ce que la génération prend en entrée. |
| **Environnement** | Instance déployée du clone, isolée, réinitialisable, attribuée à une session d’agent. |
| **Tenant** | Jeu de données complet d’une organisation cliente simulée, servant d’unité de volumétrie. Les seuils NF-02, NF-04 et RUN-13 s’y rapportent. |
| **Trace** | Enregistrement horodaté d’un parcours : actions, requêtes réseau, messages des canaux temps réel, états DOM, réponses. Unité de capture et unité de test. |
| **Écart (gap)** | Divergence observable entre clone et cible pour une même séquence d’entrées. |
| **Périmètre déclaré** | Sous-ensemble de la cible que le clone s’engage à reproduire, arrêté et versionné avant la vérification. Les seuils ACC-01 à ACC-04, ACC-07 à ACC-09 et ACC-11 s’y rapportent ; la liste fait foi au §12. |
| ***Computer use*** | Mode d’interaction où l’agent pilote un navigateur (curseur, clics, saisie). |
| ***Tool use*** | Mode d’interaction où l’agent appelle des outils/API sans interface graphique. |

## 3. Périmètre

> Socle et extensions
> Chaque exigence porte un marqueur d’origine, indépendant de sa priorité.
> **Socle** — sans marque. L’exigence répond à un besoin nommé par la référence amont, ou elle est techniquement indispensable à une exigence qui l’est. Seul le socle conditionne l’acceptation d’un clone (§12).
> **Extension** — marquée `o`. Défendable, mais absente de la source. Elle ne conditionne pas la livraison tant qu’elle n’a pas été explicitement retenue.
> Décompte : 87 exigences de socle, 4 extensions — `RUN-09`, `RUN-12`, `RUN-14`, `API-08`. Dont 64 exigences de socle bloquantes, qui sont la carte de `docs/plan.md`. Ce qui *contredisait* la source n'a pas été marqué mais retiré : sur le périmètre et les exigences, l'offre fait foi.
> **La priorité d'une extension est conditionnelle.** `Bloquant si retenue` se lit « bloquant à partir du moment où l'extension est retenue, sans effet tant qu'elle ne l'est pas ». Une extension ne peut pas être bloquante au sens du §12, qui exclut déjà tout critère dépendant d'une extension non retenue : écrire `Bloquant` sec sur une ligne marquée `o` était une contradiction dans les termes.

### 3.1 Cibles hors périmètre, déclarées

L'offre nomme trois familles de cibles : « *a legacy enterprise app, a modern SaaS, a niche
desktop tool* », et décrit le champ comme allant « *from simple websites to complex
applications* ». **Ce document ne couvre que les cibles web.** Toute exigence de capture,
de génération d'écran et de vérification visuelle suppose un navigateur et HTTP.

C'est une restriction assumée, pas un oubli : un outil de bureau n'a ni trace HTTP, ni arbre
d'accessibilité web, ni surface API observable de l'extérieur, et sa rétro-ingénierie relève
d'un autre corps de méthodes. La couvrir demanderait un second cahier, pas des exigences
supplémentaires dans celui-ci.

**Décision à confirmer** : si les cibles de bureau doivent entrer, elles entrent comme un
périmètre distinct, avec ses propres exigences de capture et son propre oracle. Les
transposer par analogie serait le pire des deux mondes.

## 4. Capture et reconnaissance

Ces exigences portent sur le corpus d’observation de la cible. C’est le seul contact avec le système d’origine ; tout le reste travaille sur ses sorties.

### 4.1 Fonctions

- **Enregistrement de parcours.** Capturer, pour une session humaine ou agentique : actions utilisateur, requêtes et réponses réseau, messages des canaux temps réel, instantanés DOM avant/après, captures d’écran, horodatage relatif.
- **Explorateur automatique.** Parcours en largeur de la surface accessible : routes atteignables, formulaires, tableaux, états vides, pagination, modales. Produit un inventaire d’écrans plutôt qu’une simple liste d’URL.
- **Sondage de comportement.** Émission contrôlée d’entrées limites (champ vide, valeur hors bornes, doublon, caractères spéciaux, action concurrente) pour observer les messages d’erreur et les règles de validation, qui sont la partie la plus souvent manquée d’un clone.
- **Capture multi-acteurs.** Enregistrement corrélé de plusieurs sessions simultanées, sans lequel une cible collaborative (messagerie, CRM partagé) ne peut être ni observée ni vérifiée.
- **Normalisation.** Conversion des captures hétérogènes en un format de trace unique, seul contrat consommé par l’inférence et la vérification.

### 4.2 Exigences

| Réf. | Exigence | Priorité |
|---|---|---|
| CAP-01 | Enregistrer un parcours complet sans modification de la cible ni installation côté serveur. | Bloquant |
| CAP-02 | Rejouer une trace enregistrée sur la cible et caractériser ce qui varie d’une exécution à l’autre — identifiants, horodatages, ordre — en le déclarant comme non-déterminisme de la cible. L’identité stricte n’a pas de sens sur un système à état ; ce relevé alimente la politique d’équivalence VER-02 sans se confondre avec elle. | Bloquant |
| CAP-03 | Expurger automatiquement des traces les secrets et données personnelles (jetons, en-têtes d’authentification, identifiants, contenus utilisateur), sans rendre la trace inutilisable comme référence de comparaison : le contenu d’écran que VER-01 compare doit rester exploitable après traitement. | Bloquant |
| CAP-04 | Produire un inventaire d’écrans avec, pour chacun : route, éléments interactifs, appels réseau déclenchés, préconditions d’accès. | Bloquant |
| CAP-05 | Respecter un budget de requêtes et une limite de débit paramétrables par cible, avec arrêt d’urgence. | Bloquant |
| CAP-06 | Pour chaque champ de formulaire inventorié, exercer au minimum les sondes de saisie — champ vide, valeur hors bornes, doublon, caractères spéciaux — et enregistrer la réponse obtenue ; les actions concurrentes relèvent de VER-04. La couverture des sondes est mesurée et rapportée au même titre que VER-05. | Bloquant |
| CAP-07 | Stocker les traces adressables par identifiant stable, versionnées, avec la version de la cible observée. | Élevée |
| CAP-08 | Ingestion d’un dépôt source lorsque la cible est un logiciel libre, pour dériver le schéma directement plutôt que par inférence. La source décrit ce mode comme l’une des deux moitiés du métier : il n’est pas optionnel. | Bloquant |
| CAP-09 | Détecter les protections anti-robot et les ruptures de session (interstitiel de vérification, filtrage applicatif, authentification multifacteur, expiration, blocage de compte), interrompre la capture, préserver l’état partiel et alerter l’opérateur qui rétablit la session manuellement. Aucun contournement automatisé n’est implémenté. | Bloquant |
| CAP-10 | Capturer les canaux temps réel (WebSocket, SSE, sondage long) comme événements horodatés du même format de trace, et non comme trafic opaque. | Bloquant |
| CAP-11 | Enregistrer plusieurs sessions concurrentes sur une même trace, avec ordre relatif des événements entre acteurs préservé. | Bloquant |

## 5. Inférence du modèle

Ces exigences portent sur la transformation d’un corpus de traces en une spécification de clone explicite, relue et amendée par un humain, puis versionnée.

### 5.1 Exigences

| Réf. | Exigence | Priorité |
|---|---|---|
| INF-01 | Proposer un schéma relationnel candidat à partir des payloads observés : types, clés, relations, cardinalités. | Bloquant |
| INF-02 | Rattacher chaque élément de la spécification aux traces qui le justifient — toute affirmation est traçable jusqu’à une observation. | Bloquant |
| INF-03 | Marquer explicitement comme *non observé* ce qui relève de la conjecture, et le faire remonter comme dette de capture plutôt que de le combler silencieusement. | Bloquant |
| INF-04 | Format lisible et éditable à la main, versionné dans le dépôt du clone, avec validation de schéma. | Bloquant |
| INF-05 | Dériver la machine à états d’une entité depuis les séquences de transitions observées. | Bloquant |
| INF-06 | Détecter les contradictions internes (deux traces impliquant des règles incompatibles) et les signaler au lieu d’arbitrer seul. | Élevée |
| INF-07 | Reprise incrémentale : de nouvelles traces enrichissent une spécification existante sans écraser les amendements humains. | Élevée |
| INF-08 | Classer écrans et opérations par fréquence d’usage observée dans les traces, et produire une proposition de périmètre hiérarchisée. C’est l’outillage de la priorisation produit exigée en l’absence de PM. | Élevée |

## 6. Génération du clone

Ces exigences portent sur la production, à partir de la spécification, d’une application exécutable : persistance, service, interface, canaux temps réel et jeu de données.

| Réf. | Exigence | Priorité |
|---|---|---|
| GEN-01 | Générer le schéma SQL et ses migrations depuis la spécification. La persistance est relationnelle par défaut ; les fichiers JSON à plat sont proscrits comme couche de stockage. | Bloquant |
| GEN-02 | Générer une couche d’accès typée et les opérations CRUD, avec les contraintes d’intégrité effectivement appliquées par la base. | Bloquant |
| GEN-03 | Reproduire les règles de validation et les messages d’erreur au caractère près : ils font partie du comportement observable. | Bloquant |
| GEN-04 | Générer les écrans en réutilisant d’une cible à l’autre ce qui leur est commun, sans empêcher la spécialisation de ce qui est propre à une cible. | Bloquant |
| GEN-05 | Générer des données de départ conformes aux distributions spécifiées, reproductibles à paramétrage identique, et incluant les cas limites déclarés. | Bloquant |
| GEN-06 | Régénérer un clone sans détruire les ajustements écrits à la main, la non-destruction étant vérifiée automatiquement. | Bloquant |
| GEN-07 | Reproduire les comportements asynchrones observés dans les traces — traitement différé, notification, verrou optimiste — y compris leur délai lorsqu’il est observable par l’agent. | Bloquant |
| GEN-08 | Reproduire les rôles et les règles d’autorisation, y compris les fuites d’information par différence de message d’erreur. | Bloquant |
| GEN-09 | Générateur de volumétrie : produire un tenant à l’échelle d’un client d’entreprise pour éprouver la tenue en charge (§11). | Bloquant |
| GEN-10 | Générer les canaux temps réel spécifiés : événements poussés, destinataires, ordonnancement, comportement à la reconnexion. Requis pour toute cible collaborative. | Bloquant |
| GEN-11 | Reproduire le comportement de recherche, de tri et de filtrage — ordre des résultats et tolérance à l’approximation compris. Un classement divergent est un écart au sens de VER-01, pas un détail d’implémentation. | Bloquant |
| GEN-12 | Migration des environnements existants construits sur fichiers JSON à plat : dérivation du schéma relationnel depuis les fichiers, reprise des données, et vérification différentielle de l’environnement migré contre sa version d’origine. GEN-01 ne vaut que pour les clones à venir, et la source est ici impérative — « *moving off* ad hoc JSON flat files » désigne l’existant. Vérification par rejeu, au sens VER-01, des traces capturées sur l’environnement d’origine. | Bloquant |

## 7. Exécution et réinitialisation

Ces exigences portent sur l’exécution des clones en instances isolées, réinitialisables et instrumentées — ce qui transforme une application en terrain d’entraînement.

| Réf. | Exigence | Priorité |
|---|---|---|
| RUN-01 | Ramener un environnement à un état de départ nommé. L’absence de résidu d’état n’étant pas démontrable dans l’absolu, elle est approchée par le protocole d’ACC-05, dont le résultat est consigné. Conjuguée à NF-04 et à la concurrence NF-07, cette exigence impose RUN-13 : c’est le principal point dur d’architecture du runtime. | Bloquant |
| RUN-02 | Capturer l’état complet à un instant quelconque et le restaurer comme point de départ d’une tâche. | Bloquant |
| RUN-03 | Isolation stricte entre sessions concurrentes — aucune donnée, aucun cache, aucun compteur partagé. | Bloquant |
| RUN-04 | Horloge et sources d’aléa contrôlables : date figée ou avançable sur commande, générateur pseudo-aléatoire ensemencé, identifiants reproductibles. | Bloquant |
| RUN-05 | Fonctionnement hors ligne : aucune dépendance sortante vers un service tiers en cours de session. | Bloquant |
| RUN-06 | Lire l’état, forcer une transition et injecter une donnée sans passer par l’interface ni apparaître dans la trace de l’agent. | Bloquant |
| RUN-07 | Journalisation intégrale des interactions de l’agent, exportable pour analyse. | Élevée |
| RUN-08 | Provisionnement à la demande et destruction automatique, infrastructure décrite comme code. | Élevée |
| o RUN-09 | Injection de fautes pilotable : lenteur réseau, erreur serveur, conflit d’édition — conditions d’erreur reproductibles à la demande, que l’environnement doit savoir produire. | Souhaitée |
| RUN-10 | Simuler en local les effets de bord sortants de la cible — envoi de courriel, webhook, authentification déléguée, dépôt et téléchargement de fichiers — avec une surface d’inspection (boîte de réception, journal d’appels) exploitable par l’agent comme par le barème. Sans quoi RUN-05 rend inaccessible une part des parcours de la cible. | Bloquant |
| RUN-11 | Faire agir dans l’environnement, de façon reproductible, au moins un second utilisateur dont les actions ont les mêmes effets que celles d’un humain. Prérequis de toute tâche collaborative. | Bloquant |
| o RUN-12 | Confinement du bac à sable : un agent qui tente de sortir de l’environnement (exécution de code, accès au système de fichiers hôte, appel réseau sortant, accès à une autre session) est bloqué et l'incident est journalisé. | Bloquant si retenue |
| RUN-13 | Le coût de stockage marginal d’un environnement supplémentaire reste inférieur à 5 % du volume du tenant de référence, faute de quoi la concurrence exigée par NF-07 devient inabordable. | Bloquant |
| o RUN-14 | Supervision de la flotte : état de santé et disponibilité de chaque environnement, détection des instances bloquées ou orphelines, alerte et destruction automatique. Sans quoi rien n’adresse la santé d’une flotte d’environnements, que la concurrence exigée par NF-07 rend inévitable. | Élevée |

## 8. Surface *tool use* et connecteurs

Objet : exposer les mêmes capacités que l’interface, sous forme d’outils appelables, et fournir aux consommateurs le moyen de s’y brancher sans que la qualité des tâches en dépende. Le point critique n’est pas l’existence de l’API mais sa *parité* avec l’UI : deux surfaces divergentes sur le même état produisent des environnements où l’agent apprend des règles contradictoires selon le mode.

| Réf. | Exigence | Priorité |
|---|---|---|
| API-01 | Toute action réalisable dans l’UI dispose d’une opération équivalente, et réciproquement, à l’exclusion de la surface d’administration RUN-06 qui n’a pas d’équivalent UI par construction et sort du décompte de parité. La couverture est vérifiée automatiquement, pas déclarée. | Bloquant |
| API-02 | UI et API partagent la même couche de règles métier : une validation ne peut exister que d’un côté. | Bloquant |
| API-03 | Descripteurs d’outils générés depuis la spécification, avec schémas d’entrée et de sortie et description en langage naturel exploitable par un modèle. | Bloquant |
| API-04 | Erreurs structurées et stables : un agent doit pouvoir distinguer un refus métier d’une panne technique. | Bloquant |
| API-05 | Pagination, tri et filtrage sur toutes les collections, avec un comportement identique à celui observé sur la cible. | Bloquant |
| API-06 | Test de parité automatisé : exécuter une même tâche par les deux surfaces et comparer l’état final selon la politique d’équivalence de VER-02, seule source de la distinction entre champ significatif et champ neutralisé. | Bloquant |
| API-07 | Exposition via un protocole d’outils standard (MCP) en plus de l’interface HTTP. | Élevée |
| o API-08 | Contrat de connecteur explicite et versionné : une version de descripteurs d’outils est immuable, toute évolution incompatible produit une version nouvelle, et un consommateur peut rester sur la précédente le temps de migrer. | Bloquant si retenue |
| API-09 | Robustesse côté consommateur : délais et reprises bornés, comportement défini en cas d’indisponibilité de l’environnement, et diagnostic permettant de distinguer une panne du connecteur d’un échec de la tâche. Un connecteur ne doit jamais faire échouer une tâche pour une raison qui ne relève pas du comportement de la cible. | Bloquant |
| API-10 | Tests de non-régression exécutés du point de vue du consommateur, sur la même chaîne d’intégration que le clone. | Élevée |

## 9. Vérification différentielle et QA adversariale

Ces exigences sont les plus déterminantes du document. Sans elles, la génération assistée par LLM ne fait qu’accélérer la production d’erreurs. Elles produisent, avant livraison, la liste chiffrée des écarts entre clone et cible.

### 9.1 Principe

Une même séquence d’entrées est rejouée sur la cible et sur le clone ; les états résultants sont comparés selon une politique d’équivalence explicite qui neutralise les différences non significatives (identifiants, horodatages, ordre non garanti) sans jamais neutraliser une différence de comportement.

Le rejeu sur la cible réelle étant limité par le débit autorisé, le coût des comptes et les effets de bord non annulables, l’oracle principal est un corpus de traces figées ; le rejeu réel est réservé à la validation et à la détection de dérive (VER-09). Ce corpus vieillit : c’est le prix assumé de la contrainte, et la raison pour laquelle VER-09 est bloquant.

### 9.2 Exigences

| Réf. | Exigence | Priorité |
|---|---|---|
| VER-01 | Rejouer une trace sur cible et clone, et produire un différentiel structuré : réponses, état persistant, contenu d’écran, événements temps réel, messages d’erreur. | Bloquant |
| VER-02 | Politique d’équivalence déclarative, versionnée et relue : chaque neutralisation est justifiée et opposable en revue. | Bloquant |
| VER-03 | Exploration adversariale par agent : un agent dont l’objectif explicite est de trouver un comportement divergent, parcourant le clone en cherchant les trous. | Bloquant |
| VER-04 | Génération de cas limites depuis le schéma : bornes, nullité, unicité, encodage, concurrence, ordre d’opérations. | Bloquant |
| VER-05 | Mesure de couverture : part des écrans, transitions et opérations du périmètre déclaré effectivement exercés par la campagne de vérification. | Bloquant |
| VER-06 | Rapport d’écarts hiérarchisé, produit automatiquement, incluant pour chaque écart la trace de reproduction. | Bloquant |
| VER-07 | Tout écart corrigé devient un test de non-régression permanent du clone concerné. | Bloquant |
| VER-08 | Vérification d’étanchéité de la simulation : détecter les indices permettant à un agent de reconnaître l’environnement — traces d’implémentation, en-têtes techniques, traces de pile, identifiants de framework, messages d’erreur non traduits. | Bloquant |
| VER-09 | Rejeu périodique contre la cible pour détecter sa dérive et signaler les clones devenus obsolètes. Fréquence à arrêter par cible sous la contrainte de budget CAP-05. Un clone signalé obsolète déclenche une re-capture ciblée, la révision de sa spécification et la publication d’une version nouvelle des descripteurs d’outils ; les sessions en cours vont à leur terme. | Bloquant |
| VER-10 | Comparaison visuelle des écrans, portant sur la structure, la position relative et le contenu textuel, à l’exclusion du rendu exact des polices et de l’*antialiasing*. En *computer use*, ce que l'agent perçoit est l'image : cet oracle n'est pas accessoire. | Bloquant |
| VER-11 | Publier, pour chaque campagne, le taux de détection de l'oracle sur le jeu de fautes semées courant. Un compte d'écarts non accompagné de son taux de détection n'est pas un résultat. Le jeu de fautes n'est pas exposé au générateur : un générateur qui voit les fautes semées apprend les fautes, pas la fidélité. Sa croissance relève de VER-07. | Bloquant |

## 10. Orchestration LLM

Ces exigences portent sur l’usage des modèles à l’intérieur de la chaîne, là où ils apportent un gain mesurable — mesuré contre une ligne de base établie sans eux, sans quoi l’affirmation de gain reste invérifiable — et sous contrôle systématique.

| Réf. | Exigence | Priorité |
|---|---|---|
| LLM-01 | Boucle génération → vérification → correction : la sortie d’un modèle n’est acceptée qu’après passage d’un vérificateur déterministe, avec plafond de tentatives et escalade humaine. | Bloquant |
| LLM-02 | Sorties structurées validées par schéma à chaque frontière ; jamais d’analyse de texte libre entre deux étapes. | Bloquant |
| LLM-03 | Journalisation intégrale des appels — entrées, sorties, coût, latence, verdict — et rejouabilité d’une exécution. | Bloquant |
| LLM-04 | Budget par tâche et par cible, avec interruption au dépassement. | Élevée |
| LLM-05 | Prompts et *scaffolds* versionnés au même titre que le code, avec un jeu d’évaluation permettant de mesurer une régression avant déploiement. | Élevée |
| LLM-06 | Parallélisation des tâches indépendantes (un écran, une entité, un cas de test) avec agrégation des résultats. | Élevée |

> Sur les jeux d’évaluation (LLM-05)
> Un jeu d’évaluation construit par la même équipe qui écrit les scaffolds ne peut pas les contredire : il encode les mêmes hypothèses. La référence doit provenir de clones réels validés par des écarts constatés en production, pas de cas fabriqués pour l’occasion.

## 11. Exigences non fonctionnelles

| Réf. | Exigence | Priorité |
|---|---|---|
| NF-01 | Délai de bout en bout : cible inconnue → clone accepté en moins de 10 jours-homme pour une application SaaS de complexité moyenne, mesuré sur trois cibles consécutives. | Bloquant |
| NF-02 | Volumétrie : supporter un tenant réaliste d’entreprise — ordre de grandeur 10^6 lignes sur les entités principales — les temps de réponse restant conformes à NF-03 à cette échelle. | Bloquant |
| NF-03 | Temps de réponse : les opérations de lecture courantes s’exécutent sous 300 ms au 95^e centile à la volumétrie NF-02. | Bloquant |
| NF-04 | Réinitialisation d’un environnement sous 5 s au 95^e centile, à la volumétrie NF-02. | Bloquant |
| NF-05 | Reproductibilité : au même point de départ et avec les mêmes paramètres, deux exécutions produisent des états identiques. | Bloquant |
| NF-06 | Intégration continue : sur chaque clone, tests de non-régression et campagne de vérification exécutés à chaque modification, sans dépendre d’un accès à la cible réelle — celui-ci reste périodique et sous budget (VER-09, CAP-05). | Bloquant |
| NF-07 | Concurrence : au moins 100 environnements simultanés par cible, avec un coût de stockage marginal par environnement sous le plafond chiffré par RUN-13, mesuré et suivi. | Bloquant |
| NF-08 | Production simultanée de plusieurs cibles : espaces de travail isolés par cible, aucune ressource partagée bloquante entre chantiers, et vue de portefeuille donnant l’avancement et les écarts ouverts de chaque clone en cours. C’est la condition de la mise à l’échelle par parallélisation des chantiers, distincte de la concurrence d’exécution NF-07. | Élevée |

## 12. Critères d’acceptation d’un clone

Un clone n’est livrable que si l’ensemble des conditions suivantes est vérifié automatiquement et consigné dans un rapport joint à la livraison. Un critère qui dépendrait d’une extension en serait exclu tant que celle-ci n’a pas été retenue ; aucun ne l’est aujourd’hui. Les seuils ACC-01 à ACC-04, ACC-07 à ACC-09 et ACC-11 sont relatifs au **périmètre déclaré** : ils ne valent que si celui-ci a été arrêté et versionné avant la campagne de vérification, faute de quoi « zéro écart » et « 100 % » s’obtiennent en rétrécissant le périmètre. ACC-05, ACC-06 et ACC-10 ne dépendent pas du périmètre déclaré.

| Réf. | Condition | Seuil |
|---|---|---|
| ACC-01 | Écarts de comportement ouverts sur le périmètre déclaré, accompagnés du taux de détection VER-11 mesuré sur la même campagne. | 0 écart, et taux de détection au moins égal au seuil déclaré avant lancement et jamais inférieur à celui de la campagne précédente |
| ACC-02 | Couverture des écrans, transitions et opérations du périmètre déclaré par la campagne de vérification, au sens de VER-05. | 100 % |
| ACC-03 | Parité UI ↔ API sur les actions du périmètre. | 100 % |
| ACC-04 | Campagne adversariale menée jusqu’à son critère d’arrêt déclaré — budget d’épisodes et durée fixés par cible avant lancement, arrêt sur absence de nouvel écart pendant la moitié du budget — écarts trouvés corrigés et couverts par un test de non-régression. | Requis |
| ACC-05 | Protocole de réinitialisation : 100 cycles consécutifs sans résidu détecté par comparaison de l’état complet à l’état de départ de référence. Approximation assumée de RUN-01, dont elle ne démontre pas la forme absolue. | Requis |
| ACC-06 | Rapport de charge joint à la livraison : mesures effectives à la volumétrie NF-02, opposables, et non simple déclaration de conformité à NF-03. | Requis |
| ACC-07 | Éléments de la spécification marqués *non observé* et restés non résolus. | 0 |
| ACC-08 | Fuites de simulation détectées par VER-08. | 0 |
| ACC-09 | Pour une cible collaborative : parcours multi-acteurs vérifié avec au moins un acteur synthétique (RUN-11) et les événements temps réel comparés à la cible. | Requis |
| ACC-10 | Revue croisée par un Curriculum Engineer : le clone est jugé utilisable en l’état pour l’entraînement. | Requis |
| ACC-11 | Comparaison visuelle VER-10 exécutée sur les écrans du périmètre déclaré ; écarts de structure ou de contenu non résolus. | 0 |

> **Ce que ces critères ne couvrent pas encore.**
> L'offre pose que « *"no known gaps" [is] the floor, not the goal, and you hunt for the
> unknown ones* ». `ACC-01` à 0 écart ouvert **est** ce plancher : il compte ce qui a été
> trouvé. Rien ici ne borne ce qui ne l'a pas été, alors que l'objectif du §1 — un clone
> qu'un agent ne distingue pas de la cible — est une propriété agrégée, pas un compte.
> Un critère mesurant le **pouvoir discriminant** d'un classifieur entraîné à séparer clone
> et cible fournirait cette borne. C'est la décision `D8` de `docs/architecture.md`, en
> attente : elle vaut pour `ACC-08`, qu'elle rendrait mesurable, et au-delà pour `ACC-01`,
> qu'elle compléterait sans le remplacer.

Périmètre et exigences établis à partir des besoins d’outillage d’une plateforme de réplication de qualité production : enregistreurs de parcours, scrapers, *scaffolds* LLM, outils de *diffing*, harnais de vérification, fondation SQL en remplacement des fichiers JSON à plat, et connecteurs pour le *tool use* dont la robustesse ne doit pas dégrader la qualité des tâches côté client. Les seuils chiffrés de la section 12 sont à confirmer par la mesure.

## 13. Traçabilité vers l'offre

Source : une offre d'emploi de référence, **volontairement non nommée ici**. Chaque famille
d'exigences est rattachée à la phrase qui la fonde. Une exigence qui ne se rattache à rien est
une extension, marquée `o`.

| Section | Phrase de l'offre |
|---|---|
| §1 Objet | « *a resettable, interactive simulation environment that an AI agent cannot tell apart from the real thing* » ; « *free of gaps or bugs that an agent could exploit or learn from* » |
| §4 Capture | « *inferring data models, APIs, and behavior from the outside, with whatever combination of inspection, scraping, and experimentation the target demands* » ; « *workflow recorders* » |
| `CAP-08` | « *open source software, where we work directly from the source code, and proprietary software (Slack, HubSpot, and the like), which we clone from the outside* » — les deux moitiés du métier, d'où le caractère bloquant |
| §5 Inférence | « *reverse engineer its data model, state machine, and UI behavior in hours rather than weeks* » |
| `INF-08` | « *without traditional PM or PO support, requiring you to proactively analyze and deeply understand the core value of a software system to prioritize and replicate its most critical features* » |
| §6 Génération | « *every workflow, every state transition, every quirk of the original, reproduced and verified* » |
| `GEN-01`, `GEN-12` | « *moving off ad hoc JSON flat files onto a proper relational/SQL foundation* » |
| §7 Exécution | « *interactive and resettable training grounds* » ; « *fully interactive, resettable* » |
| §8 Tool use | « *Tool use: there is no interface; the model makes API/MCP calls* » ; « *connectors robust enough not to degrade task quality on the client side* » |
| §9 Vérification | « *verification harnesses that hammer the clone against the original, surfacing discrepancies before delivery* » ; « *diffing tools* » |
| `VER-03` | « *you hunt for the unknown ones* » ; « *if it has a gap, an agent will find it, and a model will learn the wrong thing* » |
| `VER-10` | « *Computer use: the model operates a browser the way a person would* » — ce que l'agent perçoit est l'image |
| §10 Orchestration | « *orchestrating LLM agents to write the scrapers, glue code, and tests* » ; « *drive them to produce correct, verifiable code, not just plausible-looking code* » |
| `NF-01` | « *ship it fast* » ; « *in hours rather than weeks* » ; « *the fast cadence is the point* » |
| `NF-02`, `NF-03` | « *improving query performance at enterprise data volumes* » |
| `NF-08` | « *scale our capacity by shipping multiple environments in parallel* » |
| `ACC-10` | « *tight loop with Curriculum Engineers to ensure your clones are technically robust, faithful to the original system, and ready to be trained against immediately* » |

**Le rattachement se fait par famille, pas par exigence.** À l'intérieur d'une famille
rattachée, une exigence est socle si elle répond à la phrase, ou si elle est « techniquement
indispensable à une exigence qui l'est » (§3) : `CAP-03`, `CAP-05`, `CAP-09` ou `RUN-04`
n'ont pas de phrase propre et tiennent par ce second motif. `VER-11` est signalée à part
parce qu'elle n'est pas née de la lecture de l'offre : elle a été ajoutée après coup, par la
décision D4 de `docs/architecture.md`, et c'est la seule exigence de ce document dans ce cas.
Elle tient au socle par indispensabilité : `ACC-01` — zéro écart ouvert — ne signifie rien
sans le taux de détection de l'oracle qui a produit ce zéro, ce que confirme *The
Verification Horizon* (arXiv 2606.26300), pour qui « *verification must co-evolve with the
generator* ».

**Seuils non sourcés.** Six chiffres de ce document ne viennent pas de l'offre et sont des
propositions à confirmer par la mesure, pas des engagements repris : les **10 jours-homme**
de `NF-01`, les **10⁶ lignes** de `NF-02`, les **300 ms** de `NF-03`, les **5 s** de
`NF-04`, le plafond de **5 %** de `RUN-13` et les **100 environnements** de `NF-07`.
L'offre dit « vite » et « à l'échelle de l'entreprise » sans les chiffrer.

**Ce que l'offre demande et que ce document traite comme acquis.** « *You move fast because
you have built the tooling, the AI scaffolds, and the verification harnesses that let you
move fast without cutting corners.* » La vitesse n'est donc pas une exigence parmi les
autres : c'est ce que l'outillage achète. `docs/plan.md` ordonnance six lots dont le lot 3
est déjà la deuxième cible : l'outillage se paie sur les deux premières pour rendre les
suivantes rapides. Ce pari est la thèse du projet, et `NF-01`
est ce qui le réfutera ou non.
