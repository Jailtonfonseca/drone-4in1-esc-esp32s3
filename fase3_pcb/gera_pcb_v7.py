#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- PCB do drone (4x ESC trifasico + ESP32-S3), KiCad 5.1 headless.
v7: netlist COMPLETA + componentes que faltavam na v6.

Mudancas da v6 -> v7 (todas registradas no relatorio da fase 3):
 1. Gate driver = IR2104 (SOIC-8). Pinout cotado no datasheet IR2104S:
    1 VCC, 2 IN, 3 SD, 4 COM, 5 LO, 6 VS, 7 HO, 8 VB.  (SD -> 3V3 por 10k)
 2. Amp de corrente = INA240 (SOIC-8, pacote D). Pinout cotado no datasheet TI
    SBOS662C (fig. 6-2 / tabela 6-1): 1 IN-, 2 GND, 3 REF2, 4 NC, 5 OUT,
    6 VS, 7 REF1, 8 IN+.
 3. MCU = ESP32-S3-WROOM-1: numeracao de pino cotada no datasheet Espressif
    (v0.6, Table 2 "Pin Definitions") -- pin 1 GND ... 40 GND, 41 EPAD GND.
 4. ADC externo: a Fase 0 deixou "16 canais >= 200 ksps" em [N/D offline].
    Escolha aqui: 4x MCP3208 (SOIC-16, 12 bits, 8 canais, SPI), UM POR MOTOR,
    pinout cotado no datasheet Microchip DS21298E tabela 3-1.
    Fica abaixo dos 200 ksps desejados: registrado como limitacao.
 5. IMU = ICM-42688-P (LGA-14 2,5x3,0 mm P0,5). A v6 usava pegada QFN-24 ERRADA.
    Pinout cotado no datasheet TDK DS-000347 v1.6 (tabela 10 / fig. 6).
 6. USB: array ESD USBLC6-2SC6 (SOT-23-6, pinout no datasheet ST), 2x R 5,1k CC.
 7. Entrada: fusivel de lamina mini 30 A (solda direta) + banco de vias p/ In2.
 8. VBUS do USB entra no trilho por diodo Schottky (ORing) -- substitui o
    "ideal diode [N/D offline]" da Fase 0.
 9. Adicionados: divisor de VBAT_SENSE, NTC, I2C pull-ups, botoes EN/BOOT com RC,
    buzzer + transistor, test points, 4 furos, caps por trilho, decoupling ADC.
10. Potencia das fases do motor -> B_Cu (4 mm, afunilando p/ 2 mm no conector),
    porque nao ha corredor de 6,29 mm livre em F_Cu.
11. U_B1/B2/B3 (bucks), U_LDO e U_BARO seguem SEM CI escolhido na Fase 0: os
    pads vao NOMEADOS POR FUNCAO (nao por numero de pino) -- nao invento pinout.
    Ao escolher o CI, remapeia-se nome->pino e o roteamento continua valido.
Roda: /usr/bin/python3.9 gera_pcb_v7.py
"""
import os
import pcbnew

LIB = "/usr/share/kicad/modules/"
OUT = "/opt/jupyter/work/drone/fase3_pcb/v7"
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
    m.SetReference(ref); m.SetValue(mod.split("_")[0]); BRD.Add(m); MODS[ref] = m
    return m

def padpos(ref, name):
    for p in MODS[ref].Pads():
        if p.GetPadName() == name:
            return p
    raise RuntimeError("pad %s.%s inexistente" % (ref, name))

def setnet(ref, name, netname):
    ok = False
    for p in MODS[ref].Pads():
        if p.GetPadName() == name:
            p.SetNetCode(net(netname).GetNet()); ok = True
    if not ok:
        raise RuntimeError("pad %s.%s inexistente" % (ref, name))

def setnets(ref, mapa):
    """mapa = {'nome_do_pad': 'NET'} -- por NOME, nunca por ordem de iteracao."""
    for p in MODS[ref].Pads():
        nm = mapa.get(p.GetPadName())
        if nm:
            p.SetNetCode(net(nm).GetNet())

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
    t = pcbnew.TRACK(BRD)
    t.SetStart(pcbnew.wxPointMM(x1, y1)); t.SetEnd(pcbnew.wxPointMM(x2, y2))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer)
    t.SetNetCode(net(netname).GetNet()); BRD.Add(t)

def via(x, y, netname, drill=0.3, pad=0.6):
    v = pcbnew.VIA(BRD); v.SetPosition(pcbnew.wxPointMM(x, y))
    v.SetDrill(pcbnew.FromMM(drill)); v.SetWidth(pcbnew.FromMM(pad))
    v.SetViaType(pcbnew.VIA_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(net(netname).GetNet()); BRD.Add(v)
    return v

def zone(netname, layer, pts, clearance=0.4):
    z = pcbnew.ZONE_CONTAINER(BRD); z.SetLayer(layer)
    z.SetNetCode(net(netname).GetNet()); z.SetZoneClearance(pcbnew.FromMM(clearance))
    o = z.Outline(); o.NewOutline()
    for x, y in pts:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    BRD.Add(z); return z

def make_smd_pad(mod, name, lx, ly, sx, sy, ox, oy, shape=pcbnew.PAD_SHAPE_RECT):
    p = pcbnew.D_PAD(mod); p.SetName(name); p.SetShape(shape)
    p.SetSize(pcbnew.wxSizeMM(sx, sy)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    ls = pcbnew.LSET()
    for lay in (pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste):
        ls.AddLayer(lay)
    p.SetLayerSet(ls)
    p.SetPos0(pcbnew.wxPointMM(lx, ly)); p.SetPosition(pcbnew.wxPointMM(ox + lx, oy + ly))
    mod.Add(p)

def _novo_mod(ref, ox, oy, value):
    m = pcbnew.MODULE(BRD); m.SetPosition(pcbnew.wxPointMM(ox, oy))
    m.SetReference(ref); m.SetValue(value); BRD.Add(m); MODS[ref] = m
    return m

def make_module(ref, ox, oy, n_pins=41, pitch=1.27, bw=25.5):
    """ESP32-S3-WROOM-1: 20 pads por lado + EPAD. Numeracao = datasheet."""
    m = _novo_mod(ref, ox, oy, "ESP32-S3-WROOM-1")
    per = (n_pins - 1) // 2; k = 1
    for i in range(per):
        make_smd_pad(m, str(k), -bw / 2 - 0.5, (per - 1) * pitch / 2 - i * pitch, 2.0, 0.9, ox, oy); k += 1
    for i in range(per):
        make_smd_pad(m, str(k), bw / 2 + 0.5, (per - 1) * pitch / 2 - i * pitch, 2.0, 0.9, ox, oy); k += 1
    make_smd_pad(m, str(k), 0, 0, 6.0, 6.0, ox, oy)
    return m

def make_ic8(ref, ox, oy, names, value="IC_PENDENTE"):
    """SOIC-8 com pads NOMEADOS POR FUNCAO (CI nao escolhido na Fase 0)."""
    m = _novo_mod(ref, ox, oy, value)
    for i, nm in enumerate(names[:4]):
        make_smd_pad(m, nm, -3.0, 1.905 - i * 1.27, 2.0, 0.6, ox, oy)
    for i, nm in enumerate(names[4:8]):
        make_smd_pad(m, nm, 3.0, -1.905 + i * 1.27, 2.0, 0.6, ox, oy)
    return m

def make_sot23_5(ref, ox, oy, names, value="IC_PENDENTE"):
    m = _novo_mod(ref, ox, oy, value)
    for i, nm in enumerate(names[:3]):
        make_smd_pad(m, nm, -1.1, 0.95 - i * 0.95, 1.0, 0.6, ox, oy)
    for i, nm in enumerate(names[3:5]):
        make_smd_pad(m, nm, 1.1, 0.475 - i * 0.95, 1.0, 0.6, ox, oy)
    make_smd_pad(m, "EP", 0, 0, 1.4, 1.4, ox, oy)
    return m

def make_lga8(ref, ox, oy, names, value="IC_PENDENTE"):
    m = _novo_mod(ref, ox, oy, value)
    for i, nm in enumerate(names[:4]):
        make_smd_pad(m, nm, -0.975 + i * 0.65, -1.0, 0.45, 0.8, ox, oy)
    for i, nm in enumerate(names[4:8]):
        make_smd_pad(m, nm, 0.975 - i * 0.65, 1.0, 0.45, 0.8, ox, oy)
    return m

W_PHASE, W_VBAT, W_GATE, W_DIV = 6.29, 6.0, 0.40, 0.25
W_FASE_CU = 4.0        # trilha de fase em B_Cu
W_FASE_PAD = 2.0       # afunilamento no conector MR30 (pitch 3,5 mm)

# ================================================================
# 4 MOTORES x 3 FASES
# ================================================================
COL_X = [80.0, 118.0, 156.0, 194.0]
ROW_Y = [25.0, 69.0, 113.0]
# corredores em B_Cu: a fase MAIS RASA usa o corredor MAIS PERTO do no' (sem cruzamento)
CORR = [-11.2, -6.6, -2.0]
NODE_DX = 12.0

for mi, cx in enumerate(COL_X):
    for ph, y in enumerate(ROW_Y):
        t = "M%d%02d" % (mi + 1, ph + 1)
        # --- potencia ---
        place("Package_TO_SOT_SMD.pretty", "TO-252-3_TabPin2", "Q%sH" % t, cx + 12, y + 7, 90)
        place("Package_TO_SOT_SMD.pretty", "TO-252-3_TabPin2", "Q%sL" % t, cx + 12, y + 20, 90)
        place("Resistor_SMD.pretty", "R_2512_6332Metric", "Rs%s" % t, cx + 12, y + 33, 270)
        via(cx + 12, y + 1, "VBAT_PROT", 0.5, 1.0)
        via(cx + 12, y + 38, "GND", 0.5, 1.0)
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
        place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rsd%s" % t, cx - 2, y + 30)

        # --- netlist: potencia ---
        setnet("Q%sH" % t, "2", "VBAT_PROT"); setnet("Q%sL" % t, "2", "PH%s" % t)
        setnet("Q%sH" % t, "3", "PH%s" % t); setnet("Q%sL" % t, "3", "SN%s" % t)
        setnet("Rs%s" % t, "1", "SN%s" % t); setnet("Rs%s" % t, "2", "GND")
        setnet("Q%sH" % t, "1", "GH%s" % t); setnet("Q%sL" % t, "1", "GL%s" % t)
        for tag, dn in (("H", "VBAT_PROT"), ("L", "PH%s" % t)):
            for p in MODS["Q%s%s" % (t, tag)].Pads():
                if p.GetPadName() == "":
                    p.SetNetCode(net(dn).GetNet())

        # --- netlist: bootstrap / driver (IR2104S) / amp (INA240) ---
        setnet("Cb%s" % t, "1", "VB%s" % t); setnet("Cb%s" % t, "2", "PH%s" % t)
        setnet("Cv%s" % t, "1", "12V"); setnet("Cv%s" % t, "2", "GND")
        setnet("Db%s" % t, "1", "12V"); setnet("Db%s" % t, "2", "VB%s" % t)
        setnet("Ca%s" % t, "1", "VBAT_PROT"); setnet("Ca%s" % t, "2", "GND")
        setnet("Rgo%s" % t, "2", "GH%s" % t); setnet("Rgf%s" % t, "2", "GL%s" % t)
        setnet("Rgo%s" % t, "1", "HO%s" % t); setnet("Rgf%s" % t, "1", "LO%s" % t)
        setnet("Rsd%s" % t, "1", "SD%s" % t); setnet("Rsd%s" % t, "2", "3V3")
        setnets("U%s" % t, {"1": "12V", "2": "PWM_%s" % t, "3": "SD%s" % t, "4": "GND",
                            "5": "LO%s" % t, "6": "PH%s" % t, "7": "HO%s" % t, "8": "VB%s" % t})
        setnets("Ua%s" % t, {"1": "GND", "2": "GND", "3": "VREF%s" % t, "5": "I_%s" % t,
                             "6": "3V3_A", "7": "VREF%s" % t, "8": "SN%s" % t})
        setnet("Rd1%s" % t, "1", "3V3"); setnet("Rd1%s" % t, "2", "VREF%s" % t)
        setnet("Rd2%s" % t, "1", "VREF%s" % t); setnet("Rd2%s" % t, "2", "GND")
        setnet("Cd%s" % t, "1", "VREF%s" % t); setnet("Cd%s" % t, "2", "GND")
        setnet("Rb1%s" % t, "1", "PH%s" % t); setnet("Rb1%s" % t, "2", "RB%s" % t)
        setnet("Rb2%s" % t, "1", "RB%s" % t); setnet("Rb2%s" % t, "2", "GND")
        setnet("Cbe%s" % t, "1", "RB%s" % t); setnet("Cbe%s" % t, "2", "GND")

        # --- trilhas locais (curtas, desenhadas) ---
        wire_pt("Q%sH" % t, "3", cx + 14.3, y + 15.5, "PH%s" % t, 1.5)
        seg(cx + 14.3, y + 15.5, cx + 12.3, y + 19.5, "PH%s" % t, W_PHASE)
        wire_pt("Q%sL" % t, "2", cx + 12.3, y + 19.5, "PH%s" % t, 1.5)
        wire_pt("Q%sL" % t, "3", cx + 14.3, y + 27.0, "SN%s" % t, 1.5)
        seg(cx + 14.3, y + 27.0, cx + 12.3, y + 31.0, "SN%s" % t, W_PHASE)
        wire_pt("Rs%s" % t, "1", cx + 12.3, y + 31.0, "SN%s" % t, 1.5)
        wire_pt("Rs%s" % t, "2", cx + 12, y + 38, "GND", 3.0)
        wire_pt("Q%sH" % t, "2", cx + 12, y + 1, "VBAT_PROT", W_VBAT)
        wire("U%s" % t, "7", "Rgo%s" % t, "1", "HO%s" % t, W_GATE)
        wire("U%s" % t, "5", "Rgf%s" % t, "1", "LO%s" % t, W_GATE)
        wire("U%s" % t, "6", "Q%sL" % t, "2", "PH%s" % t, 1.2)
        wire("U%s" % t, "4", "Rs%s" % t, "2", "GND", W_GATE)
        wire("Cb%s" % t, "2", "Q%sH" % t, "3", "PH%s" % t, W_GATE)
        wire("Rb1%s" % t, "1", "Q%sL" % t, "2", "PH%s" % t, W_DIV)

        # --- fase -> conector MR30 (B_Cu: 4 mm, afunila p/ 2 mm) ---
        nc = cx - CORR[ph]
        ny = y + 17.5
        via(cx + NODE_DX, y + 15.0, "PH%s" % t, 0.6, 1.2)
        via(cx + NODE_DX, ny, "PH%s" % t, 0.6, 1.2)
        via(cx + NODE_DX, y + 20.0, "PH%s" % t, 0.6, 1.2)
        seg(cx + NODE_DX, ny, nc, ny, "PH%s" % t, W_FASE_CU, pcbnew.B_Cu)
        seg(nc, ny, nc, 26.0, "PH%s" % t, W_FASE_CU, pcbnew.B_Cu)
        seg(nc, 26.0, nc, 21.0, "PH%s" % t, W_FASE_CU, pcbnew.B_Cu)
        seg(nc, 21.0, nc, 15.6, "PH%s" % t, W_FASE_PAD, pcbnew.B_Cu)
        seg(nc, 15.6, cx - ph * 3.5, 14.0, "PH%s" % t, W_FASE_PAD, pcbnew.B_Cu)
        # conector do motor
        jm = "J_M%d" % (mi + 1)
        if ph == 0:
            place("Connector_AMASS.pretty", "AMASS_MR30PW-FB_1x03_P3.50mm_Horizontal", jm, cx, 14)
        setnet(jm, str(ph + 1), "PH%s" % t)

print("clusters:", len(COL_X) * 3, "| footprints:", len(MODS))

# ================================================================
# ENTRADA / PROTECAO / BANCO
# ================================================================
place("Connector_AMASS.pretty", "AMASS_XT60-F_1x02_P7.20mm_Vertical", "J1", 30, 136)
place("Fuse.pretty", "Fuse_Blade_Mini_directSolder", "F1", 16, 126, 90)
place("Package_TO_SOT_SMD.pretty", "TO-252-2_TabPin1", "Q1", 46, 118)
place("Diode_SMD.pretty", "D_SMB", "D1", 24, 112)
place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rg1", 38, 118)
place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rz1", 42, 112)
place("Diode_SMD.pretty", "D_SOD-123", "Dz1", 34, 108)
for i in range(6):
    r, c = divmod(i, 2)
    place("Capacitor_SMD.pretty", "CP_Elec_8x10", "Cblk%d" % (i + 1), 20 + r * 14, 92 + c * 12)
    setnet("Cblk%d" % (i + 1), "1", "VBAT_PROT"); setnet("Cblk%d" % (i + 1), "2", "GND")
for i in range(4):
    r, c = divmod(i, 2)
    place("Capacitor_SMD.pretty", "C_1206_3216Metric", "Chf%d" % (i + 1), 52 + r * 6, 92 + c * 4)
    setnet("Chf%d" % (i + 1), "1", "VBAT_PROT"); setnet("Chf%d" % (i + 1), "2", "GND")

setnet("J1", "1", "VBAT"); setnet("J1", "2", "GND")
setnet("F1", "1", "VBAT"); setnet("F1", "2", "VBAT_F")
setnet("Q1", "2", "VBAT_F"); setnet("Q1", "1", "VBAT_PROT")
setnet("D1", "1", "VBAT_PROT"); setnet("D1", "2", "GND")
setnet("Rg1", "1", "PGATE"); setnet("Rg1", "2", "GND")
setnet("Dz1", "1", "PGATE"); setnet("Dz1", "2", "VBAT_F")
setnet("Rz1", "1", "VBAT_F"); setnet("Rz1", "2", "VBAT_PROT")   # ponte opcional (nao soldar)
seg(30, 136, 16, 136, "VBAT", 8.0)
seg(16, 136, 16, 129, "VBAT", 8.0)
seg(16, 123, 16, 118, "VBAT_F", 8.0)
seg(16, 118, 46, 118, "VBAT_F", 8.0)
seg(46, 122, 46, 112, "VBAT_PROT", 8.0)
for dx in (-2.0, 0.0, 2.0):
    for dy in (-2.0, 0.0, 2.0):
        via(46 + dx, 108 + dy, "VBAT_PROT", 0.6, 1.2)
seg(46, 112, 46, 106, "VBAT_PROT", 8.0)

# ================================================================
# BUCKS (CI nao escolhido na Fase 0 -> pads por FUNCAO)
# ================================================================
def buck(ref, y, vout):
    make_ic8("U%s" % ref, 24, y, ["BST", "IN", "EN", "FB", "SS", "GND", "SW", "VCC"],
             value="BUCK_%s" % vout)
    place("Inductor_SMD.pretty", "L_Bourns-SRN8040_8x8.15mm", "L%s" % ref, 36, y - 6)
    place("Capacitor_SMD.pretty", "C_1210_3225Metric", "Co%sa" % ref, 50, y - 2)
    place("Capacitor_SMD.pretty", "C_1210_3225Metric", "Co%sb" % ref, 50, y + 3)
    place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rf1%s" % ref, 30, y + 8)
    place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rf2%s" % ref, 34, y + 8)
    place("Capacitor_SMD.pretty", "C_0402_1005Metric", "Cbst%s" % ref, 17, y + 4)
    place("Capacitor_SMD.pretty", "C_0402_1005Metric", "Cin%s" % ref, 17, y - 2)
    wire("L%s" % ref, "2", "Co%sa" % ref, "1", vout, 0.6)
    wire("U%s" % ref, "SW", "L%s" % ref, "1", "SW%s" % ref, 1.2)
    wire("U%s" % ref, "FB", "Rf1%s" % ref, "1", "FB%s" % ref, W_DIV)
    wire("Rf1%s" % ref, "2", "Rf2%s" % ref, "1", "FB%s" % ref, W_DIV)
    wire("U%s" % ref, "BST", "Cbst%s" % ref, "1", "BST%s" % ref, W_DIV)
    wire("U%s" % ref, "GND", "Co%sa" % ref, "2", "GND", 0.6)
    setnet("L%s" % ref, "1", "SW%s" % ref)
    setnet("Co%sa" % ref, "2", "GND")
    setnet("Co%sb" % ref, "1", vout); setnet("Co%sb" % ref, "2", "GND")
    setnet("Rf1%s" % ref, "2", "FB%s" % ref)
    setnet("Rf2%s" % ref, "1", "FB%s" % ref); setnet("Rf2%s" % ref, "2", "GND")
    setnet("Cin%s" % ref, "2", "GND")
    setnet("Cbst%s" % ref, "2", "SW%s" % ref)

buck("B1", 48, "12V"); buck("B2", 60, "5V"); buck("B3", 72, "3V3")
setnets("UB1", {"IN": "VBAT_PROT", "EN": "VBAT_PROT", "VCC": "12V"})
setnets("UB2", {"IN": "12V", "EN": "12V", "VCC": "5V"})
setnets("UB3", {"IN": "5V_AUX", "EN": "5V_AUX", "VCC": "3V3"})
setnet("CinB1", "1", "VBAT_PROT")
setnet("CinB2", "1", "12V")
setnet("CinB3", "1", "5V_AUX")
for ref, vout in (("B1", "12V"), ("B2", "5V"), ("B3", "3V3")):
    setnet("Rf1%s" % ref, "1", vout)

for i, (nm, qtd) in enumerate([("12V", 2), ("5V", 2), ("3V3", 2), ("3V3_A", 1)]):
    for k in range(qtd):
        r = "Cout_%s%d" % (nm, k + 1)
        place("Capacitor_SMD.pretty", "C_1210_3225Metric", r, 62 + i * 10, 100 + k * 5)
        setnet(r, "1", nm); setnet(r, "2", "GND")

# ================================================================
# LDO 3,3 V_A (SOT-23-5 por funcao)
# ================================================================
make_sot23_5("U_LDO", 62, 78, ["VIN", "GND", "EN", "NC", "VOUT"], value="LDO_3V3A")
place("Capacitor_SMD.pretty", "C_0805_2012Metric", "Cldo_i", 56, 78)
place("Capacitor_SMD.pretty", "C_0805_2012Metric", "Cldo_o", 68, 78)
place("Inductor_SMD.pretty", "L_0805_2012Metric", "FLDO", 74, 78)
setnets("U_LDO", {"VIN": "3V3", "GND": "GND", "EN": "3V3", "VOUT": "3V3_A"})
setnet("Cldo_i", "1", "3V3"); setnet("Cldo_i", "2", "GND")
setnet("Cldo_o", "1", "3V3_A"); setnet("Cldo_o", "2", "GND")
setnet("FLDO", "1", "3V3_A"); setnet("FLDO", "2", "3V3_A_F")

# ================================================================
# ADC EXTERNO: 4x MCP3208 (1 por motor)
# pinout Microchip DS21298E: 1..8 = CH0..CH7, 9 DGND, 10 CS/SHDN, 11 DIN,
#                            12 DOUT, 13 CLK, 14 AGND, 15 VREF, 16 VDD
# ================================================================
for mi, cx in enumerate(COL_X):
    ref = "U%d" % (8 + mi)
    place("Package_SO.pretty", "SOIC-16_3.9x9.9mm_P1.27mm", ref, cx, 156, 90)
    canais = ["I_M%d01" % (mi + 1), "I_M%d02" % (mi + 1), "I_M%d03" % (mi + 1),
              "RB_M%d01" % (mi + 1), "RB_M%d02" % (mi + 1), "RB_M%d03" % (mi + 1)]
    mapa = {}
    for i, nm in enumerate(canais):
        mapa[str(i + 1)] = nm
    mapa.update({"9": "GND", "10": "ADC_CS%d" % (mi + 1), "11": "SPI_MOSI",
                 "12": "SPI_MISO", "13": "SPI_SCK", "14": "GND", "15": "3V3", "16": "3V3"})
    setnets(ref, mapa)
    cr = "Cadc%d" % (mi + 1)
    place("Capacitor_SMD.pretty", "C_0603_1608Metric", cr, cx + 8, 152)
    setnet(cr, "1", "3V3"); setnet(cr, "2", "GND")

# ================================================================
# MCU ESP32-S3-WROOM-1 + periferia
# ================================================================
m = make_module("U_MCU", 42, 152)
MCU_NETS = {
    "1": "GND", "2": "3V3", "3": "EN_MCU", "4": "PWM_M101", "5": "PWM_M102",
    "6": "PWM_M103", "7": "PWM_M201", "8": "PWM_M403", "9": "SPI_MOSI",
    "10": "SPI_SCK", "11": "SPI_MISO", "12": "PWM_M202", "13": "USB_DM",
    "14": "USB_DP", "15": "ADC_CS2", "16": "BUZZER", "17": "PWM_M203",
    "18": "PWM_M301", "19": "PWM_M302", "20": "PWM_M303", "21": "PWM_M401",
    "22": "PWM_M402", "23": "ADC_CS1", "24": "IMU_INT", "25": "WD_FEED",
    "26": "LED_K", "27": "BOOT_N", "31": "I2C_SDA", "32": "I2C_SCL",
    "33": "ADC_CS3", "34": "ADC_CS4", "35": "IMU_CS", "36": "UART_RX",
    "37": "UART_TX", "38": "TEMP_SENSE", "39": "VBAT_SENSE", "40": "GND", "41": "GND",
}
setnets("U_MCU", MCU_NETS)

place("Button_Switch_SMD.pretty", "SW_Push_1P1T_NO_CK_KMR2", "SW1", 20, 158)
place("Button_Switch_SMD.pretty", "SW_Push_1P1T_NO_CK_KMR2", "SW2", 20, 163)
setnet("SW1", "1", "BOOT_N"); setnet("SW1", "2", "GND")
setnet("SW2", "1", "EN_MCU"); setnet("SW2", "2", "GND")
for ref, x, y, a, b in [("RBOOT", 25, 150, "3V3", "BOOT_N"), ("REN", 25, 154, "3V3", "EN_MCU"),
                        ("RSDA", 31, 166, "3V3", "I2C_SDA"), ("RSCL", 37, 166, "3V3", "I2C_SCL"),
                        ("RVB1", 60, 148, "VBAT_PROT", "VBAT_SENSE"),
                        ("RT1", 64, 148, "3V3", "TEMP_SENSE")]:
    place("Resistor_SMD.pretty", "R_0603_1608Metric", ref, x, y)
    setnet(ref, "1", a); setnet(ref, "2", b)
place("Capacitor_SMD.pretty", "C_0402_1005Metric", "CEN", 25, 158)
setnet("CEN", "1", "EN_MCU"); setnet("CEN", "2", "GND")
place("Resistor_SMD.pretty", "R_0603_1608Metric", "RVB2", 60, 151)
setnet("RVB2", "1", "VBAT_SENSE"); setnet("RVB2", "2", "GND")
place("Capacitor_SMD.pretty", "C_0402_1005Metric", "CVB", 60, 154)
setnet("CVB", "1", "VBAT_SENSE"); setnet("CVB", "2", "GND")
place("Resistor_SMD.pretty", "R_0603_1608Metric", "NT1", 64, 151)
setnet("NT1", "1", "TEMP_SENSE"); setnet("NT1", "2", "GND")
place("LED_SMD.pretty", "LED_0805_2012Metric", "D_LED", 14, 150)
setnet("D_LED", "2", "3V3"); setnet("D_LED", "1", "LED_K")
place("Resistor_SMD.pretty", "R_0603_1608Metric", "Rled", 14, 153)
setnet("Rled", "1", "LED_K"); setnet("Rled", "2", "GND")

place("Buzzer_Beeper.pretty", "Buzzer_CUI_CPT-9019S-SMT", "BZ1", 62, 164)
place("Package_TO_SOT_SMD.pretty", "SOT-23", "Q_BZ", 74, 164)
place("Resistor_SMD.pretty", "R_0603_1608Metric", "RBZ", 68, 161)
setnet("BZ1", "1", "BUZZER"); setnet("BZ1", "2", "GND")
setnets("Q_BZ", {"1": "BUZZER", "2": "GND", "3": "VBZ"})
setnet("RBZ", "1", "VBZ"); setnet("RBZ", "2", "3V3")

for ref, nm, x in [("TP_12V", "12V", 96), ("TP_5V", "5V", 102), ("TP_3V3", "3V3", 108),
                   ("TP_3V3A", "3V3_A", 114), ("TP_GND", "GND", 120), ("TP_WD", "WD_FEED", 126),
                   ("TP_UART_TX", "UART_TX", 132), ("TP_UART_RX", "UART_RX", 138)]:
    place("TestPoint.pretty", "TestPoint_Pad_2.0x2.0mm", ref, x, 167)
    setnet(ref, "1", nm)

for i, (hx, hy) in enumerate([(14, 14), (226, 14), (14, 166), (226, 166)]):
    place("MountingHole.pretty", "MountingHole_3.2mm_M3", "H%d" % (i + 1), hx, hy)

# ================================================================
# USB-C + ESD
# ================================================================
place("Connector_USB.pretty", "USB_C_Receptacle_GCT_USB4085", "J2", 36, 24, 180)
place("Package_TO_SOT_SMD.pretty", "SOT-23-6", "U_ESD", 24, 20)
place("Resistor_SMD.pretty", "R_0603_1608Metric", "RCC1", 48, 20)
place("Resistor_SMD.pretty", "R_0603_1608Metric", "RCC2", 48, 23)
place("Diode_SMD.pretty", "D_SMB", "D2", 56, 20)
place("Diode_SMD.pretty", "D_SMB", "D3", 56, 28)
setnets("J2", {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
               "A4": "VBUS_USB", "A9": "VBUS_USB", "B4": "VBUS_USB", "B9": "VBUS_USB",
               "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP",
               "A7": "USB_DM", "B7": "USB_DM", "S1": "GND"})
setnets("U_ESD", {"1": "USB_DM", "2": "GND", "3": "USB_DP", "4": "USB_DP",
                  "5": "VBUS_USB", "6": "USB_DM"})
setnet("RCC1", "1", "CC1"); setnet("RCC1", "2", "GND")
setnet("RCC2", "1", "CC2"); setnet("RCC2", "2", "GND")
setnet("D2", "2", "VBUS_USB"); setnet("D2", "1", "5V_AUX")
setnet("D3", "2", "5V"); setnet("D3", "1", "5V_AUX")

# ================================================================
# IMU (ICM-42688-P, LGA-14, pinout datasheet TDK) + BAROMETRO (por funcao)
# ================================================================
place("Package_LGA.pretty", "LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y", "U_IMU", 20, 146, 90)
setnets("U_IMU", {"1": "SPI_MISO", "2": "GND", "3": "GND", "4": "IMU_INT",
                  "5": "3V3", "6": "GND", "7": "GND", "8": "3V3", "9": "GND",
                  "10": "GND", "11": "GND", "12": "IMU_CS", "13": "SPI_SCK",
                  "14": "SPI_MOSI"})
place("Capacitor_SMD.pretty", "C_0402_1005Metric", "CIMU", 26, 146)
setnet("CIMU", "1", "3V3"); setnet("CIMU", "2", "GND")
make_lga8("U_BARO", 62, 140, ["GND", "GND2", "SDI", "SCK", "SDO", "CSB", "VDDIO", "VDD"],
          value="BARO_I2C")
setnets("U_BARO", {"GND": "GND", "GND2": "GND", "SDI": "I2C_SDA", "SCK": "I2C_SCL",
                   "SDO": "GND", "CSB": "3V3", "VDDIO": "3V3", "VDD": "3V3"})

print("footprints totais:", len(MODS))

# ================================================================
# PLANOS + VIAS DE COSTURA
# ================================================================
mg = 1.0
zc = [(X0 + mg, Y0 + mg), (X0 + W - mg, Y0 + mg), (X0 + W - mg, Y0 + H - mg), (X0 + mg, Y0 + H - mg)]
zone("GND", pcbnew.In1_Cu, zc)
zone("GND", pcbnew.B_Cu, zc)
zone("VBAT_PROT", pcbnew.In2_Cu, zc)

def _seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    tt = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    qx, qy = x1 + tt * dx, y1 + tt * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5

blk = []
for tr in BRD.GetTracks():
    if tr.GetLayer() == pcbnew.B_Cu:
        s, e = tr.GetStart(), tr.GetEnd()
        blk.append((pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y),
                    pcbnew.ToMM(tr.GetWidth()) / 2.0 + 0.7))
pads_all = []
for fp in (BRD.GetFootprints() if hasattr(BRD, "GetFootprints") else BRD.GetModules()):
    for p in fp.Pads():
        c = p.GetPosition()
        pads_all.append((pcbnew.ToMM(c.x), pcbnew.ToMM(c.y),
                         max(pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y)) / 2.0 + 0.8))

nv = 0; nskip = 0
for yv in range(14, 166, 8):
    for xv in range(14, 226, 8):
        bad = False
        for (x1, y1, x2, y2, r) in blk:
            if _seg_dist(xv, yv, x1, y1, x2, y2) < r:
                bad = True; break
        if not bad:
            for (px, py, r) in pads_all:
                if abs(xv - px) < r and abs(yv - py) < r:
                    bad = True; break
        if bad:
            nskip += 1
        else:
            via(xv, yv, "GND"); nv += 1
print("vias de costura GND:", nv, "| posicoes puladas:", nskip)

filler = pcbnew.ZONE_FILLER(BRD); filler.Fill(BRD.Zones())
BRD.Save(OUT + "/v7_drone.kicad_pcb")
print("salvou", OUT + "/v7_drone.kicad_pcb")

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
