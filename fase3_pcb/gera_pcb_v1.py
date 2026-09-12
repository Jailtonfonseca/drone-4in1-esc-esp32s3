#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- PCB do drone (4x ESC trifasico + ESP32-S3) em KiCad 5.1 headless.
Roda: /usr/bin/python3.9 gera_pcb_v1.py
Gera: v1_drone.kicad_pcb + gerbers/
4 camadas: F.Cu(sinal) / In1.Cu(GND) / In2.Cu(VBAT) / B.Cu(sinal+fase)
"""
import os
import pcbnew

LIB = "/usr/share/kicad/modules/"
OUT = "/opt/jupyter/work/drone/fase3_pcb/v1"
os.makedirs(OUT, exist_ok=True)

BRD = pcbnew.BOARD()
BRD.SetCopperLayerCount(4)
try:
    BRD.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
except Exception:
    pass

# ---------------------------------------------------------------- outline
X0, Y0, W, H = 10.0, 10.0, 140.0, 90.0
poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
for x, y in [(X0, Y0), (X0 + W, Y0), (X0 + W, Y0 + H), (X0, Y0 + H)]:
    poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
d = pcbnew.DRAWSEGMENT(BRD); d.SetShape(pcbnew.S_POLYGON)
d.SetPolyShape(poly); d.SetLayer(pcbnew.Edge_Cuts); BRD.Add(d)

# ---------------------------------------------------------------- nets
_nets = {}
def net(name):
    if name not in _nets:
        n = pcbnew.NETINFO_ITEM(BRD, name); BRD.Add(n); _nets[name] = n
    return _nets[name]

# ---------------------------------------------------------------- place
MODS = {}
def place(lib, mod, ref, x, y, rot=0.0):
    m = pcbnew.FootprintLoad(LIB + lib, mod)
    if m is None:
        raise RuntimeError("footprint nao encontrada: %s/%s" % (lib, mod))
    m.SetPosition(pcbnew.wxPointMM(x, y))
    if rot:
        m.SetOrientationDegrees(rot)
    m.SetReference(ref)
    BRD.Add(m)
    MODS[ref] = m
    return m

def pads_of(ref):
    return {p.GetPadName(): p for p in MODS[ref].Pads()}

def setnet(ref, padname, netname):
    """Liga um pad (por nome) a uma net. Pads sem nome -> todos."""
    ps = [p for p in MODS[ref].Pads() if p.GetPadName() == padname]
    for p in ps:
        p.SetNetCode(net(netname).GetNet())

def track(ref1, pad1, ref2, pad2, netname, width_mm, layer=pcbnew.F_Cu):
    """Trilha reta ligando o centro de dois pads + atribui a net aos dois."""
    p1 = [p for p in MODS[ref1].Pads() if p.GetPadName() == pad1][0]
    p2 = [p for p in MODS[ref2].Pads() if p.GetPadName() == pad2][0]
    setnet(ref1, pad1, netname); setnet(ref2, pad2, netname)
    t = pcbnew.TRACK(BRD)
    t.SetStart(p1.GetPosition()); t.SetEnd(p2.GetPosition())
    t.SetWidth(pcbnew.FromMM(width_mm)); t.SetLayer(layer)
    t.SetNetCode(net(netname).GetNet())
    BRD.Add(t)
    return t

def via(x, y, netname, drill=0.3, pad=0.6):
    v = pcbnew.VIA(BRD)
    v.SetPosition(pcbnew.wxPointMM(x, y))
    v.SetDrill(pcbnew.FromMM(drill)); v.SetWidth(pcbnew.FromMM(pad))
    v.SetViaType(pcbnew.VIA_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(net(netname).GetNet())
    BRD.Add(v)

def zone(netname, layer, pts):
    z = pcbnew.ZONE_CONTAINER(BRD); z.SetLayer(layer)
    z.SetNetCode(net(netname).GetNet())
    o = z.Outline(); o.NewOutline()
    for x, y in pts:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    BRD.Add(z)
    return z

# larguras calculadas (calc_trilhas_vias.py)
W_PHASE  = 6.29   # 15 A rms, 2 oz, dT 10 C
W_GATE   = 0.40   # sinal de gate, curto
W_12V    = 0.60   # 0.6 A
W_5V     = 0.60   # 2 A (0.39 mm calculado -> 0.6 mm por margem)
W_3V3    = 0.40
W_ADC    = 0.25

# ================================================================
# CLUSTER = meia-ponte (2 FETs + driver + gate R + bootstrap + shunt + amp)
# ================================================================
N_MOT = 4
MOT_POS = [(60.0, 20.0), (104.0, 20.0), (60.0, 58.0), (104.0, 58.0)]
CLUSTER_OFF = [(0.0, 0.0), (0.0, 15.0), (0.0, 30.0)]  # 3 fases por motor

HB = []  # lista de (motor, fase, hs_ref, ls_ref, ...)
for mot in range(N_MOT):
    bx0, by0 = MOT_POS[mot]
    for ph in range(3):
        dx, dy = CLUSTER_OFF[ph]
        bx, by = bx0 + dx, by0 + dy
        t = "M%d_%d" % (mot + 1, ph + 1)
        hs = place("Package_TO_SOT_SMD.pretty", "TO-252-3_TabPin2", "Q%sH" % t, bx + 6, by + 4)
        ls = place("Package_TO_SOT_SMD.pretty", "TO-252-3_TabPin2", "Q%sL" % t, bx + 6, by + 15)
        drv = place("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "U%s" % t, bx - 12, by + 8)
        r_on = place("Resistor_SMD.pretty", "R_0805_2012Metric", "Rgo%s" % t, bx - 5, by + 6)
        r_off = place("Resistor_SMD.pretty", "R_0805_2012Metric", "Rgf%s" % t, bx - 5, by + 9)
        c_boot = place("Capacitor_SMD.pretty", "C_0805_2012Metric", "Cb%s" % t, bx - 12, by + 1)
        d_boot = place("Diode_SMD.pretty", "D_SOD-123", "Db%s" % t, bx - 17, by + 1)
        c_vcc = place("Capacitor_SMD.pretty", "C_1206_3216Metric", "Cv%s" % t, bx - 17, by + 7)
        c_hf = place("Capacitor_SMD.pretty", "C_0402_1005Metric", "C%sa" % t, bx + 13, by + 4)
        sh = place("Resistor_SMD.pretty", "R_2512_6332Metric", "Rs%s" % t, bx + 6, by + 26)
        amp = place("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "Ua%s" % t, bx + 20, by + 26)
        rd1 = place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rd1%s" % t, bx + 27, by + 21)
        rd2 = place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rd2%s" % t, bx + 27, by + 24)
        cd = place("Capacitor_SMD.pretty", "C_0402_1005Metric", "Cd%s" % t, bx + 27, by + 27)
        bem1 = place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rb1%s" % t, bx + 16, by + 4)
        bem2 = place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rb2%s" % t, bx + 16, by + 7)
        cbem = place("Capacitor_SMD.pretty", "C_0402_1005Metric", "Cbe%s" % t, bx + 16, by + 10)

        # --- ligacoes locais (meia-ponte) ---
        track("Q%sH" % t, "2", "Q%sH" % t, "2", "VBAT", 0.5)            # no-op net do dreno HS
        setnet("Q%sH" % t, "1", "G%sH" % t)
        setnet("Q%sL" % t, "1", "G%sL" % t)
        setnet("Q%sH" % t, "3", "PH%s" % t)
        setnet("Q%sL" % t, "2", "PH%s" % t)   # dreno LS = no da fase
        setnet("Q%sL" % t, "3", "SN%s" % t)   # source LS -> shunt
        setnet("Rs%s" % t, "1", "SN%s" % t)
        setnet("Rs%s" % t, "2", "GND")
        setnet("Db%s" % t, "1", "12V"); setnet("Db%s" % t, "2", "VB%s" % t)
        setnet("Cb%s" % t, "1", "VB%s" % t); setnet("Cb%s" % t, "2", "PH%s" % t)
        setnet("Cv%s" % t, "1", "12V"); setnet("Cv%s" % t, "2", "GND")
        setnet("C%sa" % t, "1", "VBAT"); setnet("C%sa" % t, "2", "GND")
        for u in ("U%s" % t,):
            for p in MODS[u].Pads():
                p.SetNetCode(net("%s_pin%s" % (u, p.GetPadName())).GetNet())
        HB.append(t)

print("footprints:", len(MODS))

# ================================================================
# ENTRADA / PROTECAO / BANCO
# ================================================================
xt60 = place("Connector_AMASS.pretty", "AMASS_XT60-F_1x02_P7.20mm_Vertical", "J1", 22, 45, 90)
setnet("J1", "1", "VBAT"); setnet("J1", "2", "GND")
qrev = place("Package_TO_SOT_SMD.pretty", "TO-252-2_TabPin1", "Q1", 34, 30)
setnet("Q1", "1", "VBAT"); setnet("Q1", "2", "VBAT_PROT")
tv = place("Diode_SMD.pretty", "D_SMB", "D1", 30, 24)
setnet("D1", "1", "VBAT_PROT"); setnet("D1", "2", "GND")
for i in range(6):
    c = place("Capacitor_SMD.pretty", "CP_Elec_8x10", "Cblk%d" % (i + 1), 26, 56 + i * 5.0)
    setnet("Cblk%d" % (i + 1), "1", "VBAT_PROT"); setnet("Cblk%d" % (i + 1), "2", "GND")

# ================================================================
# BUCK 12 V / 5 V / 3,3 V + LDO
# ================================================================
def buck(ref, y, vin, vout, lval):
    place("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "U%s" % ref, 40, y)
    place("Inductor_SMD.pretty", "L_12x12mm_H6mm", "L%s" % ref, 52, y - 6)
    place("Capacitor_SMD.pretty", "C_1210_3225Metric", "Co%sa" % ref, 60, y)
    place("Capacitor_SMD.pretty", "C_1210_3225Metric", "Co%sb" % ref, 60, y + 4)
    for p in MODS["U%s" % ref].Pads():
        p.SetNetCode(net("U%s_pin%s" % (ref, p.GetPadName())).GetNet())
    track("L%s" % ref, "1", "Co%sa" % ref, "1", vout, 0.6)
    setnet("L%s" % ref, "2", "SW%s" % ref)
    setnet("Co%sa" % ref, "2", "GND"); setnet("Co%sb" % ref, "1", vout); setnet("Co%sb" % ref, "2", "GND")

buck("B1", 68, "VBAT_PROT", "12V", 89e-6)
buck("B2", 76, "12V", "5V", 17e-6)
buck("B3", 84, "5V", "3V3", 5e-6)
place("Package_TO_SOT_SMD.pretty", "SOT-23", "U_LDO", 68, 84)
l = MODS["U_LDO"].Pads()
for p, nm in zip(l, ["3V3", "GND", "3V3_A"]):
    p.SetNetCode(net(nm).GetNet())

# --- pegada gerada por script (nao existe no KiCad 5.1) ---
def make_smd_pad(mod, name, x, y, sx, sy, shape=pcbnew.PAD_SHAPE_RECT):
    p = pcbnew.D_PAD(mod)
    p.SetName(name)
    p.SetShape(shape)
    p.SetSize(pcbnew.wxSizeMM(sx, sy))
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    ls = pcbnew.LSET()
    for lay in (pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste):
        ls.AddLayer(lay)
    p.SetLayerSet(ls)
    p.SetPosition(pcbnew.wxPointMM(x, y))
    mod.Add(p)
    return p

def make_module_footprint(ref, origin_x, origin_y, n_pins=41, pitch=1.27,
                          body_w=25.5, body_h=18.0):
    """ESP32-S3-WROOM-1: 1,27 mm de passo, 41 pads.
    ATENCAO: o MAPEAMENTO pad->sinal NAO foi verificado (datasheet offline).
    A geometria (passo/corpo) e' a do modulo; os nomes sao 1..41 genericos."""
    mod = pcbnew.MODULE(BRD)
    mod.SetPosition(pcbnew.wxPointMM(origin_x, origin_y))
    mod.SetReference(ref)
    mod.SetValue("ESP32-S3-WROOM-1")
    per_side = (n_pins - 1) // 2          # 20 por lado
    n = 1
    for i in range(per_side):             # lado esquerdo
        x = -body_w / 2 - 0.5
        y = (per_side - 1) * pitch / 2 - i * pitch
        make_smd_pad(mod, str(n), x, y, 2.0, 0.9); n += 1
    for i in range(per_side):             # lado direito
        x = body_w / 2 + 0.5
        y = (per_side - 1) * pitch / 2 - i * pitch
        make_smd_pad(mod, str(n), x, y, 2.0, 0.9); n += 1
    make_smd_pad(mod, str(n), 0, 0, 6.0, 6.0, pcbnew.PAD_SHAPE_RECT)  # 41 = EP/GND
    BRD.Add(mod)
    MODS[ref] = mod
    return mod

# ================================================================
# MCU / IMU / BARO / USB  (colocados; roteamento documentado no relatorio)
# ================================================================
mcu = make_module_footprint("U_MCU", 168, 45)
for p in mcu.Pads():
    p.SetNetCode(net("MCU_%s" % p.GetPadName()).GetNet())
imu = place("Sensor_Motion.pretty", "InvenSense_QFN-24_3x3mm_P0.4mm", "U_IMU", 152, 55)
for p in imu.Pads():
    p.SetNetCode(net("IMU_%s" % p.GetPadName()).GetNet())
baro = place("Package_LGA.pretty", "Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering", "U_BARO", 152, 62)
for p in baro.Pads():
    p.SetNetCode(net("BARO_%s" % p.GetPadName()).GetNet())
usb = place("Connector_USB.pretty", "USB_C_Receptacle_GCT_USB4085", "J2", 152, 12, 180)
for p in usb.Pads():
    p.SetNetCode(net("USB_%s" % p.GetPadName()).GetNet())
led = place("LED_SMD.pretty", "LED_0805_2012Metric", "D_LED", 152, 66)
setnet("D_LED", "2", "3V3"); setnet("D_LED", "1", "LED_K")
place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rled", 146, 66)
setnet("Rled", "1", "LED_K"); setnet("Rled", "2", "GND")
sw1 = place("Button_Switch_SMD.pretty", "SW_Push_1P1T_NO_CK_KMR2", "SW1", 152, 72)
sw2 = place("Button_Switch_SMD.pretty", "SW_Push_1P1T_NO_CK_KMR2", "SW2", 152, 76)

# ================================================================
# CONECTORES DE MOTOR
# ================================================================
MOT_CONN_POS = [(46, 14), (118, 14), (46, 86), (118, 86)]
for mot in range(N_MOT):
    x, y = MOT_CONN_POS[mot]
    j = place("Connector_AMASS.pretty", "AMASS_MR30PW-FB_1x03_P3.50mm_Horizontal", "J_M%d" % (mot + 1), x, y, 0)
    for ph in range(3):
        setnet("J_M%d" % (mot + 1), str(ph + 1), "PHM%d_%d" % (mot + 1, ph + 1))

# ================================================================
# PLANOS: In1.Cu = GND (todo o board), In2.Cu = VBAT_PROT
# ================================================================
m = 1.0
zc = [(X0 + m, Y0 + m), (X0 + W - m, Y0 + m), (X0 + W - m, Y0 + H - m), (X0 + m, Y0 + H - m)]
zone("GND", pcbnew.In1_Cu, zc)
zone("GND", pcbnew.B_Cu, zc)
zone("VBAT_PROT", pcbnew.In2_Cu, [(X0 + 2, Y0 + 2), (X0 + 55, Y0 + 2), (X0 + 55, Y0 + H - 2), (X0 + 2, Y0 + H - 2)])

# ================================================================
# VIAS DE COSTURA (GND) -- malha pela borda + entre clusters
# ================================================================
n_via = 0
step = 6.0
y = Y0 + 3
while y <= Y0 + H - 3:
    x = X0 + 3
    while x <= X0 + W - 3:
        if abs(x - (X0 + W / 2)) > 2 or True:
            via(x, y, "GND"); n_via += 1
        x += step
    y += step
print("vias de costura GND:", n_via)

# ================================================================
# FILL + SALVA + GERBER
# ================================================================
pcbnew.ZONE_FILLER(BRD).Fill(BRD.Zones())
BRD.Save(OUT + "/v1_drone.kicad_pcb")
print("salvou", OUT + "/v1_drone.kicad_pcb")

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
print("arquivos:", sorted(os.listdir(OUT)))
