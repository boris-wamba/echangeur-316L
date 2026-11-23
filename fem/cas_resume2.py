# Resume comparatif des cas C1 / C2 / C3 : temperatures, contraintes axiales moyennes,
# von Mises maximale par zone. Il faut que les objets de resultats importes aient pour
# LABEL "C1", "C2", "C3" ou "M2_C3", "M3_C3"... (touche F2 dans l'arbre pour renommer).
import math
import re
import FreeCAD as App

cas = {}
for d in App.listDocuments().values():
    for o in d.Objects:
        if o.isDerivedFrom("Fem::FemResultObject") and (o.Label in ("C1", "C2", "C3") or re.match(r"M\d+_C[123]$", o.Label)) and len(o.vonMises) > 0:
            cas[o.Label] = o
print("Cas trouves :", sorted(cas))


def zone_vm(x, y, z):
    r = math.hypot(y, z)
    if (65 <= x <= 115 or 275 <= x <= 325) and y < -70:
        return "pattes"
    if x < 0 or x > 550:
        return "boites"
    if (x <= 25 or x >= 525) and r >= 60:
        return "plaques"
    if r < 60:
        return "tubes"
    if 25 < x < 525 and 79.5 < r < 84.6:
        return "calandre"
    return "autre"


for nom in sorted(cas):
    res = cas[nom]
    N = res.Mesh.FemMesh.Nodes
    nums = list(res.NodeNumbers)
    vm = list(res.vonMises)
    sxx = list(res.NodeStressXX)
    T = list(res.Temperature) if len(res.Temperature) else [293.15] * len(nums)
    best, moy = {}, {"calandre": [], "tubes": []}
    for i, nid in enumerate(nums):
        p = N[nid]
        z = zone_vm(p.x, p.y, p.z)
        if z not in best or vm[i] > best[z][0]:
            best[z] = (vm[i], p.x, p.y, p.z)
        if z in moy and 100 <= p.x <= 450:
            moy[z].append((T[i] - 273.15, sxx[i]))
    print("\n===== %s : %d noeuds, deplacement max %.3f mm, T %.1f a %.1f C =====" % (
        nom, len(nums), max(res.DisplacementLengths), min(T) - 273.15, max(T) - 273.15))
    for z in ("calandre", "tubes", "plaques", "boites", "pattes"):
        if z in best:
            v, x, y, zz = best[z]
            extra = ""
            if z in moy and moy[z]:
                tm = sum(a for a, b in moy[z]) / len(moy[z])
                sm = sum(b for a, b in moy[z]) / len(moy[z])
                extra = " | moyenne (100<x<450) : T %.1f C, sigma_xx %.1f MPa" % (tm, sm)
            print("%-9s VM max %6.1f MPa en (%.0f, %.0f, %.0f)%s" % (z, v, x, y, zz, extra))
