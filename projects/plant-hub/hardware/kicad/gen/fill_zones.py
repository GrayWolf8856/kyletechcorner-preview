#!/usr/bin/env python3
"""Load the generated board, fill GND zones, save. Separate process because
ZONE_FILLER inside the generator segfaults on macOS."""
import wx
_APP = wx.App()
import pcbnew
from pathlib import Path
PRJ = Path(__file__).resolve().parent.parent
board = pcbnew.LoadBoard(str(PRJ / "plant-hub-v1.0.kicad_pcb"))
print("loaded, zones:", len(board.Zones()), flush=True)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
print("filled", flush=True)
pcbnew.SaveBoard(str(PRJ / "plant-hub-v1.0.kicad_pcb"), board)
print("saved", flush=True)
