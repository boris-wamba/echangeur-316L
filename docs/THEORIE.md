# Objectifs de l'étude, concepts physiques et résultats théoriques attendus

## 1. Objectifs

1. Concevoir en CAO FreeCAD 1.1.3 un échangeur à tubes et calandre **à plaques tubulaires fixes** en inox 316L.
2. Vérifier par éléments finis CalculiX 2.23 le comportement mécanique sous **pression** et sous **gradient thermique**, en séparant les deux effets (cas C1, C2, C3).
3. Contrôler la crédibilité du calcul : **équilibre des efforts**, **convergence en maillage**, **comparaison à des formules analytiques**.
4. Produire les livrables d'un dossier d'ingénieur : plans normalisés (ISO 5457 / ISO 7200 / ISO 129-1), vidéos, documentation.


## 2. Concepts physiques

### 2.1 Enveloppe mince sous pression
Pour un cylindre de rayon intérieur R et d'épaisseur t soumis à une pression P (R/t grand) :

- contrainte circonférentielle : σθ = P·R / t
- contrainte axiale (fond fermé) : σx = P·R / (2t)

C'est la **contrainte membranaire** : uniforme dans l'épaisseur, de nature **primaire** elle équilibre la charge, elle ne se relaxe pas par déformation.

### 2.2 Plaque circulaire sous pression, fond plat, plaque tubulaire
Une plaque de rayon R, d'épaisseur t, chargée par une pression P fléchit. Les contraintes de flexion sont proportionnelles à P·(R/t)² :

| Appui du bord | σ au centre | σ au bord |
|---|---|---|
| Encastré | 3(1+ν)/8 · P(R/t)² | 3/4 · P(R/t)² |
| Simplement appuyé | 3(3+ν)/8 · P(R/t)² | 0 |

La réalité d'un fond soudé à une virole est **entre** les deux (bord partiellement encastré). C'est une contrainte de **flexion**, linéaire dans l'épaisseur.

La plaque tubulaire est percée de trous : le **rendement de ligament** η = (p − d)/p (pas p, trou d) mesure la section résistante restante. La contrainte locale dans les ligaments est supérieure à celle d'une plaque pleine, en gros σ/η.

### 2.3 Transfert thermique
- **Convection** (loi de Newton) à la paroi : q = h·(T_paroi − T_fluide).
- **Conduction permanente** (Fourier) à travers la paroi du tube : q = −λ·∇T. Pour un tube, la résistance de paroi par mètre est ln(Re/Ri)/(2πλ).
- Les trois résistances (film interne, paroi, film externe) sont **en série** : la température de paroi se place près du fluide qui a le plus grand h (résistance la plus faible).

### 2.4 Dilatation thermique différentielle (cœur du sujet)
Dans un échangeur à plaques fixes, les tubes et la calandre sont **liés** par les deux plaques. Les tubes chauds (≈ 88 °C) voudraient s'allonger plus que la calandre (≈ 40 °C) : ils sont donc **comprimés**, la calandre est **tendue**.

- Dilatation libre : ΔL = α·ΔT·L
- Si les plaques étaient rigides, la compatibilité des déformations et l'équilibre des forces (F_tubes = F_calandre) donnent :

  F = α·ΔT·E / (1/A_t + 1/A_c)  ;  σ_tubes = −F/A_t  ;  σ_calandre = +F/A_c

- Les plaques réelles **fléchissent** et absorbent une partie de l'écart : les contraintes réelles sont **inférieures** à ces bornes.

### 2.5 Superposition (élasticité linéaire)
En comportement élastique linéaire, les effets s'ajoutent : **C1 + C2 = C3**. Les contraintes de pression et thermiques peuvent être calculées séparément puis sommées. Cela sert de test de cohérence du calcul.

### 2.6 Classification des contraintes (démarche code de calcul)
Les contraintes ne sont pas toutes équivalentes en danger :

- **Pm** : membrane primaire (moyenne dans l'épaisseur)
- **Pb** : flexion primaire
- **Q** : secondaire (dilatation thermique gênée, discontinuités), auto-limitée

On linéarise les contraintes (von Mises) le long d'un segment à travers l'épaisseur pour extraire Pm et Pb. Les critères usuels de type ASME/EN sont Pm ≤ S, Pm+Pb ≤ 1,5·S, Pm+Pb+Q ≤ 3·S. **Ils sont cités de mémoire dans ce dossier et à vérifier dans le code visé.** S = 133 MPa est une valeur **indicative** pour le 316L.

### 2.7 Notions de fiabilité numérique
- **Équilibre** : l'intégrale de σxx sur une section doit égaler la résultante des pressions (12,4 kN ici).
- **Convergence en maillage** : une grandeur physique stable se stabilise quand on raffine ; un maximum local à un coin vif **augmente sans limite** (singularité), il ne mesure pas la résistance.
- **Saint-Venant** : loin des discontinuités, la répartition des contraintes ne dépend que de la résultante : on évalue donc les sections loin des coins.

## 3. Résultats théoriques attendus avant calcul FEM

| Grandeur | Attendu | Origine |
|---|---|---|
| Température moyenne des tubes | ≈ 88 °C | résistances en série, §2.3 |
| Contrainte circonférentielle calandre (0,6 MPa) | ≈ 10,6 MPa | P·R/t |
| Contrainte circonférentielle virole de boîte (1,0 MPa) | ≈ 17,7 MPa | P·R/t |
| Fond plat 12 mm, centre | entre 21,5 et 54,5 MPa | plaque encastrée / appuyée |
| Force axiale d'une section | 12,4 kN en C1 et C3, 0 en C2 | équilibre des pressions |
| Tubes / calandre en thermique | compression / traction, **inférieures** aux bornes plaques rigides ≈ −85 / +63 MPa | §2.4 |
| Flambement des tubes comprimés | marge large (Euler ≈ 240 MPa pour L = 550 mm) | Euler appui-appui |
| Ordre de grandeur de la déformée | de l'ordre de 0,2 à 0,8 mm | dilatation libre à 40 et 88 °C sur 750 mm |
| Maxima à coins vifs | croissent avec le raffinement | singularités |

Ces valeurs sont recalculables avec `fem/verification_analytique.py`.
