# Journal des changements

Le wiki ESI (Django + React) et ses builds Windows partageables. Les dates sont celles des
commits ; les versions correspondent aux paliers fonctionnels du projet, pas à des tags git.

## [non publié] — 2026-10-18

### Corrigé
- Le bandeau de démarrage du sample disait « Clé … : absente » à une clé **pourtant lue**. Il ne
  regardait que l'environnement du processus, alors que le `.env` posé à côté de l'.exe est chargé
  après, par `settings.py`. `packaging/launcher.py` lit maintenant le fichier avant de conclure :
  `Clé OpenRouter : présente (.env à côté de l'.exe)`.

### Publish
- Release **v1.5** : `esi-wiki-keyless-2026-10-18.zip` (60 014 124 octets), la variante sans clé
  reconstruite depuis `main` — nom d'école corrigé dans l'interface et bandeau honnête. Le `.env` du
  destinataire, le `db.sqlite3` et le `frontend/` que l'.exe recopie à côté de lui restent sur ce
  disque : l'archive porte l'.exe, `_internal/` et le gabarit `.env.example`, 4 353 membres, zéro
  valeur de clé au balayage, base livrée sans `corpus_fts` mais avec ses 104 modules et 945 documents.
- v1.4 reste en ligne, datée du 14 octobre : elle montre encore l'ancien nom et l'ancien bandeau.

## [non publié] — 2026-10-15

### Changé
- Le dépôt passe **public**.
- README **repris pour une lecture publique** : bannière `docs/banner.png` en tête, ouverture sur la
  gestion du savoir plutôt que sur l'inventaire des fichiers, l'adresse de contact en paragraphe de
  clôture, et plus aucune description du détail des fichiers d'étudiants.
- **`courses/` sort du suivi git** et rejoint `.gitignore`, avec `corpus/` : 318 Mo, 325 fichiers qui
  appartiennent à l'école et à ses étudiants. Le dépôt public garde le code, le catalogue et les
  outils ; les documents se donnent de personne à personne.
- L'historique public repart d'un **commit unique**. L'ancien — 28 commits, la clé d'un fichier
  abandonné, un message de fusion inapproprié — reste sur disque et n'est pas publié.
- `docs/architecture.png` retiré : la rasterisation du SVG amputait le diagramme, qui reste en SVG à
  côté de la bannière.

## [non publié] — 2026-10-14

### Ajouté
- `CHANGELOG.md` — ce fichier.
- Release **v1.4** : `esi-wiki-keyless-2026-10-14.zip`, la variante sans clé (57 MiB), jointe au dépôt.
- Le dossier `courses/` passe dans l'index de recherche : les cours S1-S2 du dépôt sont
  désormais lisibles par l'assistant, au même titre que le miroir EsiHub. `index_corpus` lit les
  deux racines et saute un fichier du dépôt déjà miroité (même nom, même taille en octets) pour
  que le même texte ne compte pas deux fois dans `document_frequency`.

### Changé
- **Nom de l'école corrigé partout : École de Sciences de l'Information**, et non « École Supérieure
  d'Informatique ». Cinq chaînes de l'application (titre de l'onglet, bandeau du hero, pied de page,
  page À propos, prompt système de l'assistant) plus le README ; la base de données n'en portait
  aucune. Le bundle régénéré (`index-B2ynJrDa.js`) vérifié : trois occurrences du nom correct, zéro
  de l'ancien, et le bandeau ralenti toujours à l'intérieur.
- README **réécrit en anglais et divisé par trois** (477 lignes → 183) : le texte que lit un
  employeur, pas une justification du projet. Les anecdotes de mesure, les particularités de chaque
  fournisseur et les récits de vérification sortent du README ; les chiffres, la marche à suivre,
  les quatre niveaux, les deux builds, l'API, la sécurité et les limites restent.
- Nom du projet : le dépôt GitHub devient **esi-wiki** (au lieu de `kmprj`) et passe **privé**.
- Le bandeau de modules en tête d'accueil roule à la taille du catalogue (2,5 s par nom, soit 260 s
  mesurées contre 38 s avant) et se met en pause au survol : à l'ancienne vitesse, un nom restait
  lisible 1,2 s.
- Les 33 photographies Wikimedia sont **dans le dépôt**. Elles étaient ignorées au profit de
  `tools/fetch-media.mjs`, mais cet outil relance une recherche Commons et choisit d'autres images :
  un clone n'affichait plus le site.
- L'assistant ne promet plus « polycopiés EsiHub » là où il répond aussi depuis `courses/` :
  l'étiquette du niveau 2 devient « polycopiés indexés du wiki », côté interface comme dans le
  prompt.
- Sans dossier `corpus/`, le niveau 2 s'indexe et répond quand même : `index_corpus` avertit
  au lieu d'abandonner, et `search()` ne dépend plus de la présence du miroir.
- README aligné sur l'index mesuré : **1 403 documents / 19 646 extraits** de S1 à S5.
- Le README dit maintenant ce que le mail achète : la `-Keyless` répond déjà avec **sa propre clé**
  posée dans `.env`, alors que le build à clés embarquées — zéro configuration — s'obtient en
  écrivant à `mohamed-amine.chafik@esi.ac.ma`.

### Conservé tel quel
- Le sample partagé repart toujours **sans corpus** : `packaging/strip-corpus.py` retire les
  lignes de texte et la table `corpus_fts` de la base livrée. Un destinataire n'a ni les
  polycopiés d'autrui, ni leur texte indexé.

## 1.3 — 2026-10-11 → 2026-10-12

- OpenAI devient le **quatrième fournisseur** de la voie à clés, essayé en dernier parce qu'il
  facture à l'usage ; chaque fournisseur garde sa clé, ses slugs et sa forme de clé vérifiée.
- Deux flavours de sample : `.exe` **avec clés embarquées** (remise en main propre) et
  **`-Keyless`** (lit l'environnement ou un `.env` posé à côté — la clé du destinataire, jamais
  la vôtre). Le gabarit `.env.example` voyager dans le dossier `-Keyless`.
- Une clé configurée mais morte le **dit** (`note:` listant chaque fournisseur essayé) au lieu
  de se faire passer pour une réponse de modèle.
- Le miroir EsiHub de S3-S5 entre au **catalogue** : modules, ressources et pages `/polycopies/`,
  avec repli sur le Drive d'origine quand la copie locale manque.

## 1.0 — 2026-10-11

- Réécriture complète en **Django 5.2 + DRF + SQLite** côté back, **React 18 + Vite + Tailwind**
  côté front, servie par un seul serveur en production.
- Assistant à **quatre niveaux** : tables locales, index FTS5 des polycopiés, modèles à clés,
  modèle sans clé. Un chiffre sort d'une table, une définition sort d'un fichier ; les garde-fous
  de récupération (deux mots couverts dont un rare, mot court = mot entier) empêchent la réponse
  fausse qui a l'air vraie.
- Miroir EsiHub : `tools/esihub_fetch.py` + `index_corpus`, 1,98 Go, `corpus/` ignoré par git.

## 0.x — 2025-04-09 → 2025-04-10

- Site statique d'origine (`index.html`, `qa.html`, `academy.html`, `chat/`). Remplacé par la
  version 1.0 ; les fichiers restent sur disque, ne sont plus suivis par git.
