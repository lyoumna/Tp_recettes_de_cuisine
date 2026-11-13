#!/usr/bin/env python3
"""Génère un jeu de données aléatoire (mais reproductible) pour la base PostgreSQL du site de recettes.

Usage :
    python3 modele/generer_donnees.py > modele/donnees_generees.sql
    python3 modele/generer_donnees.py --recettes 1000 --utilisateurs 500 --graine 7 > modele/donnees_generees.sql

Le script ne se connecte à aucune base : il écrit des instructions SQL sur la sortie standard.
Les règles de gestion sont respectées à la génération (pseudo/e-mail uniques, un ingrédient une fois par
recette, étapes numérotées sans trou, aucun avis d'un auteur sur sa propre recette, un avis et un favori
par couple). Bibliothèque standard uniquement.
"""
import argparse
import random
from datetime import date, timedelta

PRENOMS = ["lea", "tom", "sam", "ines", "hugo", "emma", "noah", "lina", "adam", "zoe", "yanis", "sara",
           "lucas", "mila", "enzo", "jade", "nils", "anna", "rayan", "lou", "eden", "maya", "theo", "alice"]

CATEGORIES = ["entrée", "plat", "dessert", "boisson", "accompagnement"]

# (nom, unité, quantité min, quantité max)
INGREDIENTS = [
    ("pomme", "pièce", 2, 6), ("poire", "pièce", 2, 5), ("banane", "pièce", 1, 4), ("citron", "pièce", 1, 3),
    ("tomate", "pièce", 2, 8), ("oignon", "pièce", 1, 3), ("ail", "pièce", 1, 4), ("carotte", "pièce", 2, 6),
    ("pomme de terre", "pièce", 3, 8), ("courgette", "pièce", 1, 4), ("aubergine", "pièce", 1, 3),
    ("poivron", "pièce", 1, 3), ("champignon", "g", 150, 400), ("épinards", "g", 150, 500),
    ("farine", "g", 100, 500), ("sucre", "g", 30, 250), ("beurre", "g", 30, 200), ("riz", "g", 100, 400),
    ("pâtes", "g", 150, 500), ("lentilles", "g", 150, 300), ("pois chiches", "g", 150, 300),
    ("chocolat noir", "g", 100, 300), ("parmesan", "g", 30, 120), ("fromage de chèvre", "g", 80, 200),
    ("jambon", "g", 100, 300), ("poulet", "g", 300, 800), ("saumon", "g", 200, 600), ("bœuf haché", "g", 250, 600),
    ("lait", "ml", 100, 500), ("crème fraîche", "ml", 50, 250), ("huile d'olive", "ml", 10, 60),
    ("vinaigre balsamique", "cl", 1, 5), ("vin blanc", "cl", 5, 20), ("eau", "l", 1, 2), ("jus d'orange", "cl", 10, 30),
    ("miel", "c. à soupe", 1, 3), ("moutarde", "c. à café", 1, 3), ("cannelle", "c. à café", 1, 2),
    ("levure chimique", "c. à café", 1, 2), ("sel", "pincée", 1, 3), ("poivre", "pincée", 1, 3),
    ("curry", "c. à café", 1, 3), ("basilic", "pincée", 1, 3), ("thym", "pincée", 1, 3), ("œuf", "pièce", 1, 6),
    ("pâte brisée", "pièce", 1, 2), ("thé vert", "c. à soupe", 1, 3), ("menthe", "pincée", 1, 3),
    ("gingembre", "g", 5, 30), ("noix de coco râpée", "g", 20, 80), ("amandes", "g", 30, 120),
]

PLATS = {
    "entrée": ["Velouté", "Salade", "Tartare", "Soupe", "Feuilleté"],
    "plat": ["Gratin", "Curry", "Risotto", "Tajine", "Lasagnes", "Poêlée", "Parmentier", "Blanquette"],
    "dessert": ["Tarte", "Gâteau", "Crumble", "Mousse", "Clafoutis", "Flan", "Cookies"],
    "boisson": ["Smoothie", "Limonade", "Infusion", "Milkshake", "Thé glacé"],
    "accompagnement": ["Purée", "Légumes rôtis", "Riz pilaf", "Frites maison", "Gratin dauphinois"],
}
QUALIFICATIFS = ["de la grand-mère", "express", "du chef", "léger", "gourmand", "d'automne", "d'été",
                 "à la crème", "épicé", "croustillant", "fondant", "maison", "du dimanche", "familial"]
DIFFICULTES = ["facile", "facile", "moyen", "difficile"]
ETAPES = [
    "Préparer et laver tous les ingrédients.", "Couper les légumes en petits morceaux.",
    "Mélanger les ingrédients secs dans un grand saladier.", "Faire chauffer la matière grasse dans une poêle.",
    "Faire revenir à feu moyen en remuant.", "Ajouter le liquide et porter à frémissement.",
    "Assaisonner selon le goût.", "Laisser reposer quelques minutes.", "Enfourner à 180 °C.",
    "Dresser dans les assiettes et servir aussitôt.", "Laisser refroidir avant de démouler.",
    "Réserver au frais jusqu'au moment de servir.",
]
COMMENTAIRES = ["Délicieux !", "Très bonne recette, je recommande.", "Un peu long mais ça vaut le coup.",
                "Toute la famille a adoré.", "Pas mal, j'ai réduit le sucre.", "Facile et rapide.",
                "Moyen, trop salé pour moi.", "Je referai sans hésiter.", None, None, None]


def q(valeur):
    """Littéral SQL : NULL, nombre, booléen ou texte échappé."""
    if valeur is None:
        return "NULL"
    if isinstance(valeur, bool):
        return "TRUE" if valeur else "FALSE"
    if isinstance(valeur, (int, float)):
        return str(valeur)
    return "'" + str(valeur).replace("'", "''") + "'"


def lignes(table, colonnes, rangees):
    if not rangees:
        return ""
    corps = ",\n  ".join("(" + ", ".join(q(v) for v in r) + ")" for r in rangees)
    return f"INSERT INTO {table} ({', '.join(colonnes)}) VALUES\n  {corps};\n\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--utilisateurs", type=int, default=200)
    p.add_argument("--recettes", type=int, default=300)
    p.add_argument("--graine", type=int, default=42, help="graine aléatoire (même graine, mêmes données)")
    a = p.parse_args()
    rnd = random.Random(a.graine)
    aujourdhui = date(2026, 11, 13)

    # Utilisateurs : pseudo et e-mail uniques (RG1), 5 % de comptes désactivés (RG11)
    utilisateurs, pseudos = [], set()
    for i in range(1, a.utilisateurs + 1):
        pseudo = f"{rnd.choice(PRENOMS)}{i}"
        pseudos.add(pseudo)
        inscription = aujourdhui - timedelta(days=rnd.randint(30, 900))
        utilisateurs.append((i, pseudo, f"{pseudo}@exemple.fr", inscription.isoformat(), rnd.random() > 0.05))

    categories = [(i + 1, nom) for i, nom in enumerate(CATEGORIES)]
    ingredients = [(i + 1, ing[0]) for i, ing in enumerate(INGREDIENTS)]

    recettes, contenir, etapes = [], [], []
    titres_pris = set()
    date_pub = {}
    for rid in range(1, a.recettes + 1):
        auteur = rnd.randint(1, a.utilisateurs)
        cat_id = rnd.randint(1, len(CATEGORIES))
        # titre unique par auteur (RG10)
        for _ in range(50):
            titre = f"{rnd.choice(PLATS[CATEGORIES[cat_id - 1]])} {rnd.choice(QUALIFICATIFS)}"
            if (auteur, titre) not in titres_pris:
                break
        else:
            titre = f"{titre} n°{rid}"
        titres_pris.add((auteur, titre))
        publication = aujourdhui - timedelta(days=rnd.randint(0, 600))
        date_pub[rid] = publication
        recettes.append((rid, auteur, cat_id, titre, f"Recette « {titre} » partagée par la communauté.",
                         rnd.randint(1, 8), rnd.choice([5, 10, 15, 20, 30, 45]),
                         rnd.choice([0, 0, 10, 20, 30, 45, 60]), rnd.choice(DIFFICULTES), publication.isoformat()))
        # au moins un ingrédient, chacun une fois (RG4, RG5)
        for ing_id in rnd.sample(range(1, len(INGREDIENTS) + 1), rnd.randint(3, 9)):
            _, unite, qmin, qmax = INGREDIENTS[ing_id - 1]
            contenir.append((rid, ing_id, rnd.randint(qmin, qmax), unite))
        # au moins une étape, numérotées 1..n sans trou (RG6)
        for numero, texte in enumerate(rnd.sample(ETAPES, rnd.randint(3, 7)), start=1):
            etapes.append((rid, numero, texte, rnd.choice([None, None, 5, 10, 20, 30])))

    # Avis : un par couple, jamais par l'auteur de la recette (RG7, RG8)
    avis, favoris = [], []
    auteurs = {r[0]: r[1] for r in recettes}
    for rid in range(1, a.recettes + 1):
        candidats = [u for u in range(1, a.utilisateurs + 1) if u != auteurs[rid]]
        for u in rnd.sample(candidats, min(len(candidats), rnd.choice([0, 0, 1, 2, 3, 5, 8, 12]))):
            d = date_pub[rid] + timedelta(days=rnd.randint(0, 120))
            avis.append((u, rid, rnd.choice([1, 2, 3, 3, 4, 4, 4, 5, 5, 5]), rnd.choice(COMMENTAIRES),
                         min(d, aujourdhui).isoformat()))
        # Favoris : un par couple (RG9) ; l'auteur peut mettre sa propre recette en favori
        for u in rnd.sample(range(1, a.utilisateurs + 1), min(a.utilisateurs, rnd.choice([0, 1, 2, 4, 6, 10]))):
            d = date_pub[rid] + timedelta(days=rnd.randint(0, 200))
            favoris.append((u, rid, min(d, aujourdhui).isoformat()))

    sortie = [f"-- Données générées par generer_donnees.py (graine {a.graine}) : "
              f"{a.utilisateurs} utilisateurs, {a.recettes} recettes.\n"
              "-- À exécuter après creer_base_postgresql.sql. Vide d'abord les tables (aussi les données d'exemple).\n\n"
              "TRUNCATE favori, avis, contenir, etape, recette, ingredient, categorie, utilisateur RESTART IDENTITY CASCADE;\n\n"]
    sortie.append(lignes("utilisateur", ["id_utilisateur", "pseudo", "email", "date_inscription", "actif"], utilisateurs))
    sortie.append(lignes("categorie", ["id_categorie", "libelle"], categories))
    sortie.append(lignes("ingredient", ["id_ingredient", "nom"], ingredients))
    sortie.append(lignes("recette", ["id_recette", "id_auteur", "id_categorie", "titre", "description", "nb_portions",
                                     "temps_preparation_min", "temps_cuisson_min", "difficulte", "date_publication"], recettes))
    sortie.append(lignes("contenir", ["id_recette", "id_ingredient", "quantite", "unite"], contenir))
    sortie.append(lignes("etape", ["id_recette", "numero", "texte", "duree_min"], etapes))
    sortie.append(lignes("avis", ["id_utilisateur", "id_recette", "note", "commentaire", "date_avis"], avis))
    sortie.append(lignes("favori", ["id_utilisateur", "id_recette", "date_ajout"], favoris))
    # Les identifiants ont été fixés à la main : on remet les compteurs au bon niveau
    for table, colonne in [("utilisateur", "id_utilisateur"), ("categorie", "id_categorie"),
                           ("ingredient", "id_ingredient"), ("recette", "id_recette")]:
        sortie.append(f"SELECT setval(pg_get_serial_sequence('{table}', '{colonne}'), (SELECT MAX({colonne}) FROM {table}));\n")
    print("".join(sortie), end="")


if __name__ == "__main__":
    main()
