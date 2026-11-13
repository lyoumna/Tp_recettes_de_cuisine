-- Quelques requêtes qui répondent aux usages de l'ADR (à exécuter après creer_base_postgresql.sql
-- et donnees_exemple.sql).

-- 1. Afficher une recette complète : en-tête, ingrédients, étapes
SELECT r.titre, u.pseudo AS auteur, c.libelle AS categorie, r.nb_portions
FROM recette r
JOIN utilisateur u ON u.id_utilisateur = r.id_auteur
JOIN categorie c   ON c.id_categorie   = r.id_categorie
WHERE r.id_recette = 1;

SELECT i.nom, ct.quantite, ct.unite
FROM contenir ct JOIN ingredient i USING (id_ingredient)
WHERE ct.id_recette = 1;

SELECT numero, texte FROM etape WHERE id_recette = 1 ORDER BY numero;

-- 2. Lister les recettes d'une catégorie, avec la note moyenne
SELECT r.id_recette, r.titre, ROUND(AVG(a.note), 2) AS note_moyenne, COUNT(a.note) AS nb_avis
FROM recette r
JOIN categorie c ON c.id_categorie = r.id_categorie
LEFT JOIN avis a ON a.id_recette = r.id_recette
WHERE c.libelle = 'dessert'
GROUP BY r.id_recette, r.titre
ORDER BY note_moyenne DESC NULLS LAST;

-- 3. Quelles recettes utilisent la pomme ?
SELECT r.titre
FROM recette r
JOIN contenir ct USING (id_recette)
JOIN ingredient i USING (id_ingredient)
WHERE i.nom = 'pomme';

-- 4. Lire les avis d'une recette, page par page
SELECT u.pseudo, a.note, a.commentaire, a.date_avis
FROM avis a JOIN utilisateur u USING (id_utilisateur)
WHERE a.id_recette = 1
ORDER BY a.date_avis DESC
LIMIT 20 OFFSET 0;

-- 5. Favoris d'un utilisateur
SELECT r.titre, f.date_ajout
FROM favori f JOIN recette r USING (id_recette)
WHERE f.id_utilisateur = 2
ORDER BY f.date_ajout DESC;

-- 6. Recettes les mieux notées (au moins 3 avis)
SELECT r.titre, u.pseudo AS auteur, ROUND(AVG(a.note), 2) AS note_moyenne, COUNT(*) AS nb_avis
FROM recette r
JOIN utilisateur u ON u.id_utilisateur = r.id_auteur
JOIN avis a        ON a.id_recette = r.id_recette
GROUP BY r.id_recette, r.titre, u.pseudo
HAVING COUNT(*) >= 3
ORDER BY note_moyenne DESC, nb_avis DESC
LIMIT 10;

-- 7. Recettes sans aucun avis
SELECT r.id_recette, r.titre
FROM recette r
WHERE NOT EXISTS (SELECT 1 FROM avis a WHERE a.id_recette = r.id_recette)
ORDER BY r.id_recette
LIMIT 10;

-- 8. Nombre de recettes par catégorie (une catégorie vide apparaît avec 0)
SELECT c.libelle, COUNT(r.id_recette) AS nb_recettes
FROM categorie c LEFT JOIN recette r USING (id_categorie)
GROUP BY c.libelle
ORDER BY nb_recettes DESC;

-- 9. Recettes contenant TOUS les ingrédients demandés (ici pomme ET farine)
SELECT r.titre
FROM recette r
JOIN contenir ct USING (id_recette)
JOIN ingredient i USING (id_ingredient)
WHERE i.nom IN ('pomme', 'farine')
GROUP BY r.id_recette, r.titre
HAVING COUNT(DISTINCT i.id_ingredient) = 2;

-- 10. Recettes les plus mises en favori
SELECT r.titre, COUNT(*) AS nb_favoris
FROM favori f JOIN recette r USING (id_recette)
GROUP BY r.id_recette, r.titre
ORDER BY nb_favoris DESC, r.titre
LIMIT 10;

-- 11. Utilisateurs les plus actifs : recettes publiées et avis donnés
SELECT u.pseudo,
       (SELECT COUNT(*) FROM recette r WHERE r.id_auteur = u.id_utilisateur) AS recettes_publiees,
       (SELECT COUNT(*) FROM avis a WHERE a.id_utilisateur = u.id_utilisateur) AS avis_donnes
FROM utilisateur u
WHERE u.actif
ORDER BY recettes_publiees DESC, avis_donnes DESC
LIMIT 10;

-- 12. Ingrédients du catalogue qui ne servent dans aucune recette
SELECT i.nom
FROM ingredient i
WHERE NOT EXISTS (SELECT 1 FROM contenir c WHERE c.id_ingredient = i.id_ingredient);
