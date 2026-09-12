#!/usr/bin/env python3
"""
Fase 0 - VERIFICACAO DE LIMITES -- v3 (final)
Correcao sobre a v2: C5) coluna dV_total era V rotulado como mV (bug de formatacao,
sem efeito na fisica). Agora em mV de verdade.
Novo: C6) ripple AGREGADO dos 4 motores -- sincronizado vs. portadoras intercaladas 90 graus.
"""
import math
import os
import numpy as np
L = []
def p(s=""):
    print(s); L.append(s)

p("=" * 78)
p("FASE 0 -- LIMITES CRITICOS (v3, final)")
p("=" * 78)

fpwm, f_elec, Ipk, m = 20e3, 300.0, 30.0, 0.80
ppp = 200
dt = 1 / (fpwm * ppp)
n = int(round(1 / f_elec / dt))
ts = np.arange(n) * dt
theta = 2 * np.pi * f_elec * ts
ang = theta + np.array([0.0, -2*np.pi/3, -4*np.pi/3])[:, None]
iph = Ipk * np.sin(ang)
duty = 0.5 * (1 + m * np.sin(ang))

def corrente_barramento(offset_carrier):
    carrier = (fpwm * ts + offset_carrier) % 1.0
    sw = np.array([(carrier < duty[k]).astype(float) for k in range(3)])
    return (iph * sw).sum(axis=0)

p("\n1. UM MOTOR -- ripple de corrente no barramento (PWM resolvido, 250 ns/amostra)")
ib = corrente_barramento(0.0)
imean, iac = ib.mean(), ib - ib.mean()
p(f"  I_med={imean:.2f} A (analitico (3/4)*m*Ipk={0.75*m*Ipk:.2f} A, erro "
  f"{abs(imean-0.75*m*Ipk)/(0.75*m*Ipk)*100:.3f} %) | RMS(ac)={iac.std():.2f} A | |I_ac|max={np.abs(iac).max():.2f} A")
p("")
p(f"  {'C [uF]':>8} {'ESR [mOhm]':>11} | {'dV_C pkpk':>10} {'dV_ESR pk':>10} {'dV_TOTAL pkpk':>14} | 'I*t/C'")
for C, esr in [(470e-6,15e-3),(1000e-6,12e-3),(2200e-6,10e-3),(4400e-6,8e-3)]:
    v = np.zeros_like(iac)
    for i in range(1, n):
        v[i] = v[i-1] + iac[i]*dt/C
    dvC = (v.max()-v.min())*1e3
    dvE = np.abs(iac).max()*esr*1e3
    p(f"  {C*1e6:8.0f} {esr*1e3:11.1f} | {dvC:9.0f}mV {dvE:9.0f}mV {dvC+dvE:13.0f}mV | {Ipk/fpwm/C:6.3f} V")

p("\n2. QUATRO MOTORES NO MESMO BARRAMENTO -- o caso que decide a bancada de capacitores")
tot_sinc = sum(corrente_barramento(0.0) for _ in range(4))
tot_int  = sum(corrente_barramento(k*0.25) for k in range(4))   # portadoras defasadas 90 graus
for nome, x in [("portadoras SINCRONIZADAS", tot_sinc), ("portadoras INTERCALADAS 90o", tot_int)]:
    ac = x - x.mean()
    p(f"  {nome:30s}: I_med={x.mean():7.2f} A | RMS(ac)={ac.std():6.2f} A | |I_ac|max={np.abs(ac).max():6.2f} A")
r1 = (tot_sinc-tot_sinc.mean()).std(); r2 = (tot_int-tot_int.mean()).std()
p(f"  Ganho do intercalamento no ripple RMS: {r1/r2:.2f}x  ({r1:.2f} A -> {r2:.2f} A)")
p("  >>> DECISAO DE PROJETO: os 4 MCPWM/LEDC devem ter portadoras defasadas de 90 graus entre motores.")
p("      Isso reduz a corrente RMS no banco de capacitores ~2x e e' de graca (e' configuracao de timer).")
ac4 = tot_int - tot_int.mean()
p(f"\n  Banco adotado (4x 470 uF polimero, ESR 15 mOhm): com 1 cap por motor, cada cap ve ~1 motor.")
for nome, x in [("cap dedicado por motor (adotado)", ib - ib.mean())]:
    for C, esr in [(470e-6, 15e-3)]:
        v = np.zeros_like(x)
        for i in range(1, n):
            v[i] = v[i-1] + x[i]*dt/C
        p(f"    {nome}: dV_C={(v.max()-v.min())*1e3:.0f} mV + dV_ESR={np.abs(x).max()*esr*1e3:.0f} mV "
          f"= {(v.max()-v.min())*1e3+np.abs(x).max()*esr*1e3:.0f} mV pk-pk "
          f"({((v.max()-v.min())*1e3+np.abs(x).max()*esr*1e3)/25.2*100:.1f} % de 25.2 V)")
p("  >>> Com 100 nF + 10 uF ceramico colados a cada par de MOSFETs, o cap eletrolitico deixa de ver")
p("      o degrau de fsw e passa a ver so' o envelope -> este numero e' o PIOR caso (sem os ceramicos).")
p("      Layout e' o que prova isso: Fase 3, e bancada na Fase 4.")

p("\n3. TERMICA (Rth_ja PREMISSA) / VIAS / GATE / ADC -- resumo")
rds = 2.0e-3
for nome, ipk in [("cruzeiro (5 A fase)",5.0),("nominal (15 A)",15.0),("pico (30 A)",30.0)]:
    pc = (ipk/2)**2*rds; psw = 0.133*(ipk/30)**2
    p(f"  {nome:20s}: P/FET={pc+psw:.3f} W -> 24 FETs={24*(pc+psw):5.2f} W | "
      f"Tj(Rth=60C/W, Ta=25C) = {25+(pc+psw)*60:.1f} C")
Rv = 1.72e-8*1.6e-3/(math.pi*0.3e-3*25e-6)
p(f"  Via 0.3 mm: R={Rv*1e3:.3f} mOhm -> 40 vias a 30 A: queda {30*Rv/40*1e3:.3f} mV, P={30**2*Rv/40*1e3:.0f} mW total")
Z0 = math.sqrt(20e-9/2e-9)
p(f"  Gate: Z0={Z0:.2f} ohm -> Rg>=6.3 ohm (adotado 10 ohm) | f_ring={1/(2*math.pi*math.sqrt(20e-9*2e-9))/1e6:.1f} MHz")
p(f"  ADC: janela 2 us = {2/(1/fpwm*1e6)*100:.1f} % do periodo de 50 us | dead-time 520 ns = {0.52/50*100:.1f} % de duty")

p("\n4. BALANCO NO CRUZEIRO (carga real, nao nominal)")
p_h = 750/4.5; i_bus = p_h/22.2; i_fase = i_bus/0.6
pc_h = (i_fase/2)**2*rds*24
conv = (3.3*0.55 + 12*0.049 + 5*0.20)/0.85
p(f"  Helice: {p_h:.0f} W | I_barra {i_bus:.1f} A | I_fase pico {i_fase:.1f} A")
p(f"  FETs: {pc_h:.2f} W | conversores: {conv:.2f} W (entrada) | TOTAL ~ {p_h+pc_h+conv:.0f} W "
  f"({(p_h+pc_h+conv)/p_h*100-100:.1f} % acima do ideal de helice)")

p("\n" + "="*78)
p("FIM v3 -- 100% calculo numerico. Nenhuma medicao de bancada.")
p("="*78)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verifica_limites_saida_v3.txt"),"w").write("\n".join(L)+"\n")
