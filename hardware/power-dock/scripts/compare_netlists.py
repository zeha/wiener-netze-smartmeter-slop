"""Compare schematic netlist (kicadsexpr) with the nets on the board pads."""
import re
import sys

import pcbnew

sch_file, pcb_file = sys.argv[1:3]
text = open(sch_file).read()
sch = {}
for chunk in re.split(r"\(net\s*\(code", text[text.index("(nets"):])[1:]:
    name = re.search(r'\(name "([^"]*)"\)', chunk).group(1)
    for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', chunk):
        sch[(ref, pin)] = name
board = pcbnew.LoadBoard(pcb_file)
pcb = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNumber():
            pcb[(fp.GetReference(), pad.GetNumber())] = pad.GetNetname()
bad = [(k, sch.get(k), pcb.get(k)) for k in sorted(set(sch) | set(pcb)) if sch.get(k) != pcb.get(k)]
print(f"{len(sch)} schematic pins, {len(pcb)} board pads, {len(set(sch.values()))} nets, {len(bad)} mismatches")
for b in bad:
    print(" ", b)
sys.exit(1 if bad else 0)
