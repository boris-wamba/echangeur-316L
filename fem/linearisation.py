# Linearisation des contraintes a travers une paroi (membrane + flexion + pic), le long de
# lignes definies par deux points p0 -> p1 (mm). Contraintes nodales interpolees lineairement
# dans les tetraedres (sommets seulement). L'epaisseur est MESUREE sur le maillage (portion
# continue de la ligne situee dans la matiere), la ligne est prolongee de EXT mm de chaque cote.
# Pour chaque composante : Pm = (1/t) int s ds ; Pb = (6/t^2) int s (t/2 - u) du (valeur en u=0).
import math, re
try:
    import FreeCAD as App
except ImportError:
    App = None

EXT, NPTS = 1.0, 141
LIGNES = [  # (nom, p0, p1, epaisseur nominale mm)
    ("fond_gauche_centre",   (-100.0, 0.0, 0.1), (-88.0, 0.0, 0.1), 12.0),
    ("fond_droit_centre",    (650.0, 0.0, 0.1),  (638.0, 0.0, 0.1), 12.0),
    ("calandre_x200",        (200.0, 0.1, 79.65), (200.0, 0.1, 84.15), 4.5),
    ("plaque_ligament_x0-25", (0.0, 0.0, 12.7),  (25.0, 0.0, 12.7), 25.0),
    ("virole_boite_g_x-80",  (-80.0, 0.1, 79.65), (-80.0, 0.1, 84.15), 4.5),
]
H = 6.0


def vm6(t):
    xx, yy, zz, xy, xz, yz = t
    return math.sqrt(0.5 * ((xx - yy)**2 + (yy - zz)**2 + (zz - xx)**2) + 3 * (xy**2 + xz**2 + yz**2))


def det3(a, b, c):
    return (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]))


class Locator:
    def __init__(self, pts, tets):
        self.pts, self.tets, self.g = pts, tets, {}
        for k, t in enumerate(tets):
            P = [pts[i] for i in t]
            lo = [min(p[a] for p in P) for a in range(3)]
            hi = [max(p[a] for p in P) for a in range(3)]
            for ix in range(int(lo[0] // H), int(hi[0] // H) + 1):
                for iy in range(int(lo[1] // H), int(hi[1] // H) + 1):
                    for iz in range(int(lo[2] // H), int(hi[2] // H) + 1):
                        self.g.setdefault((ix, iy, iz), []).append(k)

    def find(self, q, tol=1e-9):
        for k in self.g.get((int(q[0] // H), int(q[1] // H), int(q[2] // H)), ()):
            t = self.tets[k]
            P = [self.pts[i] for i in t]
            r = [tuple(P[i][a] - P[0][a] for a in range(3)) for i in (1, 2, 3)]
            D = det3(r[0], r[1], r[2])
            if abs(D) < 1e-18:
                continue
            w = tuple(q[a] - P[0][a] for a in range(3))
            l1, l2, l3 = det3(w, r[1], r[2]) / D, det3(r[0], w, r[2]) / D, det3(r[0], r[1], w) / D
            lam = (1 - l1 - l2 - l3, l1, l2, l3)
            if min(lam) >= -tol:
                return t, lam
        return None


def linearise(loc, vals, p0, p1, ext=EXT, n=NPTS):
    L = math.dist(p0, p1)
    u = tuple((p1[a] - p0[a]) / L for a in range(3))
    s_all = [-ext + (L + 2 * ext) * i / (n - 1) for i in range(n)]
    smp = []
    for s in s_all:
        q = tuple(p0[a] + s * u[a] for a in range(3))
        f = loc.find(q)
        if f is None:
            smp.append((s, None)); continue
        t, lam = f
        smp.append((s, tuple(sum(lam[i] * vals[t[i]][c] for i in range(4)) for c in range(6))))
    runs, cur = [], []
    for s, v in smp:
        if v is None:
            if cur: runs.append(cur); cur = []
        else:
            cur.append((s, v))
    if cur: runs.append(cur)
    if not runs:
        return None
    run = max(runs, key=len)
    if len(run) < 5:
        return None
    s0, s1 = run[0][0], run[-1][0]
    t = s1 - s0
    def integ(f):
        return sum(0.5 * (f(run[i]) + f(run[i + 1])) * (run[i + 1][0] - run[i][0]) for i in range(len(run) - 1))
    Pm, Pb = [], []
    for c in range(6):
        Pm.append(integ(lambda r: r[1][c]) / t)
        Pb.append(6.0 / t**2 * integ(lambda r: r[1][c] * (t / 2 - (r[0] - s0))))
    face0 = tuple(Pm[c] + Pb[c] for c in range(6))
    face1 = tuple(Pm[c] - Pb[c] for c in range(6))
    pic = max(vm6(v) for s, v in run)
    return dict(t=t, n=len(run), tronque=(run[0][0] <= s_all[0] + 1e-9 or run[-1][0] >= s_all[-1] - 1e-9),
                Pm=vm6(Pm), PmPb=max(vm6(face0), vm6(face1)), pic=pic, Pm_vec=Pm)


if App is not None:
    for d in App.listDocuments().values():
        for o in d.Objects:
            if not (o.isDerivedFrom("Fem::FemResultObject") and len(o.vonMises) > 0):
                continue
            if not (o.Label in ("C1", "C2", "C3") or re.match(r"M\d+_C[123]$", o.Label)):
                continue
            fm = o.Mesh.FemMesh
            N = fm.Nodes
            nums = list(o.NodeNumbers)
            cols = (list(o.NodeStressXX), list(o.NodeStressYY), list(o.NodeStressZZ),
                    list(o.NodeStressXY), list(o.NodeStressXZ), list(o.NodeStressYZ))
            vals = {n: tuple(c[i] for c in cols) for i, n in enumerate(nums)}
            pts = {n: (N[n].x, N[n].y, N[n].z) for n in nums}
            tets = []
            for e in fm.Volumes:
                nd = fm.getElementNodes(e)[:4]
                if all(n in pts for n in nd):
                    tets.append(tuple(nd))
            loc = Locator(pts, tets)
            print("\n=== %s (%d noeuds) ===" % (o.Label, len(nums)))
            for nom, p0, p1, tn in LIGNES:
                r = linearise(loc, vals, p0, p1)
                if r is None:
                    print("%-24s : ligne hors matiere" % nom); continue
                print("%-24s t=%5.2f mm (nominal %.1f)%s | Pm %6.1f | Pm+Pb(max surface) %6.1f | pic max sur la ligne %6.1f MPa (VM)" % (
                    nom, r["t"], tn, " TRONQUEE" if r["tronque"] else "", r["Pm"], r["PmPb"], r["pic"]))
