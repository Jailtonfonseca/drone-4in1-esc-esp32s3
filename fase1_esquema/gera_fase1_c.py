#!/usr/bin/env python3
"""FASE 1 v3: fig 1 (entrada, P-FET horizontal) e fig 5 (half-bridge com driver desenhado
como retangulo + stubs de pino controlados por mim). Corrige tambem o divisor de BEMF,
que deve ser referenciado ao GND (nao a fase)."""
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

def GND(p):
    global d
    d += elm.Ground().at(p)

def A(el, x0, y0, name):
    o = el.anchors[name]; return (x0 + o[0], y0 + o[1])

# ============================================================ FIG 1 v3: ENTRADA
def entrada():
    global d
    novo()
    T(9.0, 11.6, "BLOCO 1 - ENTRADA, PROTECAO, BANCO DE ENTRADA E SENSE DE VBAT", 12)
    yp = 9.4
    j1 = elm.Ic(pins=[elm.IcPin(name='+', side='right', slot='3/3', pin='1'),
                      elm.IcPin(name='-', side='right', slot='1/3', pin='2')],
                w=2.2, h=1.8, label='J1\nXT60\nAMASS_XT60-F').at((0.4, 7.55))
    d += j1
    jp = A(j1, 0.4, 7.55, '+'); jm = A(j1, 0.4, 7.55, '-')
    W(jm, (jm[0] + 0.7, jm[1])); GND((jm[0] + 0.7, jm[1]))
    W(jp, (jp[0] + 0.6, jp[1]))
    d += elm.Fuse().at((jp[0] + 0.6, yp)).to((jp[0] + 2.1, yp))
    T(jp[0] + 1.0, yp + 0.55, 'F1 30 A\nFuse_1206 (*)', 7.5)
    na = (jp[0] + 3.0, yp)
    W((jp[0] + 2.1, yp), na); d += elm.Dot().at(na)
    W(na, (na[0], na[1] - 0.6))
    d += elm.Zener().at((na[0], na[1] - 0.6)).down().length(1.2)
    T(na[0] - 1.05, yp - 0.95, 'D1\nTVS unidir.\n38 V (SMBJ33A)\nD_SMB', 7.5)
    W((na[0], na[1] - 1.8), (na[0], 4.6))
    xq = na[0] + 1.4
    W(na, (xq, yp))
    q1 = elm.PFet2().right().at((xq, yp)); d += q1
    T(xq + 2.0, yp + 1.95, 'Q1  P-FET anti-inversao: D = bateria | S = carga | G = GND\nVds >= 30 V / Rds < 10 mOhm / TO-252-2_TabPin1', 7.5)
    gq = A(q1, xq, yp, 'gate'); sq = A(q1, xq, yp, 'source')
    W(gq, (gq[0], gq[1] + 0.4))
    d += elm.Resistor().at((gq[0], gq[1] + 0.4)).right().length(1.2)
    T(gq[0] + 0.9, gq[1] + 0.8, 'R1\n10 k\nR_0603', 7)
    W((gq[0] + 1.2, gq[1] + 0.4), (gq[0] + 1.2, yp + 0.9))
    GND((gq[0] + 1.2, yp + 0.9))
    yr = yp - 2.0
    W(sq, (sq[0], yr))
    T(11.0, yr + 0.6, 'VBAT   18,0 - 25,2 V   (3,30 V/celula no minimo)', 10.5, '#8c2f2f')
    W((sq[0], yr), (16.4, yr), color='#8c2f2f', lw=2)
    yg = yr - 2.4
    for i in range(6):
        xx = 9.4 + 0.95 * i
        W((xx, yr), (xx, yr - 0.3))
        d += elm.Capacitor2().at((xx, yr - 0.3)).down().length(1.0)
        W((xx, yr - 1.3), (xx, yg))
    W((na[0], yg), (14.2, yg), lw=1.6)
    GND((11.5, yg))
    T(11.0, yg - 0.9, 'C1..C6: 6x 470 uF / 35 V polimero low-ESR (CP_Elec_8x10)', 8)
    for xx in (13.0, 13.6):
        W((xx, yr), (xx, yr - 0.3))
        d += elm.Capacitor().at((xx, yr - 0.3)).down().length(1.0)
        W((xx, yr - 1.3), (xx, yg))
    T(15.9, yr - 1.5, 'C7 10 uF/50 V X7R (C_1206)\nC8 100 nF/50 V X7R (C_0402)\ncolados a cada par de MOSFETs', 7.5)
    d += elm.Dot().at((15.2, yr))
    W((15.2, yr), (15.8, yr))
    d += elm.Resistor().at((15.8, yr)).to((17.0, yr))
    T(16.4, yr + 0.75, 'R3 100 k 1%\nR_0603', 7.5)
    d += elm.Dot().at((17.0, yr))
    W((17.0, yr), (17.7, yr))
    T(18.3, yr + 0.55, 'VBAT_SENSE\n-> GPIO1 (ADC1)\nfc = 132 Hz', 8)
    d += elm.Resistor().at((17.4, yr)).down().length(1.6)
    T(17.65, yr - 0.85, 'R4\n13,7 k 1%', 7.5)
    GND((17.4, yr - 1.6))
    d += elm.Capacitor().at((18.8, yr)).down().length(1.6)
    T(19.05, yr - 0.85, 'C9\n100 nF', 7.5)
    GND((18.8, yr - 1.6))
    T(11.0, 3.3, 'Divisor 100k/13,7k: 25,2 V -> 3,036 V (5,2 % do fundo do ADC) ; 6,7 mV/LSB ; erro +-2 % com R de 1 %.', 8.2)
    T(11.0, 2.5, 'Banco de entrada (modelo da Fase 0): 1140 mV pk-pk a 30 A de pico (C 470 uF, ESR 15 mOhm).  Quem dimensiona e ESR/ESL,', 8.2)
    T(11.0, 2.0, 'nao os microfarads.  Sem cap local: L=100 nH, di=30 A, dt=50 ns -> 60 V (mata o MOSFET de 40 V).', 8.2)
    T(11.0, 1.1, '(*) F1 recomendado (na Fase 0 ficou opcional).  Alternativa: e-fuse com CI + Rsense.', 8.2)
    d.save(D + "esq1_entrada_protecao.png")

# ============================================================ FIG 5 v3: HALF-BRIDGE
def esc_detalhe():
    global d
    novo()
    T(8.2, 12.0, "BLOCO 5 - ESC TRIFASICO: DETALHE DE 1 HALF-BRIDGE (este bloco se repete 12x)", 11.5)
    yp = 6.5
    xf = 7.0
    j2 = elm.Ic(pins=[elm.IcPin(name='U', side='right', slot='1/1', pin='1')],
                w=1.7, h=1.3, label='J2\nMR30\nfase U').at((0.4, yp))
    d += j2
    pj = A(j2, 0.4, yp, 'U')
    W(pj, (6.4, pj[1]))
    T(3.0, yp - 0.5, 'fase U -> motor', 8)
    # ---- MOSFETs
    hs = elm.NFet().at((xf, 8.0)); d += hs
    ls = elm.NFet().at((xf, 5.5)); d += ls
    T(6.35, 8.35, 'Q1A', 8)
    T(6.35, 4.65, 'Q1B', 8)
    W((xf, 9.9), (xf, 8.0), color='#8c2f2f')
    W((xf, 9.9), (11.4, 9.9), color='#8c2f2f', lw=1.8)
    T(8.6, 10.3, 'VBAT  18,0-25,2 V', 9.5, '#8c2f2f')
    W((xf, 6.5), (xf, 5.5)); d += elm.Dot().at((xf, 6.5))
    # ---- shunt + GND
    d += elm.Resistor().at((xf, 3.9)).down().length(1.3)
    T(4.0, 2.95, 'Rsh 0,5 mOhm 2 W\n2512 manganina\n112 mW continuo / 450 mW pico', 7)
    W((xf, 2.6), (xf, 1.5))
    W((xf, 1.5), (14.2, 1.5), lw=1.5)
    GND((10.0, 1.5))
    T(12.0, 1.05, 'GND (plano da camada 2)', 8)
    # ---- divisor de BEMF (referenciado ao GND, nao a fase)
    d += elm.Dot().at((3.0, yp))
    W((3.0, yp), (3.0, yp + 3.3))
    d += elm.Resistor().at((3.0, yp + 3.3)).right().length(1.5)
    T(3.75, yp + 3.7, 'R8 8,2 k 1%', 7)
    W((4.5, yp + 3.3), (4.9, yp + 3.3)); d += elm.Dot().at((4.7, yp + 3.3))
    d += elm.Resistor().at((4.7, yp + 3.3)).down().length(1.5)
    T(4.95, yp + 2.55, 'R9\n1,0 k 1%', 7)
    GND((4.7, yp + 1.8))
    W((4.9, yp + 3.3), (5.5, yp + 3.3))
    d += elm.Capacitor().at((5.5, yp + 3.3)).down().length(1.0)
    T(5.75, yp + 2.9, '1 nF', 7)
    GND((5.5, yp + 2.3))
    T(3.4, yp + 5.0, 'BEMF_U -> ADC externo SPI: 25,2 V -> 2,74 V ; fc 178 kHz ; clamp 3,3 V', 8)
    # ---- gate driver (retangulo + stubs)
    x0, x1, y0, y1 = 12.0, 15.0, 5.0, 9.4
    W((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))
    T(13.5, 7.2, 'U1\nGATE DRIVER\nhalf-bridge\nsingle-input\ndead-time 520 ns\nbootstr. 12 V\nSOIC-8\n[N/D offline]', 7.5)
    pins = {'HO': (x0, 8.6, 'left'), 'VS': (x0, 7.2, 'left'), 'LO': (x0, 5.8, 'left'),
            'VB': (13.5, y1, 'top'), 'COM': (13.5, y0, 'bottom'),
            'VCC': (x1, 8.2, 'right'), 'IN': (x1, 5.8, 'right')}
    for p, (px, py, lado) in pins.items():
        if lado == 'left':
            W((px - 0.45, py), (px, py)); T(px + 0.35, py + 0.22, p, 7.5)
        elif lado == 'right':
            W((px, py), (px + 0.45, py)); T(px - 0.95, py + 0.22, p, 7.5)
        elif lado == 'top':
            W((px, py), (px, py + 0.45)); T(px + 0.45, py + 0.25, p, 7.5)
        else:
            W((px, py), (px, py - 0.45)); T(px + 0.45, py - 0.3, p, 7.5)
    ygh, ygl = 8.0 - 0.75, 5.5 - 0.75
    W((x0 - 0.45, 8.6), (10.9, 8.6), (10.9, ygh))
    d += elm.Resistor().at((10.9, ygh)).to((9.5, ygh))
    T(10.2, ygh + 0.35, 'Rg 10 ohm\nR_0805', 7)
    W((9.5, ygh), (xf + 1.37, ygh), color='#1e5c33')
    W((x0 - 0.45, 5.8), (10.2, 5.8), (10.2, ygl))
    d += elm.Resistor().at((10.2, ygl)).to((9.0, ygl))
    T(9.6, ygl - 0.6, 'Rg 10 ohm\nR_0805', 7)
    W((9.0, ygl), (xf + 1.37, ygl), color='#1e5c33')
    W((x0 - 0.45, 7.2), (11.4, 7.2), (11.4, yp), (xf, yp), color='#555', lw=1.5)
    T(11.35, 4.25, 'VS: referencia\nflutuante\n(acompanha a fase)', 7)
    W((13.5, y1), (13.5, 10.4), (8.6, 10.4), (8.6, yp), (xf, yp))
    d += elm.Capacitor().at((8.6, 10.3)).down().length(1.1)
    T(7.0, 9.85, 'Cboot\n1 uF/25 V\nX7R C_0805', 7)
    W((11.2, 10.4), (12.4, 10.4))
    d += elm.Diode().at((11.2, 10.4)).left().length(1.1)
    T(11.6, 10.85, 'Db 100 V/1 A SOD-123  (carrega o bootstrap de +12 V)', 7)
    W((12.4, 10.4), (16.0, 10.4), (16.0, 8.2), (x1 + 0.45, 8.2), color='#8c2f2f')
    T(15.7, 9.6, '+12 V', 9, '#8c2f2f')
    W((x1 + 0.45, 5.8), (16.6, 5.8))
    T(16.75, 6.15, 'PWM_U\n(MCPWM ou\nLEDC), 20 kHz', 7.5)
    W((13.5, y0 - 0.45), (13.5, 1.5))
    # ---- amplificador de corrente (CSA) sobre o shunt
    cx0, cx1, cy0, cy1 = 10.6, 13.4, 1.9, 3.9
    W((cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1), (cx0, cy0))
    T(12.0, 2.75, 'U2  CSA\nganho 50\nSOIC-8\n[N/D offline]', 7)
    W((xf, 3.9), (10.1, 3.9), (10.1, 3.4), (cx0, 3.4)); T(10.35, 3.75, 'IN+', 6.5)
    W((xf, 2.6), (10.35, 2.6), (10.35, 2.3), (cx0, 2.3)); T(10.55, 2.8, 'IN-', 6.5)
    W((cx1, 2.9), (14.2, 2.9))
    T(14.35, 3.2, 'I_FASE_U -> ADC externo SPI\n0,5 mOhm x 50 = 25 mV/A ; 30 A -> 0,75 V', 7.5)
    W((12.0, cy1), (12.0, 4.4)); T(12.15, 4.5, 'V+ = 3,3 V', 6.5)
    W((12.0, cy0), (12.0, 1.5))
    T(4.0, 0.65, 'O driver single-input gera a saida complementar COM dead-time de hardware (520 ns): por isso basta\n'
                 '1 pino PWM por half-bridge (3 por motor, 12 no total), que e o que cabe no ESP32-S3.', 8.2)
    d.save(D + "esq5_esc_halfbridge.png")

entrada()
esc_detalhe()
print("fig 1 v3 e fig 5 v3 geradas")
