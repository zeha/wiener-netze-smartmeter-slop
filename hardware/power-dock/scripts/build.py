"""Regenerate the power-dock PCB (power-dock.kicad_pcb) from library footprints.

The schematic (power-dock.kicad_sch) and the local symbol library are maintained
by hand in the KiCad GUI; this script only rewrites the PCB and leaves both
alone. Run with KiCad's bundled Python (needs the pcbnew module), see README.md.

Layout: the v1 placement (32 x 28 mm) is scaled uniformly by SCALE and centred
with MARGIN of free edge on every side, so the board is
(32*SCALE + 2*MARGIN) x (28*SCALE + 2*MARGIN) mm = 65.2 x 58.8 mm. The scaling
opens the spacing between connectors and components for manual rework; the
margin keeps pads, vias and the outline at JLCPCB-safe distances from the edge.
Four plated mounting holes (3.2 mm drill, 6 mm pad) sit at the corners.
Every footprint, route, via, zone and silkscreen item below is data taken from
the v1 board, so a regenerated board is geometrically identical to v1 except
for the scale, margin and mounting holes.
"""
import math
import os
import uuid

import pcbnew

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KISHARE = os.environ.get("KISHARE", "/opt/data/cache/kicad/AppDir/share/kicad")
NAME = "power-dock"
ORIGIN = (100.0, 100.0)
BASE_W, BASE_H = 32.0, 28.0
SCALE = 1.6
MARGIN = 7.0
BOARD_W = BASE_W * SCALE + 2 * MARGIN
BOARD_H = BASE_H * SCALE + 2 * MARGIN


def uid(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "power-dock/" + seed))


# --- parts: ref -> (lib_id, value, footprint, LCSC, MPN, manufacturer, {pin: net}) ---
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_JST = "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal"
PARTS = {
    "U1": ("power-dock:TP4056", "TP4056", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "C725790", "TP4056", "UMW (Youtai)",
           {"1": "GND", "2": "PROG", "3": "GND", "4": "VBUS", "5": "BAT+", "6": None, "7": "CHRG", "8": "VBUS"}),
    "U2": ("power-dock:AO3401", "AO3401", "Package_TO_SOT_SMD:SOT-23", "C727156", "AO3401", "TWGMC",
           {"1": "IR_EN", "2": "VCC_3V3", "3": "IR_PWR"}),
    "J1": ("power-dock:USB_C_16P", "TYPE-C16PIN", "power-dock:TYPE-C-SMD_HX-TYPE-C-16PIN", "C393939", "TYPE-C16PIN", "SHOU HAN",
           {"B12A1": "GND", "A12B1": "GND", "B9A4": "VBUS", "A9B4": "VBUS", "A5": "CC1", "B5": "CC2",
            "A6": None, "A7": None, "A8": None, "B6": None, "B7": None, "B8": None, "S1": "GND"}),
    "J2": ("Connector_Generic:Conn_01x02", "S2B-PH-K-S-GW", FP_JST, "C157932", "S2B-PH-K-S-GW", "JST",
           {"1": "BAT+RAW", "2": "GND"}),
    "J3": ("Connector_Generic:Conn_01x02", "S2B-PH-K-S-GW", FP_JST, "C157932", "S2B-PH-K-S-GW", "JST",
           {"1": "BAT2RAW", "2": "GND"}),
    "F1": ("Device:Polyfuse", "1A PTC", "Resistor_SMD:R_0805_2012Metric", "C22472456", "SMD0805-100C-6V", "BNstar",
           {"1": "BAT+RAW", "2": "BAT+"}),
    "F2": ("Device:Polyfuse", "1A PTC", "Resistor_SMD:R_0805_2012Metric", "C22472456", "SMD0805-100C-6V", "BNstar",
           {"1": "BAT2RAW", "2": "BAT+"}),
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

# mounting holes: (x, y) in final board coordinates
MH_POS = [(4.0, 4.0), (BOARD_W - 4.0, 4.0), (BOARD_W - 4.0, BOARD_H - 4.0), (4.0, BOARD_H - 4.0)]


def pcb_net(net):
    return net if net == "GND" else "/" + net


# ---------------------------------------------------------------- board
def P(x, y):
    """absolute board coordinate (mm) -> KiCad int vector"""
    return pcbnew.VECTOR2I(pcbnew.FromMM(ORIGIN[0] + x), pcbnew.FromMM(ORIGIN[1] + y))


def Q(x, y):
    """v1 layout coordinate (mm) -> final board coordinate, scaled + margined"""
    return P(MARGIN + SCALE * x, MARGIN + SCALE * y)


# v1 layout coordinates
PLACE = {  # ref: (x, y, rotation)
    "J1": (9.0, 4.2, 180), "R1": (10.25, 10.0, 90), "R7": (7.25, 10.0, 90), "C2": (13.0, 11.0, 90),
    "U1": (8.0, 15.0, 0), "R2": (2.2, 14.365, 0), "R3": (13.5, 14.365, 0), "D1": (16.8, 14.365, 0),
    "R4": (19.5, 15.0, 90), "U2": (22.3, 15.0, 0), "C1": (13.0, 18.2, 90), "F1": (10.0, 23.0, 0),
    "J2": (2.8, 21.4, 0), "J3": (14.5, 21.6, 0), "F2": (21.0, 21.4, 0), "R5": (24.0, 5.0, 90),
    "R6": (24.0, 8.2, 90), "P1": (29.8, 2.2, 0), "P2": (29.8, 18.6, 0),
}
# reference label offsets, footprint-local (mm), as placed in the v1 board
REF_LOCAL = {
    "R1": (0, -1.43), "C1": (0, -1.43), "R2": (0, -1.43), "R7": (0, -1.43), "F1": (0, -1.65),
    "F2": (0, -1.65), "C2": (0, -1.43), "U2": (0, -2.4), "R6": (0, -1.43), "R5": (0, -1.43),
    "R4": (-2.4, -1.1), "R3": (0, -1.43), "P1": (-3.2, -1.3), "D1": (0, -1.43), "P2": (-2.8, 8.4),
    "J2": (1, -2.55), "J3": (1, -2.55),
}
# names eeschema gives single-pin nets of unconnected pins
NC_NETS = {(ref, n): f"unconnected-({ref}-{nm}-Pad{n})" for ref, n, nm in
           [("J1", "A6", "D+"), ("J1", "B6", "D+"), ("J1", "A7", "D-"), ("J1", "B7", "D-"),
            ("J1", "A8", "SBU1"), ("J1", "B8", "SBU2"), ("P2", "4", "Pin_4"), ("U1", "6", "~{STDBY")]}
# (ref, pad, local x, local y, net) — v1 pad anchors, footprint-local, from the v1 board
V1_PADS = [
    ("R1", "1", -0.825, 0.000, "GND"),
    ("R1", "2", 0.825, 0.000, "/CC1"),
    ("C1", "1", -0.775, 0.000, "GND"),
    ("C1", "2", 0.775, 0.000, "/BAT+"),
    ("R2", "1", -0.825, 0.000, "GND"),
    ("R2", "2", 0.825, 0.000, "/PROG"),
    ("R7", "1", -0.825, 0.000, "GND"),
    ("R7", "2", 0.825, 0.000, "/CC2"),
    ("F1", "1", -0.912, 0.000, "/BAT+RAW"),
    ("F1", "2", 0.912, 0.000, "/BAT+"),
    ("F2", "1", -0.912, 0.000, "BAT2RAW"),
    ("F2", "2", 0.912, 0.000, "/BAT+"),
    ("C2", "1", -0.775, 0.000, "GND"),
    ("C2", "2", 0.775, 0.000, "/VBUS"),
    ("U2", "1", -0.938, -0.950, "/IR_EN"),
    ("U2", "2", -0.938, 0.950, "/VCC_3V3"),
    ("U2", "3", 0.938, 0.000, "/IR_PWR"),
    ("R4", "1", -0.825, 0.000, "/VCC_3V3"),
    ("R4", "2", 0.825, 0.000, "/IR_EN"),
    ("R3", "1", -0.825, 0.000, "/CHRG"),
    ("R3", "2", 0.825, 0.000, "/CHRG_LED"),
    ("R5", "1", -0.825, 0.000, "/BATMID"),
    ("R5", "2", 0.825, 0.000, "/BAT+"),
    ("R6", "1", -0.825, 0.000, "GND"),
    ("R6", "2", 0.825, 0.000, "/BATMID"),
    ("P1", "1", 0.000, 0.000, "/BAT+"),
    ("P1", "2", 0.000, 2.540, "GND"),
    ("P1", "3", 0.000, 5.080, "/BATMID"),
    ("P1", "4", 0.000, 7.620, "/VCC_3V3"),
    ("P1", "5", 0.000, 10.160, "/IR_EN"),
    ("P1", "6", 0.000, 12.700, "/HICH_TX"),
    ("P2", "1", 0.000, 0.000, "/IR_PWR"),
    ("P2", "2", 0.000, 2.540, "GND"),
    ("P2", "3", 0.000, 5.080, "/HICH_TX"),
    ("P2", "4", 0.000, 7.620, "unconnected-(P2-Pin_4-Pad4)"),
    ("J2", "1", 0.000, 0.000, "/BAT+RAW"),
    ("J2", "2", 2.000, 0.000, "GND"),
    ("J3", "1", 0.000, 0.000, "BAT2RAW"),
    ("J3", "2", 2.000, 0.000, "GND"),
    ("J1", "A5", -1.250, -2.500, "/CC1"),
    ("J1", "A6", -0.250, -2.500, "unconnected-(J1-D+-PadA6)"),
    ("J1", "A7", 0.250, -2.500, "unconnected-(J1-D--PadA7)"),
    ("J1", "A8", 1.250, -2.500, "unconnected-(J1-SBU1-PadA8)"),
    ("J1", "A9B4", 2.400, -2.500, "/VBUS"),
    ("J1", "A12B1", 3.200, -2.500, "GND"),
    ("J1", "B5", 1.750, -2.500, "/CC2"),
    ("J1", "B6", 0.750, -2.500, "unconnected-(J1-D+-PadB6)"),
    ("J1", "B7", -0.750, -2.500, "unconnected-(J1-D--PadB7)"),
    ("J1", "B8", -1.750, -2.500, "unconnected-(J1-SBU2-PadB8)"),
    ("J1", "B9A4", -2.400, -2.500, "/VBUS"),
    ("J1", "B12A1", -3.200, -2.500, "GND"),
    ("J1", "S1", -4.330, -1.820, "GND"),
    ("J1", "S1", -4.330, 2.380, "GND"),
    ("J1", "S1", -2.000, 1.000, "GND"),
    ("J1", "S1", -2.000, 3.000, "GND"),
    ("J1", "S1", 0.000, 2.000, "GND"),
    ("J1", "S1", 2.000, 1.000, "GND"),
    ("J1", "S1", 2.000, 3.000, "GND"),
    ("J1", "S1", 4.330, -1.820, "GND"),
    ("J1", "S1", 4.330, 2.380, "GND"),
    ("D1", "1", -0.787, 0.000, "/CHRG_LED"),
    ("D1", "2", 0.787, 0.000, "/VCC_3V3"),
    ("U1", "1", -2.475, -1.905, "GND"),
    ("U1", "2", -2.475, -0.635, "/PROG"),
    ("U1", "3", -2.475, 0.635, "GND"),
    ("U1", "4", -2.475, 1.905, "/VBUS"),
    ("U1", "5", 2.475, 1.905, "/BAT+"),
    ("U1", "6", 2.475, 0.635, "unconnected-(U1-~{STDBY}-Pad6)"),
    ("U1", "7", 2.475, -0.635, "/CHRG"),
    ("U1", "8", 2.475, -1.905, "/VBUS"),
]


def _v1_pad_abs(ref, lx, ly):
    """v1 board coordinate of a footprint pad (math y-up convention).

    KiCad's rotation on the y-down board maps local (lx, ly) at rot 90 to
    (ly, -lx) in math coordinates (verified against the placed board:
    rot 270 gives (-ly, lx), rot 180 gives (-lx, -ly)).
    """
    x, y, rot = PLACE[ref]
    a = math.radians(rot)
    return (x + lx * math.cos(a) + ly * math.sin(a),
            y - lx * math.sin(a) + ly * math.cos(a))


# Route endpoints that must stay literal (no pad anchoring): the GND stubs
# beside the J1 shell (they tie into the shell pads through the pour;
# anchoring them would collapse a track onto a shell tab) and the BAT+ jog
# at (12.5, 16.905), whose neighbour segment already lands on C1.2
# (anchoring both ends would create a zero-length track).
NO_ANCHOR = {(5.8, 6.7), (4.67, 6.7), (12.2, 6.7), (13.33, 6.7), (12.5, 16.905)}

# v1 jog points directly below the (native, unscaled) J1 pads: their x is
# replaced by the final pad x so the tracks stay exactly axis-aligned with
# the J1 row (clearance to the neighbouring pads: 0.22-0.53 mm).
JOG_ALIGN = {
    (10.25, 8.0): 22.65,  # CC1  below J1 A5
    (7.25, 8.0): 19.65,   # CC2  below J1 B5
    (6.6, 7.4): 19.0,     # VBUS below J1 A9/B4
    (11.4, 7.4): 23.8,    # VBUS below J1 B9/A4
}


def anchor(pt, net, tol=1.0):
    """v1 route endpoint -> (ref, pad) if it sat within tol of a same-net pad.

    tol=1.0 covers tracks that ended a fraction of a mm inside the pad in
    v1 (e.g. the JST PH pin pads, 2.75 mm wide); after the 1.6x scale-up
    those fractions become mm-sized gaps DRC flags as missing connections.
    Via points and the NO_ANCHOR stubs are never anchored.
    """
    net = net.lstrip("/")
    if pt in NO_ANCHOR or pt in ROUTE_VIAS:
        return None
    best, bd = None, tol
    for ref, num, lx, ly, pnet in V1_PADS:
        if pnet.lstrip("/") != net:
            continue
        px, py = _v1_pad_abs(ref, lx, ly)
        d = math.hypot(pt[0] - px, pt[1] - py)
        if d < bd:
            best, bd = (ref, num), d
    return best

# (net, width, layer, (ax, ay), (bx, by)) in v1 layout coordinates; one entry per
# v1 board segment, so routing, layer choice and widths are reproduced exactly.
ROUTES = [
    ("GND", 0.25, "F", (5.525, 15.635), (3.9, 15.635)),
    ("GND", 0.25, "F", (5.525, 13.095), (3.9, 13.095)),
    ("GND", 0.25, "F", (1.375, 14.365), (1.375, 13.2)),
    ("GND", 0.25, "F", (24.0, 9.025), (25.2, 9.025)),
    ("GND", 0.25, "F", (13.0, 11.775), (13.0, 12.8)),
    ("GND", 0.25, "F", (7.25, 10.825), (7.25, 12.0)),
    ("GND", 0.25, "F", (5.8, 6.7), (4.67, 6.7)),
    ("GND", 0.25, "F", (13.0, 18.975), (13.0, 20.0)),
    ("GND", 0.25, "F", (16.5, 20.725), (16.5, 19.9)),
    ("GND", 0.25, "F", (16.5, 19.9), (13.0, 19.9)),
    ("GND", 0.25, "F", (12.2, 6.7), (13.33, 6.7)),
    ("GND", 0.25, "F", (10.25, 10.825), (10.25, 12.0)),
    ("GND", 0.25, "F", (13.0, 19.9), (13.0, 20.0)),
    ("CC1", 0.25, "F", (10.25, 6.7), (10.25, 8.0)),
    ("CC1", 0.25, "F", (10.25, 8.0), (10.25, 9.175)),
    ("BAT+", 0.4, "F", (10.475, 16.905), (12.5, 16.905)),
    ("BAT+", 0.4, "F", (10.475, 17.6), (10.475, 16.905)),
    ("BAT+", 0.4, "F", (24.0, 2.2), (24.0, 4.175)),
    ("BAT+", 0.4, "F", (22.425, 21.4), (23.2, 21.4)),
    ("BAT+", 0.4, "F", (10.912, 18.2), (10.475, 17.6)),
    ("BAT+", 0.4, "F", (29.8, 2.2), (24.0, 2.2)),
    ("BAT+", 0.4, "F", (10.912, 23.0), (10.912, 18.2)),
    ("BAT+", 0.4, "F", (12.5, 16.905), (13.0, 17.425)),
    ("BAT+", 0.4, "F", (13.0, 17.425), (15.5, 17.375)),
    ("BAT+", 0.4, "B", (23.2, 19.5), (15.5, 19.5)),
    ("BAT+", 0.4, "B", (15.5, 19.5), (15.5, 17.375)),
    ("BAT+", 0.4, "B", (23.2, 21.4), (23.2, 19.5)),
    ("BAT+", 0.4, "B", (15.5, 3.0), (16.3, 2.2)),
    ("BAT+", 0.4, "B", (16.3, 2.2), (29.8, 2.2)),
    ("BAT+", 0.4, "B", (15.5, 17.375), (15.5, 3.0)),
    ("PROG", 0.25, "F", (5.525, 14.365), (3.025, 14.365)),
    ("CC2", 0.25, "F", (7.25, 8.0), (7.25, 9.175)),
    ("CC2", 0.25, "F", (7.25, 6.7), (7.25, 8.0)),
    ("BAT+RAW", 0.4, "F", (2.8, 24.5), (8.0, 24.5)),
    ("BAT+RAW", 0.4, "F", (2.8, 21.4), (2.8, 24.5)),
    ("BAT+RAW", 0.4, "F", (8.0, 24.5), (9.088, 23.0)),
    ("BAT2RAW", 0.4, "F", (14.5, 24.0), (20.088, 24.0)),
    ("BAT2RAW", 0.4, "F", (14.5, 22.475), (14.5, 24.0)),
    ("BAT2RAW", 0.4, "F", (20.088, 24.0), (20.088, 22.1)),
    ("VBUS", 0.4, "F", (3.0, 16.905), (5.525, 16.905)),
    ("VBUS", 0.4, "F", (6.6, 7.4), (6.3, 8.1)),
    ("VBUS", 0.4, "F", (11.9, 9.6), (13.0, 10.225)),
    ("VBUS", 0.4, "F", (11.4, 8.1), (11.9, 8.6)),
    ("VBUS", 0.4, "F", (11.9, 12.4), (11.0, 13.095)),
    ("VBUS", 0.4, "F", (6.6, 6.7), (6.6, 7.4)),
    ("VBUS", 0.4, "F", (11.9, 8.6), (11.9, 12.4)),
    ("VBUS", 0.4, "F", (11.4, 6.7), (11.4, 7.4)),
    ("VBUS", 0.4, "F", (11.4, 7.4), (11.4, 8.1)),
    ("VBUS", 0.4, "B", (6.3, 8.1), (11.4, 8.1)),
    ("VBUS", 0.4, "B", (3.0, 8.1), (3.0, 16.905)),
    ("VBUS", 0.4, "B", (6.3, 8.1), (3.0, 8.1)),
    ("IR_EN", 0.25, "F", (29.8, 12.36), (21.5, 12.36)),
    ("IR_EN", 0.25, "F", (21.5, 12.36), (21.36, 13.0)),
    ("IR_EN", 0.25, "F", (21.36, 13.0), (21.362, 14.05)),
    ("IR_EN", 0.25, "F", (21.362, 14.05), (19.5, 14.175)),
    ("VCC_3V3", 0.25, "F", (19.5, 15.825), (21.362, 15.95)),
    ("VCC_3V3", 0.25, "F", (17.588, 14.365), (18.3, 14.365)),
    ("VCC_3V3", 0.25, "F", (18.3, 15.825), (19.5, 15.825)),
    ("VCC_3V3", 0.25, "F", (18.3, 14.365), (18.3, 15.825)),
    ("VCC_3V3", 0.25, "B", (29.8, 9.82), (18.3, 9.82)),
    ("VCC_3V3", 0.25, "B", (18.3, 9.82), (18.3, 14.365)),
    ("IR_PWR", 0.25, "F", (26.5, 18.6), (29.8, 18.6)),
    ("IR_PWR", 0.25, "F", (23.237, 15.0), (26.5, 18.6)),
    ("BATMID", 0.25, "F", (24.0, 7.375), (28.0, 7.28)),
    ("BATMID", 0.25, "F", (28.0, 7.28), (29.8, 7.28)),
    ("BATMID", 0.25, "F", (24.0, 5.825), (24.0, 7.375)),
    ("CHRG", 0.25, "F", (10.475, 14.365), (12.675, 14.365)),
    ("CHRG_LED", 0.25, "F", (14.325, 14.365), (16.013, 14.365)),
    ("HICH_TX", 0.25, "B", (27.6, 22.6), (28.7, 23.68)),
    ("HICH_TX", 0.25, "B", (29.8, 14.9), (27.6, 16.0)),
    ("HICH_TX", 0.25, "B", (27.6, 16.0), (27.6, 22.6)),
    ("HICH_TX", 0.25, "B", (28.7, 23.68), (29.8, 23.68)),
]
# (net, x, y) in v1 layout coordinates
VIAS = [
    ("GND", 25.2, 9.025), ("GND", 13.0, 12.8), ("GND", 13.0, 20.0), ("GND", 3.9, 13.095),
    ("GND", 2.0, 4.0), ("GND", 10.25, 12.0), ("GND", 3.9, 15.635), ("GND", 17.0, 6.0),
    ("GND", 20.0, 26.0), ("GND", 6.0, 26.5), ("GND", 7.25, 12.0), ("GND", 26.0, 13.8),
    ("GND", 1.375, 13.2), ("BAT+", 15.5, 17.375), ("BAT+", 23.2, 21.4), ("VBUS", 6.3, 8.1),
    ("VBUS", 11.4, 8.1), ("VBUS", 3.0, 16.905), ("VCC_3V3", 18.3, 14.365),
]
ROUTE_VIAS = {(x, y) for _, x, y in VIAS}
# (text, x, y, size) in v1 layout coordinates
SILK = [
    ("BATT", 2.9, 16.0, 0.8), ("BATT2", 14.3, 16.0, 0.8), ("+", 2.5, 17.4, 1.0),
    ("-", 4.5, 17.4, 1.0), ("+", 14.2, 17.7, 1.0), ("5V ONLY", 16.2, 3.5, 1.0),
    ("-", 16.2, 17.7, 1.0), ("PWR DOCK", 23.5, 25.5, 1.0),
]

LAYERS = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = f"{HERE}/footprints" if lib == "power-dock" else f"{KISHARE}/footprints/{lib}.pretty"
    return pcbnew.FootprintLoad(path, name)


def build_board():
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
    for ref, (lid, value, fpid, lcsc, mpn, mfr, pins) in PARTS.items():
        fp = load_fp(fpid)
        fp.SetFPID(pcbnew.LIB_ID(*fpid.split(":")))
        fp.SetReference(ref)
        fp.SetValue(value)
        for k, v in (("LCSC", lcsc), ("MPN", mpn), ("Manufacturer", mfr)):
            fp.SetField(k, v)
        for fld in fp.GetFields():
            if fld.GetName() in ("LCSC", "MPN", "Manufacturer"):
                fld.SetVisible(False)
        x, y, rot = PLACE[ref]
        board.Add(fp)
        pos = Q(x, y)
        fp.SetPosition(pos)
        fp.SetOrientationDegrees(rot)
        if ref in REF_LOCAL:
            a = math.radians(rot)
            lx, ly = REF_LOCAL[ref]
            fp.Reference().SetPosition(P(pos.x / 1e6 + lx * math.cos(a) - ly * math.sin(a),
                                         pos.y / 1e6 + lx * math.sin(a) + ly * math.cos(a)))
            fp.Reference().SetTextAngleDegrees(0)
        for pad in fp.Pads():
            n = pins.get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
                if ref == "J1":  # shell: full connection to the GND zone
                    pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            elif (ref, pad.GetNumber()) in NC_NETS:
                ni = pcbnew.NETINFO_ITEM(board, NC_NETS[(ref, pad.GetNumber())])
                board.Add(ni)
                pad.SetNet(ni)
    # mounting holes (PCB-only items, no schematic symbol)
    for i, (x, y) in enumerate(MH_POS, 1):
        fp = load_fp("power-dock:MountingHole_3.2mm_Pad")
        fp.SetFPID(pcbnew.LIB_ID("power-dock", "MountingHole_3.2mm_Pad"))
        fp.SetReference(f"MH{i}")
        fp.SetValue("3.2mm")
        board.Add(fp)
        fp.SetPosition(P(x, y))
    # route endpoints that sat on v1 pad centers must land on the real (native-
    # size) pads in the stretched layout, not on the stretched v1 coordinates
    pad_pos = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pad_pos[(fp.GetReference(), pad.GetNumber())] = pad.GetPosition()
    def endpoint(p, net):
        """v1 route endpoint -> absolute v2 coordinate.

        JOG_ALIGN points get the final (native J1) pad x and stay on the
        scaled y; anchored endpoints move to the pad centre; everything
        else scales literally.
        """
        if p in JOG_ALIGN:
            return P(JOG_ALIGN[p], MARGIN + SCALE * p[1])
        a = anchor(p, net)
        return pad_pos[a] if a else Q(*p)

    for net, w, layer, a, b in ROUTES:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(endpoint(a, net))
        t.SetEnd(endpoint(b, net))
        t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(LAYERS[layer])
        t.SetNet(nets[net])
        board.Add(t)
    for net, x, y in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(Q(x, y))
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
    for text, x, y, size in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(Q(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        t.SetTextThickness(pcbnew.FromMM(0.15))
        board.Add(t)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.SetFileName(f"{HERE}/{NAME}.kicad_pcb")
    pcbnew.SaveBoard(f"{HERE}/{NAME}.kicad_pcb", board)


if __name__ == "__main__":
    build_board()
