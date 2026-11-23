# Remplace le gabarit de chaque page TechDraw par les gabarits francais inspires ISO 5457 / ISO 7200
# (Gabarit_A3_paysage_FR.svg / Gabarit_A4_paysage_FR.svg) et remplit le cartouche.
# NON TESTE sur FreeCAD 1.1.3. Les vues ne sont pas modifiees.
# Place les deux .svg dans projet_echangeur/gabarits/ puis, dans la console Python de FreeCAD :
#   exec(open('/CHEMIN/VERS/projet_echangeur/appliquer_gabarits.py').read())
import os
import datetime
import FreeCAD as App

DOSSIER = "/CHEMIN/VERS/projet_echangeur/gabarits"
SVG = {"A3": os.path.join(DOSSIER, "Gabarit_A3_paysage_FR.svg"),
       "A4": os.path.join(DOSSIER, "Gabarit_A4_paysage_FR.svg")}
# (debut du label de la page) -> (numero de plan, echelle affichee)
INFOS = [("P1", "P1", "1:2,5"), ("P2", "P2", "1:2"), ("P3", "P3", "1:2,5 ; bout 5:1"), ("P4", "P4", "1:1"),
         ("P5", "P5", "1:2"), ("P6", "P6", "1:1"), ("P7", "P7", "1:1"), ("Plan d'ensemble", "ENS", "1:2,5")]
for f in SVG.values():
    if not os.path.exists(f):
        raise RuntimeError("gabarit introuvable : " + f)

doc = App.ActiveDocument
pages = [o for o in doc.Objects if o.TypeId == "TechDraw::DrawPage"]
total = len(pages)
for k, pg in enumerate(sorted(pages, key=lambda o: o.Label), 1):
    try:
        tpl = pg.Template
        fmt = "A3" if float(tpl.Width.Value if hasattr(tpl.Width, "Value") else tpl.Width) > 350 else "A4"
        tpl.Template = SVG[fmt]
        info = [i for i in INFOS if pg.Label.startswith(i[0])]
        champs = {"Titre": pg.Label, "Date": datetime.date.today().isoformat(), "Feuille": "1/1",
                  "TypeDoc": "Dessin de piece"}
        if info:
            champs["Numero"] = "ECH-" + info[0][1]
            champs["Echelle"] = info[0][2]
            if info[0][1] == "ENS":
                champs["TypeDoc"] = "Dessin d'ensemble"
        try:
            t = dict(tpl.EditableTexts)
            t.update({c: v for c, v in champs.items() if c in t})
            tpl.EditableTexts = t
            print("OK     : %-28s %s | champs : %s" % (pg.Label, fmt, sorted(t)))
        except Exception as e:
            print("OK     : %-28s %s | cartouche a remplir a la main (%s)" % (pg.Label, fmt, e))
    except Exception as e:
        print("ECHEC  : %s -> %s" % (pg.Label, e))
doc.recompute()
print("termine : %d pages. Verifie le cartouche (double-clic sur un champ) et l echelle." % total)
