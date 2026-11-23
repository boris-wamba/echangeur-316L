# Diagnostic (lecture seule) : liste les objets FreeCAD qui portent une forme solide, pour
# retrouver les pieces separees du CAD avant fusion. N'ecrit que pieces_diag.txt.
# A lancer dans la console Python de FreeCAD avec le document de l'echangeur ouvert :
#   exec(open('/CHEMIN/VERS/projet_echangeur/pieces_diag.py').read())
import FreeCAD as App

doc = App.ActiveDocument
if doc is None:
    for d in App.listDocuments().values():
        if d.getObjectsByLabel("Echangeur_demi"):
            doc = d
print("Document :", doc.Name if doc else None)


def porte_forme(o):
    try:
        return hasattr(o, "Shape") and not o.Shape.isNull() and len(o.Shape.Solids) > 0
    except Exception:
        return False


lignes = []
for o in doc.Objects:
    if not porte_forme(o):
        continue
    enfants = [c for c in o.OutList if porte_forme(c)]
    parents = [p for p in o.InList if porte_forme(p)]
    s = o.Shape
    bb = s.BoundBox
    vis = None
    try:
        vis = o.Visibility
    except Exception:
        pass
    lignes.append((o.Label, o.Name, o.TypeId, len(parents), len(enfants), len(s.Solids), s.Volume / 1000.0,
                   (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax), vis))

feuilles = [l for l in lignes if l[4] == 0]
tete = "%-28s %-14s %-24s par enf sol  vol_cm3  bbox x[min,max] y[min,max] z[min,max]  vis"
sortie = [tete % ("Label", "Nom", "Type")]
for l in lignes:
    b = l[7]
    sortie.append("%-28s %-14s %-24s %3d %3d %3d %8.1f  x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]  %s%s" % (
        l[0][:28], l[1][:14], l[2][:24], l[3], l[4], l[5], l[6], b[0], b[1], b[2], b[3], b[4], b[5], l[8],
        "  <- feuille" if l[4] == 0 else ""))
sortie.append("")
sortie.append("%d objets avec solide, dont %d feuilles (sans enfant solide)" % (len(lignes), len(feuilles)))
texte = "\n".join(sortie)
print(texte)
chemin = "/CHEMIN/VERS/projet_echangeur/pieces_diag.txt"
open(chemin, "w").write(texte + "\n")
print("ecrit dans", chemin)
