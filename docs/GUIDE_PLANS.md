# Plans TechDraw : mode d'emploi et liste des cotes (v2)

Scripts et menus Échelles normalisées (ISO 5455) : 1:2,5 – 1:2 – 1:1 – 5:1 – 1:5. Projection européenne (premier dièdre). Tolérances générales : ISO 2768-m. Matière : 316L.

## 0. Fichiers à placer dans `projet_echangeur/`
| Fichier | Rôle |
|---|---|
| `plans_techdraw.py` | crée les pages, les vues, les coupes et la nomenclature |
| `gabarits/Gabarit_A3_paysage_FR.svg`, `gabarits/Gabarit_A4_paysage_FR.svg` | gabarits (cadre ISO 5457, cartouche ISO 7200) |
| `appliquer_gabarits.py` | remplace le gabarit de chaque page et remplit le cartouche |
| `gen_gabarits.py` | régénère les deux SVG si tu veux modifier le cartouche (`python3 gen_gabarits.py`, crée le dossier `gabarits/`) |
| `export_plans.py` | exporte un PDF par page dans `plans/` |

## 1. Générer les pages
1. Ouvre `echangeur.FCStd`, bascule dans l'atelier **TechDraw**.
2. Console Python :
   `exec(open('/CHEMIN/VERS/projet_echangeur/plans_techdraw.py').read())`
   Chaque page affiche OK ou ECHEC.
3. Double-clique chaque page dans l'arbre et regarde les vues. Si une vue est tournée ou en miroir, change sa propriété `Direction` (face (0,-1,0), dessus (0,0,1), bout (1,0,0)) ou `XDirection`.
4. Si une coupe a échoué : sélectionne la vue de face, puis **Insérer une vue en coupe** et choisis le plan (voir §3).

## 2. Appliquer les gabarits et remplir le cartouche
Dans la console Python, document actif :
```
exec(open('/CHEMIN/VERS/projet_echangeur/appliquer_gabarits.py').read())
```
Le script remplace le gabarit de chaque page (A3 ou A4 selon l'ancien), puis remplit : titre, date du jour, feuille 1/1, numéro (ECH-P1 … ECH-ENS), échelle, type de document. Il affiche une ligne OK ou ECHEC par page. Les vues ne bougent pas.

Les champs suivants restent à vérifier ou à compléter à la main :
| Champ | Valeur par défaut | Remarque |
|---|---|---|
| Propriétaire légal | Boris Keubou Wamba | obligatoire ISO 7200 |
| Créé par / Approuvé par | B. Keubou Wamba | obligatoires ISO 7200 ; projet personnel, une seule personne |
| Titre | nom de la page | obligatoire |
| Titre complémentaire | Echangeur tubes et calandre | facultatif |
| Type de document | Dessin de piece / Dessin d'ensemble | obligatoire |
| Date d'émission | date du jour (AAAA-MM-JJ) | obligatoire |
| Indice | A | facultatif |
| Statut | Preliminaire | facultatif ; à changer seulement après vérification |
| Feuille | 1/1 | obligatoire |
| N° d'identification | ECH-Pn | obligatoire, dans le coin bas droit |
| Échelle, Matière, Tolérances générales | selon la page, 316L, ISO 2768-m | zone annexe au-dessus du cartouche |

Si une vue touche le cartouche : la zone annexe + le cartouche montent à 54 mm de haut (180 mm de large, en bas à droite). Déplace la vue avec des lignes simples, une par une (la console exige une ligne vide après une boucle `for`) :
```
d = App.ActiveDocument
d.getObject("NomDeLaVue").X = 150
d.getObject("NomDeLaVue").Y = 120
d.recompute()
```
Le nom interne de la vue est dans la propriété `Name`.

## 3. Cotes à poser (cotes fonctionnelles seulement, sans doublon ni chaîne fermée)
| Page | Cotes |
|---|---|
| P1 Calandre | Ø168,3 ; épaisseur 4,5 ; longueur 500 ; 2 × Ø52,5 ; positions 100 et 400 depuis l'extrémité gauche (un trou en haut, un en bas : l'indiquer par une note ou une vue de dessus) |
| P2 Plaque | Ø230 ; épaisseur 25 ; 19 × Ø19,0 ; pas 25,4 (vertical) et 21,997 (horizontal, rangées décalées) ; 8 × Ø14 sur Ø195 ; **détail 5:1 du ligament 6,4** (25,4 − 19,0) |
| P3 Tube | Ø19,05 ; épaisseur 1,65 ; longueur 550 |
| P4 Chicane | Ø156 ; épaisseur 5 ; 16 × Ø19,8 ; fenêtre de 45 mesurée depuis le bord du disque ; position de la rangée de trous |
| P5 Boîte | bride Ø230 × 20 ; virole Ø168,3 × 4,5 sur 68 ; fond de 12 ; longueur totale 100 ; trou Ø52,5 à 54 de la face de bride ; 8 × Ø14 sur Ø195 ; coupe A-A |
| P6 Tubulure | Ø60,3 × 3,9 ; de 60 à 154,15 de l'axe de la calandre ; profil de selle (Ø159,3) |
| P7 Patte | bloc 50 × 80 ; hauteur 39,15 ; alésage Ø159,3 |
| Ensemble | longueur hors-tout 750 ; calandre 500 ; positions des tubulures (−54, 125, 425, 604) ; hauteur hors-tout 308,3 ; Ø bride 230 ; entraxe des pattes ; ballons 1 à 7 ; nomenclature ; masse totale |

Dans TechDraw : sélectionne l'arête ou deux points dans la vue, puis l'icône de cote (longueur, rayon, diamètre). Les lignes d'axe : **Insérer une ligne d'axe** après sélection de deux arêtes. Les ballons : **Insérer un ballon** sur la vue d'ensemble, numérotés comme la colonne « Rep » de la nomenclature.

## 4. Points à décider ou à vérifier avant de coter
- **Trous Ø19,0 de la plaque P2.** Cette valeur vient du choix de modélisation (trou plus petit que le tube Ø19,05, pour que la fusion booléenne soit robuste). Elle n'est pas une cote de fabrication. Soit tu cotes la valeur du modèle avec une note « Ø19,0 : valeur de modélisation, à ajuster à la fabrication », soit tu choisis un trou de fabrication (par exemple Ø19,1 H11) dans le plan et tu le dis dans le rapport.
- **Position de la 2e chicane.** L'ancien guide donne x = 195 et x = 355. Ton diagnostic indique une chicane en x 192 à 198 (centre 195) et l'autre en x 326 à 330 environ, donc autour de 328. Mesure avec l'outil Mesure du CAD avant de coter, et cote la valeur réelle.
- **Chicanes et pièce fusionnée.** Elles figurent au plan d'ensemble mais pas dans le modèle de calcul : une note l'indique.

## 5. Ce que les gabarits respectent de l'ISO 5457 et de l'ISO 7200
Vérifié sur le texte des normes (ISO 5457:1999 et ISO 7200:2004) :
- **ISO 5457** : bordure de 20 mm à gauche (cadre compris) et de 10 mm ailleurs ; cadre continu de 0,7 mm ; quatre repères de centrage de 0,7 mm (de la bande de repères jusqu'à 10 mm dans le cadre) ; repères de zone en champs de 50 mm à partir des axes de symétrie, chiffres de 3,5 mm, lettres sans I ni O, traits de 0,35 mm, A3 : 8 × 6 champs, A4 : 6 × 4 champs ; repères de coupe aux quatre coins (deux rectangles superposés de 10 × 5 mm) ; format inscrit en bordure basse à droite.
- **ISO 7200** : les huit champs obligatoires sont présents (propriétaire légal, numéro d'identification, date d'émission, numéro de feuille, titre, approbateur, créateur, type de document). Le numéro d'identification est dans le coin bas droit. L'échelle, le symbole de projection et les tolérances générales sont hors cartouche, dans la zone annexe au-dessus.

**Écarts assumés :**
- A4 en paysage (la norme veut l'A4 en portrait, cartouche dans la partie basse).
- Repères de zone sur les quatre côtés de l'A4 (la norme les met seulement en haut et à droite) : choix pour avoir des bordures symétriques.
- Largeur du cartouche de 180 mm : valeur non vérifiée dans la norme.
- Bande de repères de 5 mm : valeur relevée hors norme.
- Proportions du symbole de projection (1er dièdre : cercles à gauche, tronc de cône à droite) et des repères de coupe : approximatives, non comparées à l'ISO 5456-2.
- Sur l'A4, le repère de centrage du bas s'arrête au cadre pour ne pas traverser le cartouche.
- Propriétaire, créateur et approbateur sont la même personne (projet personnel). Ne présente pas ces plans comme des documents certifiés conformes aux normes.

## 6. Exporter
`exec(open('/CHEMIN/VERS/projet_echangeur/export_plans.py').read())` écrit un PDF par page dans `plans/`. Sinon : clic droit sur la page → **Exporter la page en PDF**. Garde aussi `echangeur.FCStd` (les plans sont régénérés à partir du modèle).

## 7. Plan d'ensemble : version corrigée (plan_ensemble_cote.py)
Le plan d'ensemble exporté de TechDraw avait trois défauts de fond : échelle 1:2,5 trop grande pour coter proprement sur A3, vue de dessous placée sous la coupe (disposition du 3e dièdre alors que la page annonce le 1er dièdre), et cotes de détail répétées. `plan_ensemble_cote.py` reprend la géométrie réelle de l'export SVG, retire les anciennes cotes, remet les vues en 1er dièdre à l'échelle 1:5 et ajoute la cotation, les ballons, le tracé de coupe A-A, la nomenclature et les notes.

Usage : exporter la page en SVG (clic droit sur la page → Exporter en SVG), puis
`python3 plan_ensemble_cote.py Plan_ensemble.svg sortie/Plan_ensemble_cote.svg`
puis `rsvg-convert -f pdf -o Plan_ensemble_cote.pdf sortie/Plan_ensemble_cote.svg`.
Le fichier produit n'est plus lié à FreeCAD : une modification du modèle impose de réexporter et de relancer le script.

Pour reproduire la même mise en page dans FreeCAD :
1. Mettre les trois vues à l'échelle 0.2 (propriété `Scale`, `Scale Type` = `Custom`).
2. Placer la vue de dessous au-dessus de la coupe, alignée en x, et la vue de bout à gauche de la coupe, alignée en y.
3. Supprimer les anciennes cotes (objets `Cote…` des trois vues) puis recréer celles du PDF : positions des tubulures depuis la face gauche (46, 225, 525, 704), 500, 190 et 210 pour les pattes, 100 / 550 / 100, 750 en référence, 308,3 et Ø230, Ø168,3, Ø195, 8× Ø14 sur la vue de bout, 2× 50 et 80 sur la vue de dessous.
