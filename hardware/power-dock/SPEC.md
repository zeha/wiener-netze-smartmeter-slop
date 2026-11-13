# Power dock board — design specification v1 (2026-11-09)

Two-layer add-on board for JLCPCB (target ~32 x 26 mm, JLC standard 0.2 mm
min) that charges the Olimex 7000 mAh LiPo cell and carries the battery
voltage divider + IR-head power gate for the WEMOS S2-Mini.

The S2-Mini is **not** on this board. It daisy-chains to header P1 with six
jumper wires; its on-board ME6211C33 LDO (fed from the 5V/VBUS header pin by
the battery) provides the 3.3 V rail the dock's small logic uses.

Vault context (read for background, not needed to build):
- decision: `projects/wiener-netze-smartmeter/decisions/s2-mini-ldo-with-tp4056-power-dock`
- research: `projects/wiener-netze-smartmeter/research/hardware-wemos-s2-mini-and-lipo-battery`
- TP4056 datasheet (local copy): `/opt/data/cache/scratch/tp4056_datasheet.pdf`

## BOM (LCSC numbers verified in stock 2026-11-09)

| Ref | Qty | MPN | Manufacturer | LCSC | Package | Function |
|-----|-----|-----|--------------|------|---------|----------|
| U1  | 1   | TP4056 | UMW (Youtai) | C725790 | ESOP-8 (SOIC-8 3.9x4.9 P1.27) | 1 A Li charger, 4.2 V |
| U2  | 1   | AO3401 | TWGMC | C727156 | SOT-23 (1=G 2=S 3=D) | P-MOS gate for IR head power |
| J1  | 1   | TYPE-C16PIN | SHOU HAN | C393939 | SMD USB-C (JLC footprint) | USB input |
| J2  | 1   | S2B-PH-K-S-GW | JST | C157932 | JST-PH 2.0 mm, right-angle | Battery input, pin 1 = + |
| J3  | 1   | S2B-PH-K-S-GW | JST | C157932 | JST-PH 2.0 mm, right-angle | Optional second battery, pin 1 = + (parallel) |
| F1  | 1   | SMD0805-100C-6V | BNstar | C22472456 | 0805 | PTC resettable fuse 1 A on BAT+ |
| F2  | 1   | SMD0805-100C-6V | BNstar | C22472456 | 0805 | PTC resettable fuse 1 A on BAT2RAW (optional) |
| R1  | 1   | RC0603JR-075K1L | YAGEO | C14677 | 0603 | 5.1 k USB-C CC pulldown (UFP Rd) |
| R2  | 1   | RC0603JR-072K4L | YAGEO | C127450 | 0603 | 2.4 k RPROG = 500 mA charge current |
| R3  | 1   | RC0603JR-071KL | YAGEO | C14676 | 0603 | 1 k charge-LED current |
| R4  | 1   | RC0603JR-0710KL | YAGEO | C99198 | 0603 | 10 k MOSFET gate pull-up (default off) |
| R5  | 1   | RC0603JR-071ML | YAGEO | C107698 | 0603 | 1 M divider top |
| R6  | 1   | RC0603JR-071ML | YAGEO | C107698 | 0603 | 1 M divider bottom |
| C1  | 1   | 0603X106M160NT | FH | C108340 | 0603 | 10 uF 16 V on BAT+ |
| C2  | 1   | 0603X106M160NT | FH | C108340 | 0603 | 10 uF 16 V on USB VBUS (TP4056 VCC) |
| D1  | 1   | YLED0603R | YONGYUTAI | C19171390 | 0603 | red LED, charge indicator |
| P1  | 1   | 2.54-1*6 | ZHOURI | C5156615 | 1x6 2.54 mm THT | dock header to S2-Mini |
| P2  | 1   | 2.54-1*4 | ZHOURI | C5116483 | 1x4 2.54 mm THT | Hichi IR head connector |

19 footprint placements, 16 unique parts (J3 uses J2's part, F2 uses F1's part).

## Net list (complete)

- **GND** — TP4056 pin 3 (GND), TP4056 pin 1 (TEMP, tied to GND: disables NTC
  temp monitoring, datasheet section 11), R1 other end, R2 other end, R6 other
  end, C1 other end, C2 other end, all USB-C S1 shell pads, J2 pin 2, P1 pin 2,
  P2 pin 2.
- **VBUS** — USB-C pads A12B1 and B9A4, C2, TP4056 pin 4 (VCC, 4-6.5 V OK),
  TP4056 pin 8 (CE, must be high to enable charging, datasheet section 11).
- **CC** — USB-C pad A9B4 (CC1+CC2 merged in the JLC footprint) to R1 to GND.
- **BAT+RAW** — J2 pin 1 to F1 (PTC).
- **BAT2RAW** — J3 pin 1 to F2 (PTC, 1 A). Present only if J3/F2 are
  populated; with J3 empty the net carries nothing.
- **BAT+** — F1 other end, F2 other end, C1, TP4056 pin 5 (BAT), R5 (divider
  top), P1 pin 1 (VBUS out to S2-Mini 5V/VBUS pin).
- **BATMID** — R5/R6 junction, P1 pin 3.
- **CHRG_LED** — TP4056 pin 7 (CHRG, open-drain, low while charging) to R3 to
  D1 anode.
- **VCC_3V3** — from P1 pin 4 (S2-Mini 3V3 out). D1 cathode, R4 (gate
  pull-up), U2 pin 2 (source).
- **IR_EN** — P1 pin 5, U2 gate (pin 1). Driven low by S2 GPIO5 to turn the
  head on; pulled high by R4 = off by default.
- **IR_PWR** — U2 pin 3 (drain), P2 pin 1.
- **HICH_TX** — P2 pin 3 (the Hichi head's data output, yellow wire), P1 pin 6
  (to S2-Mini IO11 = UART RX, internal pull-up enabled in the config).
- **NC** — TP4056 pin 6 (STDBY), P2 pin 4 (TX spare), USB-C data pads
  A5-A8, B5-B8.

## TP4056 (ESOP-8) pin assignments

1 TEMP -> GND | 2 PROG -> R2 (2.4 k) -> GND | 3 GND -> GND |
4 VCC -> VBUS | 5 BAT -> BAT+ | 6 STDBY -> NC |
7 CHRG -> R3 -> D1 -> VCC_3V3 | 8 CE -> VBUS

Charge current: RPROG = 2.4 k -> 500 mA (datasheet table, well below the
battery's 1.4 A recommended). Termination at C/10 = 50 mA.

## Battery voltage readout

BAT+ -> R5 (1 M) -> BATMID -> R6 (1 M) -> GND; BATMID -> P1 pin 3 ->
S2-Mini IO3 (ADC1_CH0). 1 M/1 M keeps divider current under 4 uA.
ADC1 full scale 3.3 V, so BATMID spans 1.5-2.1 V for a 3.0-4.2 V cell.
The ESPHome side (already implemented, job 20261108-172121-3e7ab0) applies the
x2 factor and a battery_level lookup.

## JST connector (J2)

Olimex 7000 mAh pack: 1S 3.7 V, 2-pin JST-PH 2.0 mm, unmarked plug, red wire
= + = pin 1. Mating socket S2B-PH-K-S (right-angle, cable exits the board
edge). Right-angle orientation so the cable leaves the bottom edge of the
board. JLC part C157932.

### J3 — optional second battery (same type, in parallel)

J3 is a second, identical JST-PH socket right next to J2 (silkscreen
"BATT2", +/− marks, own 1 A PTC fuse F2 on BAT2RAW). The second battery is
the same Olimex 7000 mAh 1S pack; plugging it in parallels the two packs
(~14 Ah) and doubles the runtime. The TP4056 keeps charging at the same 500 mA
total, so full-charge time with two packs doubles; the voltage divider and
ADC readout are unaffected (same BAT+ net). Optional by design: J3 and F2 may
be left unpopulated — mark the footprints DNP in KiCad so DRC ignores their
pads — and the board works as the single-battery dock. Same wiring
convention: red wire = + = pin 1.

## Headers

- **P1 (1x6, THT, pin 1 marked)**: 1 = VBUS (BAT+), 2 = GND, 3 = BATMID
  (IO3), 4 = 3V3, 5 = IR_EN (IO5), 6 = UARTRX (IO11).
- **P2 (1x4, THT, pin 1 marked)**: 1 = IR_PWR (gated 3V3), 2 = GND,
  3 = HICH_TX (the head's data output, yellow wire), 4 = spare (NC).

Jumpers to the S2-Mini 2x16 header (verified against WEMOS schematic
v1.0.0): P1.1->5V/VBUS, P1.2->GND, P1.3->IO3, P1.4->3V3, P1.5->IO5,
P1.6->IO11.

## Layout constraints

- Board outline ~32 x 26 mm, rounded corners OK.
- J1 USB-C at the top edge, mounted per the JLC footprint (front/F.Cu side,
  cable enters from the top). Its shell screw holes and the two 0.6 mm
  np-thru-hole mount holes must keep >= 1 mm from the board edge.
- J2 JST at the bottom edge, cable exits downward; pin 1 to the right.
- J3 JST (optional 2nd battery) next to J2, same orientation; its top
  silkscreen edge is trimmed 0.3 mm shorter than the library footprint to keep
  >= 0.2 mm from the board edge (hence one DRC warning: J3 footprint differs
  from its library copy — intentional local modification).
- P1 at the top right (vertical, 90 deg), P2 at the bottom right (vertical),
  Hichi cable exits to the right/bottom-right.
- U1 TP4056 mid-left; U2 AO3401 between U1 and P1/P2; passives around U1/U2.
- All SMD parts on F.Cu unless routing forces otherwise; headers/JST/PTC are
  through-hole or SMD per their footprints (F1 is SMD 0805).
- GND copper pour on both layers, 0.2 mm clearance, connected to GND.
- Track widths: BAT+ and VBUS >= 0.4 mm, everything else >= 0.25 mm.
- Clearance >= 0.15 mm, copper-to-copper >= 0.2 mm, board edge >= 0.2 mm to
  SMD pads.
- No courtyard overlaps (DRC must be clean).
- Silkscreen: reference designators + values on all parts, pin-1 marks on
  headers/JST/TP4056, a small "PWR DOCK" label, keep silkscreen off pads.

## Files to produce (in this directory)

- `power-dock.kicad_pro`
- `power-dock.kicad_sch` + `power-dock.kicad_sym` (local symbols for TP4056,
  AO3401, USB-C 16-pin; use official library symbols for R/C/D/headers/power)
- `power-dock.kicad_pcb`
- `footprints/TYPE-C-SMD_HX-TYPE-C-16PIN.kicad_mod` (copy from
  `/opt/data/cache/scratch/jlcmods/`; all other footprints reference the
  official KiCad 10 libraries listed in the build brief)
- `BOM.csv` — columns: `Reference,Qty,Value,Package,LCSC,MPN,Manufacturer`
- `README.md` — assembly notes: JLC assembly order with this BOM, JST pin 1 =
  red = +, jumper wire map (P1 -> S2-Mini), charge-LED behavior, how to read
  battery voltage (GPIO3 x2)
- `out/` — gerbers, drill, pos, board SVG (F.Cu + B.Cu), schematic PDF, 3D PNG

## Acceptance (all must pass)

KiCad CLI: `K=/opt/data/cache/kicad/AppDir/usr/bin/kicad-cli`

1. `$K sch erc power-dock.kicad_sch` -> 0 errors (warnings: fix or justify)
2. `$K pcb drc power-dock.kicad_pcb` -> 0 errors (1 expected warning: J3
   footprint locally modified, see Layout constraints)
3. Schematic netlist and board netlist agree on every net and every footprint
   (compare `$K sch export netlist` vs `$K pcb export` netlist, or manual diff)
4. `$K pcb export gerbers`, `drill`, `pos`, `svg` (F.Cu/B.Cu), `pdf` succeed
   into `out/`
5. `$K pcb render` 3D PNG into `out/`
6. `BOM.csv` matches the spec table exactly (16 unique parts)
7. Committed on branch `hermes/power-dock-pcb` with a message per the repo's
   AGENTS.md commit convention

## Environment

- KiCad 10.0.8 AppImage at `/opt/data/cache/kicad/AppDir`
  (`usr/bin/kicad-cli`, official libraries under `share/kicad/`).
- Official footprints needed (all exist, verified 2026-11-09):
  - `Resistor_SMD.pretty/R_0603_1608Metric.kicad_mod` (R1-R6)
  - `Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod` (F1)
  - `Capacitor_SMD.pretty/C_0603_1608Metric.kicad_mod` (C1, C2)
  - `LED_SMD.pretty/LED_0603_1608Metric.kicad_mod` (D1)
  - `Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod` (U2, pad 1=G 2=S 3=D)
  - `Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod` (U1)
  - `Connector_JST.pretty/JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal.kicad_mod`
    (J2; pad 1 at (0,0), pad 2 at (2,0) in the footprint's local frame)
  - `Connector_PinHeader_2.54mm.pretty/PinHeader_1x04_P2.54mm_Vertical.kicad_mod` (P2)
  - `Connector_PinHeader_2.54mm.pretty/PinHeader_1x06_P2.54mm_Vertical.kicad_mod` (P1)
- Python 3.14.9 venv for any generator scripts:
  `/opt/data/repos/wiener-netze-smartmeter/.venv/bin/python3.14`
- Repo: `/opt/data/repos/wiener-netze-smartmeter` (work on branch
  `hermes/power-dock-pcb` created from `main`; do not touch firmware code).
