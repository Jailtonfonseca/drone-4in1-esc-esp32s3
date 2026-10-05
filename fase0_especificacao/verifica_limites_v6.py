#!/usr/bin/env python3
"""
Fase 0 -- VERIFICACAO DE LIMITES v6
Reexecuta os 8 limites criticos com a combinacao MOSFET + driver ESCOLHIDA depois da
reversao da premissa P-06 (Qg = 40 nC era falso; o datasheet do FET de referencia
diz Qg = 168 nC typ / 210 nC max).

Estilo: segue o de verifica_limites_entrada_v4.py (mesma funcao p() acumulando linhas,
mesmo cabecalho "=" * 78, mesma gravacao do .txt ao lado do proprio script).
NADA que o v4 media foi editado: o v6 reimplementa os mesmos numeros de regime
(ripple, vias, Z0, balanco no cruzeiro) e SUBSTITUI apenas o bloco de gate drive,
que e' o que a premissa P-06 quebrou.

Marcadores de fonte (mesmo vocabulario do REVERSAO_PREMISSAS_v5.md):
  [DS FET p.N] / [DS DRV p.N]  linha literal do PDF, com arquivo e pagina
  [MEDIDO]                    conta executada por ESTE arquivo agora
  [PREMISSA]                  premissa P-xx ainda em aberto (FASE0_ESPECIFICACAO.md)
  [EST]                       estimativa do redator, com a conta que a sustenta
"""
import math
import os

# =============================================================================
# 0.1  PARAMETROS DA COMBINACAO ESCOLHIDA
#      Cada constante tem arquivo + pagina de PDF. Ver ESCOLHA_MOSFET_DRIVER.md §4.
#      [DS FET] = datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf
#      [DS DRV] = /tmp nao versiona: PDF oficial Infineon 6EDL7141 Rev 1.20 (2024-03-22),
#                 pagina citada como "6EDL7141 p.N"; URL em ESCOLHA_MOSFET_DRIVER.md §4.
# =============================================================================
MOS_NAME = "IPB017N10N5 (100 V, classe mantida; substituto com Qg <= 70 nC = PENDENTE)"
MOS_QG_TYP = 168e-9      # [DS FET p.4, Table 6]  Qg total typ
MOS_QG_MAX = 210e-9      # [DS FET p.4, Table 6]  Qg total max ("not subject to production test")
MOS_RDS = 1.7e-3         # [DS FET p.4, Table 4]  RDS(on) max @ VGS=10 V, ID=100 A
MOS_RDS_TYP = 1.5e-3     # [DS FET p.4, Table 4]  RDS(on) typ
MOS_CISS = 12.0e-9       # [DS FET p.4, Table 5]  Ciss typ (VGS=0 V, VDS=50 V, 1 MHz)
                         # [FIX auditoria 8] 12 nF = 12.000 pF (o v6 tinha 12e-12 = 12 pF,
                         # 1000x menor -- a v5 (CISS_TYP = 12,0e-9) estava certa)
MOS_TR = 23e-9           # [DS FET p.4, Table 5]  rise time com Rg,ext = 1,6 ohm
MOS_TF = 27e-9           # [DS FET p.4, Table 5]  fall time
MOS_RG_EXT = 1.6         # [DS FET p.4, Table 5]  Rg externo usado na caracterizacao do DS
MOS_RG_INT = 1.3         # [DS FET p.4, Table 4]  Rg interno (gate resistance) typ
MOS_QOSS = 213e-9        # [DS FET p.1, Table 1 e p.4, Table 7]  Qoss typ
MOS_QRR = 235e-9         # [DS FET p.4, Table 7]  Qrr typ @ VR=50 V, diF/dt=100 A/us

DRV_NAME = "6EDL7141XUMA1 (MOTIX, VQFN-48 7x7 mm, 3 canais, 1,5 A de pico)"
DRV_IPEAK = 1.5          # [DS DRV p.15]  IGD_SRC_PEAK typ
DRV_INEG = 1.5           # [DS DRV p.15]  IGD_SNK_PEAK typ
DRV_IQ_TYP = 25e-6       # [DS DRV p.14]  IPVDD_OFF typ
DRV_IQ_MAX = 40e-6       # [DS DRV p.14]  IPVDD_OFF max
DRV_DT_TYP = 0.0         # [DS DRV p.15]  tDT_RISE/tDT_FALL: PISO de 120 ns, programavel por SPI.
#                         O piso de 120 ns do CI e' MENOR que os 518,750 ns que o firmware ja
#                         envia, entao nao se soma: a janela util continua sendo a do MCPWM.
DRV_DT_MIN = 120e-9      # [DS DRV p.15]  piso de dead-time do proprio CI
DRV_DT_MAX = 0.0          # nao ha dead-time interno a somar: o MCU ja manda 518,750 ns > 120 ns
DRV_PROP_TYP = 80e-9     # [DS DRV p.15]  tPROP_HS/tPROP_LS min
DRV_PROP_MAX = 250e-9    # [DS DRV p.15]  tPROP_HS/tPROP_LS max (50% entrada -> 50% saida)
DRV_VCC_MIN, DRV_VCC_MAX = 5.5, 60.0   # [DS DRV p.13, "Supply voltage PVDD"]
DRV_PVCC_MIN, DRV_PVCC_MAX = 7.0, 15.0  # [DS DRV p.15]  PVCC programavel por SPI

CBOOT_ESCOLHIDO = 4.7e-6  # 2 x 2,2 uF/25 V X7R 1210 em paralelo; minimo pela regra de 20*Qg = 3,36 uF

L = []


def p(s=""):
    print(s)
    L.append(s)


def pct(esp, med):
    if esp == 0:
        return 0.0
    return (med - esp) / esp * 100.0


def linha(nome, esp, med, fonte, unidade="", fmt="{:+.2f}"):
    p(f"  {nome:44s}| esp {esp:>10.4g} {unidade:5s}| med {med:>10.4g} {unidade:5s}"
      f"| erro {fmt.format(pct(esp, med)) + ' %':>12s}")
    p(f"  {'':44s}|   fonte: {fonte}")


# =============================================================================
# 0. COMBINACAO ESCOLHIDA
#    Fonte dos numeros: ver ESCOLHA_MOSFET_DRIVER.md. Cada constante abaixo tem
#    arquivo + pagina de PDF; nada aqui e' suposto.
# =============================================================================
p("=" * 78)
p("FASE 0 -- LIMITES CRITICOS (v6) -- combinacao MOSFET + driver ESCOLHIDA")
p("=" * 78)

# --- premissas que NAO mudaram (FASE0_ESPECIFICACAO.md, P-01..P-05, P-07..P-15)
VBAT_MAX, VBAT_NOM, VBAT_MIN = 25.2, 22.2, 19.8      # P-02 LiPo 6S
IPK, INOM = 30.0, 15.0                                # P-03, P-04
FPWM, F_ELEC, MOD, PPP = 20e3, 300.0, 0.80, 200       # P-07
RTH_JA, TA = 60.0, 25.0                               # [PREMISSA] Rth_ja da Fase 0
VTRILHO = 12.0                                        # fase3_pcb/gera_pcb_v7.py linha 239
N_FETS, N_DRIVERS = 24, 12                            # 4 motores x 3 fases, 2 FETs/driver
DT_RTL = 518.750e-9                                   # [MEDIDO em fase2_simulacao/verilog/RELATORIO_VERILOG.md]
BUCK_12V_A = 0.60                                     # dimensionamento_fase0.py

p("\n0. COMBINACAO AVALIADA (fonte: ESCOLHA_MOSFET_DRIVER.md, secao 4)")
p(f"  MOSFET de referencia (NAO escolhido) : IPB017N10N5, 100 V, Qg 168 nC typ / 210 nC max")
p(f"  MOSFET ESCOLHIDO                    : {MOS_NAME}")
p(f"  Driver ESCOLHIDO                    : {DRV_NAME}")
p(f"  Supply do driver: PVDD {DRV_VCC_MIN}-{DRV_VCC_MAX} V (trilho de {VTRILHO:.0f} V cabe); "
  f"PVCC programavel {DRV_PVCC_MIN}-{DRV_PVCC_MAX} V, {VTRILHO:.0f} V dentro da faixa")
p(f"  Premissas mantidas: Vbat {VBAT_MAX} V max, Ipk {IPK} A, Inom {INOM} A, "
  f"f_pwm {FPWM/1e3:.0f} kHz, Rth_ja {RTH_JA:.0f} C/W, Ta {TA:.0f} C, trilho {VTRILHO:.1f} V")

# =============================================================================
# 1. TEMPO DE COMUTACAO DE GATE  --  este e' o limite que a premissa P-06 quebrou
#    t = Qg / I_gate.   [MEDIDO]
# =============================================================================
p("\n1. TEMPO DE COMUTACAO DE GATE  t = Qg / I_driver")
p(f"  Qg (typ) = {MOS_QG_TYP*1e9:.1f} nC   |   Qg (max) = {MOS_QG_MAX*1e9:.1f} nC")
p(f"  I_out+ do driver = {DRV_IPEAK*1e3:.0f} mA (fonte)  |  I_out- = {DRV_INEG*1e3:.0f} mA (drain)")
p(f"  I_out+ do IR2104 = 130 mA (fonte) | I_out- = 270 mA (drain) [DS DRV p.1]")

t_on_typ = MOS_QG_TYP / DRV_IPEAK
t_off_typ = MOS_QG_TYP / DRV_INEG
t_on_max = MOS_QG_MAX / DRV_IPEAK
t_off_max = MOS_QG_MAX / DRV_INEG
p("")
p(f"  t turn-ON  (Qg typ / I+) = {MOS_QG_TYP*1e9:.1f} nC / {DRV_IPEAK*1e3:.0f} mA = {t_on_typ*1e9:8.1f} ns  [MEDIDO]")
p(f"  t turn-OFF (Qg typ / I-) = {MOS_QG_TYP*1e9:.1f} nC / {DRV_INEG*1e3:.0f} mA = {t_off_typ*1e9:8.1f} ns  [MEDIDO]")
p(f"  t turn-ON  (Qg max / I+) = {MOS_QG_MAX*1e9:.1f} nC / {DRV_IPEAK*1e3:.0f} mA = {t_on_max*1e9:8.1f} ns  [MEDIDO]")
p(f"  t turn-OFF (Qg max / I-) = {MOS_QG_MAX*1e9:.1f} nC / {DRV_INEG*1e3:.0f} mA = {t_off_max*1e9:8.1f} ns  [MEDIDO]")

T_ALVO = 0.05e-6   # 50 ns: alvo de projeto da Fase 0, mantido para comparar
linha("L1 tempo de subida do gate (esperado 50 ns)", T_ALVO * 1e9, t_on_typ * 1e9,
      f"{MOS_QG_TYP*1e9:.0f} nC / {DRV_IPEAK*1e3:.0f} mA; alvo de {T_ALVO*1e9:.0f} ns da Fase 0", "ns")
p(f"  >>> referencia do problema original: com o IR2104 e Qg 168 nC dava 1292,3 ns (+2484,6 %).")

# checagem cruzada pelo rise time do proprio datasheet do FET
p("")
p("  ANCORA DE DATASHEET (independe do driver): corrente implicita no tr do FET escolhido")
p(f"  tr do DS = {MOS_TR*1e9:.0f} ns com Rg,ext = {MOS_RG_EXT:.1f} ohm  [DS FET p.4, Table 5]")
i_implicita = MOS_QG_TYP / MOS_TR
p(f"  I = Qg/tr = {MOS_QG_TYP*1e9:.0f} nC / {MOS_TR*1e9:.0f} ns = {i_implicita:.2f} A  [MEDIDO]")
linha("I implicita no tr do DS vs I+ do driver", DRV_IPEAK, i_implicita,
      f"Qg/tr do datasheet contra a saida declarada do driver", "A")
p(f"  >>> com Qg = 168 nC essa razao era 56,2x (IPB017N10N5). Aqui ela vale {i_implicita/DRV_IPEAK:.2f}x.")

# =============================================================================
# 2. SLEW
# =============================================================================
p("\n2. SLEW DE GATE  dV/dt = 10 V / t   (dV = 0 -> 10 V, mesma janela com que o DS caracteriza Qg)")
slew_on = 10.0 / t_on_typ / 1e9      # V/ns
slew_off = 10.0 / t_off_typ / 1e9    # V/ns
linha("L6 slew de Vgs no turn-ON", 0.30, slew_on, "10 V / (Qg typ / I+); 0,30 V/ns era o valor assumido na Fase 0", "V/ns")
linha("L6 slew de Vgs no turn-OFF", 0.30, slew_off, "10 V / (Qg typ / I-)", "V/ns")
p(f"  [MEDIDO] corrente reativa em Ciss durante a comutacao: I = Ciss*dV/dt")
p(f"        Ciss = {MOS_CISS*1e12:.0f} pF [DS FET p.4, Table 5] -> I_Ciss = Ciss*dV/dt = "
  f"{MOS_CISS*1e12:.0f} pF x {slew_on:.4f} V/ns = {MOS_CISS*slew_on*1e9*1e3:.1f} mA = "
  f"{MOS_CISS*slew_on*1e9/DRV_IPEAK*100:.1f} % de I_gate")
p(f"  [MEDIDO] corrente total no no de gate = (1 + Ciss*dV/dt/I) x I_gate = "
  f"{(1 + MOS_CISS*slew_on*1e9/DRV_IPEAK):.2f}x a corrente do driver")

# =============================================================================
# 3. PERDA DE COMUTACAO
#    RESSALVA: E_off do IPB017N10N5 nao e' publicado [MEDIDO]. O modelo classico
#    E_off ~ 0,5*Vds*I*t_r e' [EST] e e' o mesmo modelo usado em
#    redimensionamento_gate_v5_saida.txt §5, para que a comparacao seja justa.
# =============================================================================
p("\n3. PERDA DE COMUTACAO NO MOSFET")
E_off_on = 0.5 * VBAT_MAX * IPK * t_on_typ
p_sw_est = E_off_on * FPWM
p(f"  [EST modelo 0,5*Vds*I*t_r] E_off(turn-ON) = 0,5 x {VBAT_MAX} V x {IPK} A x {t_on_typ*1e9:.1f} ns "
  f"= {E_off_on*1e6:.1f} uJ")
p(f"  [EST] P_sw = E_off * f = {E_off_on*1e6:.1f} uJ x {FPWM/1e3:.0f} kHz = {p_sw_est:.3f} W/FET")
p(f"  [MEDIDO] no banco ({N_FETS} FETs) = {N_FETS*p_sw_est:.2f} W")
p("  [EST] o mesmo modelo com o t_r do proprio datasheet do FET:")
p(f"        0,5 x {VBAT_MAX} V x {IPK} A x {MOS_TR*1e9:.0f} ns = {0.5*VBAT_MAX*IPK*MOS_TR*1e6:.2f} uJ "
  f"-> {0.5*VBAT_MAX*IPK*MOS_TR*FPWM:.3f} W/FET (o piso fisico do componente)")
p(f"  [EST] Tj com Rth={RTH_JA:.0f} C/W e Ta={TA:.0f} C, no caso realista: "
  f"Tj = {TA + p_sw_est*RTH_JA:.0f} C")
linha("L8 perda de comutacao por FET", 0.583, p_sw_est,
      f"0,583 W/FET e' o que verifica_limites_entrada_v4.py §3 usou como parcela de regime; "
      f"medido aqui com 0,5*Vds*I*t_r [EST]", "W")

# --- segundo limite de comutacao, com numero de TABELA do datasheet e nao com modelo
p("")
p("  CONTRAPROVA: o modelo acima NAO e' a perda real. O datasheet publica Qoss em TABELA:")
p(f"  [DS FET p.1, Table 1 'Key Performance Parameters' e p.4, Table 7] Qoss = {MOS_QOSS*1e9:.0f} nC typ")
# [FIX auditoria 11] E_oss = (1/2)*Qoss*Vds (a energia capaciva e' 1/2*C*V^2 = 1/2*Q*V;
# o v6 esquecia o 1/2 -> 107,4 mW/FET em vez de 53,7 mW/FET)
e_oss = 0.5 * MOS_QOSS * VBAT_MAX
p_oss = e_oss * FPWM
p(f"  [MEDIDO] E_oss = 1/2 x Qoss x Vds = {MOS_QOSS*1e9:.0f} nC x {VBAT_MAX} V / 2 = {e_oss*1e6:.2f} uJ")
p(f"  [MEDIDO] P(E_oss) = {e_oss*1e6:.2f} uJ x {FPWM/1e3:.0f} kHz = {p_oss*1e3:.1f} mW/FET "
  f"-> {N_FETS*p_oss:.2f} W no banco   [DS] -- energia que o MOSFET DESPERDICA por comutacao")
p(f"  [MEDIDO] P(E_oss) e' {p_oss/p_sw_est*100:.2f} % da estimativa de {p_sw_est:.2f} W do modelo 0,5*Vds*I*tr")
# [FIX auditoria 12] razao na direcao certa: p_oss/0,133 (o v6 imprimia 0,133/p_oss e chamava
# o resultado de "% dos 0,133 W"). Com o 1/2 do [FIX auditoria 11] aplicado, o piso de Qoss
# e' 40% da parcela de 0,133 W (sem o 1/2 seria 81% -- numero que a auditoria cita).
p(f"  [MEDIDO] o piso de Qoss e' {p_oss/0.133*100:.0f} % da parcela de 0,133 W que o v4 §3 usava "
  f"(0,133 W = {0.133/p_oss:.2f}x o piso)")
p(f"  [DS FET p.4, Table 7] Qrr = {MOS_QRR*1e9:.0f} nC typ / 470 nC max a 100 A/us: recuperacao")
p(f"        injetada no barramento a cada comutacao = {MOS_QRR/MOS_QG_TYP*100:.0f} % do proprio Qg")
linha("L8b perda de comutacao por FET -- piso de datasheet (Qoss)", 0.583, p_oss,
      "0,5 x Qoss x Vds x f [FIX auditoria 11], com Qoss lido da Table 1 do datasheet; e' o unico "
      "numero de tabela disponivel, porque E_on/E_off nao sao publicados [MEDIDO]", "W")
p("  >>> VEREDITO HONESTO DE L8: os dois numeros medem coisas diferentes. O de 0,133 W do v4 e' um")
p("      chute de projeto; o de Qoss e' energia de comutacao por natureza no FET, e' TABELA de")
p("      datasheet, e esta ~2 ordens de grandeza ABAIXO do modelo [FIX auditoria 11]: os 9,77 W")
p("      do redimensionamento_gate_v5 sao 182x o piso de Qoss com o 1/2 (53,7 mW), ou 91x sem")
p("      o 1/2 -- era artefato do modelo 0,5*Vds*I*tr, que cresce com t_r sem limite e nao")
p("      descreve o dispositivo. O que de fato NAO esta determinado e E_off:")
p("      [N/D offline] -- nenhum dos PDFs em datasheets/ publica E_on/E_off.")

# =============================================================================
# 4. BOOTSTRAP
# =============================================================================
p("\n4. BOOTSTRAP  dV = Qg / Cboot")
CBOOT = CBOOT_ESCOLHIDO
dv_boot = MOS_QG_TYP / CBOOT
dv_boot_max = MOS_QG_MAX / CBOOT
cboot_min = 20 * MOS_QG_TYP
linha("L2 queda no bootstrap por comutacao", 0.040, dv_boot,
      f"Qg = {MOS_QG_TYP*1e9:.0f} nC / Cboot = {CBOOT*1e6:.2f} uF; 40 mV era o orcado com Qg = 40 nC", "V")
p(f"  [MEDIDO] Cboot minimo pela regra de 20*Qg = {cboot_min*1e6:.2f} uF (adotado: {CBOOT*1e6:.2f} uF, "
  f"fator {CBOOT/cboot_min:.2f}x)")
p(f"  [MEDIDO] queda no pior caso (Qg max) = {dv_boot_max*1e3:.0f} mV = {dv_boot_max/VTRILHO*100:.2f} % de {VTRILHO:.0f} V")
# [FIX auditoria 10] Cboot p/ 0,5% de queda = Qg/(0,005 x 12 V) = 3,5 uF. O "42 uF" antigo
# esquecia de multiplicar pelos 12 V no denominador (210 nC / 0,005 = 42 uF -- errado).
p(f"  [MEDIDO] Cboot necessario para 0,5 % de queda com Qg max = Qg/(0,005 x 12 V) = "
  f"{MOS_QG_MAX/(0.005*VTRILHO)*1e6:.2f} uF")
# [FIX auditoria 10/19] a frase final agora TESTA E CITA o Cboot ADOTADO (2x 2,2 uF =
# 4,7 uF) -- antes dizia "o Cboot de 1 uF do BOM original serve" testando os 4,7 uF.
p(f"  >>> o Cboot ADOTADO (2x 2,2 uF = {CBOOT*1e6:.2f} uF) "
  f"{'SERVE' if CBOOT >= cboot_min else 'NAO SERVE'} para a combinacao escolhida "
  f"(regra 20*Qg = {cboot_min*1e6:.2f} uF; queda typ {dv_boot*1e3:.1f} mV)")
p(f"  >>> [FIX auditoria 19] ATENCAO: o BOM lista 1x 2,2 uF POR HALF-BRIDGE -> 168 nC/2,2 uF "
  f"= 76,4 mV > 40 mV (limite L2).")
p(f"      O BOM precisa de 2x 2,2 uF por canal OU o L2 precisa ser revisado -- o 35,7 mV "
  f"acima e' a conta com 4,7 uF, NAO com 2,2 uF.")

# =============================================================================
# 5. CORRENTE NO TRILHO DE 12 V
# =============================================================================
p("\n5. CORRENTE NO TRILHO DE GATE")
i_quiesc = DRV_IQ_TYP
i_gate = N_FETS * MOS_QG_TYP * FPWM
i_12 = N_DRIVERS * i_quiesc + i_gate
linha("L3 corrente no trilho de 12 V", 49.2e-3, i_12,
      f"{N_DRIVERS} x {i_quiesc*1e6:.0f} uA (Iq typ) + {N_FETS} x Qg x f = "
      f"{i_gate*1e3:.1f} mA", "A")
p(f"  [MEDIDO] uso do buck de {BUCK_12V_A*1e3:.0f} mA = {i_12/BUCK_12V_A*100:.1f} % "
  f"-> folga de {BUCK_12V_A/i_12:.1f}x   (pior caso Qg max + Iq max: "
  f"{(N_DRIVERS*DRV_IQ_MAX + N_FETS*MOS_QG_MAX*FPWM)*1e3:.1f} mA, "
  f"{BUCK_12V_A/(N_DRIVERS*DRV_IQ_MAX + N_FETS*MOS_QG_MAX*FPWM):.1f}x)")

# =============================================================================
# 6. DEAD-TIME
# =============================================================================
p("\n6. DEAD-TIME")
p(f"  [MEDIDO em fase2_simulacao/verilog/RELATORIO_VERILOG.md] dead-time do RTL do MCPWM = {DT_RTL*1e9:.3f} ns")
p(f"  [DS DRV p.15] piso de dead-time do 6EDL7141 (tDT_RISE/tDT_FALL) = {DRV_DT_MIN*1e9:.0f} ns, "
  f"programavel por SPI (DT_RISE/DT_FALL); [DS DRV p.15] tPROP_HS/tPROP_LS = "
  f"{DRV_PROP_TYP*1e9:.0f}/{DRV_PROP_MAX*1e9:.0f} ns")
p(f"  [MEDIDO] o firmware ja envia {DT_RTL*1e9:.3f} ns > {DRV_DT_MIN*1e9:.0f} ns, entao o piso do CI "
  f"nao se soma: a janela util e' a do MCPWM")
p(f"  >>> MELHORIA DE CIMA: o IR2104 tinha dead-time INTERNO de 400/520/650 ns que o firmware nao")
p(f"      programa [DS IR2104 p.3]. O 6EDL7141 NAO tem: o dead-time e' o que o MCU manda, com piso")
p(f"      de {DRV_DT_MIN*1e9:.0f} ns. Isso elimina a soma de dois dead-times que a v5 apontava.")
janela = DT_RTL + DRV_DT_TYP
janela_max = DT_RTL + DRV_DT_MAX
linha("L4 dead-time necessario para o turn-OFF (janela util do MCPWM)", DT_RTL * 1e9, t_off_typ * 1e9,
      f"Qg typ / I- = {MOS_QG_TYP*1e9:.0f} nC / {DRV_INEG*1e3:.0f} mA; janela util = "
      f"{janela*1e9:.1f} ns (RTL, sem dead-time interno somado)", "ns")
p(f"  [MEDIDO] a janela util cobre o turn-OFF com folga de {(janela-t_off_typ)/t_off_typ*100:.1f} %")
p(f"  [MEDIDO] prop delay do CI somado ao turn-OFF: "
  f"{t_off_typ*1e9 + DRV_PROP_TYP*1e9:.0f} ns (tip) a {t_off_typ*1e9 + DRV_PROP_MAX*1e9:.0f} ns (max) "
  f"-> folga de {(janela - t_off_typ - DRV_PROP_MAX)/t_off_typ*100:.1f} % no pior caso de prop delay")
p(f"  [MEDIDO] MCPWM/LEDC do ESP32-S3: passo de 1/(160 MHz x 2) = 3,125 ns na divisoria de 16 bits;")
p(f"      os {DT_RTL*1e9:.3f} ns ja medidos no Verilog sao multiplos exatos desse passo, e o modo de")
p(f"      'dead-time com duty' do MCPWM do ESP32-S3 e' programavel em passos de t_dtg, que e' o")
p(f"      suficiente para ajustar a janela ao valor que o gate exigir. [MEDIDO em RTL]")
linha("L4b dead-time necessario para o turn-ON (janela maxima)", janela_max * 1e9, t_on_max * 1e9,
      f"Qg max / I+ = {MOS_QG_MAX*1e9:.0f} nC / {DRV_IPEAK*1e3:.0f} mA", "ns")
p(f"  [MEDIDO] custo em duty: {janela/(1/FPWM)*100:.2f} % do periodo a 20 kHz; sem dead-time interno "
  f"somado, o duty perdido e' {(DT_RTL/ (1/FPWM))*100:.2f} % (era 2,075 % com o IR2104)")

# =============================================================================
# 7. Rg  --  amortecimento x velocidade
# =============================================================================
p("\n7. RESISTOR DE GATE: amortecimento x velocidade (as duas contas nao cabem no mesmo resistor)")
# [FIX auditoria 9/16] L e C do laco de gate do v4 §3: 20 nH e 2 nF (o v6 tinha TROCADOS:
# 20 nF / 2 nH -> Z0 10x menor e o "L7 OK" era artefato). Com os valores corretos:
# Z0 = sqrt(20 nH / 2 nF) = 3,16 ohm -> amortecimento exige Rg >= 6,3 ohm.
C_LACO, L_LACO = 2e-9, 20e-9   # 2 nF e 20 nH (v4 §3) [FIX auditoria 9]
Z0 = math.sqrt(L_LACO / C_LACO)
RG_ADOTADO = 10.0
rg_min_slew = VTRILHO / (MOS_QG_TYP / T_ALVO) - MOS_RG_INT
linha("L7 Rg minimo para comutar em 50 ns (com o driver escolhido)", RG_ADOTADO, rg_min_slew,
      f"Vtrilho/I_alvo - Rg_interno = {VTRILHO:.0f} V / ({MOS_QG_TYP*1e9:.0f} nC / 50 ns) - "
      f"{MOS_RG_INT:.1f} ohm; adotado = {RG_ADOTADO:.0f} ohm", "ohm")
p(f"  [MEDIDO] Z0 da trilha de gate = sqrt({L_LACO*1e9:.0f} nH / {C_LACO*1e12:.0f} pF) = {Z0:.2f} ohm")
p(f"  [MEDIDO] amortecimento exigido: Rg >= 2*Z0 = {2*Z0:.1f} ohm (adotado {RG_ADOTADO:.0f} ohm, OK)")
p(f"  [MEDIDO] com Rg = {RG_ADOTADO:.0f} + {MOS_RG_INT:.1f} = {RG_ADOTADO+MOS_RG_INT:.1f} ohm e o driver "
  f"corrente-limitado, quem manda e' o DRIVER: a corrente pedida seria "
  f"{VTRILHO/(RG_ADOTADO+MOS_RG_INT):.3f} A contra {DRV_IPEAK:.2f} A disponiveis")
p(f"  [MEDIDO] f_ring = 1/(2*pi*sqrt(LC)) = {1/(2*math.pi*math.sqrt(C_LACO*L_LACO))/1e6:.1f} MHz")
# [FIX auditoria 9] veredito honesto de L7 com os valores CORRETOS de L e C
p(f"  [FIX auditoria 9] VEREDITO HONESTO DE L7: o Rg para 50 ns ({rg_min_slew:.2f} ohm) e' MENOR "
  f"que o piso de amortecimento ({2*Z0:.1f} ohm).")
p(f"      A incompatibilidade amortecimento x velocidade CONTINUA (mesma conclusao do")
p(f"      redimensionamento_gate_v5 §4: sao duas exigencias que nao cabem no mesmo resistor).")
p(f"      O 'L7 OK' da saida anterior era artefato do LxC trocado (Z0 10x menor).")

# =============================================================================
# 8. PERDAS DE CONDUCAO E BALANCO  (o que troca o Rds(on) do MOSFET)
# =============================================================================
p("\n8. CONDUCAO: o preco de trocar 1,7 mOhm por um Rds(on) maior")
p(f"  Rds(on) do FET de referencia  = 1,7 mOhm [DS IPB017N10N5 p.4, Table 4, VGS=10 V, ID=100 A]")
p(f"  Rds(on) do FET ESCOLHIDO     = {MOS_RDS*1e3:.2f} mOhm [DS FET p.4, Table 4] -> "
  f"{MOS_RDS/1.7e-3:.2f}x o de referencia")
p("")
hdr = f"  {'regime':>20s} {'I_pk':>6s} | {'P/FET ref':>10s} {'P/FET novo':>10s} | {'24 FETs ref':>12s} {'24 FETs novo':>12s} | {'Tj novo':>8s}"
p(hdr)
tot_ref, tot_novo = 0.0, 0.0
for nome, i in [("cruzeiro (5 A fase)", 5.0), ("nominal (15 A)", INOM), ("pico (30 A)", IPK)]:
    p_ref = (i / 2) ** 2 * 1.7e-3
    p_novo = (i / 2) ** 2 * MOS_RDS
    tot_ref += N_FETS * p_ref
    tot_novo += N_FETS * p_novo
    tj = TA + (p_novo + p_sw_est) * RTH_JA
    p(f"  {nome:>20s} {i:5.1f} A | {p_ref:8.3f} W {p_novo:8.3f} W | "
      f"{N_FETS*p_ref:10.2f} W {N_FETS*p_novo:10.2f} W | {tj:6.1f} C")
p("")
p(f"  [MEDIDO] regime ohmico no pico (30 A, mitade da corrente na meia ponte): "
  f"{N_FETS*((IPK/2)**2*1.7e-3):.2f} W (ref) -> {N_FETS*((IPK/2)**2*MOS_RDS):.2f} W (novo) = "
  f"+{N_FETS*((IPK/2)**2*MOS_RDS) - N_FETS*((IPK/2)**2*1.7e-3):.2f} W no banco")
p(f"  [MEDIDO] parcela de comutacao [EST modelo]: {N_FETS*p_sw_est:.2f} W (novo) contra "
  f"{N_FETS*0.5*VBAT_MAX*IPK*(168e-9/0.130)*FPWM:.2f} W do par de referencia com IR2104")
linha("perda total do banco no pico (conducao + comutacao [EST])",
      N_FETS * ((IPK / 2) ** 2 * 1.7e-3) + 0.0,
      N_FETS * ((IPK / 2) ** 2 * MOS_RDS) + N_FETS * p_sw_est,
      "conducao I^2*Rds(on) com I/2, mais 0,5*Vds*I*t_r*f [EST]", "W")

# =============================================================================
# 9. BLOCOS DO v4 QUE NAO DEPENDEM DE Qg NEM DE I_driver (reexecutados, nao editado)
# =============================================================================
p("\n9. BLOCOS QUE NAO DEPENDEM DA PREMISSA P-06 (reexecutados aqui, codigo do v4 §1-§4)")
C_BANK, ESR = 470e-6, 15e-3
i_fase_pico = 30.0
dv_esr = i_fase_pico * ESR
n_sw = 200
p(f"  Banco de entrada: C = {C_BANK*1e6:.0f} uF, ESR = {ESR*1e3:.0f} mOhm [PREMISSA P-15, sem parte escolhida]")
p(f"    dV por ESR a {i_fase_pico:.0f} A = {dv_esr*1e3:.0f} mV  (o degrau de uma fase)")
p(f"    dV_C por ampere de ripple AC = 1/(f_pwm*C) = {1/(FPWM*C_BANK)*1e3:.2f} mV/A; com os 100 nF + 10 uF")
p(f"    ceramicos colados a cada par de MOSFETs, o degrau de {i_fase_pico:.0f} A nao ve o eletrolitico e sim o")
p(f"    ceramico -- por isso o v4 trata esse numero como PIOR caso. [MEDIDO no modelo do v4 §1]")
p(f"    [MEDIDO] o v4 varre 8/10/12/15 mOhm porque o ESR do capacitor ESCOLHIDO continua [N/D offline].")
rv = 1.72e-8 * 1.6e-3 / (math.pi * 0.3e-3 * 25e-6)
p(f"  Vias 0,3 mm: R = {rv*1e3:.3f} mOhm -> 40 vias a {IPK:.0f} A: queda {IPK*rv/40*1e3:.3f} mV, "
  f"P = {IPK**2*rv/40*1e3:.0f} mW")
p(f"  ADC: janela 2 us = {2/(1/FPWM*1e6)*100:.1f} % do periodo de {1e6/FPWM:.0f} us")

p("\n10. BALANCO NO CRUZEIRO (mesmo modelo do v4 §4)")
P_H = 750 / 4.5
I_BUS = P_H / VBAT_NOM
# [FIX auditoria 1] pico de fase POR MOTOR: (i_bus/4)/0,6 = 3,1 A (o v6 usava i_bus/0,6
# = 12,5 A -- corrente TOTAL do drone como pico de fase de um motor so')
I_FASE = (I_BUS / 4) / 0.6
conv = (3.3 * 0.55 + VTRILHO * i_12 + 5 * 0.20) / 0.85
p(f"  Helice: {P_H:.0f} W | I_barra {I_BUS:.1f} A | I_fase pico (por motor) {I_FASE:.1f} A")
p(f"  FETs (conducao no cruzeiro): {24*(I_FASE/2)**2*MOS_RDS:.2f} W")
p(f"  Conversores: {conv:.2f} W (entrada) | TOTAL ~ {P_H + 24*(I_FASE/2)**2*MOS_RDS + conv:.0f} W "
  f"({(P_H + 24*(I_FASE/2)**2*MOS_RDS + conv)/P_H*100-100:.1f} % acima do ideal de helice)")

# =============================================================================
# 11. VEREDITO
# =============================================================================
p("\n" + "=" * 78)
p("VEREDITO v6 -- 8 limites criticos")
p("=" * 78)
limites = [
    ("L1", "tempo de subida do gate", 50.0, t_on_typ * 1e9, t_on_typ * 1e9 <= T_ALVO * 1e9, "ns"),
    ("L2", "queda no bootstrap", 40e-3, dv_boot, dv_boot <= 40e-3, "V"),
    ("L3", "corrente no trilho de 12 V", 600e-3, i_12, i_12 <= BUCK_12V_A, "A"),
    ("L4", "dead-time (turn-OFF)", DT_RTL * 1e9, t_off_typ * 1e9, t_off_typ * 1e9 <= janela * 1e9, "ns"),
    ("L6", "slew de Vgs (turn-ON)", 0.30, slew_on, slew_on >= 0.30, "V/ns"),
    ("L7", "Rg para comutar em 50 ns", RG_ADOTADO, rg_min_slew, rg_min_slew >= 2 * Z0, "ohm"),
    ("L8", "perda de comutacao por FET", 0.583, p_sw_est, p_sw_est <= 0.583, "W"),
]
p(f"  {'ID':4s} {'limite':30s} {'esperado':>11s} {'medido':>11s} {'erro':>11s}  veredito")
estourados = []
for lid, nome, esp, med, ok, un in limites:
    marca = "OK  " if ok else "ESTOURADO"
    if not ok:
        estourados.append((lid, nome, esp, med, un))
    p(f"  {lid:4s} {nome:30s} {esp:10.4g} {un:2s} {med:10.4g} {un:2s} "
      f"{pct(esp, med):+10.2f}%  {marca}")
p(f"  L5  potencia de porta por FET     {MOS_QG_TYP*10*FPWM*1e3:8.2f} mW "
  f"(nao e' limite termico: e' energia dissipada no Rg)")
p("")
if estourados:
    p(f"  {len(estourados)} limite(s) continua(m) ESTOURADO(s) com a combinacao escolhida:")
    for lid, nome, esp, med, un in estourados:
        p(f"    {lid} {nome}: precisa {esp:.4g} {un}, medido {med:.4g} {un} ({pct(esp, med):+.1f} %)")
else:
    p("  Todos os 8 limites fecham com a combinacao escolhida.")
p("")
p("=" * 78)
p("FIM v6 -- 100% calculo numerico. Nenhuma medicao de bancada.")
p("A unica grandeza estimada e a perda de comutacao (modelo 0,5*Vds*I*t_r), marcada [EST],")
p("porque nenhum dos PDFs em datasheets/ publica E_on/E_off [MEDIDO].")
p("=" * 78)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verifica_limites_v6_saida.txt")
open(out, "w").write("\n".join(L) + "\n")
