#!/usr/bin/env python3
"""Fase 1 - esquemas por bloco (schemdraw headless)."""
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm

D = "/opt/jupyter/work/drone/fase1_esquema/"
def novo(unit=1.7, fs=9):
    d = schemdraw.Drawing(show=False)
    d.config(unit=unit, fontsize=fs, lw=1.3)
    return d

# ============================================================ FIG 1: ENTRADA
d = novo(unit=1.6)
d += elm.Label().at((6.0, 9.6)).label("BLOCO 1 - ENTRADA, PROTECAO E BANCO", fontsize=13)
j1 = elm.Ic(pins=[elm.IcPin(name='+', side='right', slot='1/3', pin='1'),
                  elm.IcPin(name='-', side='right', slot='3/3', pin='2')],
            w=1.8, h=1.7, label='J1 XT60\nAMASS_XT60-F').at((0.4, 6.3))
d += j1
d += elm.Line().at(j1.anchors['+']).right().length(0.7)
d += elm.Fuse().right().length(1.3).label('F1 30 A\nFuse_1206', loc='top', ofst=0.5)
d += elm.Line().right().length(0.5)
d += elm.Dot(); tv = d.here
d += elm.Zener().at(tv).down().length(1.6).label('D1 TVS\nclamp 38 V\nD_SMB', loc='left', fontsize=8)
d += elm.Ground()
d += elm.Line().at(tv).right().length(0.6)
q1 = elm.PFet().anchor('drain').at(d.here)
d += q1
d += elm.Label().at((5.6, 8.5)).label('Q1 P-FET  Vds>=30 V / Rds<10 mOhm\nTO-252-2_TabPin1 (anti-inversao)', fontsize=8.4)
d += elm.Line().at(q1.anchors['source']).right().length(0.8)
d += elm.Dot(); vs = d.here
d += elm.Line().at(q1.anchors['gate']).down().length(1.1)
d += elm.Resistor().down().length(1.3).label('R1 10 k\nR_0603', loc='right', fontsize=8)
d += elm.Ground()
d += elm.Label().at((5.9, 4.4)).label('Gate em GND -> Vgs<0 quando ha bateria.\nBateria invertida: diodo de corpo corta o caminho.', fontsize=7.8)
d += elm.Line().at(vs).right().length(0.9)
d += elm.Line().up().length(0.0)
rail = d.here
d += elm.Line().at((vs[0]+0.9, vs[1])).right().length(0.2)
d += elm.Line().up().length(9.6-vs[1])
d += elm.Line().right().length(9.0)
d += elm.Label().at((11.0, 9.85)).label('VBAT  18,0 - 25,2 V', fontsize=11, color='#8c2f2f')
xs = [9.2, 10.2, 11.2, 12.2, 13.2, 14.2]
for i, xx in enumerate(xs):
    d += elm.Line().at((xx, 9.6)).down().length(0.3)
    d += elm.Capacitor2().down().length(1.0).label(f'C{i+1}\n470 uF 35 V\nCP_Elec_8x10', loc='right', fontsize=7.2)
    d += elm.Line().down().length(0.3)
d += elm.Line().at((xs[0], 8.0)).right().length(xs[-1]-xs[0])
d += elm.Ground().at((xs[3], 8.0))
d += elm.Capacitor().at((15.2, 8.8)).down().length(1.5).label('C7\n10 uF/50 V\nC_1206', loc='right', fontsize=7.6)
d += elm.Ground().at((15.2, 7.3))
d += elm.Label().at((12.2, 6.6)).label(
    'Banco de entrada: 6x 470 uF + 10 uF + 100 nF por par de MOSFET.\n'
    'Ripple calculado: 1140 mV pk-pk com 30 A de pico (C=470 uF, ESR 15 mOhm).\n'
    'Sem cap local: L=100 nH, di=30 A, dt=50 ns -> 60 V (mata MOSFET de 40 V).', fontsize=8.2)
# VBAT sense
d += elm.Line().at((13.7, 9.6)).up().length(0.0)
d += elm.Line().at((14.7, 9.6)).right().length(1.4)
d += elm.Dot()
d += elm.Line().right().length(0.8)
d += elm.Resistor().right().length(1.7).label('R3 100 k 1%\nR_0603', loc='top', ofst=0.5, fontsize=8)
d += elm.Dot()
d += elm.Line().right().length(1.0)
d += elm.Label().at((20.6, 9.95)).label('VBAT_SENSE\n-> ADC1 GPIO1', fontsize=9)
d += elm.Resistor().at((19.6, 9.6)).down().length(1.7).label('R4\n13,7 k 1%', loc='right', fontsize=8)
d += elm.Ground()
d += elm.Capacitor().at((21.2, 9.6)).down().length(1.7).label('C9\n100 nF\nfc 132 Hz', loc='right', fontsize=7.6)
d += elm.Ground()
d += elm.Label().at((9.0, 1.6)).label(
    'Pegadas verificadas com ls em /usr/share/kicad/modules.  D1: SMBJ33A-class [N/D offline].\n'
    'Divisor VBAT 100k/13,7k -> 25,2 V = 3,036 V; resolucao 6,7 mV/LSB; erro +-2% (R 1%).', fontsize=8.4)
d.save(D + "esq1_entrada_protecao.png")

# ============================================================ FIG 2: BUCK 12 V
d = novo(unit=1.7)
d += elm.Label().at((6.5, 10.0)).label("BLOCO 2 - BUCK 12 V / 0,60 A (gate drivers)", fontsize=13)
u1 = elm.Ic(pins=[elm.IcPin(name='VIN', side='left', slot='1/5', pin='1'),
                  elm.IcPin(name='EN',  side='left', slot='3/5', pin='2'),
                  elm.IcPin(name='FB',  side='left', slot='5/5', pin='3'),
                  elm.IcPin(name='SW',  side='right', slot='1/4', pin='4'),
                  elm.IcPin(name='BOOT',side='right', slot='3/4', pin='5'),
                  elm.IcPin(name='GND', side='bottom', pin='6')],
            w=4.0, h=3.4,
            label='U1  BUCK SINCRONO\nVin >= 30 V / Iout 0,6 A\nfsw 500 kHz\n[N/D offline]').at((5.0, 6.2))
d += u1
d += elm.Line().at(u1.anchors['VIN']).left().length(1.5)
d += elm.Dot(); vin = d.here
d += elm.Line().at(vin).left().length(0.7)
d += elm.Label().at((1.9, 7.9)).label('VBAT\n18,0-25,2 V', fontsize=9, color='#8c2f2f')
d += elm.Capacitor().at((3.0, 7.6)).down().length(1.6).label('C10\n4,7 uF/50 V\nC_1206', loc='right', fontsize=7.6)
d += elm.Ground()
d += elm.Line().at(u1.anchors['EN']).left().length(1.0)
d += elm.Resistor().left().length(1.4).label('R7 100 k\nR_0603', loc='top', ofst=0.45, fontsize=8)
d += elm.Line().at(u1.anchors['SW']).right().length(0.8)
d += elm.Dot()
d += elm.Inductor2().right().length(2.4).label('L1  89 uH\nI_sat >= 1,2 A\nL_12x12mm_H6mm', loc='top', ofst=0.6, fontsize=9)
d += elm.Dot(); vout = d.here
d += elm.Line().right().length(0.9)
d += elm.Label().at((15.0, 7.6)).label('+12 V 0,60 A', fontsize=10, color='#8c2f2f')
for i, xx in enumerate([13.6, 14.3]):
    d += elm.Line().at((xx, 7.6)).down().length(0.0)
    d += elm.Capacitor().at((xx, 7.0)).down().length(1.3).label(f'C1{i+1}\n22 uF/25 V\nC_1210', loc='right', fontsize=7.2)
    d += elm.Line().at((xx, 7.6)).down().length(0.6)
    d += elm.Ground().at((xx, 5.7))
d += elm.Line().at(vout).down().length(1.1)
d += elm.Resistor().down().length(1.5).label('R5 100 k 1%\nR_0603', loc='right', fontsize=8)
d += elm.Dot(); fb = d.here
d += elm.Line().at(fb).down().length(1.1)
d += elm.Resistor().down().length(1.5).label('R6 7,15 k 1%\nR_0603', loc='right', fontsize=8)
d += elm.Ground()
d += elm.Line().at(fb).left().length(3.4)
d += elm.Line().up().length(0.6)
d += elm.Line().left().length(1.35)
d += elm.Label().at((8.2, 3.2)).label('FB: Vout = Vref x (1 + R5/R6) = 0,8 x (1+100/7,15) = 11,99 V', fontsize=8.6)
d += elm.Line().at(u1.anchors['BOOT']).right().length(0.6)
d += elm.Line().up().length(1.2)
d += elm.Capacitor().right().length(1.5).label('C13\n100 nF/25 V\nC_0603', loc='top', ofst=0.45, fontsize=8)
d += elm.Line().down().length(1.2)
d += elm.Line().left().length(0.0)
d += elm.Line().at(u1.anchors['GND']).down().length(0.8)
d += elm.Ground()
d += elm.Label().at((7.0, 1.7)).label(
    'Conta do indutor: L = (Vin-Vout)*Dmax/(0,30*Iout*fsw) = 88,9 uH -> 89 uH (E12).\n'
    'Cout: ripple 30% = 0,18 A pp; C >= 3,7 uF -> 2x22 uF (respeita ESR e derating de tensao).\n'
    'Rendimento presumido 90%: Iin(19,8 V) = 404 mA (calculado).', fontsize=8.4)
d.save(D + "esq2_buck12v.png")
print("figs 1 e 2 geradas")
