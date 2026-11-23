#!/usr/bin/env python3
"""Videos des resultats FEM a partir d'un fichier .vtu exporte de FreeCAD (PyVista + ffmpeg).

Usage : python3 video_fem.py resultat.vtu dossier_sortie [--fps 24] [--rapide] [--vm-max 100]
Scenes : 1) temperature, orbite autour du demi-modele ; 2) temperature, coupe qui balaie l'axe x ;
         3) von Mises sur la deformee, rampe de chargement puis orbite.
La rampe de chargement n'est PAS un transitoire : le calcul est lineaire et stationnaire, on
multiplie le champ par un facteur de 0 a 1 (equivalent a un chargement progressif).
Prerequis : pip install pyvista ; ffmpeg dans le PATH.
"""
import argparse, math, os, shutil, subprocess, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np
import pyvista as pv

pv.OFF_SCREEN = True


def detecter(mesh):
    noms = list(mesh.point_data.keys())
    print("Tableaux aux noeuds :", noms)
    def cherche(*cles, dim=None):
        for n in noms:
            m = n.lower()
            a = mesh.point_data[n]
            d = 1 if a.ndim == 1 else a.shape[1]
            if any(c in m for c in cles) and (dim is None or d == dim):
                return n
        return None
    return (cherche("displacement", "deplacement", "disp", dim=3),
            cherche("temperature", "temp", dim=1),
            cherche("mises", dim=1))


def echelle_depl(mesh, nom_d, facteur):
    d = np.linalg.norm(mesh.point_data[nom_d], axis=1).max()
    L = max(mesh.bounds[1] - mesh.bounds[0], mesh.bounds[3] - mesh.bounds[2], mesh.bounds[5] - mesh.bounds[4])
    return (facteur if facteur else 0.08 * L / d), d


def camera(mesh, az, elev=-30.0, zoom=1.0):
    c = np.array(mesh.center)
    L = max(mesh.bounds[1] - mesh.bounds[0], mesh.bounds[3] - mesh.bounds[2], mesh.bounds[5] - mesh.bounds[4])
    r = 1.9 * L / zoom
    a, e = math.radians(az), math.radians(elev)
    pos = c + r * np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)])
    return [tuple(pos), tuple(c), (0, 0, 1)]


def plotter(taille):
    p = pv.Plotter(off_screen=True, window_size=taille)
    p.set_background("white")
    return p


def ecrire(p, dossier, i):
    p.render()   # sans cela, PyVista peut renvoyer l'image precedente
    p.screenshot(os.path.join(dossier, "f_%04d.png" % i))


def encoder(dossier, sortie, fps):
    if not shutil.which("ffmpeg"):
        print("ffmpeg introuvable : les images PNG restent dans", dossier)
        return
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i",
                    os.path.join(dossier, "f_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", sortie], check=True)
    print("ecrit :", sortie)


def scene_orbite_T(mesh, nomT, T, rng, out, fps, n, taille):
    d = os.path.join(out, "s1"); os.makedirs(d, exist_ok=True)
    surf = mesh.extract_surface()
    p = plotter(taille)
    p.add_mesh(surf, scalars=nomT, cmap="inferno", clim=rng, show_edges=False,
               scalar_bar_args=dict(title="Temperature (degC)", color="black", n_labels=5, fmt="%.0f", position_x=0.25, position_y=0.04, width=0.5, height=0.06, title_font_size=14, label_font_size=12))
    p.add_text("Echangeur 316L - temperature, cas C3 (stationnaire)", position="upper_left", color="black", font_size=11)
    for i in range(n):
        p.camera_position = camera(mesh, 360.0 * i / n)
        ecrire(p, d, i)
    p.close()
    encoder(d, os.path.join(out, "01_temperature_orbite.mp4"), fps)


def scene_coupe_T(mesh, nomT, rng, out, fps, n, taille):
    d = os.path.join(out, "s2"); os.makedirs(d, exist_ok=True)
    x0, x1 = mesh.bounds[0], mesh.bounds[1]
    p = plotter(taille)
    p.add_mesh(mesh.extract_surface(), color="lightgrey", opacity=0.08)
    for i in range(n):
        x = x0 + (x1 - x0) * (0.02 + 0.96 * i / (n - 1))
        p.clear()
        p.add_mesh(mesh.extract_surface(), color="lightgrey", opacity=0.08)
        part = mesh.clip(normal=(1, 0, 0), origin=(x, 0, 0), invert=True)
        if part.n_cells:
            p.add_mesh(part.extract_surface(), scalars=nomT, cmap="inferno", clim=rng,
                       scalar_bar_args=dict(title="Temperature (degC)", color="black", n_labels=5, fmt="%.0f", position_x=0.25, position_y=0.04, width=0.5, height=0.06, title_font_size=14, label_font_size=12))
        p.add_text("Temperature - coupe a x = %3.0f mm" % x, position="upper_left", color="black", font_size=11)
        p.camera_position = camera(mesh, 55.0 + 20.0 * math.sin(2 * math.pi * i / n), elev=-25.0)
        ecrire(p, d, i)
    p.close()
    encoder(d, os.path.join(out, "02_temperature_coupe.mp4"), fps)


def scene_vm(mesh, nomD, nomV, vmax, facteur, out, fps, n_rampe, n_orbite, taille):
    d = os.path.join(out, "s3"); os.makedirs(d, exist_ok=True)
    s, dmax = echelle_depl(mesh, nomD, facteur)
    U = np.asarray(mesh.point_data[nomD], float)
    V = np.asarray(mesh.point_data[nomV], float)
    ref = mesh.extract_surface().extract_feature_edges(feature_angle=40.0, boundary_edges=True,
                                                       non_manifold_edges=False, manifold_edges=False)
    p = plotter(taille)
    total = n_rampe + n_orbite
    for i in range(total):
        lam = min(1.0, (i + 1) / n_rampe)
        lam = 0.5 - 0.5 * math.cos(math.pi * lam)          # montee douce 0 -> 1
        m = mesh.copy()
        m.points = mesh.points + lam * s * U
        m.point_data["vm"] = lam * V
        p.clear()
        p.add_mesh(m.extract_surface(), scalars="vm", cmap="viridis", clim=(0, vmax),
                   scalar_bar_args=dict(title="von Mises (MPa) - echelle tronquee a %g" % vmax,
                                        color="black", n_labels=5, fmt="%.0f", position_x=0.25, position_y=0.04, width=0.5, height=0.06, title_font_size=14, label_font_size=12))
        p.add_mesh(ref, color="gray", line_width=2, opacity=0.7)   # contour non deforme
        p.add_text("von Mises, chargement progressif x%.0f%%  |  deformee x%.0f (deplacement max reel %.2f mm), contour gris = non deforme" % (
            100 * lam, s, dmax), position="upper_left", color="black", font_size=10)
        az = 35.0 if i < n_rampe else 35.0 + 360.0 * (i - n_rampe) / n_orbite
        p.camera_position = camera(mesh, az, elev=-25.0)
        ecrire(p, d, i)
    p.close()
    encoder(d, os.path.join(out, "03_vonmises_deformee.mp4"), fps)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("vtu"); a.add_argument("sortie")
    a.add_argument("--fps", type=int, default=24)
    a.add_argument("--rapide", action="store_true", help="peu d'images, petite taille (test)")
    a.add_argument("--vm-max", type=float, default=100.0)
    a.add_argument("--facteur", type=float, default=0.0, help="facteur de deformee (defaut : auto)")
    a.add_argument("--scenes", default="123")
    a.add_argument("--unite-depl", choices=["auto", "m", "mm"], default="auto")
    a.add_argument("--unite-vm", choices=["auto", "pa", "mpa"], default="auto")
    arg = a.parse_args()
    os.makedirs(arg.sortie, exist_ok=True)
    mesh = pv.read(arg.vtu)
    nomD, nomT, nomV = detecter(mesh)
    print("deplacement :", nomD, "| temperature :", nomT, "| von Mises :", nomV)
    # Unites : l'export VTK de FreeCAD est en SI (deplacement en m, contrainte en Pa) alors que la
    # geometrie est en mm. Detection automatique, modifiable avec --unite-depl / --unite-vm.
    if nomD:
        U = np.asarray(mesh.point_data[nomD], float)
        dm = np.linalg.norm(U, axis=1).max()
        en_m = arg.unite_depl == "m" or (arg.unite_depl == "auto" and dm < 1e-2)
        if en_m:
            mesh.point_data[nomD] = U * 1000.0
        print("deplacement max brut %.3g -> %s ; deplacement max en mm : %.3f" % (
            dm, "lu en metres (x1000)" if en_m else "lu en mm", dm * (1000.0 if en_m else 1.0)))
    if nomV:
        V = np.asarray(mesh.point_data[nomV], float)
        en_pa = arg.unite_vm == "pa" or (arg.unite_vm == "auto" and V.max() > 1e4)
        if en_pa:
            mesh.point_data[nomV] = V / 1e6
        print("von Mises max brut %.3g -> %s ; max en MPa : %.1f" % (
            V.max(), "lu en Pa (/1e6)" if en_pa else "lu en MPa", V.max() / (1e6 if en_pa else 1.0)))
    n, taille = (6, [640, 360]) if arg.rapide else (120, [1280, 720])
    rng = None
    if nomT:
        T = np.asarray(mesh.point_data[nomT], float)
        if T.min() > 200:                       # kelvin -> degC
            mesh.point_data[nomT] = T - 273.15
            T = T - 273.15
        rng = (float(T.min()), float(T.max()))
        print("T : %.1f a %.1f degC" % rng)
    if "1" in arg.scenes and nomT:
        scene_orbite_T(mesh, nomT, T, rng, arg.sortie, arg.fps, n, taille)
    if "2" in arg.scenes and nomT:
        scene_coupe_T(mesh, nomT, rng, arg.sortie, arg.fps, n, taille)
    if "3" in arg.scenes and nomD and nomV:
        scene_vm(mesh, nomD, nomV, arg.vm_max, arg.facteur, arg.sortie, arg.fps,
                 n, n, taille)


if __name__ == "__main__":
    main()
