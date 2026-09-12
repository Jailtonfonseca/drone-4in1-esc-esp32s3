#!/usr/bin/env python3
"""Fase 1 - FIG 4: ESC trifasico completo (1 motor). Geometria explicita.
FET: elm.NFet().at((x,y)) -> drain=(x,y), source=(x,y-1,5), gate=(x+1,37,y-0,75)."""
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm

D = "/opt/jupyter/work/drone/fase1_esquema/"
d = schemdraw.Drawing(show=False); d.config(unit=1.7, fontsize=8.5, lw=1.2)

def W(*pts, color='black', lw=1.2, ls='-'):
    global d
    for a, b in zip(pts[:-1], pts[1:]):
        d += elm.Line().at(a).to(b).color(color).linewidth(lw).linestyle(ls)

d += elm.Label().at((9, 16.6)).label("BLOCO 4 - ESC TRIFASICO (1 dos 4 motores): 3 half-bridges + gate drivers + shunts + BEMF", fontsize=13)

# ---- rail 12 V e VBAT
W((4, 15.2), (16, 15.2), color='#8c2f2f', lw=2)
d += elm.Label().at((10, 15.6)).label('+12 V (BUCK 12 V/0,60 A)', fontsize=9, color='#8c2f2f')
W((18, 15.2), (27, 15.2), color='#8c2f2f', lw=2)
d += elm.Label().at((22.5, 15.6)).label('VBAT (18,0-25,2 V) -- 3 fases', fontsize=9, color='#8c2f2f')

# ---- conector do motor (a esquerda)
mj = elm.Ic(pins=[elm.IcPin(name='U', side='right', slot='1/6', pin='1'),
                  elm.IcPin(name='V', side='right', slot='3/6', pin='2'),
                  elm.IcPin(name='W', side='right', slot='5/6', pin='3')],
            w=2.0, h=13.0, label='J2\nMR30 3 pinos\nAMASS_MR30PW-FB\nMOTOR').at((0.3, 4.5))
d += mj

def fase(y, n):
    global d
    xf = 8.0            # coluna dos MOSFETs
    xd = 13.0           # driver (caixa de xd a xd+2.9)
    # MOSFETs
    hs = elm.NFet().at((xf, y+2.2)); d += hs
    ls = elm.NFet().at((xf, y-0.4)); d += ls
    d += elm.Label().at((xf-1.5, y+2.6)).label(f'Q{n}A\nVds>=40 V\nRds<=3 mOhm\nTO-252-3', fontsize=7)
    d += elm.Label().at((xf-1.5, y-0.05)).label(f'Q{n}B\nVds>=40 V\nRds<=3 mOhm\nTO-252-3', fontsize=7)
    # VBAT -> drain do HS
    W((xf, 15.2), (xf, y+2.2), color='#8c2f2f')
    d += elm.Dot().at((xf, y+2.2))
    # ponto de fase (source do HS = drain do LS) e saida para o motor
    W((xf, y+0.7), (xf, y-0.4))
    d += elm.Dot().at((xf, y+0.7))
    W((xf, y+0.7), (2.3, y+0.7))
    d += elm.Label().at((5.2, y+1.0)).label(f'fase {"UVW"[n-1]}', fontsize=8)
    # shunt low-side
    W((xf, y-1.9), (xf, y-2.6))
    d += elm.Resistor().at((xf, y-2.6)).down().length(1.3).label('Rsh\n0,5 mOhm\n2 W / 2512', loc='left', fontsize=7)
    d += elm.Dot().at((xf, y-3.9))
    W((xf, y-3.9), (xf, -6.6))
    # divisor de BEMF a partir da fase
    d += elm.Dot().at((4.6, y+0.7))
    W((4.6, y+0.7), (4.6, y+3.2))
    d += elm.Resistor().at((4.6, y+3.2)).right().length(1.6).label('R8 8,2 k', loc='top', fontsize=7)
    W((6.2, y+3.2), (7.0, y+3.2))
    d += elm.Dot().at((6.6, y+3.2))
    d += elm.Resistor().at((6.6, y+3.2)).down().length(1.6).label('R9\n1,0 k', loc='right', fontsize=7)
    W((6.6, y+1.6), (6.6, y+1.1), (6.6, y+0.7))
    W((7.0, y+3.2), (7.6, y+3.2))
    d += elm.Label().at((9.4, y+3.2)).label(f'BEMF_{n}\n(1 nF + clamp)\n-> ADC externo', fontsize=7)
    # driver
    drv = elm.Ic(pins=[elm.IcPin(name='HO', side='left', slot='1/6', pin='2'),
                       elm.IcPin(name='VS', side='left', slot='3/6', pin='3'),
                       elm.IcPin(name='LO', side='left', slot='5/6', pin='4'),
                       elm.IcPin(name='VB', side='top', pin='1'),
                       elm.IcPin(name='VCC', side='right', slot='1/3', pin='6'),
                       elm.IcPin(name='IN', side='right', slot='3/3', pin='5'),
                       elm.IcPin(name='COM', side='bottom', pin='7')],
                 w=2.9, h=2.6, label=f'U{n+1}\nGATE DRV\nsingle-input\ndead-time 520 ns\nSOIC-8').at((xd, y+0.2))
    d += drv
    # HO -> Rg -> gate do HS ; LO -> Rg -> gate do LS
    for nome, yg, corr in (('HO', y+2.2-0.75, '#1e5c33'), ('LO', y-0.4-0.75, '#1e5c33')):
        y0 = drv.anchors[nome][1]
        W((drv.anchors[nome][0], y0), (12.0, y0), (12.0, yg), color=corr)
        d += elm.Resistor().at((12.0, yg)).to((10.6, yg)).label('Rg\n10 ohm\nR_0805', loc='top', fontsize=7)
        W((10.6, yg), (xf+1.37, yg), color=corr)
    # VS -> ponto de fase
    W((drv.anchors['VS'][0], drv.anchors['VS'][1]), (xf, y+0.7), color='#555')
    d += elm.Label().at((11.2, y-0.55)).label('VS (referencia flutuante)', fontsize=6.5)
    # bootstrap
    W((drv.anchors['VB'][0], drv.anchors['VB'][1]), (drv.anchors['VB'][0], y+6.4))
    W((drv.anchors['VB'][0], y+6.4), (9.3, y+6.4), (9.3, y+0.7), (xf, y+0.7))
    d += elm.Capacitor().at((9.3, y+3.6)).down().length(0.0).label(' ', fontsize=6)
    d += elm.Capacitor2().at((9.3, y+4.6)).down().length(1.2).label('Cb 1 uF\n25 V X7R', loc='left', fontsize=7)
    W((9.3, y+4.6), (9.3, y+6.4)); W((9.3, y+3.4), (9.3, y+0.7))
    # diodo de bootstrap do 12 V para VB
    d += elm.Diode().at((15.0, 15.2)).down().length(1.0).label('Db\n100 V/1 A\nSOD-123', loc='right', fontsize=7)
    W((15.0, 14.2), (15.0, y+6.4), (drv.anchors['VB'][0], y+6.4))
    # VCC <- 12 V ; IN <- PWM ; COM -> GND
    W((drv.anchors['VCC'][0], drv.anchors['VCC'][1]), (drv.anchors['VCC'][0]+0.8, drv.anchors['VCC'][1]))
    W((drv.anchors['VCC'][0]+0.8, drv.anchors['VCC'][1]), (drv.anchors['VCC'][0]+0.8, 15.2), color='#8c2f2f')
    W((drv.anchors['IN'][0], drv.anchors['IN'][1]), (drv.anchors['IN'][0]+1.0, drv.anchors['IN'][1]))
    d += elm.Label().at((drv.anchors['IN'][0]+1.4, drv.anchors['IN'][1])).label(f'PWM_{n}\ndo MCU\n(MCPWM/LEDC)', fontsize=7)
    W((drv.anchors['COM'][0], drv.anchors['COM'][1]), (drv.anchors['COM'][0], -6.6))
    # amp de corrente
    amp = elm.Opamp(leads=True).at((xf+3.4, y-3.0)).label('CSA\nx50\nSOIC-8', loc='center', fontsize=7)
    d += amp
    W((xf, y-2.6), (11.4, y-2.6), (11.4, y-2.55))
    W((xf, y-3.9), (11.4, y-3.9), (11.4, y-3.45))
    d += elm.Label().at((x:=10.6, y-2.1)).label('IN+', fontsize=6.5)
    d += elm.Label().at((x, y-4.35)).label('IN-', fontsize=6.5)
    W((amp.anchors['out'][0], amp.anchors['out'][1]), (amp.anchors['out'][0]+1.2, amp.anchors['out'][1]))
    d += elm.Label().at((amp.anchors['out'][0]+2.6, amp.anchors['out'][1])).label(f'I_FASE_{n}\n-> ADC externo SPI', fontsize=7)

for i, y in enumerate([9.0, 3.2, -2.6]):
    fase(y, i+1)

# GND rail
W((2.3, -6.6), (20, -6.6), lw=2)
d += elm.Label().at((11, -7.1)).label('GND (plano de terra na camada 2) - retorno dos shunts, COM dos drivers, amp', fontsize=9)
d += elm.Label().at((20.5, 15.2)).label('VBAT', fontsize=9, color='#8c2f2f')
d += elm.Label().at((9, -8.4)).label(
    'Notas: (1) 1 pino PWM por half-bridge -> o driver gera o complementar com dead-time interno.\n'
    '(2) Amostragem do ADC sincrona ao PWM: shunt low-side so e valido com QnB conduzindo.\n'
    '(3) BEMF passa por divisor 8,2k/1,0k (25,2 V -> 3,07 V) + 1 nF + clamp 3,3 V.\n'
    '(4) 100 nF + 10 uF ceramicos colados a cada par de MOSFETs (nao desenhados por clareza).', fontsize=8.6)
d.save(D + "esq4_esc_trifasico.png")
print("fig 4 gerada")
