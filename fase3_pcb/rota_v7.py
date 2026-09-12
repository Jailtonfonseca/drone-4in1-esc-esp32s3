#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- roteamento automatico PROPRIO (A* em grade) + verificacao geometrica.

Entrada : /opt/jupyter/work/drone/fase3_pcb/v7/v7_drone.kicad_pcb
Saida   : /opt/jupyter/work/drone/fase3_pcb/v8/  (v8_drone.kicad_pcb, Gerbers,
          Excellon, verificacao_v8.txt)

O que este script faz, em ordem:
  1. carrega a v7;
  2. fecha no plano (via + stub) TODO pad de GND/VBAT_PROT que ainda nao tem
     via propria -- pads SMD em F_Cu nao alcancam o plano de In1 sozinhos;
  3. rasteriza a placa numa grade de 0,5 mm guardando o ID da net de cada celula
     (0 = livre, -1 = bloqueado por borda/keepout);
  4. roteia com A* todas as nets de sinal que ainda nao estao conectadas
     (F_Cu e B_Cu; In1 = GND e In2 = VBAT_PROT sao planos, nao se roteia neles);
     larguras: 0,20 mm sinal | 0,25 mm trilhos 12 V/3V3/5V | 0,40 mm 5 V ate' o buck;
  5. re-preenche as zonas e salva;
  6. VERIFICA geometricamente (tolerancia 0,02 mm) net por net: todas as nets
     ficaram conectadas? ha' curto entre nets diferentes? qual a menor folga?
  7. exporta Gerber + Excellon.

NAO existe autorouter do KiCad aqui (kicad-cli nao esta instalado); este roteador
e' codigo proprio, simples, de uma camada de "grade": os resultados sao reportados
com o que ele NAO garante (qualidade termica/EMI dos sinais, impedancia, etc.).
"""
import os
import math
import heapq
import numpy as np
import pcbnew

BASE = "/opt/jupyter/work/drone/fase3_pcb"
SRC = BASE + "/v7/v7_drone.kicad_pcb"
OUT = BASE + "/v8"
os.makedirs(OUT, exist_ok=True)

PITCH = 0.5
X0, Y0, W, H = 10.0, 10.0, 220.0, 160.0
NX, NY = int(W / PITCH), int(H / PITCH)     # 440 x 320
CLEAR = 0.25          # folga minima desejada entre nets diferentes
VIA_COST = 12.0       # penalidade de uma troca de camada (em celulas)
TURN_COST = 0.35

BRD = pcbnew.LoadBoard(SRC)
LAY_F, LAY_B = 0, 1

def c2x(i): return X0 + PITCH / 2 + i * PITCH
def c2y(j): return Y0 + PITCH / 2 + j * PITCH
def x2c(x): return int(round((x - X0 - PITCH / 2) / PITCH))
def y2c(y): return int(round((y - Y0 - PITCH / 2) / PITCH))

# ---------------------------------------------------------------- geometria
def pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)

def seg_seg(a, b, c, d):
    ax, ay = a; bx, by = b; cx, cy = c; dx, dy = d
    def ccw(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2 = ccw(c, d, a), ccw(c, d, b)
    d3, d4 = ccw(a, b, c), ccw(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg(ax, ay, cx, cy, dx, dy), pt_seg(bx, by, cx, cy, dx, dy),
               pt_seg(cx, cy, ax, ay, bx, by), pt_seg(dx, dy, ax, ay, bx, by))

def rect_gap(ra, rb):
    """folga entre dois retangulos (ax1,ay1,ax2,ay2); 0 = sobrepostos"""
    dx = max(ra[0] - rb[2], rb[0] - ra[2], 0.0)
    dy = max(ra[1] - rb[3], rb[1] - ra[3], 0.0)
    return math.hypot(dx, dy)

def seg_rect_gap(a, b, r):
    """distancia entre o segmento a-b e o retangulo r (0 se dentro)"""
    x1, y1, x2, y2 = r
    if x1 <= a[0] <= x2 and y1 <= a[1] <= y2:
        return 0.0
    if x1 <= b[0] <= x2 and y1 <= b[1] <= y2:
        return 0.0
    c = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    d = min(seg_seg(a, b, c[k], c[(k + 1) % 4]) for k in range(4))
    return d

def seg_seg_gap(a, b, wa, c, d, wb):
    return max(0.0, seg_seg(a, b, c, d) - wa / 2.0 - wb / 2.0)

# ---------------------------------------------------------------- objetos
class Obj:
    __slots__ = ("kind", "net", "layers", "pts", "w", "rect", "r", "ref")
    def __init__(self, kind, net, layers, pts=None, w=0.0, rect=None, r=0.0, ref=""):
        self.kind, self.net, self.layers = kind, net, layers
        self.pts, self.w, self.rect, self.r, self.ref = pts, w, rect, r, ref

def coleta():
    objs = []
    for fp in BRD.GetModules():
        for p in fp.Pads():
            c = p.GetPosition(); s = p.GetSize()
            lay = []
            if p.IsOnLayer(pcbnew.F_Cu): lay.append(LAY_F)
            if p.IsOnLayer(pcbnew.B_Cu): lay.append(LAY_B)
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_STANDARD, pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED):
                lay = [LAY_F, LAY_B]
            w = pcbnew.ToMM(s.x); h = pcbnew.ToMM(s.y)
            objs.append(Obj("pad", p.GetNetname(), lay,
                            rect=(pcbnew.ToMM(c.x) - w / 2, pcbnew.ToMM(c.y) - h / 2,
                                  pcbnew.ToMM(c.x) + w / 2, pcbnew.ToMM(c.y) + h / 2),
                            ref="%s.%s" % (fp.GetReference(), p.GetPadName())))
    for t in BRD.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            c = t.GetPosition(); dia = pcbnew.ToMM(t.GetWidth())
            objs.append(Obj("via", t.GetNetname(), [LAY_F, LAY_B],
                            pts=((pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)),) * 2,
                            w=dia, r=dia / 2.0))
        else:
            s, e = t.GetStart(), t.GetEnd()
            objs.append(Obj("trk", t.GetNetname(), [LAY_F if t.GetLayer() == pcbnew.F_Cu else LAY_B],
                            pts=((pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)),
                                 (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))),
                            w=pcbnew.ToMM(t.GetWidth())))
    return objs

def conecta(a, b):
    """True se o cobre de a encosta em b (tolerancia 0,02 mm)"""
    g = obj_gap(a, b)
    return g is not None and g <= 0.02

def obj_gap(a, b):
    """folga entre dois objetos (0 = encostado/sobreposto)"""
    if not (set(a.layers) & set(b.layers)):
        return None
    if a.kind == "pad" and b.kind == "pad":
        return rect_gap(a.rect, b.rect)
    if a.kind == "pad" or b.kind == "pad":
        p, s = (a, b) if a.kind == "pad" else (b, a)
        return max(0.0, seg_rect_gap(s.pts[0], s.pts[1], p.rect) - s.w / 2.0)
    if a.kind == "via" and b.kind == "via":
        return max(0.0, math.hypot(a.pts[0][0] - b.pts[0][0], a.pts[0][1] - b.pts[0][1]) - a.r - b.r)
    if a.kind == "via" or b.kind == "via":
        v, s = (a, b) if a.kind == "via" else (b, a)
        return max(0.0, pt_seg(v.pts[0][0], v.pts[0][1], s.pts[0][0], s.pts[0][1],
                               s.pts[1][0], s.pts[1][1]) - v.r - s.w / 2.0)
    return seg_seg_gap(a.pts[0], a.pts[1], a.w, b.pts[0], b.pts[1], b.w)

# ---------------------------------------------------------------- 1) via de plano
def fecha_no_plano(objs):
    """poe via + stub em cada pad SMD de GND/VBAT_PROT que nao tem via/track proprio"""
    novos = []
    cands = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1),
             (1.6, 0), (-1.6, 0), (0, 1.6), (0, -1.6)]
    alvos = [o for o in objs if o.kind == "pad" and o.net in ("GND", "VBAT_PROT")
             and LAY_F in o.layers]
    for p in alvos:
        cx = (p.rect[0] + p.rect[2]) / 2.0
        cy = (p.rect[1] + p.rect[3]) / 2.0
        ja = False
        for o in objs:
            if o is p or o.net != p.net:
                continue
            if o.kind == "via":
                if math.hypot(o.pts[0][0] - cx, o.pts[0][1] - cy) < 2.2:
                    ja = True; break
            elif o.kind == "trk" and (o.pts[0] == o.pts[1]):
                pass
        if ja:
            continue
        for (dx, dy) in cands:
            d = math.hypot(dx, dy)
            vx, vy = cx + dx * (max(p.rect[2] - p.rect[0], p.rect[3] - p.rect[1]) / 2.0 + 0.75 + d * 0.15), \
                     cy + dy * (max(p.rect[2] - p.rect[0], p.rect[3] - p.rect[1]) / 2.0 + 0.75 + d * 0.15)
            ok = True
            v = Obj("via", p.net, [LAY_F, LAY_B], pts=((vx, vy),) * 2, w=0.6, r=0.3)
            tre = Obj("trk", p.net, [LAY_F], pts=((cx, cy), (vx, vy)), w=0.3)
            for o in objs:
                if o.net == p.net:
                    continue
                g = obj_gap(v, o)
                if g is not None and g < CLEAR * 0.8:
                    ok = False; break
                g = obj_gap(tre, o)
                if g is not None and g < CLEAR * 0.8:
                    ok = False; break
            if ok:
                novos.append((v, tre)); objs.append(v); objs.append(tre)
                break
    return novos

# ---------------------------------------------------------------- 2) grade
def rasteriza(objs):
    grid = np.zeros((2, NX, NY), dtype=np.int32)
    netid = {}
    for o in objs:
        netid.setdefault(o.net, len(netid) + 1)
    # borda
    m = int(1.0 / PITCH) + 1
    grid[:, :m, :] = -1; grid[:, -m:, :] = -1
    grid[:, :, :m] = -1; grid[:, :, -m:] = -1
    for o in objs:
        nid = netid.get(o.net, 0)
        if o.kind == "pad":
            r = o.rect
            pad_w = 0.0
        elif o.kind == "via":
            r = (o.pts[0][0] - o.r, o.pts[0][1] - o.r, o.pts[0][0] + o.r, o.pts[0][1] + o.r)
            pad_w = 0.0
        else:
            r = (min(o.pts[0][0], o.pts[1][0]), min(o.pts[0][1], o.pts[1][1]),
                 max(o.pts[0][0], o.pts[1][0]), max(o.pts[0][1], o.pts[1][1]))
            pad_w = o.w / 2.0
        exp = CLEAR if o.kind != "via" else 0.25
        i0 = max(0, x2c(r[0] - exp) - 1); i1 = min(NX - 1, x2c(r[2] + exp) + 1)
        j0 = max(0, y2c(r[1] - exp) - 1); j1 = min(NY - 1, y2c(r[3] + exp) + 1)
        for i in range(i0, i1 + 1):
            x = c2x(i)
            for j in range(j0, j1 + 1):
                y = c2y(j)
                # distancia ao objeto
                if o.kind == "pad":
                    d = rect_gap((x, y, x, y), o.rect)
                    corpo = (o.rect[0] <= x <= o.rect[2] and o.rect[1] <= y <= o.rect[3])
                elif o.kind == "via":
                    d = max(0.0, math.hypot(x - o.pts[0][0], y - o.pts[0][1]) - o.r)
                    corpo = d == 0.0
                else:
                    d = max(0.0, pt_seg(x, y, o.pts[0][0], o.pts[0][1],
                                        o.pts[1][0], o.pts[1][1]) - o.w / 2.0)
                    corpo = d == 0.0
                for L in o.layers:
                    if corpo:
                        if grid[L, i, j] <= 0:
                            grid[L, i, j] = nid
                    elif d < CLEAR:
                        if grid[L, i, j] == 0:
                            grid[L, i, j] = -1
                    elif d < CLEAR * 1.8:
                        if grid[L, i, j] == 0:
                            grid[L, i, j] = -2      # zona "cara", evita passar colado
    return grid, netid

# ---------------------------------------------------------------- 3) A*
def astro(grid, nid, starts, goals, max_nodes=400000):
    """A* multi-origem/multi-destino. starts/goals = [(i,j,L)]"""
    gs = set(goals)
    if not gs:
        return None
    h = lambda i, j: min(abs(i - a) + abs(j - b) for (a, b, _) in goals)
    start_set = set(starts)
    openq = []
    for (i, j, L) in starts:
        heapq.heappush(openq, (h(i, j), 0.0, (i, j, L), None))
    best = {}
    came = {}
    nodes = 0
    while openq:
        f, g, cur, prev = heapq.heappop(openq)
        if best.get(cur, 1e18) < g:
            continue
        best[cur] = g
        came[cur] = prev
        if cur in gs:
            path = []
            k = cur
            while k is not None:
                path.append(k); k = came[k]
            return path[::-1]
        i, j, L = cur
        nodes += 1
        if nodes > max_nodes:
            return "LIMITE"
        for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY):
                continue
            v = grid[L, ni, nj]
            if v == -1 or (v > 0 and v != nid):
                continue
            if v == -2 and (ni, nj, L) not in gs and (ni, nj, L) not in start_set:
                continue
            base = 1.0 + (0.55 if v == -2 else 0.0)
            ng = g + base
            if di and came.get((i, j, L)):
                pass
            key = (ni, nj, L)
            if best.get(key, 1e18) > ng:
                heapq.heappush(openq, (ng + h(ni, nj), ng, key, cur))
        # troca de camada
        oL = 1 - L
        if 2 <= i < NX - 2 and 2 <= j < NY - 2:
            livre = True
            for (di, dj) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                for Lx in (0, 1):
                    v = grid[Lx, i + di, j + dj]
                    if v == -1 or (v > 0 and v != nid):
                        livre = False
            if livre:
                key = (i, j, oL)
                ng = g + VIA_COST
                if best.get(key, 1e18) > ng:
                    heapq.heappush(openq, (ng + h(i, j), ng, key, cur))
    return None

# ---------------------------------------------------------------- 4) roteia
objs = coleta()
print("objetos carregados:", len(objs))
planos = fecha_no_plano(objs)
print("vias de plano criadas:", len(planos))
for v, tre in planos:
    via = pcbnew.VIA(BRD); via.SetPosition(pcbnew.wxPointMM(v.pts[0][0], v.pts[0][1]))
    via.SetDrill(pcbnew.FromMM(0.3)); via.SetWidth(pcbnew.FromMM(0.6))
    via.SetViaType(pcbnew.VIA_THROUGH); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNetCode(BRD.FindNet(v.net).GetNet()); BRD.Add(via)
    t = pcbnew.TRACK(BRD)
    t.SetStart(pcbnew.wxPointMM(tre.pts[0][0], tre.pts[0][1]))
    t.SetEnd(pcbnew.wxPointMM(tre.pts[1][0], tre.pts[1][1]))
    t.SetWidth(pcbnew.FromMM(0.3)); t.SetLayer(pcbnew.F_Cu)
    t.SetNetCode(BRD.FindNet(tre.net).GetNet()); BRD.Add(t)

grid, netid = rasteriza(objs)
id2net = {v: k for k, v in netid.items()}
print("grade:", NX, "x", NY, "| nets na grade:", len(netid))

# pads por net
pads_net = {}
for o in objs:
    if o.kind == "pad" and o.net:
        pads_net.setdefault(o.net, []).append(o)

IGNORA = {"GND", "VBAT_PROT"}          # planos
filas = []
for nm, ps in pads_net.items():
    if nm in IGNORA or len(ps) < 2:
        continue
    xs = [(p.rect[0] + p.rect[2]) / 2 for p in ps]
    ys = [(p.rect[1] + p.rect[3]) / 2 for p in ps]
    filas.append((max(xs) - min(xs) + max(ys) - min(ys), nm, ps))
filas.sort()

def largura(nm):
    if nm == "5V":
        return 0.40
    if nm in ("12V", "3V3", "3V3_A", "5V_AUX", "VBAT_F", "VBAT"):
        return 0.25
    return 0.20

def cells_of(p):
    c = ((p.rect[0] + p.rect[2]) / 2.0, (p.rect[1] + p.rect[3]) / 2.0)
    return (min(max(x2c(c[0]), 0), NX - 1), min(max(y2c(c[1]), 0), NY - 1))

def marca(xx, yy, L, nid):
    gi, gj = min(max(x2c(xx), 0), NX - 1), min(max(y2c(yy), 0), NY - 1)
    grid[L, gi, gj] = nid

def emite(nm, nid, larg, path, p_ini, p_fim):
    """caminho da grade -> trilhas/vias de verdade (com snapping nos pads)"""
    newnet = BRD.FindNet(nm)
    seq = []
    cur = p_ini; ll = path[0][2]; lx, ly = path[0][0], path[0][1]
    for (i, j, L) in path[1:]:
        if L != ll:
            seq.append(("trk", cur, (c2x(lx), c2y(ly)), ll))
            seq.append(("via", (c2x(lx), c2y(ly)), None, ll))
            cur = (c2x(lx), c2y(ly)); ll = L
        lx, ly = i, j
    seq.append(("trk", cur, (c2x(lx), c2y(ly)), ll))
    for kind, a, b, L in seq:
        if kind == "via":
            v = pcbnew.VIA(BRD); v.SetPosition(pcbnew.wxPointMM(a[0], a[1]))
            v.SetDrill(pcbnew.FromMM(0.3)); v.SetWidth(pcbnew.FromMM(0.6))
            v.SetViaType(pcbnew.VIA_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNetCode(newnet.GetNet()); BRD.Add(v)
            for Lx in (0, 1):
                marca(a[0], a[1], Lx, nid)
        else:
            t = pcbnew.TRACK(BRD)
            t.SetStart(pcbnew.wxPointMM(a[0], a[1])); t.SetEnd(pcbnew.wxPointMM(b[0], b[1]))
            t.SetWidth(pcbnew.FromMM(larg)); t.SetLayer(pcbnew.F_Cu if L == LAY_F else pcbnew.B_Cu)
            t.SetNetCode(newnet.GetNet()); BRD.Add(t)
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (PITCH * 0.5)))
            for k in range(n + 1):
                marca(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, L, nid)
    # arremate final: fecha do ultimo ponto ate' o centro do pad alvo
    ult = seq[-1]
    cx = (p_fim.rect[0] + p_fim.rect[2]) / 2.0
    cy = (p_fim.rect[1] + p_fim.rect[3]) / 2.0
    t = pcbnew.TRACK(BRD)
    t.SetStart(pcbnew.wxPointMM(ult[2][0], ult[2][1]))
    t.SetEnd(pcbnew.wxPointMM(cx, cy))
    t.SetWidth(pcbnew.FromMM(larg))
    t.SetLayer(pcbnew.F_Cu if ult[3] == LAY_F else pcbnew.B_Cu)
    t.SetNetCode(newnet.GetNet()); BRD.Add(t)

falhas = []
rotas = 0
for _, nm, ps in filas:
    nid = netid[nm]
    larg = largura(nm)
    # quais pads desta net ja' estao conectados entre si por cobre existente?
    pai = list(range(len(ps)))
    def find(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]; x = pai[x]
        return x
    for a in range(len(ps)):
        for b in range(a + 1, len(ps)):
            if conecta(ps[a], ps[b]):
                ra, rb = find(a), find(b)
                if ra != rb:
                    pai[ra] = rb
    grupos = {}
    for k, p in enumerate(ps):
        grupos.setdefault(find(k), []).append(p)
    if len(grupos) < 2:
        continue
    gl = sorted(grupos.values(), key=len, reverse=True)
    arvore = list(gl[0])
    for k in range(1, len(gl)):
        alvo = gl[k][0]
        ci, cj = cells_of(alvo)
        starts = []
        for q in arvore:
            gi, gj = cells_of(q)
            for L in (LAY_F, LAY_B):
                if grid[L, gi, gj] == nid:
                    starts.append((gi, gj, L))
        if not starts:
            starts = [(ci, cj, L) for L in (LAY_F, LAY_B) if grid[L, ci, cj] == nid]
        goals = [(ci, cj, L) for L in alvo.layers]
        path = astro(grid, nid, starts, goals)
        if path is None or path == "LIMITE":
            falhas.append((nm, alvo.ref, "SEM ROTA" if path is None else "LIMITE"))
            continue
        ini = min(arvore, key=lambda q: (cells_of(q)[0] - path[0][0]) ** 2 + (cells_of(q)[1] - path[0][1]) ** 2)
        p_ini = ((ini.rect[0] + ini.rect[2]) / 2.0, (ini.rect[1] + ini.rect[3]) / 2.0)
        emite(nm, nid, larg, path, p_ini, alvo)
        arvore.extend(gl[k])
        rotas += 1
print("nets roteadas nesta passada:", rotas, "| falhas:", len(falhas))
for f in falhas[:40]:
    print("   FALHA:", f)

# ---------------------------------------------------------------- 5) zonas + salva
filler = pcbnew.ZONE_FILLER(BRD); filler.Fill(BRD.Zones())
BRD.Save(OUT + "/v8_drone.kicad_pcb")
print("salvou", OUT + "/v8_drone.kicad_pcb")

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

# ---------------------------------------------------------------- 6) verificacao
objs2 = coleta()
por_net = {}
for o in objs2:
    por_net.setdefault(o.net, []).append(o)

def conecta(a, b):
    g = obj_gap(a, b)
    return g is not None and g <= 0.02

linhas = []
tot_nets = 0; nets_ok = 0; nets_ruins = []
plano_ok = []; plano_ruim = []
for nm, os_ in sorted(por_net.items()):
    if nm == "":
        continue
    pads = [o for o in os_ if o.kind == "pad"]
    if len(pads) < 2:
        continue
    if nm in IGNORA:            # conectadas pelo plano -- nao da' p/ provar aqui
        nv_ = sum(1 for o in os_ if o.kind == "via")
        nv_pads = sum(1 for p in pads if any(o.kind == "via" and math.hypot(
            o.pts[0][0] - (p.rect[0] + p.rect[2]) / 2.0,
            o.pts[0][1] - (p.rect[1] + p.rect[3]) / 2.0) < 1.6 for o in os_))
        (plano_ok if nv_pads == len(pads) else plano_ruim).append((nm, len(pads), nv_pads))
        continue
    tot_nets += 1
    idx = {id(o): i for i, o in enumerate(os_)}
    pai = list(range(len(os_)))
    def find(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]; x = pai[x]
        return x
    def uni(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            pai[rx] = ry
    for a in range(len(os_)):
        for b in range(a + 1, len(os_)):
            if conecta(os_[a], os_[b]):
                uni(a, b)
    raizes = {find(idx[id(p)]) for p in pads}
    if len(raizes) == 1:
        nets_ok += 1
    else:
        nets_ruins.append((nm, len(pads), len(raizes),
                           [p.ref for p in pads[:4]]))
linhas.append("nets de sinal com 2+ pads: %d | CONECTADAS: %d | com mais de um grupo: %d"
              % (tot_nets, nets_ok, len(nets_ruins)))
for nm, np_, ng, ex in nets_ruins[:60]:
    linhas.append("  INCOMPLETA: %-16s pads=%d grupos=%d  ex=%s" % (nm, np_, ng, ex))
linhas.append("nets de PLANO (GND/VBAT_PROT) com 2+ pads: %d | com via propria em todos os pads: %d | sem: %d"
              % (len(plano_ok) + len(plano_ruim), len(plano_ok), len(plano_ruim)))
for nm, np_, nv_ in plano_ruim[:20]:
    linhas.append("  PLANO sem via propria em todo pad: %s pads=%d com_via=%d" % (nm, np_, nv_))

# curto: qualquer par de cobre de nets diferentes com folga < 0,15 mm
import collections
bucket = collections.defaultdict(list)
CELL = 4.0
def bkey(o):
    if o.kind == "pad":
        c = ((o.rect[0] + o.rect[2]) / 2, (o.rect[1] + o.rect[3]) / 2)
    else:
        c = o.pts[0]
    return (int(c[0] / CELL), int(c[1] / CELL))
for o in objs2:
    bucket[bkey(o)].append(o)
viol = []
seen = set()
for o in objs2:
    k = bkey(o)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for p in bucket.get((k[0] + dx, k[1] + dy), []):
                if p is o or p.net == o.net or (not p.net) or (not o.net):
                    continue
                key = (id(o), id(p)) if id(o) < id(p) else (id(p), id(o))
                if key in seen:
                    continue
                seen.add(key)
                g = obj_gap(o, p)
                if g is not None and g < 0.15:
                    viol.append((o.net, o.ref or o.kind, p.net, p.ref or p.kind, round(g, 4)))
linhas.append("pares de cobre de nets DIFERENTES com folga < 0,15 mm: %d" % len(viol))
for v in viol[:60]:
    linhas.append("  CURTO?: %s(%s) x %s(%s)  folga=%.4f mm" % v)

fp = sum(1 for _ in BRD.GetModules())
tr = sum(1 for t in BRD.GetTracks() if t.Type() != pcbnew.PCB_VIA_T)
vi = sum(1 for t in BRD.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
cab = ["PCB v8 -- verificacao geometrica (script rota_v7.py)",
       "footprints: %d | trilhas: %d | vias: %d" % (fp, tr, vi),
       "dimensoes: %.1f x %.1f mm | camadas de cobre: 4 (F_Cu, In1=GND, In2=VBAT_PROT, B_Cu)"
       % (W, H),
       "tolerancia de contato: 0,02 mm | folga alvo entre nets: 0,25 mm",
       ""] + linhas
open(OUT + "/verificacao_v8.txt", "w").write("\n".join(cab) + "\n")
print("\n".join(cab[:8]))
print("relatorio:", OUT + "/verificacao_v8.txt")
