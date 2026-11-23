#!/usr/bin/env python3
# Reecrit les blocs *DLOAD (pressions) et *FILM (convection) d'un fichier CalculiX ecrit par FreeCAD,
# en identifiant les faces mouillees par la position de leurs noeuds de coin (exactement sur la
# geometrie). Contourne le defaut de FreeCAD sur les faces courbes avec "Second Order Linear".
#
# Usage :
#   python3 charges_ccx.py FEMMeshGmsh001.inp sortie.inp --pt 1.0 --pc 0.6
#   (le film est ajoute automatiquement si le fichier contient un pas thermique)
import argparse
import math
import sys

# ---- geometrie (mm) : a adapter si les parametres du projet changent -------------------
R_IN = 79.65            # rayon interieur calandre et boites
R_TUBE = 9.525          # rayon exterieur des tubes
R_BORE = 7.875          # rayon interieur des tubes
R_NOZ = 26.25           # rayon interieur des tubulures DN50
PITCH = 25.4
X_PLANS = ((-88.0, "tubes"), (0.0, "tubes"), (25.0, "calandre"),
           (525.0, "calandre"), (550.0, "tubes"), (638.0, "tubes"))
TUBULURES = ((-54.0, "tubes"), (125.0, "calandre"), (425.0, "calandre"), (604.0, "tubes"))
TOL = 0.02

H = PITCH * math.sqrt(3) / 2
CENTRES = []
for col, zs in ((0.0, (0, 1, -1, 2, -2)), (H, (0.5, -0.5, 1.5, -1.5)), (-H, (0.5, -0.5, 1.5, -1.5)),
                (2 * H, (0, 1, -1)), (-2 * H, (0, 1, -1))):
    for k in zs:
        CENTRES.append((col, k * PITCH))

FACES = ((0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0))    # F1..F4 des tetraedres ccx


def classer(pts):
    xs = [p[0] for p in pts]
    xmin, xmax = min(xs), max(xs)
    if xmax - xmin < 0.01:                              # face plane perpendiculaire a X
        if max(math.hypot(p[1], p[2]) for p in pts) <= R_IN + 0.05:
            xm = sum(xs) / 3.0
            for x0, cote in X_PLANS:
                if abs(xm - x0) < 0.05:
                    return cote
        return None
    rs = [math.hypot(p[1], p[2]) for p in pts]
    if all(abs(r - R_IN) < TOL for r in rs):            # virole calandre ou boites
        if xmin >= 25 - TOL and xmax <= 525 + TOL:
            return "calandre"
        if (xmin >= -88 - TOL and xmax <= TOL) or (xmin >= 550 - TOL and xmax <= 638 + TOL):
            return "tubes"
    if -TOL <= xmin and xmax <= 550 + TOL:
        for cy, cz in CENTRES:
            d = [math.hypot(p[1] - cy, p[2] - cz) for p in pts]
            if all(abs(v - R_BORE) < TOL for v in d):
                return "tubes"
            if xmin >= 25 - TOL and xmax <= 525 + TOL and all(abs(v - R_TUBE) < TOL for v in d):
                return "calandre"
    if all(abs(p[1]) >= 70 for p in pts):               # tubulures (axe Y)
        for x0, cote in TUBULURES:
            if all(abs(math.hypot(p[0] - x0, p[2]) - R_NOZ) < TOL for p in pts):
                return cote
    return None


def aire(a, b, c):
    ax, ay, az = (b[k] - a[k] for k in range(3))
    bx, by, bz = (c[k] - a[k] for k in range(3))
    cx, cy, cz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entree")
    ap.add_argument("sortie")
    ap.add_argument("--pt", type=float, default=1.0, help="pression cote tubes, MPa")
    ap.add_argument("--pc", type=float, default=0.6, help="pression cote calandre, MPa")
    ap.add_argument("--tt", type=float, default=120.0, help="temperature fluide tubes, C")
    ap.add_argument("--ht", type=float, default=1500.0, help="h cote tubes, W/m2/K")
    ap.add_argument("--tc", type=float, default=40.0, help="temperature fluide calandre, C")
    ap.add_argument("--hc", type=float, default=800.0, help="h cote calandre, W/m2/K")
    a = ap.parse_args()

    lignes = open(a.entree).read().split("\n")
    noeuds, elems = {}, {}
    mode, buf = None, ""
    thermique = False
    for ligne in lignes:
        s = ligne.strip()
        if not s or s.startswith("**"):
            continue
        if s.startswith("*"):
            u = s.upper().replace(" ", "")
            buf = ""
            if u.startswith("*NODE") and not any(k in u for k in ("PRINT", "FILE", "OUTPUT")):
                mode = "node"
            elif u.startswith("*ELEMENT,"):
                mode = "elem" if "C3D10" in u else None
            else:
                mode = None
                if u.startswith("*COUPLED") or u.startswith("*HEATTRANSFER"):
                    thermique = True
            continue
        if mode in ("node", "elem"):
            buf += s
            if s.endswith(","):
                continue
            t = [x.strip() for x in buf.split(",") if x.strip()]
            buf = ""
            if mode == "node":
                noeuds[int(t[0])] = (float(t[1]), float(t[2]), float(t[3]))
            else:
                elems[int(t[0])] = [int(x) for x in t[1:11]]

    faces = {}
    for e, nn in elems.items():
        for i, f in enumerate(FACES, 1):
            faces.setdefault(frozenset(nn[k] for k in f), []).append((e, i, [nn[k] for k in f]))
    charge = {"tubes": [], "calandre": []}
    aires = {"tubes": 0.0, "calandre": 0.0}
    nbord = 0
    for cle, lst in faces.items():
        if len(lst) != 1:
            continue
        nbord += 1
        e, i, nds = lst[0]
        pts = [noeuds[n] for n in nds]
        cote = classer(pts)
        if cote:
            charge[cote].append((e, i))
            aires[cote] += aire(*pts)

    # reecriture : on retire les blocs *DLOAD / *FILM, on insere les nouveaux a la place du premier
    sortie, saut, pos = [], False, None
    for ligne in lignes:
        u = ligne.strip().upper()
        if u.startswith("*DLOAD") or u.startswith("*FILM"):
            saut = True
            if pos is None:
                pos = len(sortie)
            continue
        if saut:
            if u.startswith("*") and not u.startswith("**"):
                saut = False
            else:
                continue
        sortie.append(ligne)
    if pos is None:
        sys.exit("Aucun bloc *DLOAD ni *FILM trouve : rien a remplacer.")
    nouveau = []
    for cote, p in (("tubes", a.pt), ("calandre", a.pc)):
        if p != 0.0:
            nouveau.append("*DLOAD")
            nouveau.append("** pression cote %s (%d faces) - charges_ccx.py" % (cote, len(charge[cote])))
            nouveau += ["%d,P%d,%s" % (e, i, repr(p)) for e, i in sorted(charge[cote])]
    if thermique:
        for cote, T, h in (("tubes", a.tt, a.ht), ("calandre", a.tc, a.hc)):
            nouveau.append("*FILM")
            nouveau.append("** convection cote %s (%d faces) - charges_ccx.py" % (cote, len(charge[cote])))
            nouveau += ["%d,F%d,%s,%s" % (e, i, repr(round(T + 273.15, 2)), repr(h / 1000.0))
                        for e, i in sorted(charge[cote])]
    sortie[pos:pos] = nouveau
    open(a.sortie, "w").write("\n".join(sortie))

    print("%d noeuds, %d elements, %d faces de bord" % (len(noeuds), len(elems), nbord))
    print("cote tubes    : %6d faces, aire %7.1f cm2 (geometrie ~3492)" % (len(charge["tubes"]), aires["tubes"] / 100))
    print("cote calandre : %6d faces, aire %7.1f cm2 (geometrie ~4344)" % (len(charge["calandre"]), aires["calandre"] / 100))
    print("pas thermique : %s | pressions tubes/calandre = %s / %s MPa" % ("oui" if thermique else "non", a.pt, a.pc))
    print("ecrit :", a.sortie)


main()
