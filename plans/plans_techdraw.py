# Cree les pages TechDraw (une par piece + ensemble), leurs vues et la nomenclature.
# NON TESTE sur FreeCAD 1.1.3 : chaque etape est protegee, les erreurs sont affichees sans tout arreter.
# Prerequis : echangeur.FCStd ouvert, interface graphique active. A lancer dans la console Python :
#   exec(open('/CHEMIN/VERS/projet_echangeur/plans_techdraw.py').read())
# Ne modifie aucune piece : il ajoute seulement des objets TechDraw et un tableur "Nomenclature".
import fnmatch, glob, os
import FreeCAD as App

doc = App.ActiveDocument
if doc is None or doc.getObject("Link001") is None:
    doc = None
    for d in App.listDocuments().values():
        if d.getObject("Link001") is not None:
            doc = d
if doc is None:
    raise RuntimeError("document de l'echangeur introuvable (objet Link001 absent)")

# ---------- gabarits ----------
# Recherche recursive des gabarits SVG sous les dossiers d'installation de FreeCAD (AppImage compris).
GABARITS_IMPOSES = {"A3": None, "A4": None}     # chemin complet a mettre ici si la recherche echoue
racines = []
for r in (App.getHomePath(), App.getResourceDir()):
    if r and r not in racines:
        racines.append(r)
fichiers = []
for r in racines:
    for dp, dn, fn in os.walk(r):
        if "templ" in dp.lower() or "techdraw" in dp.lower():
            fichiers += [os.path.join(dp, f) for f in fn if f.lower().endswith(".svg")]
fichiers = sorted(set(fichiers))
print("%d gabarits SVG trouves" % len(fichiers))
for f in fichiers:
    print("   ", f)


def gabarit(format_):
    if GABARITS_IMPOSES.get(format_):
        return GABARITS_IMPOSES[format_]
    f_ = format_.lower()
    for test in (lambda n: n.startswith(f_ + "_landscape") and "iso7200" in n,
                 lambda n: n.startswith(f_ + "_landscape"),
                 lambda n: f_ in n and "landscape" in n,
                 lambda n: f_ in n):
        for f in fichiers:
            if test(os.path.basename(f).lower()):
                return f
    return None


# ---------- objets sources (noms internes, colonne "Nom" de pieces_diag.txt) ----------
P = {"P1": "Body001", "P2": "Body003", "P3": "Body", "P4": "Body004", "P5": "Body005", "P6": "Body006",
     "P7": "Body007"}
ENS = ["Link001", "Link002", "Link003", "Link004", "Link005", "Link006", "Link007", "Link008", "Link009",
       "Link010", "Link011", "Link012", "Link013", "Compound"]


def obj(nom):
    o = doc.getObject(nom)
    if o is None:
        raise RuntimeError("objet %s introuvable" % nom)
    return o


def page(nom, format_, titre):
    p = doc.addObject("TechDraw::DrawPage", nom)
    t = doc.addObject("TechDraw::DrawSVGTemplate", nom + "_Gabarit")
    f = gabarit(format_)
    if f is None:
        raise RuntimeError("aucun gabarit %s paysage trouve" % format_)
    t.Template = f
    p.Template = t
    try:                                        # projection europeenne (premier dihedre)
        valeurs = p.getEnumerationsOfProperty("ProjectionType")
        choix = [v for v in valeurs if "first" in v.lower()]
        if choix:
            p.ProjectionType = choix[0]
        else:
            print("  projection : valeurs disponibles", valeurs)
    except Exception as e:
        print("  (projection europeenne non reglee :", e, ")")
    p.Label = titre
    return p


def vue(p, nom, sources, direction, x, y, echelle, xdir=None):
    v = doc.addObject("TechDraw::DrawViewPart", nom)
    p.addView(v)
    v.Source = sources
    v.Direction = App.Vector(*direction)
    if xdir is not None:
        v.XDirection = App.Vector(*xdir)
    v.ScaleType = "Custom"
    v.Scale = echelle
    v.X, v.Y = x, y
    return v


def coupe(p, nom, base, normale, origine, x, y):
    s = doc.addObject("TechDraw::DrawViewSection", nom)
    p.addView(s)
    s.BaseView = base
    s.Source = base.Source
    s.ScaleType = "Custom"
    s.Scale = base.Scale
    s.SectionNormal = App.Vector(*normale)
    s.SectionOrigin = App.Vector(*origine)
    s.X, s.Y = x, y
    return s


def essai(nom, f):
    try:
        f()
        print("OK     :", nom)
    except Exception as e:
        print("ECHEC  : %s -> %s" % (nom, e))


# ---------- une page par piece ----------
FACE_X = (1, 0, 0), (0, 0, -1)          # vue de bout depuis +X, Y vertical
def p1():
    pg = page("Plan_P1", "A3", "P1 Calandre"); s = [obj(P["P1"])]
    vue(pg, "P1_face", s, (0, -1, 0), 235, 205, 0.4)
    vue(pg, "P1_dessus", s, (0, 0, 1), 235, 130, 0.4)
    vue(pg, "P1_bout", s, FACE_X[0], 95, 205, 0.4, FACE_X[1])

def p2():
    pg = page("Plan_P2", "A3", "P2 Plaque tubulaire"); s = [obj(P["P2"])]
    vue(pg, "P2_face", s, FACE_X[0], 130, 190, 0.5, FACE_X[1])
    vue(pg, "P2_cote", s, (0, 0, 1), 260, 190, 0.5)

def p3():
    pg = page("Plan_P3", "A4", "P3 Tube"); s = [obj(P["P3"])]
    vue(pg, "P3_face", s, (0, -1, 0), 150, 150, 0.4)
    vue(pg, "P3_bout", s, FACE_X[0], 80, 80, 5.0, FACE_X[1])

def p4():
    pg = page("Plan_P4", "A4", "P4 Chicane"); s = [obj(P["P4"])]
    vue(pg, "P4_face", s, FACE_X[0], 110, 120, 1.0, FACE_X[1])
    vue(pg, "P4_cote", s, (0, 0, 1), 230, 120, 1.0)

def p5():
    pg = page("Plan_P5", "A3", "P5 Boite de distribution"); s = [obj(P["P5"])]
    base = vue(pg, "P5_face", s, (0, -1, 0), 235, 85, 0.5)
    vue(pg, "P5_bout", s, FACE_X[0], 110, 190, 0.5, FACE_X[1])
    essai("P5 coupe A-A (plan z=0)", lambda: coupe(pg, "P5_coupeAA", base, (0, 0, 1), (-50, 0, 0), 235, 190))

def p6():
    pg = page("Plan_P6", "A4", "P6 Tubulure DN50"); s = [obj(P["P6"])]
    vue(pg, "P6_dessus", s, (0, 0, 1), 100, 120, 1.0)
    vue(pg, "P6_face", s, (0, -1, 0), 200, 120, 1.0)

def p7():
    pg = page("Plan_P7", "A4", "P7 Patte d'appui"); s = [obj(P["P7"])]
    vue(pg, "P7_face", s, (0, -1, 0), 110, 140, 1.0)
    vue(pg, "P7_dessus", s, (0, 0, 1), 110, 70, 1.0)
    vue(pg, "P7_cote", s, FACE_X[0], 210, 140, 1.0, FACE_X[1])

def ensemble():
    pg = page("Plan_Ensemble", "A3", "Plan d'ensemble"); s = [obj(n) for n in ENS]
    base = vue(pg, "Ens_face", s, (0, -1, 0), 225, 75, 0.4)             # 1:2,5
    vue(pg, "Ens_bout", s, FACE_X[0], 35, 178, 0.2, FACE_X[1])          # 1:5
    essai("Ensemble coupe A-A (plan z=0)", lambda: coupe(pg, "Ens_coupeAA", base, (0, 0, 1), (275, 0, 0), 225, 178))
    # nomenclature (tableur + vue de tableur)
    sh = doc.addObject("Spreadsheet::Sheet", "Nomenclature")
    rho = 7.95e-6   # kg/mm3 (316L, 7950 kg/m3)
    lignes = [("Rep", "Designation", "Qte", "Matiere", "Masse unit. (kg)", "Plan")]
    for rep, (cle, nom, q) in enumerate([("P1", "Calandre", 1), ("P2", "Plaque tubulaire", 2), ("P3", "Tube", 19),
                                         ("P4", "Chicane", 2), ("P5", "Boite de distribution", 2),
                                         ("P6", "Tubulure DN50", 4), ("P7", "Patte d'appui", 2)], 1):
        m = obj(P[cle]).Shape.Volume * rho
        lignes.append((str(rep), "%s %s" % (cle, nom), str(q), "316L", "%.2f" % m, "Plan_" + cle))
    for i, l in enumerate(lignes, 1):
        for j, v in enumerate(l):
            sh.set("%s%d" % ("ABCDEF"[j], i), "'" + v)
    doc.recompute()
    v = doc.addObject("TechDraw::DrawViewSpreadsheet", "Ens_nomenclature")
    pg.addView(v)
    v.Source = sh
    v.CellStart, v.CellEnd = "A1", "F%d" % len(lignes)
    v.X, v.Y = 330, 268


for nom, f in (("P1", p1), ("P2", p2), ("P3", p3), ("P4", p4), ("P5", p5), ("P6", p6), ("P7", p7),
               ("Ensemble", ensemble)):
    essai("page " + nom, f)
doc.recompute()
print("termine : ouvre chaque page (double-clic dans l'arbre) et verifie les vues avant de coter.")
