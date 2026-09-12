#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""Smoke test KiCad 5.1: board 4 camadas, footprint, zona, via, trilha, gerber, excellon."""
import pcbnew, os
B = pcbnew.BOARD()
B.SetCopperLayerCount(4)
pts = [(0,0),(20,0),(20,20),(0,20)]

seg = pcbnew.SHAPE_POLY_SET(); seg.NewOutline()
for x,y in pts: seg.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
outline = pcbnew.DRAWSEGMENT(B)
outline.SetShape(pcbnew.S_POLYGON); outline.SetPolyShape(seg)
outline.SetLayer(pcbnew.Edge_Cuts); B.Add(outline)

m = pcbnew.FootprintLoad("/usr/share/kicad/modules/Resistor_SMD.pretty","R_0603_1608Metric")
m.SetPosition(pcbnew.wxPointMM(10,10)); B.Add(m)
pads = list(m.Pads())
print("pads:", len(pads), [p.GetPadName() for p in pads])

net = pcbnew.NETINFO_ITEM(B, "VCC"); B.Add(net)

t = pcbnew.TRACK(B); t.SetStart(pcbnew.wxPointMM(9,10)); t.SetEnd(pcbnew.wxPointMM(11,10))
t.SetWidth(pcbnew.FromMM(0.5)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(net.GetNet()); B.Add(t)

v = pcbnew.VIA(B); v.SetPosition(pcbnew.wxPointMM(5,5))
v.SetDrill(pcbnew.FromMM(0.3)); v.SetWidth(pcbnew.FromMM(0.6))
v.SetViaType(pcbnew.VIA_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(net.GetNet()); B.Add(v)

z = pcbnew.ZONE_CONTAINER(B); z.SetLayer(pcbnew.In1_Cu)
z.SetNetCode(net.GetNet()); o = z.Outline(); o.NewOutline()
for x,y in pts: o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
B.Add(z)
filler = pcbnew.ZONE_FILLER(B); filler.Fill(B.Zones())
print("zona preenchida:", z.IsFilled())

out = "/tmp/smoke"; os.makedirs(out, exist_ok=True)
B.Save(out + "/smoke.kicad_pcb"); print("salvou kicad_pcb")

pc = pcbnew.PLOT_CONTROLLER(B); po = pc.GetPlotOptions()
po.SetOutputDirectory(out); po.SetPlotFrameRef(False); po.SetAutoScale(False)
po.SetScale(1); po.SetMirror(False); po.SetUseGerberAttributes(False)
po.SetUseGerberProtelExtensions(True); po.SetExcludeEdgeLayer(False)
po.SetSubtractMaskFromSilk(True); po.SetCreateGerberJobFile(False)
for layer in [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu,
              pcbnew.F_Mask, pcbnew.B_Mask, pcbnew.F_SilkS, pcbnew.B_SilkS,
              pcbnew.Edge_Cuts]:
    pc.SetLayer(layer)
    pc.OpenPlotfile("smoke_%s" % B.GetLayerName(layer), pcbnew.PLOT_FORMAT_GERBER, "teste")
    pc.PlotLayer()
pc.ClosePlot()
dw = pcbnew.EXCELLON_WRITER(B)
dw.SetOptions(False, False, pcbnew.wxPoint(0,0), False)
dw.CreateDrillandMapFilesSet(out, True, False)
print("gerbers:", sorted(os.listdir(out)))
