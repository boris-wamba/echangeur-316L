# Force axiale par INTEGRATION SUR LA SURFACE dans des plans x=cste (coupe des tetraedres,
# sigma_xx interpole lineairement entre les 4 sommets). Remplace la moyenne simple de
# force_equilibre.py. Affiche aussi l'aire reelle de la coupe du maillage, a comparer a
# l'aire exacte : l'ecart mesure l'effet de facettisation (Second Order Linear).
import math, re
try:
    import FreeCAD as App
except ImportError:
    App = None

A_S_EX = math.pi * (84.15**2 - 79.65**2) / 2          # demi-modele
A_T_EX = 19 * math.pi * (9.525**2 - 7.875**2) / 2
A_AL = 19 * math.pi * 7.875**2
A_CAL = math.pi * 79.65**2 - 19 * math.pi * 9.525**2
PLANS = (200.0, 370.0)                                # loin des tubulures et des pattes


def coupe_tets(pts, tets, vals, x0):
    """pts: {id:(x,y,z)}, tets: [(i,j,k,l)], vals: {id:v}. Renvoie liste (aire, integrale, r_centre)."""
    out = []
    for t in tets:
        P = [pts[i] for i in t]
        d = [p[0] - x0 for p in P]
        pos = [k for k in range(4) if d[k] > 0]
        if len(pos) in (0, 4):
            continue
        neg = [k for k in range(4) if d[k] <= 0]
        def inter(a, b):
            s = d[a] / (d[a] - d[b])
            y = P[a][1] + s * (P[b][1] - P[a][1]); z = P[a][2] + s * (P[b][2] - P[a][2])
            v = vals[t[a]] + s * (vals[t[b]] - vals[t[a]])
            return (y, z, v)
        if len(pos) == 1 or len(pos) == 3:
            a = pos[0] if len(pos) == 1 else neg[0]
            others = neg if len(pos) == 1 else pos
            poly = [inter(a, b) for b in others]
        else:
            a, b = pos; c, e = neg
            poly = [inter(a, c), inter(a, e), inter(b, e), inter(b, c)]
        for tri in ([poly[0], poly[1], poly[2]],) + (([poly[0], poly[2], poly[3]],) if len(poly) == 4 else ()):
            (y1, z1, v1), (y2, z2, v2), (y3, z3, v3) = tri
            A = 0.5 * abs((y2 - y1) * (z3 - z1) - (y3 - y1) * (z2 - z1))
            out.append((A, A * (v1 + v2 + v3) / 3.0,
                        math.hypot((y1 + y2 + y3) / 3.0, (z1 + z2 + z3) / 3.0)))
    return out


def resume(cells):
    sh = [c for c in cells if 79.5 < c[2] < 84.6]
    tu = [c for c in cells if c[2] < 60]
    As, Fs = sum(c[0] for c in sh), sum(c[1] for c in sh)
    At, Ft = sum(c[0] for c in tu), sum(c[1] for c in tu)
    return As, Fs, At, Ft


if App is not None:
    for d in App.listDocuments().values():
        for o in d.Objects:
            if not (o.isDerivedFrom("Fem::FemResultObject") and len(o.vonMises) > 0):
                continue
            if not (o.Label in ("C1", "C2", "C3") or re.match(r"M\d+_C[123]$", o.Label)):
                continue
            fm = o.Mesh.FemMesh
            N = fm.Nodes
            nums, sxx = list(o.NodeNumbers), list(o.NodeStressXX)
            vals = dict(zip(nums, sxx))
            pts = {n: (N[n].x, N[n].y, N[n].z) for n in nums}
            tets = []
            for e in fm.Volumes:
                nd = fm.getElementNodes(e)[:4]
                if all(n in pts for n in nd):
                    tets.append(tuple(nd))
            att = 0.0 if o.Label.endswith("C2") else (1.0 * A_AL + 0.6 * A_CAL) / 1000.0
            for x0 in PLANS:
                As, Fs, At, Ft = resume(coupe_tets(pts, tets, vals, x0))
                F = 2 * (Fs + Ft) / 1000.0
                print("%-6s x=%3.0f | calandre: aire %6.1f (exact %6.1f) mm2, sigma %6.1f MPa | tubes: aire %6.1f (exact %6.1f) mm2, sigma %6.1f MPa | F %6.1f kN (attendu %4.1f)" % (
                    o.Label, x0, As, A_S_EX, Fs / As, At, A_T_EX, Ft / At, F, att))
