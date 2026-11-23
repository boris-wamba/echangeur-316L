# Prepare le calcul thermomecanique : temperature initiale + 2 convections
# (references reprises des deux charges de pression) + solveur en thermomecanique.
import FreeCAD as App
import ObjectsFem

doc = App.ActiveDocument
analyse = doc.getObjectsByLabel("Analysis")[0]
p_tubes = doc.getObject("Pression_tubes_10bar")
p_cal = doc.getObject("Pression_calandre_6bar")
solveur = doc.getObject("SolverCcxTools")

T_INIT_C = 20.0
COTE_TUBES = ("Convection_tubes", p_tubes, 120.0, 1500.0)    # nom, faces, T fluide (C), h (W/m2/K)
COTE_CALANDRE = ("Convection_calandre", p_cal, 40.0, 800.0)


def pas_a_pas(etape, f):
    try:
        f()
        print("OK   :", etape)
    except Exception as e:
        print("ECHEC:", etape, "->", e)


def conv(nom, ref, t_c, h):
    c = ObjectsFem.makeConstraintHeatflux(doc, nom)
    c.ConstraintType = "Convection"
    c.AmbientTemp = "%.2f K" % (t_c + 273.15)
    c.FilmCoef = "%.1f W/m^2/K" % h
    c.References = list(ref.References)
    analyse.addObject(c)


def initiale():
    ti = ObjectsFem.makeConstraintInitialTemperature(doc, "Temperature_initiale")
    ti.initialTemperature = "%.2f K" % (T_INIT_C + 273.15)
    analyse.addObject(ti)


def solveur_thermo():
    solveur.AnalysisType = "thermomech"
    solveur.ThermoMechSteadyState = True


pas_a_pas("temperature initiale 20 C", initiale)
pas_a_pas("convection cote tubes (120 C, h=1500)", lambda: conv(*COTE_TUBES))
pas_a_pas("convection cote calandre (40 C, h=800)", lambda: conv(*COTE_CALANDRE))
pas_a_pas("solveur en thermomecanique, regime stable", solveur_thermo)
doc.recompute()
print("Termine. Verifie l'arbre : 3 nouveaux objets sous Analysis.")
