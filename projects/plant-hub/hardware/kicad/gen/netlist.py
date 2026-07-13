"""plant-hub-v1.0 — single source of truth netlist.

Both gen_sch.py (schematic) and gen_pcb.py (board) import this file,
so the schematic and PCB cannot disagree about connectivity.

Target MCU: ESP32-C3 Super Mini (16-pin, two 1x8 rows @ 2.54mm, rows 15.24mm apart)
Pin map (module viewed from top, USB-C at top) — verified against real board photos
2026-07-13 (power column is on the RIGHT with USB up):
  Left  row (pads 1-8,  top->bottom):  GPIO5 GPIO6 GPIO7 GPIO8 GPIO9 GPIO10 GPIO20 GPIO21
  Right row (pads 9-16, top->bottom):  5V  GND  3V3  GPIO4 GPIO3 GPIO2 GPIO1 GPIO0
Firmware pins: WHITE=GPIO6, PUMP=GPIO7 (HIGH = pump ON, 2N7000 inverts),
               GROW=GPIO10, SOIL=GPIO0 (ADC1 - WiFi safe)
"""

PROJECT = "plant-hub-v1.0"

# net name -> list of (ref, pad_number)
NETS = {
    "+5V": [("J1", "1"), ("C1", "1"), ("C2", "1"), ("U1", "9"),
            ("J2", "1"), ("K1", "1"), ("J5", "1"), ("R6", "1")],
    "GND": [("J1", "2"), ("C1", "2"), ("C2", "2"), ("C3", "2"),
            ("U1", "10"), ("R2", "2"), ("R4", "2"), ("R7", "2"),
            ("Q1", "3"), ("Q2", "3"), ("Q3", "1"),
            ("K1", "2"), ("J3", "2"), ("J4", "2"), ("D1", "1")],
    "+3V3": [("U1", "11"), ("C3", "1"), ("J4", "1")],
    "CTRL_WHITE": [("U1", "2"), ("R1", "1")],    # GPIO6
    "G_WHITE":    [("R1", "2"), ("R2", "1"), ("Q1", "1")],
    "LED_WHITE":  [("Q1", "2"), ("J2", "2")],
    "CTRL_GROW":  [("U1", "6"), ("R3", "1")],    # GPIO10
    "G_GROW":     [("R3", "2"), ("R4", "1"), ("Q2", "1")],
    "LED_GROW":   [("Q2", "2"), ("J2", "3")],
    "CTRL_PUMP":  [("U1", "3"), ("R5", "1")],    # GPIO7
    "G_PUMP":     [("R5", "2"), ("R7", "1"), ("Q3", "2")],
    "RELAY_IN":   [("Q3", "3"), ("K1", "3")],
    "PUMP_SW":    [("J5", "2"), ("J3", "1")],
    "SOIL_ADC":   [("J4", "3"), ("U1", "16")],   # GPIO0
    "PWR_LED":    [("R6", "2"), ("D1", "2")],
}

# ref -> dict(symbol, value, footprint, desc, mpn)
COMPONENTS = {
    "U1": dict(symbol="plant:ESP32-C3-SuperMini", value="ESP32-C3 SuperMini",
               footprint="plant:ESP32-C3-SuperMini-Socket",
               desc="ESP32-C3 Super Mini dev board on 2x 1x8 female headers",
               mpn="ESP32-C3 Super Mini + 2x female header 1x8 2.54mm"),
    "Q1": dict(symbol="Transistor_FET:IRLIZ44N", value="RFP30N06LE",
               footprint="Package_TO_SOT_THT:TO-220-3_Vertical",
               desc="White LED low-side switch, logic-level NMOS", mpn="RFP30N06LE"),
    "Q2": dict(symbol="Transistor_FET:IRLIZ44N", value="RFP30N06LE",
               footprint="Package_TO_SOT_THT:TO-220-3_Vertical",
               desc="Grow LED low-side switch, logic-level NMOS", mpn="RFP30N06LE"),
    "Q3": dict(symbol="Transistor_FET:2N7000", value="2N7000",
               footprint="Package_TO_SOT_THT:TO-92_Inline",
               desc="Relay-IN inverter (HIGH on GPIO7 = pump ON)", mpn="2N7000"),
    "K1": dict(symbol="Connector_Generic:Conn_01x04", value="RELAY_MODULE",
               footprint="Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
               desc="Socket for 5V relay module JQC-3FF-S-Z (VCC/GND/IN/NC)",
               mpn="1x4 female header 2.54mm"),
    "R1": dict(symbol="Device:R", value="220",
               footprint="Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
               desc="Q1 gate series", mpn="0805 220R 1%"),
    "R3": dict(symbol="Device:R", value="220",
               footprint="Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
               desc="Q2 gate series", mpn="0805 220R 1%"),
    "R2": dict(symbol="Device:R", value="10k",
               footprint="Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
               desc="Q1 gate pulldown - MANDATORY (boot flicker)", mpn="0805 10k 1%"),
    "R4": dict(symbol="Device:R", value="10k",
               footprint="Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
               desc="Q2 gate pulldown - MANDATORY (boot flicker)", mpn="0805 10k 1%"),
    "R5": dict(symbol="Device:R", value="1k",
               footprint="Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
               desc="Q3 gate series", mpn="0805 1k 1%"),
    "R7": dict(symbol="Device:R", value="10k",
               footprint="Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
               desc="Q3 gate pulldown - keeps pump off during boot", mpn="0805 10k 1%"),
    "R6": dict(symbol="Device:R", value="1k",
               footprint="Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
               desc="Power LED series", mpn="0805 1k 1%"),
    "C1": dict(symbol="Device:C_Polarized", value="470u",
               footprint="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
               desc="Bulk input cap (16V preferred, 10V acceptable)",
               mpn="470uF 16V radial D8 P3.5"),
    "C2": dict(symbol="Device:C", value="100n",
               footprint="Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
               desc="5V decoupling at U1", mpn="0805 100nF X7R"),
    "C3": dict(symbol="Device:C", value="100n",
               footprint="Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
               desc="3V3 decoupling at U1", mpn="0805 100nF X7R"),
    "D1": dict(symbol="Device:LED", value="GREEN",
               footprint="LED_THT:LED_D3.0mm",
               desc="Power indicator", mpn="LED 3mm green"),
    "J1": dict(symbol="Connector:Screw_Terminal_01x02", value="5V_IN",
               footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
               desc="5V power input (1=+5V, 2=GND)", mpn="Screw terminal 2-pos 5.08mm"),
    "J2": dict(symbol="Connector:Screw_Terminal_01x03", value="LED_OUT",
               footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
               desc="LED strips (1=+5V common, 2=WHITE-, 3=GROW-)", mpn="Screw terminal 3-pos 3.5mm"),
    "J3": dict(symbol="Connector:Screw_Terminal_01x02", value="PUMP",
               footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal",
               desc="Pump (1=switched +5V from relay NO, 2=GND)", mpn="Screw terminal 2-pos 3.5mm"),
    "J5": dict(symbol="Connector:Screw_Terminal_01x02", value="RLY_CONTACT",
               footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal",
               desc="Jumpers to relay module contacts (1=+5V->COM, 2=NO return)",
               mpn="Screw terminal 2-pos 3.5mm"),
    "J4": dict(symbol="Connector_Generic:Conn_01x03", value="SOIL",
               footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
               desc="Soil sensor (1=3V3, 2=GND, 3=AOUT)", mpn="Pin header 1x3 2.54mm"),
}

# pads with no net (mechanically present, electrically unused)
NO_CONNECTS = [("K1", "4"),  # relay module 4th pin
               ("U1", "1"), ("U1", "4"), ("U1", "5"),    # GPIO5, GPIO8, GPIO9
               ("U1", "7"), ("U1", "8"),                 # GPIO20, GPIO21
               ("U1", "12"), ("U1", "13"), ("U1", "14"), ("U1", "15")]  # GPIO4..1


def net_of(ref, pad):
    for net, pins in NETS.items():
        if (ref, pad) in pins:
            return net
    return None
