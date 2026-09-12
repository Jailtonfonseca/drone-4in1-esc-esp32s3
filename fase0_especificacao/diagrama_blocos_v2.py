#!/usr/bin/env python3
"""Fase 0 - diagrama de blocos v2 (v1 tinha blocos sobrepostos: caixa de energia em cima dos ESCs)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(17, 11))
ax.set_xlim(0, 100); ax.set_ylim(0, 72); ax.axis("off")

def box(x, y, w, h, text="", fc="#eef3fb", ec="#1f3b6e", fs=8.4, lw=1.4, bold=False, va="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.0",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    if text:
        ax.text(x + w/2, y + h/2 if va == "center" else y + h - 1.0, text, ha="center", va=va,
                fontsize=fs, zorder=3, weight="bold" if bold else "normal", linespacing=1.4)

def arrow(x1, y1, x2, y2, color="#1f3b6e", lw=1.4, ls="-", rad=0.0, ms=12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", color=color, lw=lw,
                                 linestyle=ls, mutation_scale=ms, zorder=4,
                                 connectionstyle=f"arc3,rad={rad}"))

def lab(x, y, t, fs=7.5, color="#1f3b6e", rot=0, ha="center", va="center", w="normal"):
    ax.text(x, y, t, fontsize=fs, color=color, ha=ha, va=va, rotation=rot, zorder=5, weight=w)

ax.text(50, 70.6, "DRONE com 4x ESC trifasico + MCU WiFi na MESMA PCB -- DIAGRAMA DE BLOCOS (Fase 0)",
        ha="center", fontsize=14.5, weight="bold")
ax.text(50, 68.4, "bateria 6S (18,0-25,2 V) | 4 motores brushless 2207 1750KV (premissa) | controle por WiFi/ESP-NOW",
        ha="center", fontsize=9, color="#555")

# ---------------- cadeia de entrada
box(2, 58, 14, 8, "XT60\nentrada da bateria\n6S = 18,0-25,2 V", fc="#fdecec", ec="#8c2f2f")
box(17.5, 58, 16, 8, "PROTECAO\nTVS clamp ~38 V\nP-FET anti-inversao\n(0,5 V * 7,5 A = 3,8 W\nevitados vs. diodo)", fc="#fdecec", ec="#8c2f2f", fs=7.6)
box(35, 58, 15, 8, "BANCO DE ENTRADA\n6x 470 uF polimero\n+ 10 uF + 100 nF\npor par de MOSFET", fc="#fdecec", ec="#8c2f2f", fs=7.6)
arrow(16.1, 62, 17.4, 62); arrow(33.6, 62, 34.9, 62)
ax.plot([50, 98], [62, 62], color="#8c2f2f", lw=5, zorder=1, solid_capstyle="round")
arrow(50, 62, 50, 62)
lab(74, 63.9, "BARRAMENTO VBAT  (2 oz, camada interna + costura de vias)", fs=8, color="#8c2f2f")

# ---------------- palco de potencia (1 caixa, 4 ESCs)
box(53, 22, 26, 38, "", fc="#eef7ee", ec="#1e5c33", lw=2)
ax.text(66, 58.6, "ESTAGIO DE POTENCIA -- 4x ESC trifasico", ha="center", fontsize=10.2, weight="bold")
for i, yc in enumerate([52.5, 44.5, 36.5, 28.5]):
    ax.plot([53.4, 78.6], [yc + 4.0, yc + 4.0], color="#1e5c33", lw=0.8, ls=":", zorder=3)
    ax.text(54.2, yc + 2.6, f"ESC {i+1}", fontsize=8.6, weight="bold", va="top")
    ax.text(54.2, yc + 0.2,
            "3x gate driver single-input (bootstrap,\nforced dead-time ~520 ns)\n"
            "6x MOSFET N 40-60 V (Rds~2 mOhm)\n",
            fontsize=7.3, va="top", linespacing=1.5)
    ax.text(67.5, yc + 0.2,
            "3x shunt 0,5 mOhm low-side\n+ amp de corrente (ganho 50)\n"
            "3x divisor de BEMF + clamp\ncapacitor de bootstrap 1 uF",
            fontsize=7.3, va="top", linespacing=1.5)
    box(82, yc - 0.4, 16, 6.6, f"MOTOR {i+1}\nconector 3 pinos\n(fase U/V/W)", fc="#f0ecfa", ec="#4b3a8f", fs=7.8)
    arrow(79.1, yc + 2.9, 81.9, yc + 2.9, color="#4b3a8f", ms=11)
    arrow(65, 62, 65, 60.1, color="#8c2f2f", lw=2.4)
    arrow(60, 62, 60, 51.0, color="#8c2f2f", lw=1.2, ls=":")
lab(66.5, 57.1, "VBAT", fs=7, color="#8c2f2f")

# ---------------- MCU
box(2, 20, 32, 34, "", fc="#e8f0fe", ec="#123a7a", lw=2)
ax.text(18, 51.4, "ESP32-S3-WROOM-1  (MCU + radio 2,4 GHz)", ha="center", fontsize=10, weight="bold")
ax.text(3.4, 48.6, "\n".join([
    "MCPWM unit 0 -> motor 1 | unit 1 -> motor 2",
    "        (3 operadores x par H/L, dead-time em HW)",
    "LEDC 8 canais -> motores 3 e 4 (2 timers x 3)",
    "        portadoras defasadas 90 graus entre motores",
    "            -> ripple no banco 4,5x menor (calc.)",
    "ADC 12 bits (trigger sincrono ao PWM):",
    "        12x corrente de fase + 12x BEMF",
    "VBAT sense (divisor 100k/13,7k + RC 132 Hz)",
    "I2C -> IMU 6 eixos + barometro (3,3 V_A)",
    "USB nativo D+/D- -> USB-C (so' programacao)",
    "GPIO: LED, buzzer, botao, canal de failsafe",
]), fontsize=7.6, va="top", linespacing=1.62)
box(3.5, 21.4, 29, 7.4, "PILHA DE CONTROLE (firmware)\nIMU 1-4 kHz -> PID de atitude -> setpoint de motor\nWiFi/ESP-NOW so' para COMANDOS (20-50 Hz)\nFAILSAFE: timeout 200 ms -> corta os motores",
    fc="#f2f4f7", ec="#5a5a5a", fs=7.5)

# PWM MCU -> potencia
for i, yc in enumerate([52.5, 44.5, 36.5, 28.5]):
    arrow(34.2, yc + 3.2, 52.8, yc + 3.0, color="#1e5c33", lw=1.2, rad=-0.06)
lab(43, 47.5, "6x PWM por motor\n(dead-time no driver)", fs=7.4, color="#1e5c33")
    # sensoriamento volta
arrow(53.0, 23.6, 34.2, 23.6, color="#8a6100", lw=1.3, rad=0.0)
lab(43.6, 22.3, "12x corrente de fase + 12x BEMF (trigger sincrono ao PWM)", fs=7.4, color="#8a6100")

# ---------------- energia
box(36, 3, 26, 15, "", fc="#fff7e6", ec="#8a6100", lw=1.6)
ax.text(49, 16.4, "REGULACAO DE ENERGIA", ha="center", fontsize=10, weight="bold")
ax.text(37.2, 14.2, "\n".join([
    "BUCK 12 V / 0,60 A -> 12 gate drivers (49 mA)",
    "BUCK 5 V  / 2,00 A -> 3,3 V buck, LDO anal., USB",
    "BUCK 3,3 V/ 1,50 A -> MCU+radio (pico 0,52 A)",
    "LDO 3,3 V_A/0,15 A -> IMU/barometro (baixo ruido)",
]), fontsize=7.5, va="top", linespacing=1.7)
ax.plot([44.5, 44.5], [58.0, 18.3], color="#8c2f2f", lw=2.0, ls="-", zorder=1)
arrow(44.5, 18.3, 44.5, 18.1, color="#8c2f2f", lw=2.0)
lab(45.8, 40, "VBAT", fs=7, color="#8c2f2f", rot=90)
arrow(36.1, 10, 34.3, 26, color="#8a6100", lw=1.2, rad=-0.15)
lab(33.0, 17.0, "3,3 V", fs=7, color="#8a6100", rot=90)

# ---------------- perifericos
box(64, 3, 15, 15, "SENSORES A BORDO\nIMU 6 eixos\n(SPI/I2C)\nbarometro (I2C)\nopcional:\nmagnetometro/GPS", fc="#f0ecfa", ec="#4b3a8f", fs=7.6)
box(81, 3, 17, 15, "USB-C + EXTRAS\nprotecao + ideal diode\n(alimenta 5 V sem bateria)\nLED + buzzer\npads I2C/SPI/UART\npad de debug/OTA", fc="#f0ecfa", ec="#4b3a8f", fs=7.6)
arrow(34.2, 21.0, 63.9, 12.5, color="#4b3a8f", lw=1.1, rad=0.08)
lab(49, 8.5, "I2C / SPI", fs=7, color="#4b3a8f")

ax.text(50, 0.9, "Fase 0 -- rascunho de arquitetura. Numeros conforme dimensionamento_fase0_saida_v2.txt e "
                 "verifica_limites_saida_v4.txt. Nenhum valor medido em bancada.",
        ha="center", fontsize=7.4, color="#777")
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrama_blocos_fase0_v2.png"), dpi=150)
print("ok")
