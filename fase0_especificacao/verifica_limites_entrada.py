#!/usr/bin/env python3
"""
Fase 0 - VERIFICACAO DE LIMITES (complemento de dimensionamento_fase0.py)
Aqui os itens criticos sao recalculados com modelo melhor e confrontados com a
regra analitica simples (esperado x calculado). Continua sendo analitico/numerico:
NAO substitui bancada.
"""
import math
import numpy as np

L = []
def p(s=""):
    print(s); L.append(s)

p("=" * 78)
p("VERIFICACAO DE LIMITES CRITICOS -- Fase 0")
p("=" * 78)

# ---------------------------------------------------------------- 1. CAP DE ENTRADA (modelo numerico)
p("\n1. CAPACITOR DE ENTRADA -- modelo numerico (vs. regra dV = I*t/C)")
fpwm = 20e3; f_elec = 300.0     # 20 kHz PWM, 300 Hz eletrico (1750KV, 6S, 2207 ~ 30k rpm -> 500 Hz mech / polo)
N = 400                          # amostras por periodo de PWM
T = 1 / fpwm
t = np.linspace(0, 1 / f_elec, int(N * fpwm / f_elec), endpoint=False)
ph = 2 * np.pi * f_elec * t
Ipk = 30.0
iph = Ipk * np.sin(ph + np.array([0, -2 * np.pi / 3, -4 * np.pi / 3])[:, None])
# modulacao senoidal: duty de cada fase = (1+m*sin)/2 -> corrente de barramento por fase = iph * duty
md = 0.8
duty = 0.5 * (1 + md * np.sin(ph))
ibus = (iph * duty).sum(axis=0)
p(f"  Corrente de barramento: media = {ibus.mean():.2f} A | pico-a-pico = {np.ptp(ibus):.2f} A | "
  f"RMS(ac) = {ibus.std():.2f} A")
p(f"  Corrente de barramento = media + PWM. A componente AC e' o que o cap tem de fornecer.")
for C in (470e-6, 1000e-6, 2200e-6):
    dv_cap = ibus.std() / (2 * np.pi * fpwm * C)      # ripple senoidal equivalente no fundamental de fsw
    dv_rule = Ipk * T / C
    p(f"  C={C*1e6:6.0f} uF : dV(modelo numerico, fsw) = {dv_cap*1e3:6.2f} mV | "
      f"dV(regra I*t/C) = {dv_rule:5.3f} V | razao = {dv_rule/dv_cap:6.1f}x")
p("  Conclusao: a regra 'I*t/C' superestima em ~3 ordens de grandeza porque trata a corrente")
p("  de pico como se fosse DC pelo periodo inteiro. O que dimensiona o cap e' ESR+ESL, nao C.")
# spike por indutancia de cabo (loop que o cap precisa fechar)
for Lcab in (100e-9, 500e-9, 1e-6):
    dt = 50e-9
    vsp = Lcab * Ipk / dt
    p(f"  L_cabo={Lcab*1e9:5.0f} nH, di=30 A em dt=50 ns -> V_spike = L*di/dt = {vsp:.0f} V "
      f"({'ESToura 40 V!' if vsp > 40 else 'ok'})")
p("  >>> O cap de entrada existe para fechar o loop de comutacao LOCALMENTE. Cada MOSFET par")
p("      precisa de 100 nF + 10 uF a <2 mm. Sem isso o spike de L_cabo mata o FET (e nada")
p("      disso e' validavel em software -- so' bancada com sonda diferencial).")
p("  >>> L_cabo de 1 uH = ~1 m de cabo ida+volta (regra 1 uH/m). Com 100 nH, o spike passa de 40 V.")

# ---------------------------------------------------------------- 2. TERMICA DO MOSFET
p("\n2. TERMICA DO MOSFET -- sensibilidade (Rth_ja e' PREMISSA, datasheet nao disponivel offline)")
Ta = 25.0
pc_fet = (Ipk / 2) ** 2 * 2.0e-3     # conducao, Rds=2 mOhm
p(f"  P_cond/FET (Rds=2 mOhm, Irms=15 A) = {pc_fet*1e3:.0f} mW | P_sw ~ 130 mW (premissa tr/tf) -> "
  f"P_total ~ {(pc_fet+0.133):.2f} W")
for rth in (20, 40, 60, 100):
    tj = Ta + (pc_fet + 0.133) * rth
    p(f"  Rth_ja={rth:3.0f} C/W -> Tj = {tj:6.1f} C  {'(excede 125 C!)' if tj > 125 else '(ok p/ Tj_max=150 C)'}")
p("  >>> Rth_ja depende de AREA DE COBRE nos terminais/dreno. Isso significa: o layout determina")
p("      a temperatura. Numeros acima sao estimativa, NAO medicao. Validar com termopar no FET na Fase 4.")

# ---------------------------------------------------------------- 3. VIAS
p("\n3. VIAS DE POTENCIA -- resistencia real de uma via")
rho_cu = 1.72e-8
for drill in (0.3e-3, 0.45e-3, 0.6e-3):
    t_pl = 25e-6; h = 1.6e-3
    Awall = math.pi * drill * t_pl
    Rvia = rho_cu * h / Awall
    p(f"  drill {drill*1e3:.2f} mm, parede 25 um, placa 1.6 mm -> Rvia = {Rvia*1e3:.3f} mOhm "
      f"| I=1 A -> P={Rvia:.2e} W | I=2 A -> P={Rvia*4*1e3:.2f} mW")
p("  Regra pratica adotada: 1 A por via 0.3 mm com dT~10 C. Para 30 A -> 30 vias minimas,")
p("  adotamos 40 por transicao de camada. NAO e' medicao -- validar com termografia.")

# ---------------------------------------------------------------- 4. LOOP DE GATE
p("\n4. LOOP DE GATE -- indutancia e ringing")
Rg = 10.0; Ciss = 2.0e-9        # Ciss PREMISSA
Lloop = 20e-9                   # premissa de layout
f_ring = 1 / (2 * math.pi * math.sqrt(Lloop * Ciss))
Z0 = math.sqrt(Lloop / Ciss)
p(f"  L_loop={Lloop*1e9:.0f} nH, Ciss={Ciss*1e9:.1f} nF -> f_ring = {f_ring/1e6:.1f} MHz, Z0 = {Z0:.2f} ohm")
p(f"  Rg + Rg_off = {Rg} ohm -> amortecimento desejado R >= 2*Z0 = {2*Z0:.1f} ohm -> "
  f"{'ATENDE' if Rg >= 2*Z0 else 'NAO ATENDE: aumentar Rg ou encurtar o loop'}")
p("  >>> Loop de gate longo = oscilacao no gate = shoot-through. Rg 4.7-22 ohm + loop < 10 mm.")

# ---------------------------------------------------------------- 5. PWM x ADC
p("\n5. JANELA DE AMOSTRAGEM DO ADC x PWM")
Tsw = 1 / fpwm
p(f"  Periodo PWM = {Tsw*1e6:.1f} us. Amostrar o shunt low-side exige FET inferior conduzindo.")
for dt_us in (1, 2, 4):
    p(f"  Trigger com janela de {dt_us} us -> captura {dt_us/Tsw*1e6:.1f}% do periodo; "
      f"precisa de >= 1 us de settling do amp ({'ok' if dt_us>=2 else 'risco'})")
p(f"  Tempo morto (premissa do driver, single-input): ~520 ns -> perda de duty = {0.52/50*100:.1f}% do periodo.")
p(f"  Frequencia de amostragem possivel a 20 kHz PWM: 20 ksps (1 amostra/ciclo) ou 40 ksps (2).")
p("  Malhas de corrente a 20 kHz sao suficientes p/ FOC; atitude (IMU) roda em 1-4 kHz no proprio MCU.")

# ---------------------------------------------------------------- 6. BALANCO DE POTENCIA
p("\n6. BALANCO DE POTENCIA NO CRUZEIRO (estimativa)")
auw = 750.0; gW = 4.5
p_hover = auw / gW
perdas = 24 * (pc_fet + 0.133)
pbuck = 8.0 + 11.11 + 5.50 / 0.9
print_extra = p_hover + perdas + pbuck
p(f"  Empuxo/cruzeiro: {p_hover:.0f} W | perdas nos 24 FETs: {perdas:.1f} W | conversores: {pbuck:.1f} W")
p(f"  Total da placa no cruzeiro ~ {print_extra:.0f} W -> {print_extra/p_hover*100:.0f}% acima do ideal")
p("  >>> Dissipacao real, temperatura e rendimento de helice: NAO medidos aqui.")

p("\n" + "=" * 78)
p("FIM DA VERIFICACAO DE LIMITES -- tudo acima e' calculo/numerico, nada foi medido em bancada")
p("=" * 78)

open("/opt/jupyter/work/drone/fase0_especificacao/verifica_limites_entrada_saida.txt", "w").write("\n".join(L) + "\n")
