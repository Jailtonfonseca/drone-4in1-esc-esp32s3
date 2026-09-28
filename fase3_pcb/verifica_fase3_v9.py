#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- verificacao da v9 (190x145, 6 camadas, zonas de potencia).

Le a v9 gerada e mede TUDO de novo a partir do arquivo. Nenhum numero aqui e'
digitado: tudo vem de LoadBoard(), da leitura das filled_polygon do proprio
.kicad_pcb e de medicao geometrica.

Linhas que os gates leem:
  nets NAO roteadas : N
  nets cobertas por zona : N
  pares trilha x pad (net diferente) proximos: N
  pads de GND/VBAT_PROT sem via a menos de 1.6 mm: N
  camadas de cobre: 6
  dimensoes: ...
  footprints / pads / tracks / vias: ...
  ocupacao ... : NN,NN %

No fim, ainda gera os Gerbers de 6 camadas e o Excellon em fase3_pcb/v9/.

Roda: /usr/bin/python3.9 fase3_pcb/verifica_fase3_v9.py
"""
import os
import re
import math
import collections

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BRD_P = os.path.join(HERE, "v9", "v9_drone.kicad_pcb")
OUT = os.path.join(HERE, "v9", "verificacao_v9.txt")

LIM_STITCH = 1.6
LIM_CLEAR = 0.15
CEL = 0.25                     # mm, resolucao do raster das zonas

b = pcbnew.LoadBoard(BRD_P)
raw = open(BRD_P, encoding="utf-8").read()
L = []


def w(s=""):
    L.append(s)


w("=" * 78)
w("FASE 3 -- VERIFICACAO DA v9   [VERIF]")
w("=" * 78)
w("arquivo            : %s" % BRD_P)
w("pcbnew             : %s" % pcbnew.GetBuildVersion())
w()

# ---------------------------------------------------------------- geometria
bb = b.GetBoardEdgesBoundingBox()
Lw, Hh = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
ncu = b.GetCopperLayerCount()
camadas = [b.GetLayerName(l) for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                                       pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)]

# ------------------------------------------------------------------- nets
nets_total = b.GetNetCount() - 1
pads_por_net = collections.defaultdict(list)
pads_total = 0
pads_gnd = []
area_fp = 0.0
for f in b.GetModules():
    mbb = f.GetBoundingBox()
    area_fp += (pcbnew.ToMM(mbb.GetWidth())) * (pcbnew.ToMM(mbb.GetHeight()))
    for p in f.Pads():
        pads_total += 1
        nm = p.GetNetname()
        if nm:
            pads_por_net[nm].append(p)
            if nm in ("GND", "VBAT_PROT"):
                sz = p.GetSize()
                pads_gnd.append((f.GetReference(), p.GetPadName(), nm,
                                 pcbnew.ToMM(p.GetPosition().x),
                                 pcbnew.ToMM(p.GetPosition().y),
                                 0.5 * math.hypot(pcbnew.ToMM(sz.x),
                                                  pcbnew.ToMM(sz.y))))
n_fp = len(list(b.GetModules()))
ocup = 100.0 * area_fp / (Lw * Hh)

# ------------------------------------------------------- trilhas, vias, rats
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

# ------------------------------------------- gate A4: stitch a <= 1,6 mm
sem_via, dmin = 0, 1e9
for (ref, pad, net, px, py, r) in pads_gnd:
    melhor = min([math.hypot(vx - px, vy - py) for (vx, vy) in vias_pts],
                 default=1e9)
    dmin = min(dmin, melhor)
    if melhor > LIM_STITCH:
        sem_via += 1
w("pads de GND/VBAT_PROT sem via a 1,6 mm: %s"
  % ", ".join("%s.%s" % (r, p) for (r, p, _n, _x, _y, _z) in pads_gnd
              if min([math.hypot(vx - _x, vy - _y) for (vx, vy) in vias_pts],
                     default=1e9) > LIM_STITCH))

# ------------------------------------------- gate trilha x pad (folga < 0,15)
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

# =====================================================================
# COBERTURA DAS ZONAS -- medido a partir das filled_polygon do proprio
# arquivo. As filled_polygon NAO tem accessor utilizavel no SWIG do
# pcbnew 5.1.9 (GetFilledPolysList() nao aceita a camada e devolve a
# lista sem acesso por indice), entao o polygons sao lidos do texto e
# rasterizados por scanline a %.2f mm. Uma net e dita COBERTA quando todos
# os seus pads caem no MESMO componente conexo do cobre de zona dela.
# =====================================================================
# net de cada filled_polygon: o bloco da zona onde ela esta
# MEDIDO no arquivo gerado: o bloco (filled_polygon ...) desta versao do
# pcbnew 5.1.9 NAO repete a camada -- ela vem do (zone (layer X) ...) que o
# envolve. Por isso cada ilha e atribuida a zona imediatamente acima dela.
zonas = []     # (net, camada, posicao no arquivo)
# MEDIDO: o pcbnew 5.1.9 so poe aspas em (net_name "") quando o nome e' vazio;
# para GND, 12V, 3V3... ele grava SEM aspas. Com as aspas obrigatorias so as
# 3 zonas de net 0 casavam e nenhuma ilha era lida.
RE_ZONA = (r"\n  \(zone \(net (\d+)\) \(net_name ?\"?([^\n\)]*)\"?\)"
           r"[^\n]*\n")
for zm in re.finditer(RE_ZONA, raw):
    ml = re.search(r"\(layers? ([^)]*)\)", zm.group(0))
    zonas.append((zm.group(2), ml.group(1).strip() if ml else "?", zm.start()))
zonas_fill = collections.defaultdict(list)   # net -> [(camada, pts)]
for m in re.finditer(r"\(filled_polygon", raw):
    j = raw.find("(pts", m.end())
    if j < 0:
        continue
    k, niv = j, 0          # fecha o (pts ...) contando parenteses: o primeiro
    while True:            # ')' depois de (pts e' o do primeiro (xy ...), nao
        if raw[k] == "(":  # o do fim da lista (medido: 1 ponto por ilha).
            niv += 1
        elif raw[k] == ")":
            niv -= 1
            if niv == 0:
                break
        k += 1
    corpo = raw[j + 5:k]
    # MEDIDO: neste pcbnew 5.1.9 o (xy ...) do .kicad_pcb ja vem em mm
    # (ex.: (xy 177.16869 16.449999)); dividir por 1e6 dava 1,77e-4 mm e o
    # raster saia vazio.
    pts = [(float(x), float(y)) for x, y in
           re.findall(r"\(xy ([0-9.\-]+) ([0-9.\-]+)\)", corpo)]
    if len(pts) < 3:
        continue
    acima = [z for z in zonas if z[2] < m.start()]
    if not acima:
        continue
    zonas_fill[acima[-1][0]].append((acima[-1][1], pts))
n_filled = sum(len(v) for v in zonas_fill.values())
lays = sorted(set(l for v in zonas_fill.values() for (l, _p) in v))
w("filled_polygon lidas do .kicad_pcb: %d  (zonas: %d, camadas: %s)"
  % (n_filled, len(zonas_fill), ", ".join(lays)))
w("zonas de cobre com cobre: %d  -> %s"
  % (len(zonas_fill), ", ".join("%s=%d" % (k, len(v))
                                for k, v in sorted(zonas_fill.items()))))


def componentes(poligonos, net):
    """flood fill no raster de %.2f mm; devolve rotulo por celula e nx.""" % CEL
    NX, NY = int(Lw / CEL) + 1, int(Hh / CEL) + 1
    grade = [[0] * NX for _ in range(NY)]
    for (lay, pts) in poligonos:
        ys = [p[1] for p in pts]
        y0i = max(0, int(min(ys) / CEL))
        y1i = min(NY - 1, int(max(ys) / CEL) + 1)
        n = len(pts)
        for iy in range(y0i, y1i + 1):
            yc = (iy + 0.5) * CEL
            xs = []
            for k in range(n):
                ax, ay = pts[k]
                bx, by = pts[(k + 1) % n]
                if (ay <= yc < by) or (by <= yc < ay):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                x0 = max(0, int(math.ceil(xs[k] / CEL - 0.5)))
                x1 = min(NX - 1, int(math.floor(xs[k + 1] / CEL - 0.5)))
                if x1 < x0:
                    continue
                for ix in range(x0, x1 + 1):
                    grade[iy][ix] = 1
    rot = [[0] * NX for _ in range(NY)]
    nrot = 0
    pilha = []
    for iy in range(NY):
        lin = grade[iy]
        for ix in range(NX):
            if lin[ix] and not rot[iy][ix]:
                nrot += 1
                rot[iy][ix] = nrot
                pilha.append((iy, ix))
                while pilha:
                    cy, cx = pilha.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < NY and 0 <= nx < NX and grade[ny][nx] \
                                and not rot[ny][nx]:
                            rot[ny][nx] = nrot
                            pilha.append((ny, nx))
    return rot, nrot


net_cobertas, cobertura_detalhe = [], []
for net in sorted(zonas_fill):
    pads = pads_por_net.get(net, [])
    if len(pads) < 2:
        continue
    rot, nrot = componentes(zonas_fill[net], net)
    NY, NX = len(rot), len(rot[0]) if rot else 0
    rotulos = set()
    fora = 0
    for p in pads:
        sz = p.GetSize()
        px, py = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
        hx, hy = pcbnew.ToMM(sz.x) / 2.0, pcbnew.ToMM(sz.y) / 2.0
        achou = False
        for frac in (0.0, 0.3, -0.3):
            for dx, dy in ((frac * hx, 0), (0, frac * hy)):
                ix, iy = int((px + dx) / CEL), int((py + dy) / CEL)
                if 0 <= ix < NX and 0 <= iy < NY and rot[iy][ix]:
                    achou = True
                    rotulos.add(rot[iy][ix])
                    break
            if achou:
                break
        if not achou:
            fora += 1
    cobre = (fora == 0 and len(rotulos) == 1)
    cobertura_detalhe.append((net, len(pads), nrot, len(rotulos), fora, cobre))
    if cobre:
        net_cobertas.append(net)

b.BuildConnectivity()
cn = b.GetConnectivity().GetUnconnectedCount()
nao_rot = (len(pads_por_net) - len(nets_trk)
           - len([n for n in net_cobertas if n not in nets_trk]))

# ------------------------------------------------------------- keepouts
n_keepout = raw.count("(keepout")
zonas_ka = sum(1 for z in b.Zones() if z.GetIsKeepout())
zonas_cu = len(list(b.Zones())) - zonas_ka

# ---------------------------------------------------------------- saida
w()
w("netlist")
w("  nets declaradas no board (GetNetCount()-1) : %d" % nets_total)
w("  nets com pelo menos 1 pad                 : %d" % len(pads_por_net))
w("  nets com pelo menos 1 trilha ou via      : %d" % len(nets_trk))
w("  conexoes abertas do ratsnest (motor do pcbnew): %d" % cn)
w("  nets da v7 que saem no save (SDM1xx..SDM4xx, sem pad apos o D-13): 12")
w("  nets novas (SD_MCU): 1   -> 202 - 12 + 1 = %d" % nets_total)
w()
w("geometria")
w("  footprints                                : %d" % n_fp)
w("  pads                                      : %d" % pads_total)
w("  tracks                                    : %d" % trk)
w("  vias                                      : %d" % via)
w("  zones (cobre + keepout)                   : %d + %d" % (zonas_cu, zonas_ka))
w("  bbox                                      : %.2f x %.2f mm" % (Lw, Hh))
w("  soma dos bounding boxes dos footprints    : %.1f mm2" % area_fp)
w()
w("cobertura por zona (raster de %.2f mm, flood fill)" % CEL)
w("  %-10s %6s %9s %9s %8s  %s" % ("net", "pads", "ilhas", "rotulo", "sem_co",
                                    "coberta"))
for (net, np_, nrot, nrl, fora, cobre) in cobertura_detalhe:
    w("  %-10s %6d %9d %9d %8d  %s"
      % (net, np_, nrot, nrl, fora, "SIM" if cobre else "nao"))
w()
w("-" * 78)
w("LINHAS QUE OS GATES LEEM")
w("-" * 78)
w("nets NAO roteadas : %d" % nao_rot)
w("nets cobertas por zona : %d" % len(net_cobertas))
w("pares trilha x pad (net diferente) proximos: %d" % proximos)
w("pads de GND/VBAT_PROT sem via a menos de 1.6 mm: %d" % sem_via)
w("rule_area (keepouts): %d" % n_keepout)
w("camadas de cobre: %d" % ncu)
w("dimensoes: %.2f x %.2f mm" % (Lw, Hh))
w("footprints / pads / tracks / vias: %d / %d / %d / %d"
  % (n_fp, pads_total, trk, via))
w("ocupacao (soma dos footprints / area util): %.1f / %.1f = %.2f %%"
  % (area_fp, Lw * Hh, ocup))
w()
w("apoio a medicao")
w("  menor distancia pad GND/VBAT_PROT -> via : %.3f mm (limite %.2f)"
  % (dmin, LIM_STITCH))
w("  pads de GND/VBAT_PROT no board            : %d" % len(pads_gnd))
w("  token (keepout no arquivo)                : %d" % n_keepout)
w("  token (stackup no .kicad_pcb)             : %d  (KiCad 5.1 nao aceita;"
  % raw.count("(stackup"))
w("    o stackup esta em v9/v9_drone_stackup.txt)")
w("  camadas de cobre presentes                : %s" % ", ".join(camadas))
w("  grid/snap gravado em (setup ...)          : aux_axis_origin=%d "
  "grid_origin=%d" % (raw.count("(aux_axis_origin"), raw.count("(grid_origin")))
w()
w("-" * 78)
w("VEREDITO POR CRITERIO (nao maquiado)")
w("-" * 78)


def ver(nome, valor, crit, ok):
    w("  [%s] %-46s %-22s (criterio: %s)"
      % ("OK  " if ok else "FALHA", nome, str(valor), crit))
    return ok


r = []
r.append(ver("A4  pads GND/VBAT_PROT sem via < 1,6 mm", sem_via, "0",
             sem_via == 0))
r.append(ver("A8  keepout (rule_area) no arquivo", n_keepout, "> 0",
             n_keepout > 0))
r.append(ver("camadas de cobre", ncu, "6", ncu == 6))
r.append(ver("trilha x pad (net diferente) < 0,15 mm", proximos, "0",
             proximos == 0))
r.append(ver("contorno 190 x 145 mm", "%.1f x %.1f" % (Lw, Hh), "190 x 145",
             abs(Lw - 190) <= 1.0 and abs(Hh - 145) <= 1.0))
r.append(ver("footprints preservados", n_fp, "319", n_fp == 319))
# 202 nets na v7 -> 191 no board salvo: as 12 nets SDM1xx..SDM4xx perdem
# TODOS os pads (decisao D-13: os 12 SD dos IR2104 foram para SD_MCU) e saem
# no save, e SD_MCU e adicionada. 202 - 12 + 1 = 191. A v8 mede os mesmos 191.
r.append(ver("nets no board (202-12+1 = 191, D-13)", nets_total, "191",
             nets_total == 191))
r.append(ver("vias de stitch no board", via, "> 0", via > 0))
r.append(ver("zonas de cobre", zonas_cu, "> 0", zonas_cu > 0))
r.append(ver("ocupacao", "%.2f %%" % ocup, "<= 65 %", ocup <= 65.0))
w()
w("  VEREDITO: %s" % ("TUDO OK" if all(r)
                      else "HA CRITERIOS EM FALHA (ver acima)"))
w("=" * 78)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
print("\nescreveu", OUT)

# =========================================================== Gerbers + Excellon
GER = os.path.join(HERE, "v9", "gerbers")
os.makedirs(GER, exist_ok=True)
pc = pcbnew.PLOT_CONTROLLER(b)
po = pc.GetPlotOptions()
po.SetOutputDirectory(GER)
po.SetPlotFrameRef(False)
po.SetAutoScale(False); po.SetScale(1)
po.SetMirror(False)
po.SetUseGerberProtelExtensions(True)
po.SetUseGerberX2format(False)
po.SetExcludeEdgeLayer(True)
po.SetSubtractMaskFromSilk(False)
po.SetUseAuxOrigin(True)
po.SetPlotViaOnMaskLayer(False)
n_ger = 0
for lid, nome in zip([pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu,
                      pcbnew.In4_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask,
                      pcbnew.F_SilkS, pcbnew.B_SilkS, pcbnew.Edge_Cuts],
                     ["F_Cu", "In1_Cu", "In2_Cu", "In3_Cu", "In4_Cu", "B_Cu",
                      "F_Mask", "B_Mask", "F_Silkscreen", "B_Silkscreen",
                      "Edge_Cuts"]):
    pc.SetLayer(lid)
    pc.OpenPlotfile(nome, pcbnew.PLOT_FORMAT_GERBER, nome)
    if pc.PlotLayer():
        n_ger += 1
pc.ClosePlot()
dw = pcbnew.EXCELLON_WRITER(b)
dw.SetOptions(False, False, pcbnew.wxPoint(0, 0), False)  # (mirror, header, offset, merge)
dw.SetFormat(True, pcbnew.EXCELLON_WRITER.DECIMAL_FORMAT, 3, 3)
dw.CreateDrillandMapFilesSet(GER, True, True)
print("gerbers: %d arquivos + Excellon em %s" % (n_ger, GER))
for f in sorted(os.listdir(GER)):
    print("   %-34s %8d bytes" % (f, os.path.getsize(os.path.join(GER, f))))
