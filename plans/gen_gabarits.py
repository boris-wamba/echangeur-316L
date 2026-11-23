# Genere deux gabarits TechDraw SVG A3 et A4 paysage inspires de l'ISO 5457 (cadre, reperes)
# et de l'ISO 7200 (champs du cartouche).
#
# ISO 5457 (verifie sur le texte de la norme 1999) :
#   - bordure 20 mm a gauche cadre compris, 10 mm ailleurs ; cadre en trait continu 0,7 mm
#   - 4 reperes de centrage, traits 0,7 mm, du bord de la bande de reperes jusqu'a 10 mm dans le cadre
#   - reperes de zone : champs de 50 mm a partir des axes de symetrie, chiffres 3,5 mm,
#     lettres sans I ni O, traits 0,35 mm ; A3 : 8 x 6 champs ; A4 : 6 x 4 champs
#   - reperes de coupe : deux rectangles superposes de 10 x 5 mm aux 4 coins
#   - designation du format en bordure basse, a droite
# ISO 7200 : champs obligatoires = proprietaire legal, numero d'identification, date d'emission,
#   numero de feuille, titre, personne d'approbation, createur, type de document.
#   Echelle, symbole de projection, tolerances generales : hors cartouche (zone annexe au-dessus).
# Ecarts assumes : A4 en paysage (la norme veut l'A4 en portrait) ; largeur du cartouche 180 mm
#   (non verifiee dans la norme) ; bande de reperes de 5 mm (valeur relevee hors norme) ;
#   proportions du symbole de projection approximatives.
import os

NS = ('xmlns="http://www.w3.org/2000/svg" '
      'xmlns:freecad="http://www.freecadweb.org/wiki/index.php?title=Svg_Namespace"')
LETTRES = "ABCDEFGHJKLMNPQRSTUVWXYZ"        # sans I ni O
BANDE = 5.0                                  # largeur de la bande de reperes de zone


def bornes(centre, a, b, pas=50.0):
    """Limites des champs : multiples de 50 mm a partir de l'axe de symetrie, dans ]a, b[."""
    k = int((a - centre) // pas) - 1
    out = []
    while centre + k * pas < b:
        v = centre + k * pas
        if a + 1e-6 < v < b - 1e-6:
            out.append(v)
        k += 1
    return [a] + out + [b]


def gabarit(nom, W, H, champs_attendus):
    x0, y0, x1, y1 = 20.0, 10.0, W - 10.0, H - 10.0      # cadre
    cw, ch = 180.0, 36.0                                   # cartouche
    cx, cy = x1 - cw, y1 - ch
    ah = 18.0                                              # zone annexe (au-dessus du cartouche)
    ay = cy - ah
    a3 = (nom == "A3")
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg %s width="%gmm" height="%gmm" viewBox="0 0 %g %g">' % (NS, W, H, W, H),
         '<rect x="0" y="0" width="%g" height="%g" fill="none" stroke="none"/>' % (W, H)]

    def ligne(xa, ya, xb, yb, w=0.35, extra=""):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="black" stroke-width="%g"%s/>' % (xa, ya, xb, yb, w, extra))

    def rect(x, y, w, h, ep=0.7):
        o.append('<rect x="%g" y="%g" width="%g" height="%g" fill="none" stroke="black" stroke-width="%g"/>' % (x, y, w, h, ep))

    def texte(x, y, t, taille=3.5, ancre="start", couleur="black"):
        o.append('<text x="%g" y="%g" font-family="sans-serif" font-size="%g" text-anchor="%s" fill="%s">%s</text>'
                 % (x, y, taille, ancre, couleur, t))

    def etiquette(x, y, t):
        texte(x, y, t, 2.2, "start", "#555555")

    def champ(x, y, nom_champ, valeur, taille=3.5):
        o.append('<text x="%g" y="%g" font-family="sans-serif" font-size="%g" fill="black" freecad:editable="%s"><tspan>%s</tspan></text>'
                 % (x, y, taille, nom_champ, valeur))

    # --- cadre (0,7 mm) ---
    rect(x0, y0, x1 - x0, y1 - y0)

    # --- reperes de coupe : deux rectangles 10x5 et 5x10 aux 4 coins de la feuille ---
    for (px, py, sx, sy) in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
        for (w, h) in ((10, 5), (5, 10)):
            xx = px if sx > 0 else px - w
            yy = py if sy > 0 else py - h
            rect(xx, yy, w, h, 0.35)

    # --- reperes de zone (bande de 5 mm autour du cadre) ---
    bx = bornes(W / 2.0, x0, x1)       # champs horizontaux -> chiffres
    by = bornes(H / 2.0, y0, y1)       # champs verticaux   -> lettres
    assert (len(bx), len(by)) == ((9, 7) if a3 else (7, 5)), (len(bx), len(by))
    # bande sur les 4 cotes (la norme n'en met que en haut et a droite pour l'A4 ; choix : bordures symetriques)
    ligne(x0 - BANDE, y0 - BANDE, x1 + BANDE, y0 - BANDE)
    ligne(x1 + BANDE, y0 - BANDE, x1 + BANDE, y1 + BANDE)
    if True:
        ligne(x0 - BANDE, y0 - BANDE, x0 - BANDE, y1 + BANDE)
        ligne(x0 - BANDE, y1 + BANDE, x1 + BANDE, y1 + BANDE)
    for i in range(len(bx) - 1):
        xm = (bx[i] + bx[i + 1]) / 2.0
        texte(xm, y0 - 1.4, str(i + 1), 3.5, "middle")
        if True:
            texte(xm, y1 + 4.0, str(i + 1), 3.5, "middle")
    for j in range(len(by) - 1):
        ym = (by[j] + by[j + 1]) / 2.0
        texte(x1 + BANDE / 2.0, ym + 1.2, LETTRES[j], 3.5, "middle")
        if True:
            texte(x0 - BANDE / 2.0, ym + 1.2, LETTRES[j], 3.5, "middle")
    for xv in bx[1:-1]:
        ligne(xv, y0 - BANDE, xv, y0)
        if True:
            ligne(xv, y1, xv, y1 + BANDE)
    for yv in by[1:-1]:
        ligne(x1, yv, x1 + BANDE, yv)
        if True:
            ligne(x0 - BANDE, yv, x0, yv)

    # --- reperes de centrage (0,7 mm) : de la bande jusqu'a 10 mm dans le cadre ---
    xc, yc = W / 2.0, H / 2.0
    ligne(xc, y0 - BANDE, xc, y0 + 10, 0.7)
    ligne(x1 + BANDE, yc, x1 - 10, yc, 0.7)
    ligne(x0 - BANDE, yc, x0 + 10, yc, 0.7)
    # repere bas : s'arrete au cadre s'il tomberait dans le cartouche
    bas_fin = y1 if cx <= xc <= x1 else y1 - 10
    ligne(xc, y1 + BANDE, xc, bas_fin, 0.7)

    # --- designation du format, bordure basse a droite ---
    texte(x1 + BANDE, H - 1.2, nom, 3.5, "end")

    # --- zone annexe (hors cartouche ISO 7200) : projection, echelle, matiere, tolerances ---
    rect(cx, ay, cw, ah)
    for xx in (cx + 45, cx + 90, cx + 135):
        ligne(xx, ay, xx, ay + ah)
    etiquette(cx + 1.5, ay + 3, "Projection (1er dièdre)")
    py_ = ay + ah / 2.0 + 2.5
    px_ = cx + 3
    # cercles concentriques a gauche, tronc de cone a droite (1er dièdre)
    o.append('<circle cx="%g" cy="%g" r="4.5" fill="none" stroke="black" stroke-width="0.5"/>' % (px_ + 6, py_))
    o.append('<circle cx="%g" cy="%g" r="2.25" fill="none" stroke="black" stroke-width="0.5"/>' % (px_ + 6, py_))
    o.append('<polygon points="%g,%g %g,%g %g,%g %g,%g" fill="none" stroke="black" stroke-width="0.5"/>'
             % (px_ + 17, py_ - 4.5, px_ + 31, py_ - 2.25, px_ + 31, py_ + 2.25, px_ + 17, py_ + 4.5))
    ligne(px_ - 1, py_, px_ + 34, py_, 0.25, ' stroke-dasharray="4 1 0.8 1"')
    etiquette(cx + 46.5, ay + 3, "Échelle"); champ(cx + 46.5, ay + 12, "Echelle", "1:1")
    etiquette(cx + 91.5, ay + 3, "Matière"); champ(cx + 91.5, ay + 12, "Matiere", "316L")
    etiquette(cx + 136.5, ay + 3, "Tolérances générales"); champ(cx + 136.5, ay + 12, "Tolerances", "ISO 2768-m")

    # --- cartouche ISO 7200 : 4 rangees de 9 mm ---
    rect(cx, cy, cw, ch)
    r = [cy + 9 * i for i in range(5)]
    for yy in r[1:4]:
        ligne(cx, yy, x1, yy)
    # rangee 1 : proprietaire legal | createur | approbation
    for xx in (cx + 90, cx + 135):
        ligne(xx, r[0], xx, r[1])
    etiquette(cx + 1.5, r[0] + 3, "Propriétaire légal"); champ(cx + 1.5, r[0] + 7.5, "Proprietaire", "Boris Keubou Wamba")
    etiquette(cx + 91.5, r[0] + 3, "Créé par"); champ(cx + 91.5, r[0] + 7.5, "Auteur", "B. Keubou Wamba")
    etiquette(cx + 136.5, r[0] + 3, "Approuvé par"); champ(cx + 136.5, r[0] + 7.5, "Approbateur", "B. Keubou Wamba")
    # rangee 2 : titre
    etiquette(cx + 1.5, r[1] + 3, "Titre"); champ(cx + 1.5, r[1] + 7.5, "Titre", "Titre", 4.5)
    # rangee 3 : titre complementaire | type de document
    ligne(cx + 90, r[2], cx + 90, r[3])
    etiquette(cx + 1.5, r[2] + 3, "Titre complémentaire"); champ(cx + 1.5, r[2] + 7.5, "TitreSup", "Echangeur tubes et calandre")
    etiquette(cx + 91.5, r[2] + 3, "Type de document"); champ(cx + 91.5, r[2] + 7.5, "TypeDoc", "Dessin de piece")
    # rangee 4 : date | indice | statut | feuille | numero d'identification (coin bas droit)
    for xx in (cx + 40, cx + 60, cx + 105, cx + 135):
        ligne(xx, r[3], xx, r[4])
    etiquette(cx + 1.5, r[3] + 3, "Date d'émission"); champ(cx + 1.5, r[3] + 7.5, "Date", "2026-11-22")
    etiquette(cx + 41.5, r[3] + 3, "Indice"); champ(cx + 41.5, r[3] + 7.5, "Revision", "A")
    etiquette(cx + 61.5, r[3] + 3, "Statut"); champ(cx + 61.5, r[3] + 7.5, "Statut", "Preliminaire")
    etiquette(cx + 106.5, r[3] + 3, "Feuille"); champ(cx + 106.5, r[3] + 7.5, "Feuille", "1/1")
    etiquette(cx + 136.5, r[3] + 3, "N° d'identification"); champ(cx + 136.5, r[3] + 7.5, "Numero", "ECH-00")

    o.append('</svg>')
    svg = "\n".join(o)
    manque = [c for c in champs_attendus if 'freecad:editable="%s"' % c not in svg]
    assert not manque, manque
    return svg


CHAMPS = ["Proprietaire", "Auteur", "Approbateur", "Titre", "TitreSup", "TypeDoc", "Date", "Revision",
          "Statut", "Feuille", "Numero", "Echelle", "Matiere", "Tolerances"]

os.makedirs("gabarits", exist_ok=True)
for nom, W, H in (("A3", 420, 297), ("A4", 297, 210)):
    with open("gabarits/Gabarit_%s_paysage_FR.svg" % nom, "w", encoding="utf-8") as f:
        f.write(gabarit(nom, W, H, CHAMPS))
print("ok")
