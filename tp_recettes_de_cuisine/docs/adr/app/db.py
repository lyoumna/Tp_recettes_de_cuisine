"""Accès à PostgreSQL. L'adresse de la base se règle avec la variable d'environnement DATABASE_URL."""
import os

import psycopg
from psycopg.rows import dict_row

URL = os.environ.get("DATABASE_URL", "postgresql://localhost/recettes")


def lire(sql, params=()):
    """Exécute un SELECT et renvoie la liste des lignes (dictionnaires)."""
    with psycopg.connect(URL, row_factory=dict_row) as conn:
        return conn.execute(sql, params).fetchall()


def ecrire(sql, params=()):
    """Exécute un INSERT / UPDATE / DELETE. Lève psycopg.Error si la base refuse (contrainte, trigger)."""
    with psycopg.connect(URL) as conn:
        conn.execute(sql, params)
