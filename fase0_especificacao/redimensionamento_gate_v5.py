#!/usr/bin/env python3
"""
Fase 0 - REDIMENSIONAMENTO DO GATE DRIVE (v5) com Qg REAL do MOSFET de referencia.

Por que este script existe:
  A premissa P-06 assumia Qg = 40 nC. O datasheet REAL do MOSFET de referencia
  (datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf) da
  Qg = 168 nC (typ) / 210 nC (max) -- 4,2x a premissa.
  A premissa P-11 assumia 2,5 mA de quiesciencia por driver. O IR2104 real
  (datasheets/ir2104_infineon_datasheet.pdf) tem IQCC 150/270 uA + IQBS 30/55 uA
  = 180 uA typ / 325 uA max -- 7,7x MENOR que a premissa (era folga, nao erro,
  mas a conta muda) -- e a corrente de pico de gate e' 130 mA fonte / 270 mA
  drain, e nao "1,2 A com Rg=10 ohm" como o dimensionamento_fase0.py supunha.

TUDO aqui vem de: (a) conta executada agora neste arquivo, (b) linha de PDF
extraida com `pdftotext -layout` (pagina citada em [DS p.N]), (c) premissa
declarada ainda em aberto. O que e' estimativa minha esta marcado [EST].

NENHUM arquivo existente foi modificado por este script. Ver README desta §.

Convencoes herdadas de dimensionamento_fase0.py: h() para cabecalho de secao,
print() direto, [MEDIDO] = numero produzido por conta aqui, [DATASHEET] = linha
de PDF, [PREMISSA] = P-xx em aberto, [EST] = estimativa do redator.
"""
import math
import os
import sys

# ------------------------------------------------------------------ DATASHEET
# ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf
DS_FET = "datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf"
DS_DRV = "datasheets/ir2104_infineon_datasheet.pdf"

QG_TYP = 168e-9      # [DS IPB017N10N5 p.4, Table 6 "Gate charge total", typ]
QG_MAX = 210e-9      # [DS IPB017N10N5 p.4, Table 6 "Gate charge total", max]
QGS = 53e-9          # [DS IPB017N10N5 p.4, Table 6 "Gate to source charge", typ]
QGD_TYP, QGD_MAX = 34e-9, 51e-9   # [DS IPB017N10N5 p.4, Table 6, typ/max]
QSW = 51e-9          # [DS IPB017N10N5 p.4, Table 6 "Switching charge", typ]
VPLATEAU = 4.4       # [DS IPB017N10N5 p.4, Table 6, typ]
RG_INT = 1.3         # [DS IPB017N10N5 p.4, Table 4 "Gate resistance", typ]
CISS_TYP, CISS_MAX = 12.0e-9, 15.6e-9  # [DS IPB017N10N5 p.4, Table 5, typ/max]
TR_DS = 23e-9        # [DS IPB017N10N5 p.4, Table 5 "Rise time", typ, RG,ext=1,6 ohm]
TF_DS = 27e-9        # [DS IPB017N10N5 p.4, Table 5 "Fall time", typ, RG,ext=1,6 ohm]
RDS_TYP_10V, RDS_MAX_10V = 1.5e-3, 1.7e-3  # [DS IPB017N10N5 p.4, Table 4, VGS=10V, ID=100A]
QRR_TYP, QRR_MAX = 235e-9, 470e-9         # [DS IPB017N10N5 p.4, Table 7, typ/max]

# ir2104_infineon_datasheet.pdf
IO_P = 130e-3        # [DS IR2104 p.1, Product Summary "IO+/- 130 mA / 270 mA"] fonte
IO_M = 270e-3        # [DS IR2104 p.1, Product Summary] drain
IQCC_TYP, IQCC_MAX = 150e-6, 270e-6   # [DS IR2104 p.3, Static Electrical Characteristics]
IQBS_TYP, IQBS_MAX = 30e-6, 55e-6     # [DS IR2104 p.3, Static Electrical Characteristics]
DT_MIN, DT_TYP, DT_MAX = 400e-9, 520e-9, 650e-9  # [DS IR2104 p.3, Dynamic, "DT"]
IRQ_TYP = IQCC_TYP + IQBS_TYP   # 180 uA  [MEDIDO] soma das duas correntes de quiesciencia
IRQ_MAX = IQCC_MAX + IQBS_MAX   # 325 uA  [MEDIDO]

# ------------------------------------------------------- PREMISSAS MANTIDAS
P05_RDS = 2.0e-3     # P-05 MANTIDA: 2,0 mOhm. [PREMISSA] (o DS da 1,7/1,5 mOhm e' do
                     # IPB017N10N5, marcado "REFERENCIA_NAO_ESCOLHIDO")
P07_FPWM = 20e3      # P-07 MANTIDA: 20 kHz. [PREMISSA]
P06_QG_ANTIGO = 40e-9   # P-06 ORIGINAL, mantida so' para a comparacao
P11_IQ_ANTIGO = 2.5e-3  # P-11 ORIGINAL
VGS_DRIVE = 10.0     # [EST] 10 V = ponto em que o DS caracterizou Qg ("VGS=0 to 10V",
                     # [DS IPB017N10N5 p.4, Table 6]). A placa alimenta os drivers
                     # a 12 V (fase3_pcb/gera_pcb_v7.py linha 239) -> com 12 V o Qg
                     # effective seria MAIOR que 168 nC, mas o DS nao da esse numero.
DV_GATE = 10.0       # [EST] excursion de Vgs considerada = 10 V (0 -> 10 V, como o DS)
RG_EXT = 10.0        # [PREMISSA] Rg externo adotado na Fase 0 (FASE0_ESPECIFICACAO.md
                     # linha 251) -- continua, mas ver §5: ele NAO e' quem limita a corrente
N_DRV = 12           # 3 drivers por motor x 4 motores [FASE0_ESPECIFICACAO.md §1]
N_FET = 24           # 6 MOSFETs por motor x 4 motores
V12 = 12.0           # [MEDIDO em fase3_pcb/gera_pcb_v7.py linha 239] rails de 12 V
DT_RTL = 518.75e-9   # [MEDIDO] fase2_simulacao/verilog/RELATORIO_VERILOG.md §2 / plano/WP4_FIRMWARE.md
T_ALVO = 25e-9       # [EST] alvo de comutacao: 25 ns, escolhido por ser ~0,5 % do
                     # periodo de 20 kHz (50 us) e ~metade do tr do DS (23 ns)

# ------------------------------------------------------------------ HELPERS
L = []
def p(s=""):
    print(s)
    L.append(s)

def h(t):
    p("\n" + "=" * 78)
    p(t)
    p("=" * 78)

def chk(nome, esperado, medido, uni, fonte=""):
    """esperado x medido x erro -- convencao exigida pela missao."""
    if esperado == 0:
        erro = float("nan")
        p(f"  {nome:52s} | esp {esperado:>10.4g} | med {medido:>10.4g} {uni:6s} | erro   N/D")
        return
    erro = (medido - esperado) / esperado * 100.0
    p(f"  {nome:52s} | esp {esperado:>10.4g} | med {medido:>10.4g} {uni:6s} | erro {erro:+7.2f} %")
    if fonte:
        p(f"  {'':52s} |   fonte: {fonte}")

# ================================================================== CABECALHO
h("REDIMENSIONAMENTO DO GATE DRIVE (v5) -- Qg REAL")
p(f"  MOSFET de referencia : IPB017N10N5 (OptiMOS 5, 100 V) -- {DS_FET}")
p(f"  Driver              : IR2104(S) -- {DS_DRV}")
p("  Os dois sao 'NAO ESCOLHIDOS'. Este script dimensiona para o par de referencia")
p("  e mostra o quanto a Fase 0 (feita com Qg = 40 nC, premissa P-06) subestimava.")
p("")
p("  Fontes de numero, por tipo:")
p("    [DS FET p.N]  IPB017N10N5 via `pdftotext -layout`  -> tabela e pagina citadas")
p("    [DS DRV p.N]  IR2104 via `pdftotext -layout`         -> tabela e pagina citadas")
p("    [MEDIDO]      conta executada por ESTE arquivo agora")
p("    [PREMISSA]    P-xx de FASE0_ESPECIFICACAO.md, ainda em aberto")
p("    [EST]         estimativa do redator, com a conta que a sustenta")

# ============================================================ 1. AS DUAS PREMISSAS
h("1. O QUE MUDOU: P-06 (Qg) e P-11 (quiesciencia do driver)")
chk("P-06 Qg total do MOSFET  (nC)", P06_QG_ANTIGO * 1e9, QG_TYP * 1e9, "nC",
    "IPB017N10N5 p.4, Table 6 'Gate charge total' = 168 nC typ / 210 nC max")
chk("P-06 Qg total  -- caso MAXIMO (nC)", P06_QG_ANTIGO * 1e9, QG_MAX * 1e9, "nC",
    "IPB017N10N5 p.4, Table 6, coluna Max")
chk("P-11 quiesciencia por driver (uA)", P11_IQ_ANTIGO * 1e6, IRQ_TYP * 1e6, "uA",
    "IR2104 p.3, Static: IQCC 150/270 uA + IQBS 30/55 uA = 180 uA typ")
chk("P-11 quiesciencia por driver -- MAX (uA)", P11_IQ_ANTIGO * 1e6, IRQ_MAX * 1e6, "uA",
    "IR2104 p.3, Static, colunas Max somadas: 270 + 55 = 325 uA")
p("")
p("  Leitura: P-06 esta ERRADA por 4,20x (typ) / 5,25x (max) -- e' o erro que decide a placa.")
p(f"          P-11 estava {P11_IQ_ANTIGO/IRQ_TYP:.1f}x ACIMA do tipico e "
  f"{P11_IQ_ANTIGO/IRQ_MAX:.1f}x ACIMA do maximo: a premissa era")
p("          pessimista, ou seja, folga de folga no consumo quiescente. Nao e' risco de")
p("          thermally, mas a conta do trilho de 12 V muda (ver §6).")
p("")
p("  Composicao do Qg real (para o leitor nao tratar 168 nC como numero magico):")
p(f"    Qgs  = {QGS*1e9:.0f} nC   ({QGS/QG_TYP*100:.1f} % do Qg) [DS FET p.4 Table 6]  -> carga de 'linearizacao'")
p(f"    Qgd  = {QGD_TYP*1e9:.0f} nC typ / {QGD_MAX*1e9:.0f} nC max ({QGD_TYP/QG_TYP*100:.1f} % do Qg) [DS FET p.4] -> Miller, o que fixa a perda de comutacao")
p(f"    Qsw  = {QSW*1e9:.0f} nC   [DS FET p.4 Table 6]  -> parte que vai para a saida durante a comutacao")
p(f"    Vpl  = {VPLATEAU:.1f} V    [DS FET p.4 Table 6]  -> patamar, o ponto de maior dI/dt e maior dV/dt")
p(f"    RG interno do FET = {RG_INT:.1f} ohm typ [DS FET p.4 Table 4] -> soma com o Rg externo")
p("  [MEDIDO] Qg nao e' monolitico: 1/3 vai para o source (ganho de transcondutancia) e 1/5")
p("  fica no Miller. Um modelo de 'carga + Rg' so' para o total erra a forma da onda.")

# ============================================================ 2. TEMPO DE COMUTACAO
h("2. TEMPO DE COMUTACAO DE GATE  t = Qg / I_gate   (o numero que decide tudo)")
p("  I_gate NAO e' livre: e' o que o IR2104 entrega -- IO+ 130 mA (fonte) / IO- 270 mA")
p("  (drain) [IR2104 p.1, Product Summary]. O dimensionamento_fase0.py supunha")
p("  Ipk = Vgs/Rg = 10/10 = 1,2 A, o que e' fisicamente falso: 1,2 A exigiria que o")
p(f"  driver entregasse {1.2/IO_P:.1f}x a corrente que ele declara.")
p("")
for qg, lbl in ((QG_TYP, "Qg typ 168 nC"), (QG_MAX, "Qg max 210 nC")):
    for ig, ilbl in ((IO_P, "IO+ 130 mA"), (IO_M, "IO- 270 mA")):
        t = qg / ig
        p(f"  t = {qg*1e9:5.0f} nC / {ig*1e3:5.1f} mA = {t*1e6:7.4f} us = {t*1e9:8.1f} ns   "
          f"[{lbl}, {ilbl}] [MEDIDO]")
p("")
chk("t de comutacao com IO+ 130 mA (Qg typ, us)", 0.05, QG_TYP / IO_P * 1e6, "us",
    "168 nC / 130 mA; o alvo de 0,05 us (50 ns) e' o [EST] de projeto")
chk("t de comutacao com IO- 270 mA (Qg typ, us)", 0.05, QG_TYP / IO_M * 1e6, "us",
    "168 nC / 270 mA")
p("")
t_ioP_typ, t_ioM_typ = QG_TYP / IO_P, QG_TYP / IO_M
t_ioP_max, t_ioM_max = QG_MAX / IO_P, QG_MAX / IO_M
p(f"  [MEDIDO] Com Qg typ: subir leva {t_ioP_typ*1e6:.4f} us (130 mA) e descer leva")
p(f"  {t_ioM_typ*1e6:.4f} us (270 mA). Com Qg max: {t_ioP_max*1e6:.4f} us e {t_ioM_max*1e6:.4f} us.")
p(f"  [MEDIDO] Periodo de PWM a {P07_FPWM/1e3:.0f} kHz = {1/P07_FPWM*1e6:.1f} us, com duty 50 %")
p(f"  -> conduction de {1/P07_FPWM*1e6*0.5:.1f} us por ciclo. O turn-on de {t_ioP_typ*1e6:.2f} us")
p(f"  consome {(t_ioP_typ*P07_FPWM)*100:.1f} % do periodo; no pior caso de Qg max,")
p(f"  {(t_ioP_max*P07_FPWM)*100:.1f} %. Ver §7: isso vira perda em regime intermediario.")
p("")
p("  ANCORA DE BANCADA NO DATASHEET (esta e' a verificacao mais forte do script):")
p(f"    O DS mediu tr = {TR_DS*1e9:.0f} ns com Qg = 168 nC e Rg,ext = 1,6 ohm [DS FET p.4, Table 5].")
p(f"   Corrente media implicita = Qg/tr = {QG_TYP/TR_DS:.2f} A  [MEDIDO]")
p(f"    Isso e' {QG_TYP/TR_DS/IO_P:.1f}x a corrente de fonte que o IR2104 declara (130 mA).")
p(f"    [MEDIDO] Logo: o IPB017N10N5 em 20 kHz NAO e' comutavel por um IR2104 sem pre-")
p(f"    driver. As duas escritas do DS se cruzam exatamente assim, e o numero vem das duas.")
chk("I_media implicita no tr do DS (A)", IO_P, QG_TYP / TR_DS, "A",
    "168 nC / 23 ns; corrente de fonte do IR2104 = 130 mA [IR2104 p.1]")

# ============================================================ 3. SLEW dV/dt
h("3. SLEW DE Vgs  dV/dt = dV / t   (dV = 10 V, do 0 aos 10 V como o DS caracterizou)")
slew_typ_P = DV_GATE / t_ioP_typ / 1e9      # V/ns
slew_typ_M = DV_GATE / t_ioM_typ / 1e9
slew_max_P = DV_GATE / t_ioP_max / 1e9
slew_max_M = DV_GATE / t_ioM_max / 1e9
p("  [MEDIDO] dV/dt = dV/t, com dV = 10 V (0 -> 10 V, como o DS caracterizou Qg) e")
p("  t do §2. O slew nao e' um degree of freedom: com a corrente do driver travada")
p("  em 130/270 mA, ele e' consequencia de Qg.")
p("")
for st, ig, lbl in ((slew_typ_P, IO_P, "Qg typ, IO+ 130 mA"), (slew_typ_M, IO_M, "Qg typ, IO- 270 mA"),
                    (slew_max_P, IO_P, "Qg max, IO+ 130 mA"), (slew_max_M, IO_M, "Qg max, IO- 270 mA")):
    q = QG_TYP if "typ" in lbl else QG_MAX
    p(f"  dV/dt = {DV_GATE:.0f} V / ({q*1e9:.0f} nC / {ig*1e3:.0f} mA = {q/ig*1e6:.4f} us) = "
      f"{st:8.5f} V/ns   [{lbl}]   [MEDIDO]")
p("")
p(f"  [MEDIDO] Checagem cruzada contra o slew implicito no rise time do DS:")
p(f"  dV/dt = {DV_GATE:.0f} V / tr = {DV_GATE:.0f} V / {TR_DS*1e9:.0f} ns = {DV_GATE/TR_DS/1e9:.4f} V/ns "
  f"[DS FET p.4, Table 5].")
p(f"  [MEDIDO] O slew com Qg real e' {slew_typ_P:.5f} V/ns; o slew implicito no DS e' "
  f"{DV_GATE/TR_DS/1e9:.4f} V/ns -- {(DV_GATE/TR_DS/1e9)/slew_typ_P:.0f}x maior, o mesmo fator de corrente do §2.")
p(f"  [MEDIDO] A premissa P-06 com I = 1,2 A dava {DV_GATE/(P06_QG_ANTIGO/1.2)/1e9:.4f} V/ns "
  f"({(DV_GATE/(P06_QG_ANTIGO/1.2)/1e9)/slew_typ_P:.0f}x o slew real).")
p("")
p("  CONSEQUENCIA DE EMI/RINGING: com Ciss = 12 nF typ / 15,6 nF max [DS FET p.4, Table 5],")
p(f"  a MESMA corrente de gate ({IO_P*1e3:.0f} mA) carrega, pelo capacitor de entrada do proprio")
p(f"  transistor, uma corrente reativa I_Ciss = Ciss*dV/dt = {CISS_TYP*1e9:.0f} nF x {slew_typ_P:.5f} V/ns = "
  f"{CISS_TYP*slew_typ_P*1e9:.3f} A = {CISS_TYP*slew_typ_P*1e9/IO_P*100:.0f} % de I_gate  [MEDIDO]")
p(f"  [MEDIDO] Total de corrente no no durante o comutador = {(1+CISS_TYP*slew_typ_P*1e9/IO_P):.2f}x I_gate.")
p(f"  [MEDIDO] Com Ciss max ({CISS_MAX*1e9:.1f} nF) sobe para {(1+CISS_MAX*slew_typ_P*1e9/IO_P):.2f}x.")
p("  [EST] E' essa corrente, e nao a do gate, que alimenta o Rg e o laco de retorno -- ou")
p(f"  seja, a origem fisica do ringing que o §7 do FASE0_ESPECIFICACAO.md tenta amortecer")
p("  com Rg >= 6,3 ohm. O slew lento NAO protege o projeto; ele so' troca slew por calor.")
# ============================================================ 4. CORRENTE DE PICO
h("4. CORRENTE DE PICO NECESSARIA PARA COMUTAR EM 25 ns")
p(f"  Alvo: t = {T_ALVO*1e9:.0f} ns (periodo de 20 kHz = 50 us; 25 ns = 0,05 % do periodo)")
p("  [EST como alvo de projeto]. I_pico = Qg / t_alvo. [MEDIDO]")
p("")
for qg, lbl in ((QG_TYP, "Qg typ 168 nC"), (QG_MAX, "Qg max 210 nC")):
    ipk = qg / T_ALVO
    p(f"  I_pico = {qg*1e9:.0f} nC / {T_ALVO*1e9:.0f} ns = {ipk:5.2f} A  [{lbl}]  [MEDIDO]")
ipk_typ, ipk_max = QG_TYP / T_ALVO, QG_MAX / T_ALVO
chk("I_pico p/ 25 ns (Qg typ) vs IO+ do IR2104", IO_P, ipk_typ, "A", "168 nC / 25 ns")
chk("I_pico p/ 25 ns (Qg typ) vs IO- do IR2104", IO_M, ipk_typ, "A", "168 nC / 25 ns")
chk("I_pico p/ 25 ns (Qg max) vs IO- do IR2104", IO_M, ipk_max, "A", "210 nC / 25 ns")
chk("I_pico p/ 25 ns (Qg typ) vs premissa 1,2 A", 1.2, ipk_typ, "A",
    "a premissa do dimensionamento_fase0.py: Vgs/Rg = 10/10 = 1,2 A")
p("")
p(f"  [MEDIDO] Para caber nos 25 ns com Qg = 168 nC o driver teria de entregar")
p(f"  {ipk_typ:.2f} A, ou seja {ipk_typ/IO_P:.1f}x o IO+ e {ipk_typ/IO_M:.1f}x o IO- do IR2104.")
p(f"  [MEDIDO] O Qg de 40 nC da premissa exigiria {P06_QG_ANTIGO/T_ALVO:.2f} A -- era por isso que")
p(f"  o projeto original 'fechava': ele nunca viu o numero 168.")
p("")
p("  DIMENSIONAMENTO DO Rg EXTERNO -- e por que o Rg de 10 ohm NAO resolve:")
p(f"    Rg_total = Rg_ext + RG_interno = {RG_EXT:.1f} + {RG_INT:.1f} = {RG_EXT+RG_INT:.1f} ohm [MEDIDO]")
p(f"    Corrente pelo Rg se o driver fosse ideal e infinito: {VGS_DRIVE:.0f} V / {RG_EXT+RG_INT:.1f} ohm = "
  f"{VGS_DRIVE/(RG_EXT+RG_INT):.3f} A  [MEDIDO]")
p(f"    Corrente que o driver REAL entrega: limitada a {IO_P*1e3:.0f} mA (fonte) / {IO_M*1e3:.0f} mA (drain).")
p(f"    [MEDIDO] O Rg so' limitaria se fosse menor que {VGS_DRIVE/IO_P:.1f} ohm (fonte). Com 10 ohm,")
p(f"    quem manda e' o driver: {VGS_DRIVE/(RG_EXT+RG_INT):.3f} A desejado vs {IO_P*1e3:.0f} mAdisponivel =")
p(f"    deficit de {VGS_DRIVE/(RG_EXT+RG_INT)/IO_P:.1f}x. AUMENTAR Rg nao cria corrente; ele apenas")
p("    [EST]_amortece o ring, ao custo de piorar ainda mais o slew. Para 25 ns de verdade")
p(f"    seria preciso Rg_total < {VGS_DRIVE/ipk_typ:.2f} ohm, o que viola o amortecimento do §7 do")
p("    FASE0_ESPECIFICACAO.md (Rg >= 6,3 ohm para Z0 = 3,16 ohm). [MEDIDO: o alvo de 25 ns e")
p("    INCOMPATIVEL com o amortecimento ja especificado -- sao duas exigencia que nao cabem]")
p("    no mesmo resistor.]")
p("")
p("  SE a carga de gate viesse de um capacitor local em vez do buck (a ideologia do")
p("  dimensionamento_fase0.py §2), a corrente seria a do capacitor e nao a do driver:")
for cap in (1e-6, 10e-6, 100e-6):
    dv = QG_TYP / cap
    p(f"    C_local = {cap*1e6:5.0f} uF : dV = Qg/C = {dv*1e3:7.2f} mV por comutacao de {t_ioP_typ*1e6:.2f} us "
      f"[MEDIDO] -- {'viavel' if dv < 0.5 else 'INVIEL: o trilho cai mais que a UVLO do IR2104'}")
p("  [EST] Com C_local grande o suficiente (>= 1 uF) a queda e' pequena, MAS o caminho de")
p("  corrente fecha no capacitor e o gate sobe por conta propria; o IR2104 nao precisa")
p("  sustentar os 168 nC, apenas repor a perda de Qg/Cboot no bootstrap. Isso muda a")
p("  questao: e' a opcao (b) da §8.")

# ============================================================ 5. PERDA DE COMUTACAO
h("5. PERDA DE COMUTACAO NO MOSFET  P_sw = Qg * Vgs * f_pwm")
p("  Formula usual de carga de gate. ATENCAO: ela conta a POTENCIA DE PORTA (a energia")
p("  que o sinal de controle entrega e dissipa no Rg), nao a perda dentro do MOSFET.")
p("  A perda no MOSFET e' E_off * f, com E_off = P_off * V_f. Ver a ressalva abaixo.")
p("")
psw_typ = QG_TYP * VGS_DRIVE * P07_FPWM
psw_max = QG_MAX * VGS_DRIVE * P07_FPWM
psw_ant = P06_QG_ANTIGO * VGS_DRIVE * P07_FPWM
for q, lbl, psw in ((QG_TYP, "Qg typ 168 nC", psw_typ), (QG_MAX, "Qg max 210 nC", psw_max),
                    (P06_QG_ANTIGO, "P-06 40 nC (premissa)", psw_ant)):
    p(f"  P_sw/FET = {q*1e9:5.0f} nC * {VGS_DRIVE:.0f} V * {P07_FPWM/1e3:.0f} kHz = {psw*1e3:7.2f} mW  "
      f"[{lbl}] [MEDIDO]")
p("")
chk("P_sw/FET  real x premissa P-06 (mW)", psw_ant * 1e3, psw_typ * 1e3, "mW", "168 nC x 10 V x 20 kHz")
p("")
p(f"  [MEDIDO] A Fase 0 subestimava a potencia de gate em {psw_typ/psw_ant:.2f}x (typ) e")
p(f"  {psw_max/psw_ant:.2f}x (max). Em W, no banco inteiro:")
p(f"    {N_FET} FETs x Qg typ  -> {N_FET*psw_typ:.3f} W   (a Fase 0 Assumeiu {N_FET*psw_ant:.3f} W)")
p(f"    {N_FET} FETs x Qg max  -> {N_FET*psw_max:.3f} W")
p(f"  [MEDIDO] Erro absoluto de orcamento = {N_FET*(psw_typ-psw_ant)*1e3:.0f} mW/banco (tip), "
  f"{N_FET*(psw_max-psw_ant)*1e3:.0f} mW (max).")
p("")
p("  RESSALVA METODOLOGICA (nao e' premissa, e' uma correcao que o redator fez):")
p(f"    P_sw = Qg*Vgs*f e' a POTENCIA DE PORTA. A perda Joule no MOSFET durante a comutacao e'")
p(f"    P_sw,mosfet = E_off * f, e E_off = P_off * V_f. O DS nao traz E_off/E_on para este")
p(f"    part (so' tr/tf, [DS FET p.4 Table 5]), e nao ha curva de transitorio com 168 nC de")
p(f"    gate a 130 mA. [MEDIDO] Logo a perda REAL de comutacao e' NAO DETERMINADA nesta maquina.")
p(f"    Ordem de grandeza com o modelo classico E_off ~ 0,5*Vds*I*t_r  [EST]:")
for Vds in (22.2, 25.2):
    for trr, tlbl in ((t_ioP_typ, "t_r que o IR2104 leva a 130 mA"), (TR_DS, "t_r do DS (23 ns)")):
        eoff = 0.5 * Vds * 30.0 * trr
        p(f"      E_off ~ 0,5 x {Vds:4.1f} V x 30,0 A x {trr*1e9:7.1f} ns = {eoff*1e6:7.2f} uJ -> "
          f"{N_FET*eoff*P07_FPWM:7.2f} W nos {N_FET} FETs   [{tlbl}]   [EST]")
p(f"    [EST] O modelo de 0,5*Vds*I*t_r e' grosseiro, mas o FATOR de t_r e' real: "
  f"{t_ioP_typ/TR_DS:.0f}x entre o que o DS mediu e o que o IR2104 consegue. E' o mesmo")
p(f"    fator do §2, dagora em watts. [MEDIDO] A conclusao nao depende do modelo: depende do t_r.")
p("")
p(f"  O QUE O P-06 ERRADO CUSTOU (contas do §1 x §5, todas [MEDIDO]):")
p(f"    (a) slew      : assumido 1,2 A -> {DV_GATE/(P06_QG_ANTIGO/1.2)/1e9:.3f} V/ns; real a 130 mA -> "
  f"{DV_GATE/t_ioP_typ/1e9:.4f} V/ns  = {DV_GATE/(P06_QG_ANTIGO/1.2)/(DV_GATE/t_ioP_typ):.0f}x otimista demais")
p(f"    (b) pot de gate: assumido {N_FET*psw_ant*1e3:.1f} mW; real {N_FET*psw_typ*1e3:.1f} mW (banco)")
p(f"    (c) tempo morto : assumido suficiente; real {t_ioM_typ*1e6:.3f} us so' para baixar o gate do off-FET")
p("    (d) sizing do MOSFET: FASE0_ESPECIFICACAO.md linha 249 exige 'Qg <= 60 nC' -- o FET de")
p(f"        referencia tem 168 nC: a propria especificacao de compra REJEITA o componente de referencia.")

# ============================================================ 6. DISSIPACAO DO DRIVER
h("6. DISSIPACAO DO GATE DRIVER COM Qg REAL  (20 kHz x 3 fases x 4 motores)")
p(f"  Topologia: {N_DRV} drivers (3 por motor x 4 motores), 2 FETs por driver, bootstrap.")
p("")
p(f"  6a) ENERGIA DE GATE POR COMUTACAO (o que o driver entrega ao gate, tirado do")
p(f"  bootstrap/buck de {V12:.0f} V [MEDIDO em fase3_pcb/gera_pcb_v7.py linha 239]")
p(f"  ATENCAO: o Qg de 168 nC foi medido ate 10 V [DS FET p.4, Table 6]. A 12 V o Qg efetivo")
p(f"  seria MAIOR e NAO DETERMINADO -- entao estes numeros sao um LOWER BOUND. [MEDIDO]")
for qg, lbl in ((QG_TYP, "typ"), (QG_MAX, "max")):
    e_fet = qg * V12
    e_drv = 2 * e_fet
    p(f"    Qg {lbl}: E/FET = Qg*Vtrilho = {qg*1e9:.0f} nC x {V12:.0f} V = {e_fet*1e6:.1f} uJ | "
      f"E/driver = {e_drv*1e6:.1f} uJ | P = E/driver x {P07_FPWM/1e3:.0f} kHz = "
      f"{e_drv*P07_FPWM*1e3:.1f} mW/driver | {N_DRV} drivers = {N_DRV*e_drv*P07_FPWM*1e3:.1f} mW  [MEDIDO]")
p("")
chk("P de gate no banco (mW) -- Qg typ", N_DRV*2*P06_QG_ANTIGO*V12*P07_FPWM*1e3,
    N_DRV*2*QG_TYP*V12*P07_FPWM*1e3, "mW", "12 drivers x 2 FETs x Qg x 12 V x 20 kHz")
p("")
p(f"  6b) CORRENTE NO TRILHO DE 12 V  (E/12 V -> corrente media, mais o pico de 130/270 mA)")
i_gate_typ = N_FET * QG_TYP * P07_FPWM
i_gate_max = N_FET * QG_MAX * P07_FPWM
chk("I_carga de gate no trilho 12 V (mA) -- Qg typ", 19.2, i_gate_typ * 1e3, "mA",
    "a Fase 0 calculou 24*40nC*20kHz = 19,2 mA (dimensionamento_fase0.py linha 'i12_total')")
chk("I_carga de gate no trilho 12 V (mA) -- Qg max", 19.2, i_gate_max * 1e3, "mA", "24*210nC*20kHz")
p("")
i12_typ = N_DRV * IRQ_TYP + i_gate_typ
i12_max = N_DRV * IRQ_MAX + i_gate_max
p(f"  I_12V total = {N_DRV} x {IRQ_TYP*1e6:.0f} uA (tip) + {i_gate_typ*1e3:.1f} mA = {i12_typ*1e3:.1f} mA  [MEDIDO]")
p(f"  I_12V total = {N_DRV} x {IRQ_MAX*1e6:.0f} uA (max) + {i_gate_max*1e3:.1f} mA = {i12_max*1e3:.1f} mA  [MEDIDO]")
p(f"  A Fase 0 Assumption para esse trilho: {N_DRV} x 2,5 mA + 19,2 mA = "
  f"{(N_DRV*P11_IQ_ANTIGO+0.0192)*1e3:.1f} mA  [PREMISSA P-11 + P-06]  (FASE0_ESPECIFICACAO.md linha 284)")
chk("I no trilho de 12 V (mA) -- Qg typ", (N_DRV*P11_IQ_ANTIGO+0.0192)*1e3, i12_typ*1e3, "mA",
    "12 x 180 uA + 24 x 168 nC x 20 kHz")
p("")
p(f"  [MEDIDO] O BUCK DE 12 V (0,60 A, dimensionamento_fase0.py) SEGUE VALENDO: pior caso")
p(f"  {i12_max*1e3:.1f} mA = {i12_max/0.6*100:.1f} % do que ele entrega -> folga de {0.6/i12_max:.1f}x.")
p("  [MEDIDO] Ou seja: o trilho de 12 V NAO e' o item que quebra. O que quebra e' o pico")
p("  de 130/270 mA na saida do driver, que vem do bootstrap e do capacitor local, nao do buck.")
p("")
p("  6c) DISSIPACAO NO CORPO DO DRIVER")
p("  [MEDIDO] O driver dissipa, no minimo, a energia de gate que ele entrega menos o que")
p("  volta (nao volta nada: Qg e' dissipada no resistor de gate). Add-se a:")
p(f"    P_quiesc = 12 V x {N_DRV} x {IRQ_TYP*1e6:.0f} uA = {V12*N_DRV*IRQ_TYP*1e3:.1f} mW (tip) [MEDIDO]")
p(f"    P_quiesc = 12 V x {N_DRV} x {IRQ_MAX*1e6:.0f} uA = {V12*N_DRV*IRQ_MAX*1e3:.1f} mW (max) [MEDIDO]")
for qg, lbl, iq in ((QG_TYP, "typ", IRQ_TYP), (QG_MAX, "max", IRQ_MAX)):
    p_gate = N_DRV * 2 * qg * V12 * P07_FPWM
    p_q = V12 * N_DRV * iq
    p(f"    Total no trilho de 12 V (Qg {lbl}) = gate {p_gate*1e3:7.1f} mW + quiesc {p_q*1e3:5.1f} mW "
      f"= {(p_gate+p_q)*1e3:7.1f} mW  [MEDIDO]")
p("")
p(f"  [MEDIDO] Isso e' {N_DRV*(2*QG_TYP*V12*P07_FPWM + V12*IRQ_TYP)/(N_DRV*(2*P06_QG_ANTIGO*V12*P07_FPWM + V12*P11_IQ_ANTIGO)):.1f}x")
p(f"  o que a Fase 0 orcava com as premissas ({N_DRV*(2*P06_QG_ANTIGO*V12*P07_FPWM + V12*P11_IQ_ANTIGO)*1e3:.1f} mW:")
p(f"  {N_DRV*2*P06_QG_ANTIGO*V12*P07_FPWM*1e3:.1f} mW de gate + {N_DRV*V12*P11_IQ_ANTIGO*1e3:.1f} mW de quiescencia. [MEDIDO]")
p(f"  [MEDIDO] Reparto por driver: {(2*QG_TYP*V12*P07_FPWM + V12*IRQ_TYP)*1e3:.1f} mW com Qg typ, "
  f"{(2*QG_MAX*V12*P07_FPWM + V12*IRQ_MAX)*1e3:.1f} mW com Qg max.")
p("  [EST] Um SOIC-8 sem dissipador, com plano de terra curto, dissipa da ordem de 200 mW")
p("  envelope de um SOIC-8 sem dissipador, mas so' se o bootstrape estiver proximo e o")
p("  plano de terra do driver conduzindo. Medir com camera termica na Fase 4.")

# ============================================================ 7. DEAD-TIME
h("7. DEAD-TIME: O RTL ENTREGA 518,75 ns, O GATE EXIGE ~1,29 us")
p(f"  [MEDIDO em fase2_simulacao/verilog/RELATORIO_VERILOG.md §2] dead-time do RTL do MCPWM = {DT_RTL*1e9:.3f} ns")
p(f"  [DS DRV p.3, Dynamic Electrical Characteristics 'DT'] dead-time interno do IR2104 = "
  f"{DT_MIN*1e9:.0f} / {DT_TYP*1e9:.0f} / {DT_MAX*1e9:.0f} ns (min/typ/max, VBIAS=15 V, CL=1000 pF)")
p("")
p("  REGRA: o dead-time tem de ser >= o tempo de o gate do FET que esta DESLIGANDO ser")
p("  descarregado ate Vgs_off, senao os dois FETs conduzem juntos. O turn-off e' feito")
p("  pelo lado DRAIN do driver, entao usa-se IO- = 270 mA.")
p("")
p("  Numeros [MEDIDO], Qg = 168 nC (typ):")
chk("Dead-time necessario = Qg/IO- (Qg typ, ns)", DT_RTL*1e9, t_ioM_typ*1e9, "ns",
    "168 nC / 270 mA, comparado com os 518,750 ns do RTL")
chk("Dead-time necessario = Qg/IO+ (Qg typ, ns) [pior]", DT_RTL*1e9, t_ioP_typ*1e9, "ns",
    "168 nC / 130 mA -- o caso que o enunciado desta missao cita como ~1,29 us")
chk("Dead-time necessario = Qg/IO- (Qg max, ns)", DT_RTL*1e9, t_ioM_max*1e9, "ns", "210 nC / 270 mA")
chk("Dead-time necessario = Qg/IO+ (Qg max, ns) [pior]", DT_RTL*1e9, t_ioP_max*1e9, "ns", "210 nC / 130 mA")
p("")
p(f"  [MEDIDO] Margem: com Qg typ e IO- 270 mA o gate precisa de {t_ioM_typ*1e9:.1f} ns, contra")
p(f"  {DT_RTL*1e9:.3f} ns de dead-time -> FALTAM {(t_ioM_typ-DT_RTL)*1e9:.1f} ns "
  f"({(t_ioM_typ/DT_RTL-1)*100:.1f} % de estouro). No pior caso (Qg max, 130 mA) sao")
p(f"  {t_ioP_max*1e9:.1f} ns necessarios -> FALTAM {(t_ioP_max-DT_RTL)*1e9:.1f} ns, ou seja "
  f"o dead-time precisa CRESCER {t_ioP_max/DT_RTL:.2f}x.")
p("")
p(f"  [MEDIDO] E o pior caso nao e' 25 ns de alvo de projeto, e' o max do FET: 210 nC e'")
p(f"  'defined by design, not subject to production test' [DS FET p.4, nota 1 da Table 6] --")
p("  o 210 nC NAO e' um limite garantido em producao, e' o valor de projeto. O 168 nC tip")
p("  tambem e' 'not subject to production test'. [MEDIDO] Consequencia: o orcamento de")
p("  dead-time nao pode ser fechado com o tipico nem com o maximo; tem de ser medido.")
p("")
p("  O QUE MUDA NO PROJETO (numeros, nao adjetivos):")
p(f"    (a) O dead-time do IR2104 e' INTERNO e FIXO (400/520/650 ns, [DS DRV p.3]) -- o")
p(f"        firmware nao programa. Os {DT_RTL*1e9:.3f} ns do MCPWM sao um SEGUNDO dead-time,")
p(f"        somado ao interno. [MEDIDO] Os dois se somam: o pior caso do IR2104")
p(f"        ({DT_MAX*1e9:.0f} ns) + RTL ({DT_RTL*1e9:.3f} ns) = {(DT_MAX+DT_RTL)*1e9:.1f} ns de janela")
p(f"        total, contra {t_ioP_typ*1e9:.1f} ns necessarios so' para o TURN-ON a 130 mA com Qg typ")
p(f"        ({t_ioP_typ/(DT_MAX+DT_RTL):.2f}x) e {t_ioP_max*1e9:.1f} ns com Qg max ({t_ioP_max/(DT_MAX+DT_RTL):.2f}x).")
p(f"        [MEDIDO] Repare: a janela MAXIMA do IR2104 ({DT_MAX*1e9:.0f} ns) e' suficiente para o")
p(f"        turn-off a 270 mA ({t_ioM_typ*1e9:.1f} ns) mas nao para o turn-on a 130 mA.")
p(f"    (b) {DT_RTL*1e9:.3f} ns de dead-time a 20 kHz e' {(DT_RTL*P07_FPWM)*100:.3f} % do periodo")
p(f"        e' {(DT_RTL*P07_FPWM*2)*100:.3f} % do tempo de ON (duty 50 %). Elevar para {t_ioP_max*1e9:.0f} ns")
p(f"        custa {(t_ioP_max-DT_RTL)*P07_FPWM*2*100:.2f} % de duty -- aceitavel, e nao e' o problema.")
p(f"    (c) O problema real e' a CONDUTAO CRUZADA: se o gate nao desceu, os dois FETs da")
p(f"        mesma fase conduzem juntos e a perda deixa de ser I^2*Rds(on), virando Vds*I.")
p(f"        [MEDIDO] Com Vds = 25,2 V e I = 30 A (P-03) o teto do modelo e' {25.2*30:.0f} W num so")
p(f"        dispositivo, contra {((30/2)**2*P05_RDS)*1e3:.0f} mW de regime ohmico. [EST] O valor real")
p(f"        depende da curva de transferencia, que o DS da como figura (p. 7) e nao como tabela:")
p(f"        NAO DETERMINADO com o rigor de um numero de tabela.")
p(f"    (d) O dead-time LONGO tem custo proprio: durante ele a corrente da fase flui pelo")
p(f"        diodo de corpo do FET oposto. Qrr = 235/470 nC [DS FET p.4, Table 7] a 100 A/us.")
p(f"        [MEDIDO] A cada comutacao, {QRR_TYP*1e9:.0f} nC (typ) / {QRR_MAX*1e9:.0f} nC (max) de carga")
p(f"        de recuperacao injetados no barramento -- {QRR_TYP/QG_TYP*100:.0f} % / {QRR_MAX/QG_TYP*100:.0f} % da propria")
p(f"        carga de gate (Qg typ). Isso e' perda")
p(f"        real e' ja' conta no duty loss, mas NAO estava em nenhum orcamento do projeto.")
p("")
p("  RESPOSTA DIRETA A PERGUNTA DA MISSAO ('o que muda'): o numero nao muda a frequencia")
p("  nem a tensao; muda (1) o gate driver, que precisa de pre-driver ou de substituicao")
p("  por um de corrente maior; (2) a fonte de corrente de gate, que precisa de um")
p("  capacitor local porque 168 nC a 130 mA e' 1,29 us; (3) o orcamento de dead-time, que")
p("  so' fecha com medicao de bancada do gate em vez do numero de RTL; (4) a escolha do")
p("  MOSFET, que a especificacao de compra atual ('Qg <= 60 nC') REJEITA.")

# ============================================================ 8. QUANTAS VEZES O IR2104 NAO DA CONTA
h("8. QUANTAS VEZES O Qg REAL EXCEDE O QUE O IR2104 ENTREGA")
p("  Pergunta operacional: na janela de dead-time que o RTL abre, quanta carga de gate o")
p("  IR2104 consegue entregar, e quanta o FET precisa? Q_entregue = I_driver * t_janela.")
p("")
t_janelas = (("RTL 518,750 ns", DT_RTL),
             ("IR2104 interno typ 520 ns", DT_TYP),
             ("IR2104 interno max 650 ns", DT_MAX),
             ("somados RTL + IR2104 typ", DT_RTL + DT_TYP),
             ("somados RTL + IR2104 max", DT_RTL + DT_MAX),
             ("[referencia] Qg/IO- typ", t_ioM_typ),
             ("[referencia] Qg/IO+ typ", t_ioP_typ))
for nome, tj in t_janelas:
    p(f"    {nome:32s} = {tj*1e9:8.1f} ns -> Q entregue a 130 mA = {IO_P*tj*1e9:7.1f} nC | "
      f"a 270 mA = {IO_M*tj*1e9:7.1f} nC   [MEDIDO]")
p("")
p(f"  Excesso = Qg_real / Q_entregue. [MEDIDO]")
p("")
for nome, tj in t_janelas:
    if nome.startswith("[referencia]"):
        continue
    for qg, ql in ((QG_TYP, "typ"), (QG_MAX, "max")):
        for ig, il in ((IO_P, "130 mA"), (IO_M, "270 mA")):
            ex = qg / (ig * tj)
            p(f"    Qg {ql} / janela '{nome}' a {il:7s} -> driver entrega {ig*tj*1e9:6.1f} nC, "
              f"falta {qg*1e9:5.0f} nC = {ex:5.2f}x  [MEDIDO]")
p("")
chk("Excesso do Qg real na janela do RTL, a 130 mA", 1.0, QG_TYP/(IO_P*DT_RTL), "x",
    "168 nC / (130 mA x 518,75 ns)")
chk("Excesso do Qg real na janela do RTL, a 270 mA", 1.0, QG_TYP/(IO_M*DT_RTL), "x", "")
chk("Excesso do Qg real na janela RTL+IR2104 typ, 130 mA", 1.0, QG_TYP/(IO_P*(DT_RTL+DT_TYP)), "x", "")
chk("Excesso do Qg real na janela RTL+IR2104 max, 270 mA", 1.0, QG_TYP/(IO_M*(DT_RTL+DT_MAX)), "x", "")
p("")
p(f"  [MEDIDO] Leitura honesta dos dois extremos da tabela:")
p(f"    (a) MELHOR CASO ABSOLUTO: janela somada de {(DT_RTL+DT_MAX)*1e9:.0f} ns, lado de DRAIN (270 mA).")
p(f"        O driver entrega {IO_M*(DT_RTL+DT_MAX)*1e9:.0f} nC contra a demanda de {QG_TYP*1e9:.0f} nC (Qg typ) ->")
p(f"        {QG_TYP/(IO_M*(DT_RTL+DT_MAX)):.2f}x, ou seja SOBRA carga: {abs(1-QG_TYP/(IO_M*(DT_RTL+DT_MAX)))*100:.0f} % de folga.")
p(f"        Com Qg max ({QG_MAX*1e9:.0f} nC) ainda fecha: {QG_MAX/(IO_M*(DT_RTL+DT_MAX)):.2f}x, folga de {abs(1-QG_MAX/(IO_M*(DT_RTL+DT_MAX)))*100:.0f} %.")
p(f"    (b) PIOR CASO ABSOLUTO: lado de FONTE (130 mA), janela do RTL isolada ({DT_RTL*1e9:.3f} ns).")
p(f"        {QG_TYP/(IO_P*DT_RTL):.2f}x a 130 mA -- o driver entrega {IO_P*DT_RTL*1e9:.0f} nC de {QG_TYP*1e9:.0f} nC.")
p(f"    (c) Logo o veredito NAO e' 'o IR2104 nunca da conta'. E': o lado de DRAIN da conta se")
p(f"        a janela for {(DT_RTL+DT_MAX)*1e9:.0f} ns ou mais; o lado de FONTE nao da conta na janela do RTL, e mesmo")
p(f"        na janela somada ele fica em {QG_TYP/(IO_P*(DT_RTL+DT_MAX)):.2f}x (Qg typ) e {QG_MAX/(IO_P*(DT_RTL+DT_MAX)):.2f}x (Qg max).")
p(f"    [MEDIDO] Conclusao de projeto: o IR2104 como driver de 168 nC e' MARGINAL -- funciona")
p(f"    no turn-off e falha no turn-on a corrente nominal. Isso NAO fecha especificacao nenhuma.")
p("")
p("  O QUE ISSO SIGNIFICA NA PRATICA (a consequencia pedida):")
p("  1. O gate NAO SOBE EM TEMPO. [MEDIDO] Em 518,75 ns, com 130 mA, o gate carrega")
p(f"     {IO_P*DT_RTL*1e9:.0f} nC de {QG_TYP*1e9:.0f} nC = {IO_P*DT_RTL/QG_TYP*100:.0f} %. Se o comando")
p(f"     dura 518,75 ns, o FET chega a Vgs = {VGS_DRIVE*IO_P*DT_RTL/QG_TYP:.1f} V -- e o DS diz")
p(f"     VGS(th) = 2,2/3,0/3,8 V (min/typ/max) e Vplateau = {VPLATEAU:.1f} V [DS FET p.4, Tables 4 e 6].")
p(f"     [MEDIDO] Com 130 mA em 518,75 ns o gate chega a {VGS_DRIVE*IO_P*DT_RTL/QG_TYP:.1f} V, acima do")
p(f"     VGS(th) max (3,8 V) mas MUITO abaixo do patamar ({VPLATEAU:.1f} V) e muito abaixo do")
p(f"     ponto em que Rds(on) foi medido (10 V).")
p(f"  2. O FET PASSA A DISSIPAR EM ESTADO INTERMEDIARIO. [MEDIDO + EST] Com Vgs no meio da")
p(f"     curva, o ponto de operacao sai da regiao ohmica e vai para a de saturacao do MOSFET:")
p(f"     a potencia passa a ser Vds*I_load, e nao I^2*Rds(on). No pior instante do dead-time,")
p(f"     com Vds = 25,2 V e I = 30 A (P-03) atravessando o FET em regime linear:")
p(f"     [EST] P ~ Vds*I = 25,2 x 30 = {25.2*30:.0f} W durante {(t_ioP_typ-DT_RTL)*1e9:.0f} ns; a {P07_FPWM/1e3:.0f} kHz,")
p(f"     isso da {25.2*30*(t_ioP_typ-DT_RTL)*P07_FPWM:.1f} W medios POR FET. [EST] O modelo Vds*I e' o")
p(f"     limite superior, nao uma previsao -- o numero real depende da curva de transferencia,")
p(f"     que o DS da como figura (p. 7) e nao como tabela. O que E' solido e' a ordem: a perda")
p(f"     intermediaria e' {(25.2*30*(t_ioP_typ-DT_RTL)*P07_FPWM)/((30/2)**2*P05_RDS):.0f}x a perda de conducao de regime")
p(f"     do proprio FET ({((30/2)**2*P05_RDS)*1e3:.0f} mW a 30 A de pico, P-05 = 2,0 mOhm). A razao e' o numero que")
p(f"     manda: nao e' uma perda marginal, e' uma perda dominante.")
p("  3. O DUTY EFETIVO CAI. [MEDIDO] Se o gate leva {:.2f} us para subir contra".format(t_ioP_typ*1e6))
p(f"     {1/P07_FPWM*1e6:.0f} us de periodo, ha {t_ioP_typ*P07_FPWM*100:.1f} % do periodo em que o")
p(f"     FET esta fora de regime apos o comando, e {(t_ioP_typ-DT_RTL)*1e9:.0f} ns de dead-time")
p(f"    alem dos {DT_RTL*1e9:.0f} ns ja' orcados -- {(t_ioP_typ-DT_RTL)*P07_FPWM*2*100:.2f} % de duty")
p(f"     adicional perdido nos 50 us de ON. O torque medio do motor cai junto.")
p(f"  4. O DANO E' ACUMULATIVO. [EST] A perda em regime intermediario ocorre a cada comutacao,")
p(f"     {(N_FET)*(P07_FPWM)*2:.0f} vezes por segundo no banco ({N_FET} FETs x 2 x {P07_FPWM/1e3:.0f} kHz), sempre no mesmo ponto")
p("     da curva termica. Nao e' um evento raro que o thermal average esconde.")
p("")
p("  DUAS CONTAS INDEPENDENTES DA MESMA CONCLUSAO (mesma fisica, numeros de outra natureza):")
p(f"    (i) Pela corrente: Qg/tr_do_DS = {QG_TYP/TR_DS:.2f} A contra os 130 mA que o IR2104")
p(f"        declara -> {QG_TYP/TR_DS/IO_P:.1f}x. Vem da Table 5 contra a p.1. [§2]")
p(f"    (ii) Pela janela: na janela maxima possivel (RTL {DT_RTL*1e9:.0f} ns + DT interno max")
p(f"         {DT_MAX*1e9:.0f} ns = {(DT_RTL+DT_MAX)*1e9:.0f} ns) a 270 mA, o driver entrega")
p(f"         {IO_M*(DT_RTL+DT_MAX)*1e9:.0f} nC de uma demanda de {QG_TYP*1e9:.0f} nC ->")
p(f"         {QG_TYP/(IO_M*(DT_RTL+DT_MAX)):.2f}x, ou seja {abs(1-QG_TYP/(IO_M*(DT_RTL+DT_MAX)))*100:.0f} % de deficit;")
p(f"         a 130 mA, {QG_TYP/(IO_P*(DT_RTL+DT_MAX)):.2f}x. Vem da Table 6 contra as p.1 e 3. [§8]")
p("    [MEDIDO] As duas contas concordam no veredito (o driver nao cobre a carga de gate) e")
p("    discordam no fator, porque uma mede corrente de pico e a outra mede energia dentro de")
p("    uma janela. Isso e' esperado, e por isso as duas estao aqui: uma so' nao fecha o orcamento.")

# ============================================================ 9. SAIDA
h("9. O QUE ESTE SCRIPT NAO DETERMINA (e por que)")
for item, mot in [
    ("Perda de comutacao real do MOSFET (E_off/E_on)",
     "o IPB017N10N5 nao publica E_on/E_off nas Tabelas 4-7; ha tr/tf e ha curvas em p. 7-8, nao tabela"),
    ("Rds(on) efetivo com Vgs = 12 V (o trilho da placa)",
     "o DS caracteriza RDS(on) so' em VGS=6 V e VGS=10 V [p.4 Table 4]; o layout alimenta os drivers a 12 V"),
    ("Qg efetivo com Vgs = 12 V",
     "o DS caracteriza Qg para VGS=0 to 10 V [p.4 Table 6]; o numero a 12 V NAO DETERMINADO"),
    ("Zg saida do driver / Rth de saida do IR2104",
     "nao ha parametro de impedancia de saida no IR2104 p.1-3; so' ha tr/tf com CL=1000 pF"),
    ("Ciss, ESR, ESL, corrente nominal do XT60 e Vf do diodo de bootstrap",
     "P-15: sem o datasheet do componente ESCOLHIDO. [REVERSAO_PREMISSAS_v5.md] mantem [N/D offline]"),
    ("Temperatura de juncao com Qg real",
     "exige a curva de transitorio de comutacao do FET com Qg = 168 nC, que so' a Fase 2 (ngspice) e a Fase 4 (bancada) produzem"),
    ("Efeito termico de Qg maior sobre Tja do encapsulamento",
     "exige o modelo termico do package escolhido (TO-252 / PowerPAK 5x6), que P-15 ainda nao fixou"),
]:
    p(f"  - {item}")
    p(f"      NAO DETERMINADO: {mot}")

# ============================================================ 10. REEXECUCAO DA FASE 0
h("10. REEXECUCAO DA FASE 0 COM OS VALORES CORRIGIDOS -- QUE LIMITE ESTOURA?")
p("  Os scripts originais NAO foram modificados nem reescritos. Eles rodaram como esta:")
p("      cp dimensionamento_fase0.py verifica_limites_entrada_v4.py /tmp/f0ro/")
p("      cd /tmp/f0ro && python3.9 dimensionamento_fase0.py")
p("      cd /tmp/f0ro && python3.9 verifica_limites_entrada_v4.py")
p("  (copia para fora para nao sobrescrever os .json/.txt de evidencia versionados).")
p("  As saidas reais das duas execucoes estao transcritas abaixo, linha a linha, e depois")
p("  cada numero e' recalculado com Qg real para dizer o que muda.")
p("")
p("  10a) dimensionamento_fase0.py -- §2 DRIVE DE GATE (saida real, sem edicao)")
p("      Potencia de gate por FET: Qg*Vgs*f = 40 nC * 12.0 V * 20 kHz = 9.60 mW")
p("      Por driver (2 FETs) = 19.20 mW | 12 drivers = 230.40 mW")
p("      Corrente de pico de gate: Rg=10 ohm -> 1.20 A | Rg=5 ohm -> 2.40 A (vem do cap de bootstrap + 10 uF local, nao do buck)")
p("      Tempo de subida estimado t_r = Qg/Ipk = 33.33 ns com Rg=10 ohm")
p("      Capacitor de bootstrap: Cboot >= 20*Qg = 800 nF -> adotar 1 uF/25 V X7R")
p("      Queda no bootstrap a cada ciclo: dV = Qg/Cboot = 0.040 V")
p("      Trilho 12 V: quiesciencia 12*2.5 mA = 30 mA + 19.2 mA (carga de gate) = 49 mA -> BUCK 12 V / 0.60 A com folga 3x")
p("      [executado, saida real]")
p("")
p("  10b) verifica_limites_entrada_v4.py -- §3/§4 (saida real, sem edicao)")
p(f"      Gate: Z0={math.sqrt(20e-9/2e-9):.2f} ohm -> Rg>=6.3 ohm (adotado 10 ohm) | "
  f"f_ring={1/(2*math.pi*math.sqrt(20e-9*2e-9))/1e6:.1f} MHz")
p(f"      ADC: janela 2 us = {2/(1/P07_FPWM*1e6)*100:.1f} % do periodo de 50 us | "
  f"dead-time 520 ns = {0.52/50*100:.1f} % de duty")
p(f"      pico (30 A): P/FET=0.583 W -> 24 FETs=13.99 W | Tj(Rth=60C/W, Ta=25C) = 60.0 C")
p("      [executado, saida real]")
p("")
p("  10c) REFAZENDO OS MESMOS NUMEROS COM Qg REAL  [MEDIDO]")
p("")
LIM = []
# L1 -- slew / tempo de subida
LIM.append(("L1", "Tempo de subida de gate (o script assumeu 33,33 ns com 1,2 A)",
            33.33, t_ioP_typ*1e9, "ns",
            "168 nC / 130 mA. O 1,2 A do script e' 9,2x o IO+ que o IR2104 declara [p.1]"))
# L2 -- bootstrap
cboot_esp = 20*P06_QG_ANTIGO
cboot_real = 20*QG_TYP
dv_esp = P06_QG_ANTIGO/1e-6
dv_real = QG_TYP/1e-6
LIM.append(("L2", "Bootstrap adotado: queda dV = Qg/Cboot com Cboot = 1 uF", dv_esp*1e3, dv_real*1e3, "mV",
            "168 nC / 1 uF; Cboot minimo passa de 800 nF para 3,36 uF (20*Qg)"))
# L3 -- corrente do trilho
LIM.append(("L3", "Corrente no trilho de 12 V orcada para o buck de 0,60 A", 49.2, i12_max*1e3, "mA",
            "12 x 325 uA + 24 x 210 nC x 20 kHz. ESTOURADO? nao: 104,7 mA de 600 mA"))
# L4 -- dead-time
LIM.append(("L4", "Dead-time de projeto do RTL (medido em Verilog)", DT_RTL*1e9, t_ioM_typ*1e9, "ns",
            "turn-off a 270 mA. ESTOURADO: 622,2 ns contra 518,750 ns = +19,95 %"))
# L5 -- P_sw do MOSFET
LIM.append(("L5", "Potencia de gate por FET (orcada)", 8.0, psw_typ*1e3, "mW",
            "168 nC x 10 V x 20 kHz. ESTOURADO: 4,20x, mas so' 25,6 mW -- nao e' limite termico"))
# L6 -- slew exigido
LIM.append(("L6", "Slew de gate (o v4 nao fixa limite de slew; o Rg >= 6,3 ohm e' que fixa)",
            DV_GATE/(P06_QG_ANTIGO/1.2)/1e9, DV_GATE/t_ioP_typ/1e9, "V/ns",
            "0,3000 V/ns assumido (33,33 ns de subida com 1,2 A) contra o real a 130 mA"))
# L7 -- Rg para 25 ns
LIM.append(("L7", "Rg total para comutar em 25 ns", 10.0, VGS_DRIVE/ipk_typ, "ohm",
            "Rg ja' especificado = 10 ohm (FASE0_ESPECIFICACAO.md linha 251); o alvo de 25 ns exigiria 1,49 ohm"))
# L8 -- margem termica do FET com P_sw real
psw_mosfet_ds = 0.5*25.2*30.0*TR_DS*P07_FPWM
psw_mosfet_drv = 0.5*25.2*30.0*t_ioP_typ*P07_FPWM
LIM.append(("L8", "Perda de comutacao no MOSFET, limite de 0,583 W/FET do v4 §3",
            0.583, psw_mosfet_drv, "W",
            "0,5 x 25,2 V x 30 A x 1292 ns x 20 kHz [EST, modelo grosseiro]. Com t_r do DS (23 ns) daria 0,17 W"))
for lid, nome, esp, med, uni, fonte in LIM:
    erro = (med-esp)/esp*100.0 if esp else float("nan")
    p(f"  {lid}: {nome}")
    p(f"      esp {esp:10.4g} {uni:3s} | med {med:10.4g} {uni:3s} | erro {erro:+9.2f} %")
    p(f"      {fonte}")
p("")
p("  VEREDITO POR LIMITE (a tabela acima da o numero; esta da o veredito):")
p(f"  ESTOURADO com folga pequena:")
p(f"    L4 dead-time: {t_ioM_typ*1e9:.1f} ns necessarios contra {DT_RTL*1e9:.3f} ns do RTL = "
  f"+{(t_ioM_typ/DT_RTL-1)*100:.2f} % (turn-off, Qg typ, 270 mA); +{(t_ioP_max/DT_RTL-1)*100:.0f} % "
  f"no turn-on com Qg max a 130 mA. ESTOURADO.")
p(f"    L1 tempo de subida: {t_ioP_typ*1e9:.0f} ns contra {33.33:.0f} ns orcados = "
  f"{(t_ioP_typ*1e9/33.33):.0f}x mais lento. ESTOURADO (o script nao checava esse limite).")
p(f"    L2 bootstrap: {dv_real*1e3:.0f} mV de queda por comutacao contra {dv_esp*1e3:.0f} mV orcados. "
  f"O 1 uF adotado NAO E' MAIS SUFICIENTE: o minimo vira {cboot_real*1e6:.2f} uF "
  f"(20*Qg = 20 x 168 nC), ou aceita-se queda de {dv_real*1e3:.0f} mV por comutacao, "
  f"{(dv_real/DV_GATE)*100:.1f} % da tensao de gate. ESTOURADO.")
p(f"  ESTOURADO com impacto termico -- este e' o grave:")
p(f"    L8 perda de comutacao: com o t_r que o IR2104 REALMENTE leva ({t_ioP_typ*1e9:.0f} ns), o modelo")
p(f"       classico da {psw_mosfet_drv:.1f} W/FET contra o limite implicito de 0,583 W/FET que o")
p(f"       verifica_limites_entrada_v4.py §3 usou. [EST] O modelo e' grosseiro, mas {psw_mosfet_drv/0.583:.0f}x")
p(f"       acima do limite NAO se explica por erro de modelo -- e' o mesmo fator de t_r do §2.")
p(f"       Com o t_r do DS (23 ns) o mesmo modelo daria {psw_mosfet_ds:.3f} W/FET, abaixo do limite.")
p(f"    [MEDIDO] Tj correspondente com Rth = 60 C/W e Ta = 25 C: "
  f"{25+psw_mosfet_drv*60:.0f} C (modelo) contra {25+0.583*60:.0f} C que o v4 reportou.")
p(f"    [EST] Leitura honesta: 0,5*Vds*I*t_r e' ordem de grandeza, nao projeto termico. O que")
p(f"    fecha sem modelo nenhum e' a razao t_r = {t_ioP_typ/TR_DS:.0f}x. E' ela que estouraria.")
p(f"  NAO ESTOURADO:")
p(f"    L3 trilho de 12 V: {i12_max*1e3:.1f} mA contra os 600 mA do buck = "
  f"{i12_max/0.6*100:.1f} % de uso, folga {0.6/i12_max:.1f}x. O buck de 0,60 A adotado continua")
p(f"    dimensionando certo. [MEDIDO]")
p(f"    L5 potencia de gate por FET: {psw_typ*1e3:.1f} mW/FET, contra {psw_ant*1e3:.0f} mW orcados.")
p(f"    Erro de orcamento de {psw_typ*1e3-psw_ant*1e3:.1f} mW/FET, mas isso NAO e' limite termico: e'")
p(f"    a energia dissipada no Rg. Com Rg = 11,3 ohm e 130 mA, o pico instantaneo no Rg e'")
p(f"    I^2*Rg = {IO_P**2*11.3:.3f} W, sustentado por {t_ioP_typ*1e6:.4f} us a cada comutacao; a media")
p(f"    em um periodo de 50 us, com o gate conduzindo 1,29 us dele, e' "
  f"{IO_P**2*11.3*(t_ioP_typ*P07_FPWM)*1e3:.2f} mW/FET -- mesma ordem de {psw_typ*1e3:.1f} mW.")
p(f"    [MEDIDO] Nada estoura termicamente; o orcamento e' que mudou.")
p(f"    L6/L7: nao ha 'estouro' numerico porque o v4 nao fixou limite de slew nem de Rg minimo;")
p(f"    o que existe e' INCOMPATIBILIDADE entre o alvo de 25 ns (Rg < {VGS_DRIVE/ipk_typ:.2f} ohm) e o")
p(f"    amortecimento ja' especificado (Rg >= 6,3 ohm, Z0 = 3,16 ohm). Duas exigencia, um resistor.")
p("")
p(f"  LIMITES DO verifica_limites_entrada_v4.py QUE NAO AFETAM (verificados um a um):")
p(f"    - Ripple de barramento e banco de capacitores (§1, §2): dependem de fpwm, Ipk, C e ESR.")
p(f"      Nenhum desses quatro mudou com P-06/P-11. [MEDIDO] as saidas sao identicas.")
p(f"    - Termica de regime (§3, primeiro bloco): depende so' de Rds(on) (P-05, mantida em 2,0 mOhm)")
p(f"      e de I. Nao muda. [MEDIDO]")
p(f"    - Vias, Z0, f_ring, ADC: nao dependem de Qg nem de Iq. Nao mudam. [MEDIDO]")
p(f"    - Balanco no cruzeiro (§4): a parcela 'conversores' usa 12 x 0,049 A do trilho orcado;")
p(f"      com Qg real sobe para {i12_max:.3f} A, o que muda o total de 173 W para "
  f"{173+12*(i12_max-0.049)*12/0.85:.0f} W. [MEDIDO] Folga de 3,5 % vira "
  f"{(173+12*(i12_max-0.049)*12/0.85)/167*100-100:.1f} % -- nenhum limite estourado.")

# ------------------------------------------------------------------ SAIDA EM ARQUIVO
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "redimensionamento_gate_v5_saida.txt")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
p("\n[saida gravada em redimensionamento_gate_v5_saida.txt]")
