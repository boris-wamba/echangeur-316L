# Analyse des résultats FEM 

Statut : étude **préliminaire**. Valeurs numériques extraites de `RESULTATS_FEM.md` maillage M3 sauf mention ; comparaisons analytiques calculées par `fem/verification_analytique.py`.

## 1. Thermique (cas C2)

| Grandeur | Analytique | FEM |
|---|---|---|
| Température moyenne des tubes | 88,2 °C | 88,2 °C (M2 et M3) |

**Lecture.** Les trois résistances en série (film tubes 1500 W/m²K, paroi, film calandre 800 W/m²K) donnent un flux de ≈ 2,2 kW par mètre de tube. La paroi (λ = 15) ne chute que de ≈ 4,5 K : le tube est quasi isotherme, sa température est fixée par les deux films, pas par l'acier. La paroi est plus proche du fluide chaud (côté de plus grand h), d'où 88 °C et non 80 °C.

**Limite de cette concordance.** Elle valide l'implémentation des conditions de film dans CalculiX, pas le réalisme des coefficients h, qui sont **supposés** (pas de corrélation de Nusselt, pas d'encrassement). M1 (86,6 °C) est légèrement sous-convergé.

## 2. Pression (cas C1)

| Section | Analytique | FEM |
|---|---|---|
| Calandre, σθ | 10,6 MPa | Pm = 11,0 MPa |
| Virole de boîte, σθ | 17,7 MPa | Pm = 17,0 à 17,5 MPa |
| Fond plat, centre (Pm+Pb) | 21,5 (encastré) à 54,5 (appuyé) | 41,2 MPa |
| Ligament de plaque (Pm+Pb) | 3,0 (plaque pleine) ; ≈ 12 (÷ η = 0,252) | 4,6 MPa |

**Lecture.**
- Calandre et virole : accord à quelques pourcents avec P·R/t. La formule de paroi mince s'applique (R/t ≈ 18).
- Fond plat : la valeur FEM tombe **entre** l'encastrement et l'appui simple, ce qui est le résultat physique attendu pour un fond soudé (bord partiellement retenu). Forte part de flexion (Pm = 2,7 contre Pm+Pb = 41 MPa) : un fond plat travaille en flexion, ce qui est coûteux en matière, d'où l'intérêt d'un fond bombé en conception réelle.
- Ligament de plaque : sous la seule pression différentielle (0,4 MPa) la plaque de 25 mm est très peu sollicitée. La valeur FEM (4,6 MPa) est entre la plaque pleine et la borne ligament, probablement parce que les tubes raidissent la plaque (hypothèse non testée) : la formule « plaque pleine ÷ η » est donc un majorant, pas une prédiction.

## 3. Équilibre axial loi de la statique

La résultante de σxx sur une section de calandre + tubes doit valoir ΣP·A = 1,0 × 3 702 + 0,6 × 14 515 mm² = **12,4 kN** (C1, C3) et **0** (C2).

| Cas | M1 | M3 |
|---|---|---|
| C1 | 11,9 / 12,0 kN | 12,4 / 12,4 kN |
| C2 | 5,4 / −2,4 kN | 0,1 / 1,3 kN |
| C3 | 17,2 / 9,6 kN | 12,5 / 13,7 kN |

**Lecture.** L'équilibre converge avec le maillage : M1 est insuffisant (erreur jusqu'à 5 kN en C2), M3 est correct (12,4 kN en pression, ≈ 0 en thermique). Le résidu de 1,3 kN en C2 et 13,7 contre 12,4 kN en C3 (≈ 10 %) vient de la facettisation des tubes (89 à 96 % de la section exacte) et de la position de la coupe ; il n'est pas à ignorer. Il est la raison pour laquelle les contraintes moyennes des tubes sont déduites de l'équilibre (aire exacte) et non lues directement.

## 4. Dilatation thermique différentielle (cœur de l'étude)

| | Plaques rigides (analytique) | FEM réel (C2/C3) |
|---|---|---|
| Tubes | ≈ −85 MPa | ≈ −54 à −55 MPa |
| Calandre | ≈ +63 MPa | +41 à +45,5 MPa |
| Force axiale thermique | ≈ 146 kN | ≈ 94 kN (0,64 de la borne) |

(RESULTATS_FEM.md cite −83 / +62 MPa : même ordre de grandeur, légère différence d'hypothèse sur les aires et ΔT.)

**Lecture.**
- **Signe** : tubes comprimés, calandre tendue. C'est conforme à la physique : le fluide chaud est dans les tubes.
- **Équilibre interne** : 54 MPa × 1 714 mm² ≈ 94 kN dans les tubes et 41 MPa × 2 316 mm² ≈ 95 kN dans la calandre. Les forces s'équilibrent, comme l'impose la statique de la liaison par les plaques.
- **Valeur inférieure à la borne** : les plaques de 25 mm fléchissent et absorbent ≈ 36 % de la dilatation empêchée. C'est le mécanisme qui explique pourquoi la contrainte réelle est plus faible que celle à plaques rigides, et pourquoi la flexion de plaque domine les contraintes totales du ligament (Pm+Pb = 75,8 MPa en C2 contre Pm = 29,3).
- **Flambement** : la compression de 55 MPa est loin de la contrainte critique d'Euler d'un tube de 550 mm sans appui (≈ 240 MPa, appui-appui, cas le plus défavorable). Rapport ≈ 4,4 sans compter les chicanes.
- **Déplacement maximal** 0,507 mm : cohérent avec les dilatations libres de 0,24 mm (élément à 40 °C) à 0,82 mm (à 88 °C) sur 750 mm. Cette comparaison est un ordre de grandeur : le déplacement exact dépend de la position de la patte fixe.

## 5. Superposition C1 + C2 = C3

En élasticité linéaire, la superposition s'applique aux **déplacements et aux tenseurs de contraintes**, pas aux valeurs de von Mises qui est un scalaire non linéaire. Les sommes brutes de von Mises surestiment donc C3 : ligament Pm+Pb 4,6 + 75,8 = 80,4 contre 71,2 MPa (C3) ; calandre Pm 11,0 + 41,2 = 52,2 contre 42,5 MPa ; virole 17,0 + 0,8 = 17,8 contre 17,5 MPa. Le sens des écarts est celui attendu (inégalité triangulaire : C3 ≤ C1 + C2 en von Mises). **La superposition au niveau des tenseurs n'a pas été vérifiée ici** ; elle peut l'être en additionnant les champs σ de C1 et C2 et en comparant à C3.

## 6. Convergence en maillage et singularités

| Grandeur (C3) | M1 | M2 | M3 | Verdict |
|---|---|---|---|---|
| Déplacement max (mm) | 0,499 | 0,505 | 0,507 | convergé (< 2 %) |
| σxx calandre (MPa) | 46,7 | 45,6 | 45,5 | convergé |
| Fond Pm+Pb (MPa) | 38,8 | 40,6 | 41,2 | convergé à quelques % |
| Ligament Pm+Pb (MPa) | 90,7 | 71,7 | 71,2 | M1 insuffisant, M2→M3 stable |
| Maximum nodal VM tubulure (MPa) | 139,7 | 143,9 | 148,9 | **ne converge pas** |
| Maximum nodal VM pattes (MPa) | 104,1 | 128,6 | 144,1 | **ne converge pas** |

**Lecture.** Deux familles de résultats cohabitent :
- les grandeurs **intégrées ou linéarisées** (déplacement, forces, Pm, Pb) convergent : on peut s'y fier ;
- les maxima nodaux aux coins vifs **croissent avec le raffinement** : ce sont des singularités géométriques (coin sans congé, élasticité linéaire = contrainte théoriquement infinie). Ils ne mesurent pas la résistance. On ne les compare donc pas à S.

## 7. Marge (indicative) et limites

Avec S = 133 MPa **indicatif** :

| Contrainte | Valeur max | Limite (citée de mémoire) | Rapport |
|---|---|---|---|
| Pm | 17,5 MPa | S = 133 | 0,13 |
| Pm+Pb primaire | 41,2 MPa | 1,5 S = 200 | 0,21 |
| Pm+Pb+Q (ligament) | 71,2 MPa | 3 S = 399 | 0,18 |

RESULTATS_FEM.md exprime les mêmes valeurs par rapport à S seul (0,31 S et 0,54 S), ce qui est plus conservateur. La classification de la contrainte thermique du ligament comme secondaire est une hypothèse de travail à confirmer dans le code visé.

**Ce qui n'est PAS évalué (à ne pas présenter comme validé)** :
- ligaments de tubulure (pics nodaux de 136 à 149 MPa à la jonction) ;
- jonction tube/plaque ;
- pattes ;
- fatigue ; congés et soudures ; brides sans boulons ni joint ; chicanes ; propriétés constantes en température ;
- coefficients d'échange supposés ;
- limite du solveur SPOOLES (≈ 1,1 à 1,2 M d'équations).

## 8. Conclusion

Le modèle reproduit les lois attendues : parois minces (±5 %), plaque circulaire avec une valeur entre les bornes, statique (12,4 kN), thermique en série (88,2 °C) et dilatation différentielle (signes et bilan de forces corrects, valeur inférieure à la borne rigide). Les sections de référence convergent entre M2 et M3. Les marges sont larges sur les sections évaluées, mais **trois zones critiques restent à traiter** : tubulures, jonction tube/plaque, pattes.

**perspectives** : linéarisation aux tubulures et à la jonction tube/plaque, étude paramétrique de l'épaisseur de plaque 15 à 35 mm, congés aux jonctions.
