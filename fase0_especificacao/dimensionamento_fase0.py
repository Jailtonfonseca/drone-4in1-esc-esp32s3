#!/usr/bin/env python3
"""
Fase 0 - ESPECIFICACAO do drone (4x ESC trifasico + MCU WiFi na mesma PCB)
Dimensionamento analitico. TODA premissa esta marcada com P-xx.

IMPORTANTE: nenhum datasheet esta no disco desta maquina.
Todos os parametros que normalmente vem de datasheet (Rds_on, Qg, Ciss, gain de
amp, correntes nominais de conector, Vf de diodo) entram aqui como PREMISSA
explicita, nunca como "dado de datasheet". A confirmacao experimental acontece
na Fase 2 (ngspice) e na bancada (Fase 4).
"""
import json, math, sys

R = {}          # resultados
P = {}          # premissas

def h(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)

def fmt(x, u="", n=4):
    return f"{x:.{n}g} {u}".strip()

# ---------------------------------------------------------------- PREMISSAS
h("0. PREMISSAS (P-xx) -- NENHUMA VERIFICADA EM DATASHEET (nao ha datasheet offline)")
P["P01_motor"] = "2207, 1750 KV, helice 5\"/3 pas  (usuario ainda nao forneceu dados reais)"
P["P02_bateria"] = "LiPo 6S (22.2 V nom, 25.2 V max, 19.8 V a 3.30 V/celula)"
P["P03_i_pico_motor"] = 30.0      # A por motor, pico (rajada)
P["P04_i_cont_motor"] = 15.0      # A por motor, continuo (premissa, confirmar na bancada)
P["P05_rds_on"] = 2.0e-3          # ohm, MOSFET de potencia 40-60 V, classe 2 mOhm (PREMISSA)
P["P06_qg"] = 40e-9               # C, carga total de gate (PREMISSA)
P["P07_fpwm"] = 20e3              # Hz, frequencia de chaveamento do inversor
P["P08_fbuck"] = 500e3            # Hz, frequencia de chaveamento dos bucks
P["P09_shunt"] = 0.5e-3           # ohm, shunt de fase (manganina 2512, 2 W)
P["P10_gain_csa"] = 50.0          # ganho do amplificador de corrente (PREMISSA)
P["P11_iq_driver"] = 2.5e-3       # A, consumo de quiescencia por gate driver (PREMISSA)
P["P12_adc_bits"] = 12            # ADC do ESP32-S3
P["P13_vref"] = 3.300             # V, referencia do ADC (atenuacao 11 dB ~ FS 3.1-3.3 V)
print(json.dumps(P, indent=2))

# ---------------------------------------------------------------- 1. MOTORES
h("1. ESTAGIO DE POTENCIA -- 4x inversor trifasico (12 half-bridges, 24 MOSFETs)")
Vmax, Vnom, Vmin = 25.2, 22.2, 19.8
print(f"Tensao de barramento: max {Vmax} V | nom {Vnom} V | min {Vmin} V")
print("-> MOSFET precisa de Vds >= 40 V (margem 1.6x sobre 25.2 V). Premissa de classe 40-60 V.")

irms_fet = lambda i_pk: i_pk / 2.0          # cada FET conduz ~metade do ciclo (modulacao senoidal)
for rds in (1.5e-3, 2.0e-3, 3.0e-3, 5.0e-3):
    irms = irms_fet(P["P03_i_pico_motor"])
    pc = irms ** 2 * rds
    print(f"  Rds_on={rds*1e3:4.1f} mOhm -> Irms/FET={irms:5.2f} A -> Pcond={pc*1e3:6.1f} mW/FET "
          f"-> 24 FETs = {pc*24:6.2f} W no total")
print(f"  (premissa adotada: Rds_on = {P['P05_rds_on']*1e3:.1f} mOhm -> "
      f"{(irms_fet(30)**2*P['P05_rds_on'])*24:.2f} W de conducao total)")

# perdas de comutacao (estimativa analitica, NAO medida)
tr = tf = 20e-9
Esw = Vnom * P["P03_i_pico_motor"] * (tr + tf) / 2 / 2   # /2 dev: cada FET chaveia ~1 vez por periodo util
Psw_fet = Esw * P["P07_fpwm"]
print(f"  Comutacao: tr=tf=20 ns -> Esw={Esw*1e9:.2f} nJ por evento -> {Psw_fet*1e3:.1f} mW/FET "
      f"-> 24 FETs = {Psw_fet*24:.2f} W")
print("  >>> ATENCAO: tr/tf e' PREMISSA. Dissipacao real, acoplamento termico e EMI so se provam na bancada.")

# corrente total
itot_pk = 4 * P["P03_i_pico_motor"]
itot_cont = 4 * P["P04_i_cont_motor"]
print(f"\nBarramento: PICO = {itot_pk:.0f} A | CONTINUO (premissa) = {itot_cont:.0f} A")
pw_pk = Vmax * itot_pk
print(f"Potencia instantanea de pico no barramento = {pw_pk:.0f} W ({pw_pk/746:.2f} hp)  << numero de seguranca")
# estimativa de cruzeiro, modelo empirico de eficiencia de helice (PREMISSA)
g_per_W = 4.5
auw_g = 750.0
p_hover = auw_g / g_per_W
i_hover = p_hover / Vnom
print(f"Estimativa de CRUZEIRO (PREMISSA AUW={auw_g:.0f} g, {g_per_W} g/W): P={p_hover:.0f} W "
      f"-> I_barramento = {i_hover:.1f} A  (usar este valor para dimensionar trilha continua)")

# ---------------------------------------------------------------- 2. GATE DRIVE
h("2. DRIVE DE GATE (12 half-bridges x driver com dead-time interno + bootstrap)")
vgs = 12.0
Pg_fet = P["P06_qg"] * vgs * P["P07_fpwm"]
print(f"Potencia de gate por FET: Qg*Vgs*f = {P['P06_qg']*1e9:.0f} nC * {vgs} V * {P['P07_fpwm']/1e3:.0f} kHz "
      f"= {Pg_fet*1e3:.2f} mW")
print(f"Por driver (2 FETs) = {2*Pg_fet*1e3:.2f} mW | 12 drivers = {12*2*Pg_fet*1e3:.2f} mW")
ipk_gate_10r = vgs / 10.0
ipk_gate_5r = vgs / 5.0
print(f"Corrente de pico de gate: Rg=10 ohm -> {ipk_gate_10r:.2f} A | Rg=5 ohm -> {ipk_gate_5r:.2f} A "
      f"(vem do cap de bootstrap + 10 uF local, nao do buck)")
t_r = P["P06_qg"] / ipk_gate_10r
print(f"Tempo de subida estimado t_r = Qg/Ipk = {t_r*1e9:.2f} ns com Rg=10 ohm")
c_boot = 20 * P["P06_qg"]
print(f"Capacitor de bootstrap: Cboot >= 20*Qg = {c_boot*1e9:.0f} nF -> adotar 1 uF/25 V X7R")
print(f"Queda no bootstrap a cada ciclo: dV = Qg/Cboot = {P['P06_qg']/1e-6:.3f} V")
# dimensao do trilho 12 V
iq12 = 12 * P["P11_iq_driver"]
i12_total = iq12 + 24 * Pg_fet / vgs
print(f"Trilho 12 V: quiescencia 12*{P['P11_iq_driver']*1e3:.1f} mA = {iq12*1e3:.0f} mA + "
      f"{24*Pg_fet/vgs*1e3:.1f} mA (carga de gate) = {i12_total*1e3:.0f} mA -> BUCK 12 V / 0.60 A com folga 3x")

# ---------------------------------------------------------------- 3. SENSORIAMENTO
h("3. SENSORIAMENTO DE CORRENTE (shunt low-side + amp) e BEMF")
Rsh = P["P09_shunt"]; G = P["P10_gain_csa"]
for ipk in (30.0, 40.0):
    vsh = ipk * Rsh
    vout = vsh * G
    print(f"  I={ipk:4.0f} A -> Vshunt={vsh*1e3:5.2f} mV -> Vout(ganho {G:.0f}) = {vout:5.3f} V")
        # com offset de 1.65 V (bidirecional)
    print(f"      saida bipolar: {1.650-vout:.3f} .. {1.650+vout:.3f} V  (limite 0..3.3 V)")
vsh30 = 30 * Rsh; vout30 = vsh30 * G
print(f"  Fundo de escala utilizado = {vout30/P['P13_vref']*100:.1f} % do ADC -> ADOTAR este par (Rs, G)")
psh_cont = P["P04_i_cont_motor"] ** 2 * Rsh
psh_pk = 30.0 ** 2 * Rsh
print(f"  Dissipacao no shunt: continua {psh_cont*1e3:.0f} mW | pico {psh_pk:.2f} W -> resistor 2512 2 W OK "
      f"(pico e' rajada, nao continuo)")
lsb = P["P13_vref"] / 2 ** P["P12_adc_bits"]
realdc = P["P13_vref"] / 1000   # erro tipico de ADC em ESP32-S3 (PREMISSA: 10 mV)
print(f"  Resolucao ADC: {lsb*1e6:.0f} uV/LSB -> {lsb/(Rsh*G)*1000:.1f} mA/LSB  "
      f"| erro de offset do ADC(~{realdc*1e3:.0f} mV) = {realdc/(Rsh*G):.2f} A de offset")
print("  >>> ATENCAO: shunt low-side so' e' valido quando o FET inferior esta ON -> a amostragem do ADC")
print("      TEM de ser sincronizada com o PWM (trigger no centro/centro-esquerda do periodo).")
    # BEMF
div = 25.2 / 3.0
print(f"  BEMF: divisor 1:{div:.2f} (ex. 8.2k/1.0k) -> 25.2 V => 3.07 V; cap 1 nF + clamp 3.3 V.")
vb = 3.07 - 0
print(f"      erro de divisor 1% : {3.07*0.02:.3f} V -> {3.07*0.02/(3.07/25.2):.2f} V na fase")

h("4. VBAT SENSE + FILTRO DE ADC")
Rtop, Rbot = 100e3, 13.7e3      # 25.2 V -> 3.03 V
ratio = Rbot / (Rtop + Rbot)
print(f"  Divisor {Rtop/1e3:.1f}k/{Rbot/1e3:.1f}k -> ratio {ratio:.5f}")
print(f"  25.2 V -> {25.2*ratio:.3f} V | 22.2 V -> {22.2*ratio:.3f} V | 19.8 V -> {19.8*ratio:.3f} V | "
      f"14.0 V -> {14.0*ratio:.3f} V")
i_div = 25.2 / (Rtop + Rbot)
print(f"  Corrente do divisor = {i_div*1e6:.0f} uA ({i_div*25.2*1e3:.2f} mW) -- aceitavel")
print(f"  Resolucao efetiva = {lsb/ratio*1000:.1f} mV/LSB -> {lsb/ratio/4.2*100:.3f} % da faixa de celula (4.2 V)")
fc = 1 / (2 * math.pi * ((Rtop*Rbot/(Rtop+Rbot)) ) * 100e-9)
print(f"  Filtro RC (C=100 nF): fc={fc:.1f} Hz (paralelo de Thevenin {Rtop*Rbot/(Rtop+Rbot)/1e3:.2f} kOhm)")

# ---------------------------------------------------------------- 5. BUCKS
h("5. FONTES CHAVEADAS (3 bucks) -- fsw = 500 kHz")
def buck(nome, vin_max, vin_min, vout, iout, fb=500e3, dril=0.30, dvout=0.010, esr=2e-3):
    dmax = vout / vin_min; dmin = vout / vin_max
    d = vout / vin_max
    L = (vin_max - vout) * dmax / (dril * iout * fb)
    cout = dril * iout / (8 * fb * dvout)
    icin_rms = iout * math.sqrt(d * (1 - d))
    pin = vout * iout / 0.90
    iin = pin / vin_min
    print(f"\n  [{nome}] {vin_min:.1f}-{vin_max:.1f} V -> {vout} V @ {iout:.2f} A")
    print(f"    D = {dmin:.3f}..{dmax:.3f} | L(30% ripple) = {L*1e6:.1f} uH -> adotar {round(L*1e6)} uH")
    print(f"    Cout (dV={dvout*1e3:.0f} mV) = {cout*1e6:.1f} uF -> adotar 2x22 uF X7R + 100 nF")
    print(f"    ripple ESR: dV_esr = dIL*ESR = {dril*iout*esr*1e3:.1f} mV (domina sobre o capacitivo)")
    print(f"    Ic_in(rms) = {icin_rms:.3f} A | Pin({0.90*100:.0f}%) = {pin:.2f} W -> Iin(vin_min) = {iin*1e3:.0f} mA")
    return dict(L=L, Cout=cout, D=dmax, iin=iin, icin=icin_rms)

b12 = buck("BUCK 12 V (gate drivers)", Vmax, Vmin, 12.0, 0.60, dvout=0.012)
b5 = buck("BUCK 5 V (USB/perifericos/aux)", Vmax, Vmin, 5.0, 2.00, dvout=0.025)
b33 = buck("BUCK 3.3 V (MCU+WiFi+sensores)", 5.0, 4.75, 3.3, 1.50, dvout=0.033)
ldo = dict(p=(5.0-3.3)*0.15)
print(f"\n  [LDO 3.3 V_A (analogico IMU/baro)] 5 V -> 3.3 V @ 0.15 A : Pdiss = {ldo['p']:.3f} W (SOT-23 com pad, OK)")

# ---------------------------------------------------------------- 6. CAP DE ENTRADA
h("6. CAPACITOR DE ENTRADA (barramento) -- conta de ripple")
for c, in [(470e-6,), (1000e-6,), (2200e-6,)]:
    dv = P["P03_i_pico_motor"] * (1 / P["P07_fpwm"]) / c
    print(f"  C={c*1e6:6.0f} uF : dV = I*t/C = 30 A * {1/P['P07_fpwm']*1e6:.0f} us / C = {dv:.3f} V "
          f"(por motor, pior caso pico)")
ics = 4 * P["P03_i_pico_motor"] * math.sqrt(0.5 * 0.5) / 2
print(f"  Ripple RMS agregado estimado (4 motores, D=50%): ~{ics:.1f} A -> exigir cap de entrada com")
print(f"  Io_ripple >= 1.5x = {ics*1.5:.0f} A. ADOTADO: 4x 470 uF/35 V low-ESR (polimero) + 4x 10 uF + 40x 100 nF ceramico junto aos FETs.")
print("  >>> ESR/ESL e' o que manda, nao a capacitancia. O layout (laco minimo) e' a metade do projeto.")
trip = 25.2 * 1.5
print(f"\n  TVS de entrada: precisa suportar Vbat max (25.2 V) sem conduzir -> standoff >= 30 V; "
      f"clamp ~{trip:.1f} V. PREMISSA (datasheet nao disponivel offline).")
print(f"  Protecao de inversao: P-FET ideal diode (Q de canal P, 30 V, Rdson < 10 mOhm) ou D Schottky "
      f"-> Schottky perderia Vf*I = 0.5 V * {i_hover:.1f} A = {0.5*i_hover:.1f} W. ADOTADO: P-FET + gate clamp.")

# ---------------------------------------------------------------- 7. COBRE / PCB
h("7. TRILHAS DE POTENCIA -- IPC-2221 (calculo, a ser validado na bancada)")
def ipc2221(I, dT, oz=2, external=True):
    k = 0.048 if external else 0.024
    A_mil = (I / (k * dT ** 0.44)) ** (1 / 0.725)     # mil^2
    t_mil = 1.378 * oz
    w_mil = A_mil / t_mil
    return w_mil * 0.0254, A_mil, t_mil
for I in (10, 30, 60, 120):
    for dT in (10, 20, 30):
        w, A, t = ipc2221(I, dT, 2)
        print(f"  I={I:5.0f} A, 2 oz (t={t:.0f} mil={t*25.4:.0f} um), dT={dT:2.0f} C -> "
              f"A={A:8.1f} mil^2 -> largura = {w:.2f} mm ({w/25.4*1000:.0f} mil)")
    print()
print("  Decisao: barramento DC (dezenas de A continuos) EM CAMADA INTERNA + metal exposto/barra;")
print("  nao existe trilha de 2 oz que aguente 120 A de forma continua -- 120 A e' PICO, nao continuo.")

# vias
def via_capacity(d_drill=0.3, t_wall=25e-6, dT=10):
    # via vertical: area da parede de cobre, aprox IPC
    d_mid = d_drill
    A_mil = math.pi * d_mid * t_wall / (0.0254 ** 2) * 1e0   # incompleto -> usar regra pratica abaixo
    return None
print("  Vias: regra pratica verificada em bancada ~ 1 A por via 0.3 mm (parede 25 um, dT 10 C).")
print("  => 30 A continuos exigem >= 30 vias de costura por transicao; adotar 40 (margem 1.3x).")
print("  >>> Isto e' REGRA PRATICA, nao medicao. Validar com termografia/termopar na Fase 4.")

# ---------------------------------------------------------------- 8. WiFi
h("8. ANALISE CRITICA DO REQUISITO 'CONTROLE VIA WiFi'")
print("  Orcamento de latencia (802.11 b/g/n 2.4 GHz, quadro unicast, sem retry):")
for rate, name in [(1e6, "1 Mbps (DSSS)"), (6e6, "6 Mbps (OFDM)"), (54e6, "54 Mbps (OFDM)")]:
    payload = 32 * 8
    overhead = 192
    t_air = (overhead + payload) / rate
    print(f"    {name:14s}: t_ar ~ {t_air*1e6:7.1f} us por quadro")
print("  Somar: backoff CSMA (~130 us tipico em rede limpa), fila do driver, USB/PHY,")
print("  e o pior caso: retry/ARQ. Medido na literatura pratica: 2-20 ms por pacote, com CAUDA longa")
print("  (p99 de 50-200 ms quando ha retransmissao). Isso NAO e' um canal de controle deterministico.")
for f in (50, 100, 250, 500):
    print(f"    Loop a {f:3d} Hz -> periodo {1000/f:5.1f} ms; jitter de 10 ms = {10/(1000/f)*100:5.0f}% do periodo")
print("\n  VEREDITO: 'pilotagem direta' (stick -> WiFi -> motor) NAO e' viavel com seguranca.")
print("  Arquitetura correta: WiFi/ESP-NOW apenas para COMANDOS (setpoint de atitude/posicao) a 20-50 Hz;")
print("  estabilizacao (IMU + PID) roda A BORDO a 1-8 kHz; FAILSAFE por timeout de link (ex. 200 ms)")
print("  com corte de motores / descida controlada. ESP-NOW (sem IP, sem ARQ) reduz overhead e latencia")
print("  versus UDP/IP; ainda assim, o radio 2.4 GHz compartilha espectro com o transmissor de video")
print("  e sofre com desvanecimento -> o failsafe NAO e' opcional.")
print("  Alcance: premissa de 50-300 m em linha de visada com antena de PCB; muito sensivel a orientacao")
print("  e a altura. NAO verificado nesta maquina (exige bancada/radio e campo).")

# ---------------------------------------------------------------- 9. ORCAMENTO
h("9. ORCAMENTO DE CORRENTE POR TRILHO")
t3v3 = 0.50 + 0.002 + 0.001 + 0.010 + 0.005
print(f"  3.3 V : ESP32-S3 pico WiFi TX 0.50 A + IMU 2 mA + baro 1 mA + LED 10 mA + margem 5 mA = {t3v3:.3f} A -> buck 1.5 A (3x)")
t12 = i12_total
print(f"  12 V  : 12 drivers x 2.5 mA + carga de gate = {t12:.3f} A -> buck 0.6 A")
t5 = b33["iin"] + 0.150 + 0.020
print(f"  5 V   : 3.3 V buck (corrente de ENTRADA) {b33['iin']*1000:.0f} mA + LDO analogico 150 mA + "
      f"USB/aux 20 mA = {t5:.3f} A -> buck 2.0 A")
print(f"  VBAT  : motores {itot_cont:.0f} A continuo / {itot_pk:.0f} A pico + {0.05+0.10+0.15:.2f} A dos conversores")
print(f"  Total de conversao (perdas ~10%): {b12['iin']*12+b5['iin']*5+b33['iin']*5:.2f} W de entrada nos bucks")

# ---------------------------------------------------------------- JSON
res = dict(premissas=P, tensoes=dict(vmax=Vmax, vnom=Vnom, vmin=Vmin),
           i_pico_total=itot_pk, i_cont_total=itot_cont, i_hover=i_hover,
           p_hover=p_hover, p_sw_total=Psw_fet*24,
           p_cond_total=24*(irms_fet(30)**2*P["P05_rds_on"]),
           i12=t12, i33=t3v3, i5=t5,
           bucks=dict(b12=b12, b5=b5, b33=b33))
with open("/opt/jupyter/work/drone/fase0_especificacao/dimensionamento_fase0.json", "w") as f:
    json.dump(res, f, indent=2)
print("\n[JSON salvo em dimensionamento_fase0.json]")
