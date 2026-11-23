# Cree les deux charges de pression (cote tubes 1.0 MPa, cote calandre 0.6 MPa)
# sur Echangeur_demi, a partir de regles geometriques validees sur diag_faces.txt.
# A lancer dans la console Python de FreeCAD, document enregistre au prealable.
import FreeCAD as App
import ObjectsFem

P_TUBES = "1.0 MPa"    # 10 bar
P_CALANDRE = "0.6 MPa"  # 6 bar
CREER = True            # False = affichage seul, rien n'est cree

doc = App.ActiveDocument
obj = doc.getObjectsByLabel("Echangeur_demi")[0]
analyse = doc.getObjectsByLabel("Analysis")[0]
sh = obj.Shape
AX = "XYZ"


def comps(v):
    return (v.x, v.y, v.z)


def axis_letter(a):
    c = [abs(x) for x in comps(a)]
    return AX[c.index(max(c))] if max(c) > 0.999 else "?"


def classify(typ, L, R, vers_axe, bb):
    """Retourne 'tubes', 'calandre' ou None (face non mouillee).
    bb = (xmin, xmax, ymin, ymax, zmin, zmax)"""
    xc = 0.5 * (bb[0] + bb[1])
    if typ == "Cylinder" and L == "X":
        if abs(R - 7.875) < 0.05 and vers_axe:      # alesage des tubes
            return "tubes"
        if abs(R - 9.525) < 0.05 and not vers_axe:  # exterieur des tubes
            return "calandre"
        if abs(R - 79.65) < 0.05 and vers_axe:      # virole calandre ou boites
            return "tubes" if (xc < 0 or xc > 550) else "calandre"
    if typ == "Cylinder" and L == "Y":
        if abs(R - 26.25) < 0.05 and vers_axe:      # alesage des tubulures
            return "tubes" if (xc < 0 or xc > 550) else "calandre"
    if typ == "Plane" and L == "X":
        dans = bb[2] >= -80.5 and bb[3] <= 80.5 and bb[5] <= 80.5
        if dans:                                    # faces circulaires R < 80
            return "tubes" if (xc < 12.5 or xc > 537.5) else "calandre"
    return None


sets = {"tubes": [], "calandre": []}
aires = {"tubes": 0.0, "calandre": 0.0}
for i, f in enumerate(sh.Faces, 1):
    s = f.Surface
    typ = type(s).__name__
    p = f.Vertexes[0].Point
    u, w = s.parameter(p)
    n = f.normalAt(u, w)
    L, R, vers_axe = "?", 0.0, False
    if typ == "Plane":
        L = axis_letter(s.Axis)
    elif typ == "Cylinder":
        L = axis_letter(s.Axis)
        R = s.Radius
        if L != "?":
            k = AX.index(L)
            rel = p - s.Center
            r = [comps(rel)[j] if j != k else 0.0 for j in range(3)]
            vers_axe = sum(r[j] * comps(n)[j] for j in range(3)) < 0
    b = f.BoundBox
    cote = classify(typ, L, R, vers_axe, (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
    if cote:
        sets[cote].append("Face%d" % i)
        aires[cote] += f.Area

print("Cote tubes    : %d faces, %.1f cm2" % (len(sets["tubes"]), aires["tubes"] / 100))
print("Cote calandre : %d faces, %.1f cm2" % (len(sets["calandre"]), aires["calandre"] / 100))
print("Attendu       : 19 faces cote tubes, 16 faces cote calandre")

if (len(sets["tubes"]), len(sets["calandre"])) != (19, 16):
    print("ERREUR : nombre de faces inattendu, aucune charge creee. Envoie-moi cette sortie.")
elif CREER:
    for nom, p_val, cle in (("Pression_tubes_10bar", P_TUBES, "tubes"),
                            ("Pression_calandre_6bar", P_CALANDRE, "calandre")):
        c = ObjectsFem.makeConstraintPressure(doc, nom)
        c.References = [(obj, tuple(sets[cle]))]
        c.Pressure = p_val
        analyse.addObject(c)
    doc.recompute()
    print("OK : 2 charges de pression creees dans Analysis.")
