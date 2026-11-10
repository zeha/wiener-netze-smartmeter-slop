# Power dock v1

Two-layer 32 x 28 mm add-on board: TP4056 charger for the Olimex 7000 mAh LiPo,
1 M / 1 M battery divider and an AO3401 high-side gate for the Hichi IR head.
The WEMOS S2-Mini is not on the board; it is wired to P1. Design brief: `SPEC.md`.

## Deviations from SPEC.md v1

- **USB-C pads.** The spec puts VBUS on `A12B1` + `B9A4` and CC on `A9B4`.
  In the JLC footprint `A12B1`/`B12A1` are the outer GND pins and
  `A9B4`/`B9A4` are VBUS, so following the spec would short VBUS to GND.
  The board uses VBUS = `A9B4` + `B9A4`, GND = `A12B1` + `B12A1` + shell,
  CC1 = `A5`, CC2 = `B5`.
- **Second CC resistor R7.** CC1 and CC2 are separate pads. Each one gets its
  own 5.1 k Rd (R1 on CC1, R7 on CC2). Without them a USB-C charger never
  turns VBUS on. That adds one row to `BOM.csv` (same part as R1, C14677).
- **Charge LED direction.** CHRG is open-drain and pulls low, so D1 anode goes to
  VCC_3V3 and the cathode goes through R3 to CHRG (net CHRG_LED between R3
  and D1). The spec's orientation would leave the LED reverse-biased.
- J2 sits at the bottom edge with the cable exiting downward. On the top side
  of the board this puts pin 1 (+) on the **left**, not the right.
- **Optional second battery (J3/F2, added 2026-11-10):** a second identical
  JST-PH socket next to J2 (silkscreen "BATT2") with its own 1 A PTC (F2),
  paralleling a second Olimex 7000 mAh pack for ~14 Ah / double runtime.
  Charging stays 500 mA total, so two packs take twice as long to full.
  J3 and F2 may be left unpopulated (mark them DNP in KiCad so DRC ignores
  the pads); the board then works as the single-battery dock.
- U1 uses the plain SOIC-8 footprint the spec lists, so the TP4056 exposed pad
  is not soldered. That is fine at 500 mA.
- Board is 28 mm tall, not 26 mm, so P1 and P2 fit stacked on the right edge.
- Project hole clearance is 0.2 mm (KiCad default 0.25 mm). The JLC USB-C
  footprint has 0.204 mm between its GND pads and the NPTH pegs.
- Part values show on the fab layer. The silkscreen carries references,
  pin-1 marks and "PWR DOCK".

## Assembly (JLCPCB)

Order with the gerber zip (`out/gerbers/`), `BOM.csv` and
`out/power-dock-pos.csv` (top side only). Check the USB-C, JST and LED
rotations in the JLC preview. The headers and JST are THT, so either use
JLC THT assembly or hand-solder them.

- **Battery J2:** Olimex pack red wire = + = pin 1 (marked on silkscreen).
  The plug is unmarked, so check polarity with a meter before plugging in.
- **Battery J3 (optional):** same pack type, wired the same way (red = + =
  pin 1, "BATT2" + polarity marks on silkscreen). Leave the socket and the
  F2 PTC unpopulated for the single-battery dock; populate both to run two
  packs in parallel (~14 Ah).
- **P1 to S2-Mini jumpers:** P1.1 -> 5V/VBUS, P1.2 -> GND, P1.3 -> IO3,
  P1.4 -> 3V3, P1.5 -> IO5, P1.6 -> IO21.
- **P2 Hichi IR head:** 1 = switched 3V3, 2 = GND, 3 = Hichi TX, 4 = not connected.
- **Charge LED D1:** lights while the TP4056 is charging and goes out when
  charging ends (C/10 = 50 mA) or with no USB. It runs from the S2-Mini 3V3
  rail, so it only lights while the S2-Mini is powered.
- **Charge current:** R2 = 2.4 k sets 500 mA.
- **Battery voltage:** GPIO3 (ADC1_CH0) reads BAT+/2 through R5/R6. Multiply
  by 2 (the ESPHome config already does this). A 3.0-4.2 V cell gives 1.5-2.1 V.
- **IR head gate:** GPIO5 low = head on. R4 holds the gate high, so the head
  is off by default.

## Regenerate and check

```sh
scripts/run.sh                       # writes .kicad_sch, .kicad_sym, .kicad_pcb
K=/opt/data/cache/kicad/AppDir/usr/bin/kicad-cli
$K sch erc power-dock.kicad_sch
$K pcb drc --schematic-parity --refill-zones --save-board power-dock.kicad_pcb
$K sch export netlist -o out/power-dock.sch.net power-dock.kicad_sch
SCRIPT=scripts/compare_netlists.py scripts/run.sh out/power-dock.sch.net power-dock.kicad_pcb
```

Edit placement and routing in `scripts/build.py` (`PLACE`, `ROUTES`, `VIAS`),
not in the generated files.
