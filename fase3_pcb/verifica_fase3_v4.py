#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""Verificacao do PCB v3: contagens, nets roteadas x nao roteadas, planos."""
import pcbnew, io, collections, os

OUT = "/opt/jupyter/work/drone/fase3_pcb/v4"
b = pcbnew.LoadBoard(OUT + "/v4_drone.kicad_pcb")
o = io.StringIO()
def P(*a):
    s = " ".join(str(x) for x in a); print(s); o.write(s + "\n")

mods = list(b.GetModules())
pads = [p for m in mods for p in m.Pads()]
tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.VIA)]
vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.VIA)]
zones = list(b.Zones())

P("=" * 74)
P("VERIFICACAO DO PCB v3 (KiCad 5.1)  [CALC/EXECUTADO]")
P("=" * 74)
P("footprints        :", len(mods))
P("pads              :", len(pads))
P("trilhas (tracks)  :", len(tracks))
P("vias              :", len(vias))
P("zonas (planos)    :", len(zones), "->", [b.GetLayerName(z.GetLayer()) for z in zones])

bb = b.GetBoardEdgesBoundingBox()
P("dimensoes da placa: %.1f x %.1f mm" % (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())))
P("camadas de cobre  :", b.GetCopperLayerCount())

# --- nets: quantos pads e quanto foi roteado ---
net_pads = collections.Counter()
for p in pads:
    nc = p.GetNetCode()
    if nc > 0:
        net_pads[p.GetNetname()] += 1
net_routed = collections.Counter()
for t in tracks:
    net_routed[t.GetNetname()] += 1
for v in vias:
    net_routed[v.GetNetname()] += 1
for z in zones:
    net_routed[z.GetNetname()] += 1

todas = set(net_pads) | set(net_routed)
com_pads = {n for n in todas if net_pads[n] > 0}
nao_roteadas = sorted(n for n in com_pads if net_routed[n] == 0)
roteadas = sorted(n for n in com_pads if net_routed[n] > 0)

P("")
P("nets com pad      :", len(com_pads))
P("nets roteadas     :", len(roteadas))
P("nets NAO roteadas :", len(nao_roteadas))

P("")
P("-- nets roteadas (amostra das potentes) --")
for n in sorted(roteadas):
    if net_pads[n] >= 2 and (n.startswith(("PH", "SN", "GND", "VBAT", "GH", "GL"))):
        P("   %-12s pads=%2d  trilhas/vias/zonas=%d" % (n, net_pads[n], net_routed[n]))

P("")
P("-- grupos de nets NAO roteadas (por prefixo) --")
g = collections.Counter()
for n in nao_roteadas:
    g[n.split("_")[0].split("p")[0][:6]] += 1
for k, v in g.most_common(12):
    P("   %-10s %d nets" % (k, v))

# --- checagem de CURTO: pad x pad e trilha x pad de nets diferentes ---
P("")
P("-- checagem de curto (pads de nets diferentes que se tocam) --")
pinfo = []
for m in mods:
    for p in m.Pads():
        r = p.GetBoundingBox()
        pinfo.append((m.GetReference(), p.GetPadName(), p.GetNetname(),
                      pcbnew.ToMM(r.GetX()), pcbnew.ToMM(r.GetY()),
                      pcbnew.ToMM(r.GetWidth()), pcbnew.ToMM(r.GetHeight())))
n_pad = 0; ex_pad = []
for i in range(len(pinfo)):
    r1, p1, n1, x1, y1, w1, h1 = pinfo[i]
    for j in range(i + 1, len(pinfo)):
        r2, p2, n2, x2, y2, w2, h2 = pinfo[j]
        if r1 == r2 and p1 == p2:
            continue
        if n1 and n2 and n1 == n2:
            continue          # mesma net: tocar e' esperado
        if not n1 or not n2:
            continue          # sem net: nao avalia
        if x1 < x2 + w2 and x2 < x1 + w1 and y1 < y2 + h2 and y2 < y1 + h1:
            n_pad += 1
            if len(ex_pad) < 8:
                ex_pad.append("%s.%s(%s) x %s.%s(%s)" % (r1, p1, n1, r2, p2, n2))
P("   pads de nets diferentes com bbox sobreposto:", n_pad)
for e in ex_pad:
    P("     ex:", e)

# --- checagem de curto: trilha atravessando pad de net diferente ---
P("")
P("-- checagem de curto (trilha x pad de net diferente) --")
n_tp = 0; ex_tp = []
for t in tracks:
    s = t.GetStart(); e = t.GetEnd()
    x1, y1 = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
    x2, y2 = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
    w = pcbnew.ToMM(t.GetWidth()) / 2.0
    tn = t.GetNetname()
    for (r, pn, nn, px, py, pw, ph) in pinfo:
        if not nn or nn == tn:
            continue
        cx, cy = px + pw / 2.0, py + ph / 2.0
        vx, vy = x2 - x1, y2 - y1
        L2 = vx * vx + vy * vy
        if L2 == 0:
            continue
        tt = max(0.0, min(1.0, ((cx - x1) * vx + (cy - y1) * vy) / L2))
        dx, dy = cx - (x1 + tt * vx), cy - (y1 + tt * vy)
        if (dx * dx + dy * dy) ** 0.5 < (w + max(pw, ph) / 2.0) * 0.75:
            n_tp += 1
            if len(ex_tp) < 8:
                ex_tp.append("trilha %s x pad %s.%s(%s)" % (tn, r, pn, nn))
P("   pares trilha x pad (net diferente) proximos:", n_tp)
for e in ex_tp:
    P("     ex:", e)

txt = o.getvalue()
open(OUT + "/verificacao_v4.txt", "w").write(txt)
print("\n[salvo]", OUT + "/verificacao_v4.txt")
