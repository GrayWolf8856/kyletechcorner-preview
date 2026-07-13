#!/usr/bin/env python3
"""Generate plant-hub-v1.0.kicad_pcb from netlist.py using the pcbnew API.

Board: 85 x 60 mm, 2 layers, GND pour on both, M3 holes in corners.
Run with KiCad's bundled python:
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
import sys
from pathlib import Path

import wx  # noqa: F401  (wx.App must exist before pcbnew zone fill on macOS)
_APP = wx.App()

sys.path.insert(0, str(Path(__file__).resolve().parent))
import netlist as NL  # noqa: E402
import pcbnew  # noqa: E402
from pcbnew import FromMM, VECTOR2I  # noqa: E402

PRJ = Path(__file__).resolve().parent.parent
OUT = PRJ / "plant-hub-v1.0.kicad_pcb"
FPDIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
OX, OY = 100.0, 100.0          # board origin on sheet
W, H = 85.0, 60.0

board = pcbnew.CreateEmptyBoard()


def P(x, y):
    return VECTOR2I(FromMM(OX + x), FromMM(OY + y))


# ---- nets -------------------------------------------------------------------
nets = {}
for name in NL.NETS:
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    nets[name] = ni

# ---- footprints -------------------------------------------------------------
FPS = {}


def load(ref):
    lib, name = NL.COMPONENTS[ref]["footprint"].split(":")
    path = str(PRJ / "plant.pretty") if lib == "plant" else "%s/%s.pretty" % (FPDIR, lib)
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit("footprint not found: %s:%s" % (lib, name))
    fp.SetReference(ref)
    fp.SetValue(NL.COMPONENTS[ref]["value"])
    board.Add(fp)
    FPS[ref] = fp
    return fp


PLACE = {
    #  ref: (x, y, rot)
    "J1": (6, 24, 270),
    "C1": (16, 26, 270),
    "D1": (5, 14, 0),
    "R6": (10.5, 18, 90),
    "J4": (6, 40, 0),
    "U1": (38, 26, 0),
    "C2": (48, 12.5, 0),
    "C3": (49.5, 22.19, 0),
    "R7": (52.5, 41, 0),
    "Q1": (58, 12, 0),
    "R1": (50, 15, 0),
    "R2": (54, 15, 0),
    "Q2": (58, 26, 0),
    "R3": (50, 29, 0),
    "R4": (54, 29, 0),
    "J2": (80.5, 16, 270),
    "Q3": (46, 44, 0),
    "R5": (50, 38, 270),
    "K1": (58, 47, 90),
    "J5": (80.5, 40, 270),
    "J3": (72, 56, 180),
}

for ref in NL.COMPONENTS:
    load(ref)
    x, y, rot = PLACE[ref]
    FPS[ref].SetPosition(P(x, y))
    FPS[ref].SetOrientationDegrees(rot)

# assign nets to pads
for net, pins in NL.NETS.items():
    for ref, num in pins:
        pad = FPS[ref].FindPadByNumber(num)
        if pad is None:
            raise SystemExit("pad %s-%s missing" % (ref, num))
        pad.SetNetCode(nets[net].GetNetCode())

# mounting holes
for i, (x, y) in enumerate(((4, 4), (81, 4), (4, 56), (81, 56)), 1):
    fp = pcbnew.FootprintLoad(FPDIR + "/MountingHole.pretty",
                              "MountingHole_3.2mm_M3_Pad_Via")
    fp.SetReference("H%d" % i)
    fp.SetValue("M3")
    fp.Reference().SetVisible(False)
    board.Add(fp)
    fp.SetPosition(P(x, y))
    for pad in fp.Pads():
        pad.SetNetCode(nets["GND"].GetNetCode())

# report actual pad coordinates (for route sanity)
def pad_xy(ref, num):
    p = FPS[ref].FindPadByNumber(num).GetPosition()
    return (pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY)


for ref in sorted(PLACE):
    fp = FPS[ref]
    coords = ", ".join("%s:(%.2f,%.2f)" % ((pad.GetNumber(),) + tuple(
        (pcbnew.ToMM(pad.GetPosition().x) - OX, pcbnew.ToMM(pad.GetPosition().y) - OY)))
        for pad in fp.Pads())
    print(ref, coords)

print("STAGE: outline", flush=True)
# ---- board outline ----------------------------------------------------------
rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(P(0, 0))
rect.SetEnd(P(W, H))
rect.SetLayer(pcbnew.Edge_Cuts)
rect.SetWidth(FromMM(0.1))
board.Add(rect)

print("STAGE: tracks", flush=True)
# ---- tracks -----------------------------------------------------------------
def track(net, pts, w=0.25, layer=pcbnew.F_Cu):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(*a))
        t.SetEnd(P(*b))
        t.SetWidth(FromMM(w))
        t.SetLayer(layer)
        t.SetNetCode(nets[net].GetNetCode())
        board.Add(t)


def via(net, x, y, dia=0.8, drill=0.4):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetDrill(FromMM(drill))
    v.SetWidth(FromMM(dia))
    v.SetNetCode(nets[net].GetNetCode())
    board.Add(v)


PW = 1.0   # power width
# +5V spine: J1.1 -> C1.1 -> vertical -> south rail; branches
track("+5V", [pad_xy("J1", "1"), (14, 24), (22, 24)], PW)
track("+5V", [(16, 24), pad_xy("C1", "1")], PW)
track("+5V", [(22, 52), (22, 8)], PW)                         # west vertical
track("+5V", [(22, 52), (76, 52)], PW)                        # south rail
track("+5V", [(58, 52), pad_xy("K1", "1")], PW)               # relay VCC
track("+5V", [(76, 52), (76, 40), pad_xy("J5", "1")], PW)     # relay COM feed
track("+5V", [(22, 8), (79, 8), (79, 16), pad_xy("J2", "1")], PW)  # LED common
track("+5V", [(45.62, 8), pad_xy("U1", "9")], PW)             # drop to module 5V
track("+5V", [(45.62, 12.5), pad_xy("C2", "1")], 0.5)         # C2 stub
track("+5V", [(10.5, 24), pad_xy("R6", "1")], 0.5)            # power LED feed

# power LED
track("PWR_LED", [pad_xy("R6", "2"), (10.5, 14), pad_xy("D1", "2")], 0.25)

# 3V3: J4.1 -> U1 pin3, bottom layer (both ends THT)
track("+3V3", [pad_xy("J4", "1"), (20, 31.5), (26, 28.54), (34, 28.54),
               (42, 23.5), pad_xy("U1", "11")], 0.3, pcbnew.B_Cu)
track("+3V3", [pad_xy("U1", "11"), pad_xy("C3", "1")], 0.4)  # C3 stub, top

# soil analog: J4.3 -> U1 pin8 (GPIO0), bottom layer, short diagonal
track("SOIL_ADC", [pad_xy("J4", "3"), (26, 36.7), pad_xy("U1", "16")], 0.25, pcbnew.B_Cu)

# LED channel white: GPIO6 -> R1 -> gate node (R2 pulldown) -> Q1
track("CTRL_WHITE", [pad_xy("U1", "2"), (43.5, 18.38), (47.3, 18.38), pad_xy("R1", "1")])
track("G_WHITE", [pad_xy("R1", "2"), pad_xy("R2", "1")])
track("G_WHITE", [(52, 15), (52, 12), pad_xy("Q1", "1")])
track("LED_WHITE", [pad_xy("Q1", "2"), (60.54, 9.7), (68, 9.7), (74, 15), (74, 19.5), pad_xy("J2", "2")], PW)

# LED channel grow: GPIO10 -> R3 -> gate node (R4 pulldown) -> Q2
track("CTRL_GROW", [pad_xy("U1", "6"), (43, 28.54), (47.8, 28.54), pad_xy("R3", "1")])
track("G_GROW", [pad_xy("R3", "2"), pad_xy("R4", "1")])
track("G_GROW", [(52, 29), (52, 26), pad_xy("Q2", "1")])
track("LED_GROW", [pad_xy("Q2", "2"), (60.54, 22.8), (66, 22.8), pad_xy("J2", "3")], PW)

# pump: GPIO7 -> R5 -> Q3 gate; Q3 drain -> relay IN; contact loop J5.2 -> J3.1
track("CTRL_PUMP", [pad_xy("U1", "3"), (43, 23.46), (47, 23.46), (50, 25.5),
                    pad_xy("R5", "1")])
track("G_PUMP", [pad_xy("R5", "2"), (50, 41), (47.27, 42.8), pad_xy("Q3", "2")])
track("G_PUMP", [(50, 41), pad_xy("R7", "1")])
track("RELAY_IN", [pad_xy("Q3", "3"), (51.08, 44.4), (61.5, 44.4), pad_xy("K1", "3")], 0.5)
track("PUMP_SW", [pad_xy("J5", "2"), (80.5, 50), (77, 53), pad_xy("J3", "1")], PW)

# GND stitching vias (pours on both layers do the conduction)
for x, y in ((63.08, 14.5), (65, 28.5), (44, 46.5), (10, 10), (74, 11),
             (10, 54), (40, 55), (60, 57.5), (25.5, 41), (36, 45), (36, 25.5), (36, 20.9), (47.5, 26.8), (38, 31), (20, 35), (48.96, 10.8)):
    via("GND", x, y)

print("STAGE: zones", flush=True)
# ---- GND zones on both layers ----------------------------------------------
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(nets["GND"].GetNetCode())
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((0, 0), (W, 0), (W, H), (0, H)):
        ol.Append(FromMM(OX + x), FromMM(OY + y))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(FromMM(0.4))
    z.SetThermalReliefSpokeWidth(FromMM(0.5))
    z.SetMinThickness(FromMM(0.25))
    try:
        z.SetLocalClearance(FromMM(0.3))
    except Exception:
        pass
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_AREA)
    z.SetMinIslandArea(int(5e12))   # drop orphan slivers under 5 mm^2
    z.SetAssignedPriority(0)
    board.Add(z)

print("STAGE: silk", flush=True)
# ---- silkscreen labels ------------------------------------------------------
def silk(txt, x, y, size=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
    t.SetTextThickness(FromMM(0.15 if size >= 1 else 0.12))
    board.Add(t)


silk("PLANT HUB v1.0", 42.5, 2.8, 1.5)
silk("5V IN", 14.2, 22.2, 0.9)
silk("+", 2.8, 24, 1.2)
silk("-", 2.8, 29.1, 1.2)
silk("PWR", 5.2, 16.4, 0.8)
silk("3V3", 9, 40, 0.8)
silk("GND", 9, 42.54, 0.8)
silk("SIG", 9, 45.08, 0.8)
silk("+5", 77.6, 16, 0.9)
silk("W", 77.6, 19.5, 0.9)
silk("G", 77.6, 23, 0.9)
silk("LED", 77.5, 12.8, 0.9)
silk("V", 58, 49.6, 0.8)
silk("G", 60.54, 49.6, 0.8)
silk("IN", 63.08, 49.6, 0.8)
silk("-", 65.62, 49.6, 0.8)
silk("RELAY MODULE", 61.8, 43.4, 0.9)
silk("COM", 77.2, 40, 0.9)
silk("NO", 77.5, 43.5, 0.9)
silk("PUMP", 70.2, 53.6, 0.9)
silk("+", 72, 54.6, 0.9)
silk("-", 68.5, 54.6, 0.9)
silk("IO6=WHITE IO7=PUMP IO10=GROW IO0=SOIL", 38, 58.5, 1.0)

# ---- fill zones, save -------------------------------------------------------
# keep reference designators on-board and clear of pads
REFPOS = {"J1": (6, 20.2), "J2": (80.5, 26.4), "J3": (74.5, 52.6),
          "J4": (6, 36.4), "J5": (80.5, 37.2), "K1": (54, 47),
          "C1": (16, 20.8), "D1": (5, 11.4), "U1": (38, 13.2)}
for r, (rx, ry) in REFPOS.items():
    FPS[r].Reference().SetPosition(P(rx, ry))

print("STAGE: save-unfilled", flush=True)
pcbnew.SaveBoard(str(OUT), board)
print("wrote", OUT)
