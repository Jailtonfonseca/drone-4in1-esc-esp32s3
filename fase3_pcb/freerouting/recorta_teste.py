#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
recorta_teste.py -- Gera um sub-board de teste (corte do design) para validar o
pipeline DSN/SES ponta a ponta sem mexer no board original.

Corte: bloco do motor 4 (driver UB4 + 3 MOSFETs de meio-ponte + gate resistors + bulk).
Uso:  /usr/bin/python3.9 recorta_teste.py v8_drone.kicad_pcb corte_motor4.kicad_pcb
"""
import sys
import pcbnew

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    "/opt/jupyter/work/drone/fase3_pcb/v8/v8_drone.kicad_pcb"
DST = sys.argv[2] if len(sys.argv) > 2 else \
    "/opt/jupyter/work/drone/fase3_pcb/freerouting/teste/corte_motor4.kicad_pcb"

# refs do bloco do motor 4 (bridge 3-fase + 3 MOSFETs de alto lado)
REFS = set()
for n in (401, 402, 403):
    for suf in ("H", "L"):
        REFS.add("QM%d%s" % (n, suf))
for n in (401, 402, 403):
    REFS.add("UM%d" % n)
    REFS.add("UaM%d" % n)
    REFS.add("DbM%d" % n)
REFS.add("UB4")
REFS.add("Q_BZ")
REFS.add("CbstB")
REFS.add("RgfB")
REFS.add("RgB")

board = pcbnew.LoadBoard(SRC)

kept = 0
for m in list(board.GetModules()):
    if str(m.GetReference()) in REFS:
        kept += 1
    else:
        board.Remove(m)

# remove trilhas e zonas do original: o teste e do zero
for t in list(board.GetTracks()):
    board.Remove(t)
for z in list(board.Zones()):
    board.Remove(z)

# recorta o Edge.Cuts para a bbox dos componentes restantes
bb = None
for m in board.GetModules():
    r = m.GetBoundingBox()
    bb = r if bb is None else (bb.Merge(r) or bb)

# reconstroi as 4 linhas de contorno em volta dos componentes
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)

if bb is not None:
    x1, y1 = bb.GetX() / 1e6, bb.GetY() / 1e6
    x2 = (bb.GetX() + bb.GetWidth()) / 1e6
    y2 = (bb.GetY() + bb.GetHeight()) / 1e6
    m = 2.0
    x1, y1, x2, y2 = x1 - m, y1 - m, x2 + m, y2 + m
    for (a, b2, c, d2) in [(x1, y1, x2, y1), (x2, y1, x2, y2),
                           (x2, y2, x1, y2), (x1, y2, x1, y1)]:
        seg = pcbnew.DRAWSEGMENT(board)
        seg.SetShape(pcbnew.S_SEGMENT)
        seg.SetStart(pcbnew.wxPointMM(a, b2))
        seg.SetEnd(pcbnew.wxPointMM(c, d2))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(int(0.1 * 1e6))
        board.Add(seg)

pcbnew.SaveBoard(DST, board)

chk = pcbnew.LoadBoard(DST)
n = len(list(chk.GetModules()))
npin = sum(len(list(mm.Pads())) for mm in chk.GetModules())
nets = set()
for mm in chk.GetModules():
    for p in mm.Pads():
        if str(p.GetNetname()):
            nets.add(str(p.GetNetname()))
print("corte salvo: %s" % DST)
print("  modulos     : %d" % n)
print("  pads        : %d" % npin)
print("  nets com pad: %d" % len(nets))
bbx = chk.GetBoardEdgesBoundingBox()
print("  bbox mm     : %.1f x %.1f" % (bbx.GetWidth() / 1e6, bbx.GetHeight() / 1e6))
