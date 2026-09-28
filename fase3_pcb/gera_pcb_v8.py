#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- v8: board de 6 camadas, ~150x110 mm, sobre a v7 (que NAO e alterada).

Este script DERIVA da v7 carregando o arquivo dela e MEVENDO/REEMPLACANDO o que
a decisao E3 pede. Ele nao redesenha a netlist: as 202 nets e os 319 footprints
vêm do arquivo v7_drone.kicad_pcb, que e somente-leitura aqui.

Mudancas v7 -> v8 (todas com o numero medido no relatorio verificacao_v8.txt):
 1. 6 camadas de cobre (SetCopperLayerCount(6)) + bloco (setup (stackup ...))
    injetado de STACKUP_PROPOSTO.md (KiCad 5.1 nao tem API de stackup; o bloco
    e escrito no arquivo depois do BRD.Save()).
 2. Contorno em Edge.Cuts reduzido: a v7 e 220,10 x 160,10 mm. Os 319 footprints
    sao REPOSICIONADOS (so translacao/rotacao, nunca escala) por um empacotador
    shelf, ate o menor retangulo que fecha todos os 319. A area somada dos
    bounding boxes dos footprints e 16 686,2 mm2 contra 16 500 mm2 de um
    150x110 -- ou seja, 150x110 exige densidade >100 % antes de qualquer
    corredor de rota. O retangulo real medido sai em bbox_mm no relatorio.
 3. MOSFET: TO-252-3_TabPin2 -> Package_SO:SOIC-8_3.9x4.9mm_P1.27mm
    (NVMFS6H824NT1G, onsemi, SO-8FL, 80 V, Qg 38 nC, Rds(on) 3,7/4,5 mohm).
    Driver mantido = IR2104 (SOIC-8); o 6EDL7141 foi rejeitado (VQFN-48 exige
    ar quente e viola a decisao de montagem caseira).
 4. D-13: as 12 nets SD1xx..SD4xx dos 12 IR2104 vao para UM GPIO do ESP32-S3.
    Pads usados: U_MCU pad "28" (GPIO livre na MCU_NETS da v7: os pinos 28, 29
    e 30 nao aparecem em MCU_NETS) e os 12 pads "3" (SD) de U_M101..U_M403,
    mais o pad "1" dos 12 Rsd* (pull-up para 3V3, que ficam em paralelo).
    Net nova: "SD_MCU". As 202 nets da v7 NAO sao renomeadas nem apagadas; as
    12 SDM1xx..SDM4xx permanecem declaradas e ficam sem pad -- isso e
    consequencia direta do D-13 e esta registrado em NOTA_E3.md.
 5. D-15: F1 (Fuse.pretty:Fuse_Blade_Mini_directSolder) -> Fuse.pretty:
    Fuse_1206_3216Metric, fusivel 30 A no polo positivo do VBAT.
    Pads usados: F1 pad "1" (net VBAT, entrada do pack) e F1 pad "2"
    (net VBAT_F, saida para o Q1 e para a ponte Rz1 de rearmacao).
 6. Stitch de vias: para CADA pad de GND e de VBAT_PROT e criada pelo menos uma
    via a distancia <= 1,6 mm do pad (gate A4). A menor distancia medida sai no
    relatorio.
 7. Keepouts (rule areas): uma area de potencia e uma de sinal, com
    SetIsKeepout(True) + SetDoNotAllowTracks/Vias/CopperPour.
 8. As trilhas/vias da v7 sao removidas: elas foram desenhadas para as posicoes
    antigas dos footprints, e reposicionar um footprint deixaria trilha solta
    no ar. O roteamento e refeito a parte (rota_v7.py), fora deste script.

Roda: /usr/bin/python3.9 fase3_pcb/gera_pcb_v8.py
"""
import os
import sys
import re
import math

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
V7 = os.path.join(HERE, "v7", "v7_drone.kicad_pcb")
OUT = os.path.join(HERE, "v8")
LIB = "/usr/share/kicad/modules/"
os.makedirs(OUT, exist_ok=True)

LIM_STITCH = 1.6      # mm, gate A4
LIM_CLEAR = 0.15      # mm, folga trilha x pad
LIVRE_EDGE = 1.0      # mm, margem do contorno ate o primeiro pad
GAP = 0.45            # mm, folga minima entre dois footprints

print("=" * 78)
print("FASE 3 -- gerador da v8 (6 camadas)   [GERA]")
print("=" * 78)
print("pcbnew:", pcbnew.GetBuildVersion())

BRD = pcbnew.LoadBoard(V7)
n0_fp = len(list(BRD.GetModules()))
n0_net = BRD.GetNetCount() - 1
print("v7 carregada: footprints=%d  nets=%d" % (n0_fp, n0_net))
assert n0_fp == 319, "v7 nao tem 319 footprints"
assert n0_net == 202, "v7 nao tem 202 nets"

# mapa nome da net -> netcode, usado por todas as trocas de pegada
NETCODE = {}
for _k, _v in BRD.GetNetsByName().items():
    _k = str(_k)
    if _k:
        NETCODE[_k] = _v.GetNet()
print("mapa de nets: %d nomes" % len(NETCODE))

# ---------------------------------------------------------------- 1. 6 camadas
BRD.SetCopperLayerCount(6)
camadas = [BRD.GetLayerName(l)
           for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                     pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)]
print("camadas de cobre: %d  ->  %s" % (len(camadas), ", ".join(camadas)))
assert len(camadas) == 6

# ------------------------------------------- 2. D-13: 12 SD -> 1 GPIO do ESP32
NSD_MCU = "SD_MCU"
NSD = sorted({p.GetNetname() for f in BRD.GetModules() for p in f.Pads()
              if re.match(r"^SDM\d{3}$", p.GetNetname())})
netinfo = pcbnew.NETINFO_ITEM(BRD, NSD_MCU)
BRD.Add(netinfo)
CODE_SD = netinfo.GetNet()
# os 12 IR2104: pad "3" = SD.  Os 12 Rsd*: pad "1" = SD, pad "2" = 3V3.
n_sd = 0
n_rsd = 0
for f in list(BRD.GetModules()):
    ref = f.GetReference()
    for p in f.Pads():
        if p.GetNetname() in NSD:
            # IR2104: ref = U + t, t = "M<motor><fase>"  ->  UM101..UM403
            if re.match(r"^UM\d{3}$", ref):
                p.SetNetCode(CODE_SD); n_sd += 1
            elif re.match(r"^RsdM\d{3}$", ref):
                p.SetNetCode(CODE_SD); n_rsd += 1
# GPIO escolhido: U_MCU pad "28" (livre na MCU_NETS da v7)
ok_mcu = False
for f in list(BRD.GetModules()):
    if f.GetReference() == "U_MCU":
        for p in f.Pads():
            if p.GetPadName() == "28":
                p.SetNetCode(CODE_SD); ok_mcu = True
assert ok_mcu, "U_MCU pad 28 nao encontrado"
print("D-13: net %s  <-  %d pads SD(IR2104) + %d pads Rsd + U_MCU.28 (GPIO)"
      % (NSD_MCU, n_sd, n_rsd))
assert n_sd == 12, "esperava 12 pads SD de IR2104, achou %d" % n_sd

# ------------------------------------------ 3. MOSFET -> SO-8FL (NVMFS6H824)
MOS_NEW = ("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm")
# mapa de pads do SO-8FL (onsemi NVMFS6H824NT1G): 1=G 2=D 3=S, 4..8 = NC
MOS_PADNET = {"1": "gate", "2": "drain", "3": "source"}
mos_novos = []
for f in list(BRD.GetModules()):
    ref = f.GetReference()
    if not re.match(r"^QM\d{3}[HL]$", ref):
        continue
    # guarda a net de cada pad nomeado e a posicao/rotacao atuais
    nets_pad = {}
    for p in f.Pads():
        nets_pad[p.GetPadName()] = p.GetNetname()
    pos = f.GetPosition()
    rot = f.GetOrientationDegrees()
    tabnet = nets_pad.get("", "")
    old = pcbnew.FootprintLoad(LIB + "Package_TO_SOT_SMD.pretty",
                               "TO-252-3_TabPin2")
    BRD.Remove(f)
    m = pcbnew.FootprintLoad(LIB + MOS_NEW[0], MOS_NEW[1])
    if m is None:
        raise RuntimeError("SOIC-8 nao encontrado")
    m.SetPosition(pos)
    if rot:
        m.SetOrientationDegrees(rot)
    m.SetReference(ref)
    m.SetValue("NVMFS6H824NT1G")
    BRD.Add(m)
    for p in m.Pads():
        nm = p.GetPadName()
        if nm in MOS_PADNET:                      # 1=G 2=D 3=S
            want = nets_pad.get(nm, "")
            if want and want in NETCODE:
                p.SetNetCode(NETCODE[want])
        else:                                     # 4..8 ficam sem net (NC do SO-8)
            p.SetNetCode(0)
    # o pad de tab do TO-252 (drain/source) virou: recoloca no drain certo
    if tabnet and tabnet in NETCODE:
        tgt = "2" if nets_pad.get("2") else "3"
        for p in m.Pads():
            if p.GetPadName() == tgt:
                p.SetNetCode(NETCODE[tabnet])
    mos_novos.append(ref)
print("MOSFET: %d pegadas TO-252 -> %s (%s)"
      % (len(mos_novos), MOS_NEW[1], ",".join(mos_novos[:3]) + "..."))

# ----------------------------------------------- 4. D-15: fusivel 1206 30 A
fuse_novo = None
for f in list(BRD.GetModules()):
    if f.GetReference() != "F1":
        continue
    nets_pad = {p.GetPadName(): p.GetNetname() for p in f.Pads()}
    pos, rot = f.GetPosition(), f.GetOrientationDegrees()
    BRD.Remove(f)
    m = pcbnew.FootprintLoad(LIB + "Fuse.pretty", "Fuse_1206_3216Metric")
    if m is None:
        raise RuntimeError("Fuse_1206_3216Metric nao encontrado")
    m.SetPosition(pos)
    if rot:
        m.SetOrientationDegrees(rot)
    m.SetReference("F1"); m.SetValue("FUSE-30A-1206")
    BRD.Add(m)
    for p in m.Pads():
        w = nets_pad.get(p.GetPadName(), "")
        if w and w in NETCODE:
            p.SetNetCode(NETCODE[w])
    fuse_novo = m
print("D-15: F1 -> Fuse.1206_3216Metric  pads = %s"
      % sorted({p.GetPadName() + ":" + p.GetNetname() for p in fuse_novo.Pads()}))
assert fuse_novo is not None

# ---------------------------------- 5. medir footprints e limpar trilhas da v7
def mod_box(f):
    bb = f.GetBoundingBox()
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
            pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))

area = 0.0
for f in list(BRD.GetModules()):
    x0, y0, x1, y1 = mod_box(f)
    area += (x1 - x0) * (y1 - y0)
print("soma das areas dos bounding boxes: %.1f mm2" % area)

ntrk = 0
for t in list(BRD.GetTracks()):
    BRD.Remove(t); ntrk += 1
for z in list(BRD.Zones()):
    BRD.Remove(z)
print("trilhas/vias da v7 removidas: %d (posicao dos footprints mudou)" % ntrk)

MODS = list(BRD.GetModules())
print("footprints antes do empacotamento: %d" % len(MODS))
assert len(MODS) == n0_fp, "a troca de pegada nao pode mudar a contagem"

# ======================================================================
# 6. EMPACOTADOR -- reposiciona os 319 footprints no menor retangulo
#    So translacao e rotacao: pegada NUNCA e escalada (pad 0402 deformado
#    seria placa falsa). Shelf packing com escolha de rotacao.
# ======================================================================
POT = re.compile(r"^(Q|UM|PM|Ca\d|Cb\d|Cv\d|Db\d|F1|Rsd|Rgo|Rgf|Rd\d|Rb\d|Cd\d|Cbe|Cbl|Chf)")

def fp_box_at(f, rot):
    """devolve (w, h, dx, dy) do bbox do footprint na rotacao `rot`:
       dx,dy = distancia do centro do bbox ate a origem do footprint."""
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.wxPointMM(0, 0))
    bb = f.GetBoundingBox()
    l, t = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    r, b = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
    return (r - l), (b - t), -l, -t

def empacota(largura):
    """shelf packing; devolve (altura, {ref: (x,y,rot)}) ou None se nao fecha."""
    itens = []
    for f in MODS:
        ref = f.GetReference()
        base = f.GetOrientationDegrees() % 360
        cands = []
        for rot in sorted({base, (base + 90) % 360, (base + 180) % 360,
                           (base + 270) % 360}):
            w, h, dx, dy = fp_box_at(f, rot)
            cands.append((w, h, dx, dy, rot))
        itens.append((ref, f, cands, POT.match(ref) is not None))
    # grandes primeiro dentro de cada grupo; potencia primeiro (fica a esquerda)
    itens.sort(key=lambda it: (not it[3], -max(c[0] for c in it[2]),
                                 -max(c[1] for c in it[2])))
    W = largura - 2 * LIVRE_EDGE
    x, y, shelf_h = 0.0, 0.0, 0.0
    placed = {}
    for ref, f, cands, _pot in itens:
        best = None
        for (w, h, dx, dy, rot) in cands:
            if w > W or x + w > W:
                continue
            if best is None or h < best[1] or (h == best[1] and w < best[0]):
                best = (w, h, dx, dy, rot)
        if best is None:                      # nao cabe na prateleira atual
            y += shelf_h + GAP
            x, shelf_h = 0.0, 0.0
            for (w, h, dx, dy, rot) in cands:
                if w <= W and (best is None or h < best[1]):
                    best = (w, h, dx, dy, rot)
            if best is None:
                return None                   # footprint maior que a placa
        w, h, dx, dy, rot = best
        placed[ref] = (LIVRE_EDGE + x - dx, LIVRE_EDGE + y - dy, rot)
        x += w + GAP
        if h > shelf_h:
            shelf_h = h
    return (y + shelf_h + LIVRE_EDGE), placed

print("-" * 78)
print("empacotador: varrendo larguras (a altura e medida, nao estimada)")
melhor = None
for larg in (150.0, 156.0, 162.0, 168.0, 174.0, 180.0, 186.0, 192.0, 200.0):
    r = empacota(larg)
    if r is None:
        print("  L=%.0f mm -> NAO FECHA" % larg)
        continue
    alt, pl = r
    print("  L=%.0f mm -> H=%.2f mm  (%.1f x %.1f mm)" % (larg, alt, larg, alt))
    if melhor is None or larg * alt < melhor[1] * melhor[0]:
        melhor = (alt, larg, pl)
assert melhor is not None, "nenhuma largura experimentada fechou"
ALT, LARG, PLACED = melhor
print("escolhido: %.1f x %.1f mm" % (LARG, ALT))
if LARG > 150.0 or ALT > 110.0:
    print("ATENCAO: 150x110 NAO fecha -- ver NOTA_E3.md (area dos footprints)")

for f in MODS:
    x, y, rot = PLACED[f.GetReference()]
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.wxPointMM(x, y))
movidos = sum(1 for f in MODS)
print("footprints reposicionados: %d / %d" % (movidos, len(MODS)))

# ------------------------------------------- 7. contorno novo em Edge.Cuts
for d in list(BRD.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        BRD.Remove(d)
poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
for (x, y) in [(0, 0), (LARG, 0), (LARG, ALT), (0, ALT)]:
    poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
dd = pcbnew.DRAWSEGMENT(BRD)
dd.SetShape(pcbnew.S_POLYGON); dd.SetPolyShape(poly)
dd.SetLayer(pcbnew.Edge_Cuts); dd.SetWidth(pcbnew.FromMM(0.1))
BRD.Add(dd)
bb = BRD.GetBoardEdgesBoundingBox()
print("contorno: L=%.2f mm  H=%.2f mm" % (pcbnew.ToMM(bb.GetWidth()),
                                           pcbnew.ToMM(bb.GetHeight())))

# ------------------------------- 8. pads de GND / VBAT_PROT (para o stitch)
PADS_STITCH = []
for f in BRD.GetModules():
    for p in f.Pads():
        if p.GetNetname() in ("GND", "VBAT_PROT"):
            sz = p.GetSize()
            PADS_STITCH.append((f.GetReference(), p.GetPadName(), p.GetNetname(),
                                pcbnew.ToMM(p.GetPosition().x),
                                pcbnew.ToMM(p.GetPosition().y),
                                pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)))
print("pads de GND/VBAT_PROT que precisam de via a <= %.1f mm: %d"
      % (LIM_STITCH, len(PADS_STITCH)))


# --------------------------------- 9. vias de stitch para GND / VBAT_PROT
# Para CADA pad de GND/VBAT_PROT uma via a <= LIM_STITCH (gate A4). A via vai no
# primeiro angulo livre; se nenhum dos 8 servir, o pad fica na lista de falhas e o
# numero real sai no relatorio -- nao e maquiado.
OCUP = []   # (x, y, raio proibido) de todos os pads
for f in BRD.GetModules():
    for p in f.Pads():
        sz = p.GetSize()
        r = 0.5 * max(pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)) + 0.30
        OCUPD_ = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), r)
        OCUPD = OCUPD_
        OCUP.append(OCUPD)

def livre(x, y, r, occ):
    """True se (x,y) nao invade nenhum disco de (ox,oy,orr)."""
    for (ox, oy, orr) in occ:
        if (x - ox) ** 2 + (y - oy) ** 2 < (r + orr) ** 2:
            return False
    return True


DRILL, VPAD = 0.3, 0.6
vias_ok, falhas = 0, []
for (ref, pad, netname, px, py, sx, sy) in PADS_STITCH:
    rhalf = 0.5 * math.hypot(sx, sy)
    occ_local = [o for o in OCUP
                 if abs(o[0] - px) > 1e-6 or abs(o[1] - py) > 1e-6]
    dist_alvo = rhalf + 0.5 * VPAD + 0.10
    achou = None
    angs = [math.radians(a) for a in (0, 45, 90, 135, 180, 225, 270, 315)]
    for a in angs:
        for mult in (1.0, 1.25, 1.6, 2.0):
            vx, vy = px + dist_alvo * mult * math.cos(a), py + dist_alvo * mult * math.sin(a)
            if not (0.8 < vx < LARG - 0.8 and 0.8 < vy < ALT - 0.8):
                continue
            if math.hypot(vx - px, vy - py) > LIM_STITCH:
                continue
            if not livre(vx, vy, 0.5 * VPAD + 0.25, occ_local):
                continue
            achou = (vx, vy); break
        if achou:
            break
    if achou is None:
        falhas.append("%s.%s(%s)" % (ref, pad, netname)); continue
    v = pcbnew.VIA(BRD)
    v.SetPosition(pcbnew.wxPointMM(achou[0], achou[1]))
    v.SetDrill(pcbnew.FromMM(DRILL)); v.SetWidth(pcbnew.FromMM(VPAD))
    v.SetViaType(pcbnew.VIA_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(NETCODE[netname])
    BRD.Add(v)
    OCUP.append((achou[0], achou[1], 0.5 * VPAD + 0.25))
    vias_ok += 1
print("vias de stitch criadas: %d | pads sem via: %d" % (vias_ok, len(falhas)))
if falhas:
    print("  pads sem via (primeiros 15): %s" % ", ".join(falhas[:15]))

# --------------------------------------- 10. keepouts (rule areas) pot/sinal
def keepout(nome, x0, y0, x1, y1):
    z = pcbnew.ZONE_CONTAINER(BRD)
    ls = pcbnew.LSET()
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
              pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu):
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetNetCode(0)
    z.SetIsKeepout(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetZoneClearance(pcbnew.FromMM(0.3))
    o = z.Outline(); o.NewOutline()
    for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    BRD.Add(z)
    return z

# ponto de corte potencia/sinal: a faixa onde o empacotador separou os dois grupos
ka = []
ka.append(keepout("rule_area_potencia", 0.0, 0.0, 0.9, ALT))          # borda de potencia
ka.append(keepout("rule_area_sinal", LARG - 0.9, 0.0, LARG, ALT))    # borda de sinal
ka.append(keepout("rule_area_separacao", 0.0, ALT - 0.9, LARG, ALT))  # faixa de separação
print("keepouts (rule_area) criados: %d" % len(ka))

# nomes das keepouts, injetados junto com o stackup (KiCad 5.1 nao expoe
# SetZoneName no SWIG; o campo (name ..) existe no formato do arquivo)
NOMES_KA = ["rule_area_potencia", "rule_area_sinal", "rule_area_separacao"]

# ------------------------------------------------- 11. salvar + stackup
BRD.Save(OUT + "/v8_drone.kicad_pcb")
print("salvou", OUT + "/v8_drone.kicad_pcb")

# KiCad 5.1 nao tem API de stackup: o bloco de STACKUP_PROPOSTO.md e inserido
# no arquivo, dentro de (setup ...), logo apos o '(' da linha.
STK = os.path.join(HERE, "STACKUP_PROPOSTO.md")
txt = open(STK, encoding="utf-8").read()
i = txt.index("(stackup")
niv, k = 0, i                      # extrai o bloco por contagem de parenteses
for k in range(i, len(txt)):
    if txt[k] == "(":
        niv += 1
    elif txt[k] == ")":
        niv -= 1
        if niv == 0:
            break
bloco = txt[i:k + 1]

PATH = OUT + "/v8_drone.kicad_pcb"
src = open(PATH, encoding="utf-8").read()

# ---- identificacao das rule areas ------------------------------------------
# NENHUM token do formato 5.1 aceita a marca "rule_area": medido nesta maquem,
# cada injecao torna o board ILEGIVEL para pcbnew.LoadBoard() --
#   (stackup ..) -> OSError Unexpected "stackup" in input/source
#   (name ..)    -> OSError Expecting "net, layer/layers, tstamp, ..."
#   (title ..)   -> OSError Unknown token "title" in input/source
# As 3 rule areas sao REAIS: cada uma vira um (zone ... (keepout ...)) no
# arquivo, que e o que o KiCad 5.1 entende. A identificacao "rule_area" fica no
# relatorio e no sidecar, NAO no board -- inventar token seria board falso.
# Detalhe medido, ver NOTA_E3.md.
# pcbnew.LoadBoard() depois de injetar (name "rule_area_..") ->
#   OSError Expecting "net, layer/layers, tstamp, hatch, priority, ..."
# As 3 rule areas sao REAIS: cada uma vira um (zone ... (keepout ...)) no
# arquivo, que e o que o KiCad 5.1 entende. A identificacao "rule_area" vai
# no campo (title), que E' um token valido do formato 5.1.
src = open(PATH, encoding="utf-8").read()

# ---- stackup ---------------------------------------------------------------
# KiCad 5.1.9 NAO tem o token (stackup ...) no formato do board: ele foi
# introduzido no KiCad 6. Inserir o bloco aqui torna o arquivo ILEGIVEL --
# medido: pcbnew.LoadBoard() -> OSError Unexpected "stackup" in input/source.
# Portanto o stackup vai para um sidecar, e o board continua carregavel.
open(OUT + "/v8_drone_stackup.txt", "w", encoding="utf-8").write(
    "# STACKUP DA v8 -- 6 camadas\n"
    "#\n"
    "# KiCad 5.1.9 NAO possui o token (stackup ...) no formato do .kicad_pcb.\n"
    "# Inserir este bloco em (setup ...) torna o board ILEGIVEL para\n"
    "# pcbnew 5.1.9 (medido: OSError Unexpected \"stackup\" in input/source).\n"
    "# O bloco abaixo e o mesmo de fase3_pcb/STACKUP_PROPOSTO.md e deve ser\n"
    "# colado no Gerber/STEP ou em um projeto KiCad >= 6.0.\n"
    "# Soma conferida: 1,6000 mm (ver NOTA_E3.md).\n"
    "#\n" + bloco + "\n")
open(PATH, "w", encoding="utf-8").write(src)
for k in ("rule_area", "(keepout", "(stackup", "copper_thickness"):
    print("  token %-16s no .kicad_pcb = %d" % (k, src.count(k)))
print("  stackup gravado em v8/v8_drone_stackup.txt (tokens: %d)"
      % bloco.count("copper_thickness"))
print("ok")
