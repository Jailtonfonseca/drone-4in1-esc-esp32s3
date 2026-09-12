#!/usr/bin/env python3
"""FASE 1 - gerador de esquemas. Metodo: TODO elemento e posicionado em coordenada
absoluta (.at/.to) e os pinos de CI/FET sao calculados como at + offset_local
(comportamento verificado nesta maquina com dots de conferencia).
Saidas: esq1..esq8 .png em fase1_esquema/
"""
import os
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm

D = os.path.dirname(os.path.abspath(__file__)) + "/"
d = None

def novo(unit=0.75, fs=9):
    global d
    d = schemdraw.Drawing(show=False)
    d.config(unit=unit, fontsize=fs, lw=1.2)

def W(*pts, color='black', lw=1.2):
    global d
    for a, b in zip(pts[:-1], pts[1:]):
        d += elm.Line().at(a).to(b).color(color).linewidth(lw)

def T(x, y, txt, fs=8, color='black'):
    global d
    d += elm.Label().at((x, y)).label(txt, fontsize=fs, color=color)

def A(el, x0, y0, name):
    o = el.anchors[name]
    return (x0 + o[0], y0 + o[1])

def GND(p):
    global d
    d += elm.Ground().at(p)

# =============================================================== FIG 1: ENTRADA
novo()
T(7.0, 9.4, "BLOCO 1 - ENTRADA, PROTECAO, BANCO DE ENTRADA E SENSE DE VBAT", 12)
j1 = elm.Ic(pins=[elm.IcPin(name='+', side='right', slot='1/3', pin='1'),
                  elm.IcPin(name='-', side='right', slot='3/3', pin='2')],
            w=2.2, h=1.8, label='J1\nXT60\nAMASS_XT60-F').at((0.3, 6.2))
d += j1
jp = A(j1, 0.3, 6.2, '+'); jm = A(j1, 0.3, 6.2, '-')
W(jm, (jm[0] + 0.5, jm[1])); GND((jm[0] + 0.5, jm[1]))
W(jp, (jp[0] + 0.6, jp[1]))
d += elm.Fuse().at((jp[0] + 0.6, jp[1])).to((jp[0] + 2.1, jp[1]))
T(jp[0] + 1.35, jp[1] + 0.55, 'F1 30 A Fuse_1206 (*)', 7.5)
W((jp[0] + 2.1, jp[1]), (jp[0] + 3.0, jp[1]))
na = (jp[0] + 3.0, jp[1])
d += elm.Dot().at(na)
d += elm.Zener().at(na).down().length(1.7)
T(na[0] - 0.35, na[1] - 1.0, 'D1\nTVS 38 V\nD_SMB', 7.5)
GND((na[0], na[1] - 1.7))
W(na, (na[0] + 0.9, na[1]))
xa, ya = na[0] + 0.9, na[1]
q1 = elm.PFet().at((xa, ya)); d += q1
T(xa + 1.5, ya + 1.05, 'Q1 P-FET  Vds>=30 V / Rds<10 mOhm / TO-252-2_TabPin1', 7.5)
gq = A(q1, xa, ya, 'gate'); sq = A(q1, xa, ya, 'source')
W(gq, (gq[0] + 0.6, gq[1]))
d += elm.Resistor().at((gq[0] + 0.6, gq[1])).down().length(1.4)
T(gq[0] + 0.85, gq[1] - 0.7, 'R1\n10 k\nR_0603', 7.5)
GND((gq[0] + 0.6, gq[1] - 1.4))
W(sq, (sq[0], sq[1] - 0.4), (sq[0] + 0.6, sq[1] - 0.4))
yr = sq[1] - 0.4
T(6.0, yr + 1.05, 'VBAT  18,0-25,2 V', 10.5, '#8c2f2f')
W((sq[0] + 0.6, yr), (13.6, yr), color='#8c2f2f', lw=2)
dt = ('Divisor 100k/13,7k -> 25,2 V = 3,036 V (5,2 %) ; 6,7 mV/LSB ; fc = 132 Hz.\n'
      'Modelo de ripple: 1140 mV pk-pk @30 A de pico (ESR 15 mOhm) - quem manda e ESR/ESL.\n'
      'Sem cap local: L=100 nH, di=30 A, dt=50 ns -> 60 V (mata MOSFET de 40 V): 100 nF+10 uF a <2 mm.\n'
      '(*) F1 recomendado (opcional no desenho da Fase 0). Alternativa: e-fuse com CI + Rsense.')
T(6.2, yr - 3.5, dt, 8.2)
for i in range(6):
    xx = 3.2 + 0.95 * i
    W((xx, yr), (xx, yr - 0.3))
    d += elm.Capacitor2().at((xx, yr - 0.3)).down().length(1.0)
    W((xx, yr - 1.3), (xx, yr - 2.0))
T(6.2, yr - 1.95, 'C1..C6: 6x 470 uF / 35 V polimero low-ESR  (CP_Elec_8x10)', 8)
W((3.2, yr - 2.0), (7.95, yr - 2.0))
GND((5.5, yr - 2.0))
for i, xx in enumerate([9.0, 9.6]):
    W((xx, yr), (xx, yr - 0.3))
    d += elm.Capacitor().at((xx, yr - 0.3)).down().length(1.0)
    W((xx, yr - 1.3), (xx, yr - 2.0))
    GND((xx, yr - 2.0))
T(9.35, yr - 2.65, 'C7 10 uF/50 V X7R (C_1206)  +  C8 100 nF/50 V X7R (C_0402)\ncolados ao par de MOSFETs', 8)
W((11.2, yr), (13.6, yr), color='#8c2f2f', lw=2)
d += elm.Dot().at((11.2, yr))
W((11.7, yr), (12.3, yr))
d += elm.Resistor().at((12.3, yr)).to((13.4, yr))
T(12.85, yr + 0.5, 'R3 100 k 1%\nR_0603', 7.5)
d += elm.Dot().at((13.4, yr))
W((13.4, yr), (14.0, yr))
T(14.6, yr + 0.45, 'VBAT_SENSE\n-> GPIO1 (ADC1)', 8)
d += elm.Resistor().at((13.9, yr)).down().length(1.6)
T(14.15, yr - 0.85, 'R4 13,7 k 1%', 7.5)
GND((13.9, yr - 1.6))
d += elm.Capacitor().at((15.3, yr)).down().length(1.6)
T(15.55, yr - 0.85, 'C9 100 nF', 7.5)
GND((15.3, yr - 1.6))
T(2.0, 1.2, 'Nota: D1 e Q1 sao a protecao de entrada (sobretensao + inversao de polaridade).\n'
            'Q1 conduz com Vgs<0 (gate em GND). Bateria invertida -> diodo de corpo corta.', 8.2)
d.save(D + "esq1_entrada_protecao.png")

# =============================================================== FIG 2: BUCK 12 V
def buck(nome, titulo, vin_txt, vout_txt, iout_txt, Lval, fsw_txt, Rtop, Rbot, extra="", fs_note=8.2):
    global d
    novo()
    T(7.0, 9.4, titulo, 12)
    ax, ay = 5.6, 5.6
    u = elm.Ic(pins=[elm.IcPin(name='VIN', side='left', slot='1/5', pin='1'),
                     elm.IcPin(name='EN',  side='left', slot='3/5', pin='2'),
                     elm.IcPin(name='FB',  side='left', slot='5/5', pin='3'),
                     elm.IcPin(name='SW',  side='right', slot='1/4', pin='4'),
                     elm.IcPin(name='BOOT',side='right', slot='3/4', pin='5'),
                     elm.IcPin(name='GND', side='bottom', pin='6')],
                w=3.8, h=3.4, label='U\nBUCK SINCRONO\nVin >= 30 V\nessincrono\n[N/D offline]').at((ax, ay))
    d += u
    pV = A(u, ax, ay, 'VIN'); pE = A(u, ax, ay, 'EN'); pF = A(u, ax, ay, 'FB')
    pS = A(u, ax, ay, 'SW');  pB = A(u, ax, ay, 'BOOT'); pG = A(u, ax, ay, 'GND')
    # entrada
    n1 = (pV[0] - 1.4, pV[1])
    W(pV, n1); d += elm.Dot().at(n1)
    W(n1, (n1[0] - 0.5, n1[1]))
    T(n1[0] - 0.6, n1[1] + 0.45, vin_txt, 9, '#8c2f2f')
    d += elm.Capacitor().at(n1).down().length(1.3)
    T(n1[0] + 0.25, n1[1] - 0.7, 'Cin\n4,7 uF/50 V\nC_1206', 7.5)
    GND((n1[0], n1[1] - 1.3))
    # EN
    W(pE, (pE[0] - 0.5, pE[1]))
    d += elm.Resistor().at((pE[0] - 0.5, pE[1])).to((pE[0] - 1.8, pE[1]))
    T(pE[0] - 1.15, pE[1] + 0.45, 'Ren\n100 k\nR_0603', 7)
    W((pE[0] - 1.8, pE[1]), (pE[0] - 1.8, n1[1]), (n1[0], n1[1]))
    # saida
    W(pS, (pS[0] + 0.8, pS[1]))
    d += elm.Inductor2().at((pS[0] + 0.8, pS[1])).to((pS[0] + 3.0, pS[1]))
    T(pS[0] + 1.9, pS[1] + 0.55, f'L {Lval}', 8.5)
    vo = (pS[0] + 3.0, pS[1])
    W(vo, (vo[0] + 1.4, vo[1]))
    T(vo[0] + 1.6, vo[1] + 0.45, vout_txt, 10, '#8c2f2f')
    d += elm.Dot().at(vo)
    for i, xx in enumerate([vo[0] + 0.5, vo[0] + 1.15]):
        d += elm.Capacitor().at((xx, vo[1])).down().length(1.3)
        GND((xx, vo[1] - 1.3))
    T(vo[0] + 0.8, vo[1] - 1.75, 'Cout\n2x 22 uF/25 V\nC_1210', 7.5)
    # divisor de realimentacao
    W(vo, (vo[0], vo[1] - 0.9))
    d += elm.Resistor().at((vo[0], vo[1] - 0.9)).down().length(1.5)
    T(vo[0] + 0.3, vo[1] - 1.65, f'Rtop {Rtop}', 7.5)
    fb = (vo[0], vo[1] - 2.4)
    d += elm.Dot().at(fb)
    d += elm.Resistor().at(fb).down().length(1.5)
    T(vo[0] + 0.3, vo[1] - 3.15, f'Rbot {Rbot}', 7.5)
    GND((vo[0], vo[1] - 3.9))
    W(fb, (pF[0] - 1.6, fb[1]), (pF[0] - 1.6, pF[1]), pF)
    T(pF[0] - 1.5, pF[1] - 0.55, 'FB', 7)
    # bootstrap
    W(pB, (pB[0] + 0.5, pB[1]))
    d += elm.Capacitor().at((pB[0] + 0.5, pB[1])).down().length(pB[1] - pS[1])
    T(pB[0] + 0.8, (pB[1] + pS[1]) / 2 + 0.15, 'Cboot\n100 nF\nC_0603', 7.5)
    # gnd do CI
    W(pG, (pG[0], pG[1] - 0.8)); GND((pG[0], pG[1] - 0.8))
    T(2.6, 0.9, extra, fs_note)
    d.save(D + nome)

buck("esq2_buck12v.png", "BLOCO 2 - BUCK 12 V / 0,60 A  (12 gate drivers)", "VBAT\n18,0-25,2 V",
     '+12 V\n0,60 A', '0,60 A', '89 uH\nI_sat>=1,2 A\nL_12x12mm_H6mm', 'fsw 500 kHz',
     '100 k 1%', '7,15 k 1%',
     'fsw = 500 kHz. D = Vout/Vin = 0,606 (max) ; di_L = 30 % de 0,60 A = 0,18 A pk-pk.\n'
     'L = (Vin-Vout)*D/(0,30*Iout*fsw) = 88,9 uH -> 89 uH (E12).  Cout >= 3,7 uF -> 2x22 uF (ESR).\n'
     'FB: Vout = Vref x (1+Rtop/Rbot) = 0,8 x (1+100/7,15) = 11,99 V   [Vref 0,8 V PRESUMIDO]\n'
     'Iin media = Pout/(Vin*0,90) = 404 mA @19,8 V.  Forma de onda critica por 30 A de pico (nao desenhada).')

# =============================================================== FIG 3: BUCK 5 V
buck("esq3_buck5v.png", "BLOCO 3 - BUCK 5 V / 2,00 A  (entrada do buck 3,3 V + LDO)", "12 V\n0,60 A",
     '+5 V\n2,00 A', '2,00 A', '17 uH\nI_sat>=3 A\nL_Bourns_SRR1210A', 'fsw 500 kHz',
     '100 k 1%', '19,1 k 1%',
     'fsw = 500 kHz. D = 5/12 = 0,417 ; di_L = 30 % de 2,0 A = 0,60 A pk-pk.\n'
     'L = (12-5)*0,417/(0,30*2,0*500k) = 9,72 uH no criterio de 30% -> a Fase 0 adotou 17 uH (ripple menor, 17 %).\n'
     'Cout >= 6,0 uF -> 2x22 uF.  FB: Vout = 0,8 x (1+100/19,1) = 4,99 V.\n'
     'Orcamento de carga: buck 3,3 V (1,16 A) + LDO_A (0,15 A) + USB/aux (0,02 A) = 1,33 A -> folga 1,5x.')

# =============================================================== FIG 4: BUCK 3,3 V + LDO
buck("esq4_buck3v3.png", "BLOCO 4 - BUCK 3,3 V / 1,50 A  (MCU, IMU, barometro)", "5 V\n2,00 A",
     '+3,3 V\n1,50 A', '1,50 A', '5 uH\nI_sat>=3 A\nL_Bourns_SRR1210A', 'fsw 500 kHz',
     '100 k 1%', '32,4 k 1%',
     'fsw = 500 kHz. D = 3,3/5 = 0,66 ; di_L = 30 % de 1,5 A = 0,45 A pk-pk. L = 5,2 uH -> 5 uH.\n'
     'Cout >= 3,4 uF -> 2x22 uF.  FB: Vout = 0,8 x (1+100/32,4) = 3,27 V.\n'
     'Carga: ESP32-S3 pico WiFi TX 0,50 A + IMU 2 mA + baro 1 mA + LED 10 mA + margem = 0,518 A (folga 2,9x).')
print("figs 1-4 geradas")
