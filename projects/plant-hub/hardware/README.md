# Plant Hub v1.0 — ESP32-C3 plant watering controller

85 × 60 mm, 2-layer PCB. Drives two 5V LED strip channels (MOSFET low-side),
one pump via a plug-in 5V relay module, and reads an analog soil-moisture
sensor. ESP32-C3 Super Mini is socketed and removable.

## Files

| Path | What |
|---|---|
| `kicad/plant-hub-v1.0.kicad_pro/.kicad_sch/.kicad_pcb` | KiCad 10 project (ERC + DRC clean) |
| `kicad/gen/` | Generators — `netlist.py` is the single source of truth; `gen_libs.py` builds the schematic + libs, `gen/build_pcb.sh` rebuilds the board |
| `manufacturing/plant-hub-v1.0.zip` | **Upload this to JLCPCB** (Gerbers + drill) |
| `manufacturing/plant-hub-v1.0-BOM.csv` | Bill of materials |
| `kicad/plant-hub-v1.0-schematic.pdf` | Printable schematic |
| `kicad/render-top.png`, `render-iso.png` | 3D previews |

## JLCPCB order settings

Defaults are fine. Specifically: 2 layers, 1.6 mm FR-4, 1 oz copper, HASL
(lead-free if offered at no cost), any solder mask color. Min track/space on
this board is 0.25 mm / 0.2 mm — far above their 6 mil (0.152 mm) capability.

## Firmware pin map (ESP32-C3 Super Mini)

| Function | GPIO | Notes |
|---|---|---|
| White LED channel | **6** | HIGH = on |
| Pump | **7** | **HIGH = pump ON** (2N7000 inverts; relay IN is active-low) |
| Grow LED channel | **10** | HIGH = on |
| Soil sensor ADC | **0** | ADC1 — safe to read while WiFi is on |

GPIO2/8/9 are strapping pins and are intentionally unused. Boot-time gate
pulldowns R2/R4 (LEDs) and R7 (pump) keep every output off during reset —
do not omit them.

## Wiring after assembly

- **J1 (5.08 mm)**: 5V PSU in. `+` and `−` marked on silk. The USB-C on the
  ESP32 can stay plugged in at the same time (the module has a protection
  diode), but USB alone cannot power LEDs/pump.
- **J2**: LED strips. `+5` = common +5V to both strips, `W` = white strip
  return (Q1 drain), `G` = grow strip return (Q2 drain).
- **K1 socket**: relay module plugs in here. Order: `V G IN −` (VCC, GND, IN,
  spare). **Verify against your module's silkscreen before plugging in.**
- **J5 → relay contacts**: two short jumper wires: `COM` screw on J5 → COM
  screw terminal on the relay module; `NO` screw on the module → `NO` screw
  on J5. This routes the switched 5V through the board.
- **J3**: pump. `+` = switched 5V (from relay NO via J5), `−` = GND.
- **J4**: soil sensor. `3V3 / GND / SIG` marked. Sensor is 3.3V-only — it is
  wired to the ESP32's 3V3 regulator, never 5V.

## Assembly notes (first-PCB gotchas)

1. **Order of soldering**: SMD resistors/caps first (R1–R6, C2, C3), then
   TO-92/TO-220, then through-hole caps/LED, then sockets and terminal blocks.
2. **C1 polarity**: longer leg = `+`, into the pad nearer the board top edge
   (silk `+`). Stripe on the can = negative side.
3. **D1 polarity**: flat spot / short leg = cathode = toward GND (silk shows outline).
4. **TO-220 (Q1/Q2)**: metal tab faces the top board edge; silk outline makes
   the orientation unambiguous. No heatsink needed at LED-strip currents.
5. **2N7000 (Q3)**: flat face orientation per silk. Pins are S-G-D.
6. **ESP32 socket**: solder the two 1×8 female headers, then plug the module
   in with **USB-C facing the top board edge** (silk says `USB`). With USB up,
   the module's power column (5V/G/3.3 printed on the module) is on the
   RIGHT — the board silk matches this exactly (verified against the standard
   Super Mini pinout). Still eyeball module-silk vs board-silk before first
   power-up; clones occasionally differ.
7. **Smoke test**: before plugging in U1 or the relay module, apply 5V at J1
   and check: D1 lights, 5V on the socket's 5V pin, 3.3V appears only after
   U1 is inserted (the 3V3 rail comes from the module's regulator).

## Design decisions

- Relay is a plug-in module (JQC-3FF-S-Z type) — it already carries the
  transistor, flyback diode and LED, so the board only provides the socket
  and the 2N7000 level/polarity inverter.
- Soil ADC trace runs on the bottom layer, short and straight, with ground
  pour on both layers around it, away from the MOSFET switching area.
- Ground: single GND net, pours on both layers, stitching vias near each
  MOSFET source and around the board.
- Grounded M3 mounting holes (pad+via ring) — metal standoffs tie the frame
  to GND.
