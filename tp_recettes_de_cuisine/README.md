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

```
Tp_recettes_de_cuisine/
  README.md           le sujet en deux lignes, le groupe, la base choisie
  CONCEPTION.md       règles de gestion, MCD, MLD dans MongoDB, ce que le schéma ne garantit pas
  docs/adr/
    0001-choix-de-la-base.md   choix de la base (MongoDB, comparé à PostgreSQL et Neo4j)
  modele/             bonus : la base (PostgreSQL), le script de données, les requêtes
    creer_base_postgresql.sql  création des tables, contraintes, trigger RG8, index
    donnees_exemple.sql        petit jeu de données écrit à la main
    generer_donnees.py         génère un jeu de données aléatoire (reproductible)
    requetes.sql               12 requêtes qui répondent aux usages de l'ADR
    tests_regles.sql           vérifie que la base refuse chaque violation des règles de gestion
  app/                bonus : petite application web (Flask)
    app.py, db.py, requirements.txt
```

## Implémentation (bonus)

La conception et l'ADR retiennent **MongoDB**. Pour le bonus, nous avons implémenté le **même MCD dans PostgreSQL** (créé avec pgAdmin). Cette version est un prototype relationnel : l'écart avec le MLD MongoDB de `CONCEPTION.md` est volontaire. Ici les étapes et les lignes d'ingrédients sont dans des tables séparées au lieu d'être imbriquées dans la recette. PostgreSQL garantit en plus directement les clés étrangères, les `CHECK`, `ON DELETE CASCADE` et, par un trigger, RG8, ce que MongoDB laisse à l'application (voir l'ADR).

### Prérequis

PostgreSQL 14 ou plus (pgAdmin facultatif), Python 3.10 ou plus. Seule l'application a besoin de paquets : `pip install -r app/requirements.txt`.

### 1. Créer la base

```bash
createdb recettes
psql -d recettes -f modele/creer_base_postgresql.sql
```

Avec pgAdmin : créer une base vide `recettes`, ouvrir le *Query Tool*, puis charger et exécuter le fichier.

### 2. Charger des données (au choix)

```bash
# a) le petit jeu d'exemple
psql -d recettes -f modele/donnees_exemple.sql

# b) un jeu généré : 200 utilisateurs et 300 recettes par défaut, option --graine pour une autre série
python3 modele/generer_donnees.py > modele/donnees_generees.sql
psql -d recettes -f modele/donnees_generees.sql
```

Le jeu généré vide d'abord les tables : on peut donc le charger après l'exemple. Il respecte les règles de gestion (un seul avis par couple, jamais d'avis d'un auteur sur sa recette, étapes numérotées sans trou, etc.).

### 3. Requêtes et vérification des règles

```bash
psql -d recettes -f modele/requetes.sql
psql -d recettes -f modele/tests_regles.sql   # affiche « OK » pour chaque règle bien refusée ; n'écrit rien
```

### 4. Lancer l'application

```bash
pip install -r app/requirements.txt
export DATABASE_URL=postgresql://utilisateur:mot_de_passe@localhost/recettes   # facultatif, défaut : postgresql://localhost/recettes
flask --app app/app.py run
```

Puis ouvrir http://127.0.0.1:5000. On peut lister et filtrer les recettes (catégorie, ingrédient), ouvrir une recette, choisir « Je suis » dans la liste en haut à droite, puis donner un avis ou mettre en favori. Si l'auteur de la recette essaie de la noter, la base refuse (RG8) et l'application affiche son message.

Sous Windows (PowerShell) : `$env:DATABASE_URL="postgresql://..."`, et `psql` se trouve dans `C:\Program Files\PostgreSQL\<version>\bin`.
