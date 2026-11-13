-- Petit jeu de données d'exemple (à exécuter après creer_base_postgresql.sql).
INSERT INTO utilisateur (pseudo, email) VALUES
 ('lea','lea@example.com'), ('tom','tom@example.com'), ('sam','sam@example.com');

INSERT INTO categorie (libelle) VALUES ('entrée'), ('plat'), ('dessert'), ('boisson');

INSERT INTO ingredient (nom) VALUES ('pomme'), ('farine'), ('beurre'), ('sucre'), ('tomate');

INSERT INTO recette (id_auteur, id_categorie, titre, description, nb_portions, temps_preparation_min, temps_cuisson_min, difficulte) VALUES
 (1, 3, 'Tarte aux pommes', 'Classique', 6, 30, 40, 'facile'),
 (2, 2, 'Salade de tomates', 'Simple', 2, 10, 0, 'facile');

INSERT INTO contenir (id_recette, id_ingredient, quantite, unite) VALUES
 (1, 1, 5,   'pièce'), (1, 2, 250, 'g'), (1, 3, 100, 'g'), (1, 4, 80, 'g'),
 (2, 5, 4,   'pièce');

INSERT INTO etape (id_recette, numero, texte, duree_min) VALUES
 (1, 1, 'Étaler la pâte.', NULL), (1, 2, 'Disposer les pommes.', NULL), (1, 3, 'Cuire au four.', 40),
 (2, 1, 'Couper les tomates et assaisonner.', NULL);

INSERT INTO avis (id_utilisateur, id_recette, note, commentaire) VALUES
 (2, 1, 5, 'Délicieuse'), (3, 1, 4, 'Très bonne'), (1, 2, 3, 'Correct');

INSERT INTO favori (id_utilisateur, id_recette) VALUES (2, 1), (3, 1), (1, 2);
