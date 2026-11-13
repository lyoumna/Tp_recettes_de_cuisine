# Tp_recettes_de_cuisine

Site de recettes de cuisine : des utilisateurs publient des recettes, les classent par catégorie, les notent et les mettent en favori.
TP noté « Conception et architecture des données » (Bachelor 3, Ycode A2627_4672) : cahier des charges, MCD, choix de la base (ADR) et MLD.

## Groupe

- Aya
- Youmna
- Mehdi

## Base choisie

**MongoDB**, base orientée documents : une recette se lit en entier (étapes et lignes d'ingrédients imbriquées). Le choix est comparé à PostgreSQL et Neo4j dans l'ADR.

## Contenu du dépôt

| Fichier | Contenu |
|---|---|
| [`CONCEPTION.md`](CONCEPTION.md) | Règles de gestion (RG1 à RG11), questions posées, MCD, MLD dans MongoDB, ce que le schéma ne garantit pas |
| [`docs/adr/0001-choix-de-la-base.md`](docs/adr/0001-choix-de-la-base.md) | ADR : choix de la base, comparaison avec PostgreSQL et Neo4j, dénormalisation, conséquences |

## Implémentation (bonus)

Non réalisée dans ce rendu : la base n'est pas créée et il n'y a pas de script de données ni d'application. Les fichiers `modele/creer_base.js`, `modele/ajouter_avis.js` et `modele/supprimer_recette.js` cités dans `CONCEPTION.md` décrivent ce qui serait à écrire pour garantir les règles.
