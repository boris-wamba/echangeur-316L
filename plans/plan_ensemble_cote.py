#!/usr/bin/env python3
# Reconstruit le plan d'ensemble a partir de l'export SVG de TechDraw :
#  - garde la geometrie reelle des 3 vues (aucune reconstruction) et le cartouche,
#  - retire les anciennes cotes, la nomenclature et les hachures raster,
#  - passe l'ensemble a l'echelle 1:5 (3 vues a la meme echelle), vues remises en 1er dièdre,
#  - ajoute hachures vectorielles, cotation, ballons, trace de coupe A-A, nomenclature, notes.
# Usage : python3 plan_ensemble_cote.py Plan_ensemble.svg sortie/Plan_ensemble_cote.svg
import re, sys, math
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
for p, u in [('', 'http://www.w3.org/2000/svg'), ('xlink', 'http://www.w3.org/1999/xlink'),
             ('freecad', 'https://www.freecad.org/wiki/index.php?title=Svg_Namespace'),
             ('inkscape', 'http://www.inkscape.org/namespaces/inkscape'),
             ('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'),
             ('dc', 'http://purl.org/dc/elements/1.1/'), ('cc', 'http://creativecommons.org/ns#'),
             ('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')]:
    ET.register_namespace(p, u)

SRC = sys.argv[1] if len(sys.argv) > 1 else 'Plan_ensemble.svg'
DST = sys.argv[2] if len(sys.argv) > 2 else 'sortie/Plan_ensemble_cote.svg'

# ---------------- parametres de mise en page (mm sur la page) ----------------
K = 0.2                      # mm de page par mm de modele (1:5)
S = 0.5                      # facteur 1:2,5 -> 1:5 applique aux vues de l'export
SX, SY = 180.0, 150.0        # axe de la coupe : (modele x=275, y=0)
FY = 62.0                    # axe de la vue de dessous (modele x=275, z=0)
EX = 62.0                    # axe de la vue de bout
ORIG = {'sec': (2586.78, 793.084), 'face': (2338.2, 1766.95), 'end': (610.602, 789.074)}
NEW = {'sec': (SX * 10, SY * 10), 'face': (SX * 10, FY * 10), 'end': (EX * 10, SY * 10)}
NOM_T = {'matrix(2.37941,0,0,2.3771,316.973,2261.96)', 'matrix(0.285529,0,0,0.285252,316.973,2261.96)'}


def sx(mx): return SX + (mx - 275.0) * K          # coupe : x modele -> page
def sy(my): return SY - my * K                    # coupe : y modele -> page
def fy(mz): return FY - mz * K                    # vue de dessous : z modele -> page


def matrice(g):
    m = re.match(r'matrix\(([^)]*)\)', g.get('transform') or '')
    return [float(v) for v in m.group(1).split(',')] if m else None


def est_cote(g):
    ch = [x.tag.replace(NS, '') for x in g]
    a = g.attrib
    if g.get('transform') in NOM_T:
        return False
    if ch == ['text']:
        return True
    if a.get('fill') == 'none' and a.get('stroke') == '#212529' and a.get('stroke-width') == '3.5' and ch == ['path']:
        return True
    if a.get('fill') == '#212529' and a.get('stroke-width') == '3.5' and ch == ['path']:
        return True
    return False


def mettre_echelle(d, f):
    def r(m):
        return ('%.3f' % (float(m.group(0)) * f)).rstrip('0').rstrip('.')
    return re.sub(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', r, d)


def bbox_d(d):
    n = [float(v) for v in re.findall(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', d)]
    xs, ys = n[0::2], n[1::2]
    return min(xs), max(xs), min(ys), max(ys)


tree = ET.parse(SRC)
root = tree.getroot()
dc = [e for e in root.iter() if e.get('id') == 'DrawingContent'][0]
parent = [p for p in root.iter() if dc in list(p)][0]

# ---------------- 1. tri des groupes ----------------
groupes = list(dc)
vues = {'sec': [], 'face': [], 'end': []}
hachures = []
nb = {'cotes': 0, 'nomenclature': 0, 'trace': 0, 'marques': 0, 'images': 0}
for g in groupes:
    ch = [x.tag.replace(NS, '') for x in g]
    a = g.attrib
    if est_cote(g):
        nb['cotes'] += 1; dc.remove(g); continue
    if g.get('transform') in NOM_T:
        nb['nomenclature'] += 1; dc.remove(g); continue
    if ch == ['image']:
        nb['images'] += 1; dc.remove(g); continue
    if a.get('stroke') == '#000000' or a.get('fill') == '#ffffff':
        nb['trace' if a.get('stroke') == '#000000' else 'marques'] += 1; dc.remove(g); continue
    m = matrice(g)
    cle = None
    for k, (ox, oy) in ORIG.items():
        if abs(m[4] - ox) < 0.05 and abs(m[5] - oy) < 0.05:
            cle = k
    if cle is None:
        raise SystemExit('groupe inattendu : %s' % g.get('transform'))
    vues[cle].append(g)
    if a.get('fill') == '#f1f3f5' and a.get('stroke') == '#212529' and a.get('stroke-width') == '0.7':
        hachures.append((cle, g))
print('retires :', nb, '| gardes :', {k: len(v) for k, v in vues.items()}, '| faces coupees :', len(hachures))

# ---------------- 2. transformation des vues ----------------
CORR_EP = {'7': '5', '5': '2.5', '3.5': '2.5'}
for cle, lst in vues.items():
    f = S if cle in ('sec', 'face') else 1.0
    nx, ny = NEW[cle]
    for g in lst:
        for p in g.iter(NS + 'path'):
            if f != 1.0:
                p.set('d', mettre_echelle(p.get('d'), f))
        g.set('transform', 'matrix(1,0,0,1,%g,%g)' % (nx, ny))
        sw = g.get('stroke-width')
        if sw in CORR_EP and g.get('fill') != '#212529':
            if g.get('stroke-dasharray'):
                g.set('stroke-dasharray', '60,15,10,15')
            g.set('stroke-width', CORR_EP[sw])
        if g.get('fill') == '#f1f3f5':
            g.set('fill', '#ffffff')

# ---------------- 3. hachures vectorielles (trois motifs) ----------------
defs = root.find(NS + 'defs')
if defs is None:
    defs = ET.SubElement(root, NS + 'defs')
for nom, ang, pas in (('hA', 45, 15), ('hB', 135, 15), ('hC', 45, 25)):
    pat = ET.SubElement(defs, NS + 'pattern', {'id': nom, 'patternUnits': 'userSpaceOnUse', 'width': str(pas),
                                               'height': str(pas), 'patternTransform': 'rotate(%d)' % ang})
    ET.SubElement(pat, NS + 'rect', {'width': str(pas), 'height': str(pas), 'fill': '#ffffff'})
    ET.SubElement(pat, NS + 'line', {'x1': '0', 'y1': '0', 'x2': '0', 'y2': str(pas), 'stroke': '#000000', 'stroke-width': '2.5'})


def motif(cx, cy, w, h):
    """cx, cy, largeur, hauteur de la face en mm de modele (coupe)."""
    if (cx < 25 and w <= 30 and h > 20) or (cx > 525 and w <= 30 and h > 20 and 525 <= cx - w / 2 + 1):
        pass
    if 0 <= cx - w / 2 + 1 and cx + w / 2 <= 25 + 1:        # plaque gauche
        return 'hB'
    if cx - w / 2 >= 524 and cx + w / 2 <= 551:              # plaque droite
        return 'hB'
    if cx + w / 2 <= 1 or cx - w / 2 >= 549:                 # boites
        if w < 5 and h > 60:                                 # parois de tubulures de boite
            return 'hA'
        return 'hC'
    if w < 5 and h > 60:                                     # parois de tubulures de calandre
        return 'hB'
    if h < 5 and w > 60:                                     # calandre
        return 'hA'
    if w >= 49 and h < 25 and cy < -75:                      # pattes
        return 'hB'
    if w <= 5.1 and h > 20:                                  # chicanes
        return 'hC'
    return 'hA'                                              # tubes


for cle, g in hachures:
    if cle != 'sec':
        g.set('fill', '#ffffff'); continue
    x0, x1, y0, y1 = bbox_d(g.find(NS + 'path').get('d'))
    # coordonnees locales apres mise a l'echelle : 2 unites par mm de modele
    mx0, mx1, my0, my1 = 275 + x0 / 2, 275 + x1 / 2, -y1 / 2, -y0 / 2
    g.set('fill', 'url(#%s)' % motif((mx0 + mx1) / 2, (my0 + my1) / 2, mx1 - mx0, my1 - my0))

# ---------------- 4. surcouche : cotation, ballons, nomenclature ----------------
OUT = []
FONT = 'font-family="Inter, sans-serif"'


def fmt(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')


def L(x1, y1, x2, y2, w=0.25, dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    OUT.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="#000" stroke-width="%g"%s/>' % (x1, y1, x2, y2, w, d))


def T(x, y, s, size=4.0, anchor='middle', rot=0):
    tr = ' transform="rotate(%g %.3f %.3f)"' % (rot, x, y) if rot else ''
    OUT.append('<text x="%.3f" y="%.3f" %s font-size="%g" text-anchor="%s" fill="#000"%s>%s</text>' % (x, y, FONT, size, anchor, tr, s))


def ARR(x, y, ux, uy):
    nx, ny = -uy, ux
    bx, by = x - 3.0 * ux, y - 3.0 * uy
    OUT.append('<polygon points="%.3f,%.3f %.3f,%.3f %.3f,%.3f" fill="#000"/>' % (x, y, bx + 0.9 * nx, by + 0.9 * ny, bx - 0.9 * nx, by - 0.9 * ny))


def DOT(x, y):
    OUT.append('<circle cx="%.3f" cy="%.3f" r="0.8" fill="#000"/>' % (x, y))


def lg(s):                      # largeur approximative d'un texte (mm)
    return 0.6 * 4.0 * len(s)


def dim_h(xa, xb, yd, txt, ya, yb=None, tx=None, ta='middle'):
    yb = ya if yb is None else yb
    for xx, yf in ((xa, ya), (xb, yb)):
        s = 1 if yd > yf else -1
        L(xx, yf + s * 1.0, xx, yd + s * 2.0)
    xa, xb = min(xa, xb), max(xa, xb)
    if xb - xa >= lg(txt) + 7:
        L(xa, yd, xb, yd); ARR(xa, yd, -1, 0); ARR(xb, yd, 1, 0)
    else:
        L(xa - 5, yd, xb + 5, yd); ARR(xa, yd, 1, 0); ARR(xb, yd, -1, 0)
    T((xa + xb) / 2 if tx is None else tx, yd - 1.0, txt, anchor=ta)


def dim_v(ya, yb, xd, txt, xa=None, xb=None, cote='gauche'):
    for yy, xf in ((ya, xa), (yb, xb if xb is not None else xa)):
        if xf is not None:
            s = 1 if xd > xf else -1
            L(xf + s * 1.0, yy, xd + s * 2.0, yy)
    ya, yb = min(ya, yb), max(ya, yb)
    if yb - ya >= lg(txt) + 7:
        L(xd, ya, xd, yb); ARR(xd, ya, 0, -1); ARR(xd, yb, 0, 1)
    else:
        L(xd, ya - 5, xd, yb + 5); ARR(xd, ya, 0, 1); ARR(xd, yb, 0, -1)
    if cote == 'gauche':
        T(xd - 1.0, (ya + yb) / 2, txt, rot=-90)
    else:
        T(xd + 3.4, (ya + yb) / 2, txt, rot=-90)


def leader(px, py, ang, txt, ext=6.0, lon=None):
    u = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    qx, qy = px + ext * u[0], py + ext * u[1]
    L(qx, qy, px, py); ARR(px, py, -u[0], -u[1])
    lon = lon or lg(txt) + 2
    s = 1 if u[0] >= 0 else -1
    L(qx, qy, qx + s * lon, qy)
    T(qx + s * 1.0, qy - 1.0, txt, anchor='start' if s > 0 else 'end') if False else \
        T(qx + (1.0 if s > 0 else -1.0), qy - 1.0, txt, anchor='start' if s > 0 else 'end')


def dia(cx, cy, r, ang, txt, ext=5.0):
    u = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    p1 = (cx + r * u[0], cy + r * u[1]); p2 = (cx - r * u[0], cy - r * u[1])
    L(p2[0], p2[1], p1[0] + ext * u[0], p1[1] + ext * u[1])
    ARR(p1[0], p1[1], u[0], u[1]); ARR(p2[0], p2[1], -u[0], -u[1])
    qx, qy = p1[0] + ext * u[0], p1[1] + ext * u[1]
    lon = lg(txt) + 2
    s = 1 if u[0] >= 0 else -1
    L(qx, qy, qx + s * lon, qy)
    T(qx + (1.0 if s > 0 else -1.0), qy - 1.0, txt, anchor='start' if s > 0 else 'end')


def chain(x1, y1, x2, y2):
    L(x1, y1, x2, y2, 0.25, '6,1.5,1,1.5')


def croix(x, y, t=2.4):
    L(x - t, y, x + t, y); L(x, y - t, x, y + t)


def ballon(num, bx, by, tx, ty, r=4.2):
    d = math.hypot(tx - bx, ty - by)
    ex, ey = bx + (tx - bx) / d * r, by + (ty - by) / d * r
    L(ex, ey, tx, ty); DOT(tx, ty)
    OUT.append('<circle cx="%.3f" cy="%.3f" r="%g" fill="#fff" stroke="#000" stroke-width="0.25"/>' % (bx, by, r))
    T(bx, by + 1.8, str(num), 5.0)


# ---- reperes de projection : positions modele -> page ----
X0, XF = -100.0, 650.0            # extremites du modele
Y_SH = 84.15                      # rayon exterieur de la calandre
# axes (lignes mixtes) des tubulures dans la coupe
for xn, haut in ((-54, True), (125, True), (425, False), (604, False)):
    xp = sx(xn)
    if haut:
        chain(xp, sy(154.15) - 3, xp, sy(60))
    else:
        chain(xp, sy(-60), xp, sy(-154.15) + 3)
chain(sx(X0) - 6, SY, sx(XF) + 6, SY)                       # axe de la calandre (coupe)
chain(sx(X0) - 6, FY, sx(XF) + 6, FY)                       # axe (vue de dessous)

# ---- COUPE : cotes en haut (nozzles +Y, longueur calandre) ----
yA1, yA2, yA3 = sy(154.15) - 7.0, sy(154.15) - 15.0, sy(154.15) - 23.0
dim_h(sx(X0), sx(-54), yA1, '46', sy(84.15) - 0.0, sy(154.15))
dim_h(sx(X0), sx(125), yA2, '225', sy(84.15), sy(154.15), tx=sx(75))
dim_h(sx(25), sx(525), yA3, '500', sy(115), sy(115))
# ---- COUPE : cotes en bas ----
b0 = sy(-154.15) + 7.0
yB = [b0 + 8.0 * i for i in range(5)]
dim_h(sx(X0), sx(90), yB[0], '190', sy(-84.15), sy(-99.2), tx=sx(-50))
dim_h(sx(90), sx(300), yB[0], '210', sy(-99.2), sy(-99.2))
dim_h(sx(X0), sx(425), yB[1], '525', sy(-84.15), sy(-154.15))
dim_h(sx(X0), sx(604), yB[2], '704', sy(-84.15), sy(-154.15))
dim_h(sx(X0), sx(0), yB[3], '100', sy(-115), sy(-115))
dim_h(sx(0), sx(550), yB[3], '550', sy(-115), sy(-115))
dim_h(sx(550), sx(XF), yB[3], '100', sy(-115), sy(-115))
dim_h(sx(X0), sx(XF), yB[4], '(750)', sy(-84.15), sy(-84.15))
for xn in (90, 300):
    chain(sx(xn), sy(-99.2) + 1.5, sx(xn), yB[0] + 2)       # axes de pattes
chain(sx(425), sy(-154.15) + 3, sx(425), yB[1] + 2)
chain(sx(604), sy(-154.15) + 3, sx(604), yB[2] + 2)

# ---- VUE DE DESSOUS : pattes et tubulures ----
croix(sx(425), FY); croix(sx(604), FY)
dim_h(sx(65), sx(115), fy(-40) + 5.6, '2× 50', fy(-40), fy(-40), tx=sx(115) + 6.5, ta='start')
dim_v(fy(40), fy(-40), sx(135), '80', sx(115), sx(115), cote='droite')
# (tubulures : voir note 5)

# ---- VUE DE BOUT ----
R_F, R_S, R_P = 115.0 * K, Y_SH * K, 97.5 * K
OUT.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="none" stroke="#000" stroke-width="0.25" stroke-dasharray="6,1.5,1,1.5"/>' % (EX, SY, R_P))
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    croix(EX + R_P * math.cos(a), SY - R_P * math.sin(a), 2.2)
chain(EX - R_F - 4, SY, EX + R_F + 4, SY); chain(EX, SY - 31.5, EX, SY + 31.5)
dim_h(EX - 30.15 * K, EX + 30.15 * K, SY - 154.15 * K - 7.0, 'Ø60,3', SY - 154.15 * K)
dim_v(SY - 154.15 * K, SY + 154.15 * K, EX + 23.0 + 12.0, '308,3', EX + 6.1, EX + 6.1)
dia(EX, SY, R_F, 150, 'Ø230', ext=5.0)
dia(EX, SY, R_S, 210, 'Ø168,3', ext=10.5)
a = math.radians(315)
leader(EX + R_P * math.cos(a), SY - R_P * math.sin(a), 315, 'Ø195', ext=9.0)
a = math.radians(67.5)
leader(EX + R_P * math.cos(a) + 1.4 * math.cos(math.radians(45)), SY - R_P * math.sin(a) - 1.4 * math.sin(math.radians(45)), 45, '8× Ø14', ext=9.0)

# ---- trace de coupe A-A sur la vue de dessous ----
xl, xr = sx(X0) - 9.0, sx(XF) + 9.0
L(xl, FY, xr, FY, 0.25, '6,1.5,1,1.5')
for xx, s in ((xl, 1), (xr, -1)):
    L(xx, FY, xx + s * 6.0, FY, 0.7)
    L(xx, FY, xx, FY + 8.0, 0.5); ARR(xx, FY + 8.0, 0, 1)
    T(xx, FY - 2.0, 'A', 5.0)

# ---- titre de la coupe ----
T(SX, yB[4] + 11.0, 'A-A', 5.0)

# ---- ballons ----
ballon(2, sx(60), sy(143), sx(12.5), sy(100))
ballon(4, sx(195), sy(120), sx(195), sy(66))
ballon(3, sx(260), sy(120), sx(260), sy(52.7))
ballon(1, sx(420), sy(120), sx(420), sy(81.95))
ballon(5, sx(610), sy(118), sx(610), sy(82))
ballon(6, sx(505), sy(-140), sx(453.2), sy(-140))
ballon(7, sx(360), sy(-120), sx(320), sy(-91))

# ---- nomenclature (au-dessus de la zone annexe du cartouche) ----
COL = [12, 50, 12, 18, 30, 28]
ENT = ['Rep', 'Désignation', 'Qté', 'Matière', 'Masse unit. (kg)', 'Plan']
LIG = [('1', 'Calandre', '1', '316L', '9,05', 'ECH-P1'), ('2', 'Plaque tubulaire', '2', '316L', '6,95', 'ECH-P2'),
       ('3', 'Tube', '19', '316L', '0,39', 'ECH-P3'), ('4', 'Chicane', '2', '316L', '0,38', 'ECH-P4'),
       ('5', 'Boîte de distribution', '2', '316L', '6,54', 'ECH-P5'), ('6', 'Tubulure DN50', '4', '316L', '0,42', 'ECH-P6'),
       ('7', "Patte d'appui", '2', '316L', '0,73', 'ECH-P7')]
tot = sum(int(l[2]) * float(l[4].replace(',', '.')) for l in LIG)
NX1, NY1, RH = 410.0, 233.0, 7.0
NX0 = NX1 - sum(COL)
nlig = len(LIG) + 2
ny0 = NY1 - nlig * RH
OUT.append('<rect x="%g" y="%g" width="%g" height="%g" fill="none" stroke="#000" stroke-width="0.5"/>' % (NX0, ny0, sum(COL), nlig * RH))
for i in range(1, nlig):
    L(NX0, ny0 + i * RH, NX1, ny0 + i * RH, 0.25 if i > 1 else 0.5)
xx = NX0
for c in COL[:-1]:
    xx += c
    L(xx, ny0, xx, ny0 + (nlig - 1) * RH, 0.25)
for r_i, ligne in enumerate([ENT] + LIG):
    xx = NX0
    for c, val in zip(COL, ligne):
        T(xx + 1.5, ny0 + r_i * RH + 4.8, val, 3.4 if r_i == 0 else 3.6, 'start')
        xx += c
T(NX0 + 1.5, NY1 - 2.2, 'Masse totale (somme du tableau) : %s kg' % ('%.1f' % tot).replace('.', ','), 3.4, 'start')

# ---- notes ----
notes = ['NOTES',
         '1. Cotes en mm. Tolérances générales ISO 2768-m.',
         '2. Cotes de position repérées depuis la face gauche de la boîte gauche.',
         '3. Chicanes (rep. 4) : axes à 195 et 328 de la face gauche de la plaque (voir ECH-P4).',
         '4. Les chicanes ne figurent pas dans le modèle de calcul (voir rapport).',
         '5. Tubulures (rep. 6) : tube Ø60,3 × 3,9 (DN50), 4 exemplaires.']
for i, s in enumerate(notes):
    T(26, 247 + i * 5.2, s, 3.4, 'start')

# ---------------- 5. echelle dans le cartouche ----------------
for t in root.iter(NS + 'text'):
    s = ''.join(t.itertext())
    if s.strip() == '1:2,5':
        for tsp in t.iter():
            if tsp.text and tsp.text.strip() == '1:2,5':
                tsp.text = '1:5'

ov = ET.Element(NS + 'g', {'id': 'cotation_iso', 'transform': 'scale(10)', 'fill': 'none'})
ov.append(ET.fromstring('<g xmlns="http://www.w3.org/2000/svg">' + ''.join(OUT) + '</g>'))
idx = list(parent).index(dc)
parent.insert(idx + 1, ov)
tree.write(DST, encoding='utf-8', xml_declaration=True)
print('ecrit', DST)
