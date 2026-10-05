#!/usr/bin/env python3
"""
Fase 0 -- VERIFICACAO DE LIMITES v7
Reexecuta os 8 limites criticos com o MOSFET de BAIXO Qg realmente localizado na
fonte de cotacao (NVMFS6H824NT1G, onsemi, SO-8FL) no lugar do IPB017N10N5.

Estilo: segue o de verifica_limites_v6.py (mesma funcao p() acumulando linhas,
mesmo cabecalho "=" * 78, mesma gravacao do .txt ao lado do proprio script).
v6 e ESCOLHA_MOSFET_DRIVER.md foram LIDOS e NAO editados.

O que muda em relacao a v6: apenas o bloco do MOSFET. Os numeros de regime
(ripple, vias, Z0, balanco no cruzeiro, trilho de 12 V) sao os mesmos do v4/v6.
O que NAO mudou: o alvo de 50 ns de L1, herdado da Fase 0.

Marcadores de fonte:
  [DS VENC p.N]  datasheets/nvmfs6h824nt1g_onsemi_VENCEDOR.pdf (onsemi, PDF real)
  [DS REF p.N]  datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf
  [DS IR p.1]   datasheets/ir2104_infineon_datasheet.pdf
  [MEDIDO]      conta executada por ESTE arquivo agora
  [MEDIDO LCSC] valor lido da API de catalogo em 2026-09-28
  [PREMISSA]    premissa P-xx ainda em aberto
  [EST]         estimativa declarada, com a conta que a sustenta
"""
import math
import os

# =============================================================================
# 0.1  MOSFET VENCEDOR -- cada constante tem arquivo + pagina de PDF real
# =============================================================================
MOS_NAME = "NVMFS6H824NT1G (onsemi, 80 V, SO-8FL, Qg 38 nC)"
MOS_C = "C900472"
MOS_QG = 38e-9            # [DS VENC p.2, "Total Gate Charge QG(TOT)"]  VGS=10 V, VDS=40 V, ID=30 A
MOS_QG_TH = 7.4e-9        # [DS VENC p.2]  QG(TH)
MOS_RDS_TYP = 3.7e-3      # [DS VENC p.2]  RDS(on) typ @ VGS=10 V, ID=20 A
MOS_RDS_MAX = 4.5e-3      # [DS VENC p.2]  RDS(on) max @ VGS=10 V, ID=20 A
MOS_VDS = 80.0            # [DS VENC p.2]  V(BR)DSS
MOS_ID_MAX = 107.0        # [DS VENC p.1]  ID MAX
MOS_CISS = 2470e-12       # [DS VENC p.2]  CISS typ
MOS_COSS = 342e-12        # [DS VENC p.2]  COSS typ
MOS_QRR = 67e-9           # [DS VENC p.2]  QRR typ
MOS_RTHJC = 1.3           # [DS VENC p.1]  RqJC
MOS_RTHJA = 39.8          # [DS VENC p.1]  RqJA
MOS_PKG = "SO-8FL"
MOS_PRECO = 2.2632        # [MEDIDO LCSC] 2026-09-28, faixa de 1 unidade
MOS_PRECO10 = 1.9371      # [MEDIDO LCSC] 2026-09-28, faixa >= 10 (a que vale para 24 un)
MOS_ESTOQUE = 96          # [MEDIDO LCSC] 2026-09-28

# referencia orcada (o que esta no BOM hoje)
REF_NAME = "IPB017N10N5 (100 V, TO-263-7)"
REF_QG_TYP, REF_QG_MAX = 168e-9, 210e-9   # [DS REF p.4, Table 6]
REF_RDS = 1.7e-3                          # [DS REF p.4, Table 4] max @ 10 V
REF_PRECO = 5.2721                        # [MEDIDO LCSC] 2026-09-28, faixa de 1 unidade
REF_PRECO10 = 4.5461                      # [MEDIDO LCSC] 2026-09-28, faixa >= 10
REF_ESTOQUE = 143                         # [MEDIDO LCSC] 2026-09-28

# drivers ja cotados na v6 -- mantidos aqui para comparar os dois caminhos
DRV_IPEAK_6ED = 1.5       # [DS 6EDL7141 p.15]  IGD_SRC_PEAK
DRV_IPEAK_IR2104 = 0.130  # [DS IR2104 p.1]    IO+ (fonte)
DRV_INEG_IR2104 = 0.270   # [DS IR2104 p.1]    IO- (drain)

CBOOT = 4.7e-6            # 2 x 2,2 uF/25 V X7R 1206 em paralelo, como na v6

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
# 0. PREMISSAS (nao mudam: P-01..P-05, P-07..P-15, + trilho do PCB)
# =============================================================================
VBAT_MAX, VBAT_NOM = 25.2, 22.2
IPK, INOM = 30.0, 15.0
FPWM = 20e3
RTH_JA, TA = 60.0, 25.0
VTRILHO = 12.0
N_FETS, N_DRIVERS = 24, 12
DT_RTL = 518.750e-9
BUCK_12V_A = 0.60
T_ALVO = 0.05e-6
SPIKE_CALC = 60.0        # [FIX auditoria 14] spike de cabo L*di/dt = 100 nH x 30 A / 50 ns,
                         # CALCULADO na Fase 0 (FASE0_ESPECIFICACAO.md §4.4 / verifica_limites_
                         # entrada_v2 §1). NAO e' medido -- o rotulo antigo "[MEDIDO]" era falso.

p("=" * 78)
p("FASE 0 -- LIMITES CRITICOS (v7) -- MOSFET de BAIXO Qg REALMENTE LOCALIZADO")
p("=" * 78)
p(f"\n0. MOSFET AVALIADO (fonte: MOSfet_BAIXO_QG.md + datasheet real em datasheets/)")
p(f"  VENCEDOR : {MOS_NAME}, {MOS_C}, {MOS_PKG}")
p(f"     QG(TOT) = {MOS_QG*1e9:.0f} nC @ VGS=10 V, VDS=40 V, ID=30 A   [DS VENC p.2]")
p(f"     RDS(on) = {MOS_RDS_TYP*1e3:.1f} mOhm typ / {MOS_RDS_MAX*1e3:.1f} mOhm max @ 10 V  [DS VENC p.2]")
p(f"     V(BR)DSS = {MOS_VDS:.0f} V   |   ID max = {MOS_ID_MAX:.0f} A   [DS VENC p.2 / p.1]")
p(f"     RqJC = {MOS_RTHJC:.1f} C/W  |  RqJA = {MOS_RTHJA:.1f} C/W   [DS VENC p.1]")
p(f"     preco 1 un = {MOS_PRECO:.4f} USD  |  estoque = {MOS_ESTOQUE}   [MEDIDO LCSC 2026-09-28]")
p(f"  REFERENCIA (orcada hoje): {REF_NAME}, Qg {REF_QG_TYP*1e9:.0f}/{REF_QG_MAX*1e9:.0f} nC, "
  f"Rds {REF_RDS*1e3:.1f} mOhm, {REF_PRECO:.4f} USD, estoque {REF_ESTOQUE}")
# [FIX auditoria 14] margem de tensao no pior caso: o spike SOMA ao barramento.
# pior caso = 25,2 V + 60 V = 85,2 V contra V(BR)DSS de 80 V -> margem -6,1% (FALHA).
# A linha antiga somava ERRADO ("25,2 + 60 = 60") e reportava "folga de 33%" comparando
# 80 V so' contra o spike de 60 V, ignorando o barramento.
v_worst = VBAT_MAX + SPIKE_CALC                          # 85,2 V
margem_vds = (MOS_VDS - v_worst) / v_worst * 100.0      # -6,1 %
p(f"  Margem de tensao: barramento {VBAT_MAX:.1f} V + spike [CALC] {SPIKE_CALC:.0f} V = "
  f"{v_worst:.1f} V contra V(BR)DSS de {MOS_VDS:.0f} V -> margem de {margem_vds:.1f} % "
  f"({'FOLGA' if margem_vds >= 0 else 'FALHA'})  [CALC]")
p("  >>> [FIX auditoria 14] HONESTO: o MOSFET vencedor de 80 V NAO passa no criterio de")
p("      spike do projeto (pior caso 85,2 V > 80 V; o mesmo criterio reprovou o de 60 V por")
p("      'zero margem'). decisao pendente: aceitar o risco, reduzir o spike (snubber/layout)")
p("      ou subir para FET >= 100 V. O spike de 60 V e' [CALC], nao 'medido'.")

# =============================================================================
# 1. TEMPO DE COMUTACAO DE GATE
# =============================================================================
p("\n1. TEMPO DE COMUTACAO DE GATE  t = Qg / I_driver")
t_on = MOS_QG / DRV_IPEAK_IR2104
t_off = MOS_QG / DRV_INEG_IR2104
p(f"  Com IR2104 (130 mA fonte / 270 mA drain) [DS IR2104 p.1]:")
p(f"    t turn-ON  = {MOS_QG*1e9:.0f} nC / {DRV_IPEAK_IR2104*1e3:.0f} mA = {t_on*1e9:8.1f} ns  [MEDIDO]")
p(f"    t turn-OFF = {MOS_QG*1e9:.0f} nC = {t_off*1e9:8.1f} ns  [MEDIDO]")
p(f"  Com 6EDL7141 (1,5 A) [DS 6EDL7141 p.15]:")
p(f"    t turn-ON  = {MOS_QG*1e9:.0f} nC / {DRV_IPEAK_6ED*1e3:.0f} mA = "
  f"{MOS_QG/DRV_IPEAK_6ED*1e9:8.1f} ns  [MEDIDO]")
p(f"  t turn-ON da REFERENCIA com IR2104 = {REF_QG_TYP/DRV_IPEAK_IR2104*1e9:.1f} ns  [MEDIDO]")
linha("L1 tempo de subida do gate (esperado 50 ns)", T_ALVO * 1e9, t_on * 1e9,
      f"Qg = {MOS_QG*1e9:.0f} nC [DS VENC p.2] / {DRV_IPEAK_IR2104*1e3:.0f} mA [DS IR2104 p.1]; "
      f"referencia IPB017N10N5 dava {REF_QG_TYP/DRV_IPEAK_IR2104*1e9:.0f} ns", "ns")
p(f"  >>> reducao do erro de L1: de {pct(T_ALVO*1e9, REF_QG_TYP/DRV_IPEAK_IR2104*1e9):+.0f} % "
  f"(v6) para {pct(T_ALVO*1e9, t_on*1e9):+.0f} % -- 5,0x melhor, mas AINDA ESTOURADO.")
p(f"  >>> L1 so fecha com o 6EDL7141: {MOS_QG/DRV_IPEAK_6ED*1e9:.1f} ns contra o alvo de 50 ns.")

# =============================================================================
# 2. SLEW
# =============================================================================
p("\n2. SLEW DE GATE  dV/dt = 10 V / t")
slew_ir = 10.0 / t_on / 1e9
slew_6ed = 10.0 / (MOS_QG / DRV_IPEAK_6ED) / 1e9
linha("L6 slew de Vgs no turn-ON (com IR2104)", 0.30, slew_ir,
      "10 V / (Qg/I+) do IR2104; 0,30 V/ns era o valor assumido na Fase 0", "V/ns")
linha("L6b slew de Vgs no turn-ON (com 6EDL7141)", 0.30, slew_6ed,
      "10 V / (Qg/1,5 A); mesmo alvo de 0,30 V/ns", "V/ns")
p(f"  [MEDIDO] slew da REFERENCIA com IR2104 = 10 V / "
  f"{REF_QG_TYP/DRV_IPEAK_IR2104*1e9:.0f} ns = {10.0/(REF_QG_TYP/DRV_IPEAK_IR2104)/1e9:.5f} V/ns")
p(f"  [MEDIDO] corrente reativa em Ciss = Ciss*dV/dt = {MOS_CISS*1e12:.0f} pF x "
  f"{slew_6ed:.4f} V/ns = {MOS_CISS*slew_6ed*1e9*1e3:.0f} mA de um total de "
  f"{DRV_IPEAK_6ED*1e3:.0f} mA = {MOS_CISS*slew_6ed*1e9/DRV_IPEAK_6ED*100:.1f} %")

# =============================================================================
# 3. PERDA DE COMUTACAO
# =============================================================================
p("\n3. PERDA DE COMUTACAO")
p_sw_model = MOS_QG * VTRILHO * FPWM
linha("L8a perda de gate por FET (Qg*Vgs*f_pwm)", 0.583, p_sw_model,
      f"Qg x Vgs x f = {MOS_QG*1e9:.0f} nC x {VTRILHO:.0f} V x {FPWM/1e3:.0f} kHz; "
      f"0,583 W era o orcado de regime (v4 §3)", "W")
p(f"  [MEDIDO] no banco ({N_FETS} FETs) = {N_FETS*p_sw_model*1e3:.1f} mW; "
  f"a referencia IPB017N10N5 daria {N_FETS*REF_QG_TYP*VTRILHO*FPWM*1e3:.1f} mW "
  f"-> reducao de {(1-p_sw_model/(REF_QG_TYP*VTRILHO*FPWM))*100:.1f} %")
e_off_model = 0.5 * VBAT_MAX * IPK * t_on
p(f"  [EST modelo 0,5*Vds*I*t_r] E_off = 0,5 x {VBAT_MAX} V x {IPK} A x {t_on*1e9:.1f} ns = "
  f"{e_off_model*1e6:.1f} uJ -> {e_off_model*FPWM:.3f} W/FET (mesmo modelo do v6, "
  f"que dava {0.5*VBAT_MAX*IPK*REF_QG_TYP/DRV_IPEAK_IR2104*FPWM:.2f} W com a referencia)")
p(f"  >>> o modelo 0,5*Vds*I*t_r CRESCE com t_r e por isso MELHORA com um Qg menor; "
  f"ele nao e' a perda real do componente, e' so um comparavel entre as duas combinacoes.")
p(f"  [MEDIDO] E_oss = COSS x Vds = {MOS_COSS*1e12:.0f} pF x {VBAT_MAX} V = "
  f"{MOS_COSS*VBAT_MAX*1e9:.2f} nJ por comutacao (numero de tabela COSS, [DS VENC p.2],")
p(f"         que aqui e' ordem de grandeza MENOR que a energia de gate -- ao contrario do")
p(f"         IPB017N10N5, cujo Qoss de 213 nC [DS REF p.1] dominava a perda de comutacao)")

# =============================================================================
# 4. BOOTSTRAP
# =============================================================================
p("\n4. BOOTSTRAP  dV = Qg / Cboot")
dv_boot = MOS_QG / CBOOT
cboot_min = 20 * MOS_QG
linha("L2 queda no bootstrap por comutacao", 0.040, dv_boot,
      f"Qg = {MOS_QG*1e9:.0f} nC [DS VENC p.2] / Cboot = {CBOOT*1e6:.2f} uF; "
      f"o minimo pela regra de 20*Qg cai de 3,36 uF para {cboot_min*1e6:.2f} uF", "V")
p(f"  [MEDIDO] Cboot minimo (20*Qg) = {cboot_min*1e6:.2f} uF; adotado {CBOOT*1e6:.2f} uF "
  f"-> folga de {CBOOT/cboot_min:.2f}x")
p(f"  [MEDIDO] a Qg caiu de {REF_QG_TYP*1e9:.0f} nC para {MOS_QG*1e9:.0f} nC, ou seja "
  f"{REF_QG_TYP/MOS_QG:.1f}x menos carga: o Cboot do BOM pode SHRINK, nao precisa crescer.")

# =============================================================================
# 5. CORRENTE NO TRILHO DE 12 V
# =============================================================================
p("\n5. CORRENTE NO TRILHO DE GATE")
i_12 = N_DRIVERS * 25e-6 + N_FETS * MOS_QG * FPWM
linha("L3 corrente no trilho de 12 V", BUCK_12V_A, i_12,
      f"{N_DRIVERS} x 25 uA (Iq typ do 6EDL7141, [DS 6EDL7141 p.14]) + {N_FETS} x Qg x f; "
      f"o buck e' de {BUCK_12V_A*1e3:.0f} mA (dimensionamento_fase0.py)", "A")
p(f"  [MEDIDO] uso do buck = {i_12/BUCK_12V_A*100:.1f} % -> folga de {BUCK_12V_A/i_12:.1f}x "
  f"(a referencia consumia {N_DRIVERS*25e-6 + N_FETS*REF_QG_TYP*FPWM:.3f} A)")

# =============================================================================
# 6. DEAD-TIME
# =============================================================================
p("\n6. DEAD-TIME")
t_off_6ed = MOS_QG / DRV_IPEAK_6ED
linha("L4 dead-time necessario no turn-OFF (IR2104)", DT_RTL * 1e9, t_off * 1e9,
      f"Qg/I- = {MOS_QG*1e9:.0f} nC / {DRV_INEG_IR2104*1e3:.0f} mA; janela util do MCPWM = "
      f"{DT_RTL*1e9:.3f} ns (RELATORIO_VERILOG.md)", "ns")
linha("L4b dead-time necessario no turn-OFF (6EDL7141)", DT_RTL * 1e9, t_off_6ed * 1e9,
      f"Qg/1,5 A = {t_off_6ed*1e9:.1f} ns; piso do CI e' 120 ns < janela do MCPWM, "
      f"entao o dead-time NAO se soma (ESCOLHA_MOSFET_DRIVER.md §4.3)", "ns")
# [FIX auditoria 15] percentual = tempo x 100 / valor_base. A formula antiga era
# (DT_RTL - t_ref)*100 -- tempo multiplicado por 100 SEM dividir pela base ("sobe de 0 %").
t_ref_6ed = REF_QG_TYP / DRV_IPEAK_6ED                   # 112 ns
p(f"  [MEDIDO] folga no caminho do 6EDL7141 = {(DT_RTL - t_off_6ed)/t_off_6ed*100:.0f} % "
  f"(sobe de {(DT_RTL - t_ref_6ed)/t_ref_6ed*100:.0f} % com a referencia)")

# =============================================================================
# 7. Rg
# =============================================================================
p("\n7. RESISTOR DE GATE")
# [FIX auditoria 9/16] L e C do laco de gate do v4 §3: 20 nH e 2 nF (o v7 tinha TROCADOS:
# 20 nF / 2 nH -> Z0 = 0,32 ohm em vez de 3,16 ohm). Com os valores corretos o piso de
# amortecimento e' Rg >= 6,3 ohm (o adotado 10 ohm continua atendendo).
C_LACO, L_LACO = 2e-9, 20e-9   # 2 nF e 20 nH (v4 §3) [FIX auditoria 9]
Z0 = math.sqrt(L_LACO / C_LACO)
RG_ADOTADO = 10.0
linha("L7 Rg vs amortecimento (adotado 10 ohm)", RG_ADOTADO, 2 * Z0,
      f"Z0 = sqrt({L_LACO*1e9:.0f} nH / {C_LACO*1e12:.0f} pF) = {Z0:.2f} ohm; "
      f"amortecimento exige Rg >= 2*Z0 = {2*Z0:.1f} ohm", "ohm")
p(f"  [MEDIDO] com Rg = {RG_ADOTADO:.0f} ohm e Ciss = {MOS_CISS*1e12:.0f} pF, a constante "
  f"de tempo do gate e' RC = {RG_ADOTADO*MOS_CISS*1e9:.1f} ns; a comutacao de 0->10 V em 3,2*RC")
p(f"         levaria {3.2*RG_ADOTADO*MOS_CISS*1e9:.0f} ns, ou seja o Rg de 10 ohm NAO e' o gargalo -- "
  f"a corrente do driver e'.")
# [FIX auditoria 9] nota honesta: com o Z0 CORRETO (3,16 ohm) o piso de amortecimento e'
# 6,3 ohm. Para o VENCEDOR + 6EDL7141 nao ha conflito (t = 25,3 ns com Rg de 10 ohm);
# para a REFERENCIA de 168 nC o conflito amortecimento x velocidade continua (o Rg p/
# 50 ns seria ~2,3 ohm < 6,3 ohm) -- veredito L7 do verifica_limites_v6.py.
p(f"  [FIX auditoria 9] com o Z0 correto, o amortecimento exige Rg >= {2*Z0:.1f} ohm: o adotado "
  f"{RG_ADOTADO:.0f} ohm atende; com o IR2104 o L1 ja' esta estourado por corrente do driver "
  f"({t_on*1e9:.0f} ns).")

# =============================================================================
# 8. CONDUCAO  -- o preco de trocar 1,7 mOhm por 3,7/4,5 mOhm
# =============================================================================
p("\n8. CONDUCAO: o preco de trocar o Rds(on) do IPB017N10N5")
p(f"  Metade da corrente da fase fica em cada FET da meia-ponte: P = (I/2)^2 * Rds(on).")
p(f"  Rds(on) da REFERENCIA  = {REF_RDS*1e3:.1f} mOhm max [DS REF p.4, Table 4] (TO-263-7)")
p(f"  Rds(on) do VENCEDOR   = {MOS_RDS_TYP*1e3:.1f} mOhm typ / {MOS_RDS_MAX*1e3:.1f} mOhm max "
  f"[DS VENC p.2] ({MOS_PKG})")
p("")
p(f"  {'regime':>16s} {'I':>6s} | {'P/FET ref':>10s} {'P/FET venc typ':>14s} {'P/FET venc max':>14s} |"
  f" {'6 FETs ref':>11s} {'6 FETs venc':>11s} | {'Tj ref':>7s} {'Tj venc':>7s}")
linhas = []
for nome, i in [("nominal", INOM), ("pico", IPK)]:
    p_ref = (i / 2) ** 2 * REF_RDS
    p_typ = (i / 2) ** 2 * MOS_RDS_TYP
    p_max = (i / 2) ** 2 * MOS_RDS_MAX
    tj_ref = TA + p_ref * RTH_JA
    tj_venc = TA + p_max * RTH_JA
    linhas.append((nome, i, p_ref, p_typ, p_max))
    p(f"  {nome:>16s} {i:5.1f} A | {p_ref:8.3f} W {p_typ:12.3f} W {p_max:12.3f} W |"
      f" {6*p_ref:9.3f} W {6*p_max:9.3f} W | {tj_ref:5.1f}C {tj_venc:5.1f}C")
p("")
p(f"  [MEDIDO] 6 FETs de UM MOTOR no pico de {IPK:.0f} A: "
  f"{6*linhas[1][2]:.3f} W (ref) -> {6*linhas[1][4]:.3f} W (vencedor, Rds max) = "
  f"+{6*linhas[1][4]-6*linhas[1][2]:.3f} W por motor, {4*(6*linhas[1][4]-6*linhas[1][2]):.3f} W no banco")
p(f"  [MEDIDO] banco inteiro ({N_FETS} FETs) no pico: {N_FETS*linhas[1][2]:.2f} W (ref) -> "
  f"{N_FETS*linhas[1][4]:.2f} W (vencedor)")
p(f"  [MEDIDO] Tj do vencedor com o Rth de projeto {RTH_JA:.0f} C/W e Ta {TA:.0f} C: "
  f"{TA + linhas[1][4]*RTH_JA:.1f} C  (referencia: {TA + linhas[1][2]*RTH_JA:.1f} C)")
p(f"  [MEDIDO] Tj do vencedor com o RqJA REAL de datasheet ({MOS_RTHJA:.1f} C/W, SO-8FL, "
  f"[DS VENC p.1]): {TA + linhas[1][4]*MOS_RTHJA:.1f} C  (referencia em TO-263-7, Rth de projeto: "
  f"{TA + linhas[1][2]*RTH_JA:.1f} C)")
p(f"  [MEDIDO] soma P_cond + P_sw no pico de {IPK:.0f} A, por FET (P_cond com Rds MAX, que e' o orcamento):")
p(f"        REFERENCIA  IPB017N10N5 : P_cond {linhas[1][2]:.3f} W + P_sw {REF_QG_TYP*VTRILHO*FPWM*1e3:.1f} mW "
  f"= {linhas[1][2] + REF_QG_TYP*VTRILHO*FPWM:.3f} W")
p(f"        VENCEDOR  NVMFS6H824NT1G: P_cond {linhas[1][4]:.3f} W + P_sw {p_sw_model*1e3:.1f} mW "
  f"= {linhas[1][4] + p_sw_model:.3f} W")
p(f"        DELTA                  : {(linhas[1][4] + p_sw_model) - (linhas[1][2] + REF_QG_TYP*VTRILHO*FPWM):+.3f} W por FET")
p(f"  >>> ESTA E' A TROCA REAL: a perda de GATE caiu "
  f"{(1 - p_sw_model/(REF_QG_TYP*VTRILHO*FPWM))*100:.0f} %, mas a de CONDUCAO subiu "
  f"{(linhas[1][4]/linhas[1][2]-1)*100:.0f} %, e o total FICOU PIOR. O vencedor ganha em")
p(f"      velocidade de gate e perde em resistencia -- e a resistencia e' o que pesa a 30 A.")
p(f"  [EST] com o modelo 0,5*Vds*I*t_r (mesmo dos dois lados, corrente de cada regime):")
for nome, i, p_ref, p_typ, p_max in linhas:
    sw_v = 0.5 * VBAT_MAX * i * t_on * FPWM
    sw_r = 0.5 * VBAT_MAX * i * (REF_QG_TYP / DRV_IPEAK_IR2104) * FPWM
    p(f"        {nome:8s} I={i:4.1f} A: ref = {p_ref + sw_r:7.3f} W  |  venc = {p_max + sw_v:7.3f} W  |  "
      f"delta = {(p_max + sw_v) - (p_ref + sw_r):+7.3f} W")
p(f"  >>> o aumento de P_cond e' de ~{linhas[1][4]/linhas[1][2]:.1f}x, mas o SO-8FL tem "
  f"RqJA de {MOS_RTHJA:.1f} C/W contra os 60 C/W de projeto, e sobra folga de "
  f"{(125 - (TA + linhas[1][4]*MOS_RTHJA)):.0f} C antes dos 125 C limites de encapsulamento.")

# =============================================================================
# 9. CUSTO
# =============================================================================
p("\n9. CUSTO (24 MOSFETs, [MEDIDO LCSC] 2026-09-28)")
p(f"  Escada de precos da fonte -- 24 unidades cai na FAIXA >= 10 (o degrau seguinte e' 30):")
p(f"    NVMFS6H824NT1G: 1u {MOS_PRECO:.4f} | >=10 {MOS_PRECO10:.4f} | >=30 1.7323 | >=100 1.5241 USD")
p(f"    IPB017N10N5   : 1u {REF_PRECO:.4f} | >=10 {REF_PRECO10:.4f} | >=30 3.6759 | >=100 3.2400 USD")
p(f"  Referencia IPB017N10N5 : 24 x {REF_PRECO10:.4f} USD = {24*REF_PRECO10:8.3f} USD  (estoque {REF_ESTOQUE})")
p(f"  Vencedor  NVMFS6H824NT1G: 24 x {MOS_PRECO10:.4f} USD = {24*MOS_PRECO10:8.3f} USD  (estoque {MOS_ESTOQUE})")
p(f"  DELTA                    = {24*MOS_PRECO10 - 24*REF_PRECO10:+8.3f} USD "
  f"({(MOS_PRECO10/REF_PRECO10-1)*100:+.1f} %)")
p(f"  >>> o MOSFET BARATO. A troca nao so fecha o Qg: ela CUSTA MENOS.")

# =============================================================================
# 10. BLOCOS QUE NAO DEPENDEM DO MOSFET
# =============================================================================
p("\n10. BLOCOS QUE NAO DEPENDEM DE Qg NEM DE I_driver (reexecutados, codigo do v4/v6)")
C_BANK, ESR = 470e-6, 15e-3
p(f"  Banco: C = {C_BANK*1e6:.0f} uF, ESR = {ESR*1e3:.0f} mOhm [PREMISSA P-15, sem parte escolhida]")
p(f"    dV por ESR a {IPK:.0f} A = {IPK*ESR*1e3:.0f} mV   [MEDIDO]")
p(f"    dV_C por ampere de ripple = 1/(f_pwm*C) = {1/(FPWM*C_BANK)*1e3:.2f} mV/A   [MEDIDO]")
rv = 1.72e-8 * 1.6e-3 / (math.pi * 0.3e-3 * 25e-6)
p(f"  Vias 0,3 mm: R = {rv*1e3:.3f} mOhm -> 40 vias a {IPK:.0f} A: queda {IPK*rv/40*1e3:.3f} mV, "
  f"P = {IPK**2*rv/40*1e3:.0f} mW   [MEDIDO]")
p(f"  ADC: janela 2 us = {2/(1/FPWM*1e6)*100:.1f} % do periodo de {1e6/FPWM:.0f} us   [MEDIDO]")
P_H = 750 / 4.5
I_BUS = P_H / VBAT_NOM
# [FIX auditoria 1] pico de fase POR MOTOR: (i_bus/4)/0,6 = 3,1 A (o v7 usava i_bus/0,6
# = 12,5 A -- corrente TOTAL do drone como pico de fase de um motor so')
I_FASE = (I_BUS / 4) / 0.6
i_12_b = N_DRIVERS * 25e-6 + N_FETS * MOS_QG * FPWM
conv = (3.3 * 0.55 + VTRILHO * i_12_b + 5 * 0.20) / 0.85
p("\n11. BALANCO NO CRUZEIRO (mesmo modelo do v4 §4, com o Rds do vencedor)")
p(f"  Helice {P_H:.0f} W | I_barra {I_BUS:.1f} A | I_fase pico (por motor) {I_FASE:.1f} A   [MEDIDO]")
p(f"  FETs (conducao no cruzeiro, Rds typ): {N_FETS*(I_FASE/2)**2*MOS_RDS_TYP:.2f} W   [MEDIDO]")
p(f"  Conversores: {conv:.2f} W (entrada)   [MEDIDO]")
p(f"  TOTAL ~ {P_H + N_FETS*(I_FASE/2)**2*MOS_RDS_TYP + conv:.0f} W "
  f"({(P_H + N_FETS*(I_FASE/2)**2*MOS_RDS_TYP + conv)/P_H*100-100:.1f} % acima do ideal)")

# =============================================================================
# 12. VEREDITO
# =============================================================================
p("\n" + "=" * 78)
p("VEREDITO v7 -- 8 limites criticos, ESPERADO x MEDIDO x ERRO")
p("=" * 78)
limites = [
    ("L1", "tempo de subida do gate (IR2104, 50 ns)", 50.0, t_on * 1e9, t_on * 1e9 <= 50.0, "ns"),
    ("L2", "queda no bootstrap (40 mV)", 40e-3, dv_boot, dv_boot <= 40e-3, "V"),
    ("L3", "corrente no trilho de 12 V (600 mA)", 600e-3, i_12, i_12 <= BUCK_12V_A, "A"),
    ("L4", "dead-time turn-OFF (518,75 ns)", DT_RTL * 1e9, t_off * 1e9,
     t_off * 1e9 <= DT_RTL * 1e9, "ns"),
    ("L5", "perda de gate por FET (0,583 W)", 0.583, p_sw_model, p_sw_model <= 0.583, "W"),
    ("L6", "slew de Vgs (0,30 V/ns)", 0.30, slew_ir, slew_ir >= 0.30, "V/ns"),
    ("L7", "Rg vs amortecimento (10 ohm)", 10.0, 2 * Z0, 2 * Z0 <= 10.0, "ohm"),
    ("L8", "perda total por FET no pico (0,583 W)", 0.583, p_sw_model + (IPK / 2) ** 2 * MOS_RDS_MAX,
     False, "W"),
]
p(f"  {'ID':4s} {'limite':40s} {'esperado':>11s} {'medido':>11s} {'erro':>10s}  veredito")
estourados, ok_n = [], 0
for lid, nome, esp, med, ok, un in limites:
    # nenhum limite recebe tolerancia de folga: verde e' verde ou e' vermelho
    marca = "\u2705 VERDE" if ok else "\U0001f534 VERMELHO"
    if ok:
        ok_n += 1
    else:
        estourados.append((lid, nome, esp, med, un))
    p(f"  {lid:4s} {nome:40s} {esp:10.4g} {un:2s} {med:10.4g} {un:2s} "
      f"{pct(esp, med):+9.1f}%  {marca}")
p(f"\n  {ok_n} de {len(limites)} limites VERDES, {len(estourados)} VERMELHOS.")
if estourados:
    p("\n  O QUE CONTINUA ESTOURADO, E O QUE AINDA SERIA PRECISO:")
    for lid, nome, esp, med, un in estourados:
        p(f"    {lid} {nome}: precisa {esp:.4g} {un}, medido {med:.4g} {un} ({pct(esp, med):+.1f} %)")
    p("")
    p("    L1 e L6 NAO sao problema de MOSFET: sao problema de CORRENTE DE DRIVER.")
    p(f"      Com o MESMO MOSFET e o 6EDL7141 (1,5 A): t = {MOS_QG/DRV_IPEAK_6ED*1e9:.1f} ns "
      f"e slew = {slew_6ed:.4f} V/ns -- os dois FECHAM. O que impede o IR2104 de fechar L1 e' a")
    p(f"      propria corrente dele: 50 ns a 130 mA exige Qg <= {130e-3*50e-9*1e9:.1f} nC, e nenhum")
    p("      MOSFET com Qg <= 6,5 nC E Rds(on) <= 5 mOhm a 60 V em package soldavel a mao foi")
    p("      encontrado na varredura de 7 familias de MOSFET_BAIXO_QG.md -- o de menor Rds da varredura")
    p("      com Vds >= 60 V e package de mao e' o proprio vencedor, com Qg de 38 nC.")
    p("    L8 e' balanco de POTENCIA, nao de tempo. A troca FECHOU o gate e ABRIU a conducao:")
    p(f"        P_gate  {REF_QG_TYP*VTRILHO*FPWM*1e3:.1f} mW -> {p_sw_model*1e3:.1f} mW   "
      f"(ganho de {REF_QG_TYP*VTRILHO*FPWM/p_sw_model:.1f}x)")
    p(f"        P_cond  {linhas[1][2]:.3f} W -> {linhas[1][4]:.3f} W   "
      f"(perda de {linhas[1][4]/linhas[1][2]:.2f}x)")
    p(f"        P_total {linhas[1][2] + REF_QG_TYP*VTRILHO*FPWM:.3f} W -> "
      f"{linhas[1][4] + p_sw_model:.3f} W")
    p(f"      A REFERENCIA PASSARIA em L8 com {linhas[1][2] + REF_QG_TYP*VTRILHO*FPWM:.3f} W "
      f"({pct(0.583, linhas[1][2] + REF_QG_TYP*VTRILHO*FPWM):+.1f} %);")
    p(f"      o VENCEDOR NAO PASSA com {linhas[1][4] + p_sw_model:.3f} W "
      f"({pct(0.583, linhas[1][4] + p_sw_model):+.1f} %). Nenhuma das saidas de projeto fecha isto:")
    p("        (a) AUMENTAR f_pwm NAO AJUDA: P_sw = Qg*Vgs*f e' linear em f, e a perda de")
    p("            conducao sobe junto. Nao existe f_pwm que conserte L8.")
    p(f"        (b) AUMENTAR A AREA DE COPRE: o SO-8FL tem RqJA de {MOS_RTHJA:.1f} C/W [DS VENC p.1],")
    p(f"            e a conta de Tj com esse valor REAL da {TA + linhas[1][4]*MOS_RTHJA:.1f} C no pico --")
    p(f"            folga de {125 - (TA + linhas[1][4]*MOS_RTHJA):.0f} C ate o limite de 125 C do encapsulamento.")
    p("            A fisica NAO esta estourada. O que esta apertado e' o ORCAMENTO de 0,583 W/FET,")
    p("            que o v4 §3 adoptou sem parte de package escolhida. Com 2 oz de cobre sob o dreno,")
    p(f"            o orcamento de regime por FET precisa ser reprecificado para "
      f"~{linhas[1][4] + p_sw_model:.2f} W.")
    p("            Reprecificar orcamento e' decisao da FASE 0, nao parametro que o v7 possa")
    p("            escolher sozinho -- por isso L8 fica VERMELHO neste relatorio.")
    p("        (c) VOLTAR AO PACOTE GRANDE: o TO-220 do IPP052N08N5 tem Qg de 42 nC typ / 53 nC max")
    p("            [datasheets/ipp052n08n5_infineon_ALTERNATIVA_TO220.pdf p.5] e Rds(on) de 6,0 mOhm typ")
    p("            / 6,9 mOhm max [mesmo PDF p.5] -- 6,0 mOhm tip NAO fecha o criterio de")
    p("            Rds(on) <= 5 mOhm. Ele ganha em Qg e NAO fecha em Rds. Ver MOSFET_BAIXO_QG.md §3.")
    p("")
    p("  >>> NADA foi marcado verde por conveniencia: L1, L6 e L8 sao vermelhos porque os")
    p("      numeros medidos sao vermelhos, inclusive o L8, que a troca MELHOROU no gate e")
    p("      PIOROU no cobre.")
    # [FIX auditoria 16] removido o paragrafo final DUPLICADO ("NADA foi marcado verde..."
    # aparecia duas vezes seguidas na saida)
p("\n" + "=" * 78)
p("FIM v7 -- 100% calculo numerico, zero medicao de bancada.")
p("Parametros do MOSFET: datasheets/nvmfs6h824nt1g_onsemi_VENCEDOR.pdf p.1 e p.2 (PDF real).")
p("Preco e estoque: API de catalogo EasyEDA/LCSC em 2026-09-28.")
p("E_on/E_off continuam [N/D]: o datasheet do onsemi nao publica E_on/E_off, so COSS.")
p("=" * 78)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verifica_limites_v7_saida.txt")
open(out, "w").write("\n".join(L) + "\n")
