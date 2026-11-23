#!/usr/bin/env python3
"""Video d'assemblage eclate de l'echangeur, a partir de la VRAIE geometrie FreeCAD.

Les pieces sont exportees en STL par export_pieces.py (dans FreeCAD), puis lues ici.
Usage : python3 video_eclate.py dossier_pieces dossier_sortie [--rapide] [--fps 24]
Prerequis : pip install pyvista ; ffmpeg dans le PATH.
"""
import argparse, math, os, shutil, subprocess, warnings
import numpy as np
import pyvista as pv
import vtk

warnings.filterwarnings("ignore")
vtk.vtkObject.GlobalWarningDisplayOff()
pv.OFF_SCREEN = True

# nom FreeCAD (Name) -> (fichier STL, famille, groupe de deplacement)
PIECES = [
    ("Link004", "Boites",              "boite_g"),
    ("Link005", "Boites",              "boite_d"),
    ("Link002", "Plaques tubulaires",  "plaque_g"),
    ("Link003", "Plaques tubulaires",  "plaque_d"),
    ("Link001", "Calandre",            "calandre"),
    ("Compound", "Tubes (19)",         "tubes"),
    ("Link007", "Tubulures",           "boite_g"),
    ("Link009", "Tubulures",           "boite_d"),
    ("Link006", "Tubulures",           "calandre"),
    ("Link008", "Tubulures",           "calandre"),
    ("Link010", "Pattes",              "calandre"),
    ("Link011", "Pattes",              "calandre"),
    ("Link012", "Chicanes",            "tubes"),
    ("Link013", "Chicanes",            "tubes"),
]
COULEURS = {"Boites": "#0072B2", "Plaques tubulaires": "#D55E00", "Calandre": "#009E73",
            "Tubes (19)": "#E69F00", "Tubulures": "#CC79A7", "Pattes": "#999999", "Chicanes": "#56B4E9"}
DECAL = {"boite_g": (-130, 0, 0), "boite_d": (130, 0, 0), "plaque_g": (-45, 0, 0), "plaque_d": (45, 0, 0),
         "calandre": (0, 230, 0), "tubes": (0, 0, 0)}
FENETRE = {"plaque_g": (0.0, 0.5), "plaque_d": (0.0, 0.5), "boite_g": (0.15, 0.75), "boite_d": (0.15, 0.75),
           "calandre": (0.55, 1.0), "tubes": (0.0, 1.0)}


def lire(dossier, nom):
    f = os.path.join(dossier, nom + ".stl")
    if not os.path.exists(f):
        raise SystemExit("fichier manquant : %s (lance d'abord export_pieces.py dans FreeCAD)" % f)
    m = pv.read(f).clean()
    return m.compute_normals(split_vertices=True, feature_angle=35.0)


def lisse(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def camera(c0, c1, p, az, elev=22.0):
    c = np.array([0.5 * (c0[0] + c1[0]), (0.5 * (c0[1] + c1[1])) * 0 + 115.0 * p, 0.0])
    L = max(c1[0] - c0[0], 1.0)
    r = 1.9 * L + 0.9 * L * p
    a, e = math.radians(az), math.radians(elev)
    pos = c + r * np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])
    return [tuple(pos), tuple(c), (0, 1, 0)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pieces"); ap.add_argument("sortie")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--rapide", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    frames_dir = os.path.join(a.sortie, "images_eclate")
    os.makedirs(frames_dir, exist_ok=True)
    taille = [640, 360] if a.rapide else [1280, 720]
    n_att, n_ecl, n_orb, n_ret = (2, 8, 6, 6) if a.rapide else (24, 120, 120, 96)
    pl = pv.Plotter(off_screen=True, window_size=taille)
    pl.set_background("white")
    acteurs, xs = [], []
    for nom, fam, grp in PIECES:
        m = lire(a.pieces, nom)
        print("%-9s %-20s %7d triangles  x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]" % ((nom, fam, m.n_cells) + tuple(m.bounds)))
        xs += [m.bounds[0], m.bounds[1]]
        acteurs.append((grp, pl.add_mesh(m, color=COULEURS[fam], smooth_shading=True, specular=0.3)))
    pl.add_legend(labels=[[f, c] for f, c in COULEURS.items()], bcolor="#333333", border=False,
                  loc="lower left", size=(0.27, 0.34), face="rectangle")
    pl.add_text("Echangeur a tubes et calandre 316L - assemblage eclate", position="upper_left",
                color="black", font_size=12)
    pl.add_text("Geometrie FreeCAD (pieces du modele)", position="lower_right", color="gray", font_size=8)
    c0, c1 = (min(xs), 0, 0), (max(xs), 0, 0)
    ligne = []
    ligne += [(0.0, 35.0 + 20.0 * i / n_att) for i in range(n_att)]
    ligne += [(i / (n_ecl - 1), 55.0 + 60.0 * i / (n_ecl - 1)) for i in range(n_ecl)]
    ligne += [(1.0, 115.0 + 360.0 * i / n_orb) for i in range(n_orb)]
    ligne += [(1.0 - i / (n_ret - 1), 115.0 + 40.0 * i / (n_ret - 1)) for i in range(n_ret)]
    for k, (p, az) in enumerate(ligne):
        for grp, act in acteurs:
            d0, d1 = FENETRE[grp]
            f = lisse((p - d0) / (d1 - d0)) if d1 > d0 else 0.0
            dx, dy, dz = DECAL[grp]
            act.position = (f * dx, f * dy, f * dz)
        pl.camera_position = camera(c0, c1, lisse(p), az)
        pl.render()
        pl.screenshot(os.path.join(frames_dir, "f_%04d.png" % k))
    pl.close()
    sortie = os.path.join(a.sortie, "00_assemblage_eclate.mp4")
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i",
                        os.path.join(frames_dir, "f_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", sortie], check=True)
        print("ecrit :", sortie)
    else:
        print("ffmpeg introuvable : images PNG dans", frames_dir)


if __name__ == "__main__":
    main()
