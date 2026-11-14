"""Piezas 3D Yagi 5el 915 MHz (v3): boom con aletas para la bornera del driven y bloque de corte.
Mismo boom/aletas que el v2 de 3 elementos; solo cambian posiciones y longitudes (yagi-dl6wu-5el-3mm20mm-915MHz.txt).
Uso: python3 build_boom_5el.py  (genera 2 STL v3 en esta carpeta; el soporte GoPro v2 sirve igual)
Ejes: X = largo del boom (reflector en 0; punta redondeada del lado directores, extremo cuadrado + GoPro del lado reflector), Y = a lo ancho (direccion de los elementos), Z = alto.
Todas las medidas en mm. AJUSTAR con calibre: BLOCK_X, BOOM_W, BOOM_H, COAX_D."""
import cadquery as cq

ELEMENTS = {"reflector": 0.0, "driven": 34.5, "director1": 59.7, "director2": 118.2, "director3": 188.6}  # posicion X (modelo MMANA 5el)
BOOM_W = 8.9       # ancho (Y = direccion de los elementos) -- ORIGINAL v1
BOOM_H = 11.0      # alto (Z): sube para que el eje a ZA=8 quede con pared sobre el agujero
ROD_D = 3.0        # varilla
HOLE_D = ROD_D + 0.2
CALLSIGN = "HJ7-RMN"
# Regleta (bornera) del driven -- SUPUESTOS, medir con calibre:
BLOCK_X = 9.0      # ancho de la regleta a lo largo del boom (medido 8 + 1 de tolerancia)
BLOCK_Y = 22.0     # largo de la regleta en Y (direccion de los elementos): las aletas la sostienen
WALL = 2.0         # espesor de las aletas laterales
TUNNEL_Z = 6.0     # base de la regleta al eje del alambre: 5 medidos + 1 de pegamento
FLOOR = 2.0        # piso que queda bajo la regleta (el boom no se parte)
CLEAR = 0.3        # holgura del nicho
# Forma (como el v1): punta redondeada, aristas largas achaflanadas, rampa a un extremo cuadrado para el manguito GoPro
NOSE_R = 3.0                  # radio de la punta redondeada (lado ultimo director) en planta
CH = 1.2                      # chaflan de las 4 aristas largas (v1: 1.6; menor para no tocar el agujero)
RAMP_L = 10.0                 # rampa chaflan->cuadrado
NOSE_X = max(ELEMENTS.values()) + 12.0  # punta redondeada, 12 mm tras el ultimo director
TAIL_X = -34.0                # extremo cuadrado del lado reflector: ahi va el soporte GoPro (cerca del driver)

# ALINEACION: el eje de la varilla queda a la misma altura ZA en los 3 elementos.
# El nicho del driven fija ZA (piso + eje del tunel de la regleta); reflector y director se perforan a esa misma ZA.
ZA = FLOOR + TUNNEL_Z
assert ZA + HOLE_D / 2 <= BOOM_H - CH, f"ZA={ZA}: el agujero toca el chaflan; bajar TUNNEL_Z/FLOOR o CH"

ramp0 = ELEMENTS["reflector"] - 4.0          # el chaflan termina 4 mm antes del reflector
ramp1 = ramp0 - RAMP_L                       # rampa hacia el tramo cuadrado (lado reflector)
x0, x1 = TAIL_X, NOSE_X
SLEEVE = 15.0                                # largo del manguito GoPro
# PRUEBA BASICA DE ORIENTACION: el GoPro va en el tramo cuadrado, con a lo mas 1 elemento (el reflector) entre el manguito y el driver
assert ramp1 - x0 >= SLEEVE, "el tramo cuadrado debe cubrir los 15 mm del manguito GoPro"
assert list(ELEMENTS)[1] == "driven" and sum(ELEMENTS["driven"] > v > x0 + SLEEVE for v in ELEMENTS.values()) <= 1, "GoPro a mas de 1 elemento del driver"
boom = cq.Workplane("XY").box(x1 - x0, BOOM_W, BOOM_H, centered=(False, True, False)).translate((x0, 0, 0))
boom = boom.edges("|Z and >X").fillet(NOSE_R)   # punta redondeada en planta

def corner(sy, sz, c, x):  # triangulo de chaflan en la esquina (sy*W/2, sz*H) del plano YZ a la posicion x
    cy, cz = sy * BOOM_W / 2, BOOM_H / 2 + sz * BOOM_H / 2
    return [(cy, cz), (cy - sy * c, cz), (cy, cz - sz * c)]
for sy in (-1, 1):
    for sz in (-1, 1):
        k = cq.Workplane("YZ").workplane(offset=ramp0).polyline(corner(sy, sz, CH, 0)).close().extrude(x1 - ramp0 + 1)
        ramp = (cq.Workplane("YZ").workplane(offset=ramp0).polyline(corner(sy, sz, CH, 0)).close()
                .workplane(offset=-RAMP_L).polyline(corner(sy, sz, 0.02, 0)).close().loft())
        boom = boom.cut(k.union(ramp))

# aletas del driven: bandeja (piso + 2 paredes en X) de BLOCK_Y de ancho, hasta el eje del alambre, que sostiene la regleta de 22 mm
xd = ELEMENTS["driven"]
TRAY_X, TRAY_Y = BLOCK_X + 2 * CLEAR, BLOCK_Y + 2 * CLEAR
tray = cq.Workplane("XY").box(TRAY_X + 2 * WALL, TRAY_Y, ZA, centered=(True, True, False)).translate((xd, 0, 0))
boom = boom.union(tray)

for name, x in ELEMENTS.items():
    if name == "driven":  # nicho abierto arriba y por los lados Y: la regleta sobresale del boom, como en la foto
        cut = cq.Workplane("XY").box(TRAY_X, TRAY_Y + 2, BOOM_H, centered=(True, True, False)).translate((x, 0, FLOOR))
    else:                 # elemento continuo: un agujero pasante en Y
        cut = cq.Workplane("XZ").center(x, ZA).circle(HOLE_D / 2).extrude((BOOM_W + 2) / 2, both=True)
    boom = boom.cut(cut)

# indicativo grabado en la cara superior, entre reflector y nicho del driven (se lee con la punta a la izquierda)
xt = (ELEMENTS["reflector"] + ELEMENTS["driven"] - TRAY_X / 2 - WALL) / 2
boom = boom.cut(cq.Workplane("XY").workplane(offset=BOOM_H - 0.6).center(xt, 0)
                .text(CALLSIGN, 4.0, 1.0, combine=False, halign="center", valign="center"))

cq.exporters.export(boom, "Yagi_915MHz_5el_v3.stl", tolerance=0.01)
bb = boom.val().BoundingBox()
print(f"boom {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm; eje de elementos a Z={ZA} en X={list(ELEMENTS.values())}; valido={boom.val().isValid()}")


# ---------- Bloque de corte (mismo concepto que el 1160 original): ranuras cerradas centradas en una linea media ----------
# La varilla se corta un poco larga y se lima hasta que cae justa en su ranura. La linea media sirve para centrar el dipolo.
ROD_D = 3.0
G_W, WALL, PLATE_H, G_DEPTH = ROD_D + 0.4, 3.0, 5.0, 2.5   # ranura, pared, espesor, profundidad (varilla queda a ras +0.5)
SLACK = 0.4                                                 # holgura de la ranura sobre la longitud nominal
LABEL_H, END_M, TOP_M = 3.0, 4.0, 14.0                      # texto de longitud (rotado, bajo cada ranura), margenes
LENGTHS = {"R": 173.6, "D": 157.8, "1": 137.2, "2": 137.9, "3": 136.3}  # reflector, driven, directores 1-3 (MMANA 5el, 915 MHz)
pitch = G_W + WALL
lmax = max(LENGTHS.values()) + SLACK
plate_w = WALL + len(LENGTHS) * pitch
BOT_M = END_M + 10                                           # abajo: etiqueta de longitud
plate_l = BOT_M + lmax + END_M + TOP_M                       # arriba: "915"
yc = BOT_M + lmax / 2                                   # linea media (centro de las ranuras)
blk = cq.Workplane("XY").box(plate_w, plate_l, PLATE_H, centered=False)

def engrave(txt, size, x, y, rot=0):
    t = cq.Workplane("XY").text(txt, size, 1.0, combine=False, halign="center", valign="center")
    if rot:
        t = t.rotate((0, 0, 0), (0, 0, 1), rot)
    return t.translate((x, y, PLATE_H - 0.6))

for i, (tag, L) in enumerate(LENGTHS.items()):
    gx = WALL + i * pitch + G_W / 2
    ln = L + SLACK
    blk = blk.cut(cq.Workplane("XY").box(G_W, ln, G_DEPTH, centered=(True, True, False)).translate((gx, yc, PLATE_H - G_DEPTH)))
    try:  # longitud grabada, leida a lo largo de Y, bajo el extremo inferior de su ranura
        blk = blk.cut(engrave(f"{L:.1f}", 2.6, gx, yc - ln / 2 - END_M - 5, rot=90))
    except Exception as e:
        print("sin texto:", e)
# marcas solo en la cara superior: cortes rectos de 0.6 x 0.5 mm (nada en el piso de las ranuras)
def mark(y, width):
    return cq.Workplane("XY").box(width, 0.6, 0.5, centered=(True, True, False)).translate((plate_w / 2 if width > plate_w else 0, y, PLATE_H - 0.5))
blk = blk.cut(mark(yc, plate_w + 2))                       # linea media, todo el ancho
for i, tag in enumerate(LENGTHS):
    if tag != "D":                                   # continuos: medio ancho de boom a cada lado del centro
        gx = WALL + i * pitch + G_W / 2
        for sgn in (-1, 1):
            blk = blk.cut(mark(yc + sgn * BOOM_W / 2, pitch).translate((gx, 0, 0)))
try:
    blk = blk.cut(engrave("915", 8, plate_w / 2, plate_l - TOP_M / 2 - 1))
except Exception as e:
    print("sin texto:", e)
cq.exporters.export(blk, "sd_yagi_915mhz_5el_sizing_block_v3.stl", tolerance=0.05, angularTolerance=0.5)
print("bloque", LENGTHS, f"placa {plate_w:.1f} x {plate_l:.1f} x {PLATE_H}")
# Soporte GoPro: sin cambios, usar sd_yagi_gopro_mount_v2.stl (mismo boom 8.9 x 11).
