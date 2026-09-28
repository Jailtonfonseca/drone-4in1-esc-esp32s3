#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
V8 -- exporta o .kicad_pcb para DSN (Specctra) a mao, para o FreeRouting.

POR QUE A MAO: o pcbnew 5.1.9 (medido) NAO expoe nenhuma funcao de DSN --
    $ /usr/bin/python3.9 -c "import pcbnew; print(hasattr(pcbnew,'ExportSpecctraDSN'))"
    False
e tambem nao ha `kicad-cli` nesta maquina. O formato DSN e texto, entao ele e
gerado direto do board pelo modulo pcbnew 5.1.9 (que le e understande o arquivo
proprio) e escrito no formato aceito pelo FreeRouting 1.9.0.

O formato de referencia foi conferido contra o proprio DSN de teste do
FreeRouting (tests/Issue107-freq_teiler_200kHz_kicad.dsn, v1.9.0):
  - (resolution um 10) e (unit um): coordenadas em micrometros com 1 casa
  - (boundary (path pcb 0  x1 y1  x2 y2 ...)): coordenadas INLINE, nao (xy ..)
  - (placement (component "LIB:FP" (place REF x y front 0 (PN PART))))
  - (library (image "LIB:FP" (outline (path signal W x1 y1 x2 y2))
      (pin TIPO[NOME] 1 dx dy)))
  - (network (net NOME (pins REF-PAD ...)))
  - (class nome "" N1 N2 ...)

Roda: /usr/bin/python3.9 fase3_pcb/v8/gera_dsn_v8.py [entrada.kicad_pcb] [saida.dsn]
"""
import os
import sys
import re
import math

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "v8_drone.kicad_pcb")
DSN = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "v8_drone.dsn")

# --- largura de trilha por net, em micrometros -------------------------------
# 2 oz = 0,0700 mm de cobre (Tarefa 0). Os valores sao IPC-2221 dT=10 C
# conferidos contra calc_trilhas_vias_saida.txt:
#   15 A -> 6,29 mm ; 7,5 A -> 2,42 mm ; 2,0 A -> 0,391 mm ; 0,6 A -> 0,074 mm
# O piso e 0,20 mm (sinal) ou o menor valor que a corrente exige, o que for maior.
POT_LARG = {
    "VBM": 6.29,        # 12 nets VBM101..403: fase do motor, 15 A RMS
    "VBAT_F": 2.42,     # 7,5 A continuo
    "VBAT_SENSE": 0.20, # 0,1 A: piso de sinal domina
    "12V": 0.20,        # 0,6 A: piso de sinal domina
    "5V": 0.391,        # 2,0 A
    "5V_AUX": 0.20,
    "3V3": 0.263,       # 1,5 A
    "3V3_A": 0.263,     # 1,5 A
}
SINAL_W = 0.20
CLEAR_MM = 0.15
VIA_D = 0.60
VIA_DR = 0.30
# camadas roteaveis: os 3 planos internos (In1, In3, In4) ficam fora do DSN --
# sao plano de GND/VBAT, nao trilhas
LAYERS_R = ["F.Cu", "In2.Cu", "B.Cu"]
LAYERS_R_IDX = {"F.Cu": 0, "In1.Cu": 1, "In2.Cu": 2, "In3.Cu": 3,
                "In4.Cu": 4, "B.Cu": 5}


def larg_mm(netname):
    if netname in POT_LARG:
        return POT_LARG[netname]
    for pfx, v in POT_LARG.items():
        if pfx.endswith("M") and netname.startswith("VBM"):
            return v
        if netname.startswith("RB_M"):
            return v
    return SINAL_W


def um(mm):
    """mm -> micrometros com 1 casa (resolucao (um 10) do DSN)."""
    return int(round(mm * 1000.0))


BRD = pcbnew.LoadBoard(PCB)
print("pcbnew:", pcbnew.GetBuildVersion())
print("board :", PCB)

# ---------------------------------------------------------------- contorno
bb = BRD.GetBoardEdgesBoundingBox()
W = pcbnew.ToMM(bb.GetWidth())
H = pcbnew.ToMM(bb.GetHeight())
print("bbox  : %.2f x %.2f mm" % (W, H))

# ponto de referencia do FreeRouting: canto do bbox
X0 = bb.GetX()
Y0 = bb.GetY()
# KiCad usa Y para baixo; o FreeRouting tambem aceita, mas para nao embaralhar
# as camadas, uso a mesma convencao de Y do KiCad (mesmo sinal, mesma origem).


def q(s):
    return '"' + str(s).replace('"', "'") + '"'


# ------------------------------------------------------------------ camadas
L = []
L.append("(pcb %s" % q(PCB))
L.append("  (parser")
L.append('    (string_quote ")')
L.append("    (space_in_quoted_tokens on)")
L.append("    (host_cad \"KiCad's Pcbnew\")")
L.append('    (host_version "(5.1.9)-1")')
L.append("    )")
L.append("  (resolution um 10)")
L.append("  (unit um)")
L.append("  (structure")
for lay in LAYERS_R:
    L.append("    (layer %s" % lay)
    L.append("      (type signal)")
    L.append("      (property")
    L.append("        (index %d)" % LAYERS_R_IDX[lay])
    L.append("        )")
    L.append("      )")

# contorno: um unico path fechado, como o KiCad 5.1 escreve
pts = []
for e in BRD.GetDrawings():
    if e.GetLayerName() != "Edge.Cuts":
        continue
    st = e.GetShape()
    if st == pcbnew.S_SEGMENT:
        pts.append(((pcbnew.ToMM(e.GetStart().x), pcbnew.ToMM(e.GetStart().y)),
                    (pcbnew.ToMM(e.GetEnd().x), pcbnew.ToMM(e.GetEnd().y))))
    elif st == 4:                 # contorno desenhado como gr_poly
        vs = e.GetPolyShape().Outline(0)
        n = vs.PointCount()
        ring = [(pcbnew.ToMM(vs.CPoint(k).x), pcbnew.ToMM(vs.CPoint(k).y))
                for k in range(n)]
        if ring and ring[0] == ring[-1]:
            ring = ring[:-1]
        ANEL_DIRETO = ring
        print("   gr_poly: %d vertices" % len(ring))
    elif st == pcbnew.S_CIRCLE:
        cx, cy, r = pcbnew.ToMM(e.GetCenter().x), pcbnew.ToMM(e.GetCenter().y), pcbnew.ToMM(e.GetRadius())
        for k in range(33):
            a = 2 * math.pi * k / 32.0
            pts.append(((cx + r * math.cos(a), cy + r * math.sin(a)), None))
# junta as pontas: monta o loop percorrendo segmentos encadeados

def encadeia(pts):
    """une os segmentos de Edge.Cuts num anel unico (DSN aceita 1 shape)."""
    if not pts:
        return []
    from collections import defaultdict
    g = defaultdict(list)
    deg = defaultdict(int)
    def R(x, y):
        return (round(x, 4), round(y, 4))
    for seg in pts:
        if seg[1] is None:
            continue
        (x1, y1), (x2, y2) = seg
        a, b = R(x1, y1), R(x2, y2)
        g[a].append(b)
        g[b].append(a)
        deg[a] += 1
        deg[b] += 1
    # ponto mais a esquerda/baixo como inicio
    start = min(deg, key=lambda p: (p[0], p[1]))
    ring = [start]
    cur = start
    usado = set()
    while True:
        prox = None
        for c in g[cur]:
            if (cur, c) not in usado:
                prox = c
                break
        if prox is None:
            break
        usado.add((cur, prox))
        ring.append(prox)
        cur = prox
        if cur == start:
            break
    return ring


ring = globals().get("ANEL_DIRETO") or encadeia(pts)
if ring and ring[0] == ring[-1]:
    ring = ring[:-1]
if len(ring) < 4:
    sys.exit("ERRO: contorno nao fechou (ring=%d)" % len(ring))
print("contorno: %d vertices" % len(ring))
flat = []
for (x, y) in ring:
    flat.append("%d %d" % (um(x - pcbnew.ToMM(X0)), um(y - pcbnew.ToMM(Y0))))
L.append("    (boundary")
L.append("      (path pcb 0  " + "  ".join(flat) + ")")
L.append("      )")
L.append("    (via \"Via_600_um\" \"Via_600_um\")")
L.append("    (rule")
L.append("      (width %d)" % um(SINAL_W))
L.append("      (clearance %d)" % um(CLEAR_MM))
L.append("      (clearance %d (type default_smd))" % um(CLEAR_MM))
L.append("      )")
L.append("    )")
L.append("  )")

# --------------------------------------------------------------- footprints
MODS = list(BRD.GetModules())
COMP = {}     # refdes -> (libid, x, y, rot, side)
NETPADS = {}  # refdes -> [(padname, netname, dx, dy, shape, w, h, layers)]
FP = {}       # libid -> {padname: (shape, w, h, layers, dx, dy)}

for m in MODS:
    ref = m.GetReference()
    libid = m.GetFPID().GetLibItemName().wx_str() + "|" + m.GetFPID().GetLibNickname().wx_str()
    libid = str(libid, "utf-8") if not isinstance(libid, str) else libid
    pos = m.GetPosition()
    mx, my = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
    rot = m.GetOrientationDegrees() % 360.0
    side = "back" if m.IsFlipped() else "front"
    COMP[ref] = (libid, mx, my, rot, side)
    d = FP.setdefault(libid, {})
    pads = []
    for p in m.Pads():
        nm = p.GetName()
        pp = p.GetPosition()
        dxx, dyy = pcbnew.ToMM(pp.x - pos.x), pcbnew.ToMM(pp.y - pos.y)
        sw, sh = pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y)
        shp = str(p.GetShape()).split(".")[-1].replace("PAD_SHAPE_", "")
        lays = []
        lset = p.GetLayerSet()
        names = []
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            if i in lset.Seq():
                nmL = BRD.GetLayerName(i)
                if nmL in LAYERS_R:
                    names.append(nmL)
        netnm = p.GetNetname() or ""
        pads.append((nm, netnm, dxx, dyy, shp, sw, sh, names))
        d[nm] = (shp, sw, sh, names, dxx, dyy)
    NETPADS[ref] = pads

print("footprints: %d   libs distintas: %d" % (len(MODS), len(FP)))

L.append("  (placement")
porlib = {}
for ref, (libid, mx, my, rot, side) in sorted(COMP.items()):
    porlib.setdefault(libid, []).append(ref)
for libid, refs in sorted(porlib.items()):
    L.append("    (component %s" % q(libid))
    for ref in refs:
        _, mx, my, rot, side = COMP[ref]
        L.append("      (place %s %d %d %s %d)"
                 % (ref, um(mx - pcbnew.ToMM(X0)), um(my - pcbnew.ToMM(Y0)),
                    side, int(round(rot))))
    L.append("      )")
L.append("    )")

L.append("  (library")
for libid in sorted(FP):
    L.append("    (image %s" % q(libid))
    for nm, (shp, sw, sh, names, dx, dy) in sorted(FP[libid].items()):
        lay = names[0] if names else "F.Cu"
        L.append("      (pin R[%s] 1 %d %d)" % (nm, um(dx), um(dy)))
    L.append("      )")
L.append("  )")

# --------------------------------------------------------------------- nets
nets = {}
for ni in range(BRD.GetNetCount()):
    nd = BRD.FindNet(ni)
    nets[ni] = nd.GetNetname()
print("nets no board: %d" % len(nets))

nodos = {}
for ref, pads in NETPADS.items():
    for (nm, netnm, dx, dy, shp, sw, sh, names) in pads:
        if not netnm or netnm not in nets.values():
            continue
        if not names:
            continue
        nodos.setdefault(netnm, []).append("%s-%s" % (ref, nm))

L.append("  (network")
for netnm in sorted(nodos):
    ns = nodos[netnm]
    if len(ns) < 2:
        continue
    L.append("    (net %s" % q(netnm))
    L.append("      (pins " + " ".join(ns) + ")")
    L.append("      )")
L.append("  )")

# classes: uma por largura de trilha (o FreeRouting usa a class p/ a largura)
grupos = {}
for netnm in nodos:
    if len(nodos[netnm]) < 2:
        continue
    grupos.setdefault(round(larg_mm(netnm), 3), []).append(netnm)
L.append("  (class")
for w in sorted(grupos):
    L.append("    (class w%s %s  %s)"
             % (str(w).replace(".", "_"),
                " ".join(q(n) for n in sorted(grupos[w])),
                ""))
    L.append("      (circuit 0)")
    L.append("      (width %d)" % um(w))
    L.append("      (clearance %d)" % um(CLEAR_MM))
    L.append("      (via_dia %d)" % um(VIA_D))
    L.append("      (via_drill %d)" % um(VIA_DR))
    L.append("      )")
L.append("  )")
L.append("  )")

open(DSN, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("DSN gravado:", DSN, os.path.getsize(DSN), "bytes")
print("classes de largura:")
for w in sorted(grupos):
    print("   %.3f mm -> %d nets" % (w, len(grupos[w])))
