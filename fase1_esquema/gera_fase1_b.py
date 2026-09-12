#!/usr/bin/env python3
"""FASE 1 - figuras 5..9 (entrada v3, ESC detalhe, ESC visao geral, MCU, arvore de energia).
Metodo: coordenadas absolutas; pinos de CI calculados por at+offset_local (offsets medidos
antes de desenhar, com a funcao offsets())."""
import os
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm

D = os.path.dirname(os.path.abspath(__file__)) + "/"
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

def rect(x0, y0, x1, y1, lw=1.0, color='black'):
    W((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0), lw=lw, color=color)

def offsets(pins, w, h):
    """mede os offsets locais dos pinos antes de posicionar o CI no desenho real"""
    tmp = schemdraw.Drawing(show=False)
    el = elm.Ic(pins=pins, w=w, h=h).at((0.0, 0.0))
    tmp += el
    return {k: v for k, v in el.anchors.items()}

# ============================================================ FIG 5: ESC DETALHE
def esc_detalhe():
    global d
    novo()
    T(7.5, 12.3, "BLOCO 5 - ESC TRIFASICO: DETALHE DE 1 HALF-BRIDGE (repetido 12x na placa)", 11.5)
    yp = 6.5                     # linha de fase
    xf = 7.0                     # coluna dos MOSFETs
    # conector de motor (1 fase mostrada)
    j2 = elm.Ic(pins=[elm.IcPin(name='U', side='right', slot='1/1', pin='1')],
                w=1.7, h=1.3, label='J2\nMR30\nfase U').at((0.4, yp))
    d += j2
    o = offsets([elm.IcPin(name='U', side='right', slot='1/1')], 1.7, 1.3)
    pj = (0.4 + o['U'][0], yp + o['U'][1])
    W(pj, (xf, pj[1]))
    T(3.6, yp - 0.55, 'fase U -> motor', 8)
    # MOSFETs
    hs = elm.NFet().at((xf, 8.0)); d += hs
    ls = elm.NFet().at((xf, 5.5)); d += ls
    T(xf - 1.35, 8.4, 'Q1A\nVds>=40 V\nRds<=3 mOhm\nTO-252-3 (DPAK)', 7)
    T(xf - 1.35, 5.9, 'Q1B\nVds>=40 V\nRds<=3 mOhm\nTO-252-3 (DPAK)', 7)
    W((xf, 9.7), (xf, 8.0), color='#8c2f2f')
    W((xf, 9.7), (11.8, 9.7), color='#8c2f2f', lw=1.8)
    T(8.4, 10.1, 'VBAT 18,0-25,2 V', 9.5, '#8c2f2f')
    W((xf, 6.5), (xf, 5.5))          # no de fase
    d += elm.Dot().at((xf, 6.5))
    # shunt
    W((xf, 4.0), (xf, 3.9))
    d += elm.Resistor().at((xf, 3.9)).down().length(1.3)
    T(xf - 0.9, 3.2, 'Rsh 0,5 mOhm\n2 W / 2512\n112 mW cont.', 7)
    W((xf, 2.6), (xf, 1.7))
    W((xf, 1.7), (13.5, 1.7), lw=1.5)
    GND((9.6, 1.7))
    T(11.6, 1.25, 'GND (plano da camada 2)', 8)
    # divisor de BEMF
    d += elm.Dot().at((4.2, yp))
    W((4.2, yp), (4.2, yp + 2.1))
    d += elm.Resistor().at((4.2, yp + 2.1)).right().length(1.6)
    T(5.0, yp + 2.6, 'R8 8,2 k 1%', 7)
    W((5.8, yp + 2.1), (6.6, yp + 2.1))
    d += elm.Dot().at((6.2, yp + 2.1))
    d += elm.Resistor().at((6.2, yp + 2.1)).down().length(1.6)
    T(6.45, yp + 1.0, 'R9 1,0 k 1%', 7)
    W((6.2, yp + 0.5), (6.2, yp))
    d += elm.Capacitor().at((7.1, yp + 2.1)).down().length(1.0)
    T(7.35, yp + 1.5, '1 nF', 7)
    W((7.1, yp + 2.1), (7.6, yp + 2.1))
    W((7.1, yp + 1.1), (7.1, yp))
    T(8.6, yp + 2.9, 'BEMF_U -> ADC externo SPI (divisor 8,2k/1,0k; 25,2 V -> 2,74 V;\nfc = 178 kHz; clamp 3,3 V na entrada do ADC)', 8)
    # gate driver
    pins = [elm.IcPin(name='HO', side='left', slot='5/6', pin='2'),
            elm.IcPin(name='VS', side='left', slot='3/6', pin='3'),
            elm.IcPin(name='LO', side='left', slot='1/6', pin='4'),
            elm.IcPin(name='VB', side='top', pin='1'),
            elm.IcPin(name='VCC', side='right', slot='3/4', pin='6'),
            elm.IcPin(name='IN', side='right', slot='1/4', pin='5'),
            elm.IcPin(name='COM', side='bottom', pin='7')]
    o = offsets(pins, 3.0, 4.0)
    ax, ay = 12.6, 6.5 - o['VS'][1]
    drv = elm.Ic(pins=pins, w=3.0, h=4.0, label='U1\nGATE\nDRIVER\nsingle\ninput\ndead-time\n520 ns\nSOIC-8').at((ax, ay))
    d += drv
    P = {k: (ax + o[k][0], ay + o[k][1]) for k in ('HO', 'VS', 'LO', 'VB', 'VCC', 'IN', 'COM')}
    # HO -> Rg -> gate do HS (gate em (xf+1.37, 7.25))
    ygh, ygl = 8.0 - 0.75, 5.5 - 0.75
    W(P['HO'], (10.9, P['HO'][1]), (10.9, ygh))
    d += elm.Resistor().at((10.9, ygh)).to((9.5, ygh))
    T(10.2, ygh + 0.35, 'Rg 10 ohm\nR_0805', 7)
    W((9.5, ygh), (xf + 1.37, ygh), color='#1e5c33')
    # LO -> Rg -> gate do LS
    W(P['LO'], (10.9, P['LO'][1]), (10.9, ygl))
    d += elm.Resistor().at((10.9, ygl)).to((9.5, ygl))
    T(10.2, ygl - 0.55, 'Rg 10 ohm\nR_0805', 7)
    W((9.5, ygl), (xf + 1.37, ygl), color='#1e5c33')
    # VS -> no de fase
    W(P['VS'], (11.6, P['VS'][1]), (11.6, 6.5), (xf, 6.5), color='#555', lw=1.5)
    T(11.0, 5.9, 'VS = referencia flutuante\n(acompanha a fase)', 7)
    # bootstrap VB -> Cboot -> no de fase
    W(P['VB'], (P['VB'][0], 10.6), (8.6, 10.6), (8.6, 6.5), (xf, 6.5))
    d += elm.Capacitor().at((8.6, 10.6 - 0.1)).down().length(1.1)
    T(8.85, 9.8, 'Cboot\n1 uF/25 V\nX7R (C_0805)', 7)
    d += elm.Diode().at((11.0, 10.6)).right().length(1.2)
    T(11.6, 11.1, 'Db 100 V/1 A SOD-123\n(carga o bootstrap a partir de +12 V)', 7)
    W((11.0, 10.6), (8.6, 10.6))
    W((12.2, 10.6), (14.6, 10.6), (14.6, P['VCC'][1]), P['VCC'], color='#8c2f2f')
    T(14.2, 10.15, '+12 V', 9, '#8c2f2f')
    # IN <- PWM
    W(P['IN'], (P['IN'][0] + 1.0, P['IN'][1]))
    T(P['IN'][0] + 1.05, P['IN'][1] + 0.45, 'PWM_U  do MCU\n(MCPWM ou LEDC)\n20 kHz', 7.5)
    # COM -> GND
    W(P['COM'], (P['COM'][0], 1.7))
    T(4.2, 0.7, 'Gate driver single-input: o CI gera a saida complementar com dead-time de hardware (520 ns),\n'
                'por isso basta 1 pino PWM por half-bridge (3 por motor, 12 no total).', 8.2)
    d.save(D + "esq5_esc_halfbridge.png")

# ============================================================ FIG 6: ESC VISAO GERAL
def esc_geral():
    global d
    novo(unit=0.75, fs=9)
    T(9.0, 13.4, "BLOCO 6 - OS 4 ESCs: CONTAGEM DE PERIFERICOS, PWM E CANAIS DE ADC", 11.5)
    for i in range(4):
        y = 11.0 - i * 2.6
        rect(0.6, y - 0.85, 8.6, y + 0.85)
        T(4.6, y + 0.35, f'MOTOR {i+1}  -  3 half-bridges', 9.5)
        T(4.6, y - 0.15, '6 MOSFET N (Vds>=40 V/Rds<=3 mOhm) + 3 gate drivers single-input (dead-time 520 ns)', 7.5)
        T(4.6, y - 0.6, '3 shunts 0,5 mOhm + 3 amplificadores ganho 50 + 3 divisores de BEMF 8,2k/1,0k', 7.5)
        rect(9.4, y - 0.85, 12.6, y + 0.85)
        T(11.0, y + 0.35, f'CONECTOR\nMR30 3 pinos', 8.5)
        T(11.0, y - 0.45, 'fase U/V/W', 7.5)
        W((8.6, y), (9.4, y), lw=1.6, color='#1e5c33')
        T(9.0, y + 0.28, '3 fases', 6.5)
        W((0.6, y), (-0.5, y), lw=1.4, color='#8c2f2f')
        T(-0.3, y + 0.3, 'VBAT', 6.5, '#8c2f2f')
    T(-2.2, 11.3, 'PWM  (do ESP32-S3):\n12 canais de 20 kHz\n', 8.5)
    T(-2.2, 10.4, 'motor 1 e 2 -> MCPWM\n(6 canais, dead-time em HW)\n'
                  'motor 3 e 4 -> LEDC\n(6 canais, sem dead-time em HW)\n'
                  '-> por isso o driver single-input', 7.5)
    T(-2.2, 8.4, 'portadoras defasadas\n0/90/180/270 graus\n(interleaving: -4,5x no\nripple RMS do banco)', 7.5)
    T(-0.3, 6.2, 'VBAT  (4 ESCs)', 7.5, '#8c2f2f')
    T(-2.2, 4.6, '12 x I_FASE  ->  ADC externo 1\n12 x BEMF     ->  ADC externo 2\n'
                 '(16 canais SPI cada, amostragem\nsimultanea; o ADC1 do MCU tem ~10 canais\ne o ADC2 divide o silicio com o radio)', 7.5)
    rect(-3.6, -0.4, 15.4, 3.0)
    T(5.9, 2.45, 'TOTAIS DA PLACA (4 motores)', 9.5)
    T(5.9, 1.6, '24 MOSFETs de potencia  |  12 gate drivers  |  12 shunts 0,5 mOhm  |  12 amplificadores de corrente\n'
                '12 divisores de BEMF  |  4 conectores de motor  |  12 canais PWM  |  24 canais de ADC externo', 8)
    T(5.9, 0.45, 'Corrente: 60 A continuo / 120 A de pico no VBAT [PREMISSA].  Barramento dimensionado para dezenas de amperes em 2 oz\n'
                 'com camada interna dedicada e metal exposto; o pico e absorvido pela massa de cobre + capacitancia (nao validavel em software).', 7.5)
    d.save(D + "esq6_esc_visao_geral.png")

# ============================================================ FIG 7: MCU
def mcu():
    global d
    novo(unit=0.75, fs=9)
    T(8.0, 12.6, "BLOCO 7 - ESP32-S3 (WiFi), USB-C, IMU, BAROMETRO E ADC EXTERNO", 11.5)
    rect(4.6, 3.2, 11.4, 11.6)
    T(8.0, 11.2, 'U5  ESP32-S3-WROOM-1', 10)
    T(8.0, 10.6, 'WiFi 2,4 GHz + USB nativo\npegada gerada por script (nao existe no KiCad 5.1)', 7.5)
    T(8.0, 9.4, 'PWM:\nGPIO4,5,6 / 7,8,9 (MCPWM)\nGPIO10,11,12 / 13,14,15 (LEDC)', 7.5)
    T(8.0, 7.6, 'SPI do ADC externo:\nGPIO16=MOSI 17=SCK 18=MISO\n21=CS 47=IRQ/DRDY', 7.5)
    T(8.0, 5.9, 'GPIO1 = VBAT_SENSE (ADC1)\nGPIO2 = temperatura (ADC1)\nGPIO48 = feed do watchdog externo', 7.5)
    T(8.0, 4.1, 'USB nativo: GPIO19 = D-  GPIO20 = D+\nUART0: GPIO43 = TXD0, GPIO44 = RXD0\nBOOT: GPIO0   EN: reset', 7.5)
    # USB-C
    rect(0.4, 8.0, 3.4, 10.4)
    T(1.9, 9.9, 'J3  USB-C 16p\nGCT_USB4085\n5 V / D+ / D-\nCC1/CC2 5,1 k', 7.5)
    W((3.4, 9.2), (4.6, 9.2), lw=1.4)
    T(4.0, 9.55, 'USB nativo', 6.5)
    W((3.4, 8.6), (4.0, 8.6), (4.0, 7.0), (4.6, 7.0))
    T(4.65, 6.6, 'VBUS -> diodo ideal\n-> +5 V (auxiliar)', 7)
    # IMU
    rect(0.4, 4.6, 3.4, 6.6)
    T(1.9, 6.0, 'U6  IMU 6 eixos\nQFN-24 3x3 mm\nSPI 4-8 MHz\nCS = GPIO42\n(compartilha 16/17/18)', 7)
    W((3.4, 5.6), (4.6, 5.6), lw=1.4)
    T(3.6, 5.95, 'SPI', 6.5)
    # barometro
    rect(0.4, 1.4, 3.4, 3.6)
    T(1.9, 2.9, 'U7  BAROMETRO\nLGA-8\nI2C 400 kHz\nSDA=GPIO38\nSCL=GPIO39', 7)
    T(1.9, 1.75, 'pull-ups 4,7 k', 6.5)
    W((3.4, 2.6), (4.6, 2.6), lw=1.4)
    T(3.6, 2.95, 'I2C', 6.5)
    # ADC externo
    rect(12.6, 3.2, 16.6, 11.6)
    T(14.6, 11.0, 'U8/U9\nADC EXTERNO\nSPI 16 canais', 8.5)
    T(14.6, 9.4, 'canal 0..11:\nI_FASE 1..12\n(shunt x50)', 7.5)
    T(14.6, 7.6, 'canal 12..15:\nsobram 4\n-> BEMF em 2 CI\n(mux interno)', 7.5)
    T(14.6, 5.4, 'por que externo:\n26 canais analogicos\n> ~10 do ADC1;\nADC2 divide o radio\ncom o WiFi', 7.5)
    W((11.4, 7.6), (12.6, 7.6), lw=1.4)
    T(12.0, 7.95, 'SPI', 6.5)
    # extras
    rect(12.6, 0.6, 16.6, 2.6)
    T(14.6, 1.9, 'EXTRAS\nLED GPIO45 / buzzer GPIO46 / botao GPIO0\npads UART + I2C + SPI + 4 GPIO livres', 7.5)
    T(8.0, 0.0, 'Total: ~32 dos 36 GPIOs usados (folga apertada).  Os numeros fixos (USB D+/D-) e a contagem real de\n'
                'MCPWM/LEDC/ADC sao [N/D offline] - conferir no TRM do ESP32-S3 antes de rotear.', 7.5)
    d.save(D + "esq7_mcu.png")

# ============================================================ FIG 8: ARVORE DE ENERGIA
def arvore():
    global d
    novo(unit=0.75, fs=9)
    T(8.0, 10.6, "BLOCO 8 - ARVORE DE ENERGIA E ORCAMENTO POR TRILHO", 11.5)
    def blk(x0, y0, x1, y1, txt, fs=8):
        rect(x0, y0, x1, y1); T((x0 + x1) / 2, (y0 + y1) / 2, txt, fs)
    blk(0.4, 7.8, 3.6, 9.8, 'BATERIA LiPo 6S\n25,2 V max / 22,2 nom\n19,8 V min (3,30 V/cel)\n[PREMISSA P-02]', 7.5)
    blk(4.6, 7.8, 7.8, 9.8, 'PROTECAO\nTVS 38 V + P-FET\nanti-inversao\n+ fusivel/e-fuse', 7.5)
    blk(8.8, 7.8, 12.6, 9.8, 'BANCO DE ENTRADA\n6x 470 uF + 10 uF + 100 nF\nripple 1140 mV pk-pk @30 A\n(ESR/ESL mandam)', 7.5)
    blk(13.6, 7.8, 17.6, 9.8, 'VBAT\n18,0-25,2 V\n4 ESCs: 60 A cont. / 120 A pico\n[PREMISSA]', 7.5)
    W((3.6, 8.8), (4.6, 8.8), lw=1.6); W((7.8, 8.8), (8.8, 8.8), lw=1.6); W((12.6, 8.8), (13.6, 8.8), lw=1.6)
    blk(13.6, 5.4, 17.6, 7.2, 'BUCK 12 V / 0,60 A\nL 89 uH  fsw 500 kHz\ncarga real: 12 drivers\nx2,5 mA + gate 19,2 mA = 49 mA\nfolga 12x', 7.5)
    W((15.6, 7.8), (15.6, 7.2), lw=1.4, color='#8c2f2f')
    blk(8.6, 5.4, 12.6, 7.2, 'BUCK 5 V / 2,00 A\nL 17 uH  fsw 500 kHz\ncarga: buck 3,3 V (1,16 A)\n+ LDO_A (0,15 A) + aux (0,02 A)\n= 1,33 A -> folga 1,5x', 7.5)
    W((13.6, 6.3), (12.6, 6.3), lw=1.4, color='#8c2f2f')
    blk(3.6, 5.4, 7.6, 7.2, 'BUCK 3,3 V / 1,50 A\nL 5 uH  fsw 500 kHz\ncarga: ESP32-S3 pico WiFi TX\n0,50 A + sensores + LED\n= 0,518 A -> folga 2,9x', 7.5)
    W((8.6, 6.3), (7.6, 6.3), lw=1.4, color='#8c2f2f')
    blk(3.6, 3.0, 7.6, 4.6, 'LDO 3,3 V_A / 150 mA\nanalogico (ADC, referencia)\nPdiss = 0,255 W -> SOT-23\ncom pad termico', 7.5)
    W((6.0, 5.4), (6.0, 4.6), lw=1.4, color='#8c2f2f')
    blk(8.6, 3.0, 12.6, 4.6, 'CARGA 3,3 V\nESP32-S3 + IMU + baro\n+ ADC externo', 7.5)
    W((2.2, 5.4), (2.2, 4.6), lw=0)  # espaco
    blk(13.6, 3.0, 17.6, 4.6, 'CARGA 12 V\n12 gate drivers\n(3 por motor)', 7.5)
    T(8.8, 2.2, 'Verificacao do balanco (Fase 0, calculado): cruzeiro 167 W de helice -> 7,5 A de barra, 12,5 A de pico de fase;\n'
                'perdas nos 24 FETs 1,88 W; conversores 4,00 W; total ~173 W (3,5 % acima do ideal de helice).', 8)
    T(8.8, 1.2, 'Orcamento por trilho: 3,3 V = 0,518 A (buck 1,50 A) | 12 V = 0,049 A (buck 0,60 A) | 5 V = 1,328 A (buck 2,00 A) |\n'
                'VBAT = 60 A continuo [PREMISSA] + 0,30 A dos conversores.  Nenhuma dessas correntes foi medida em bancada.', 8)
    d.save(D + "esq8_arvore_energia.png")

esc_detalhe()
esc_geral()
mcu()
arvore()
print("figs 5-8 geradas")
