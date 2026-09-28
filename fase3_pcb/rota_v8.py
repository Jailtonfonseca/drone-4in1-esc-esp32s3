#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- ROTEAMENTO AUTOMATICO PROPRIO DO BOARD v8 (6 camadas)  [ROTA v8]
=====================================================================
Derivado de fase3_pcb/rota_v7.py (que NAO e' editado por este script).
Entrada : fase3_pcb/v8/v8_drone.kicad_pcb   (backup em /tmp antes de escrever)
Saida   : fase3_pcb/v8/v8_drone.kicad_pcb, Gerbers, Excellon,
          fase3_pcb/v8/verificacao_v8.txt, fase3_pcb/v8/rota_v8_log.txt

O que faz, em ordem:
  1. carrega a v8;
  2. fecha no plano (via + stub) TODO pad de GND/VBAT_PROT que nao tem via
     propria (gate A4);
  3. rasteriza numa grade (pitch padrao 0,5 mm) com o ID da net de cada celula,
     nas 3 camadas de SINAL do stackup D-02: F.Cu, In2.Cu, B.Cu;
     In1.Cu, In3.Cu (GND) e In4.Cu (VBAT) sao PLANOS e nao sao roteados;
  4. ordena as nets por maldade (2 pontos por distancia; 3+ por MST) e roteia
     com A* multi-origem/multi-destino, com ORCAMENTO DE TEMPO explicito e
     CHECKPOINT incremental do .kicad_pcb a cada N nets (a v7 perdia tudo
     porque so salvava no fim);
  5. emite trilhas/vias reais, marcando na grade o corpo e a faixa de bloqueio
     de cada trilha (a v7 marcava so a linha central -> clearance nao era
     respeitado na verificacao);
  6. re-preenche zonas, salva, exporta Gerber + Excellon;
  7. VERIFICA geometricamente e escreve verificacao_v8.txt.

Uso (deadline = orçamento total de roteamento, em segundos):
  /usr/bin/python3.9 fase3_pcb/rota_v8.py --deadline 900 --pitch 0.5 --clear 0.25
"""
import os
import sys
import math
import time
import heapq
import shutil
import collections

import numpy as np
import pcbnew

# ------------------------------------------------------------------ argumentos
def arg(nome, padrao, tipo=float):
    for a in sys.argv[1:]:
        if a.startswith("--" + nome + "="):
            v = a.split("=", 1)[1]
            return tipo(v)
    return padrao

T0 = time.time()
BASE = os.path.dirname(os.path.abspath(__file__))
SRC = BASE + "/v8/v8_drone.kicad_pcb"
OUT = BASE + "/v8"
BACKUP = "/tmp/v8_drone_pre_rota.kicad_pcb"
LOG = OUT + "/rota_v8_log.txt"
os.makedirs(OUT, exist_ok=True)

PITCH = arg("pitch", 0.5)
CLEAR = arg("clear", 0.25)          # folga minima desejada entre nets diferentes
DEADLINE_S = arg("deadline", 900.0)  # orcamento de tempo do roteamento
MAX_NODES = int(arg("maxnodes", 120000))
CKPT = int(arg("ckpt", 5))          # salvar o .kicad_pcb a cada N nets roteadas
BENCH = int(arg("bench", 0))         # >0: roda so as N primeiras filas (medida)
NL = arg("nlayers", 3)              # 2 = so F.Cu/B.Cu ; 3 = F.Cu/In2.Cu/B.Cu

VIA_COST = arg("viacost", 14.0)
TURN_COST = arg("turncost", 0.35)
T0_POR_NET = 6.0                    # seguranca maxima por net (s)

LOGF = open(LOG, "w")

def log(*a):
    m = "".join(str(x) for x in a)
    print(m)
    LOGF.write(m + "\n")
    LOGF.flush()

# ------------------------------------------------------------------ grade
GX0, GY0 = -2.0, -2.0
GW, GH = 168.0, 152.0
NX = int(GW / PITCH)
NY = int(GH / PITCH)
NC = NY * NX

LAYERS_ALL = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
              pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
# stackup D-02 (STACKUP_PROPOSO.md):
#   F.Cu  sinal | In1.Cu PLANO GND | In2.Cu sinal (stripline) |
#   In3.Cu PLANO GND | In4.Cu PLANO VBAT | B.Cu sinal
if NL >= 3:
    LAY_ROT = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
else:
    LAY_ROT = [pcbnew.F_Cu, pcbnew.B_Cu]
LIDX = dict((l, i) for i, l in enumerate(LAY_ROT))
NL_ROT = len(LAY_ROT)

log("=" * 78)
log("FASE 3 -- ROTEAMENTO DO BOARD v8 (6 camadas)   [ROTA v8]")
log("=" * 78)
log("t0                         : %.1f s" % (time.time() - T0))
log("origem                     : %s" % SRC)
log("orçamento de roteamento    : %.0f s" % DEADLINE_S)
log("grade                      : %.2f x %.2f mm -> %d x %d celulas" % (GW, GH, NX, NY))
log("pitch / clearance alvo     : %.2f / %.2f mm" % (PITCH, CLEAR))
LNAME = {pcbnew.F_Cu: "F.Cu", pcbnew.B_Cu: "B.Cu", pcbnew.In1_Cu: "In1.Cu",
         pcbnew.In2_Cu: "In2.Cu", pcbnew.In3_Cu: "In3.Cu", pcbnew.In4_Cu: "In4.Cu"}
log("camadas roteadas           : %d -> %s" % (NL_ROT, ", ".join(
    LNAME[l] for l in LAY_ROT)))
log("camadas de PLANO (nao roteadas): In1.Cu=GND, In3.Cu=GND, In4.Cu=VBAT")
log("max nodes por A* / seguranca por net: %d / %.1f s" % (MAX_NODES, T0_POR_NET))

if os.path.exists(BACKUP):
    shutil.copy2(BACKUP, SRC)      # idempotente: sempre parte do board limpo
    log("restaurado do backup       : %s -> %s" % (BACKUP, SRC))
else:
    shutil.copy2(SRC, BACKUP)
    log("backup do board original   : %s (criado)" % BACKUP)

BRD = pcbnew.LoadBoard(SRC)
log("pcbnew                     : %s" % pcbnew.GetBuildVersion())

def c2x(i): return GX0 + PITCH / 2 + i * PITCH
def c2y(j): return GY0 + PITCH / 2 + j * PITCH
def x2c(x): return int(round((x - GX0 - PITCH / 2) / PITCH))
def y2c(y): return int(round((y - GY0 - PITCH / 2) / PITCH))
def flat(i, j, L): return (L * NY + j) * NX + i
def unflat(f):
    i = f % NX
    j = (f // NX) % NY
    L = f // (NX * NY)
    return i, j, L
def cl(f):
    """celula -> (x, y) em mm, com clamp"""
    i, j, _ = unflat(f)
    return (c2x(min(max(i, 0), NX - 1)), c2y(min(max(j, 0), NY - 1)))

# ------------------------------------------------------------------ geometria
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
    dx = max(ra[0] - rb[2], rb[0] - ra[2], 0.0)
    dy = max(ra[1] - rb[3], rb[1] - ra[3], 0.0)
    return math.hypot(dx, dy)

def seg_rect_gap(a, b, r):
    x1, y1, x2, y2 = r
    if x1 <= a[0] <= x2 and y1 <= a[1] <= y2:
        return 0.0
    if x1 <= b[0] <= x2 and y1 <= b[1] <= y2:
        return 0.0
    c = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    return min(seg_seg(a, b, c[k], c[(k + 1) % 4]) for k in range(4))

def seg_seg_gap(a, b, wa, c, d, wb):
    return max(0.0, seg_seg(a, b, c, d) - wa / 2.0 - wb / 2.0)

# ------------------------------------------------------------------ objetos
class Obj:
    __slots__ = ("kind", "net", "layers", "pts", "w", "rect", "r", "ref")
    def __init__(self, kind, net, layers, pts=None, w=0.0, rect=None, r=0.0, ref=""):
        self.kind, self.net, self.layers = kind, net, layers
        self.pts, self.w, self.rect, self.r, self.ref = pts, w, rect, r, ref

def lay_rot(pad):
    """camadas roteaveis em que um pad tem cobre"""
    if pad.kind == "via":
        return list(range(NL_ROT))
    r = []
    for l in pad.layers:
        if l in LIDX:
            r.append(LIDX[l])
    return r

def coleta():
    objs = []
    for fp in BRD.GetModules():
        for p in fp.Pads():
            c = p.GetPosition(); s = p.GetSize()
            lay = []
            if p.IsOnLayer(pcbnew.F_Cu): lay.append(pcbnew.F_Cu)
            if p.IsOnLayer(pcbnew.B_Cu): lay.append(pcbnew.B_Cu)
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_STANDARD,
                                    pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED):
                lay = list(LAYERS_ALL)
            w = pcbnew.ToMM(s.x); h = pcbnew.ToMM(s.y)
            objs.append(Obj("pad", p.GetNetname(), lay,
                            rect=(pcbnew.ToMM(c.x) - w / 2, pcbnew.ToMM(c.y) - h / 2,
                                  pcbnew.ToMM(c.x) + w / 2, pcbnew.ToMM(c.y) + h / 2),
                            ref="%s.%s" % (fp.GetReference(), p.GetPadName())))
    for t in BRD.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            c = t.GetPosition(); dia = pcbnew.ToMM(t.GetWidth())
            objs.append(Obj("via", t.GetNetname(), list(LAYERS_ALL),
                            pts=((pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)),) * 2,
                            w=dia, r=dia / 2.0))
        else:
            s, e = t.GetStart(), t.GetEnd()
            lay = [t.GetLayer()]
            objs.append(Obj("trk", t.GetNetname(), lay,
                            pts=((pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)),
                                 (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))),
                            w=pcbnew.ToMM(t.GetWidth())))
    return objs

def conecta(a, b):
    g = obj_gap(a, b)
    return g is not None and g <= 0.02

def obj_gap(a, b):
    if not (set(a.layers) & set(b.layers)):
        return None
    if a.kind == "pad" and b.kind == "pad":
        return rect_gap(a.rect, b.rect)
    if a.kind == "pad" or b.kind == "pad":
        p, s = (a, b) if a.kind == "pad" else (b, a)
        return max(0.0, seg_rect_gap(s.pts[0], s.pts[1], p.rect) - s.w / 2.0)
    if a.kind == "via" and b.kind == "via":
        return max(0.0, math.hypot(a.pts[0][0] - b.pts[0][0],
                                   a.pts[0][1] - b.pts[0][1]) - a.r - b.r)
    if a.kind == "via" or b.kind == "via":
        v, s = (a, b) if a.kind == "via" else (b, a)
        return max(0.0, pt_seg(v.pts[0][0], v.pts[0][1], s.pts[0][0], s.pts[0][1],
                               s.pts[1][0], s.pts[1][1]) - v.r - s.w / 2.0)
    return seg_seg_gap(a.pts[0], a.pts[1], a.w, b.pts[0], b.pts[1], b.w)

# indice espacial (celula de 3 mm) para as buscas de clearance -- evita o O(n^2)
# do v7 na etapa de fecha_no_plano
BC = 3.0
def bkey(x, y):
    return (int(math.floor(x / BC)), int(math.floor(y / BC)))

class Indice(object):
    def __init__(self):
        self.d = collections.defaultdict(list)
    def add(self, o):
        xs = [o.rect[0], o.rect[2]] if o.rect else [o.pts[0][0], o.pts[1][0]]
        ys = [o.rect[1], o.rect[3]] if o.rect else [o.pts[0][1], o.pts[1][1]]
        for kx in range(int(math.floor(min(xs) / BC)), int(math.floor(max(xs) / BC)) + 1):
            for ky in range(int(math.floor(min(ys) / BC)), int(math.floor(max(ys) / BC)) + 1):
                self.d[(kx, ky)].append(o)
    def perto(self, x, y, raio):
        r = int(math.ceil(raio / BC))
        cx, cy = int(math.floor(x / BC)), int(math.floor(y / BC))
        out = []
        for kx in range(cx - r, cx + r + 1):
            for ky in range(cy - r, cy + r + 1):
                out.extend(self.d.get((kx, ky), ()))
        return out

# ------------------------------------------------------------------ 1) vias de plano
def fecha_no_plano(objs, idx):
    """via + stub em cada pad de GND/VBAT_PROT que ainda nao tem via perto"""
    novos = 0
    cands = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1),
             (2, 0), (-2, 0), (0, 2), (0, -2), (1, 2), (-1, 2), (1, -2), (-1, -2),
             (2, 1), (2, -1), (-2, 1), (-2, -1)]
    alvos = [o for o in objs if o.kind == "pad" and o.net in ("GND", "VBAT_PROT")]
    for p in alvos:
        cx = (p.rect[0] + p.rect[2]) / 2.0
        cy = (p.rect[1] + p.rect[3]) / 2.0
        # ja' tem via da mesma net a menos de 2,2 mm?
        tem = False
        for o in idx.perto(cx, cy, 2.2):
            if o.kind == "via" and o.net == p.net:
                if math.hypot(o.pts[0][0] - cx, o.pts[0][1] - cy) < 2.2:
                    tem = True; break
        if tem:
            continue
        metade = max(p.rect[2] - p.rect[0], p.rect[3] - p.rect[1]) / 2.0
        for (dx, dy) in cands:
            d = math.hypot(dx, dy)
            off = metade + 0.35 + d * 0.18
            vx, vy = cx + dx * off, cy + dy * off
            if not (GX0 + 1 < vx < GX0 + GW - 1 and GY0 + 1 < vy < GY0 + GH - 1):
                continue
            v = Obj("via", p.net, list(LAYERS_ALL), pts=((vx, vy),) * 2, w=0.6, r=0.3)
            tre = Obj("trk", p.net, [pcbnew.F_Cu], pts=((cx, cy), (vx, vy)), w=0.3)
            ok = True
            perto = idx.perto((cx + vx) / 2.0, (cy + vy) / 2.0, off + 10.0)
            for o in perto:
                if o.net == p.net or o is p:
                    continue
                g1 = obj_gap(v, o)
                if g1 is not None and g1 < CLEAR * 0.8:
                    ok = False; break
                g2 = obj_gap(tre, o)
                if g2 is not None and g2 < CLEAR * 0.8:
                    ok = False; break
            if ok:
                nn = BRD.FindNet(p.net)
                via = pcbnew.VIA(BRD)
                via.SetPosition(pcbnew.wxPointMM(vx, vy))
                via.SetDrill(pcbnew.FromMM(0.3)); via.SetWidth(pcbnew.FromMM(0.6))
                via.SetViaType(pcbnew.VIA_THROUGH)
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                via.SetNetCode(nn.GetNet()); BRD.Add(via)
                t = pcbnew.TRACK(BRD)
                t.SetStart(pcbnew.wxPointMM(cx, cy)); t.SetEnd(pcbnew.wxPointMM(vx, vy))
                t.SetWidth(pcbnew.FromMM(0.3)); t.SetLayer(pcbnew.F_Cu)
                t.SetNetCode(nn.GetNet()); BRD.Add(t)
                idx.add(v); idx.add(tre)
                objs.append(v); objs.append(tre)
                novos += 1
                break
    return novos

objs = coleta()
log("objetos carregados         : %d (%d pads, %d trilhas/vias)" % (
    len(objs), sum(1 for o in objs if o.kind == "pad"),
    sum(1 for o in objs if o.kind != "pad")))

idx = Indice()
for o in objs:
    idx.add(o)
tpl = time.time()
n_plano = fecha_no_plano(objs, idx)
log("vias+stubs de PLANO criados: %d  (em %.1f s)  -- gate A4" % (n_plano, time.time() - tpl))

# ------------------------------------------------------------------ 2) grade
def rasteriza(objs):
    grid = np.zeros((NL_ROT, NX, NY), dtype=np.int32)
    casca = np.zeros((NL_ROT, NX, NY), dtype=np.int32)   # dono da casca (-2)
    netid = {}
    for o in objs:
        if o.net:
            netid.setdefault(o.net, len(netid) + 1)
    m = int(1.2 / PITCH) + 1
    grid[:, :m, :] = -1; grid[:, -m:, :] = -1
    grid[:, :, :m] = -1; grid[:, :, -m:] = -1
    casca[:] = 0
    mlog = [o for o in objs if o.kind == "pad" and o.net]
    mlog.sort(key=lambda o: o.net)
    for o in mlog:
        nid = netid[o.net]
        r = o.rect
        # celula que contem o centro do pad: SEMPRE e' desta net
        ic = min(max(x2c((r[0] + r[2]) / 2.0), 0), NX - 1)
        jc = min(max(y2c((r[1] + r[3]) / 2.0), 0), NY - 1)
        for L in lay_rot(o):
            if grid[L, ic, jc] <= 0:
                grid[L, ic, jc] = nid
        i0 = max(0, min(NX - 1, x2c(r[0] - CLEAR) - 1))
        i1 = max(0, min(NX - 1, x2c(r[2] + CLEAR) + 1))
        j0 = max(0, min(NY - 1, y2c(r[1] - CLEAR) - 1))
        j1 = max(0, min(NY - 1, y2c(r[3] + CLEAR) + 1))
        if i1 < i0 or j1 < j0:
            continue
        for L in lay_rot(o):
            sub = grid[L, i0:i1 + 1, j0:j1 + 1]
            ii = np.arange(i0, i1 + 1)
            jj = np.arange(j0, j1 + 1)
            X = GX0 + PITCH / 2 + ii * PITCH
            Y = GY0 + PITCH / 2 + jj * PITCH
            dentro = ((X >= r[0]) & (X <= r[2]))[:, None] & \
                     ((Y >= r[1]) & (Y <= r[3]))[None, :]
            perto = (np.abs(X - (r[0] + r[2]) / 2)[:, None] <= (r[2] - r[0]) / 2 + CLEAR) & \
                    (np.abs(Y - (r[1] + r[3]) / 2)[None, :] <= (r[3] - r[1]) / 2 + CLEAR)
            sub[dentro] = np.where(sub[dentro] <= 0, nid, sub[dentro])
            fora = perto & ~dentro
            novo = fora & (sub == 0)
            sub[novo] = -2
            csub = casca[L, i0:i1 + 1, j0:j1 + 1]
            csub[novo] = nid
    # trilhas e vias: AABB expandida (exata para trilhas ortogonais da grade)
    for o in objs:
        if o.kind == "pad":
            continue
        nid = netid.get(o.net, 0)
        if o.kind == "via":
            x, y = o.pts[0]
            r = (x - o.r, y - o.r, x + o.r, y + o.r)
        else:
            r = (min(o.pts[0][0], o.pts[1][0]) - o.w / 2,
                 min(o.pts[0][1], o.pts[1][1]) - o.w / 2,
                 max(o.pts[0][0], o.pts[1][0]) + o.w / 2,
                 max(o.pts[0][1], o.pts[1][1]) + o.w / 2)
        i0 = max(0, x2c(r[0] - CLEAR) - 1); i1 = min(NX - 1, x2c(r[2] + CLEAR) + 1)
        j0 = max(0, y2c(r[1] - CLEAR) - 1); j1 = min(NY - 1, y2c(r[3] + CLEAR) + 1)
        if i1 < i0 or j1 < j0:
            continue
        for L in lay_rot(o):
            sub = grid[L, i0:i1 + 1, j0:j1 + 1]
            if nid:
                sub[sub == 0] = nid
            novo = sub == 0
            sub[novo] = -2
            csub = casca[L, i0:i1 + 1, j0:j1 + 1]
            csub[novo] = nid
    return grid, netid, casca

tpl = time.time()
grid, netid, casca = rasteriza(objs)
id2net = dict((v, k) for k, v in netid.items())
liv = int((grid == 0).sum()); bloq = int((grid == -1).sum())
ocup = int((grid > 0).sum())
log("rasterizacao               : %.1f s | celulas %d (livre %d, bloqueada %d, de net %d)"
    % (time.time() - tpl, grid.size, liv, bloq, ocup))
log("densidade de bloqueio     : %.1f %% do grid" % (100.0 * (bloq) / grid.size))

# ------------------------------------------------------------------ 3) A*
def astro(nid, starts, goals, max_nodes, deadline):
    if not goals:
        return None
    gs = set(goals)
    if not gs:
        return None
    if len(goals) == 1:
        gi0, gj0, _ = unflat(goals[0])
        h = lambda i, j: abs(i - gi0) + abs(j - gj0)
    else:
        gxy = [(unflat(g)[0], unflat(g)[1]) for g in goals]
        def h(i, j):
            return min(abs(i - a) + abs(j - b) for (a, b) in gxy)
    openq = []
    best = {}
    came = {}
    for s in starts:
        i, j, _ = unflat(s)
        heapq.heappush(openq, (h(i, j), 0.0, s, -1))
    nodes = 0
    push = heapq.heappush
    pop = heapq.heappop
    tcheck = 0
    while openq:
        f, g, cur, prev = pop(openq)
        if best.get(cur, 1e18) < g:
            continue
        best[cur] = g
        came[cur] = prev
        if cur in gs:
            path = []
            k = cur
            while k != -1:
                path.append(k); k = came[k]
            path.reverse()
            return path
        nodes += 1
        if nodes >= max_nodes:
            return "LIMITE"
        tcheck += 1
        if tcheck >= 4096:
            tcheck = 0
            if time.time() > deadline:
                return "TEMPO"
        i, j, L = unflat(cur)
        Lb = L * NC
        for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni = i + di; nj = j + dj
            if ni < 0 or ni >= NX or nj < 0 or nj >= NY:
                continue
            key = Lb + nj * NX + ni
            v = GF[key]
            if v == -1 or (v > 0 and v != nid):
                continue
            caro = 0.0
            if v == -2:
                if CASCA[key] != nid:
                    continue
                caro = 0.5
            ng = g + 1.0 + caro
            if prev >= 0:
                pi, pj, _ = unflat(prev)
                if di and pi != ni:
                    ng += TURN_COST
                if dj and pj != nj:
                    ng += TURN_COST
            if best.get(key, 1e18) > ng:
                push(openq, (ng + h(ni, nj), ng, key, cur))
        # troca de camada (um via atravessa F.Cu/In2.Cu/B.Cu)
        if 2 <= i < NX - 2 and 2 <= j < NY - 2:
            ok = VOK[i * NY + j]
            if ok:
                for oL in range(NL_ROT):
                    if oL == L:
                        continue
                    key = oL * NC + j * NX + i
                    ng = g + VIA_COST
                    if best.get(key, 1e18) > ng:
                        push(openq, (ng + h(i, j), ng, key, cur))
    return None

# ------------------------------------------------------------------ 4) roteia
pads_net = {}
for o in objs:
    if o.kind == "pad" and o.net:
        pads_net.setdefault(o.net, []).append(o)

IGNORA = ("GND", "VBAT_PROT")            # fechadas por plano (In1/In3/In4)
POTENCIA = ("12V", "5V", "3V3", "3V3_A", "VBAT_F", "VBAT_SENSE", "5V_AUX")
MOTOR = tuple([n for n in pads_net if n.startswith("VBM")])

LARG = {"12V": 0.25, "5V": 0.40, "5V_AUX": 0.25, "3V3": 0.25, "3V3_A": 0.25,
        "VBAT_F": 0.60, "VBAT_SENSE": 0.60}

def largura(nm):
    if nm in LARG:
        return LARG[nm]
    if nm.startswith("VBM") or nm.startswith("RB_M"):
        return 0.60          # corrente de fase -- ver NOTA_ROTAS_v8.md secao 4
    return 0.20

def grupos_de(ps):
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
    g = {}
    for k, p in enumerate(ps):
        g.setdefault(find(k), []).append(p)
    return list(g.values())

def cx(p): return (p.rect[0] + p.rect[2]) / 2.0
def cy(p): return (p.rect[1] + p.rect[3]) / 2.0

def mst_len(ps):
    """comprimento da arvore geradora minima -> medida de maldade"""
    pts = [(cx(p), cy(p)) for p in ps]
    if len(pts) < 2:
        return 0.0
    dentro = [0]
    fora = list(range(1, len(pts)))
    tot = 0.0
    while fora:
        best = None
        for i in dentro:
            for j in fora:
                d = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
                if best is None or d < best[0]:
                    best = (d, j)
        tot += best[0]
        dentro.append(best[1]); fora.remove(best[1])
    return tot

# ordem: nets de 2 pontos primeiro (as mais curtas liberam espaco), depois 3+ por MST
filas = []
for nm, ps in pads_net.items():
    if nm in IGNORA or len(ps) < 2:
        continue
    gs = grupos_de(ps)
    if len(gs) < 2:
        continue
    if len(ps) == 2:
        mal = math.hypot(cx(ps[0]) - cx(ps[1]), cy(ps[0]) - cy(ps[1]))
        filas.append((0, mal, nm, ps, gs))
    else:
        filas.append((1, mst_len(ps), nm, ps, gs))
filas.sort(key=lambda r: (r[0], r[1]))
n_total = len(filas)
if BENCH:
    filas = filas[:BENCH]
n_alvo = len(filas)
log("nets a rotear              : %d de %d  (2 pontos: %d | 3+ pontos: %d)%s" % (
    n_alvo, n_total, sum(1 for f in filas if f[0] == 0),
    sum(1 for f in filas if f[0] == 1),
    "   [MODO BENCH: %d primeiras]" % BENCH if BENCH else ""))

GRID = grid
# listas de Python: acesso a numpy-scalar custa ~10x mais que int nativo e
# dominava o tempo do A* (medido: <20 mil nos/s com numpy, >150 mil com int)
GF = grid.reshape(-1).tolist()
CASCA_ARR = casca                      # numpy: escrito por marca_corpo_py
CASCA = casca.reshape(-1).tolist()     # lista: so' leitura no A*
_tv = time.time()
_livre = (grid <= 0) | (grid == -2)
_vok = np.ones((NX, NY), dtype=bool)
for _d in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
    _vok &= np.roll(np.roll(_livre, -_d[0], axis=1), -_d[1], axis=2).all(axis=0)
_vok[:2, :] = False; _vok[-2:, :] = False
_vok[:, :2] = False; _vok[:, -2:] = False
VOK = _vok.reshape(-1).tolist()
log("mascara de via (VOK)       : %.1f s | %d celulas com via possivel (%.1f %%)"
    % (time.time() - _tv, int(np.sum(VOK)), 100.0 * float(np.sum(VOK)) / len(VOK)))
def cells_of(p):
    return (min(max(x2c(cx(p)), 0), NX - 1), min(max(y2c(cy(p)), 0), NY - 1))

def marca_corpo(x, y, L, w, nid, nout):
    """marca a trilha (corpo) e bloqueia a faixa de clearance ao redor"""
    rbody = int(math.floor((w / 2.0 + 1e-9) / PITCH))
    rbloq = int(math.ceil((w / 2.0 + CLEAR) / PITCH))
    gi, gj = min(max(x2c(x), 0), NX - 1), min(max(y2c(y), 0), NY - 1)
    i0 = max(0, min(NX - 1, gi - rbloq)); i1 = max(0, min(NX - 1, gi + rbloq))
    j0 = max(0, min(NY - 1, gj - rbloq)); j1 = max(0, min(NY - 1, gj + rbloq))
    if i1 < i0 or j1 < j0:
        return
    sub = GRID[L, i0:i1 + 1, j0:j1 + 1]
    ii = np.arange(i0, i1 + 1); jj = np.arange(j0, j1 + 1)
    d = np.maximum(np.abs(ii - gi)[:, None], np.abs(jj - gj)[None, :])
    sub[(d <= rbody) & (sub <= 0)] = nid
    faixa = (d > rbody) & (d <= rbloq)
    novo = faixa & (sub == 0)
    sub[novo] = -2
    csub = CASCA_ARR[L, i0:i1 + 1, j0:j1 + 1]
    csub[novo] = nid
    sub[faixa & (sub == -2) & (csub != nid)] = -1
    atualiza_vok(x, y, w)
    if d[(d > rbody) & (d <= rbloq)].size:
        nout[0] += int((sub == -1).sum()) if False else 0

def atualiza_vok(x, y, w):
    """apos colocar cobre em (x,y) com largura w, a area perde o status de
    'via cabe' (um via precisa de todas as 3 camadas limpas num raio)"""
    raio = int(math.ceil((w / 2.0 + 0.6) / PITCH)) + 1
    gi, gj = x2c(x), y2c(y)
    for dj in range(-raio, raio + 1):
        jj = gj + dj
        if jj < 0 or jj >= NY:
            continue
        b = jj * NY
        for di in range(-raio, raio + 1):
            ii = gi + di
            if ii < 0 or ii >= NX:
                continue
            VOK[b + ii] = 0

def marca_corpo_py(x, y, L, w, nid):
    rbody = int(math.floor((w / 2.0 + 1e-9) / PITCH))
    rbloq = int(math.ceil((w / 2.0 + CLEAR) / PITCH))
    gi, gj = min(max(x2c(x), 0), NX - 1), min(max(y2c(y), 0), NY - 1)
    i0 = max(0, min(NX - 1, gi - rbloq)); i1 = max(0, min(NX - 1, gi + rbloq))
    j0 = max(0, min(NY - 1, gj - rbloq)); j1 = max(0, min(NY - 1, gj + rbloq))
    if i1 < i0 or j1 < j0:
        return
    sub = GRID[L, i0:i1 + 1, j0:j1 + 1]
    ii = np.arange(i0, i1 + 1); jj = np.arange(j0, j1 + 1)
    d = np.maximum(np.abs(ii - gi)[:, None], np.abs(jj - gj)[None, :])
    sub[(d <= rbody) & (sub <= 0)] = nid
    faixa = (d > rbody) & (d <= rbloq)
    novo = faixa & (sub == 0)
    sub[novo] = -2
    csub = CASCA_ARR[L, i0:i1 + 1, j0:j1 + 1]
    csub[novo] = nid
    sub[faixa & (sub == -2) & (csub != nid)] = -1
    atualiza_vok(x, y, w)

def emite(nm, nid, larg, path, p_ini, p_fim):
    nn = BRD.FindNet(nm)
    seq = []
    L0 = unflat(path[0])[2]
    lx, ly = unflat(path[0])[0], unflat(path[0])[1]
    cur = (p_ini[0], p_ini[1])
    ll = L0
    for f in path[1:]:
        i, j, L = unflat(f)
        if L != ll:
            seq.append(("trk", cur, (c2x(lx), c2y(ly)), ll))
            seq.append(("via", (c2x(lx), c2y(ly)), None, ll))
            cur = (c2x(lx), c2y(ly)); ll = L
        lx, ly = i, j
    seq.append(("trk", cur, (c2x(lx), c2y(ly)), ll))
    ntr = 0
    for kind, a, b, L in seq:
        lay = LAY_ROT[L]
        if kind == "via":
            v = pcbnew.VIA(BRD)
            v.SetPosition(pcbnew.wxPointMM(a[0], a[1]))
            v.SetDrill(pcbnew.FromMM(0.3)); v.SetWidth(pcbnew.FromMM(0.6))
            v.SetViaType(pcbnew.VIA_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNetCode(nn.GetNet()); BRD.Add(v)
            for Lx in range(NL_ROT):
                marca_corpo_py(a[0], a[1], Lx, 0.6, nid)
        else:
            t = pcbnew.TRACK(BRD)
            t.SetStart(pcbnew.wxPointMM(a[0], a[1]))
            t.SetEnd(pcbnew.wxPointMM(b[0], b[1]))
            t.SetWidth(pcbnew.FromMM(larg)); t.SetLayer(lay)
            t.SetNetCode(nn.GetNet()); BRD.Add(t)
            ntr += 1
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (PITCH * 0.5)))
            for k in range(n + 1):
                marca_corpo_py(a[0] + (b[0] - a[0]) * k / n,
                               a[1] + (b[1] - a[1]) * k / n, L, larg, nid)
    # arremate: do ultimo ponto ate' o centro do pad alvo
    ult = seq[-1]
    pcx, pcy = cx(p_fim), cy(p_fim)
    t = pcbnew.TRACK(BRD)
    t.SetStart(pcbnew.wxPointMM(ult[2][0], ult[2][1]))
    t.SetEnd(pcbnew.wxPointMM(pcx, pcy))
    t.SetWidth(pcbnew.FromMM(larg)); t.SetLayer(LAY_ROT[ult[3]])
    t.SetNetCode(nn.GetNet()); BRD.Add(t)
    marca_corpo_py(pcx, pcy, ult[3], larg, nid)
    return ntr

deadline = T0 + DEADLINE_S
rotas = 0
falhas = []
por_fase = {"2p": [0, 0], "3p": [0, 0]}     # [ok, total]
t_rt = time.time()
ultimo_t = t_rt
n_trk = 0

def checkpoint(rotas, forcado=False):
    global ultimo_t
    if not forcado and (rotas % CKPT) != 0:
        return
    BRD.Save(SRC)
    agora = time.time()
    log("[progresso] t=%6.1f s | filas=%3d/%3d | rotas=%3d | falhas=%3d | "
        "trilhas=%5d | restam %5.1f s"
        % (agora - T0, fidx + 1, n_alvo, rotas, len(falhas),
           sum(1 for x in BRD.GetTracks() if x.Type() != pcbnew.PCB_VIA_T),
           deadline - agora))
    ultimo_t = agora

fidx = -1
for fidx, (fase, mal, nm, ps, gs) in enumerate(filas):
    agora = time.time()
    if agora > deadline:
        log("[orcamento] DEADLINE de %.0f s estourado na fila %d/%d (net %s) "
            "-- o que foi roteado ate' aqui JA' esta salvo no .kicad_pcb"
            % (DEADLINE_S, fidx + 1, n_alvo, nm))
        break
    key = "2p" if fase == 0 else "3p"
    por_fase[key][1] += 1
    nid = netid[nm]
    larg = largura(nm)
    gl = sorted(gs, key=len, reverse=True)
    arvore = list(gl[0])
    dn = agora + T0_POR_NET
    parou = False
    for k in range(1, len(gl)):
        alvo = gl[k][0]
        ci, cj = cells_of(alvo)
        starts = []
        for q in arvore:
            gi, gj = cells_of(q)
            for L in range(NL_ROT):
                if grid[L, gi, gj] == nid:
                    starts.append(flat(gi, gj, L))
        if not starts:
            for L in range(NL_ROT):
                if grid[L, ci, cj] == nid:
                    starts.append(flat(ci, cj, L))
        goals = [flat(ci, cj, L) for L in lay_rot(alvo)] or [flat(ci, cj, 0)]
        startset = set(starts)
        path = astro(nid, starts, goals, MAX_NODES, min(dn, deadline))
        if path is None or path == "LIMITE" or path == "TEMPO":
            motivo = ("SEM ROTA" if path is None else
                      ("LIMITE DE NOS" if path == "LIMITE" else "TEMPO"))
            falhas.append((nm, alvo.ref, motivo))
            if path == "TEMPO":
                parou = True
                log("[orcamento] TEMPO esgotado no A* da net %s (fila %d/%d)"
                    % (nm, fidx + 1, n_alvo))
                break
            continue
        ini = min(arvore, key=lambda q: (cells_of(q)[0] - unflat(path[0])[0]) ** 2
                  + (cells_of(q)[1] - unflat(path[0])[1]) ** 2)
        n_trk += emite(nm, nid, larg, path, (cx(ini), cy(ini)), alvo)
        arvore.extend(gl[k])
        rotas += 1
        por_fase[key][0] += 1
    if parou:
        break
    checkpoint(rotas)

if fidx + 1 >= n_alvo or True:
    checkpoint(rotas, forcado=True)

log("-" * 78)
log("roteamento terminou em %.1f s | rotas emitidas: %d | falhas: %d" % (
    time.time() - T0, rotas, len(falhas)))
log("  2 pontos : %d/%d rotas" % (por_fase["2p"][0], por_fase["2p"][1]))
log("  3+ pontos: %d/%d rotas" % (por_fase["3p"][0], por_fase["3p"][1]))
mot = [f for f in falhas if f[0].startswith("VBM") or f[0] in ("VBAT_F", "VBAT_SENSE")]
log("  falhas em nets de CORRENTE (VBM*/VBAT_F/VBAT_SENSE): %d" % len(mot))
for f in falhas[:60]:
    log("   FALHA: %-14s %-18s %s" % f)
log("checkpoint gravado         : %s" % SRC)

# ------------------------------------------------------------------ 5) zonas + salva
tpl = time.time()
try:
    filler = pcbnew.ZONE_FILLER(BRD)
    filler.Fill(BRD.Zones())
except Exception as e:
    log("aviso ao preencher zonas: %s" % e)
BRD.Save(SRC)
log("zonas + save               : %.1f s -> %s" % (time.time() - tpl, SRC))

pc = pcbnew.PLOT_CONTROLLER(BRD)
po = pc.GetPlotOptions()
po.SetOutputDirectory(OUT)
po.SetPlotFrameRef(False); po.SetAutoScale(False)
po.SetScale(1); po.SetMirror(False)
po.SetUseGerberAttributes(False)
po.SetUseGerberProtelExtensions(True); po.SetExcludeEdgeLayer(False)
po.SetSubtractMaskFromSilk(True); po.SetCreateGerberJobFile(False)
for layer in LAYERS_ALL + [pcbnew.F_Mask, pcbnew.B_Mask, pcbnew.F_SilkS,
                           pcbnew.B_SilkS, pcbnew.Edge_Cuts]:
    pc.SetLayer(layer)
    pc.OpenPlotfile("drone_%s" % BRD.GetLayerName(layer),
                    pcbnew.PLOT_FORMAT_GERBER, "drone")
    pc.PlotLayer()
pc.ClosePlot()
dw = pcbnew.EXCELLON_WRITER(BRD)
dw.SetOptions(False, False, pcbnew.wxPoint(0, 0), False)
dw.CreateDrillandMapFilesSet(OUT, True, False)
n_ger = len([f for f in os.listdir(OUT) if f.endswith((".gbr", ".gtl", ".gbl", ".gto",
                                                        ".gbo", ".gts", ".gbs", ".gm1"))])
log("gerbers/excellon exportados: %d arquivos em %s" % (n_ger, OUT))

# ------------------------------------------------------------------ 6) verificacao
objs2 = coleta()
por_net = collections.defaultdict(list)
for o in objs2:
    por_net[o.net].append(o)

def conecta2(a, b):
    g = obj_gap(a, b)
    return g is not None and g <= 0.02

linhas = []
tot_nets = 0; nets_ok = 0; nets_ruins = []
plano_ruim = []
for nm, os_ in sorted(por_net.items()):
    if nm == "":
        continue
    pads = [o for o in os_ if o.kind == "pad"]
    if len(pads) < 2:
        continue
    if nm in IGNORA:
        nv_pads = sum(1 for p in pads
                      if any(o.kind == "via" and math.hypot(
                          o.pts[0][0] - cx(p), o.pts[0][1] - cy(p)) < 1.6
                          for o in os_))
        if nv_pads != len(pads):
            plano_ruim.append((nm, len(pads), nv_pads))
        continue
    tot_nets += 1
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
            if conecta2(os_[a], os_[b]):
                uni(a, b)
    raizes = set(find(k) for k, o in enumerate(os_) if o.kind == "pad")
    if len(raizes) == 1:
        nets_ok += 1
    else:
        nets_ruins.append((nm, len(pads), len(raizes), [p.ref for p in pads[:4]]))

NETS_NAO_ROTEADAS = len(nets_ruins)
linhas.append("nets de sinal com 2+ pads: %d | conectadas: %d | NAO roteadas: %d"
              % (tot_nets, nets_ok, NETS_NAO_ROTEADAS))
for nm, np_, ng, ex in sorted(nets_ruins, key=lambda r: -r[2])[:80]:
    linhas.append("  NAO ROTEADA: %-14s pads=%d grupos=%d ex=%s" % (nm, np_, ng, ex))
linhas.append("nets de PLANO (GND/VBAT_PROT) com 2+ pads: %d | sem via propria em algum pad: %d"
              % (2, len(plano_ruim)))
for nm, np_, nv_ in plano_ruim[:20]:
    linhas.append("  PLANO sem via em todo pad: %s pads=%d com_via=%d" % (nm, np_, nv_))

# clearance: pares de cobre de nets diferentes
bucket = collections.defaultdict(list)
CELL = 4.0
def bk(o):
    if o.kind == "pad":
        c = (cx(o), cy(o))
    else:
        c = o.pts[0]
    return (int(c[0] / CELL), int(c[1] / CELL))
for o in objs2:
    bucket[bk(o)].append(o)
viol = []
seen = set()
minfolga = 99.0
for o in objs2:
    k = bk(o)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for p in bucket.get((k[0] + dx, k[1] + dy), ()):
                if p is o or p.net == o.net or (not p.net) or (not o.net):
                    continue
                key = (id(o), id(p)) if id(o) < id(p) else (id(p), id(o))
                if key in seen:
                    continue
                seen.add(key)
                g = obj_gap(o, p)
                if g is None:
                    continue
                if g < minfolga:
                    minfolga = g
                if g < 0.15:
                    viol.append((o.net, o.ref or o.kind, p.net, p.ref or p.kind, round(g, 4)))
linhas.append("pares de cobre de nets DIFERENTES com folga < 0,15 mm: %d" % len(viol))
linhas.append("menor folga encontrada entre nets diferentes: %.4f mm" % minfolga)
for v in viol[:60]:
    linhas.append("  CURTO?: %s(%s) x %s(%s)  folga=%.4f mm" % v)

# gate A4: pads de GND/VBAT_PROT sem via a menos de 1,6 mm
n_pads_pl = 0
pad_pl = []
for o in objs2:
    if o.kind == "pad" and o.net in IGNORA:
        n_pads_pl += 1
        pad_pl.append(o)
vias_all = [o for o in objs2 if o.kind == "via"]
sem_via = 0
for p in pad_pl:
    px, py = cx(p), cy(p)
    if not any(o.net == p.net and math.hypot(o.pts[0][0] - px, o.pts[0][1] - py) < 1.6
               for o in vias_all):
        sem_via += 1
A4 = sem_via
dv_pl = 99.0
for p in pad_pl:
    px, py = cx(p), cy(p)
    for o in vias_all:
        if o.net == p.net:
            d = math.hypot(o.pts[0][0] - px, o.pts[0][1] - py)
            if d < dv_pl:
                dv_pl = d
linhas.append("pads de GND/VBAT_PROT: %d | sem via a menos de 1,6 mm: %d | menor dist: %.3f mm"
              % (n_pads_pl, A4, dv_pl))

fp = sum(1 for _ in BRD.GetModules())
tr = sum(1 for t in BRD.GetTracks() if t.Type() != pcbnew.PCB_VIA_T)
vi = sum(1 for t in BRD.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
bbs = BRD.GetBoardEdgesBoundingBox()
Wmm = pcbnew.ToMM(bbs.GetWidth()); Hmm = pcbnew.ToMM(bbs.GetHeight())
n_nets = BRD.GetNetCount() - 1
n_cobre = len(LAYERS_ALL)
n_pads_total = sum(1 for f in BRD.GetModules() for _ in f.Pads())

# conferencia com a netlist de producao
conf = "(netlist v7 nao encontrada)"
pnet = BASE + "/v7/v7_drone.net"
if os.path.exists(pnet):
    nets_pnet = set()
    for ln in open(pnet, errors="ignore"):
        ln = ln.strip()
        if ln.startswith("(net (code") and '"' in ln:
            try:
                nets_pnet.add(ln.split('"')[1])
            except Exception:
                pass
    nets_brd = set(por_net.keys()) - {""}
    conf = ("netlist de producao %s: %d nets | board: %d | "
            "so no board: %d | so na netlist: %d"
            % (os.path.basename(pnet), len(nets_pnet), len(nets_brd),
               len(nets_brd - nets_pnet), len(nets_pnet - nets_brd)))
    if nets_brd - nets_pnet:
        conf += "\n  nets so no board: %s" % sorted(nets_brd - nets_pnet)[:20]
    if nets_pnet - nets_brd:
        conf += "\n  nets so na netlist (nao declaradas no board): %s" % sorted(nets_pnet - nets_brd)[:30]

cab = ["=" * 78,
       "FASE 3 -- VERIFICACAO DA v8 APOS ROTEAMENTO   [VERIF]",
       "=" * 78,
       "gerado por                : fase3_pcb/rota_v8.py (nao maquiado)",
       "board                      : %s" % SRC,
       "pcbnew                     : %s" % pcbnew.GetBuildVersion(),
       "rota_v8 (tempo total)      : %.1f s" % (time.time() - T0),
       "orçamento de roteamento    : %.0f s" % DEADLINE_S,
       "grade / pitch / clearance  : %.0fx%.0f cel / %.2f mm / %.2f mm"
       % (NX, NY, PITCH, CLEAR),
       "camadas roteadas           : %d (%s)" % (NL_ROT, ", ".join(
           LNAME[l] for l in LAY_ROT)),
       "camadas de PLANO          : In1.Cu=GND, In3.Cu=GND, In4.Cu=VBAT",
       ""]
cab += linhas
cab += ["", "=" * 78,
        "LINHAS QUE OS GATES LEEM",
        "=" * 78,
        "nets NAO roteadas : %d" % NETS_NAO_ROTEADAS,
        "pares trilha x pad (net diferente) proximos: %d" % len(viol),
        "pads de GND/VBAT_PROT sem via a menos de 1.6 mm: %d" % A4,
        "rule_area (keepouts): %d" % sum(
            1 for z in BRD.Zones() if z.GetIsKeepout()),
        "camadas de cobre: %d" % n_cobre,
        "dimensoes: %.2f x %.2f mm" % (Wmm, Hmm),
        "footprints / pads / tracks / vias: %d / %d / %d / %d"
        % (fp, n_pads_total, tr, vi),
        "", "apoio a medicao",
        "  nets declaradas no board          : %d" % n_nets,
        "  nets de sinal com 2+ pads         : %d" % tot_nets,
        "  trilhas / vias                     : %d / %d" % (tr, vi),
        "  trilhas por net (media)            : %.1f" % (tr / float(max(1, n_nets))),
        "  menor folga entre nets diferentes  : %.4f mm" % minfolga,
        "  menor dist pad de PLANO -> via     : %.3f mm (limite 1,60)" % dv_pl,
        "  pads de GND/VBAT_PROT no board     : %d" % n_pads_pl,
        "  copper_thickness / impedance       : ver v8_drone_stackup.txt",
        "  conference com netlist             : " + conf,
        "", "=" * 78,
        "VEREDITO POR CRITERIO (nao maquiado)",
        "=" * 78,
        "  [%s] A4  pads GND/VBAT_PROT sem via < 1,6 mm        %d   (criterio: 0)"
        % ("OK  " if A4 == 0 else "FALHA", A4),
        "  [%s] A3  trilhas x pads < 0,15 mm                  %d   (criterio: 0)"
        % ("OK  " if len(viol) == 0 else "FALHA", len(viol)),
        "  [%s] A2  todas as nets roteadas                   %d/%d"
        % ("OK  " if NETS_NAO_ROTEADAS == 0 else "FALHA", tot_nets - NETS_NAO_ROTEADAS, tot_nets),
        "  [%s] camadas de cobre                              %d   (criterio: 6)"
        % ("OK  " if n_cobre == 6 else "FALHA", n_cobre),
        "  [%s] footprints preservados                        %d   (criterio: 319)"
        % ("OK  " if fp == 319 else "FALHA", fp),
        "",
        "  VEREDITO: %s" % ("TODOS OS CRITERIOS DE ROTEAMENTO OK" if (
            A4 == 0 and len(viol) == 0 and NETS_NAO_ROTEADAS == 0) else
            "HA CRITERIOS EM FALHA (ver acima)"),
        "=" * 78]
txt = "\n".join(cab) + "\n"
open(OUT + "/verificacao_v8.txt", "w").write(txt)
log("")
log("\n".join(cab[-16:]))
log("relatorio: %s/verificacao_v8.txt" % OUT)
log("log      : %s" % LOG)
LOGF.close()
