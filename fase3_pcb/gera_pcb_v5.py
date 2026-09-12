#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- PCB do drone (4x ESC trifasico + ESP32-S3), KiCad 5.1 headless.
v4: MOSFETs em rot 90 (fluxo vertical), 4 colunas (1 por motor) x 3 fases.
Corrige: (a) curto da trilha de fase sobre o tab do FET (v1/v2);
         (b) pads do modulo MCU fora de lugar (Pos0).
Roda: /usr/bin/python3.9 gera_pcb_v3.py
"""
import os
import pcbnew

LIB = "/usr/share/kicad/modules/"
OUT = "/opt/jupyter/work/drone/fase3_pcb/v5"
os.makedirs(OUT, exist_ok=True)

BRD = pcbnew.BOARD()
BRD.SetCopperLayerCount(4)
try:
    BRD.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
except Exception:
    pass

X0, Y0, W, H = 10.0, 10.0, 220.0, 160.0
poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
for x, y in [(X0, Y0), (X0 + W, Y0), (X0 + W, Y0 + H), (X0, Y0 + H)]:
    poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
dd = pcbnew.DRAWSEGMENT(BRD); dd.SetShape(pcbnew.S_POLYGON)
dd.SetPolyShape(poly); dd.SetLayer(pcbnew.Edge_Cuts); BRD.Add(dd)

_nets = {}
def net(name):
    if name not in _nets:
        n = pcbnew.NETINFO_ITEM(BRD, name); BRD.Add(n); _nets[name] = n
    return _nets[name]

MODS = {}
def place(lib, mod, ref, x, y, rot=0.0):
    m = pcbnew.FootprintLoad(LIB + lib, mod)
    if m is None:
        raise RuntimeError("footprint ausente: %s/%s" % (lib, mod))
    m.SetPosition(pcbnew.wxPointMM(x, y))
    if rot:
        m.SetOrientationDegrees(rot)
    m.SetReference(ref); BRD.Add(m); MODS[ref] = m
    return m

def padpos(ref, name):
    for p in MODS[ref].Pads():
        if p.GetPadName() == name:
            return p
    raise RuntimeError("pad %s.%s inexistente" % (ref, name))

def setnet(ref, name, netname):
    for p in MODS[ref].Pads():
        if p.GetPadName() == name:
            p.SetNetCode(net(netname).GetNet())

def wire(ref1, pd1, ref2, pd2, netname, w, layer=pcbnew.F_Cu):
    p1 = padpos(ref1, pd1); p2 = padpos(ref2, pd2)
    setnet(ref1, pd1, netname); setnet(ref2, pd2, netname)
    t = pcbnew.TRACK(BRD)
    t.SetStart(p1.GetPosition()); t.SetEnd(p2.GetPosition())
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer)
    t.SetNetCode(net(netname).GetNet()); BRD.Add(t)

def wire_pt(ref1, pd1, x2, y2, netname, w, layer=pcbnew.F_Cu):
    p1 = padpos(ref1, pd1)
    setnet(ref1, pd1, netname)
    t = pcbnew.TRACK(BRD)
    t.SetStart(p1.GetPosition()); t.SetEnd(pcbnew.wxPointMM(x2, y2))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer)
    t.SetNetCode(net(netname).GetNet()); BRD.Add(t)

def seg(x1, y1, x2, y2, netname, w, layer=pcbnew.F_Cu):
    """Trilha reta entre dois pontos (sem exigir pad nas pontas)."""
    t = pcbnew.TRACK(BRD)
    t.SetStart(pcbnew.wxPointMM(x1, y1)); t.SetEnd(pcbnew.wxPointMM(x2, y2))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer)
    t.SetNetCode(net(netname).GetNet()); BRD.Add(t)

def via(x, y, netname, drill=0.3, pad=0.6):
    v = pcbnew.VIA(BRD); v.SetPosition(pcbnew.wxPointMM(x, y))
    v.SetDrill(pcbnew.FromMM(drill)); v.SetWidth(pcbnew.FromMM(pad))
    v.SetViaType(pcbnew.VIA_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(net(netname).GetNet()); BRD.Add(v)

def zone(netname, layer, pts, clearance=0.4):
    z = pcbnew.ZONE_CONTAINER(BRD); z.SetLayer(layer)
    z.SetNetCode(net(netname).GetNet()); z.SetZoneClearance(pcbnew.FromMM(clearance))
    o = z.Outline(); o.NewOutline()
    for x, y in pts:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    BRD.Add(z); return z

W_PHASE, W_VBAT, W_GATE, W_DIV = 6.29, 6.0, 0.40, 0.25

def make_smd_pad(mod, name, lx, ly, sx, sy, ox, oy, shape=pcbnew.PAD_SHAPE_RECT):
    p = pcbnew.D_PAD(mod); p.SetName(name); p.SetShape(shape)
    p.SetSize(pcbnew.wxSizeMM(sx, sy)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    ls = pcbnew.LSET()
    for lay in (pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste):
        ls.AddLayer(lay)
    p.SetLayerSet(ls)
    p.SetPos0(pcbnew.wxPointMM(lx, ly)); p.SetPosition(pcbnew.wxPointMM(ox + lx, oy + ly))
    mod.Add(p)

def make_module(ref, ox, oy, n_pins=41, pitch=1.27, bw=25.5):
    m = pcbnew.MODULE(BRD); m.SetPosition(pcbnew.wxPointMM(ox, oy))
    m.SetReference(ref); m.SetValue("ESP32-S3-WROOM-1")
    per = (n_pins - 1) // 2; k = 1
    for i in range(per):
        make_smd_pad(m, str(k), -bw / 2 - 0.5, (per - 1) * pitch / 2 - i * pitch, 2.0, 0.9, ox, oy); k += 1
    for i in range(per):
        make_smd_pad(m, str(k), bw / 2 + 0.5, (per - 1) * pitch / 2 - i * pitch, 2.0, 0.9, ox, oy); k += 1
    make_smd_pad(m, str(k), 0, 0, 6.0, 6.0, ox, oy)
    BRD.Add(m); MODS[ref] = m; return m

# ================================================================
# 4 MOTORES x 3 FASES  (coluna por motor, fluxo vertical no FET)
# ================================================================
COL_X = [80.0, 118.0, 156.0, 194.0]
ROW_Y = [25.0, 69.0, 113.0]
clusters = []

for mi, cx in enumerate(COL_X):
    for ph, y in enumerate(ROW_Y):
        t = "M%d%02d" % (mi + 1, ph + 1)
        # --- potencia ---
        place("Package_TO_SOT_SMD.pretty", "TO-252-3_TabPin2", "Q%sH" % t, cx + 12, y + 7, 90)   # dreno p/ cima
        place("Package_TO_SOT_SMD.pretty", "TO-252-3_TabPin2", "Q%sL" % t, cx + 12, y + 20, 90)
        place("Resistor_SMD.pretty", "R_2512_6332Metric", "Rs%s" % t, cx + 12, y + 33, 270)
        via(cx + 12, y + 1, "VBAT_PROT"); via(cx + 12, y + 38, "GND")
        # --- controle ---
        place("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "U%s" % t, cx - 6, y + 20)
        place("Capacitor_SMD.pretty", "C_1206_3216Metric", "Cv%s" % t, cx - 6, y + 8)
        place("Diode_SMD.pretty", "D_SOD-123", "Db%s" % t, cx - 12, y + 8)
        place("Capacitor_SMD.pretty", "C_0402_1005Metric", "Ca%s" % t, cx - 6, y + 14)
        place("Capacitor_SMD.pretty", "C_0805_2012Metric", "Cb%s" % t, cx + 4, y + 14)
        place("Resistor_SMD.pretty", "R_0805_2012Metric", "Rgo%s" % t, cx + 4, y + 7)
        place("Resistor_SMD.pretty", "R_0805_2012Metric", "Rgf%s" % t, cx + 4, y + 24)
        place("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "Ua%s" % t, cx + 20, y + 22)
        place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rd1%s" % t, cx + 20, y + 13)
        place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rd2%s" % t, cx + 20, y + 16)
        place("Capacitor_SMD.pretty", "C_0402_1005Metric", "Cd%s" % t, cx + 20, y + 19)
        place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rb1%s" % t, cx + 20, y + 2)
        place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rb2%s" % t, cx + 20, y + 5)
        place("Capacitor_SMD.pretty", "C_0402_1005Metric", "Cbe%s" % t, cx + 20, y + 8)

        # --- netlist ---
        setnet("Q%sH" % t, "2", "VBAT_PROT"); setnet("Q%sL" % t, "2", "PH%s" % t)
        setnet("Q%sH" % t, "3", "PH%s" % t); setnet("Q%sL" % t, "3", "SN%s" % t)
        setnet("Rs%s" % t, "1", "SN%s" % t); setnet("Rs%s" % t, "2", "GND")
        setnet("Q%sH" % t, "1", "GH%s" % t); setnet("Q%sL" % t, "1", "GL%s" % t)
        setnet("Cb%s" % t, "1", "VB%s" % t); setnet("Cb%s" % t, "2", "PH%s" % t)
        setnet("Cv%s" % t, "1", "12V"); setnet("Cv%s" % t, "2", "GND")
        setnet("Db%s" % t, "1", "12V"); setnet("Db%s" % t, "2", "VB%s" % t)
        setnet("Ca%s" % t, "1", "VBAT_PROT"); setnet("Ca%s" % t, "2", "GND")
        setnet("Rgo%s" % t, "2", "GH%s" % t); setnet("Rgf%s" % t, "2", "GL%s" % t)
        setnet("Rgo%s" % t, "1", "HO%s" % t); setnet("Rgf%s" % t, "1", "LO%s" % t)
        for p in MODS["U%s" % t].Pads():
            p.SetNetCode(net("DRV%s_p%s" % (t, p.GetPadName())).GetNet())
        for p in MODS["Ua%s" % t].Pads():
            p.SetNetCode(net("CSA%s_p%s" % (t, p.GetPadName())).GetNet())
        setnet("Rd1%s" % t, "1", "VREF"); setnet("Rd2%s" % t, "1", "VREF")
        setnet("Rd1%s" % t, "2", "GND"); setnet("Rd2%s" % t, "2", "GND")
        setnet("Cd%s" % t, "1", "VREF"); setnet("Cd%s" % t, "2", "GND")
        setnet("Rb1%s" % t, "1", "PH%s" % t); setnet("Rb2%s" % t, "2", "GND")
        setnet("Cbe%s" % t, "1", "RB%s" % t); setnet("Cbe%s" % t, "2", "GND")

        # pads SEM NOME do TO-252 sao o tab = dreno -> mesma net do pad '2'
        for tag, dn in (("H", "VBAT_PROT"), ("L", "PH%s" % t)):
            for p in MODS["Q%s%s" % (t, tag)].Pads():
                if p.GetPadName() == "":
                    p.SetNetCode(net(dn).GetNet())

        # --- trilhas de potencia (largura calculada) ---
        # no da fase: stub estreito no source do HS (o tab fica a so' 2,6 mm)
        wire_pt("Q%sH" % t, "3", cx + 14.3, y + 16, "PH%s" % t, 2.0)
        seg(cx + 14.3, y + 16, cx + 12, y + 24.2, "PH%s" % t, W_PHASE)
        # source LS -> shunt: stub estreito + trecho largo
        wire_pt("Q%sL" % t, "3", cx + 14.3, y + 27, "SN%s" % t, 2.0)
        seg(cx + 14.3, y + 27, cx + 12, y + 31, "SN%s" % t, W_PHASE)
        # shunt -> via de GND
        wire_pt("Rs%s" % t, "2", cx + 12, y + 38, "GND", W_PHASE)
        wire_pt("Q%sH" % t, "2", cx + 12, y + 1, "VBAT_PROT", W_VBAT)      # dreno HS -> via VBAT
        # --- capacitores locais p/ GND ---
        wire_pt("Ca%s" % t, "2", cx - 6, y + 18, "GND", W_GATE)
        wire_pt("Cv%s" % t, "2", cx - 6, y + 18, "GND", W_GATE)
        # --- bootstrap / gate ---
        wire("Cb%s" % t, "2", "Q%sH" % t, "3", "PH%s" % t, W_GATE)
        wire("Q%sH" % t, "1", "Rgo%s" % t, "2", "GH%s" % t, W_GATE)
        wire("Q%sL" % t, "1", "Rgf%s" % t, "2", "GL%s" % t, W_GATE)
        # --- divisor BEMF do no da fase ---
        wire("Rb1%s" % t, "1", "Q%sL" % t, "2", "PH%s" % t, W_DIV)
        clusters.append(t)

print("clusters:", len(clusters), "| footprints ate aqui:", len(MODS))

# ================================================================
# ENTRADA / PROTECAO / BANCO / BUCKS / MCU
# ================================================================
place("Connector_AMASS.pretty", "AMASS_XT60-F_1x02_P7.20mm_Vertical", "J1", 30, 136)
setnet("J1", "1", "VBAT"); setnet("J1", "2", "GND")
place("Package_TO_SOT_SMD.pretty", "TO-252-2_TabPin1", "Q1", 46, 118)
setnet("Q1", "1", "VBAT"); setnet("Q1", "2", "VBAT_PROT")
place("Diode_SMD.pretty", "D_SMB", "D1", 24, 118)
setnet("D1", "1", "VBAT_PROT"); setnet("D1", "2", "GND")
for i in range(6):
    r, c = divmod(i, 2)
    place("Capacitor_SMD.pretty", "CP_Elec_8x10", "Cblk%d" % (i + 1), 20 + r * 14, 92 + c * 12)
    setnet("Cblk%d" % (i + 1), "1", "VBAT_PROT"); setnet("Cblk%d" % (i + 1), "2", "GND")

def buck(ref, y, vout):
    place("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "U%s" % ref, 24, y)
    place("Inductor_SMD.pretty", "L_Bourns-SRN8040_8x8.15mm", "L%s" % ref, 36, y - 6)
    place("Capacitor_SMD.pretty", "C_1210_3225Metric", "Co%sa" % ref, 50, y - 2)
    place("Capacitor_SMD.pretty", "C_1210_3225Metric", "Co%sb" % ref, 50, y + 3)
    for p in MODS["U%s" % ref].Pads():
        p.SetNetCode(net("U%s_p%s" % (ref, p.GetPadName())).GetNet())
    wire("L%s" % ref, "2", "Co%sa" % ref, "1", vout, 0.6)
    setnet("L%s" % ref, "1", "SW%s" % ref)
    setnet("Co%sa" % ref, "2", "GND"); setnet("Co%sb" % ref, "1", vout); setnet("Co%sb" % ref, "2", "GND")

buck("B1", 48, "12V"); buck("B2", 60, "5V"); buck("B3", 72, "3V3")
place("Package_TO_SOT_SMD.pretty", "SOT-23", "U_LDO", 60, 78)
for p, nm in zip(MODS["U_LDO"].Pads(), ["3V3", "GND", "3V3_A"]):
    p.SetNetCode(net(nm).GetNet())

m = make_module("U_MCU", 42, 152)
for p in m.Pads():
    p.SetNetCode(net("MCU_%s" % p.GetPadName()).GetNet())
place("Sensor_Motion.pretty", "InvenSense_QFN-24_3x3mm_P0.4mm", "U_IMU", 20, 146)
for p in MODS["U_IMU"].Pads():
    p.SetNetCode(net("IMU_%s" % p.GetPadName()).GetNet())
place("Package_LGA.pretty", "Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering", "U_BARO", 62, 146)
for p in MODS["U_BARO"].Pads():
    p.SetNetCode(net("BARO_%s" % p.GetPadName()).GetNet())
place("Connector_USB.pretty", "USB_C_Receptacle_GCT_USB4085", "J2", 36, 24, 180)
for p in MODS["J2"].Pads():
    p.SetNetCode(net("USB_%s" % p.GetPadName()).GetNet())
place("LED_SMD.pretty", "LED_0805_2012Metric", "D_LED", 14, 150)
setnet("D_LED", "2", "3V3"); setnet("D_LED", "1", "LED_K")
place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rled", 14, 154)
setnet("Rled", "1", "LED_K"); setnet("Rled", "2", "GND")
place("Button_Switch_SMD.pretty", "SW_Push_1P1T_NO_CK_KMR2", "SW1", 14, 160)
place("Button_Switch_SMD.pretty", "SW_Push_1P1T_NO_CK_KMR2", "SW2", 14, 165)

# --- conectores de motor: 1 por coluna ---
for mi, cx in enumerate(COL_X):
    place("Connector_AMASS.pretty", "AMASS_MR30PW-FB_1x03_P3.50mm_Horizontal", "J_M%d" % (mi + 1), cx, 14)
    for ph in range(3):
        setnet("J_M%d" % (mi + 1), str(ph + 1), "PHM%d%d" % (mi + 1, ph + 1))
print("footprints totais:", len(MODS))

# ================================================================
# PLANOS + VIAS DE COSTURA
# ================================================================
mg = 1.0
zc = [(X0 + mg, Y0 + mg), (X0 + W - mg, Y0 + mg), (X0 + W - mg, Y0 + H - mg), (X0 + mg, Y0 + H - mg)]
zone("GND", pcbnew.In1_Cu, zc)
zone("GND", pcbnew.B_Cu, zc)
zone("VBAT_PROT", pcbnew.In2_Cu, zc)
for (vx, vy) in [(20, 86), (34, 86), (48, 86), (28, 112), (46, 112), (24, 130)]:
    via(vx, vy, "VBAT_PROT")

nv = 0
for yv in range(14, 166, 8):
    for xv in range(14, 226, 8):
        via(xv, yv, "GND"); nv += 1
print("vias de costura GND:", nv)

filler = pcbnew.ZONE_FILLER(BRD); filler.Fill(BRD.Zones())
BRD.Save(OUT + "/v5_drone.kicad_pcb")
print("salvou", OUT + "/v5_drone.kicad_pcb")

pc = pcbnew.PLOT_CONTROLLER(BRD); po = pc.GetPlotOptions()
po.SetOutputDirectory(OUT); po.SetPlotFrameRef(False); po.SetAutoScale(False)
po.SetScale(1); po.SetMirror(False); po.SetUseGerberAttributes(False)
po.SetUseGerberProtelExtensions(True); po.SetExcludeEdgeLayer(False)
po.SetSubtractMaskFromSilk(True); po.SetCreateGerberJobFile(False)
for layer in [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu,
              pcbnew.F_Mask, pcbnew.B_Mask, pcbnew.F_SilkS, pcbnew.B_SilkS,
              pcbnew.Edge_Cuts]:
    pc.SetLayer(layer)
    pc.OpenPlotfile("drone_%s" % BRD.GetLayerName(layer), pcbnew.PLOT_FORMAT_GERBER, "drone")
    pc.PlotLayer()
pc.ClosePlot()
dw = pcbnew.EXCELLON_WRITER(BRD)
dw.SetOptions(False, False, pcbnew.wxPoint(0, 0), False)
dw.CreateDrillandMapFilesSet(OUT, True, False)
print("ok")
