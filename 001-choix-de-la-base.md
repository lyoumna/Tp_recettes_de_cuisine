# ADR 0001 : choix de la base de données

Date : 10 novembre 2026

## Contexte

Notre site permet à des utilisateurs de publier des recettes, de les classer par catégorie, de les noter et de les mettre en favori. Les règles de gestion RG1 à RG11 sont décrites dans `CONCEPTION.md`. Elles sont fixées : la base choisie doit toutes les respecter. La question est de savoir où chaque règle est garantie, par la base elle-même ou par l'application.

### Les données

| **Donnée**                             | **Règles** | **Caractéristique utile pour le choix**                                                                    |
|----------------------------------------|------------|------------------------------------------------------------------------------------------------------------|
| Étapes d'une recette                   | RG6, RG11  | Elles n'existent que dans leur recette, sont peu nombreuses (une dizaine) et sont toujours lues avec elle. |
| Lignes d'ingrédients (quantité, unité) | RG4, RG5   | Elles n'ont de sens que dans la recette, sont peu nombreuses et sont toujours lues avec elle.              |
| Catalogue des ingrédients              | RG4        | Il est partagé entre les recettes et existe même si aucune recette ne l'utilise.                           |
| Catégories                             | RG3        | Il y en a peu, et une catégorie peut être vide.                                                            |
| Avis                                   | RG7, RG8   | Leur nombre par recette n'est pas limité. Un seul avis par utilisateur et par recette.                     |
| Favoris                                | RG9        | Leur nombre n'est pas limité. Un seul favori par utilisateur et par recette.                               |
| Utilisateurs                           | RG1, RG11  | Pseudo et e-mail uniques. Un compte est désactivé, jamais supprimé.                                        |

### Les usages

| **Opération**                                                  | **Fréquence** | **Données lues ou écrites**                           |
|----------------------------------------------------------------|---------------|-------------------------------------------------------|
| Afficher une recette complète                                  | très élevée   | recette, étapes, ingrédients, auteur                  |
| Lister les recettes d'une catégorie ou contenant un ingrédient | élevée        | recettes, note moyenne                                |
| Lire les avis d'une recette                                    | moyenne       | avis, page par page                                   |
| Ajouter un avis ou un favori                                   | moyenne       | un avis ou un favori                                  |
| Publier, modifier ou supprimer une recette                     | faible        | recette, et ses avis et favoris en cas de suppression |

### Volumes estimés

Environ 10 000 recettes, 1 500 ingrédients, 50 000 utilisateurs et quelques centaines de milliers d'avis et de favoris. Ce volume tient sur un seul serveur. La montée en charge ne départage donc pas les options : le critère principal est la forme des données et la manière dont on les lit.

## Options étudiées

| **Option** | **Comment le sujet y est rangé**                                                                                                                                            |
|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MongoDB    | Une recette est un document qui contient ses étapes et ses lignes d'ingrédients. Utilisateurs, catégories, ingrédients, avis et favoris sont dans des collections séparées. |
| PostgreSQL | Une table par entité et par association : `utilisateur`, `categorie`, `ingredient`, `recette`, `etape`, `contenir`, `avis`, `favori`.                                       |
| Neo4j      | Utilisateurs, recettes, ingrédients et catégories sont des nœuds. Avis, favoris et lignes d'ingrédients sont des relations qui portent leurs propriétés.                    |

Redis a été écarté dès le départ. Il peut servir de cache, mais ne permet pas de chercher des recettes par ingrédient ni de garantir les unicités du sujet.

### Comparaison sur nos usages

| **Usage**                              | **MongoDB**                                                  | **PostgreSQL**                                                          | **Neo4j**                                                                  | **Le plus adapté**         |
|----------------------------------------|--------------------------------------------------------------|-------------------------------------------------------------------------|----------------------------------------------------------------------------|----------------------------|
| Afficher une recette complète          | Une seule lecture : le document contient tout.               | Quatre tables à joindre (`recette`, `etape`, `contenir`, `ingredient`). | Les étapes ordonnées sont à reconstruire à partir de nœuds ou d'une liste. | MongoDB                    |
| Lister par catégorie ou par ingrédient | Index sur `categorie_id` et sur `ingredients.ingredient_id`. | Requête SQL avec index.                                                 | Parcours depuis le nœud catégorie ou ingrédient.                           | PostgreSQL, MongoDB proche |
| Calculer la note moyenne               | Agrégation `$avg` sur la collection `avis`.                  | `AVG` en une ligne de SQL.                                              | Agrégation sur les relations d'avis.                                       | PostgreSQL                 |
| Lire les avis page par page            | Requête sur `avis` avec index sur `recette_id`.              | Requête sur `avis` avec index.                                          | Parcours des relations d'avis.                                             | Équivalent                 |
| Ajouter un avis ou un favori           | Une insertion.                                               | Une insertion.                                                          | Création d'une relation.                                                   | Équivalent                 |
| Supprimer une recette                  | Une transaction sur trois collections.                       | Une suppression, la cascade fait le reste.                              | `DETACH DELETE` sur le nœud.                                               | PostgreSQL                 |

### Comparaison sur nos règles de gestion

Toutes les règles sont respectées quelle que soit la base. Le tableau indique où chacune est garantie : par la base, ou par l'application.

| **Règle**                                              | **MongoDB**                                                                     | **PostgreSQL**                                    | **Neo4j**                    |
|--------------------------------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------|------------------------------|
| RG1 : pseudo et e-mail uniques                         | Base : index uniques                                                            | Base : `UNIQUE`                                   | Base : contraintes d'unicité |
| RG2, RG3 : un auteur et une catégorie par recette      | Base pour la présence, application pour l'existence                             | Base : clés étrangères `NOT NULL`                 | Application                  |
| RG4 : nom d'ingrédient unique                          | Base : index unique                                                             | Base : `UNIQUE`                                   | Base : contrainte d'unicité  |
| RG5 : quantité positive et unité de la liste           | Base : validateur `$jsonSchema`                                                 | Base : `CHECK`                                    | Application                  |
| RG5 : un ingrédient une fois par recette               | Application                                                                     | Base : clé primaire `(id_recette, id_ingredient)` | Application (`MERGE`)        |
| RG6 : au moins une étape, numérotée sans trou          | Base pour le minimum, application pour la numérotation                          | Application (trigger)                             | Application                  |
| RG7 : note de 1 à 5, un avis par couple                | Base : validateur et index unique                                               | Base : `CHECK` et clé primaire                    | Application (`MERGE`)        |
| RG8 : pas d'avis sur sa propre recette                 | Application                                                                     | Application (trigger)                             | Application                  |
| RG9 : un favori par couple                             | Base : index unique                                                             | Base : clé primaire                               | Application (`MERGE`)        |
| RG10 : titre, portions, temps, titre unique par auteur | Base : validateur et index unique                                               | Base : `CHECK` et `UNIQUE`                        | Application                  |
| RG11 : suppression en cascade                          | Base pour les étapes et ingrédients imbriqués, transaction pour avis et favoris | Base : `ON DELETE CASCADE`                        | Base : `DETACH DELETE`       |
| RG11 : compte désactivé, pas supprimé                  | Application et droits                                                           | Application et droits                             | Application                  |

### Bilan

|                               | **MongoDB**                                                                                | **PostgreSQL**                                                         | **Neo4j**                                                                                              |
|-------------------------------|--------------------------------------------------------------------------------------------|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Point fort pour notre sujet   | La recette, opération la plus fréquente, se lit en une fois.                               | Le schéma garantit le plus grand nombre de règles.                     | Les associations porteuses de données sont naturelles.                                                 |
| Point faible pour notre sujet | Quatre règles reposent sur l'application (RG5 unicité, RG6 numérotation, RG8, références). | L'opération la plus fréquente demande des jointures sur quatre tables. | Aucune de nos requêtes ne parcourt plusieurs liens ; la plupart des règles reposent sur l'application. |

## Décision

Nous choisissons MongoDB.

L'opération la plus fréquente est l'affichage d'une recette complète. Les étapes et les lignes d'ingrédients n'existent que dans leur recette (RG5, RG6) et sont en nombre limité : elles correspondent bien à un document, qui se lit en une seule fois.

PostgreSQL garantit davantage de règles par son schéma. Avec MongoDB, ces règles restent respectées, mais une partie est vérifiée par l'application. Chacune est listée dans la section 4.2 de `CONCEPTION.md`, avec l'endroit où elle est vérifiée.

### Normalisation et dénormalisation

| **Donnée**                              | **Choix**                                        | **Justification**                                                                                             |
|-----------------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| Étapes                                  | Imbriquées dans la recette                       | Entité faible (RG6), en nombre limité, lue avec la recette et supprimée avec elle (RG11).                     |
| Lignes d'ingrédients                    | Imbriquées dans la recette, avec `ingredient_id` | La quantité et l'unité n'ont de sens que dans la recette (RG5).                                               |
| Ingrédients                             | Collection `ingredients`, référencée             | Catalogue indépendant des recettes, nom unique (RG4).                                                         |
| Catégories                              | Collection `categories`, référencée              | Une catégorie peut exister sans recette (RG3).                                                                |
| Avis                                    | Collection `avis`, référencée                    | Nombre non limité par recette, lus page par page (RG7). Les imbriquer ferait grossir le document sans limite. |
| Favoris                                 | Collection `favoris`, référencée                 | Nombre non limité (RG9).                                                                                      |
| Nom de l'ingrédient, pseudo de l'auteur | Copiés dans la recette                           | Ils permettent d'afficher la recette sans autre lecture et changent rarement.                                 |
| Note moyenne                            | Non stockée, calculée avec `$avg`                | Elle change à chaque avis, modifié ou retiré. La stocker obligerait à la recalculer à chaque fois.            |

## Conséquences

| **Ce qui est simplifié**                                                             | **Ce qui est plus difficile**                                                                                                           |
|--------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Une recette s'affiche avec un seul `findOne`.                                        | RG5 (unicité), RG6 (numérotation), RG8 et l'existence des références sont vérifiées par l'application.                                  |
| Les étapes et lignes d'ingrédients sont supprimées avec la recette.                  | La suppression d'une recette (RG11) passe par une transaction, ce qui impose un replica set, même à un seul nœud.                       |
| Un champ facultatif peut être ajouté à une étape, comme `duree_min`, sans migration. | Les copies (nom d'ingrédient, pseudo) doivent être mises à jour avec un `updateMany` en cas de renommage.                               |
|                                                                                      | La note moyenne est recalculée à chaque liste affichée : acceptable pour une page de 20 recettes, pas pour trier tout le site par note. |

### Ce qui nous ferait revoir ce choix

| **Évolution**                                                   | **Conséquence**                                                                           |
|-----------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| Une page « recettes les mieux notées » très consultée           | Stocker la somme des notes et le nombre d'avis dans la recette, mis à jour à chaque avis. |
| Des recherches multicritères qui deviennent l'usage principal   | PostgreSQL deviendrait plus adapté.                                                       |
| Des liens entre recettes ou entre utilisateurs ajoutés au sujet | Neo4j pourrait être ajouté pour cette partie.                                             |
