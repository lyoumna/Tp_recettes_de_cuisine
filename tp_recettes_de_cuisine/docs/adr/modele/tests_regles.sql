-- Vérifie que la base refuse les données qui violent les règles de gestion.
-- Chaque test doit afficher « OK ». S'exécute dans une transaction annulée : aucune donnée n'est modifiée.
-- Usage : psql -d recettes -f modele/tests_regles.sql   (après avoir chargé des données)

BEGIN;

CREATE FUNCTION pg_temp.doit_echouer(nom TEXT, instruction TEXT) RETURNS void AS $$
BEGIN
    BEGIN
        EXECUTE instruction;
        RAISE NOTICE 'ECHEC : % (la base a accepté une donnée interdite)', nom;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'OK     : % -> %', nom, SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;

SELECT pg_temp.doit_echouer('RG1 pseudo déjà pris',
  $t$INSERT INTO utilisateur(pseudo,email) SELECT pseudo,'autre@exemple.fr' FROM utilisateur LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG1 e-mail déjà pris',
  $t$INSERT INTO utilisateur(pseudo,email) SELECT 'nouveau_pseudo',email FROM utilisateur LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG4 ingrédient en double dans le catalogue',
  $t$INSERT INTO ingredient(nom) SELECT nom FROM ingredient LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG5 quantité nulle',
  $t$UPDATE contenir SET quantite = 0 WHERE ctid = (SELECT ctid FROM contenir LIMIT 1)$t$);
SELECT pg_temp.doit_echouer('RG5 unité hors liste',
  $t$UPDATE contenir SET unite = 'tasse' WHERE ctid = (SELECT ctid FROM contenir LIMIT 1)$t$);
SELECT pg_temp.doit_echouer('RG5 même ingrédient deux fois dans une recette',
  $t$INSERT INTO contenir SELECT * FROM contenir LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG6 étape numérotée 0',
  $t$UPDATE etape SET numero = 0 WHERE ctid = (SELECT ctid FROM etape LIMIT 1)$t$);
SELECT pg_temp.doit_echouer('RG6 texte d''étape vide (NULL)',
  $t$UPDATE etape SET texte = NULL WHERE ctid = (SELECT ctid FROM etape LIMIT 1)$t$);
SELECT pg_temp.doit_echouer('RG7 note de 6',
  $t$UPDATE avis SET note = 6 WHERE ctid = (SELECT ctid FROM avis LIMIT 1)$t$);
SELECT pg_temp.doit_echouer('RG7 deuxième avis du même utilisateur sur la même recette',
  $t$INSERT INTO avis SELECT * FROM avis LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG8 avis de l''auteur sur sa recette',
  $t$INSERT INTO avis(id_utilisateur,id_recette,note) SELECT id_auteur,id_recette,5 FROM recette
     WHERE NOT EXISTS (SELECT 1 FROM avis a WHERE a.id_recette = recette.id_recette AND a.id_utilisateur = recette.id_auteur) LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG9 favori en double',
  $t$INSERT INTO favori SELECT * FROM favori LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG10 portions = 0',
  $t$UPDATE recette SET nb_portions = 0 WHERE id_recette = (SELECT MIN(id_recette) FROM recette)$t$);
SELECT pg_temp.doit_echouer('RG10 temps négatif',
  $t$UPDATE recette SET temps_cuisson_min = -5 WHERE id_recette = (SELECT MIN(id_recette) FROM recette)$t$);
SELECT pg_temp.doit_echouer('RG10 même titre pour un même auteur',
  $t$INSERT INTO recette(id_auteur,id_categorie,titre,nb_portions,temps_preparation_min,temps_cuisson_min)
     SELECT id_auteur,id_categorie,titre,1,0,0 FROM recette LIMIT 1$t$);
SELECT pg_temp.doit_echouer('RG2 recette sans auteur',
  $t$INSERT INTO recette(id_auteur,id_categorie,titre,nb_portions,temps_preparation_min,temps_cuisson_min)
     VALUES (NULL,1,'x',1,0,0)$t$);
SELECT pg_temp.doit_echouer('RG3 recette dans une catégorie inexistante',
  $t$INSERT INTO recette(id_auteur,id_categorie,titre,nb_portions,temps_preparation_min,temps_cuisson_min)
     VALUES (1,-1,'x',1,0,0)$t$);
SELECT pg_temp.doit_echouer('RG11 supprimer un utilisateur qui a des recettes',
  $t$DELETE FROM utilisateur WHERE id_utilisateur = (SELECT id_auteur FROM recette LIMIT 1)$t$);
SELECT pg_temp.doit_echouer('RG11 supprimer un ingrédient utilisé',
  $t$DELETE FROM ingredient WHERE id_ingredient = (SELECT id_ingredient FROM contenir LIMIT 1)$t$);

-- RG11 : la suppression d'une recette emporte ses étapes, ingrédients, avis et favoris, rien d'autre.
DO $$
DECLARE r INT; n_ing INT; n_cat INT; n_usr INT; reste INT;
BEGIN
    SELECT id_recette INTO r FROM recette r
      WHERE EXISTS (SELECT 1 FROM avis a WHERE a.id_recette = r.id_recette)
        AND EXISTS (SELECT 1 FROM favori f WHERE f.id_recette = r.id_recette) LIMIT 1;
    SELECT count(*) INTO n_ing FROM ingredient;
    SELECT count(*) INTO n_cat FROM categorie;
    SELECT count(*) INTO n_usr FROM utilisateur;
    DELETE FROM recette WHERE id_recette = r;
    SELECT (SELECT count(*) FROM etape WHERE id_recette = r) + (SELECT count(*) FROM contenir WHERE id_recette = r)
         + (SELECT count(*) FROM avis WHERE id_recette = r) + (SELECT count(*) FROM favori WHERE id_recette = r) INTO reste;
    IF reste = 0 AND n_ing = (SELECT count(*) FROM ingredient) AND n_cat = (SELECT count(*) FROM categorie)
       AND n_usr = (SELECT count(*) FROM utilisateur) THEN
        RAISE NOTICE 'OK     : RG11 la suppression d''une recette emporte ses étapes, ingrédients, avis et favoris, et rien d''autre';
    ELSE
        RAISE NOTICE 'ECHEC : RG11 cascade';
    END IF;
END $$;

ROLLBACK;
