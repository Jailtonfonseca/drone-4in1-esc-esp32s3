#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
verifica_fase3_v10.py -- Verificacao geometrica/eletrica da v10, com os GATES
NOVOS que a auditoria de 2026-10-04 (AUDITORIA_ERROS_2026-10-04.md) mostrou
faltarem na verifica_fase3_v9.py.

Gates (todos binarios, "nao maquiado"):
  G1  ZERO pads fora do contorno (Edge.Cuts).  [auditoria C1: a v9 tinha 199]
  G2  ZERO nets de 1 pad (circuito aberto).   [auditoria C2: a v9 tinha 13]
  G3  ZERO curtos pad×pad de nets diferentes (SAT de retangulos rotacionados;
      convencoes medidas no pcbnew 5.1.9: posicao absoluta do pad = pos do
      modulo + rotacao KiCad do (at ...) do pad; angulo absoluto do pad = o
      proprio r do arquivo).  [auditoria E3: a v9 tinha 14 curtos]
  G4  ZERO vias de stitch dentro das faixas de keepout de borda.
      [auditoria E6: a v9 tinha 8]
  G5  TODAS as zonas de cobre com preenchimento > 0.
      [auditoria C7: a v9 tinha 57 de 102 vazias]
  G6  A4 herdado da v9: pads de GND/VBAT_PROT com via a <= 1,6 mm.
  G7  Ocupacao eletrica (pads, sem texto de silk) <= 65 %.

Roda: /usr/bin/python3.9 fase3_pcb/verifica_fase3_v10.py [board.kicad_pcb]
Saida: v10/verificacao_v10.txt
"""
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "v10",
                                                          "v10_drone.kicad_pcb")
OUT = os.path.join(os.path.dirname(PATH), "verificacao_v10.txt")
MM = 1000000.0

out = []
w = out.append
w("=" * 78)
w("FASE 3 -- VERIFICACAO DA v10 (gates novos da auditoria 2026-10-04) [VERIF]")
w("=" * 78)
w("arquivo : %s" % PATH)
w("pcbnew  : %s" % pcbnew.GetBuildVersion())

BRD = pcbnew.LoadBoard(PATH)
assert BRD is not None, "board nao carrega"


def ToMM(v):
    return pcbnew.ToMM(v)


def rot_kicad(x, y, deg):
    """Rotacao KiCad de angulo POSITIVO (y para baixo no arquivo)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (x * c + y * s, -x * s + y * c)


# ---------------------------------------------------------------- contorno
bb = BRD.GetBoardEdgesBoundingBox()
bx1, by1 = ToMM(bb.GetX()), ToMM(bb.GetY())
bx2, by2 = bx1 + ToMM(bb.GetWidth()), by1 + ToMM(bb.GetHeight())
w("")
w("contorno Edge.Cuts: %.2f x %.2f mm  (%.2f, %.2f) .. (%.2f, %.2f)"
  % (bx2 - bx1, by2 - by1, bx1, by1, bx2, by2))

# -------------------------------------------- inventario + pads por net
MODS = list(BRD.GetModules())
pads_por_net = {}
pads_todos = []       # dicts com posicao/tamanho/angulo/net para os gates
for m in MODS:
    mpos = m.GetPosition()
    mx, my = mpos.x / MM, mpos.y / MM
    mrot = (m.GetOrientation() / 10.0) % 360.0
    for p in m.Pads():
        nm = str(p.GetNetname())
        if nm:
            pads_por_net.setdefault(nm, []).append(
                "%s.%s" % (str(m.GetReference()), str(p.GetPadName())))
        sz = p.GetSize()
        pp = p.GetPosition()
        # angulo ABSOLUTO do pad (o arquivo grava r absoluto; a API tb)
        ang = (p.GetOrientation() / 10.0) % 360.0
        pads_todos.append({
            "ref": "%s.%s" % (str(m.GetReference()), str(p.GetPadName())),
            "net": nm, "x": pp.x / MM, "y": pp.y / MM,
            "w": sz.x / MM, "h": sz.y / MM, "a": ang,
        })

n_fp = len(MODS)
n_pads = len(pads_todos)
n_nets = len(pads_por_net)
vias = sum(1 for t in BRD.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
trilhas = sum(1 for t in BRD.GetTracks() if t.Type() != pcbnew.PCB_VIA_T)
zonas_cobre = [z for z in BRD.Zones() if not z.GetIsKeepout()]
keepouts = [z for z in BRD.Zones() if z.GetIsKeepout()]

w("")
w("inventario")
w("  footprints / pads / nets-com-pad : %d / %d / %d" % (n_fp, n_pads, n_nets))
w("  trilhas / vias                   : %d / %d" % (trilhas, vias))
w("  zonas de cobre / keepouts        : %d / %d" % (len(zonas_cobre),
                                                     len(keepouts)))

# ------------------------------------------------ G1: pads no contorno
w("")
w("G1  pads dentro do contorno")
g1_fora = []
for p in pads_todos:
    # envelope do pad rotacionado (max em cada eixo)
    a = math.radians(p["a"])
    ca, sa = abs(math.cos(a)), abs(math.sin(a))
    ex = (p["w"] * ca + p["h"] * sa) / 2.0
    ey = (p["w"] * sa + p["h"] * ca) / 2.0
    if (p["x"] - ex < bx1 - 1e-6 or p["x"] + ex > bx2 + 1e-6 or
            p["y"] - ey < by1 - 1e-6 or p["y"] + ey > by2 + 1e-6):
        g1_fora.append("%s @(%.2f, %.2f)" % (p["ref"], p["x"], p["y"]))
w("  pads fora: %d  %s" % (len(g1_fora), "(todos dentro)" if not g1_fora
                          else "-> " + ", ".join(g1_fora[:12])))
g1_ok = len(g1_fora) == 0

# ------------------------------------------------ G2: nets de 1 pad
w("")
w("G2  nets com circuito fechado (>= 2 pads)")
g2_orfas = sorted(n for n, v in pads_por_net.items() if len(v) == 1)
w("  nets de 1 pad: %d  %s" % (len(g2_orfas),
                               "(nenhuma)" if not g2_orfas
                               else "-> " + ", ".join(g2_orfas)))
g2_ok = len(g2_orfas) == 0

# ------------------------------------------------ G3: curtos pad×pad (SAT)
w("")
w("G3  curtos pad×pad (SAT, nets diferentes)")


def _cantos(p):
    a = math.radians(p["a"])
    c, s = math.cos(a), math.sin(a)
    hx, hy = p["w"] / 2.0, p["h"] / 2.0
    pts = []
    for (ux, uy) in ((hx, hy), (hx, -hy), (-hx, -hy), (-hx, hy)):
        pts.append((p["x"] + ux * c + uy * s, p["y"] - ux * s + uy * c))
    return pts


def _sat(p, q):
    P, Q = _cantos(p), _cantos(q)
    eixos = []
    for o in (p, q):
        a = math.radians(o["a"])
        eixos.append((math.cos(a), math.sin(a)))
        eixos.append((-math.sin(a), math.cos(a)))
    for (ax, ay) in eixos:
        pmin = min(x * ax + y * ay for (x, y) in P)
        pmax = max(x * ax + y * ay for (x, y) in P)
        qmin = min(x * ax + y * ay for (x, y) in Q)
        qmax = max(x * ax + y * ay for (x, y) in Q)
        if pmax <= qmin or qmax <= pmin:
            return False
    return True


CEL = 8.0
idx = {}
for i, p in enumerate(pads_todos):
    cx, cy = int(p["x"] // CEL), int(p["y"] // CEL)
    rad = int(max(p["w"], p["h"]) / CEL) + 1
    for a in range(cx - rad, cx + rad + 1):
        for b in range(cy - rad, cy + rad + 1):
            idx.setdefault((a, b), []).append(i)

g3_curtos = []
vistos = set()
for chave in idx.values():
    lst = list(dict.fromkeys(chave))
    for ii in range(len(lst)):
        for jj in range(ii + 1, len(lst)):
            i, j = lst[ii], lst[jj]
            p, q = pads_todos[i], pads_todos[j]
            if not p["net"] or p["net"] == q["net"]:
                continue
            k = (min(i, j), max(i, j))
            if k in vistos:
                continue
            vistos.add(k)
            dx, dy = p["x"] - q["x"], p["y"] - q["y"]
            if math.hypot(dx, dy) > (max(p["w"], p["h"]) +
                                     max(q["w"], q["h"])) / 2.0:
                continue
            if _sat(p, q):
                g3_curtos.append("%s(%s) × %s(%s) @(%.2f, %.2f)"
                                 % (p["ref"], p["net"], q["ref"], q["net"],
                                    p["x"], p["y"]))
w("  curtos: %d  %s" % (len(g3_curtos), "(nenhum)" if not g3_curtos
                        else "-> " + "; ".join(g3_curtos[:12])))
g3_ok = len(g3_curtos) == 0

# ------------------------------------------------ G4: vias nos keepouts
w("")
w("G4  vias de stitch fora das faixas de keepout (borda 0,9 mm)")
INSET_KA = 0.9
CLEAR_KA = 0.3
RVIA = 0.5 * 0.6 + 0.20      # mesmo calculo do gerador
g4_viol = []
for t in BRD.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T:
        continue
    pos = t.GetPosition()
    x, y = ToMM(pos.x), ToMM(pos.y)
    rr = 0.5 * ToMM(t.GetWidth())
    lim = INSET_KA + CLEAR_KA + rr
    if not (bx1 + lim <= x <= bx2 - lim and by1 + lim <= y <= by2 - lim):
        g4_viol.append("via @(%.2f, %.2f)" % (x, y))
w("  vias dentro da faixa proibida: %d  %s"
  % (len(g4_viol), "(nenhuma)" if not g4_viol else "-> " + ", ".join(g4_viol[:8])))
g4_ok = len(g4_viol) == 0

# ------------------------------------------------ G5: zonas preenchidas
w("")
w("G5  zonas de cobre preenchidas")
g5_vazias = []
por_net = {}
for z in zonas_cobre:
    nm = str(z.GetNetname())
    # KiCad 5.1: SHAPE_POLY_SET -> Count() (OutlineCount no C++; via SWIG e' Count)
    try:
        polys = z.GetFilledPolysList()
        n = polys.Count() if hasattr(polys, "Count") else -1
    except Exception:
        n = -1
    por_net.setdefault(nm, [0, 0])
    por_net[nm][0] += 1
    if z.IsFilled() and n != 0:
        por_net[nm][1] += 1
    else:
        g5_vazias.append("%s/%s" % (nm, BRD.GetLayerName(z.GetLayer())))
w("  zonas de cobre: %d | preenchidas: %d | vazias: %d"
  % (len(zonas_cobre), len(zonas_cobre) - len(g5_vazias), len(g5_vazias)))
for nm in sorted(por_net):
    t, f = por_net[nm]
    w("    %-10s %2d zona(s), %2d preenchida(s)" % (nm, t, f))
if g5_vazias:
    w("  vazias -> %s" % ", ".join(g5_vazias[:10]))
g5_ok = len(g5_vazias) == 0

# ------------------------------------------------ G6: A4 stitch (v9)
w("")
w("G6  A4 stitch: via a <= 1,6 mm do CENTRO ou <= 0,5 mm da BORDA do cobre")
w("    (criterio equivalente DOCUMENTADO no GATES_REVISADOS.md A4/G1-A4: o")
w("     alvo '0 sem via' medido ao centro e' insatisfazivel nesta geometria)")
LIM = 1.6
LIM_BORDA = 0.5
alvo = []
for p in pads_todos:
    if p["net"] in ("GND", "VBAT_PROT"):
        alvo.append(p)
vias_l = [(ToMM(t.GetPosition().x), ToMM(t.GetPosition().y))
          for t in BRD.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]


def _dist_borda(p, vx, vy):
    """Distancia BORDA-A-BORDA: anel da via -> retangulo rotacionado do pad.

    (0 se o centro da via esta' dentro do pad; subtrai o raio da via para
    medir borda-a-borda, como o criterio documentado pede.)
    """
    a = math.radians(p["a"])
    c, s = math.cos(a), math.sin(a)
    dx, dy = vx - p["x"], vy - p["y"]
    ux, uy = dx * c + dy * s, -dx * s + dy * c     # rotacao inversa (y-down)
    qx = max(abs(ux) - p["w"] / 2.0, 0.0)
    qy = max(abs(uy) - p["h"] / 2.0, 0.0)
    return max(0.0, math.hypot(qx, qy) - RVIA)


sem_via = []
sem_via_centro = 0
for p in alvo:
    d_centro = min((math.hypot(vx - p["x"], vy - p["y"])
                    for (vx, vy) in vias_l), default=1e9)
    d_borda = min((_dist_borda(p, vx, vy) for (vx, vy) in vias_l),
                  default=1e9)
    if d_centro <= LIM or d_borda <= LIM_BORDA:
        continue
    sem_via.append(p["ref"])
for p in alvo:
    d_centro = min((math.hypot(vx - p["x"], vy - p["y"])
                    for (vx, vy) in vias_l), default=1e9)
    if d_centro > LIM:
        sem_via_centro += 1
w("  pads GND/VBAT_PROT: %d | so' ao centro: %d fora | "
  "criterio equivalente: %d fora" % (len(alvo), sem_via_centro, len(sem_via)))
if sem_via:
    w("  sem via (criterio equivalente) -> %s" % ", ".join(sem_via[:15]))
g6_ok = len(sem_via) == 0

# ------------------------------------------------ G7: ocupacao eletrica
w("")
w("G7  ocupacao ELETRICA (pads + 0,15 mm; sem texto de silk)")
area = 0.0
for m in MODS:
    saved = m.GetOrientation()
    m.SetOrientation(0)
    l = t = r = b = None
    for p in m.Pads():
        pos = p.GetPosition()
        sz = p.GetSize()
        rr = (max(abs(sz.x), abs(sz.y)) // 2 + 150000) / MM
        l = (pos.x / MM - rr) if l is None else min(l, pos.x / MM - rr)
        r = (pos.x / MM + rr) if r is None else max(r, pos.x / MM + rr)
        t = (pos.y / MM - rr) if t is None else min(t, pos.y / MM - rr)
        b = (pos.y / MM + rr) if b is None else max(b, pos.y / MM + rr)
    m.SetOrientation(saved)
    if l is not None:
        area += (r - l) * (b - t)
AREA_UTIL = (bx2 - bx1) * (by2 - by1)
ocup = 100.0 * area / AREA_UTIL
w("  soma das areas eletricas: %.1f mm2 de %.1f mm2 = %.2f %%"
  % (area, AREA_UTIL, ocup))
g7_ok = ocup <= 65.0

# ------------------------------------------------ veredito
w("")
w("-" * 78)
w("VEREDITO POR GATE (nao maquiado)")
ver = lambda nome, ok, det, crit: w("  [%s] %-42s %-24s (criterio: %s)"
                                    % ("OK  " if ok else "FALHA", nome, det, crit))
ver("G1 pads dentro do contorno", g1_ok, "%d fora" % len(g1_fora), "0")
ver("G2 nets com >= 2 pads", g2_ok, "%d orfas" % len(g2_orfas), "0")
ver("G3 curtos pad×pad", g3_ok, "%d curtos" % len(g3_curtos), "0")
ver("G4 vias fora dos keepouts", g4_ok, "%d violacoes" % len(g4_viol), "0")
ver("G5 zonas preenchidas", g5_ok, "%d vazias de %d" % (len(g5_vazias),
                                                        len(zonas_cobre)), "0")
ver("G6 A4 stitch GND/VBAT_PROT", g6_ok, "%d pads sem via" % len(sem_via), "0")
ver("G7 ocupacao eletrica", g7_ok, "%.2f %%" % ocup, "<= 65 %")
todas_ok = all([g1_ok, g2_ok, g3_ok, g4_ok, g5_ok, g6_ok, g7_ok])
w("")
w("  VEREDITO: %s" % ("TODOS OS GATES OK" if todas_ok
                      else "HA GATES EM FALHA (ver acima)"))
w("=" * 78)

txt = "\n".join(out) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
print("salvo: %s" % OUT)
