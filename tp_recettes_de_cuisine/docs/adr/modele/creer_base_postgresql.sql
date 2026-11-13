-- Site de recettes de cuisine : version relationnelle (PostgreSQL), à ouvrir dans pgAdmin (Query Tool).
-- Traduction du MCD de CONCEPTION.md par les règles de passage du cours.
-- La base choisie dans l'ADR reste MongoDB : ce script est le prototype relationnel du même MCD.

DROP TABLE IF EXISTS favori, avis, contenir, etape, recette, ingredient, categorie, utilisateur CASCADE;
DROP TYPE IF EXISTS unite_mesure;

CREATE TYPE unite_mesure AS ENUM ('g','kg','ml','cl','l','c. à café','c. à soupe','pièce','pincée');

CREATE TABLE utilisateur (
    id_utilisateur   SERIAL PRIMARY KEY,
    pseudo           VARCHAR(50)  NOT NULL UNIQUE,                  -- RG1
    email            VARCHAR(255) NOT NULL UNIQUE,                  -- RG1
    date_inscription DATE         NOT NULL DEFAULT CURRENT_DATE,
    actif            BOOLEAN      NOT NULL DEFAULT TRUE             -- RG11 : désactivé, jamais supprimé
);

CREATE TABLE categorie (
    id_categorie SERIAL PRIMARY KEY,
    libelle      VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE ingredient (
    id_ingredient SERIAL PRIMARY KEY,
    nom           VARCHAR(100) NOT NULL UNIQUE                      -- RG4
);

CREATE TABLE recette (
    id_recette            SERIAL PRIMARY KEY,
    id_auteur             INT NOT NULL REFERENCES utilisateur(id_utilisateur),   -- RG2
    id_categorie          INT NOT NULL REFERENCES categorie(id_categorie),       -- RG3
    titre                 VARCHAR(150) NOT NULL,                                 -- RG10
    description           TEXT,
    nb_portions           INT NOT NULL CHECK (nb_portions >= 1),                 -- RG10
    temps_preparation_min INT NOT NULL CHECK (temps_preparation_min >= 0),       -- RG10
    temps_cuisson_min     INT NOT NULL CHECK (temps_cuisson_min >= 0),           -- RG10
    difficulte            VARCHAR(20),
    date_publication      DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (id_auteur, titre)                                                    -- RG10
);

-- Entité faible : identifiant relatif (id_recette, numero). RG6, RG11
CREATE TABLE etape (
    id_recette INT NOT NULL REFERENCES recette(id_recette) ON DELETE CASCADE,
    numero     INT NOT NULL CHECK (numero >= 1),
    texte      TEXT NOT NULL,
    duree_min  INT CHECK (duree_min >= 0),
    PRIMARY KEY (id_recette, numero)
);

-- Association CONTENIR (quantité, unité). RG4, RG5, RG11
CREATE TABLE contenir (
    id_recette    INT NOT NULL REFERENCES recette(id_recette) ON DELETE CASCADE,
    id_ingredient INT NOT NULL REFERENCES ingredient(id_ingredient),             -- pas de cascade : le catalogue reste
    quantite      NUMERIC(10,2) NOT NULL CHECK (quantite > 0),
    unite         unite_mesure  NOT NULL,
    PRIMARY KEY (id_recette, id_ingredient)                                      -- un ingrédient une fois par recette
);

-- Association NOTER (note, commentaire, date). RG7, RG11
CREATE TABLE avis (
    id_utilisateur INT NOT NULL REFERENCES utilisateur(id_utilisateur),
    id_recette     INT NOT NULL REFERENCES recette(id_recette) ON DELETE CASCADE,
    note           INT NOT NULL CHECK (note BETWEEN 1 AND 5),
    commentaire    TEXT,
    date_avis      DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (id_utilisateur, id_recette)
);

-- Association METTRE EN FAVORI (date d'ajout). RG9, RG11
CREATE TABLE favori (
    id_utilisateur INT NOT NULL REFERENCES utilisateur(id_utilisateur),
    id_recette     INT NOT NULL REFERENCES recette(id_recette) ON DELETE CASCADE,
    date_ajout     DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (id_utilisateur, id_recette)
);

-- RG8 : un utilisateur ne note pas sa propre recette (contrainte entre deux tables : trigger).
CREATE OR REPLACE FUNCTION interdire_avis_auteur() RETURNS trigger AS $$
BEGIN
    IF NEW.id_utilisateur = (SELECT id_auteur FROM recette WHERE id_recette = NEW.id_recette) THEN
        RAISE EXCEPTION 'RG8 : un utilisateur ne peut pas noter sa propre recette';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_avis_pas_auteur
    BEFORE INSERT OR UPDATE ON avis
    FOR EACH ROW EXECUTE FUNCTION interdire_avis_auteur();

-- Index pour les lectures fréquentes de l'ADR
CREATE INDEX idx_recette_categorie  ON recette(id_categorie);
CREATE INDEX idx_contenir_ingredient ON contenir(id_ingredient);
CREATE INDEX idx_avis_recette       ON avis(id_recette);
