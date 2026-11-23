#!/usr/bin/env python3
"""Verifications analytiques (ordres de grandeur) de l'echangeur a plaques tubulaires fixes, 316L.
Les resultats sont a comparer aux resultats FEM (voir docs/ANALYSE_RESULTATS.md).
Toutes les longueurs en mm, contraintes en MPa, forces en N, temperatures en degC."""
import math

# ---- donnees (identiques au modele FEM) ----
E, NU, ALPHA, LAM = 193e3, 0.3, 16e-6, 15.0        # MPa, -, 1/K, W/(m.K)
S = 133.0                                           # MPa, admissible INDICATIF (a confirmer dans le code vise)
P_T, P_C = 1.0, 0.6                                 # MPa : cote tubes (10 bar), cote calandre (6 bar)
T_T, T_C, T_REF = 120.0, 40.0, 20.0                 # degC
H_T, H_C = 1500.0, 800.0                            # W/(m2.K)
R_CAL_E, E_CAL = 84.15, 4.5                         # calandre : rayon exterieur, epaisseur
R_CAL_I = R_CAL_E - E_CAL
R_TUBE_E, E_TUBE, N_TUBES = 9.525, 1.65, 19
R_TUBE_I = R_TUBE_E - E_TUBE
L_CAL, L_TUBE = 500.0, 550.0
E_FOND, E_PLAQUE, PAS, D_TROU = 12.0, 25.0, 25.4, 19.0

print("=== 1. Thermique : tube = resistances en serie (par metre de tube) ===")
Ri = 1 / (H_T * 2 * math.pi * R_TUBE_I * 1e-3)
Rw = math.log(R_TUBE_E / R_TUBE_I) / (2 * math.pi * LAM)
Ro = 1 / (H_C * 2 * math.pi * R_TUBE_E * 1e-3)
q = (T_T - T_C) / (Ri + Rw + Ro)
Ti = T_T - q * Ri
To = Ti - q * Rw
print(f"flux lineique {q:.0f} W/m ; paroi interne {Ti:.1f} degC ; paroi externe {To:.1f} degC ; moyenne {(Ti+To)/2:.1f} degC")
T_TUBES = (Ti + To) / 2

print("\n=== 2. Pression : parois minces et plaque circulaire ===")
s_cal = P_C * R_CAL_I / E_CAL
s_box = P_T * R_CAL_I / E_CAL
print(f"calandre : sigma_theta = P R / e = {s_cal:.1f} MPa")
print(f"virole de boite : sigma_theta = {s_box:.1f} MPa")
r_over_t2 = (R_CAL_I / E_FOND) ** 2
print(f"fond plat e={E_FOND:.0f} mm, P={P_T} MPa : centre encastre {3*(1+NU)/8*P_T*r_over_t2:.1f} MPa ; "
      f"appuye {3*(3+NU)/8*P_T*r_over_t2:.1f} MPa ; bord encastre {0.75*P_T*r_over_t2:.1f} MPa")
dP = P_T - P_C
eta = (PAS - D_TROU) / PAS
sig_plaque = 0.75 * dP * (R_CAL_I / E_PLAQUE) ** 2
print(f"plaque pleine encastree, dP={dP:.1f} MPa : {sig_plaque:.1f} MPa ; rendement de ligament {eta:.3f} -> ligament ~ {sig_plaque/eta:.1f} MPa (borne haute, sans effet des tubes)")

print("\n=== 3. Efforts axiaux ===")
A_T = N_TUBES * math.pi * (R_TUBE_E**2 - R_TUBE_I**2)
A_C = math.pi * (R_CAL_E**2 - R_CAL_I**2)
A_Ti = N_TUBES * math.pi * R_TUBE_I**2
A_Cl = math.pi * R_CAL_I**2 - N_TUBES * math.pi * R_TUBE_E**2
print(f"section metal tubes {A_T:.0f} mm2 ; calandre {A_C:.0f} mm2 ; interieur tubes {A_Ti:.0f} mm2 ; fluide calandre {A_Cl:.0f} mm2")
F_P = (P_T * A_Ti + P_C * A_Cl)
print(f"resultante des pressions sur une coupe : {F_P/1e3:.2f} kN (valeur attendue de l'integrale de sigma_xx)")
dT = T_TUBES - T_C
F_th = ALPHA * dT * E / (1 / A_T + 1 / A_C)
print(f"dilatation differentielle libre {ALPHA*dT*L_TUBE:.3f} mm sur {L_TUBE:.0f} mm (dT = {dT:.1f} K)")
print(f"plaques RIGIDES : force thermique {F_th/1e3:.0f} kN -> tubes {-F_th/A_T:.0f} MPa, calandre {F_th/A_C:.0f} MPa (bornes hautes)")
print(f"FEM M3 (C2) : tubes -55, calandre +41 MPa -> force ~ {55*A_T/1e3:.0f} kN, soit {55*A_T/F_th:.2f} de la borne rigide")

print("\n=== 4. Von Mises sur la calandre (cas C3, etat biaxial) ===")
sx, st = 45.5, s_cal
vm = math.sqrt(sx**2 + st**2 - sx * st)
print(f"sigma_x = {sx} (FEM), sigma_theta = {st:.1f} -> VM = {vm:.1f} MPa (FEM Pm calandre : 42.5)")

print("\n=== 5. Dilatations libres (ordre de grandeur du deplacement) ===")
for T, nom in ((T_TUBES, "element a la temperature moyenne des tubes"), (T_C, "element a 40 degC")):
    print(f"{nom} : {ALPHA*(T-T_REF)*750:.2f} mm sur 750 mm")
print("FEM M3 (C3) : deplacement maximal 0.507 mm")

print("\n=== 6. Marges indicatives (S = %.0f MPa) ===" % S)
for nom, v, lim in (("Pm max", 17.5, S), ("Pm+Pb primaire max", 41.2, 1.5 * S), ("Pm+Pb+Q max (ligament)", 71.2, 3 * S)):
    print(f"{nom} = {v} MPa ; limite {lim:.0f} MPa ; rapport {v/lim:.2f}")

print("\n=== 7. Flambement d'Euler d'un tube comprime (appui-appui, conservatif) ===")
I = math.pi / 4 * (R_TUBE_E**4 - R_TUBE_I**4)
A1 = math.pi * (R_TUBE_E**2 - R_TUBE_I**2)
for L, nom in ((L_TUBE, "sans chicane (L = 550 mm, cas le plus defavorable)"),):
    sig = math.pi**2 * E * I / L**2 / A1
    print(f"{nom} : sigma_critique = {sig:.0f} MPa (FEM : -55 MPa en moyenne)")
