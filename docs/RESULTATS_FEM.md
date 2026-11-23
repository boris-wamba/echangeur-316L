# Résultats FEM — échangeur à tubes et calandre, 316L (demi-modèle)

Statut : résultats **préliminaires** d'une étude exploratoire. Calculs CalculiX 2.23 (FreeCAD 1.1.3), éléments tétraédriques du second ordre, élasticité linéaire, régime thermique permanent couplé. Les valeurs de résistance sont comparées à une contrainte admissible **indicative** de 133 MPa (316L, à confirmer dans le code visé).

## 1. Cas de charge

| Cas | Contenu |
|---|---|
| C1 | Pressions seules : tubes 1,0 MPa, calandre 0,6 MPa, température uniforme 20 °C |
| C2 | Thermique seule : fluide tubes 120 °C (h = 1500), fluide calandre 40 °C (h = 800), initial 20 °C |
| C3 | C1 + C2 |

Conditions limites : symétrie en z = 0, patte fixe (X, Y), patte coulissante (Y). Matériau : E = 193 GPa, ν = 0,3, α = 16e-6 /K, λ = 15 W/m/K.

## 2. Maillages

| Maillage | Tailles max / min (mm) | Nœuds | Équations (couplé) |
|---|---|---|---|
| M1 | 20 / 8 | 98 014 | ≈ 390 000 |
| M2 | 12 / 4 | 222 956 | 885 448 |
| M3 | 8 / 2 | 267 828 | 1 063 410 |

Les charges de pression et de film sont appliquées par `charges_ccx.py` (voir §6) parce que le fichier écrit par FreeCAD ne charge pas les faces courbes avec les éléments du second ordre linéaire.

## 3. Équilibre axial d'une section (x = 200 et x = 370)

Force attendue : 12,4 kN (C1, C3) et 0 (C2). Intégration de σxx sur la surface de coupe (`section_force.py`).

| Cas | M1 | M2 | M3 |
|---|---|---|---|
| C1 | 11,9 / 12,0 kN | — | 12,4 / 12,4 kN |
| C2 | 5,4 / −2,4 kN | — | 0,1 / 1,3 kN |
| C3 | 17,2 / 9,6 kN | 12,4 / 13,7 kN | 12,5 / 13,7 kN |

## 4. Convergence en maillage, cas C3

| Grandeur | M1 | M2 | M3 |
|---|---|---|---|
| Déplacement max (mm) | 0,499 | 0,505 | 0,507 |
| T moyenne des tubes (°C) | 86,6 | 88,2 | 88,2 |
| σxx moyenne, calandre (MPa) | 46,7 | 45,6 | 45,5 |
| Fond (centre) Pm+Pb (MPa) | 38,8 | 40,6 | 41,2 |
| Calandre x = 200 Pm / Pm+Pb (MPa) | 43,6 / 44,9 | 42,6 / 43,3 | 42,5 / 43,2 |
| Ligament de plaque Pm / Pm+Pb (MPa) | 36,7 / 90,7 | 28,4 / 71,7 | 27,8 / 71,2 |
| Virole de boîte x = −80 Pm / Pm+Pb (MPa) | 15,4 / 34,1 | 18,0 / 44,0 | 17,5 / 41,8 |

Contrainte moyenne des tubes : la valeur lue sur le maillage dépend de la position de la coupe (−51,8 à −61 MPa), car la section des tubes est facettisée (89 à 96 % de la section exacte sur M2 et M3, identique entre les deux). La valeur retenue vient de l'équilibre avec l'aire exacte : **≈ −54 MPa** (C3), −55 MPa (C2).

Maxima nodaux de von Mises (MPa), M1 / M2 / M3 : tubulure de calandre 139,7 / 143,9 / 148,9 ; pattes 104,1 / 128,6 / 144,1 ; plaques 71,5 / 83,5 / 91,6 ; boîtes 139,0 / 148,1 / 148,1. Ces pics sont sur des coins vifs sans congé (singularités) : ils augmentent avec le maillage et ne servent pas à juger la résistance.

## 5. Séparation primaire / secondaire sur M3 (linéarisation, MPa, VM)

| Section | C1 (pression) Pm / Pm+Pb | C2 (thermique) Pm / Pm+Pb | C3 Pm / Pm+Pb |
|---|---|---|---|
| Centre du fond | 2,8 / 41,1 | 0,1 / 0,2 | 2,7 / 41,2 |
| Calandre x = 200 | 11,0 / 14,1 | 41,2 / 41,4 | 42,5 / 43,2 |
| Ligament de plaque | 1,6 / 4,6 | 29,3 / 75,8 | 27,8 / 71,2 |
| Virole de boîte x = −80 | 17,0 / 41,2 | 0,8 / 1,0 | 17,5 / 41,8 |

Contrôles à la main : contrainte circonférentielle de la calandre 0,6 × 79,65 / 4,5 ≈ 10,6 MPa (FEM : 11,0) ; de la virole de boîte 17,7 MPa (FEM : 17,0 à 17,5) ; fond plat 12 mm, centre entre 21,5 MPa (encastré) et 54,6 MPa (appuyé) (FEM : 41,2). Contraintes axiales moyennes avec plaques rigides : +62 (calandre) et −83 MPa (tubes) ; le FEM donne +45,5 et −54 MPa, car les plaques fléchissent.

## 6. Limites 

- Sections évaluées : fond, calandre, ligament de plaque, virole de boîte. **Non évaluées** : ligaments de tubulure (pics nodaux de 136 à 149 MPa à leur jonction), jonction tube/plaque, pattes.
- Pas de congés ni de soudures, pas de chicanes, brides sans boulons ni joint, matériau élastique linéaire à propriétés constantes, coefficients d'échange supposés. Pas de fatigue.
- Second Order Linear remplace les surfaces courbes par des cordes : les tubes restent sous-estimés en section (voir §4).
- Convergence : sections de plaque, calandre, fond et virole stables à quelques % entre M2 et M3. Le maillage des tubes n'a pas changé entre M2 et M3.
- Limite de SPOOLES : le couplé plante vers 1,1 à 1,2 M d'équations.

## 7. Ordre de grandeur 

Avec S = 133 MPa : membrane primaire maximale 17,5 MPa (0,13 S) ; membrane + flexion primaire maximale 41,2 MPa (0,31 S) ; membrane + flexion totale (primaire + thermique) maximale 71,2 MPa sur le ligament de plaque (0,54 S, soit un facteur 1,9). Ces valeurs ne couvrent pas les zones non évaluées.

## 8. Reproduire

1. Maillage et conditions limites dans FreeCAD ; `pressions.py`, `thermique.py`.
2. Écrire le .inp, puis `python3 charges_ccx.py FEMMeshGmsh001.inp <cas>.inp --pt 1.0 --pc 0.6 [--tt 20 --tc 20 | --pt 0 --pc 0]` et `ccx -i <cas>`.
3. Importer le .frd, renommer l'objet de résultats `M<n>_C<i>`, puis `cas_resume2.py`, `section_force.py`, `linearisation.py`.
