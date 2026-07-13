#!/usr/bin/env python3
"""Generate plant-hub-v1.0.kicad_sch from netlist.py.

Approach: real KiCad library symbols are extracted from the installed
libraries and embedded, so ERC checks genuine pin types. All symbols are
placed at rotation 0 and connected with short wires + global labels +
power symbols, on a strict 1.27mm grid.
"""
import re
import uuid
from pathlib import Path

import netlist as NL

KICAD_SYMDIR = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
OUT = Path(__file__).resolve().parent.parent / "plant-hub-v1.0.kicad_sch"

NS = uuid.UUID("2f1b7a10-5c6e-4d29-9b1a-plant0000000".replace("plant0000000", "3d5e7f90a1b2"))
ROOT = str(uuid.uuid5(NS, "root-sheet"))


def uid(key):
    return str(uuid.uuid5(NS, key))


G = 1.27


def mm(gx):  # grid -> mm
    return round(gx * G, 2)


def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".") if abs(v - round(v)) > 1e-9 or True else str(v)


# ---------------------------------------------------------------- lib symbols
def extract_symbol(lib_file, name):
    txt = (KICAD_SYMDIR / lib_file).read_text()
    key = '(symbol "%s"' % name
    i = txt.find(key)
    if i < 0:
        raise SystemExit("symbol %s not found in %s" % (name, lib_file))
    depth = 0
    j = i
    in_str = False
    while j < len(txt):
        c = txt[j]
        if in_str:
            if c == '"' and txt[j - 1] != "\\":
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return txt[i:j + 1]
        j += 1
    raise SystemExit("unbalanced sexpr for " + name)


PIN_RE = re.compile(
    r'\(pin\s+(\w+)\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)\s*'
    r'\(length\s+[\d.]+\)(.*?)\(number\s+"([^"]+)"', re.S)


def pin_offsets(sym_text):
    """pin number -> (dx, dy) in symbol space (y up)."""
    pins = {}
    for m in PIN_RE.finditer(sym_text):
        pins[m.group(6)] = (float(m.group(2)), float(m.group(3)))
    return pins


ESP32_SYM = """(symbol "plant:ESP32-C3-SuperMini"
  (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "U" (at 0 13.97 0) (effects (font (size 1.27 1.27))))
  (property "Value" "ESP32-C3 SuperMini" (at 0 -13.97 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "plant:ESP32-C3-SuperMini-Socket" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (symbol "ESP32-C3-SuperMini_0_1"
    (rectangle (start -10.16 12.7) (end 10.16 -12.7)
      (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "ESP32-C3-SuperMini_1_1"
%s  )
)"""

_left = ["GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO20", "GPIO21"]
_right = ["5V", "GND", "3V3", "GPIO4", "GPIO3", "GPIO2", "GPIO1", "GPIO0"]
_types = {"9": "power_in", "10": "power_in", "11": "power_out"}


def esp32_pins_sexpr():
    out = []
    for i, nm in enumerate(_left):
        num = str(i + 1)
        y = 8.89 - 2.54 * i
        out.append(
            '    (pin %s line (at -12.7 %s 0) (length 2.54)\n'
            '      (name "%s" (effects (font (size 1.27 1.27))))\n'
            '      (number "%s" (effects (font (size 1.27 1.27)))))'
            % (_types.get(num, "bidirectional"), fmt(y), nm, num))
    for i, nm in enumerate(_right):
        num = str(i + 9)
        y = 8.89 - 2.54 * i
        out.append(
            '    (pin %s line (at 12.7 %s 180) (length 2.54)\n'
            '      (name "%s" (effects (font (size 1.27 1.27))))\n'
            '      (number "%s" (effects (font (size 1.27 1.27)))))'
            % (_types.get(num, "bidirectional"), fmt(y), nm, num))
    return "\n".join(out) + "\n"


LIBS = {
    "Device:R": ("Device.kicad_sym", "R"),
    "Device:C": ("Device.kicad_sym", "C"),
    "Device:C_Polarized": ("Device.kicad_sym", "C_Polarized"),
    "Device:LED": ("Device.kicad_sym", "LED"),
    "Transistor_FET:IRLIZ44N": ("Transistor_FET.kicad_sym", "IRLIZ44N"),
    "Transistor_FET:2N7000": ("Transistor_FET.kicad_sym", "2N7000"),
    "Connector:Screw_Terminal_01x02": ("Connector.kicad_sym", "Screw_Terminal_01x02"),
    "Connector:Screw_Terminal_01x03": ("Connector.kicad_sym", "Screw_Terminal_01x03"),
    "Connector_Generic:Conn_01x03": ("Connector_Generic.kicad_sym", "Conn_01x03"),
    "Connector_Generic:Conn_01x04": ("Connector_Generic.kicad_sym", "Conn_01x04"),
    "power:+5V": ("power.kicad_sym", "+5V"),
    "power:+3V3": ("power.kicad_sym", "+3V3"),
    "power:GND": ("power.kicad_sym", "GND"),
    "power:PWR_FLAG": ("power.kicad_sym", "PWR_FLAG"),
}

lib_texts = {}
for lib_id, (f, n) in LIBS.items():
    t = extract_symbol(f, n)
    t = t.replace('(symbol "%s"' % n, '(symbol "%s"' % lib_id, 1)
    lib_texts[lib_id] = t
lib_texts["plant:ESP32-C3-SuperMini"] = ESP32_SYM % esp32_pins_sexpr()

PINS = {lib_id: pin_offsets(t) for lib_id, t in lib_texts.items()}

# sanity checks on geometry assumptions
assert PINS["Device:R"]["1"][1] > 0 and PINS["Device:R"]["2"][1] < 0
assert PINS["Transistor_FET:IRLIZ44N"]["1"][0] < 0          # gate left
assert PINS["Transistor_FET:2N7000"]["2"][0] < 0      # gate left

# ---------------------------------------------------------------- emitters
S = []          # schematic body chunks
pwr_count = [0]


def wire(a, b):
    S.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'
             % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), uid("w%s%s%s%s" % (a + b))))


def poly(pts):
    for a, b in zip(pts, pts[1:]):
        wire(a, b)


def junction(p):
    S.append('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))'
             % (fmt(p[0]), fmt(p[1]), uid("j%s%s" % p)))


def no_connect(p):
    S.append('(no_connect (at %s %s) (uuid "%s"))' % (fmt(p[0]), fmt(p[1]), uid("nc%s%s" % p)))


def glabel(name, p, angle=0):
    S.append('(global_label "%s" (shape bidirectional) (at %s %s %d) (fields_autoplaced yes)\n'
             '  (effects (font (size 1.27 1.27)) (justify left))\n  (uuid "%s"))'
             % (name, fmt(p[0]), fmt(p[1]), angle, uid("gl%s%s%s" % (name, p[0], p[1]))))


def text(s, gx, gy, size=1.5):
    S.append('(text "%s" (exclude_from_sim no) (at %s %s 0)\n'
             '  (effects (font (size %s %s)) (justify left bottom)) (uuid "%s"))'
             % (s.replace('"', "'"), fmt(mm(gx)), fmt(mm(gy)), size, size, uid("t" + s[:40])))


ORIGINS = {}


def symbol(ref, lib_id, value, footprint, gx, gy):
    x, y = mm(gx), mm(gy)
    ORIGINS[ref] = (x, y, lib_id)
    pins = "\n".join('  (pin "%s" (uuid "%s"))' % (n, uid("pin%s-%s" % (ref, n)))
                     for n in sorted(PINS[lib_id], key=lambda s: int(s) if s.isdigit() else 0))
    hide_ref = "yes" if ref.startswith("#") else "no"
    # big symbols: keep ref/value text outside the body
    rv_dx, rv_dy = (3, 1.5) if "SuperMini" not in lib_id else (0, 16.51)
    S.append('''(symbol (lib_id "%s") (at %s %s 0) (unit 1)
  (exclude_from_sim no) (in_bom %s) (on_board yes) (dnp no) (fields_autoplaced yes)
  (uuid "%s")
  (property "Reference" "%s" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide %s)))
  (property "Value" "%s" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide %s)))
  (property "Footprint" "%s" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Datasheet" "~" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))
%s
  (instances (project "%s" (path "/%s" (reference "%s") (unit 1))))
)''' % (lib_id, fmt(x), fmt(y), "no" if ref.startswith("#") else "yes",
        uid("sym" + ref), ref, fmt(x + rv_dx), fmt(y - rv_dy), hide_ref,
        value, fmt(x + rv_dx), fmt(y + rv_dy), hide_ref,
        footprint, fmt(x), fmt(y),
        fmt(x), fmt(y), pins, NL.PROJECT, ROOT, ref))


def pin_pos(ref, pad):
    x, y, lib_id = ORIGINS[ref]
    dx, dy = PINS[lib_id][pad]
    return (round(x + dx, 2), round(y - dy, 2))     # symbol y-up -> sheet y-down


def power(net, p, kind=None):
    """Place a power symbol whose pin lands exactly at point p."""
    pwr_count[0] += 1
    ref = "#PWR%03d" % pwr_count[0]
    lib = {"+5V": "power:+5V", "+3V3": "power:+3V3",
           "GND": "power:GND", "PWR_FLAG": "power:PWR_FLAG"}[kind or net]
    symbol(ref, lib, kind or net, "", p[0] / G, p[1] / G)


def comp(ref, gx, gy):
    c = NL.COMPONENTS[ref]
    symbol(ref, c["symbol"], c["value"], c["footprint"], gx, gy)


# ---------------------------------------------------------------- layout
# --- power input: J1 + PWR_FLAGs -------------------------------------------
comp("J1", 30, 44)
e1, e2 = pin_pos("J1", "1"), pin_pos("J1", "2")
poly([e1, (e1[0] - 4 * G, e1[1]), (e1[0] - 4 * G, e1[1] - 2 * G)])
power("+5V", (e1[0] - 4 * G, e1[1] - 2 * G))
power("PWR_FLAG", (e1[0] - 2 * G, e1[1]), "PWR_FLAG")
junction((e1[0] - 2 * G, e1[1]))
poly([e2, (e2[0] - 6 * G, e2[1]), (e2[0] - 6 * G, e2[1] + 2 * G)])
power("GND", (e2[0] - 6 * G, e2[1] + 2 * G))
power("PWR_FLAG", (e2[0] - 4 * G, e2[1]), "PWR_FLAG")
junction((e2[0] - 4 * G, e2[1]))

# --- bulk + decoupling caps, power LED --------------------------------------
for ref, gx in (("C1", 44), ("C2", 52)):
    comp(ref, gx, 44)
    power("+5V", pin_pos(ref, "1"))
    power("GND", pin_pos(ref, "2"))
comp("C3", 60, 44)
power("+3V3", pin_pos("C3", "1"))
power("GND", pin_pos("C3", "2"))

comp("R6", 70, 42)
power("+5V", pin_pos("R6", "1"))
# LED below R6; orient so anode meets the wire from R6.2
a_dx = PINS["Device:LED"]["2"][0]          # anode x-offset in symbol space
r6b = pin_pos("R6", "2")
led_y = r6b[1] + 5 * G
symbol("D1", "Device:LED", NL.COMPONENTS["D1"]["value"],
       NL.COMPONENTS["D1"]["footprint"], (r6b[0] - a_dx) / G, led_y / G)
wire(r6b, pin_pos("D1", "2"))
power("GND", pin_pos("D1", "1"))

# --- U1 ESP32-C3 SuperMini ---------------------------------------------------
comp("U1", 110, 63)
p = pin_pos("U1", "9")   # 5V (top right)
poly([p, (p[0] + 2 * G, p[1]), (p[0] + 2 * G, p[1] - 2 * G)])
power("+5V", (p[0] + 2 * G, p[1] - 2 * G))
p = pin_pos("U1", "10")  # GND
poly([p, (p[0] + 6 * G, p[1]), (p[0] + 6 * G, p[1] + 4 * G)])
power("GND", (p[0] + 6 * G, p[1] + 4 * G))
p = pin_pos("U1", "11")  # 3V3
poly([p, (p[0] + 2 * G, p[1]), (p[0] + 2 * G, p[1] + 4 * G)])
power("+3V3", (p[0] + 2 * G, p[1] + 4 * G), "+3V3")
glabel("SOIL_ADC", pin_pos("U1", "16"))
glabel("CTRL_WHITE", pin_pos("U1", "2"), 180)
glabel("CTRL_PUMP", pin_pos("U1", "3"), 180)
glabel("CTRL_GROW", pin_pos("U1", "6"), 180)
for r, n in NL.NO_CONNECTS:
    if r == "U1":
        no_connect(pin_pos("U1", n))

# --- driver channel builder --------------------------------------------------
def channel(qref, g_pad, d_pad, s_pad, rser, rpull, ctrl, dlabel, X, Y):
    comp(qref, X, Y)
    gp = pin_pos(qref, g_pad)
    gj = (round(gp[0] - 4 * G, 2), gp[1])
    wire(gj, gp)
    comp(rser, gj[0] / G, gj[1] / G - 5)
    wire(pin_pos(rser, "2"), gj)
    glabel(ctrl, pin_pos(rser, "1"), 90)
    if rpull:
        comp(rpull, gj[0] / G, gj[1] / G + 5)
        wire(gj, pin_pos(rpull, "1"))
        power("GND", pin_pos(rpull, "2"))
        junction(gj)
    dp = pin_pos(qref, d_pad)
    wire(dp, (dp[0], dp[1] - 2 * G))
    glabel(dlabel, (dp[0], dp[1] - 2 * G), 90)
    power("GND", pin_pos(qref, s_pad))


channel("Q1", "1", "2", "3", "R1", "R2", "CTRL_WHITE", "LED_WHITE", 150, 36)
channel("Q2", "1", "2", "3", "R3", "R4", "CTRL_GROW", "LED_GROW", 150, 56)
channel("Q3", "2", "3", "1", "R5", "R7", "CTRL_PUMP", "RELAY_IN", 150, 76)

# --- connectors --------------------------------------------------------------
comp("J2", 180, 34)
p = pin_pos("J2", "1")
poly([p, (p[0] - 2 * G, p[1]), (p[0] - 2 * G, p[1] - 2 * G)])
power("+5V", (p[0] - 2 * G, p[1] - 2 * G))
glabel("LED_WHITE", pin_pos("J2", "2"), 180)
glabel("LED_GROW", pin_pos("J2", "3"), 180)

comp("K1", 180, 56)
p = pin_pos("K1", "1")
poly([p, (p[0] - 2 * G, p[1]), (p[0] - 2 * G, p[1] - 2 * G)])
power("+5V", (p[0] - 2 * G, p[1] - 2 * G))
p = pin_pos("K1", "2")
poly([p, (p[0] - 4 * G, p[1]), (p[0] - 4 * G, p[1] + 6 * G)])
power("GND", (p[0] - 4 * G, p[1] + 6 * G))
glabel("RELAY_IN", pin_pos("K1", "3"), 180)
no_connect(pin_pos("K1", "4"))

comp("J5", 180, 74)
p = pin_pos("J5", "1")
poly([p, (p[0] - 2 * G, p[1]), (p[0] - 2 * G, p[1] - 2 * G)])
power("+5V", (p[0] - 2 * G, p[1] - 2 * G))
glabel("PUMP_SW", pin_pos("J5", "2"), 180)

comp("J3", 180, 86)
glabel("PUMP_SW", pin_pos("J3", "1"), 180)
p = pin_pos("J3", "2")
poly([p, (p[0] - 2 * G, p[1]), (p[0] - 2 * G, p[1] + 2 * G)])
power("GND", (p[0] - 2 * G, p[1] + 2 * G))

comp("J4", 60, 70)
p = pin_pos("J4", "1")
poly([p, (p[0] - 2 * G, p[1]), (p[0] - 2 * G, p[1] - 2 * G)])
power("+3V3", (p[0] - 2 * G, p[1] - 2 * G))
p = pin_pos("J4", "2")
poly([p, (p[0] - 4 * G, p[1]), (p[0] - 4 * G, p[1] + 4 * G)])
power("GND", (p[0] - 4 * G, p[1] + 4 * G))
glabel("SOIL_ADC", pin_pos("J4", "3"), 180)

# --- notes -------------------------------------------------------------------
text("PUMP LOGIC: Q3 (2N7000) inverts. Relay module IN is active-LOW, so", 118, 96)
text("digitalWrite(GPIO7, HIGH) = relay energized = PUMP ON. Keep the inverter.", 118, 98)
text("J5 wiring: J5.1 (+5V) -> relay module COM screw. Relay NO screw -> J5.2.", 118, 102)
text("Pump then connects at J3 (1 = +, 2 = GND).", 118, 104)
text("SOIL SENSOR: J4 supplies 3.3V ONLY. GPIO0 = ADC1, WiFi-safe.", 40, 96)
text("PIN MAP: WHITE=GPIO6  PUMP=GPIO7  GROW=GPIO10  SOIL=GPIO0", 40, 98)
text("K1 socket order: 1=VCC 2=GND 3=IN 4=spare. VERIFY against your module!", 40, 100)

# ---------------------------------------------------------------- assemble
body = "\n".join(S)
libsec = "\n".join(lib_texts.values())
doc = '''(kicad_sch
  (version 20231120)
  (generator "gen_sch")
  (uuid "%s")
  (paper "A3")
  (title_block (title "Plant Hub") (date "2026-07-13") (rev "1.0")
    (comment 1 "ESP32-C3 SuperMini plant watering controller"))
  (lib_symbols
%s
  )
%s
  (sheet_instances (path "/" (page "1")))
)
''' % (ROOT, libsec, body)

OUT.write_text(doc)
print("wrote", OUT)
print("symbols:", len(ORIGINS), "| power symbols:", pwr_count[0])
