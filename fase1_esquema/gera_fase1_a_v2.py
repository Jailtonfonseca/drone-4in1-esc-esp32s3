#!/usr/bin/env python3
"""FASE 1 v2 - esquemas com geometria planejada.
Regra verificada: posicao_absoluta_do_pino = ponto_de_colocacao + offset_local (anchors),
com slots de IcPin contando DE BAIXO PARA CIMA.
Saidas em /opt/jupyter/work/drone/fase1_esquema/
"""
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm

D = "/opt/jupyter/work/drone/fase1_esquema/"
d = None

def novo(unit=0.75, fs=9):
    global d
    d = schemdraw.Drawing(show=False); d.config(unit=unit, fontsize=fs, lw=1.2)

def W(*pts, color='black', lw=1.2):
    global d
    for a, b in zip(pts[:-1], pts[1:]):
        d += elm.Line().at(a).to(b).color(color).linewidth(lw)

def T(x, y, txt, fs=8, color='black'):
    global d
    d += elm.Label().at((x, y)).label(txt, fontsize=fs, color=color)

def A(el, x0, y0, name):
    o = el.anchors[name]; return (x0 + o[0], y0 + o[1])

def GND(p):
    global d
    d += elm.Ground().at(p)

# ========================================================= FIG 1: ENTRADA
def fig_entrada():
    global d
    novo()
    T(8.0, 10.5, "BLOCO 1 - ENTRADA, PROTECAO, BANCO DE ENTRADA E SENSE DE VBAT", 12)
    jx, jy = 0.4, 7.4
    j1 = elm.Ic(pins=[elm.IcPin(name='+', side='right', slot='3/3', pin='1'),
                      elm.IcPin(name='-', side='right', slot='1/3', pin='2')],
                w=2.2, h=1.8, label='J1\nXT60\nAMASS_XT60-F').at((jx, jy))
    d += j1
    jp = A(j1, jx, jy, '+'); jm = A(j1, jx, jy, '-')
    W(jm, (jm[0] + 0.6, jm[1])); GND((jm[0] + 0.6, jm[1]))
    W(jp, (jp[0] + 0.7, jp[1]))
    d += elm.Fuse().at((jp[0] + 0.7, jp[1])).to((jp[0] + 2.2, jp[1]))
    T(jp[0] + 1.45, jp[1] + 0.6, 'F1 30 A  Fuse_1206 (*)', 7.5)
    na = (jp[0] + 3.1, jp[1])
    W((jp[0] + 2.2, jp[1]), na); d += elm.Dot().at(na)
    T(na[0] - 1.05, na[1] - 1.05, 'D1\nTVS\n38 V\nD_SMB', 7.5)
    W(na, (na[0], na[1] - 7.0))
    xq, yq = na[0] + 1.2, na[1]
    W(na, (xq, yq))
    q1 = elm.PFet().at((xq, yq)); d += q1
    T(xq + 2.3, yq + 1.35, 'Q1  P-FET anti-inversao\nVds >= 30 V / Rds < 10 mOhm  TO-252-2_TabPin1', 7.5)
    gq = A(q1, xq, yq, 'gate'); sq = A(q1, xq, yq, 'source')
    W(gq, (gq[0] + 0.5, gq[1]))
    d += elm.Resistor().at((gq[0] + 0.5, gq[1])).down().length(1.3)
    T(gq[0] + 0.75, gq[1] - 0.65, 'R1\n10 k\nR_0603', 7)
    GND((gq[0] + 0.5, gq[1] - 1.3))
    yr = yq - 1.8
    W(sq, (sq[0], yr))
    T(10.0, yr + 0.8, 'VBAT   18,0 - 25,2 V   (min 3,30 V/celula)', 10.5, '#8c2f2f')
    W((sq[0], yr), (16.6, yr), color='#8c2f2f', lw=2)
    yg = yr - 2.2
    W((na[0], yr), (na[0], yg))
    for i in range(6):
        xx = 7.0 + 0.95 * i
        W((xx, yr), (xx, yr - 0.3))
        d += elm.Capacitor2().at((xx, yr - 0.3)).down().length(1.0)
        W((xx, yr - 1.3), (xx, yg))
    W((na[0], yg), (14.2, yg), lw=1.6)
    GND((9.0, yg))
    T(10.4, yg - 0.85, 'C1..C6: 6x 470 uF / 35 V polimero low-ESR (CP_Elec_8x10)', 8)
    for xx in (13.2, 13.8):
        W((xx, yr), (xx, yr - 0.3))
        d += elm.Capacitor().at((xx, yr - 0.3)).down().length(1.0)
        W((xx, yr - 1.3), (xx, yg))
    T(15.2, yr - 1.35, 'C7 10 uF/50 V X7R (C_1206)\nC8 100 nF/50 V X7R (C_0402)\ncolados a cada par de MOSFETs', 7.5)
    d += elm.Dot().at((15.4, yr))
    W((15.4, yr), (16.0, yr))
    d += elm.Resistor().at((16.0, yr)).to((17.2, yr))
    T(16.6, yr + 0.75, 'R3 100 k 1%\nR_0603', 7.5)
    d += elm.Dot().at((17.2, yr))
    W((17.2, yr), (18.0, yr))
    T(18.6, yr + 0.5, 'VBAT_SENSE\n-> GPIO1 (ADC1)\nfc = 132 Hz', 8)
    d += elm.Resistor().at((17.6, yr)).down().length(1.6)
    T(17.85, yr - 0.85, 'R4\n13,7 k 1%', 7.5)
    GND((17.6, yr - 1.6))
    d += elm.Capacitor().at((19.0, yr)).down().length(1.6)
    T(19.25, yr - 0.85, 'C9\n100 nF', 7.5)
    GND((19.0, yr - 1.6))
    T(9.8, 2.6, 'Divisor 100k/13,7k: 25,2 V -> 3,036 V (5,2 % do fundo) ; 6,7 mV/LSB ; erro +-2 % (R 1 %).', 8.2)
    T(9.8, 1.9, 'Modelo de ripple do banco (Fase 0): 1140 mV pk-pk a 30 A de pico (ESR 15 mOhm): quem manda e ESR/ESL,\n'
                'nao os uF. Sem cap local: L=100 nH, di=30 A, dt=50 ns -> 60 V (mata o MOSFET de 40 V).', 8.2)
    T(9.8, 0.7, '(*) F1: fusivel recomendado (a Fase 0 deixou como opcional).  Alternativa: e-fuse com CI + Rsense.', 8.2)
    d.save(D + "esq1_entrada_protecao.png")

# ========================================================= BUCKS (2,3,4)
def buck(nome, titulo, unome, vin_txt, vout_txt, Lval, Rtop, Rbot, extra):
    global d
    novo()
    T(7.6, 9.4, titulo, 12)
    ax, ay = 5.5, 4.2
    u = elm.Ic(pins=[elm.IcPin(name='VIN', side='left', slot='5/5', pin='1'),
                     elm.IcPin(name='EN',  side='left', slot='3/5', pin='2'),
                     elm.IcPin(name='FB',  side='left', slot='1/5', pin='3'),
                     elm.IcPin(name='SW',  side='right', slot='3/4', pin='4'),
                     elm.IcPin(name='BOOT',side='right', slot='1/4', pin='5'),
                     elm.IcPin(name='GND', side='bottom', pin='6')],
                w=3.8, h=3.4, label=' ').at((ax, ay))
    d += u
    pV = A(u, ax, ay, 'VIN'); pE = A(u, ax, ay, 'EN'); pF = A(u, ax, ay, 'FB')
    pS = A(u, ax, ay, 'SW');  pB = A(u, ax, ay, 'BOOT'); pG = A(u, ax, ay, 'GND')
    T(6.75, pV[1] + 0.95, f'{unome}  BUCK SINCRONO  500 kHz   Vin >= 30 V   [N/D offline]', 8.5)
    # --- entrada
    n1 = (2.0, pV[1])
    W(pV, n1); d += elm.Dot().at(n1)
    T(2.0, pV[1] + 0.55, vin_txt, 9, '#8c2f2f')
    d += elm.Capacitor().at(n1).down().length(1.2)
    T(1.05, n1[1] - 0.6, 'Cin\n4,7 uF/50 V\nC_1206', 7)
    GND((2.0, n1[1] - 1.2))
    # --- enable
    W(pE, (pE[0] - 0.6, pE[1]))
    d += elm.Resistor().at((pE[0] - 0.6, pE[1])).to((pE[0] - 0.6, pV[1]))
    T(pE[0] - 0.35, (pE[1] + pV[1]) / 2 + 0.15, 'Ren\n100 k', 7)
    W((pE[0] - 0.6, pV[1]), n1)
    # --- saida
    W(pS, (pS[0] + 0.7, pS[1]))
    d += elm.Inductor2().at((pS[0] + 0.7, pS[1])).to((pS[0] + 2.9, pS[1]))
    T(pS[0] + 1.8, pS[1] + 0.6, Lval, 8)
    vo = (pS[0] + 2.9, pS[1]); d += elm.Dot().at(vo)
    W(vo, (vo[0] + 0.6, vo[1]))
    T(vo[0] + 1.5, vo[1] + 0.75, vout_txt, 10, '#8c2f2f')
    for xx in (vo[0] + 0.4, vo[0] + 1.0):
        d += elm.Capacitor().at((xx, vo[1])).down().length(1.2)
        GND((xx, vo[1] - 1.2))
    T(vo[0] + 2.15, vo[1] - 1.35, 'Cout\n2x 22 uF\nC_1210', 7)
    # --- divisor de realimentacao
    W(vo, (vo[0], vo[1] - 0.5))
    d += elm.Resistor().at((vo[0], vo[1] - 0.5)).down().length(1.5)
    T(vo[0] - 1.75, vo[1] - 1.05, f'Rtop {Rtop}', 7.5)
    tap = (vo[0], vo[1] - 2.0); d += elm.Dot().at(tap)
    d += elm.Resistor().at(tap).down().length(1.5)
    T(vo[0] + 0.35, vo[1] - 2.85, f'Rbot {Rbot}', 7.5)
    GND((vo[0], vo[1] - 3.5))
    tb = (vo[0] - 0.9, tap[1])
    W(tap, tb, (tb[0], pF[1] - 1.4), (pF[0] - 0.6, pF[1] - 1.4), (pF[0] - 0.6, pF[1]), pF)
    T(pF[0] - 1.9, pF[1] - 0.9, 'FB', 7)
    # --- bootstrap
    W(pB, (pB[0] + 0.5, pB[1]))
    d += elm.Capacitor().at((pB[0] + 0.5, pB[1])).to((pB[0] + 0.5, pS[1]))
    T(10.0, pS[1] - 0.7, 'Cboot\n100 nF', 7)
    # --- gnd do CI
    W(pG, (pG[0], pG[1] - 0.6)); GND((pG[0], pG[1] - 0.6))
    T(7.6, 1.5, extra, 8.2)
    d.save(D + nome)

fig_entrada()
buck("esq2_buck12v.png", "BLOCO 2 - BUCK 12 V / 0,60 A  (alimenta os 12 gate drivers)", "U1",
     'VBAT\n18,0-25,2 V', '+12 V\n0,60 A', 'L 89 uH\nI_sat >= 1,2 A\nL_12x12mm_H6mm', '100 k 1%', '7,15 k 1%',
     'D = Vout/Vin = 0,606 (max) ; di_L = 30 % x 0,60 A = 0,18 A pk-pk ; L = (Vin-Vout)*D/(0,30*Iout*fsw) = 88,9 uH -> 89 uH (E12).\n'
     'Cout >= 3,7 uF -> 2x22 uF (limite real e ESR).  FB: Vout = Vref x (1+Rtop/Rbot) = 0,8 x (1+100/7,15) = 11,99 V [Vref 0,8 V PRESUMIDO].\n'
     'Iin media = Pout/(Vin*0,90) = 404 mA @19,8 V.  fsw 500 kHz [PREMISSA P-08].  CI exato: [N/D offline].')
buck("esq3_buck5v.png", "BLOCO 3 - BUCK 5 V / 2,00 A  (entrada do buck 3,3 V, do LDO_A e auxiliares)", "U2",
     '12 V\n0,60 A', '+5 V\n2,00 A', 'L 17 uH\nI_sat >= 3 A\nL_Bourns_SRR1210A', '100 k 1%', '19,1 k 1%',
     'D = 5/12 = 0,417 ; di_L = 30 % x 2,0 A = 0,60 A pk-pk ; L(30 %) = 9,7 uH -> adotado 17 uH (ripple 17 %, decidido na Fase 0).\n'
     'Cout >= 6,0 uF -> 2x22 uF.  FB: Vout = 0,8 x (1+100/19,1) = 4,99 V.\n'
     'Carga: buck 3,3 V (1,16 A) + LDO_A (0,15 A) + USB/aux (0,02 A) = 1,33 A -> folga 1,5x.')
buck("esq4_buck3v3.png", "BLOCO 4 - BUCK 3,3 V / 1,50 A  (ESP32-S3, IMU, barometro)", "U3",
     '5 V\n2,00 A', '+3,3 V\n1,50 A', 'L 5 uH\nI_sat >= 3 A\nL_Bourns_SRR1210A', '100 k 1%', '32,4 k 1%',
     'D = 3,3/5 = 0,66 ; di_L = 30 % x 1,5 A = 0,45 A pk-pk ; L(30 %) = 5,2 uH -> 5 uH.\n'
     'Cout >= 3,4 uF -> 2x22 uF.  FB: Vout = 0,8 x (1+100/32,4) = 3,27 V.\n'
     'Carga: ESP32-S3 pico WiFi TX 0,50 A + IMU 2 mA + baro 1 mA + LED 10 mA + margem = 0,518 A -> folga 2,9x.')
print("figs 1-4 (v2) geradas")
