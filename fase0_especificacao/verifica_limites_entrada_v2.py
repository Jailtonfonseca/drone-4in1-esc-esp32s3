#!/usr/bin/env python3
"""
Fase 0 - VERIFICACAO DE LIMITES -- v2 (supersede a v1)
Correcoes em relacao a v1 (registradas no relatorio):
  C1) v1 aplicava o MESMO duty as 3 fases -> soma das correntes = 0 (modelo invalido).
      Agora duty e' por fase (angulo deslocado 120 graus).
  C2) v1 nao resolvia a comutacao PWM: agora a corrente de barramento e' gerada com
      portadora triangular real (resolve o ripple de fsw, que e' o que o cap ve).
  C3) v1 tinha erro de unidade no calculo "captura X% do periodo" (us/sem conversao).
  C4) v1 comparava perdas no CRUZEIRO usando corrente de PICO -> agora ha dois casos
      (cruzeiro e pico) e o balanco dos conversores usa a CARGA REAL, nao a nominal.
Tudo continua sendo calculo numerico -- nada foi medido em bancada.
"""
import math
import os
import numpy as np

L = []
def p(s=""):
    print(s); L.append(s)

p("=" * 78)
p("VERIFICACAO DE LIMITES CRITICOS -- Fase 0 (v2)")
p("=" * 78)

# ================================================================ 1. CAP DE ENTRADA
p("\n1. CAPACITOR DE ENTRADA -- modelo numerico COM comutacao PWM resolvida")
fpwm = 20e3; f_elec = 300.0; Ipk = 30.0; m = 0.80
ppp = 200                                     # pontos por periodo de PWM
dt = 1 / (fpwm * ppp)
n = int(round(1 / f_elec / dt))
ts = np.arange(n) * dt
theta = 2 * np.pi * f_elec * ts
ang = theta + np.array([0.0, -2 * np.pi / 3, -4 * np.pi / 3])[:, None]
iph = Ipk * np.sin(ang)                       # corrente de fase (constante dentro do periodo PWM)
duty = 0.5 * (1 + m * np.sin(ang))            # modulacao senoidal por fase
carrier = (fpwm * ts) % 1.0                   # portadora triangular 0..1
sw = np.array([(carrier < duty[k]).astype(float) for k in range(3)])
ibus_sw = (iph * sw).sum(axis=0)              # corrente instantanea puxada do barramento
imean = ibus_sw.mean()
iac = ibus_sw - imean
p(f"  Modelo: 20 kHz PWM, 300 Hz eletrico, m={m:.2f}, Ipk={Ipk:.0f} A, "
  f"{n} amostras ({dt*1e9:.0f} ns)")
p(f"  I_barramento: media = {imean:6.2f} A | pico = {ibus_sw.max():6.2f} A | "
  f"RMS(ac) = {iac.std():6.2f} A | I_pk(ac) = {np.abs(iac).max():6.2f} A")
p(f"  Conferencia analitica: I_med = (3/4)*m*Ipk = {0.75*m*Ipk:.2f} A  | "
  f"erro = {abs(imean-0.75*m*Ipk)/(0.75*m*Ipk)*100:.3f} %")
p("")
p(f"  {'C':>8} {'ESR':>7} | {'dV_C(pk-pk)':>12} {'dV_ESR(pk)':>11} {'dV_total':>9} | regra I*t/C")
for C, esr in [(470e-6, 15e-3), (1000e-6, 12e-3), (2200e-6, 10e-3), (4400e-6, 8e-3)]:
    v = np.zeros_like(iac); v[0] = 0.0
    for i in range(1, n):                     # integra i = C dv/dt (Euler, dt pequeno)
        v[i] = v[i - 1] + iac[i] * dt / C
    dvC = v.max() - v.min()
    dvE = np.abs(iac).max() * esr
    p(f"  {C*1e6:8.0f} {esr*1e3:6.1f}m | {dvC*1e3:11.1f}mV {dvE*1e3:10.1f}mV {dvC+dvE:8.1f}mV | {Ipk/fpwm/C:6.3f} V")
p("  Leitura: a regra 'I*t/C' (ultima coluna) da' VOLTS; o ripple real fica em mV. O que manda e'")
p("  ESR do cap + ESL do layout. Nao ha trilha de cobre que salve um cap ruim.")
for Lcab in (100e-9, 500e-9):
    p(f"  L_cabo={Lcab*1e9:4.0f} nH, di=30 A em dt=50 ns -> V_spike = L*di/dt = {Lcab*Ipk/50e-9:5.0f} V "
      f"({'ESTOURA o MOSFET de 40 V' if Lcab*Ipk/50e-9 > 40 else 'ok'})")
p("  >>> Conclusao de projeto: 4x470 uF polimero (low-ESR) + 10 uF + 100 nF POR MOSFET PAR,")
p("      a <2 mm do par, com o loop de comutacao minimizado no layout.")

# ================================================================ 2. TERMICA
p("\n2. TERMICA DO MOSFET -- dois pontos de operacao (Rth_ja e' PREMISSA)")
rds = 2.0e-3; Ta = 25.0; psw_fet = 0.133
for nome, ipk in [("cruzeiro (~5 A de fase pico)", 5.0), ("nominal (15 A)", 15.0), ("pico (30 A)", 30.0)]:
    pc = (ipk / 2) ** 2 * rds
    ptot = pc + psw_fet * (ipk / 30.0) ** 2
    p(f"  {nome:26s}: P_cond={pc*1e3:7.1f} mW, P_sw={psw_fet*(ipk/30)**2*1e3:6.1f} mW -> P={ptot:5.2f} W/FET "
      f"-> 24 FETs = {24*ptot:5.2f} W")
    for rth in (30, 60, 100):
        tj = Ta + ptot * rth
        p(f"      Rth_ja={rth:3d} C/W -> Tj={tj:6.1f} C {'>> EXCEDE 125 C' if tj>125 else ''}")
p("  >>> Rth_ja vem da AREA DE COBRE do layout -> a temperatura e' decidida no PCB (Fase 3)")
p("      e comprovada com termopar (Fase 4). Nada aqui e' medicao.")

# ================================================================ 3. VIAS
p("\n3. VIAS DE POTENCIA")
rho = 1.72e-8
for d in (0.3e-3, 0.45e-3, 0.6e-3):
    A = math.pi * d * 25e-6
    Rv = rho * 1.6e-3 / A
    p(f"  drill {d*1e3:.2f} mm / parede 25 um / placa 1.6 mm -> R = {Rv*1e3:.3f} mOhm | "
      f"30 vias em paralelo = {Rv/30*1e3:.3f} mOhm -> queda a 30 A = {30*Rv/30*1e3:.3f} mV, "
      f"P_total = {30**2*Rv/30*1e3:.1f} mW")
p("  Adotado: 40 vias de costura (0.3 mm) por transicao de camada. NAO medido.")

# ================================================================ 4. GATE
p("\n4. LOOP DE GATE")
Rg = 10.0; Ciss = 2.0e-9; Ll = 20e-9
fring = 1 / (2 * math.pi * math.sqrt(Ll * Ciss)); Z0 = math.sqrt(Ll / Ciss)
p(f"  L_loop={Ll*1e9:.0f} nH, Ciss={Ciss*1e9:.1f} nF -> f_ring={fring/1e6:.1f} MHz, Z0={Z0:.2f} ohm")
p(f"  Rg={Rg:.0f} ohm >= 2*Z0={2*Z0:.1f} ohm -> {'AMORTECIDO' if Rg>=2*Z0 else 'SUBDIMENSIONADO'}")

# ================================================================ 5. ADC x PWM
p("\n5. JANELA DE ADC x PWM")
Tsw = 1 / fpwm
p(f"  T_PWM = {Tsw*1e6:.1f} us")
for dt_us in (1.0, 2.0, 4.0):
    p(f"  janela {dt_us:.0f} us -> {dt_us/(Tsw*1e6)*100:4.1f} % do periodo "
      f"(precisa >= 1 us de settling do amp -> {'risco' if dt_us<2 else 'ok'})")
p(f"  tempo morto ~520 ns (premissa de driver single-input) -> {0.52/(Tsw*1e6)*100:.1f} % de duty perdido")
p(f"  taxa de amostragem: 1 amostra/ciclo = {fpwm/1e3:.0f} ksps (FOC ok); 2 amostras = {2*fpwm/1e3:.0f} ksps")

# ================================================================ 6. BALANCO
p("\n6. BALANCO DE POTENCIA -- CARGA REAL, nao nominal")
auw, gW = 750.0, 4.5
p_hover = auw / gW
i_hover_bus = p_hover / 22.2
i_fase_hover = i_hover_bus / 0.75 / 0.8      # desfazendo o modelo (3/4)*m*Ipk
pc_h = (i_fase_hover / 2) ** 2 * rds * 24
conv_cruzeiro = 3.3 * 0.55 + 12 * 0.049 + 5 * 0.20
conv_cruzeiro = conv_cruzeiro / 0.85          # entrada, 85% de rendimento
ptot_h = p_hover + pc_h + conv_cruzeiro
p(f"  Empuxo p/ sustentar {auw:.0f} g: {p_hover:.0f} W -> I_barra = {i_hover_bus:.1f} A "
  f"-> I_fase(pico) = {i_fase_hover:.1f} A")
p(f"  Perdas de conducao nos 24 FETs (cruzeiro): {pc_h:.2f} W")
p(f"  Conversores (MCU+radio 0.55 A@3.3, gate 49 mA@12, aux 0.20 A@5): {conv_cruzeiro:.2f} W na entrada")
p(f"  TOTAL da placa no cruzeiro = {p_hover:.0f} W (helice) + {pc_h:.2f} W + {conv_cruzeiro:.2f} W "
  f"= {ptot_h:.0f} W  ({ptot_h/p_hover*100-100:.1f} % acima do ideal)")
p(f"  No PICO (4x30 A): so' a conducao dos FETs = {24*(15**2*rds):.1f} W + comutacao ~3.2 W + helice (I^2) "
  f"-> regime termico de rajada, NAO continuo.")
p("  >>> Rendimento da helice (g/W) e' PREMISSA. O numero que importa (temperatura real em voo)")
p("      nao existe nesta maquina: exige tunel de vento/bancada.")

p("\n" + "=" * 78)
p("FIM -- calculo numerico. Nenhuma medicao de bancada foi feita.")
p("=" * 78)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verifica_limites_saida_v2.txt"), "w").write("\n".join(L) + "\n")
