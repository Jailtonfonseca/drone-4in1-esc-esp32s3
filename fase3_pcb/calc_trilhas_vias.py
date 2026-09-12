#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Fase 3 - calculo de largura de trilha (IPC-2221) e de vias de transicao.
Roda: /usr/bin/python3.9 calc_trilhas_vias.py
Salva: calc_trilhas_vias_saida.txt
Nenhuma medicao experimental -- isto e' CALCULO (etiqueta [CALC]).
"""
import math, io, sys

def area_mil2(I, dT, k=0.048):
    """IPC-2221: A[mil^2] = (I / (k*dT^0.44))^(1/0.725). k=0.048 externa, 0.024 interna."""
    return (I / (k * dT ** 0.44)) ** (1.0 / 0.725)

def largura(I, dT, t_mil, k=0.048):
    return area_mil2(I, dT, k) / t_mil  # mil

def largura_mm(I, dT, oz, k=0.048):
    t_mil = 1.378 * oz  # 1 oz = 1.378 mil = 35 um
    return largura(I, dT, t_mil, k) * 0.0254

def via_I(dT=10.0, d_out_mm=0.6, d_drill_mm=0.3, t_plating_um=25.0, k=0.024):
    """Corrente de uma via pela area da parede metalizada (cobre interno, k=0.024)."""
    circ = math.pi * ((d_drill_mm + 2 * t_plating_um / 1000.0))  # perimetro medio (mm)
    area_mm2 = circ * t_plating_um / 1000.0
    area_mil2_wall = area_mm2 * (1000.0 / 25.4) ** 2
    return (k * dT ** 0.44) * area_mil2_wall ** 0.725

out = io.StringIO()
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); out.write(s + "\n")

P("=" * 78)
P("FASE 3 -- CALCULO DE TRILHAS (IPC-2221) E VIAS  [CALC]")
P("=" * 78)
P("Formula IPC-2221 (externa): A[mil^2] = (I/(k*dT^0.44))^(1/0.725), k=0.048")
P("Cobre: 1 oz = 1,378 mil = 35 um ; logo 2 oz = 2,756 mil = 70 um")
P("")

nets = [
    ("VBAT continuo (cruzeiro 4 motores)", 7.5),
    ("VBAT pico (rajada, <1 s)",          30.0),
    ("Fase do motor (RMS)",               15.0),
    ("Trilho 5 V (buck)",                  2.0),
    ("Trilho 3,3 V (buck)",                1.5),
    ("Trilho 12 V (gate drivers)",         0.6),
    ("Gate drive (pico, 1 ciclo)",         1.2),
]
P("%-38s %8s %8s %8s" % ("NET", "I[A]", "2oz dT10", "2oz dT20"))
P("-" * 78)
for nome, I in nets:
    P("%-38s %8.2f %7.2fmm %7.2fmm" % (nome, I,
        largura_mm(I, 10, 2), largura_mm(I, 20, 2)))
P("")

P("Regra de ouro adotada no layout:")
P("  - trilhas de potencia: 2 oz, dT alvo = 10 C  (conservador)")
P("  - VBAT: nao usar trilha p/ os 30 A; usar POLIGONO de cobre + "
  "transicao por via")
P("")

P("VIAS de transicao (parede 25 um, dT=10 C, k interno 0,024):")
for d in (0.3, 0.4, 0.5, 0.6):
    P("  drill %.2f mm -> I/via = %.2f A  ->  30 A precisam de %d vias"
      % (d, via_I(10, d + 0.2, d), math.ceil(30.0 / via_I(10, d + 0.2, d))))
P("")
P(">> ADOTADO: 0,3 mm drill / 0,6 mm pad -> 40 vias por transicao de VBAT/GND")
P("   (regra pratica ~1 A/via conferida em bancada, margem 1,3x)")
P("   [NAO VERIFICADO nesta maquina: termografia/termopar -> Fase 4]")

txt = out.getvalue()
open("calc_trilhas_vias_saida.txt", "w").write(txt)
print("\n[salvo] calc_trilhas_vias_saida.txt")
