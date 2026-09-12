#!/usr/bin/env python3
"""Fase 0 - diagrama de blocos do drone (headless, matplotlib Agg)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

fig, ax = plt.subplots(figsize=(17, 11.5))
ax.set_xlim(0, 100); ax.set_ylim(0, 74); ax.axis("off")

def box(x, y, w, h, text, fc="#eef3fb", ec="#1f3b6e", fs=8.5, lw=1.4, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.2",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs,
            zorder=3, weight="bold" if bold else "normal", linespacing=1.35)

def arrow(x1, y1, x2, y2, color="#1f3b6e", style="-|>", lw=1.4, ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, color=color,
                                 lw=lw, linestyle=ls, mutation_scale=13, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))

def lab(x, y, t, fs=7.4, color="#1f3b6e", rot=0, ha="center"):
    ax.text(x, y, t, fontsize=fs, color=color, ha=ha, va="center", rotation=rot, zorder=4)

ax.text(50, 72.2, "DRONE 4x ESC TRIFASICO + MCU WiFi -- DIAGRAMA DE BLOCOS (Fase 0)",
        ha="center", fontsize=15, weight="bold")
ax.text(50, 69.6, "PCB unica | bateria 6S (18,0-25,2 V) | 4 motores brushless | controle por WiFi/ESP-NOW",
        ha="center", fontsize=9.5, color="#555")

# ---------------- ENTRADA / PROTEÇÃO
box(2, 58, 15, 8, "XT60\n(entrada bateria)\n6S = 18,0-25,2 V", fc="#fdecec", ec="#8c2f2f")
box(19.5, 58, 17, 8, "PROTECAO\nTVS (clamp ~38 V)\nP-FET anti-inversao\nfusivel/e-fuse opcional", fc="#fdecec", ec="#8c2f2f")
box(39, 58, 15, 8, "BANCO DE ENTRADA\n6x 470 uF polimero\n+ 10 uF + 100 nF\npor par de MOSFET", fc="#fdecec", ec="#8c2f2f")
arrow(17, 62, 19.4, 62); arrow(36.5, 62, 38.9, 62)

# barramento
ax.plot([54, 97], [62, 62], color="#8c2f2f", lw=6, zorder=1, solid_capstyle="round")
lab(75.5, 63.8, "BARRAMENTO VBAT (2 oz, camada interna + costura de vias)", fs=8, color="#8c2f2f")
arrow(54.1, 62, 54.1, 62)

# ---------------- 4 ESC
for i in range(4):
    y = 44 - i * 8.6
    box(53, y, 20, 7.4, f"ESC {i+1}\n3x gate driver (bootstrap)\n6x MOSFET N 40-60 V", fc="#eef7ee", ec="#1e5c33")
    box(75, y, 11, 7.4, "3x SHUNT\n0,5 mOhm\nlow-side", fc="#fff7e6", ec="#8a6100")
    box(88, y, 10, 7.4, f"MOTOR {i+1}\nconector 3 pinos", fc="#f0ecfa", ec="#4b3a8f")
    arrow(64, y + 3.7, 64, 45.7 + (3 if i == 0 else 0), color="none")   # placeholder
    arrow(73.1, y + 3.7, 74.9, y + 3.7); arrow(86.1, y + 3.7, 87.9, y + 3.7)
    arrow(64, y + 7.5, 64, y + 9.7 if i < 3 else y + 7.5, color="#8c2f2f", lw=2.2)
    lab(66.5, y + 8.2, "VBAT", fs=7, color="#8c2f2f")

# ---------------- MCU
box(2, 12, 30, 30, "", fc="#e8f0fe", ec="#123a7a", lw=2)
ax.text(17, 39.5, "ESP32-S3-WROOM-1  (MCU + radio 2,4 GHz)", ha="center", fontsize=10, weight="bold")
linhas = [
    "MCPWM unit 0: motor 1 (3 pares H/L + dead-time HW)",
    "MCPWM unit 1: motor 2",
    "LEDC 8 canais: motores 3 e 4 (2 timers x 3 canais)",
    "  -> portadoras defasadas 90 graus (ripple 4,5x menor)",
    "ADC1/ADC2 (12 bits): 12x corrente de fase,",
    "  3x BEMF por motor, VBAT sense, temperatura",
    "I2C: IMU + barometro   | SPI/UART: pads expostos",
    "USB nativo (D+/D-) -> USB-C, so' programacao",
    "GPIO: LED, buzzer, botao, canal de failsafe",
]
ax.text(3.4, 36.0, "\n".join(linhas), ha="left", va="top", fontsize=8.2, linespacing=1.75)

box(2, 2.5, 30, 8, "PILHA DE CONTROLE (firmware)\nIMU 1-4 kHz -> PID de atitude -> setpoint de motor\ncomandos por WiFi/ESP-NOW a 20-50 Hz | FAILSAFE por timeout (200 ms) -> corta motores",
    fc="#f2f4f7", ec="#5a5a5a", fs=8)

# ---------------- SENSORES / PERIFÉRICOS
box(36, 2.5, 24, 8, "SENSORES A BORDO\nIMU 6 eixos (SPI/I2C) + barometro (I2C)\nopcional: magnetometro / GPS (pad UART)", fc="#f0ecfa", ec="#4b3a8f")
box(63, 2.5, 16, 8, "USB-C\nprotecao + ideal diode\nalimenta 5 V sem bateria", fc="#f0ecfa", ec="#4b3a8f")
box(82, 2.5, 16, 8, "EXTRA\nLED + buzzer\npad I2C/SPI/UART\npad de debug/OTA", fc="#f0ecfa", ec="#4b3a8f")

# ---------------- ENERGIA (bucks)
box(36, 24, 27, 15, "", fc="#fff7e6", ec="#8a6100", lw=1.6)
ax.text(49.5, 37.2, "REGULACAO DE ENERGIA", ha="center", fontsize=10, weight="bold")
energia = [
    "BUCK 12 V / 0,60 A  -> 12 gate drivers (49 mA)",
    "BUCK 5 V  / 2,00 A  -> 3,3 V buck, LDO analogico, USB",
    "BUCK 3,3 V / 1,50 A -> MCU+radio (pico 0,52 A), IMU",
    "LDO 3,3 V_A / 0,15 A -> IMU/barometro (baixo ruido)",
]
ax.text(37.4, 34.4, "\n".join(energia), ha="left", va="top", fontsize=8.2, linespacing=1.8)
arrow(39, 39.1, 39, 41.5, color="#8c2f2f", lw=2.2)
lab(41.5, 40.4, "VBAT", fs=7, color="#8c2f2f")
arrow(49.5, 24, 49.5, 11.2, color="#8a6100", style="<|-|>", lw=1.2)
lab(52.5, 17.5, "5 V / 3,3 V", fs=7.2, rot=90, color="#8a6100")

# ---------------- LIGAÇÕES MCU <-> ESC
for i in range(4):
    y = 44 - i * 8.6
    yy = y + 3.7
    arrow(32.2, 30 + (0 if i < 2 else -2), 52.8, yy, color="#1e5c33", lw=1.1,
          rad=-0.12 + 0.04 * i)
lab(42, 42.5, "6x PWM com dead-time por motor", fs=7.2, color="#1e5c33")
arrow(75, 44 - 0 * 8.6 + 1.2, 40.5, 20.5, color="#8a6100", lw=1.0, rad=0.08)
lab(60, 26.5, "12x corrente de fase + 12x BEMF -> ADC (trigger sincrono ao PWM)",
    fs=7.4, color="#8a6100", ha="center")

# ---------------- nota
ax.text(50, 0.5, "Rascunho de arquitetura -- nenhum numero aqui e' medicao; valores conforme "
                 "dimensionamento_fase0.py e verifica_limites_entrada_v4.py",
        ha="center", fontsize=7.6, color="#777")
plt.tight_layout()
plt.savefig("/opt/jupyter/work/drone/fase0_especificacao/diagrama_blocos_fase0.png", dpi=150)
print("ok")
