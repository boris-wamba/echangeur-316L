# Exporte les vraies pieces de l'assemblage en maillages STL (mm), pour video_eclate.py.
# A lancer dans la console Python de FreeCAD, document de l'echangeur ouvert :
#   exec(open('/CHEMIN/VERS/projet_echangeur/export_pieces.py').read())
# N'ecrit que dans le dossier pieces/ ; ne modifie pas le document.
import os
import FreeCAD as App
import MeshPart

DOSSIER = "/CHEMIN/VERS/projet_echangeur/pieces"
# noms internes (colonne "Nom" de pieces_diag.txt) et role
PIECES = {
    "Link004": "boite gauche (L1_P5_boite_gauche)",
    "Link005": "boite droite (L2_P5_boite_droite)",
    "Link002": "plaque tubulaire gauche (L1_P2)",
    "Link003": "plaque tubulaire droite (L2_P2)",
    "Link001": "calandre (L1_P1_Calandre)",
    "Compound": "faisceau de 19 tubes (Tubes)",
    "Link007": "tubulure boite gauche (L2_P6)",
    "Link009": "tubulure boite droite (L4_P6)",
    "Link006": "tubulure calandre x=125 (L1_P6)",
    "Link008": "tubulure calandre x=425 (L3_P6)",
    "Link010": "patte gauche (L1_P7)",
    "Link011": "patte droite (L2_P7)",
    "Link012": "chicane 1 (L1_P4)",
    "Link013": "chicane 2 (L2_P4)",
}
doc = App.ActiveDocument
if doc is None or doc.getObject("Link001") is None:
    doc = None
    for d in App.listDocuments().values():
        if d.getObject("Link001") is not None and d.getObject("Compound") is not None:
            doc = d
if doc is None:
    raise RuntimeError("document de l'echangeur introuvable (objet Link001 absent)")
os.makedirs(DOSSIER, exist_ok=True)
for nom, role in PIECES.items():
    o = doc.getObject(nom)
    if o is None:
        print("MANQUE :", nom, role)
        continue
    s = o.Shape
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False)
    chemin = os.path.join(DOSSIER, nom + ".stl")
    m.write(chemin)
    b = s.BoundBox
    print("%-9s %-38s %7d facettes  vol %8.1f cm3  x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]" % (
        nom, role, m.CountFacets, s.Volume / 1000.0, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
print("ecrit dans", DOSSIER)
