#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gera_tabela.py -- monta a tabela ESPERADO x MEDIDO x ERRO lendo os .log
reais que o ngspice gerou, e escreve resultados_fase2_spice.csv.

NENHUM valor "medido" e digitado a mao: todos sao extraidos por regex dos
arquivos buck12.log, buck5.log, ... gerados por
    ngspice -b <circuito>.cir > <circuito>.log 2>&1
Se um valor nao for encontrado no log, o script ABORTA com erro (em vez de
inventar).  Os valores "esperados" sao os calculados analiticamente, com a
formula escrita em cada linha.
"""
import re
import sys
import csv
import os

DIR = os.path.dirname(os.path.abspath(__file__))


def ler_log(nome):
    caminho = os.path.join(DIR, nome)
    with open(caminho, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# --------------------------------------------------------------------------
# formulas dos valores esperados (analitico)
# --------------------------------------------------------------------------
D12, VIN12, L12, DCR12, R12 = 0.606, 19.8, 89e-6, 30e-3, 20.0
VOUT12_IDEAL = D12 * VIN12                                  # 11.9988
VOUT12 = VOUT12_IDEAL / (1 + (1e-3 + DCR12) / R12)          # 11.980229
I12 = VOUT12 / R12                                          # 0.5990115
TON12 = D12 / 500e3
DIL12 = (VIN12 - I12 * 1e-3 - VOUT12 - I12 * DCR12) * TON12 / L12
VSW12 = D12 * VIN12 - I12 * 1e-3

D5, VIN5, L5, R5 = 0.417, 12.0, 17e-6, 2.5
VOUT5 = D5 * VIN5 / (1 + 1e-3 / R5)
I5 = VOUT5 / R5
DIL5 = (VIN5 - I5 * 1e-3 - VOUT5) * (D5 / 500e3) / L5

D3, VIN3, L3, R3 = 0.66, 5.0, 5e-6, 2.2
VOUT3 = D3 * VIN3 / (1 + 1e-3 / R3)
I3 = VOUT3 / R3
DIL3 = (VIN3 - I3 * 1e-3 - VOUT3) * (D3 / 500e3) / L3

# divisores (R1||R2)*C define o polo; fc = 1/(2*pi*(R1||R2)*C)
R1D, R2D, CD = 100e3, 13.7e3, 100e-9
RP_D = R1D * R2D / (R1D + R2D)
VOP_D = 25.2 * R2D / (R1D + R2D)
FC_D = 1.0 / (2 * 3.141592653589793 * RP_D * CD)
HDC_D = 20 * __import__("math").log10(R2D / (R1D + R2D))

R1B, R2B, CB = 8.2e3, 1.0e3, 1e-9
RP_B = R1B * R2B / (R1B + R2B)
VOP_B = 25.2 * R2B / (R1B + R2B)
FC_B = 1.0 / (2 * 3.141592653589793 * RP_B * CB)
HDC_B = 20 * __import__("math").log10(R2B / (R1B + R2B))

# gate drive: tau = Rg*Ciss ; t10-90 = tau*ln(9) ; droop = (Iq*t + Qg)/Cboot
TAU = 10 * 4e-9
TRISE = TAU * __import__("math").log(9)
DROOP = (0.5e-3 * 50e-6 + 40e-9) / 1e-6

# shunt: V = I*R ; ganho ideal 50 ; com ganho finito A=1e5, beta = 1/51
VSH = 30 * 0.5e-3
VOUT_SH_IDEAL = VSH * 50
ABETA = 1e5 * (1e3 / (1e3 + 50e3))
VOUT_SH_FIN = VOUT_SH_IDEAL / (1 + 1.0 / ABETA)

# protecao reversa: Rds_on = 1/(KP*(W/L)*(|Vgs|-|Vto|)) ; W/L = 100
RDS_ON = 1.0 / (28.125e-3 * 100 * (19.8 - 2.0))
IPROT = 19.8 / (10 + RDS_ON)
QUEDA = IPROT * RDS_ON

# --------------------------------------------------------------------------
# coleta dos valores medidos (parse dos logs reais)
# --------------------------------------------------------------------------
LOGS = {n: ler_log(n + ".log") for n in
        ["buck12", "buck5", "buck3v3", "divisor_vbat", "bemf_div",
         "gate_drive", "shunt_amp", "prot_inversao"]}

MED = {}
FALTANDO = []


def pega(log, chave):
    """extrai 'chave = numero' do log; aborta se nao existir"""
    m = re.search(r"^%s\s*=\s*([-+0-9.eE]+)" % re.escape(chave),
                  LOGS[log], re.M)
    if not m:
        FALTANDO.append("%s :: %s" % (log, chave))
        return None
    return float(m.group(1))


# bucks
for tag, log in [("12", "buck12"), ("5", "buck5"), ("3v3", "buck3v3")]:
    for k in ["vout_med", "vout_pp", "dil_pp", "il_med", "id1_max", "id2_max"]:
        MED["%s.%s" % (tag, k)] = pega(log, k)
MED["12.vsw_med"] = pega("buck12", "vsw_med")

# divisor_vbat: as duas linhas 'v(out) =' vem do .op e do .ac; a primeira e a do op
MED["dv.vop"] = float(re.search(r"v\(out\) = ([-+0-9.eE]+)", LOGS["divisor_vbat"]).group(1))
MED["dv.hdc"] = pega("divisor_vbat", "hdc_db")
MED["dv.fc"] = pega("divisor_vbat", "fc_3db_f")

MED["bm.vop"] = float(re.search(r"v\(out\) = ([-+0-9.eE]+)", LOGS["bemf_div"]).group(1))
MED["bm.hdc"] = pega("bemf_div", "hdc_db")
MED["bm.fc"] = pega("bemf_div", "fc_3db_f")

MED["gd.trise"] = pega("gate_drive", "tg_10_90")
MED["gd.droop"] = pega("gate_drive", "droop")

MED["sh.vsh"] = pega("shunt_amp", "vshunt")
MED["sh.vout"] = pega("shunt_amp", "vout")
MED["sh.i"] = pega("shunt_amp", "ishunt_der")

# prot_inversao: primeiro bloco = caso (a), segundo = caso (b)
blocos = LOGS["prot_inversao"].split("polaridade INVERTIDA")
rl_a = float(re.search(r"@rl\[i\] = ([-+0-9.eE]+)", blocos[0]).group(1))
qu_a = float(re.search(r"v\(vin\)-v\(load\) = ([-+0-9.eE]+)", blocos[0]).group(1))
rl_b = float(re.search(r"@rl\[i\] = ([-+0-9.eE]+)", blocos[1]).group(1))
MED["pt.i_a"], MED["pt.queda_a"], MED["pt.i_b"] = rl_a, qu_a, rl_b

if FALTANDO:
    print("ERRO: valores nao encontrados nos logs (nenhum numero inventado!):")
    for f in FALTANDO:
        print("   ", f)
    sys.exit(2)

# --------------------------------------------------------------------------
# tabela
# --------------------------------------------------------------------------
# (circuito, grandeza, esperado, medido, unidade, fonte do esperado, log, chave)
LINHAS = [
 ("buck12", "Vout media (D*Vin, ideal)", VOUT12_IDEAL, MED["12.vout_med"], "V",
  "D*Vin = 0.606*19.8", "buck12.log", "vout_med"),
 ("buck12", "Vout media (com Ron+DCR)", VOUT12, MED["12.vout_med"], "V",
  "D*Vin/(1+(Ron+DCR)/R); I=Vout/R", "buck12.log", "vout_med"),
 ("buck12", "dIL pk-pk", DIL12, MED["12.dil_pp"], "A",
  "(Vin-I*Ron-Vout-I*DCR)*Ton/L", "buck12.log", "dil_pp"),
 ("buck12", "Ripple saida pk-pk", 0.6342085e-3, MED["12.vout_pp"], "V",
  "vC+vESR ponto a ponto (minimiza_ripple.py)", "buck12.log", "vout_pp"),
 ("buck12", "iL media (=Iout)", I12, MED["12.il_med"], "A",
  "I = Vout/R", "buck12.log", "il_med"),
 ("buck12", "Vsw media", VSW12, MED["12.vsw_med"], "V",
  "D*Vin - I*Ron", "buck12.log", "vsw_med"),
 ("buck12", "Corrente max diodo de corpo D1", 0.0, MED["12.id1_max"], "A",
  "acionamento complementar exato -> nunca conduz", "buck12.log", "id1_max"),
 ("buck12", "Corrente max diodo de corpo D2", 0.0, MED["12.id2_max"], "A",
  "acionamento complementar exato -> nunca conduz", "buck12.log", "id2_max"),

 ("buck5", "Vout media (com Ron)", VOUT5, MED["5.vout_med"], "V",
  "D*Vin/(1+Ron/R)", "buck5.log", "vout_med"),
 ("buck5", "Vout media (D*Vin, ideal)", D5 * VIN5, MED["5.vout_med"], "V",
  "D*Vin = 0.417*12", "buck5.log", "vout_med"),
 ("buck5", "dIL pk-pk (calculado dos parametros dados)", DIL5, MED["5.dil_pp"], "A",
  "(Vin-I*Ron-Vout)*Ton/L", "buck5.log", "dil_pp"),
 ("buck5", "dIL pk-pk (numero citado no enunciado)", 0.246, MED["5.dil_pp"], "A",
  "VALOR DO ENUNCIADO - inconsistente, ver relatorio", "buck5.log", "dil_pp"),
 ("buck5", "Ripple saida pk-pk", 2.0471545e-3, MED["5.vout_pp"], "V",
  "minimiza_ripple.py", "buck5.log", "vout_pp"),
 ("buck5", "iL media (=Iout)", I5, MED["5.il_med"], "A", "I = Vout/R",
  "buck5.log", "il_med"),

 ("buck3v3", "Vout media (com Ron)", VOUT3, MED["3v3.vout_med"], "V",
  "D*Vin/(1+Ron/R)", "buck3v3.log", "vout_med"),
 ("buck3v3", "Vout media (D*Vin, ideal)", D3 * VIN3, MED["3v3.vout_med"], "V",
  "D*Vin = 0.66*5", "buck3v3.log", "vout_med"),
 ("buck3v3", "dIL pk-pk (calculado dos parametros dados)", DIL3, MED["3v3.dil_pp"], "A",
  "(Vin-I*Ron-Vout)*Ton/L", "buck3v3.log", "dil_pp"),
 ("buck3v3", "dIL pk-pk (numero citado no enunciado)", 0.178, MED["3v3.dil_pp"], "A",
  "VALOR DO ENUNCIADO - inconsistente, ver relatorio", "buck3v3.log", "dil_pp"),
 ("buck3v3", "Ripple saida pk-pk", 2.6875125e-3, MED["3v3.vout_pp"], "V",
  "minimiza_ripple.py", "buck3v3.log", "vout_pp"),
 ("buck3v3", "iL media (=Iout)", I3, MED["3v3.il_med"], "A", "I = Vout/R",
  "buck3v3.log", "il_med"),

 ("divisor_vbat", "Vout .op (Vin=25.2 V)", VOP_D, MED["dv.vop"], "V",
  "Vin*R2/(R1+R2)", "divisor_vbat.log", "v(out)"),
 ("divisor_vbat", "Ganho DC", HDC_D, MED["dv.hdc"], "dB",
  "20*log10(R2/(R1+R2))", "divisor_vbat.log", "hdc_db"),
 ("divisor_vbat", "fc (-3 dB)", FC_D, MED["dv.fc"], "Hz",
  "1/(2*pi*(R1||R2)*C)", "divisor_vbat.log", "fc_3db_f"),

 ("bemf_div", "Vout .op (Vin=25.2 V)", VOP_B, MED["bm.vop"], "V",
  "Vin*R2/(R1+R2)", "bemf_div.log", "v(out)"),
 ("bemf_div", "Ganho DC", HDC_B, MED["bm.hdc"], "dB",
  "20*log10(R2/(R1+R2))", "bemf_div.log", "hdc_db"),
 ("bemf_div", "fc (-3 dB)", FC_B, MED["bm.fc"], "Hz",
  "1/(2*pi*(R1||R2)*C)", "bemf_div.log", "fc_3db_f"),

 ("gate_drive", "Tempo de subida do gate 10-90%", TRISE, MED["gd.trise"], "s",
  "Rg*Ciss*ln(9) = 2.1972*40n", "gate_drive.log", "tg_10_90"),
 ("gate_drive", "Droop do bootstrap em 50 us", DROOP, MED["gd.droop"], "V",
  "(Iq*ton + Qg)/Cboot = 65nC/1uF", "gate_drive.log", "droop"),

 ("shunt_amp", "Tensao no shunt", VSH, MED["sh.vsh"], "V",
  "I*Rsh = 30*0.5m", "shunt_amp.log", "vshunt"),
 ("shunt_amp", "Vout (ganho ideal 50)", VOUT_SH_IDEAL, MED["sh.vout"], "V",
  "50*Vshunt (valor do enunciado)", "shunt_amp.log", "vout"),
 ("shunt_amp", "Vout (com ganho finito A=1e5)", VOUT_SH_FIN, MED["sh.vout"], "V",
  "G/(1+1/(A*beta)); beta=1/51", "shunt_amp.log", "vout"),
 ("shunt_amp", "Corrente no shunt (derivada de Vshunt/Rsh)", 30.0, MED["sh.i"], "A",
  "I nominal da fonte PULSE", "shunt_amp.log", "ishunt_der"),

 ("prot_inversao", "Caso (a) corrente na carga", IPROT, MED["pt.i_a"], "A",
  "19.8/(10+Rds_on); Rds_on=1/(KP*(W/L)*(|Vgs|-|Vto|))", "prot_inversao.log", "@rl[i]"),
 ("prot_inversao", "Caso (a) queda dreno-source", QUEDA, MED["pt.queda_a"], "V",
  "I*Rds_on = 1.976*20.02m", "prot_inversao.log", "v(vin)-v(load)"),
 ("prot_inversao", "Caso (b) corrente na carga (bloqueio)", 1e-12, MED["pt.i_b"], "A",
  "Is do diodo de corpo reverso (criterio: < 1 mA)", "prot_inversao.log", "@rl[i]"),
]

with open(os.path.join(DIR, "resultados_fase2_spice.csv"), "w", newline="",
          encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["circuito", "grandeza", "esperado", "medido",
                "erro_relativo_pct", "fonte_do_esperado", "log", "chave_no_log"])
    for circ, grande, esp, med, un, fonte, log, chave in LINHAS:
        if med is None:
            continue
        if esp == 0:
            erro = "n/a (esperado=0)"
        else:
            erro = "%.6g" % (abs(med - esp) / abs(esp) * 100.0)
        w.writerow([circ, grande, "%.10g" % esp, "%.10g" % med, erro, fonte, log, chave])

print("CSV gravado: resultados_fase2_spice.csv  (%d linhas)" % len(LINHAS))
print()
print("| circuito | grandeza | esperado | medido | erro |")
print("|---|---|---|---|---|")
for circ, grande, esp, med, un, fonte, log, chave in LINHAS:
    if med is None:
        continue
    if esp == 0:
        erro = "0 (exato)" if med == 0 else "MEDIDO!=0"
    else:
        e = abs(med - esp) / abs(esp) * 100.0
        erro = "%.5g%%" % e if e >= 1e-6 else "%.2e%%" % e
    print("| %s | %s | %s | %s | %s |" % (
        circ, grande,
        ("%.6g %s" % (esp, un)).replace("e-", "e-"),
        "%.6g %s" % (med, un), erro))
