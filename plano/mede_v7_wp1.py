#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
WP1 -- auditoria MEDIDA da v7 (roteamento da Fase 3).

Le  fase3_pcb/v7/v7_drone.kicad_pcb  com pcbnew 5.1.9 e imprime, medidos:
  - contagens globais (footprints, pads, trilhas, vias, zones);
  - camada de cada trilha;
  - nets declaradas / com pad / com pad e ZERO trilha (por camada e global);
  - agrupamento das nets sem cobre por prefixo;
  - geometria: nets de plano, uso de In1_Cu e In2_Cu, larguras de trilha;
  - medidas de board (dimensoes, bbox, espessura, camadas de cobre).

Nao escreve nada no projeto: apenas imprime em stdout.
"""
import os
import sys
import collections
import pcbnew

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, "fase3_pcb", "v7", "v7_drone.kicad_pcb")

b = pcbnew.LoadBoard(SRC)

print("arquivo medido      :", SRC)
print("pcbnew              :", pcbnew.GetBuildVersion())
print("=" * 78)

# ---------------------------------------------------------------- contagens
mods = list(b.GetModules())
pads = [p for m in mods for p in m.Pads()]
tracks_all = list(b.GetTracks())
tracks = [t for t in tracks_all if not isinstance(t, pcbnew.VIA)]
vias = [t for t in tracks_all if isinstance(t, pcbnew.VIA)]
zones = list(b.Zones())

print("footprints          :", len(mods))
print("pads                :", len(pads))
print("trilhas (tracks)    :", len(tracks))
print("vias                :", len(vias))
print("zonas (planos)      :", len(zones),
      "->", [b.GetLayerName(z.GetLayer()) for z in zones])
print("nets declaradas     :", b.GetNetCount() - 1, "(GetNetCount()-1; 0 = sem net)")

# ---------------------------------------------------------------- dimensoes
bb = b.GetBoardEdgesBoundingBox()
print("dimensoes (bbox)   : %.2f x %.2f mm"
      % (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())))
print("origem do bbox      : X=%.2f..%.2f  Y=%.2f..%.2f mm"
      % (pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetX() + bb.GetWidth()),
         pcbnew.ToMM(bb.GetY()), pcbnew.ToMM(bb.GetY() + bb.GetHeight())))
print("area do bbox        : %.1f cm2"
      % (pcbnew.ToMM(bb.GetWidth()) * pcbnew.ToMM(bb.GetHeight()) / 100.0))
print("camadas de cobre    :", b.GetCopperLayerCount())
print("espessura do PCB    : %.2f mm" % pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()))

# ---------------------------------------------------------------- trilhas por camada
per_layer = collections.Counter()
for t in tracks:
    per_layer[b.GetLayerName(t.GetLayer())] += 1
print("trilhas por camada  :", dict(per_layer))
vias_layer = collections.Counter()
for v in vias:
    pair = sorted([b.GetLayerName(v.TopLayer()), b.GetLayerName(v.BottomLayer())])
    vias_layer["/".join(pair)] += 1
print("vias por par de cam.:", dict(vias_layer))

# ---------------------------------------------------------------- larguras
w = collections.Counter()
for t in tracks:
    w[round(pcbnew.ToMM(t.GetWidth()), 3)] += 1
print("larguras de trilha  :", dict(sorted(w.items())))
vw = collections.Counter(round(pcbnew.ToMM(v.GetWidth()), 3) for v in vias)
vd = collections.Counter(round(pcbnew.ToMM(v.GetDrill()), 3) for v in vias)
print("larguras de via     :", dict(sorted(vw.items())))
print("drills de via       :", dict(sorted(vd.items())))

# ---------------------------------------------------------------- nets
net_pads = collections.Counter()
for p in pads:
    if p.GetNetCode() > 0:
        net_pads[p.GetNetname()] += 1
net_trk = collections.Counter()
for t in tracks:
    if t.GetNetCode() > 0:
        net_trk[t.GetNetname()] += 1
net_via = collections.Counter()
for v in vias:
    if v.GetNetCode() > 0:
        net_via[v.GetNetname()] += 1
net_zone = collections.Counter()
for z in zones:
    net_zone[z.GetNetname()] += 1
net_fp = collections.Counter()   # KiCad 5.1: MODULE nao tem GetNet() -- pads sao a fonte

nets_declaradas = set()
for code in range(b.GetNetCount()):
    ni = b.FindNet(code)
    if ni is not None and ni.GetNetname():
        nets_declaradas.add(ni.GetNetname())

com_pad = {n for n in net_pads if net_pads[n] > 0}
com_pad_e_trilha = {n for n in com_pad if net_trk[n] > 0}
zero_trilha = sorted(n for n in com_pad if net_trk[n] == 0)

print("-" * 78)
print("nets declaradas (no arquivo)   :", len(nets_declaradas))
print("nets com >=1 pad              :", len(com_pad))
print("nets com pad e >=1 trilha      :", len(com_pad_e_trilha))
print("nets com pad e ZERO trilha     :", len(zero_trilha))
print("nets com pad e zero trilha E sem via:")
z2 = sorted(n for n in zero_trilha if net_via[n] == 0)
print("   ->", len(z2))

# nets com pad, com trilha, mas so em uma das faces (nao tem cobre nas duas)
so_uma_face = []
for n in sorted(com_pad_e_trilha):
    ls = {b.GetLayerName(t.GetLayer()) for t in tracks if t.GetNetname() == n}
    if ls and not ({"F.Cu", "B.Cu"} & ls):
        so_uma_face.append((n, sorted(ls)))
print("nets roteadas so em 1 face     :", len(so_uma_face))

print("-" * 78)
print("prefixo -> nets com pad e ZERO trilha (top 25)")
g = collections.Counter()
for n in zero_trilha:
    g[n.split("_")[0]] += 1
for k, v in g.most_common(25):
    print("   %-10s %3d nets" % (k, v))
print("   TOTAL (soma dos grupos)     :", sum(g.values()))

print("-" * 78)
print("as 20 primeiras nets com pad e ZERO trilha:")
for n in zero_trilha[:20]:
    print("   %-14s pads=%d vias=%d zonas=%d" % (n, net_pads[n], net_via[n], net_zone[n]))

print("-" * 78)
print("nets de PLANO (GND / VBAT_PROT) e cobertura de plano por camada:")
for z in zones:
    nm = z.GetNetname()
    lay = b.GetLayerName(z.GetLayer())
    fp_ = z.GetFilledPolysList()   # KiCad 5.1: sem argumento
    nv_ = fp_.VertexCount() if fp_ is not None else 0
    print("   zona net=%-10s camada=%-8s vertices_preenchidos=%-6d pads_da_net=%-4d vias_da_net=%d"
          % (nm, lay, nv_, net_pads.get(nm, 0), net_via.get(nm, 0)))
print("   -> os 3 planos: In1.Cu=GND, B.Cu=GND, In2.Cu=VBAT_PROT; "
      "F_Cu NAO tem plano (todas as 605 camadas de cobre estao em F/B/In1/In2)")
print("   -> trilhas em In1_Cu:", per_layer.get("In1.Cu", 0),
      "| trilhas em In2_Cu:", per_layer.get("In2.Cu", 0))

print("-" * 78)
print("pads por tipo (para saber quantos SMD em F_Cu precisam de via p/ o plano):")
att = collections.Counter()
for p in pads:
    att[str(p.GetAttribute())] += 1
print("   atributos:", dict(att))
smd_f = sum(1 for p in pads
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.F_Cu))
smd_b = sum(1 for p in pads
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.B_Cu))
smd_any = sum(1 for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD)
th = sum(1 for p in pads if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD)
print("   SMD total=%d  (SMD so em F_Cu=%d, so em B_Cu=%d, em ambas=%d)  TH/fixo=%d"
      % (smd_any, smd_f, smd_b, smd_any - smd_f - smd_b, th))

print("-" * 78)
print("pads de GND e VBAT_PROT SEM via a menos de 1,6 mm (== fica_no_plano nao alcanca):")
import math
for plano in ("GND", "VBAT_PROT"):
    alvo = [p for p in pads if p.GetNetname() == plano and p.GetNetCode() > 0]
    vs = [(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y))
          for v in vias if v.GetNetname() == plano]
    sem = []
    for p in alvo:
        r = p.GetBoundingBox()
        cx = pcbnew.ToMM(r.GetX()) + pcbnew.ToMM(r.GetWidth()) / 2.0
        cy = pcbnew.ToMM(r.GetY()) + pcbnew.ToMM(r.GetHeight()) / 2.0
        perto = any(math.hypot(x - cx, y - cy) < 1.6 for (x, y) in vs)
        if not perto:
            sem.append("%s.%s" % (p.GetParent().GetReference(), p.GetPadName()))
    print("   %-11s pads=%d  vias=%d  pads_sem_via_perto=%d"
          % (plano, len(alvo), len(vs), len(sem)))
    print("      ex:", sem[:12])

print("-" * 78)
print("GND/VBAT_PROT possuem trilha de sinal? (o roteiro de rota_v7.py os ignora)")
for n in ("GND", "VBAT_PROT"):
    print("   %-11s trilhas=%d vias=%d" % (n, net_trk.get(n, 0), net_via.get(n, 0)))
print("=" * 78)
