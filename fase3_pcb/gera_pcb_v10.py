#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
FASE 3 -- v10: board de 6 camadas, 190 x 145 mm — CORRECOES DA AUDITORIA.

DERIVA de fase3_pcb/gera_pcb_v9.py (leia aquele antes deste). A v9 e'
somente-leitura aqui. A v10 carrega a v7 (com a netlist ja corrigida pelo
gera_pcb_v7.py — typo RB_M###/RBM### e ferrite 3V3_IMU, ver abaixo), reaplica
as MESMAS decisoes da v9 e CORRIGE os erros apontados pela auditoria de
2026-10-04 (AUDITORIA_ERROS_2026-10-04.md):

 1. [C1/E2] SINAL DO EMPACOTADOR: `placed = X - dx` deslocava cada footprint
    centrado uma bbox inteira para a esquerda/cima — 27 footprints / 199 pads
    caiam FORA do contorno (QM101H em y=-3,16; U_MCU em x=-13,25). Corrigido
    para `X + dx` (a ancora fica em shelf + dx, a bbox cai no shelf).
 2. [C1/E2] BBOX POR PADS: GetBoundingBox() inclui os textos de silkscreen
    (o texto do value "NVMFS6H824NT1G" media o SOIC-8 como 13,6 mm de largura;
    espacamento observado entre MOSFETs era 14,08 mm = texto + GAP). Agora a
    bbox e' a uniao dos pads (circulo circunscrito por pad) + MARGEM_BBOX.
 3. [E8] FALTAVA o keepout da borda SUPERIOR (só existiam esq/dir/inf).
 4. [E6] acha_via usava limite 0,8 mm, menor que o keepout (0,9 mm + folga
    0,3 mm): 8 vias GND foram criadas DENTRO do keepout esquerdo. Agora o
    limite respeita keepout + clearance + raio da via.
 5. [C6] AS NETS DE POTENCIA NAO TIAM COBRE NENHUM (o registro 1.g era falso
    para 26 das 28 nets excluidas do DSN): adicionadas zonas locais para
    VBAT, VBAT_F e as 24 nets de fase PHM*/SNM*. O caminho de 30 A e as 24
    fases agora têm cobre planejado; o refinamento fino continua no roteador.
 6. [C2] NETLIST: 190 nets (era 202 — as 12 RBM### fundiram nas RB_M### do
    typo; a 3V3_A_F orfa virou 3V3_IMU alimentando IMU + barometro).

O que NAO mudou (decisoes ja tomadas, ver NOTA_E3.md):
  - 319 footprints, mesma netlist corrigida da v7.
  - MOSFET NVMFS6H824NT1G em Package_SO:SOIC-8_3.9x4.9mm_P1.27mm (1=G 2=D 3=S).
  - IR2104 mantido como driver.
  - SD dos 12 IR2104 em SD_MCU (pino 28 do MCU).
  - F1 = Fuse_1206_3216Metric no VBAT+.
  - Stitch: malha de 0,05 mm x 36 angulos a partir da borda real do pad, ate
    2 vias por pad, 1 via garantida no 1o laco (STITCH_v8.md secao 2).
  - F.Cu e B.Cu a 0,0700 mm (2 oz) no stackup: o calculo de potencia de
    calc_trilhas_vias_saida.txt (fase do motor = 6,29 mm) so fecha com 2 oz.

Roda: /usr/bin/python3.9 fase3_pcb/gera_pcb_v10.py [pasta_de_saida]
"""
import os
import re
import math
import sys
import time

import pcbnew

T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))
V7 = os.path.join(HERE, "v7", "v7_drone.kicad_pcb")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "v10")
LIB = "/usr/share/kicad/modules/"
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------- constantes
LARG_ALVO = 190.0      # mm -- largura do contorno
ALT_ALVO = 145.0       # mm -- altura do contorno
LIM_STITCH = 1.6       # mm -- gate A4
MARGEM_PAD = 0.20      # mm -- folga via x pad de outra net (STITCH_v8.md)
LIVRE_EDGE = 1.0       # mm -- margem do contorno ate o primeiro pad
GAP = 0.45             # mm -- folga minima entre dois footprints
DRILL, VPAD = 0.3, 0.6
RVIA = 0.5 * VPAD + 0.20
STEP_R, STEP_A = 0.05, 36
INSET_KA = 0.9   # mm -- largura das faixas de keepout de borda (E6/E8)

print("=" * 78)
print("FASE 3 -- gerador da v10 (correcoes da auditoria) (190x145, 6 camadas, zonas de potencia) [GERA]")
print("=" * 78)
print("pcbnew:", pcbnew.GetBuildVersion())

BRD = pcbnew.LoadBoard(V7)
n0_fp = len(list(BRD.GetModules()))
n0_net = BRD.GetNetCount() - 1
print("v7 carregada: footprints=%d  nets=%d" % (n0_fp, n0_net))
assert n0_fp == 319, "v7 nao tem 319 footprints"
assert n0_net == 190, "v7 nao tem 190 nets (202 - 12 RBM fundidas + typo fix)"

NETCODE = {}
for _k, _v in BRD.GetNetsByName().items():
    _k = str(_k)
    if _k:
        NETCODE[_k] = _v.GetNet()
print("mapa de nets: %d nomes" % len(NETCODE))

# =========================================================== 1. seis camadas
BRD.SetCopperLayerCount(6)
CU_LAYERS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
             pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
camadas = [BRD.GetLayerName(l) for l in CU_LAYERS]
print("camadas de cobre: %d  ->  %s" % (len(camadas), ", ".join(camadas)))
assert len(camadas) == 6

# ================================================ 2. D-13: 12 SD -> 1 GPIO
NSD_MCU = "SD_MCU"
NSD = sorted({p.GetNetname() for f in BRD.GetModules() for p in f.Pads()
              if re.match(r"^SDM\d{3}$", p.GetNetname())})
netinfo = pcbnew.NETINFO_ITEM(BRD, NSD_MCU)
BRD.Add(netinfo)
CODE_SD = netinfo.GetNet()
n_sd = n_rsd = 0
for f in list(BRD.GetModules()):
    ref = f.GetReference()
    for p in f.Pads():
        if p.GetNetname() in NSD:
            if re.match(r"^UM\d{3}$", ref):
                p.SetNetCode(CODE_SD); n_sd += 1
            elif re.match(r"^RsdM\d{3}$", ref):
                p.SetNetCode(CODE_SD); n_rsd += 1
ok_mcu = False
for f in list(BRD.GetModules()):
    if f.GetReference() == "U_MCU":
        for p in f.Pads():
            if p.GetPadName() == "28":
                p.SetNetCode(CODE_SD); ok_mcu = True
assert ok_mcu, "U_MCU pad 28 nao encontrado"
print("D-13: net %s <- %d pads SD(IR2104) + %d pads Rsd + U_MCU.28"
      % (NSD_MCU, n_sd, n_rsd))
assert n_sd == 12

# ========================================= 3. MOSFET -> SO-8FL (NVMFS6H824)
MOS_NEW = ("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm")
MOS_PADNET = {"1": "gate", "2": "drain", "3": "source"}
mos_novos = []
for f in list(BRD.GetModules()):
    ref = f.GetReference()
    if not re.match(r"^QM\d{3}[HL]$", ref):
        continue
    nets_pad = {p.GetPadName(): p.GetNetname() for p in f.Pads()}
    pos, rot = f.GetPosition(), f.GetOrientationDegrees()
    tabnet = nets_pad.get("", "")
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
        if nm in MOS_PADNET:
            want = nets_pad.get(nm, "")
            if want and want in NETCODE:
                p.SetNetCode(NETCODE[want])
        else:
            p.SetNetCode(0)
    if tabnet and tabnet in NETCODE:
        tgt = "2" if nets_pad.get("2") else "3"
        for p in m.Pads():
            if p.GetPadName() == tgt:
                p.SetNetCode(NETCODE[tabnet])
    mos_novos.append(ref)
print("MOSFET: %d pegadas TO-252 -> %s (%s)"
      % (len(mos_novos), MOS_NEW[1], ",".join(sorted(mos_novos)[:3]) + "..."))

# =========================================== 4. D-15: fusivel 1206 de 30 A
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

# ==================================== 5. medir footprints e limpar trilhas v7
def mod_box(f):
    bb = f.GetBoundingBox()
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
            pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))


# [FIX auditoria C1/E2] margem da bbox alem do pad, para o silk nao encostar
MARGEM_BBOX = 0.15   # mm


def fp_box_at(f, rot):
    """Bbox ELETRICA (pads) do footprint na rotacao `rot`, ancorado em (0,0).

    [FIX auditoria C1/E2] GetBoundingBox() inclui os textos de silkscreen/fab:
    o value "NVMFS6H824NT1G" media o SOIC-8 como ~13,6 mm de largura (o
    espacamento entre MOSFETs da v9 era 14,08 mm = texto + GAP). Aqui a bbox
    e' a uniao dos pads: cada pad e' coberto por um circulo circunscrito de
    raio max(w,h)/2 (conservador para qualquer rotacao de pad), mais
    MARGEM_BBOX. Devolve (w, h, dx, dy) com dx/dy = offset ancora -> canto
    min da bbox (mesmo contrato da v9).
    """
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.wxPointMM(0, 0))
    l = t = r = b = None
    for p in f.Pads():
        pos = p.GetPosition()
        sz = p.GetSize()
        rr = max(abs(sz.x), abs(sz.y)) // 2 + pcbnew.FromMM(MARGEM_BBOX)
        x0, x1 = pos.x - rr, pos.x + rr
        y0, y1 = pos.y - rr, pos.y + rr
        l = x0 if l is None else min(l, x0)
        r = x1 if r is None else max(r, x1)
        t = y0 if t is None else min(t, y0)
        b = y1 if b is None else max(b, y1)
    if l is None:            # sem pads: fallback (nenhum caso neste board)
        bb = f.GetBoundingBox()
        l, t, r, b = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    l, t, r, b = (v / 1e6 for v in (l, t, r, b))
    return (r - l), (b - t), -l, -t


# [FIX auditoria C1] area por PADS (a GetBoundingBox infla com texto de silk —
# a v9 reportava 16 562,9 mm2 de "bounding boxes" que eram, em boa parte,
# rotulos de silkscreen). A area eletrica e' a base honesta da ocupacao.
area_fp = 0.0
_area_txt = 0.0
for f in list(BRD.GetModules()):
    saved_rot = f.GetOrientation()
    saved_pos = f.GetPosition()
    w, h, _dx, _dy = fp_box_at(f, round(f.GetOrientationDegrees() % 360, 4))
    area_fp += w * h
    f.SetOrientation(saved_rot)
    f.SetPosition(saved_pos)
    x0, y0, x1, y1 = mod_box(f)
    _area_txt += (x1 - x0) * (y1 - y0)
print("soma das areas ELETRICAS (pads): %.1f mm2  "
      "[por comparação, com texto de silk: %.1f mm2]" % (area_fp, _area_txt))

ntrk = 0
for t in list(BRD.GetTracks()):
    BRD.Remove(t); ntrk += 1
for z in list(BRD.Zones()):
    BRD.Remove(z)
print("trilhas/vias da v7 removidas: %d" % ntrk)

MODS = list(BRD.GetModules())
assert len(MODS) == n0_fp
print("footprints antes do empacotamento: %d" % len(MODS))

# =============================================== 6. EMPACOTADOR (medido)
POT = re.compile(r"^(Q|UM|PM|Ca\d|Cb\d|Cv\d|Db\d|F1|Rsd|Rgo|Rgf|Rd\d|Rb\d|"
                 r"Cd\d|Cbe|Cbl|Chf)")
# fp_box_at() e MARGEM_BBOX agora vivem na secao 5 (usados tambem pela
# medicao de area eletrica).


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
        if best is None:
            y += shelf_h + GAP
            x, shelf_h = 0.0, 0.0
            for (w, h, dx, dy, rot) in cands:
                if w <= W and (best is None or h < best[1]):
                    best = (w, h, dx, dy, rot)
            if best is None:
                return None
        w, h, dx, dy, rot = best
        # [FIX auditoria C1/E2] era `x - dx`, o que punha a bbox-esquerda em
        # LIVRE_EDGE + x - 2*dx (um bbox inteiro atras) e jogava 27 footprints
        # para fora do contorno. A ancora fica em shelf + dx => bbox no shelf.
        placed[ref] = (LIVRE_EDGE + x + dx, LIVRE_EDGE + y + dy, rot)
        x += w + GAP
        if h > shelf_h:
            shelf_h = h
    return (y + shelf_h + LIVRE_EDGE), placed


print("-" * 78)
print("empacotador a L=%.0f mm (altura MEDIDA, nao estimada)" % LARG_ALVO)
r = empacota(LARG_ALVO)
assert r is not None, "190 mm nao fecha os 319 footprints"
ALT_MEDIDA, PLACED = r
print("  altura usada pelo empacotador : %.2f mm" % ALT_MEDIDA)
print("  altura do contorno             : %.2f mm (alvo)" % ALT_ALVO)
print("  folga vertical restante        : %.2f mm" % (ALT_ALVO - ALT_MEDIDA))
assert ALT_MEDIDA <= ALT_ALVO, ("empacotamento (%.2f) estourou a altura do "
                                "contorno (%.2f)" % (ALT_MEDIDA, ALT_ALVO))
LARG, ALT = LARG_ALVO, ALT_ALVO
ocup = 100.0 * area_fp / (LARG * ALT)
print("  ocupacao = %.1f / %.1f = %.2f %%" % (area_fp, LARG * ALT, ocup))

for f in MODS:
    x, y, rot = PLACED[f.GetReference()]
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.wxPointMM(x, y))
print("footprints reposicionados: %d / %d" % (len(MODS), len(MODS)))

# ================================================== 7. contorno Edge.Cuts
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

# ------------------------------------------- 8. pads de GND / VBAT_PROT
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

# ====================================== 9. vias de stitch (algoritmo da v8)
# Gate A4: CADA pad de GND/VBAT_PROT precisa de >= 1 via a <= 1,6 mm. Um pad
# SMD em F.Cu NAO alcanca In1..In4/B.Cu sem via -- medido em STITCH_v8.md
# secao 1 (caso B: 1 conexao aberta; caso D, com via, 0).
OCUP = []
for f in BRD.GetModules():
    for p in f.Pads():
        sz = p.GetSize()
        r = 0.5 * max(pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)) + MARGEM_PAD
        OCUP.append((pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), r))

CELULA = 4.0
IDX = {}


def _cel(x, y):
    return (int(math.floor(x / CELULA)), int(math.floor(y / CELULA)))


def indexa(d):
    x, y, r = d
    cx, cy = _cel(x, y)
    n = int(math.ceil(r / CELULA))
    for i in range(cx - n, cx + n + 1):
        for j in range(cy - n, cy + n + 1):
            IDX.setdefault((i, j), []).append(d)


def vizinhos(x, y, r):
    cx, cy = _cel(x, y)
    n = int(math.ceil(r / CELULA))
    out = []
    for i in range(cx - n, cx + n + 1):
        for j in range(cy - n, cy + n + 1):
            out.extend(IDX.get((i, j), ()))
    return out


def livre(x, y, r, occ):
    for (ox, oy, orr) in occ:
        if (x - ox) ** 2 + (y - oy) ** 2 < (r + orr) ** 2:
            return False
    return True


for _d in OCUP:
    indexa(_d)


def cria_via(x, y, netcode):
    v = pcbnew.VIA(BRD)
    v.SetPosition(pcbnew.wxPointMM(x, y))
    v.SetDrill(pcbnew.FromMM(DRILL)); v.SetWidth(pcbnew.FromMM(VPAD))
    v.SetViaType(pcbnew.VIA_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(netcode)
    BRD.Add(v)
    indexa((x, y, RVIA + MARGEM_PAD))


def acha_via(px, py, hx, hy):
    # [FIX auditoria G6] o raio de busca era LIM_STITCH=1,6 mm do CENTRO do
    # pad; para pads grandes (bulk 8x10, EPAD do MCU) a via precisa ficar a
    # extent+RVIA+folga do centro para nao tocar o cobre do pad — raio maior
    # que a busca. Estende o alcance ate cobrir o minimo geometrico.
    raio_max = max(LIM_STITCH, math.hypot(hx, hy) + RVIA + 0.45)
    raio = 0.0
    while raio <= raio_max + 1e-9:
        for k in range(STEP_A):
            a = 2.0 * math.pi * k / STEP_A
            ca, sa = abs(math.cos(a)), abs(math.sin(a))
            rmin = hx * ca + hy * sa + RVIA + 0.05
            if raio + 1e-9 < rmin:
                continue
            vx, vy = px + raio * math.cos(a), py + raio * math.sin(a)
            # [FIX auditoria E6] era 0,8 mm — MENOR que a faixa de keepout
            # (0,9 mm) + sua clearance (0,3 mm); a v9 criou 8 vias DENTRO do
            # keepout esquerdo. O centro da via precisa ficar a
            # keepout + clearance + raio da via de cada borda.
            LIM_V = INSET_KA + 0.3 + RVIA
            if not (LIM_V < vx < LARG - LIM_V and LIM_V < vy < ALT - LIM_V):
                continue
            occ = [o for o in vizinhos(vx, vy, RVIA)
                   if abs(o[0] - px) > 1e-6 or abs(o[1] - py) > 1e-6]
            if not livre(vx, vy, RVIA, occ):
                continue
            return (vx, vy)
        raio += STEP_R
    return None


vias_ok, falhas, n_mult = 0, [], 0
for (ref, pad, netname, px, py, sx, sy) in PADS_STITCH:
    achou = acha_via(px, py, 0.5 * sx, 0.5 * sy)
    if achou is None:
        falhas.append("%s.%s(%s)" % (ref, pad, netname))
        continue
    cria_via(achou[0], achou[1], NETCODE[netname])
    vias_ok += 1
for (ref, pad, netname, px, py, sx, sy) in PADS_STITCH:
    achou = acha_via(px, py, 0.5 * sx, 0.5 * sy)
    if achou is None:
        continue
    cria_via(achou[0], achou[1], NETCODE[netname])
    vias_ok += 1
    n_mult += 1
print("vias de stitch criadas: %d | pads sem via: %d | 2a via em: %d"
      % (vias_ok, len(falhas), n_mult))
if falhas:
    print("  pads sem via: %s" % ", ".join(falhas))

# ================================== 10. keepouts (rule areas) pot/sinal
def keepout(x0, y0, x1, y1):
    z = pcbnew.ZONE_CONTAINER(BRD)
    ls = pcbnew.LSET()
    for l in CU_LAYERS:
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


# [FIX auditoria E8] faltava a faixa da borda SUPERIOR — a v9 só tinha
# esquerda/direita/inferior. Agora as 4 bordas têm keepout de 0,9 mm.
KA = [keepout(0.0, 0.0, INSET_KA, ALT),              # borda esquerda (potencia)
      keepout(LARG - INSET_KA, 0.0, LARG, ALT),      # borda direita (sinal)
      keepout(0.0, 0.0, LARG, INSET_KA),             # borda SUPERIOR (faltava)
      keepout(0.0, ALT - INSET_KA, LARG, ALT)]        # faixa de separacao (inf)
NOMES_KA = ["rule_area_potencia", "rule_area_sinal",
            "rule_area_topo", "rule_area_separacao"]
print("keepouts (rule_area) criados: %d" % len(KA))

# ================================================ 11. ZONAS DE POTENCIA
# Prioridade: quanto MAIOR, mais o cobre vence a sobreposicao. Por isso as nets
# pequenas (3V3_A, 3V3, 5V, 12V) tem prioridade MAIOR que o GND espalhado --
# se fosse o contrario, o pour de GND comeria o plano de 3V3 e cada pad ficaria
# numa ilha solta, sem ligacao entre pads.
ZONAS = [
    # (net,          layer,          prioridade, modo)
    ("GND",         pcbnew.F_Cu,      50,  "plano"),
    ("GND",         pcbnew.B_Cu,      50,  "plano"),
    # [FIX auditoria C6] VBAT e VBAT_F nao tinham zona NENHUMA — o caminho de
    # 30 A (J1 -> F1 -> Q1) nao tinha condutor previsto em nenhuma camada.
    ("VBAT",        pcbnew.F_Cu,      60,  "local"),
    ("VBAT",        pcbnew.B_Cu,      60,  "local"),
    ("VBAT_F",      pcbnew.F_Cu,      60,  "local"),
    ("VBAT_F",      pcbnew.B_Cu,      60,  "local"),
    ("VBAT_PROT",   pcbnew.F_Cu,      70,  "local"),
    ("VBAT_PROT",   pcbnew.B_Cu,      70,  "local"),
    ("12V",         pcbnew.F_Cu,      75,  "local"),
    ("12V",         pcbnew.B_Cu,      75,  "local"),
    ("5V",          pcbnew.F_Cu,      80,  "local"),
    ("5V",          pcbnew.B_Cu,      80,  "local"),
    ("3V3",         pcbnew.F_Cu,      85,  "local"),
    ("3V3",         pcbnew.B_Cu,      85,  "local"),
    ("3V3_A",       pcbnew.F_Cu,      90,  "local"),
    ("3V3_A",       pcbnew.B_Cu,      90,  "local"),
    ("GND",         pcbnew.In1_Cu,   100,  "plano"),
    ("VBAT_PROT",   pcbnew.In4_Cu,   100,  "plano"),
]
# [FIX auditoria C6] as 24 nets de fase (PHM*/SNM*) tambem nao tinham cobre:
# 15 A RMS por fase sem condutor planejado. Zona local F.Cu por fase (o no' de
# fase e compacto: MOSFET alto/baixo + conector + VS do driver + bootstrap).
# Prioridade 60: acima do plano de GND (50), abaixo das rails pequenas.
for _nm in sorted(NETCODE):
    if re.match(r"^(PHM|SNM)\d{3}$", str(_nm)):
        ZONAS.append((str(_nm), pcbnew.F_Cu, 60, "local"))
MARGEM_ZONA = 3.0     # mm, folga da zona alem do pad mais afastado da net
INSET = 0.9           # mm, mesma largura da faixa de keepout


CEL_Z = 3.0     # mm, celula do agrupamento de pads por zona local
DIL_Z = 1       # celulas de dilatacao ao redor de cada pad


def aglomerados(nome, cel=CEL_Z, dil=DIL_Z):
    """Agrupa os pads de `nome` em retangulos conectados (grade de `cel` mm).

    MEDIDO na v9, primeira tentativa: a zona local era o bounding box inteiro
    da net + 3 mm. Como 3V3 (181 x 101 mm), 5V (178 x 54 mm) e 3V3_A
    (137 x 49 mm) se sobrepoem quase por inteiro, a zona de 5V (prio 80) era
    COMIDA pela de 3V3 (prio 85) e nao gerava uma unica ilha. Uma zona retan-
    gular por aglomerado de pads nao se sobrepoe a si mesma: cobre so onde a
    net realmente tem cobre, e o que sobra da area vira GND.
    """
    celulas = set()
    for f in BRD.GetModules():
        for p in f.Pads():
            if p.GetNetname() != nome:
                continue
            sz = p.GetSize()
            x = pcbnew.ToMM(p.GetPosition().x)
            y = pcbnew.ToMM(p.GetPosition().y)
            hw = pcbnew.ToMM(sz.x) / 2.0 + 0.8
            hh = pcbnew.ToMM(sz.y) / 2.0 + 0.8
            for i in range(int((x - hw) / cel), int((x + hw) / cel) + 1):
                for j in range(int((y - hh) / cel), int((y + hh) / cel) + 1):
                    celulas.add((i, j))
    for _ in range(dil):
        novo_c = set()
        for (i, j) in celulas:
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)):
                novo_c.add((i + d[0], j + d[1]))
        celulas |= novo_c
    vistos, out = set(), []
    for c in sorted(celulas):
        if c in vistos:
            continue
        comp, pilha = set(), [c]
        vistos.add(c)
        while pilha:
            x, y = pilha.pop()
            comp.add((x, y))
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = (x + d[0], y + d[1])
                if v in celulas and v not in vistos:
                    vistos.add(v); pilha.append(v)
        xs = [q[0] for q in comp]; ys = [q[1] for q in comp]
        x0 = max(INSET, min(xs) * cel)
        y0 = max(INSET, min(ys) * cel)
        x1 = min(LARG - INSET, (max(xs) + 1) * cel)
        y1 = min(ALT - INSET, (max(ys) + 1) * cel)
        if x1 - x0 > 0.5 and y1 - y0 > 0.5:
            out.append((x0, y0, x1, y1))
    return out


def nova_zona(net, layer, prio, x0, y0, x1, y1):
    z = pcbnew.ZONE_CONTAINER(BRD)
    z.SetLayer(layer)
    z.SetNetCode(NETCODE[net])
    z.SetPriority(prio)
    z.SetIsFilled(False)
    # preenchimento solide: nestas 6 redes a conexao e por cobre, nao por
    # ancora termica -- o plano e o que substitui a trilha.
    z.SetPadConnection(pcbnew.PAD_ZONE_CONN_FULL)
    z.SetZoneClearance(pcbnew.FromMM(0.25))
    z.SetMinThickness(pcbnew.FromMM(0.20))
    z.SetThermalReliefGap(pcbnew.FromMM(0.3))
    o = z.Outline(); o.NewOutline()
    for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    BRD.Add(z)
    return z


infos_zona = []
for (net, layer, prio, modo) in ZONAS:
    if modo == "plano":
        rects = [(INSET, INSET, LARG - INSET, ALT - INSET)]
    else:
        rects = aglomerados(net)
    for (x0, y0, x1, y1) in rects:
        z = nova_zona(net, layer, prio, x0, y0, x1, y1)
        infos_zona.append((net, BRD.GetLayerName(layer), prio, modo,
                           x1 - x0, y1 - y0))
print("  zonas criadas: %d" % len(infos_zona))
agg = {}
for (net, lay, prio, modo, aw, ah) in infos_zona:
    a_ = agg.setdefault((net, lay), [0, 0.0])
    a_[0] += 1
    a_[1] += aw * ah
for (net, lay), (n, ar) in sorted(agg.items()):
    print("  %-10s %-6s prio %3d  %2d zona(s), %.0f mm2 de contorno"
          % (net, lay, [p for (nn, ll, p, _m) in ZONAS
                        if nn == net and BRD.GetLayerName(ll) == lay][0],
             n, ar))

# ---------------------------------------------------- medicao ANTES do fill
BRD.BuildConnectivity()
cn_antes = BRD.GetConnectivity().GetUnconnectedCount()
# NOTA: GetRatsnestForNet() devolve um SwigPyObject sem len() nem iteracao no
# pcbnew 5.1.9 (medido), entao a contagem POR NET e feita de forma independente
# em fase3_pcb/verifica_fase3_v9.py (raster das filled_polygon + flood fill).
# Aqui fica so o total, que e a saida do proprio motor de conectividade.
print("ratsnest ANTES do fill das zonas: %d conexoes abertas" % cn_antes)

# ------------------------------------------------------------- preencher
tpl = time.time()
filler = pcbnew.ZONE_FILLER(BRD)
filler.Fill(BRD.Zones())
BRD.BuildConnectivity()
cn_depois = BRD.GetConnectivity().GetUnconnectedCount()
print("zonas preenchidas em %.1f s; ratsnest: %d -> %d conexoes abertas (-%d)"
      % (time.time() - tpl, cn_antes, cn_depois, cn_antes - cn_depois))
copo = n_fill = n_ka = 0
for z in BRD.Zones():
    if z.GetIsKeepout():
        n_ka += 1
        continue
    n_fill += 1
    if z.IsFilled():
        copo += 1
print("zonas: %d de cobre (delas, %d preenchidas) + %d keepout"
      % (n_fill, copo, n_ka))

# ================================================ 12. salvar + stackup 2 oz
PATH = OUT + "/v10_drone.kicad_pcb"
BRD.Save(PATH)
print("salvou", PATH)

STK = os.path.join(HERE, "v8", "v8_drone_stackup.txt")
txt = open(STK, encoding="utf-8").read()
i = txt.index("\n(stackup") + 1   # NAO usar txt.index("(stackup"): a
                                # 1a ocorrencia esta DENTRO de um comentario
                                #  do proprio sidecar (medido: bloco vazio).
niv, k = 0, i
for k in range(i, len(txt)):
    if txt[k] == "(":
        niv += 1
    elif txt[k] == ")":
        niv -= 1
        if niv == 0:
            break
bloco = txt[i:k + 1]
import re as _re

# ---- TAREFA 0: F.Cu e B.Cu a 2 oz (0,0700 mm) -------------------------------
# calc_trilhas_vias_saida.txt (fase do motor 15 A = 6,29 mm) foi calculado para
# 2 oz. Com 1 oz a largura necessaria seria 1,41x maior. Como o sidecar da v8 em
# disco esta com 0,0350 mm, a MESMA correcao que gera_pcb_v8.py aplica e' feita
# aqui, de forma idempotente. O dieletrico 5 cai 0,2894 -> 0,2194 mm para a soma
# fechar em 1,6000 mm, casando com o (general (thickness 1.6)) do board.
ESP_FB = 0.0700
for _l in ("F.Cu", "B.Cu"):
    bloco = _re.sub(r'\(layer %s \(type "copper"\) \(thickness [0-9.]+\)\)'
                    % _re.escape(_l),
                    '(layer %s (type "copper") (thickness %.4f))' % (_l, ESP_FB),
                    bloco)
bloco = _re.sub(r'\(layer "dielectric 5" \(type "core"\) \(thickness [0-9.]+\)',
                '(layer "dielectric 5" (type "core") (thickness 0.2194)', bloco)
bloco = _re.sub(r"\(copper_thickness [0-9.]+\)", "(copper_thickness 0.0700)",
                bloco)
bloco = _re.sub(r"\(dielectric_thickness [0-9.]+\)",
                "(dielectric_thickness 1.3370)", bloco)
_vals = [float(v) for v in _re.findall(r"\(layer\b.*?\(thickness ([0-9.]+)\)", bloco)]
n2oz = sum(1 for l in ("F.Cu", "B.Cu")
           if '(layer %s (type "copper") (thickness 0.0700))' % l in bloco)
print("  stackup: F.Cu/B.Cu a %.4f mm (2 oz) em %d camadas; soma = %.4f mm "
      "em %d entradas" % (ESP_FB, n2oz, sum(_vals), len(_vals)))
assert n2oz == 2, "stackup sem 2 oz em F.Cu/B.Cu"
assert len(_vals) == 11, "esperava 11 camadas no stackup, achei %d" % len(_vals)
assert abs(sum(_vals) - 1.6000) < 5e-4, "soma do stackup != 1,6000 mm"

# ---- grade/snap dentro de (setup ...) --------------------------------------
# KiCad 5.1 aceita (aux_axis_origin ..) e (grid ..) dentro de (setup ..).
# Nenhum token de stackup e aceito -- ver v8_drone_stackup.txt.
src = open(PATH, encoding="utf-8").read()
GRADE = ("  (setup\n"
         "    (last_trace_width 0.2500)\n"
         "    (trace_clearance 0.1500)\n"
         "    (zone_clearance 0.2500)\n"
         "    (zone_45_only no)\n"
         "    (trace_min 0.2000)\n"
         "    (via_size 0.6000)\n"
         "    (via_drill 0.3000)\n"
         "    (via_min_size 0.4000)\n"
         "    (via_min_drill 0.2000)\n"
         "    (uvia_size 0.3000)\n"
         "    (uvia_drill 0.1000)\n"
         "    (uvias_allowed no)\n"
         "    (uvia_min_size 0.2000)\n"
         "    (uvia_min_drill 0.1000)\n"
         "    (edge_width 0.1000)\n"
         "    (segment_width 0.2000)\n"
         "    (pcb_text_width 0.3000)\n"
         "    (pcb_text_size 1.5000 1.5000)\n"
         "    (mod_edge_width 0.1500)\n"
         "    (mod_text_size 1.0000 1.0000)\n"
         "    (mod_text_width 0.1500)\n"
         "    (pad_size 1.5000 1.5000)\n"
         "    (pad_drill 0.8000)\n"
         "    (aux_axis_origin 0.0000 0.0000)\n"
         "    (grid_origin 0.0000 0.0000)\n"
         "    (visible_elements 0x0001F)\n"
         "  )\n")
assert "(setup" in src, "board sem bloco (setup ...)"
if "(grid " not in src:
    i0 = src.index("(setup") + len("(setup")
    # substitui o (setup ...) existente, se houver
    j, niv = i0, 1     # o '(' de (setup ja conta: sem isto o contador
                     # fecha no PRIMEIRO token e deixa o resto do bloco
                     # antigo no arquivo (medido: OSError Unknown token
                     # "trace_clearance").
    for j in range(i0, len(src)):
        if src[j] == "(":
            niv += 1
        elif src[j] == ")":
            niv -= 1
            if niv == 0:
                break
    src = src[:i0 - len("(setup")] + GRADE + src[j + 1:]
    open(PATH, "w", encoding="utf-8").write(src)
    print("grade/snap gravado em (setup ...)")

# ---- titulos das rule areas ------------------------------------------------
# (title ..) E' token valido do formato 5.1; (name ..) NAO e (medido na v8:
# OSError "Expecting net, layer/layers, tstamp, ..."). Entao as 3 rule areas
# sao identificadas por (title "rule_area_<nome>").
# ---- identificacao das rule areas ------------------------------------------
# MEDIDO NESTA MAQUINA, agora com a v9: o parser de zone do KiCad 5.1.9 NAO
# aceita (title ..) nem (name ..). Injetar qualquer um dos dois da
#   OSError Expecting "net, layer/layers, tstamp, hatch, priority,
#   connect_pads, min_thickness, fill, polygon, filled_polygon, or
#   fill_segments"
# (o v8 documente a tentativa com (title ..); o medido aqui e que tambem falha).
# As 4 rule areas sao REAIS: cada uma vira um (zone ... (keepout ...)) no
# arquivo. A identificacao "rule_area_*" vai para o sidecar
# v10_rule_areas.txt, NAO para o board -- inventar token seria board falso.
KA_TXT = ["# RULE AREAS DA v10 (keepouts) -- identificacao em sidecar",
          "#",
          "# KiCad 5.1.9 nao aceita (name ..) nem (title ..) em (zone ..):",
          "#   OSError Expecting \"net, layer/layers, tstamp, hatch, priority,",
          "#   connect_pads, min_thickness, fill, polygon, filled_polygon, or",
          "#   fill_segments\"   (medido nesta maquina, 2026-09-28).",
          "# As 4 areas abaixo sao reais: 4 tokens (keepout no .kicad_pcb,",
          "# cobrindo F.Cu, In1.Cu, In2.Cu, In3.Cu, In4.Cu e B.Cu.",""]
for _n, (x0, y0, x1, y1) in zip(NOMES_KA, [(0, 0, INSET_KA, ALT),
                                            (LARG - INSET_KA, 0, LARG, ALT),
                                            (0, 0, LARG, INSET_KA),
                                            (0, ALT - INSET_KA, LARG, ALT)]):
    KA_TXT.append("%-22s x0=%6.2f y0=%6.2f x1=%6.2f y1=%6.2f mm  "
                  "(%.1f x %.1f mm)  tracks/vias/pour = not_allowed"
                  % (_n, x0, y0, x1, y1, x1 - x0, y1 - y0))
open(OUT + "/v10_rule_areas.txt", "w", encoding="utf-8").write(
    "\n".join(KA_TXT) + "\n")
print("  rule areas: 4 reais (bordas esq/dir/topo/inf), identificadas em "
      "v10_rule_areas.txt")

open(OUT + "/v10_drone_stackup.txt", "w", encoding="utf-8").write(
    "# STACKUP DA v10 -- 6 camadas, F.Cu e B.Cu a 2 oz\n"
    "#\n"
    "# KiCad 5.1.9 NAO possui o token (stackup ...) no formato do .kicad_pcb:\n"
    "# injetar torna o board ILEGIVEL (OSError Unexpected \"stackup\").\n"
    "# Este sidecar e' o mesmo bloco de fase3_pcb/v8/v8_drone_stackup.txt --\n"
    "# a v10 muda a geometria da placa, nao o stackup.\n"
    "# Soma conferida: %.4f mm em %d entradas.\n"
    "#\n" % (sum(_vals), len(_vals)) + bloco + "\n")

# ---------------------------------------------------- prova de carregamento
b2 = pcbnew.LoadBoard(PATH)
print("LoadBoard(v10) OK: footprints=%d  zonas=%d  vias=%d  trilhas=%d"
      % (len(list(b2.GetModules())), len(b2.Zones()),
         sum(1 for t in b2.GetTracks() if t.Type() == pcbnew.PCB_VIA_T),
         sum(1 for t in b2.GetTracks() if t.Type() != pcbnew.PCB_VIA_T)))
raw_rule = src.count("rule_area")
print("  (keepout=%d  rule_area=%d  grid=%d)"
      % (src.count("(keepout"), raw_rule, src.count("(grid ")))
print("tempo total: %.1f s" % (time.time() - T0))
print("ok")
