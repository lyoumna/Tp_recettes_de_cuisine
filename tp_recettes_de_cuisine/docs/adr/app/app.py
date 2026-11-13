"""Petite application web pour le site de recettes : lire les recettes, donner un avis, mettre en favori.

    pip install -r app/requirements.txt
    flask --app app/app.py run          (ou : python3 app/app.py)

Pas d'authentification : on choisit « qui on est » dans une liste (c'est un TP). Les règles de gestion sont
garanties par la base ; l'application affiche simplement le message de la base quand elle refuse une écriture
(par exemple RG8 : on ne note pas sa propre recette).
"""
import psycopg
from flask import Flask, redirect, render_template_string, request, url_for

import db

app = Flask(__name__)

PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recettes</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:16px;line-height:1.45}
 header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;border-bottom:1px solid #ccc;padding-bottom:8px}
 a{color:#0b5cad} table{border-collapse:collapse;width:100%} td,th{padding:6px 8px;border-bottom:1px solid #ddd;text-align:left}
 .erreur{background:#fde8e8;border:1px solid #e0a0a0;padding:8px 12px;border-radius:6px}
 .ok{background:#e6f4ea;border:1px solid #9fcfae;padding:8px 12px;border-radius:6px}
 form.inline{display:inline} .muted{color:#666} input,select,textarea,button{font:inherit;padding:4px 8px}
</style></head><body>
<header><a href="{{ url_for('accueil', moi=moi) }}"><strong>🍳 Recettes</strong></a>
 <form method="get"><label>Je suis
  <select name="moi" onchange="this.form.submit()">
   <option value="">— choisir —</option>
   {% for u in utilisateurs %}<option value="{{ u.id_utilisateur }}" {{ 'selected' if u.id_utilisateur == moi }}>{{ u.pseudo }}</option>{% endfor %}
  </select></label></form></header>
{% if message %}<p class="{{ 'erreur' if erreur else 'ok' }}">{{ message }}</p>{% endif %}
{{ corps|safe }}
</body></html>"""

LISTE = """<h1>Recettes</h1>
<form method="get">
 <input type="hidden" name="moi" value="{{ moi or '' }}">
 <select name="categorie"><option value="">Toutes les catégories</option>
  {% for c in categories %}<option value="{{ c.id_categorie }}" {{ 'selected' if c.id_categorie == categorie }}>{{ c.libelle }}</option>{% endfor %}</select>
 <input name="ingredient" value="{{ ingredient }}" placeholder="Ingrédient (ex. pomme)">
 <button>Filtrer</button></form>
<p class="muted">{{ recettes|length }} recette(s){{ ' (20 premières)' if recettes|length == 20 }}</p>
<table><tr><th>Recette</th><th>Catégorie</th><th>Auteur</th><th>Note</th></tr>
{% for r in recettes %}<tr>
 <td><a href="{{ url_for('recette', id_recette=r.id_recette, moi=moi) }}">{{ r.titre }}</a></td>
 <td>{{ r.categorie }}</td><td>{{ r.auteur }}</td>
 <td>{% if r.nb_avis %}{{ r.note_moyenne }} / 5 ({{ r.nb_avis }}){% else %}<span class="muted">—</span>{% endif %}</td></tr>
{% endfor %}</table>"""

FICHE = """<p><a href="{{ url_for('accueil', moi=moi) }}">← Toutes les recettes</a></p>
<h1>{{ r.titre }}</h1>
<p class="muted">{{ r.categorie }} · par {{ r.auteur }} · {{ r.nb_portions }} portion(s) · préparation {{ r.temps_preparation_min }} min · cuisson {{ r.temps_cuisson_min }} min{% if r.difficulte %} · {{ r.difficulte }}{% endif %}</p>
<p>{{ r.description or '' }}</p>
<p><strong>{% if moyenne.nb_avis %}{{ moyenne.note_moyenne }} / 5{% else %}Pas encore noté{% endif %}</strong>
 <span class="muted">({{ moyenne.nb_avis }} avis)</span>
 {% if moi %}<form class="inline" method="post" action="{{ url_for('favori', id_recette=r.id_recette) }}">
  <input type="hidden" name="moi" value="{{ moi }}"><button>{{ '★ Retirer des favoris' if est_favori else '☆ Mettre en favori' }}</button></form>{% endif %}</p>
<h2>Ingrédients</h2>
<ul>{% for i in ingredients %}<li>{{ i.quantite }} {{ i.unite }} {{ i.nom }}</li>{% endfor %}</ul>
<h2>Étapes</h2>
<ol>{% for e in etapes %}<li>{{ e.texte }}{% if e.duree_min %} <span class="muted">({{ e.duree_min }} min)</span>{% endif %}</li>{% endfor %}</ol>
<h2>Avis</h2>
{% if moi %}<form method="post" action="{{ url_for('donner_avis', id_recette=r.id_recette) }}">
 <input type="hidden" name="moi" value="{{ moi }}">
 <label>Note <select name="note">{% for n in [5,4,3,2,1] %}<option>{{ n }}</option>{% endfor %}</select></label>
 <input name="commentaire" placeholder="Commentaire (facultatif)" size="40"><button>Donner mon avis</button></form>
{% else %}<p class="muted">Choisissez qui vous êtes (en haut à droite) pour donner un avis ou un favori.</p>{% endif %}
<table>{% for a in avis %}<tr><td>{{ a.pseudo }}</td><td>{{ a.note }} / 5</td><td>{{ a.commentaire or '' }}</td><td class="muted">{{ a.date_avis }}</td></tr>
{% else %}<tr><td class="muted">Aucun avis.</td></tr>{% endfor %}</table>"""


def moi_courant():
    """Identifiant de l'utilisateur choisi dans la liste (None si personne)."""
    valeur = request.values.get("moi", "")
    return int(valeur) if valeur.isdigit() else None


def afficher(modele, message=None, erreur=False, **contexte):
    moi = moi_courant()
    utilisateurs = db.lire("SELECT id_utilisateur, pseudo FROM utilisateur WHERE actif ORDER BY pseudo")
    corps = render_template_string(modele, moi=moi, **contexte)
    return render_template_string(PAGE, corps=corps, moi=moi, utilisateurs=utilisateurs, message=message, erreur=erreur)


@app.get("/")
def accueil():
    categorie = request.args.get("categorie", "")
    ingredient = request.args.get("ingredient", "").strip()
    categorie = int(categorie) if categorie.isdigit() else None
    recettes = db.lire(
        """SELECT r.id_recette, r.titre, c.libelle AS categorie, u.pseudo AS auteur,
                  ROUND(AVG(a.note), 2) AS note_moyenne, COUNT(a.note) AS nb_avis
           FROM recette r
           JOIN categorie c   ON c.id_categorie = r.id_categorie
           JOIN utilisateur u ON u.id_utilisateur = r.id_auteur
           LEFT JOIN avis a   ON a.id_recette = r.id_recette
           WHERE (%(cat)s::int IS NULL OR r.id_categorie = %(cat)s)
             AND (%(ing)s = '' OR EXISTS (SELECT 1 FROM contenir ct JOIN ingredient i USING (id_ingredient)
                                          WHERE ct.id_recette = r.id_recette AND i.nom ILIKE %(ing)s))
           GROUP BY r.id_recette, c.libelle, u.pseudo
           ORDER BY r.date_publication DESC, r.id_recette DESC
           LIMIT 20""",
        {"cat": categorie, "ing": ingredient},
    )
    categories = db.lire("SELECT id_categorie, libelle FROM categorie ORDER BY libelle")
    return afficher(LISTE, recettes=recettes, categories=categories, categorie=categorie, ingredient=ingredient)


def charger_fiche(id_recette):
    """Toutes les données d'une recette, ou None si elle n'existe pas."""
    fiche = db.lire(
        """SELECT r.*, c.libelle AS categorie, u.pseudo AS auteur
           FROM recette r JOIN categorie c USING (id_categorie) JOIN utilisateur u ON u.id_utilisateur = r.id_auteur
           WHERE r.id_recette = %s""", (id_recette,))
    if not fiche:
        return None
    moi = moi_courant()
    return {
        "r": fiche[0],
        "ingredients": db.lire("""SELECT i.nom, ct.quantite::float AS quantite, ct.unite
                                  FROM contenir ct JOIN ingredient i USING (id_ingredient)
                                  WHERE ct.id_recette = %s ORDER BY i.nom""", (id_recette,)),
        "etapes": db.lire("SELECT numero, texte, duree_min FROM etape WHERE id_recette = %s ORDER BY numero", (id_recette,)),
        "avis": db.lire("""SELECT u.pseudo, a.note, a.commentaire, a.date_avis
                           FROM avis a JOIN utilisateur u USING (id_utilisateur)
                           WHERE a.id_recette = %s ORDER BY a.date_avis DESC LIMIT 20""", (id_recette,)),
        "moyenne": db.lire("SELECT ROUND(AVG(note), 2) AS note_moyenne, COUNT(*) AS nb_avis FROM avis WHERE id_recette = %s",
                           (id_recette,))[0],
        "est_favori": bool(moi and db.lire("SELECT 1 FROM favori WHERE id_utilisateur = %s AND id_recette = %s",
                                           (moi, id_recette))),
    }


def page_recette(id_recette, message=None, erreur=False):
    donnees = charger_fiche(id_recette)
    if donnees is None:
        return "Recette introuvable", 404
    return afficher(FICHE, message=message, erreur=erreur, **donnees)


@app.get("/recette/<int:id_recette>")
def recette(id_recette):
    return page_recette(id_recette)


@app.post("/recette/<int:id_recette>/avis")
def donner_avis(id_recette):
    moi = moi_courant()
    if moi is None:
        return page_recette(id_recette, "Choisissez d'abord qui vous êtes.", erreur=True)
    try:
        # RG7 : un seul avis par couple ; en donner un deuxième le remplace. RG8 est refusée par le trigger.
        db.ecrire(
            """INSERT INTO avis (id_utilisateur, id_recette, note, commentaire) VALUES (%s, %s, %s, NULLIF(%s, ''))
               ON CONFLICT (id_utilisateur, id_recette)
               DO UPDATE SET note = EXCLUDED.note, commentaire = EXCLUDED.commentaire, date_avis = CURRENT_DATE""",
            (moi, id_recette, int(request.form.get("note", 0)), request.form.get("commentaire", "").strip()))
    except psycopg.Error as e:
        return page_recette(id_recette, str(e).splitlines()[0], erreur=True)
    return page_recette(id_recette, "Avis enregistré.")


@app.post("/recette/<int:id_recette>/favori")
def favori(id_recette):
    moi = moi_courant()
    if moi is None:
        return page_recette(id_recette, "Choisissez d'abord qui vous êtes.", erreur=True)
    try:
        if db.lire("SELECT 1 FROM favori WHERE id_utilisateur = %s AND id_recette = %s", (moi, id_recette)):
            db.ecrire("DELETE FROM favori WHERE id_utilisateur = %s AND id_recette = %s", (moi, id_recette))
        else:
            db.ecrire("INSERT INTO favori (id_utilisateur, id_recette) VALUES (%s, %s)", (moi, id_recette))
    except psycopg.Error as e:
        return page_recette(id_recette, str(e).splitlines()[0], erreur=True)
    return redirect(url_for("recette", id_recette=id_recette, moi=moi))


if __name__ == "__main__":
    app.run(debug=True)
