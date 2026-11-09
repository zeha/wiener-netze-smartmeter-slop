"""Generate power-dock schematic, symbol library and PCB.

Run with KiCad's bundled Python (needs the pcbnew module), see README.md.
"""
import math
import os
import re
import uuid

import pcbnew

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KISHARE = os.environ.get("KISHARE", "/opt/data/cache/kicad/AppDir/usr/share/kicad")
NAME = "power-dock"
ORIGIN = (100.0, 100.0)
BOARD_W, BOARD_H = 32.0, 28.0


def uid(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "power-dock/" + seed))


# --- parts: ref -> (lib_id, value, footprint, LCSC, MPN, manufacturer, {pin: net}) ---
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
PARTS = {
    "U1": ("power-dock:TP4056", "TP4056", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "C725790", "TP4056", "UMW (Youtai)",
           {"1": "GND", "2": "PROG", "3": "GND", "4": "VBUS", "5": "BAT+", "6": None, "7": "CHRG", "8": "VBUS"}),
    "U2": ("power-dock:AO3401", "AO3401", "Package_TO_SOT_SMD:SOT-23", "C727156", "AO3401", "TWGMC",
           {"1": "IR_EN", "2": "VCC_3V3", "3": "IR_PWR"}),
    "J1": ("power-dock:USB_C_16P", "TYPE-C16PIN", "power-dock:TYPE-C-SMD_HX-TYPE-C-16PIN", "C393939", "TYPE-C16PIN", "SHOU HAN",
           {"B12A1": "GND", "A12B1": "GND", "B9A4": "VBUS", "A9B4": "VBUS", "A5": "CC1", "B5": "CC2",
            "A6": None, "A7": None, "A8": None, "B6": None, "B7": None, "B8": None, "S1": "GND"}),
    "J2": ("Connector_Generic:Conn_01x02", "S2B-PH-K-S-GW", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", "C157932", "S2B-PH-K-S-GW", "JST",
           {"1": "BAT+RAW", "2": "GND"}),
    "F1": ("Device:Polyfuse", "1A PTC", "Resistor_SMD:R_0805_2012Metric", "C22472456", "SMD0805-100C-6V", "BNstar",
           {"1": "BAT+RAW", "2": "BAT+"}),
    "R1": ("Device:R", "5.1k", FP_R, "C14677", "RC0603JR-075K1L", "YAGEO", {"2": "CC1", "1": "GND"}),
    "R7": ("Device:R", "5.1k", FP_R, "C14677", "RC0603JR-075K1L", "YAGEO", {"2": "CC2", "1": "GND"}),
    "R2": ("Device:R", "2.4k", FP_R, "C127450", "RC0603JR-072K4L", "YAGEO", {"2": "PROG", "1": "GND"}),
    "R3": ("Device:R", "1k", FP_R, "C14676", "RC0603JR-071KL", "YAGEO", {"1": "CHRG", "2": "CHRG_LED"}),
    "R4": ("Device:R", "10k", FP_R, "C99198", "RC0603JR-0710KL", "YAGEO", {"2": "IR_EN", "1": "VCC_3V3"}),
    "R5": ("Device:R", "1M", FP_R, "C107698", "RC0603JR-071ML", "YAGEO", {"2": "BAT+", "1": "BATMID"}),
    "R6": ("Device:R", "1M", FP_R, "C107698", "RC0603JR-071ML", "YAGEO", {"2": "BATMID", "1": "GND"}),
    "C1": ("Device:C", "10uF 16V", FP_C, "C108340", "0603X106M160NT", "FH", {"2": "BAT+", "1": "GND"}),
    "C2": ("Device:C", "10uF 16V", FP_C, "C108340", "0603X106M160NT", "FH", {"2": "VBUS", "1": "GND"}),
    "D1": ("Device:LED", "red", "LED_SMD:LED_0603_1608Metric", "C19171390", "YLED0603R", "YONGYUTAI",
           {"1": "CHRG_LED", "2": "VCC_3V3"}),
    "P1": ("Connector_Generic:Conn_01x06", "S2-Mini dock", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "C5156615", "2.54-1*6", "ZHOURI",
           {"1": "BAT+", "2": "GND", "3": "BATMID", "4": "VCC_3V3", "5": "IR_EN", "6": "HICH_TX"}),
    "P2": ("Connector_Generic:Conn_01x04", "Hichi IR", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "C5116483", "2.54-1*4", "ZHOURI",
           {"1": "IR_PWR", "2": "GND", "3": "HICH_TX", "4": None}),
}


def pcb_net(net):
    return net if net == "GND" else "/" + net


# ---------------------------------------------------------------- symbols
def local_symbol(name, ref, value, pins, box, desc):
    """pins: list of (number, name, x, y, angle)."""
    out = [f'\t(symbol "{name}"', '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)']
    for i, (k, v, hide) in enumerate([("Reference", ref, False), ("Value", value, False),
                                      ("Footprint", "", True), ("Datasheet", "", True), ("Description", desc, True)]):
        y = box[1] + 1.27 if i == 0 else box[3] - 1.27
        y = -y if i < 2 else 0
        out.append(f'\t\t(property "{k}" "{v}" (at 0 {y if i < 2 else 0} 0) {"(hide yes) " if hide else ""}(effects (font (size 1.27 1.27))))')
    x0, y0, x1, y1 = box
    out.append(f'\t\t(symbol "{name}_0_1" (rectangle (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.254) (type default)) (fill (type background))))')
    out.append(f'\t\t(symbol "{name}_1_1"')
    for num, pname, x, y, a in pins:
        out.append(f'\t\t\t(pin passive line (at {x} {y} {a}) (length 2.54) (name "{pname}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    out.append('\t\t)\n\t)')
    return "\n".join(out)


def local_symbols():
    tp = [("1", "TEMP", -10.16, 3.81, 0), ("2", "PROG", -10.16, 1.27, 0), ("3", "GND", -10.16, -1.27, 0),
          ("4", "VCC", -10.16, -3.81, 0), ("5", "BAT", 10.16, -3.81, 180), ("6", "~{STDBY}", 10.16, -1.27, 180),
          ("7", "~{CHRG}", 10.16, 1.27, 180), ("8", "CE", 10.16, 3.81, 180)]
    ao = [("1", "G", -7.62, 0, 0), ("2", "S", 0, 7.62, 270), ("3", "D", 0, -7.62, 90)]
    usb_pins = [("B12A1", "GND"), ("A12B1", "GND"), ("B9A4", "VBUS"), ("A9B4", "VBUS"), ("A5", "CC1"), ("B5", "CC2"),
                ("A6", "D+"), ("B6", "D+"), ("A7", "D-"), ("B7", "D-"), ("A8", "SBU1"), ("B8", "SBU2"), ("S1", "SHIELD")]
    usb = [(n, nm, 12.7, 15.24 - 2.54 * i, 180) for i, (n, nm) in enumerate(usb_pins)]
    return [
        ("TP4056", local_symbol("TP4056", "U", "TP4056", tp, (-7.62, -6.35, 7.62, 6.35), "1 A linear Li-ion charger, ESOP-8")),
        ("AO3401", local_symbol("AO3401", "U", "AO3401", ao, (-5.08, -5.08, 2.54, 5.08), "P-channel MOSFET 30 V 4 A, SOT-23 (1=G 2=S 3=D)")),
        ("USB_C_16P", local_symbol("USB_C_16P", "J", "USB_C_16P", usb, (-7.62, -17.78, 10.16, 17.78), "USB-C receptacle, 16 pin, JLC HX TYPE-C-16PIN")),
    ]


def official_symbol(lib, name):
    with open(f"{KISHARE}/symbols/{lib}.kicad_symdir/{name}.kicad_sym") as f:
        text = f.read()
    start = text.index(f'(symbol "{name}"')
    depth = 0
    for i in range(start, len(text)):
        depth += {"(": 1, ")": -1}.get(text[i], 0)
        if depth == 0:
            break
    return text[start:i + 1]


def symbol_pins(body):
    """(number, x, y, angle) for every pin in a symbol S-expression."""
    return [(m.group(4), float(m.group(1)), float(m.group(2)), float(m.group(3)))
            for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\).*?\(number "([^"]+)"', body, re.S)]


def write_symbol_lib(syms):
    with open(f"{HERE}/{NAME}.kicad_sym", "w") as f:
        f.write('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "power_dock_build")\n\t(generator_version "10.0")\n')
        for _, body in syms:
            f.write(body + "\n")
        f.write(")\n")


def write_schematic():
    loc = local_symbols()
    write_symbol_lib(loc)
    lib = {f"power-dock:{n}": b for n, b in loc}
    for lid in ["Device:R", "Device:C", "Device:LED", "Device:Polyfuse", "Connector_Generic:Conn_01x02",
                "Connector_Generic:Conn_01x04", "Connector_Generic:Conn_01x06", "power:GND", "power:PWR_FLAG"]:
        l, n = lid.split(":")
        lib[lid] = official_symbol(l, n)
    root = uid("root")
    items = []

    def prop(k, v, x, y, hide=False):
        return f'\t\t(property "{k}" "{v}" (at {x:.2f} {y:.2f} 0) {"(hide yes) " if hide else ""}(effects (font (size 1.27 1.27))))'

    def place(lid, ref, value, x, y, props, in_bom=True):
        u = uid("sym/" + ref)
        body = lib[lid]
        s = [f'\t(symbol (lib_id "{lid}") (at {x:.2f} {y:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board {"yes" if in_bom else "no"}) (dnp no) (uuid "{u}")',
             prop("Reference", ref, x + 2.54, y - 8.5, ref.startswith("#")), prop("Value", value, x + 2.54, y + 8.5)]
        for k, v in props.items():
            s.append(prop(k, v, x, y, True))
        for num, *_ in symbol_pins(body):
            s.append(f'\t\t(pin "{num}" (uuid "{uid("pin/" + ref + "/" + num)}"))')
        s.append(f'\t\t(instances (project "{NAME}" (path "/{root}" (reference "{ref}") (unit 1))))\n\t)')
        items.append("\n".join(s))
        return u

    pwr = [0]

    def gnd_at(x, y):
        pwr[0] += 1
        place("power:GND", f"#PWR{pwr[0]:02d}", "GND", x, y, {"Footprint": "", "Datasheet": ""})

    layout = {"J1": (40, 60), "R1": (75, 50), "R7": (85, 50), "C2": (95, 50), "U1": (140, 60), "R2": (110, 75),
              "R3": (175, 50), "D1": (195, 50), "C1": (175, 80), "J2": (40, 120), "F1": (75, 120),
              "R5": (110, 120), "R6": (125, 120), "P1": (240, 60), "U2": (200, 120), "R4": (175, 120), "P2": (240, 120)}
    syms = {}
    for ref, (lid, value, fp, lcsc, mpn, mfr, pins) in PARTS.items():
        x, y = (round(v / 2.54) * 2.54 for v in layout[ref])
        syms[ref] = place(lid, ref, value, x, y, {"Footprint": fp, "Datasheet": "", "LCSC": lcsc, "MPN": mpn, "Manufacturer": mfr})
        for num, px, py, a in symbol_pins(lib[lid]):
            net = pins[num]
            ex, ey = x + px, y - py
            if net is None:
                items.append(f'\t(no_connect (at {ex:.2f} {ey:.2f}) (uuid "{uid("nc/" + ref + num)}"))')
                continue
            dx, dy = -math.cos(math.radians(a)), math.sin(math.radians(a))
            sx, sy = ex + 2.54 * round(dx), ey + 2.54 * round(dy)
            items.append(f'\t(wire (pts (xy {ex:.2f} {ey:.2f}) (xy {sx:.2f} {sy:.2f})) (stroke (width 0) (type default)) (uuid "{uid("w/" + ref + num)}"))')
            if net == "GND":
                gnd_at(sx, sy)
            else:
                ang = 180 if round(dx) < 0 else 0
                just = "right bottom" if ang == 180 else "left bottom"
                items.append(f'\t(label "{net}" (at {sx:.2f} {sy:.2f} {ang}) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{uid("l/" + ref + num)}"))')
    # one PWR_FLAG marks GND as driven (the pack and USB supply it off-sheet)
    items.append(f'\t(wire (pts (xy 20.32 152.4) (xy 20.32 157.48)) (stroke (width 0) (type default)) (uuid "{uid("w/flag")}"))')
    place("power:PWR_FLAG", "#FLG01", "PWR_FLAG", 20.32, 152.4, {"Footprint": "", "Datasheet": ""})
    gnd_at(20.32, 157.48)
    items.append(f'\t(text "Power dock v1: TP4056 charger, battery divider, IR head gate. See SPEC.md." (at 20 20 0) (effects (font (size 2 2)) (justify left bottom)) (uuid "{uid("txt")}"))')

    libs = "\n".join(re.sub(r'^\(symbol "[^"]+"', f"(symbol \"{k}\"", v.strip(), count=1) for k, v in lib.items())
    with open(f"{HERE}/{NAME}.kicad_sch", "w") as f:
        f.write(f'(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "{root}")\n\t(paper "A4")\n')
        f.write(f'\t(title_block (title "Power dock") (date "2026-11-09") (rev "1") (company "wiener-netze-smartmeter"))\n')
        f.write(f"\t(lib_symbols\n{libs}\n\t)\n")
        f.write("\n".join(items))
        f.write(f'\n\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n')
    return syms


# ---------------------------------------------------------------- board
def P(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(ORIGIN[0] + x), pcbnew.FromMM(ORIGIN[1] + y))


PLACE = {  # ref: (x, y, rotation)
    "J1": (9.0, 4.2, 180), "R1": (10.25, 10.0, 90), "R7": (7.25, 10.0, 90), "C2": (13.0, 11.0, 90),
    "U1": (8.0, 15.0, 0), "R2": (2.2, 14.365, 0), "R3": (13.5, 14.365, 0), "D1": (16.8, 14.365, 0),
    "R4": (19.5, 15.0, 90), "U2": (22.3, 15.0, 0), "C1": (13.0, 18.2, 90), "F1": (10.0, 23.0, 0),
    "J2": (2.8, 21.4, 0), "R5": (24.0, 5.0, 90), "R6": (24.0, 8.2, 90), "P1": (29.8, 2.2, 0), "P2": (29.8, 18.6, 0),
}

REF_POS = {"P1": (26.6, 0.9), "P2": (27.0, 27.0), "R4": (18.4, 17.4), "U1": (8.0, 15.0)}
# names eeschema gives single-pin nets of unconnected pins
NC_NETS = {("J1", n): f"unconnected-(J1-{nm}-Pad{n})" for n, nm in
           [("A6", "D+"), ("B6", "D+"), ("A7", "D-"), ("B7", "D-"), ("A8", "SBU1"), ("B8", "SBU2")]}
NC_NETS.update({("P2", "4"): "unconnected-(P2-Pin_4-Pad4)", ("U1", "6"): "unconnected-(U1-~{STDBY}-Pad6)"})

W_PWR, W_SIG = 0.4, 0.25
# (net, width, layer, points); a point is (x, y) or a "REF.PAD" string
ROUTES = [
    ("CC1", W_SIG, "F", ["J1.A5", (10.25, 8.0), "R1.2"]),
    ("CC2", W_SIG, "F", ["J1.B5", (7.25, 8.0), "R7.2"]),
    ("VBUS", W_PWR, "F", ["J1.B9A4", (11.4, 8.1), (11.9, 8.6), (11.9, 12.4), (11.0, 13.095)]),
    ("VBUS", W_PWR, "F", [(11.9, 9.6), "C2.2"]),
    ("VBUS", W_PWR, "F", ["J1.A9B4", (6.6, 7.4), (6.3, 8.1)]),
    ("VBUS", W_PWR, "B", [(6.3, 8.1), (11.4, 8.1)]),
    ("VBUS", W_PWR, "B", [(6.3, 8.1), (3.0, 8.1), (3.0, 16.905)]),
    ("VBUS", W_PWR, "F", [(3.0, 16.905), "U1.4"]),
    ("GND", W_SIG, "F", ["J1.B12A1", (13.33, 6.7)]),
    ("GND", W_SIG, "F", ["J1.A12B1", (4.67, 6.7)]),
    ("GND", W_SIG, "F", ["R1.1", (10.25, 12.0)]),
    ("GND", W_SIG, "F", ["R7.1", (7.25, 12.0)]),
    ("GND", W_SIG, "F", ["C2.1", (13.0, 12.8)]),
    ("GND", W_SIG, "F", ["U1.1", (3.9, 13.095)]),
    ("GND", W_SIG, "F", ["U1.3", (3.9, 15.635)]),
    ("GND", W_SIG, "F", ["R2.1", (1.375, 13.2)]),
    ("GND", W_SIG, "F", ["C1.1", (13.0, 20.0)]),
    ("GND", W_SIG, "F", ["R6.1", (25.2, 9.025)]),
    ("PROG", W_SIG, "F", ["U1.2", "R2.2"]),
    ("BAT+RAW", W_PWR, "F", ["J2.1", (2.8, 24.5), (8.0, 24.5), "F1.1"]),
    ("BAT+", W_PWR, "F", ["F1.2", (10.9125, 18.2), (10.475, 17.6), "U1.5"]),
    ("BAT+", W_PWR, "F", ["U1.5", (12.5, 16.905), "C1.2"]),
    ("BAT+", W_PWR, "F", ["C1.2", (15.5, 17.375)]),
    ("BAT+", W_PWR, "B", [(15.5, 17.375), (15.5, 3.0), (16.3, 2.2), "P1.1"]),
    ("BAT+", W_PWR, "F", ["P1.1", (24.0, 2.2), "R5.2"]),
    ("BATMID", W_SIG, "F", ["R5.1", "R6.2"]),
    ("BATMID", W_SIG, "F", ["R6.2", (28.0, 7.28), "P1.3"]),
    ("CHRG", W_SIG, "F", ["U1.7", "R3.1"]),
    ("CHRG_LED", W_SIG, "F", ["R3.2", "D1.1"]),
    ("VCC_3V3", W_SIG, "B", ["P1.4", (18.3, 9.82), (18.3, 14.365)]),
    ("VCC_3V3", W_SIG, "F", ["D1.2", (18.3, 14.365), (18.3, 15.825), "R4.1"]),
    ("VCC_3V3", W_SIG, "F", ["R4.1", "U2.2"]),
    ("IR_EN", W_SIG, "F", ["P1.5", (21.5, 12.36), (21.36, 13.0), "U2.1"]),
    ("IR_EN", W_SIG, "F", ["U2.1", "R4.2"]),
    ("IR_PWR", W_SIG, "F", ["U2.3", (26.5, 18.6), "P2.1"]),
    ("HICH_TX", W_SIG, "B", ["P1.6", (27.6, 16.0), (27.6, 22.6), (28.7, 23.68), "P2.3"]),
]
VIAS = [("VBUS", 6.3, 8.1), ("VBUS", 11.4, 8.1), ("VBUS", 3.0, 16.905), ("BAT+", 15.5, 17.375),
        ("VCC_3V3", 18.3, 14.365)] + [("GND", x, y) for x, y in [
            (10.25, 12.0), (7.25, 12.0), (13.0, 12.8), (3.9, 13.095), (3.9, 15.635), (1.375, 13.2),
            (13.0, 20.0), (25.2, 9.025), (20.0, 26.0), (17.0, 6.0), (2.0, 4.0), (6.0, 26.5), (26.0, 13.8)]]


def build_board(syms):
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nets = {}
    for pins in (p[6] for p in PARTS.values()):
        for n in pins.values():
            if n and n not in nets:
                ni = pcbnew.NETINFO_ITEM(board, pcb_net(n))
                board.Add(ni)
                nets[n] = ni
    pads = {}
    for ref, (lid, value, fpid, lcsc, mpn, mfr, pins) in PARTS.items():
        lib, name = fpid.split(":")
        path = f"{HERE}/footprints" if lib == "power-dock" else f"{KISHARE}/footprints/{lib}.pretty"
        fp = pcbnew.FootprintLoad(path, name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        for k, v in (("LCSC", lcsc), ("MPN", mpn), ("Manufacturer", mfr)):
            fp.SetField(k, v)
        for fld in fp.GetFields():
            if fld.GetName() in ("LCSC", "MPN", "Manufacturer"):
                fld.SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH("/" + syms[ref]))
        fp.SetSheetname("/")
        fp.SetSheetfile(f"{NAME}.kicad_sch")
        x, y, rot = PLACE[ref]
        board.Add(fp)
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(rot)
        if ref in REF_POS:
            fp.Reference().SetPosition(P(*REF_POS[ref]))
            fp.Reference().SetTextAngleDegrees(0)
        for pad in fp.Pads():
            n = pins.get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
                if ref == "J1":  # already tied to the shell legs by tracks
                    pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            elif (ref, pad.GetNumber()) in NC_NETS:
                ni = pcbnew.NETINFO_ITEM(board, NC_NETS[(ref, pad.GetNumber())])
                board.Add(ni)
                pad.SetNet(ni)
            if pad.GetNumber():
                pads[f"{ref}.{pad.GetNumber()}"] = pad.GetPosition()
    layers = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    for net, w, layer, pts in ROUTES:
        vs = [pads[p] if isinstance(p, str) else P(*p) for p in pts]
        for a, b in zip(vs, vs[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(a)
            t.SetEnd(b)
            t.SetWidth(pcbnew.FromMM(w))
            t.SetLayer(layers[layer])
            t.SetNet(nets[net])
            board.Add(t)
    for net, x, y in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(x, y))
        v.SetWidth(pcbnew.FromMM(0.6))
        v.SetDrill(pcbnew.FromMM(0.3))
        v.SetNet(nets[net])
        board.Add(v)
    # outline
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(nets["GND"])
        z.SetLocalClearance(pcbnew.FromMM(0.2))
        z.SetMinThickness(pcbnew.FromMM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        ol = z.Outline()
        ol.NewOutline()
        for c in corners:
            ol.Append(P(*c))
        board.Add(z)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("PWR DOCK")
    t.SetPosition(P(21.0, 25.5))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
    t.SetTextThickness(pcbnew.FromMM(0.15))
    board.Add(t)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.SetFileName(f"{HERE}/{NAME}.kicad_pcb")
    pcbnew.SaveBoard(f"{HERE}/{NAME}.kicad_pcb", board)


if __name__ == "__main__":
    build_board(write_schematic())
