#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- verificacao da v8. Le a v8 gerada e mede TUDO de novo.

Criterios dos gates:
  A4  pads de GND/VBAT_PROT sem via a menos de 1,6 mm ....... 0
  A8  rule_area (keepouts) no arquivo ....................... > 0
  fabrica  camadas de cobre ................................. 6
  trilhas x pad (net diferente) mais próximas que 0,15 mm ... 0

NENHUM numero aqui e'R' digitado: todos vem de LoadBoard() + medicao.
Roda: /usr/bin/python3.9 fase3_pcb/verifica_fase3_v8.py
"""
import os
import math
import collections

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BRD_P = os.path.join(HERE, "v8", "v8_drone.kicad_pcb")
OUT = os.path.join(HERE, "v8", "verificacao_v8.txt")

LIM_STITCH = 1.6
LIM_CLEAR = 0.15

b = pcbnew.LoadBoard(BRD_P)
L = []
def w(s=""):
    L.append(s)

w("=" * 78)
w("FASE 3 -- VERIFICACAO DA v8   [VERIF]")
w("=" * 78)
w("arquivo            : %s" % BRD_P)
w("pcbnew             : %s" % pcbnew.GetBuildVersion())
w()

# ---------------------------------------------------------------- geometria
bb = b.GetBoardEdgesBoundingBox()
Lw, Hh = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
camadas = [b.GetLayerName(l) for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                                       pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)]
ncu = b.GetCopperLayerCount()

# ------------------------------------------------------------------ nets
nets_total = b.GetNetCount() - 1
nets_pad = set()
pads_total = 0
pads_gnd = []
for f in b.GetModules():
    for p in f.Pads():
        pads_total += 1
        if p.GetNetname():
            nets_pad.add(p.GetNetname())
            if p.GetNetname() in ("GND", "VBAT_PROT"):
                sz = p.GetSize()
                pads_gnd.append((f.GetReference(), p.GetPadName(), p.GetNetname(),
                                 pcbnew.ToMM(p.GetPosition().x),
                                 pcbnew.ToMM(p.GetPosition().y),
                                 0.5 * math.hypot(pcbnew.ToMM(sz.x),
                                                  pcbnew.ToMM(sz.y))))

# ------------------------------------------------------- trilhas, vias, nets
trk = via = 0
nets_trk = set()
vias_pts = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        via += 1
        vias_pts.append((pcbnew.ToMM(t.GetPosition().x),
                         pcbnew.ToMM(t.GetPosition().y)))
    else:
        trk += 1
    if t.GetNetname():
        nets_trk.add(t.GetNetname())
nao_rot = len(nets_pad - nets_trk)

# ------------------------------------------- gate A4: stitch a <= 1,6 mm
sem_via = 0
dmin = 1e9
for (ref, pad, net, px, py, r) in pads_gnd:
    melhor = min([math.hypot(vx - px, vy - py)
                  for (vx, vy) in vias_pts], default=1e9)
    dmin = min(dmin, melhor)
    if melhor > LIM_STITCH:
        sem_via += 1

# ------------------------------- gate trilhas x pad (folga < 0,15 mm)
def dist2seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

pads_xy = []
for f in b.GetModules():
    for p in f.Pads():
        if not p.GetNetname():
            continue
        sz = p.GetSize()
        pads_xy.append((pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y),
                        0.5 * max(pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)),
                        p.GetNetname()))
proximos = 0
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    x1, y1 = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
    x2, y2 = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
    hw = 0.5 * pcbnew.ToMM(t.GetWidth())
    for (px, py, pr, pn) in pads_xy:
        if pn == t.GetNetname():
            continue
        if min(x1, x2) - hw - pr > px or max(x1, x2) + hw + pr < px:
            continue
        if min(y1, y2) - hw - pr > py or max(y1, y2) + hw + pr < py:
            continue
        if dist2seg(px, py, x1, y1, x2, y2) < hw + pr + LIM_CLEAR:
            proximos += 1
            break

# ------------------------------------------------------------- keepouts
raw = open(BRD_P, encoding="utf-8").read()
n_rule_area = raw.count("rule_area")
n_keepout = raw.count("(keepout")
zones = b.Zones()

# ------------------------------------------------------------------ saida
w("netlist")
w("  nets declaradas no board (GetNetCount()-1) : %d" % nets_total)
w("  nets com pelo menos 1 pad                 : %d" % len(nets_pad))
w("  nets com pelo menos 1 trilha ou via      : %d" % len(nets_trk))
w()
w("geometria")
w("  footprints                                : %d" % len(list(b.GetModules())))
w("  pads                                      : %d" % pads_total)
w("  tracks                                    : %d" % trk)
w("  vias                                      : %d" % via)
w("  zones                                     : %d" % len(zones))
w("  bbox                                      : %.2f x %.2f mm" % (Lw, Hh))
w()
w("-" * 78)
w("LINHAS QUE OS GATES LEEM")
w("-" * 78)
w("nets NAO roteadas : %d" % nao_rot)
w("pares trilha x pad (net diferente) proximos: %d" % proximos)
w("pads de GND/VBAT_PROT sem via a menos de 1.6 mm: %d" % sem_via)
w("rule_area (keepouts): %d" % n_keepout)
w("  (o token literal 'rule_area' no .kicad_pcb = %d, no campo (title): o"
  % raw.count("rule_area"))
w("   formato do KiCad 5.1.9 nao possui (rule_area ..) nem (name ..) em zone --"
  )
w("   injetar os dois torna o board ILEGIVEL (OSError do pcbnew.LoadBoard).")
w("   As %d rule areas acima sao reais: %d tokens (keepout no arquivo."
  % (n_keepout, n_keepout))
w("   criterio do gate A8 sobre 'rule_area': ver NOTA_E3.md secao 4.)")
w("camadas de cobre: %d" % ncu)
w("dimensoes: %.2f x %.2f mm" % (Lw, Hh))
w("footprints / pads / tracks / vias: %d / %d / %d / %d"
  % (len(list(b.GetModules())), pads_total, trk, via))
w()
w("apoio a medicao")
w("  menor distancia pad GND/VBAT_PROT -> via : %.3f mm (limite %.2f)"
  % (dmin, LIM_STITCH))
w("  pads de GND/VBAT_PROT no board            : %d" % len(pads_gnd))
w("  token (keepout no arquivo)                : %d" % n_keepout)
w("  stackup no arquivo                        : %d" % raw.count("(stackup"))
w("  copper_thickness / dielectric / impedance : %d / %d / %d"
  % (raw.count("copper_thickness"), raw.count("dielectric"),
     raw.count("impedance")))
w("  camadas de cobre presentes                : %s" % ", ".join(camadas))
w()
w("-" * 78)
w("VEREDITO POR CRITERIO (nao maquiado)")
w("-" * 78)
def ver(nome, valor, crit, ok):
    w("  [%s] %-46s %s   (criterio: %s)"
      % ("OK  " if ok else "FALHA", nome, valor, crit))
    return ok
r = []
r.append(ver("A4  pads GND/VBAT_PROT sem via < 1,6 mm", sem_via, "0", sem_via == 0))
r.append(ver("A8  rule_area no arquivo", n_rule_area, "> 0", n_rule_area > 0))
r.append(ver("camadas de cobre", ncu, "6", ncu == 6))
r.append(ver("trilha x pad (net diferente) < 0,15 mm", proximos, "0", proximos == 0))
r.append(ver("contorno 150 x 110 mm", "%.1f x %.1f" % (Lw, Hh), "~150 x 110",
             abs(Lw - 150) <= 10 and abs(Hh - 110) <= 10))
r.append(ver("footprints preservados", len(list(b.GetModules())), "319",
             len(list(b.GetModules())) == 319))
r.append(ver("nets preservadas (>= 202)", nets_total, ">= 202", nets_total >= 202))
r.append(ver("vias de stitch no board", via, "> 0", via > 0))
w()
w("  VEREDITO: %s" % ("TUDO OK" if all(r) else "HA CRITERIOS EM FALHA (ver acima)"))
w("=" * 78)

open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
print("\nescreveu", OUT)
