# hardware/power-dock: agent notes

- Generated files: `power-dock.kicad_sch`, `.kicad_sym` and `.kicad_pcb`
  come from `scripts/build.py`. Change the script, then run `scripts/run.sh`.
  The script needs KiCad's bundled Python for `pcbnew`. `run.sh` sets
  PYTHONPATH and LD_LIBRARY_PATH for the AppImage at /opt/data/cache/kicad/AppDir.
- Run DRC with `--refill-zones --save-board`. The script fills zones, but this
  keeps the saved board consistent. Add `--schematic-parity` for the netlist check.
- Schematic nets from local labels are named `/NAME` and the PCB nets must
  match. Pads of unconnected pins need eeschema's
  `unconnected-(REF-PIN-PadN)` net names, or parity reports net_conflict.
- Schematic coordinates must be on the 2.54 mm grid (endpoint_off_grid otherwise).
- JLC USB-C footprint pad names: `A12B1`/`B12A1` are GND, `A9B4`/`B9A4` are
  VBUS, CC is `A5`/`B5` (see README "Deviations").
