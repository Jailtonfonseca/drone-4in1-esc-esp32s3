#!/usr/bin/env python3
"""Fase 0 - diagrama de blocos v3 (v1: blocos sobrepostos; v2: linhas/labels colidindo com blocos)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(17.5, 11))
ax.set_xlim(0, 100); ax.set_ylim(0, 72); ax.axis("off")
BB = dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85)

def box(x, y, w, h, text="", fc="#eef3fb", ec="#1f3b6e", fs=8.4, lw=1.4, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.0",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    if text:
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, zorder=3,
                weight="bold" if bold else "normal", linespacing=1.4)

def arrow(x1, y1, x2, y2, color="#1f3b6e", lw=1.4, ls="-", rad=0.0, ms=12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", color=color, lw=lw,
                                 linestyle=ls, mutation_scale=ms, zorder=4,
                                 connectionstyle=f"arc3,rad={rad}"))

def line(pts, color="#1f3b6e", lw=1.2, ls="-", z=3):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="round")

def lab(x, y, t, fs=7.5, color="#1f3b6e", rot=0, ha="center", va="center", bg=True):
    ax.text(x, y, t, fontsize=fs, color=color, ha=ha, va=va, rotation=rot, zorder=6,
            bbox=BB if bg else None)

ax.text(50, 70.6, "DRONE com 4x ESC trifasico + MCU WiFi na MESMA PCB -- DIAGRAMA DE BLOCOS (Fase 0)",
        ha="center", fontsize=14.5, weight="bold")
ax.text(50, 68.4, "bateria 6S (18,0-25,2 V) | 4 motores brushless 2207 1750KV (premissa) | controle por WiFi/ESP-NOW",
        ha="center", fontsize=9, color="#555")

# cadeia de entrada
box(2, 58, 14, 8, "XT60\nentrada da bateria\n6S = 18,0-25,2 V", fc="#fdecec", ec="#8c2f2f")
box(17.5, 58, 16, 8, "PROTECAO\nTVS clamp ~38 V\nP-FET anti-inversao\n(poupa 3,8 W vs. diodo)", fc="#fdecec", ec="#8c2f2f", fs=7.6)
box(35, 58, 15, 8, "BANCO DE ENTRADA\n6x 470 uF polimero\n+ 10 uF + 100 nF\npor par de MOSFET", fc="#fdecec", ec="#8c2f2f", fs=7.6)
arrow(16.1, 62, 17.4, 62); arrow(33.6, 62, 34.9, 62)
line([(50, 62), (98, 62)], color="#8c2f2f", lw=5, z=1)
lab(74, 63.8, "BARRAMENTO VBAT  (2 oz, camada interna + costura de vias)", fs=8, color="#8c2f2f")

# palco de potencia
box(53, 22, 26, 38, "", fc="#eef7ee", ec="#1e5c33", lw=2)
ax.text(66, 58.4, "ESTAGIO DE POTENCIA -- 4x ESC trifasico", ha="center", fontsize=10.2,
        weight="bold", zorder=6, bbox=BB)
for i, yc in enumerate([52.0, 44.0, 36.0, 28.0]):
    if i:
        line([(53.4, yc + 5.6), (78.6, yc + 5.6)], color="#1e5c33", lw=0.8, ls=":")
    ax.text(54.2, yc + 4.2, f"ESC {i+1}", fontsize=8.6, weight="bold", va="top", zorder=5)
    ax.text(54.2, yc + 1.0, "3x gate driver single-input\n(bootstrap, dead-time ~520 ns)\n6x MOSFET N 40-60 V (2 mOhm)",
            fontsize=7.2, va="top", linespacing=1.5, zorder=5)
    ax.text(68.0, yc + 1.0, "3x shunt 0,5 mOhm + amp (x50)\n3x divisor de BEMF + clamp\ncap. de bootstrap 1 uF",
            fontsize=7.2, va="top", linespacing=1.5, zorder=5)
    box(82, yc - 0.6, 16, 6.6, f"MOTOR {i+1}\nconector 3 pinos\n(fases U/V/W)", fc="#f0ecfa", ec="#4b3a8f", fs=7.8)
    arrow(79.1, yc + 2.7, 81.9, yc + 2.7, color="#4b3a8f", ms=11)
arrow(65, 62, 65, 60.3, color="#8c2f2f", lw=2.6)
lab(67.5, 61.3, "VBAT", fs=7.2, color="#8c2f2f")

# MCU
box(2, 22, 32, 32, "", fc="#e8f0fe", ec="#123a7a", lw=2)
ax.text(18, 51.2, "ESP32-S3-WROOM-1  (MCU + radio 2,4 GHz)", ha="center", fontsize=10, weight="bold", zorder=5)
ax.text(3.4, 48.6, "\n".join([
    "MCPWM unit 0 -> motor 1 | unit 1 -> motor 2",
    "       (3 operadores x par H/L, dead-time em HW)",
    "LEDC 8 canais -> motores 3 e 4 (2 timers x 3)",
    "       portadoras defasadas 90 graus entre motores",
    "            -> ripple no banco 4,5x menor (calculado)",
    "ADC 12 bits, trigger sincrono ao PWM:",
    "       12x corrente de fase + 12x BEMF",
    "VBAT sense (divisor 100k/13,7k + RC 132 Hz)",
    "I2C -> IMU 6 eixos + barometro (3,3 V_A)",
    "USB nativo D+/D- -> USB-C (so' programacao)",
    "GPIO: LED, buzzer, botao, canal de failsafe",
]), fontsize=7.6, va="top", linespacing=1.6, zorder=5)
box(3.5, 23.2, 29, 7.6, "PILHA DE CONTROLE (firmware)\nIMU 1-4 kHz -> PID de atitude -> setpoint\nde motor | WiFi/ESP-NOW so' para COMANDOS\nFAILSAFE: timeout 200 ms -> corta motores",
    fc="#f2f4f7", ec="#5a5a5a", fs=7.4)

# PWM + sensoriamento
for yc in [52.0, 44.0, 36.0, 28.0]:
    arrow(34.2, yc + 3.6, 52.8, yc + 3.4, color="#1e5c33", lw=1.2, rad=-0.05)
lab(43.5, 55.6, "6x PWM por motor\n(dead-time no driver)", fs=7.4, color="#1e5c33")
line([(53.0, 20.6), (24.0, 20.6)], color="#8a6100", lw=1.3)
arrow(24.0, 20.6, 24.0, 22.1, color="#8a6100", lw=1.3)
arrow(53.0, 20.6, 53.0, 21.9, color="#8a6100", lw=1.3, ms=11)
lab(41.0, 19.4, "12x corrente de fase + 12x BEMF (trigger sincrono ao PWM)", fs=7.4, color="#8a6100")

# energia
box(36, 3, 26, 14.6, "", fc="#fff7e6", ec="#8a6100", lw=1.6)
ax.text(49, 16.2, "REGULACAO DE ENERGIA", ha="center", fontsize=10, weight="bold", zorder=6, bbox=BB)
ax.text(37.2, 14.0, "\n".join([
    "BUCK 12 V / 0,60 A -> 12 gate drivers (49 mA)",
    "BUCK 5 V  / 2,00 A -> 3,3 V buck, LDO anal., USB",
    "BUCK 3,3 V/ 1,50 A -> MCU+radio (pico 0,52 A)",
    "LDO 3,3 V_A/0,15 A -> IMU/barometro (baixo ruido)",
]), fontsize=7.4, va="top", linespacing=1.7, zorder=5)
line([(44.0, 58.0), (44.0, 17.7)], color="#8c2f2f", lw=2.0, z=1)
arrow(44.0, 17.7, 44.0, 17.6, color="#8c2f2f", lw=2.0)
lab(44.0, 40.0, "VBAT", fs=7.2, color="#8c2f2f", rot=90)
line([(36.0, 10.0), (33.0, 10.0), (33.0, 21.8)], color="#8a6100", lw=1.2)
arrow(33.0, 21.8, 33.0, 21.6, color="#8a6100", lw=1.2)
lab(31.6, 16.0, "3,3 V", fs=7.2, color="#8a6100", rot=90)

# perifericos
box(64, 3, 15, 14.6, "SENSORES A BORDO\nIMU 6 eixos\n(SPI/I2C)\nbarometro (I2C)\n\nopcional:\nmagnetometro/GPS", fc="#f0ecfa", ec="#4b3a8f", fs=7.6)
box(81, 3, 17, 14.6, "USB-C + EXTRAS\nprotecao + ideal diode\n(alimenta 5 V sem bateria)\n\nLED + buzzer\npads I2C/SPI/UART\npad de debug/OTA", fc="#f0ecfa", ec="#4b3a8f", fs=7.6)
line([(20.0, 22.0), (20.0, 19.0), (71.5, 19.0)], color="#4b3a8f", lw=1.1)
arrow(71.5, 19.0, 71.5, 17.8, color="#4b3a8f", lw=1.1)
lab(52.0, 20.2, "I2C / SPI / UART", fs=7.2, color="#4b3a8f")

ax.text(50, 0.9, "Fase 0 -- rascunho de arquitetura. Numeros conforme dimensionamento_fase0_saida_v2.txt e "
                 "verifica_limites_saida_v4.txt. Nenhum valor medido em bancada.",
        ha="center", fontsize=7.4, color="#777")
plt.tight_layout()
plt.savefig("/opt/jupyter/work/drone/fase0_especificacao/diagrama_blocos_fase0_v3.png", dpi=150)
print("ok")
