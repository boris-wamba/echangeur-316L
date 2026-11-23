# Exporte les pages TechDraw en PDF (un fichier par page) dans projet_echangeur/plans/.
# A lancer dans la console Python :
#   exec(open('/CHEMIN/VERS/projet_echangeur/export_plans.py').read())
import os
import FreeCAD as App
import TechDrawGui

DOSSIER = "/CHEMIN/VERS/projet_echangeur/plans"
os.makedirs(DOSSIER, exist_ok=True)
doc = App.ActiveDocument
for o in doc.Objects:
    if o.TypeId == "TechDraw::DrawPage":
        f = os.path.join(DOSSIER, o.Name + ".pdf")
        try:
            TechDrawGui.exportPageAsPdf(o, f)
            print("ecrit :", f)
        except Exception as e:
            print("ECHEC :", o.Name, "->", e)
