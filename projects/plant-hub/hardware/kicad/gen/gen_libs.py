#!/usr/bin/env python3
"""Write project-local 'plant' symbol + footprint libraries and lib tables."""
import uuid
from pathlib import Path

PRJ = Path(__file__).resolve().parent.parent
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def uid(k):
    return str(uuid.uuid5(NS, "plantlib" + k))


# ---- symbol library: reuse the symbol text from gen_sch ---------------------
import gen_sch  # noqa: E402  (side effect: regenerates schematic, harmless)

sym = gen_sch.lib_texts["plant:ESP32-C3-SuperMini"].replace(
    '(symbol "plant:ESP32-C3-SuperMini"', '(symbol "ESP32-C3-SuperMini"', 1)
(PRJ / "plant.kicad_sym").write_text(
    '(kicad_symbol_lib (version 20231120) (generator "gen_libs")\n%s\n)\n' % sym)

# ---- footprint: 2x8 socket rows, 2.54mm pitch, 15.24mm row spacing ----------
LEFT = ["IO5", "IO6", "IO7", "IO8", "IO9", "IO10", "IO20", "IO21"]
RIGHT = ["5V", "GND", "3V3", "IO4", "IO3", "IO2", "IO1", "IO0"]

pads, texts = [], []
for i in range(8):
    y = -8.89 + 2.54 * i
    for (num, x, names, just) in ((i + 1, -7.62, LEFT, "right"),
                                  (i + 9, 7.62, RIGHT, "left")):
        shape = "rect" if num == 1 else "circle"
        pads.append(
            '  (pad "%d" thru_hole %s (at %.2f %.2f) (size 1.7 1.7) (drill 1.0)'
            ' (layers "*.Cu" "*.Mask") (uuid "%s"))' % (num, shape, x, y, uid("pad%d" % num)))
        tx = x + (2.2 if just == "left" else -2.2)
        texts.append(
            '  (fp_text user "%s" (at %.2f %.2f 0) (layer "F.SilkS") (uuid "%s")\n'
            '    (effects (font (size 0.8 0.8) (thickness 0.12)) (justify %s)))'
            % (names[i], tx, y, uid("txt%d" % num), just))

lines = []
def rectangle(x0, y0, x1, y1, layer, w):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        lines.append(
            '  (fp_line (start %.2f %.2f) (end %.2f %.2f)'
            ' (stroke (width %s) (type solid)) (layer "%s") (uuid "%s"))'
            % (a[0], a[1], b[0], b[1], w, layer, uid("l%s%s%s%s%s" % (layer, a[0], a[1], b[0], b[1]))))

rectangle(-8.89, -11.43, 8.89, 11.43, "F.SilkS", 0.15)   # module outline
rectangle(-9.15, -11.7, 9.15, 11.7, "F.CrtYd", 0.05)
rectangle(-8.89, -11.43, 8.89, 11.43, "F.Fab", 0.1)
texts.append('  (fp_text user "USB" (at 0 -10.2 0) (layer "F.SilkS") (uuid "%s")\n'
             '    (effects (font (size 1 1) (thickness 0.15))))' % uid("usb"))

fp = '''(footprint "ESP32-C3-SuperMini-Socket"
  (version 20240108) (generator "gen_libs")
  (layer "F.Cu")
  (descr "Socket for ESP32-C3 Super Mini: two 1x8 female headers, 2.54mm pitch, rows 15.24mm apart")
  (tags "ESP32-C3 SuperMini socket")
  (attr through_hole)
  (property "Reference" "REF**" (at 0 -12.7 0) (layer "F.SilkS") (uuid "%s")
    (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "ESP32-C3 SuperMini" (at 0 12.7 0) (layer "F.Fab") (uuid "%s")
    (effects (font (size 1 1) (thickness 0.15))))
%s
%s
%s
)
''' % (uid("ref"), uid("val"), "\n".join(pads), "\n".join(lines), "\n".join(texts))

(PRJ / "plant.pretty").mkdir(exist_ok=True)
(PRJ / "plant.pretty" / "ESP32-C3-SuperMini-Socket.kicad_mod").write_text(fp)

(PRJ / "sym-lib-table").write_text(
    '(sym_lib_table\n  (version 7)\n'
    '  (lib (name "plant")(type "KiCad")(uri "${KIPRJMOD}/plant.kicad_sym")(options "")(descr "project lib"))\n)\n')
(PRJ / "fp-lib-table").write_text(
    '(fp_lib_table\n  (version 7)\n'
    '  (lib (name "plant")(type "KiCad")(uri "${KIPRJMOD}/plant.pretty")(options "")(descr "project lib"))\n)\n')
print("wrote plant.kicad_sym, plant.pretty/, lib tables")
