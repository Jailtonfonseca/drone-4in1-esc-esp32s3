#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ORCAMENTO DE COMPONENTES -- projeto drone (ESC 4x + ESP32-S3 na mesma PCB)

Fontes de verdade:
  - Quantidades: fase0_especificacao/lista_componentes_fase0.csv
    (lida linha a linha; a tabela de precos abaixo e' indexada na MESMA ordem
     e o script FALHA se o nome do item nao bater -> nao existe preco orfao)
  - Dolar: R$ 5,1312 / US$  (Bloomberg Linea, 11/09/2026)
  - Impostos de importacao (Remessa Conforme, 2026): II 60% acima de US$50 com
    deducao fixa de US$30 + ICMS 17% (fonte: Valor/Min. Fazenda, Portaria 1.342)
  - Montagem JLCPCB: setup US$ 8 + US$ 0,0017/joint (pagina oficial jlcpcb.com/smt-assembly)

Confianca de cada preco:
  [COT]  = valor cotado nesta sessao, com fonte/URL no campo 'fonte'
  [CALC] = derivado de uma cotacao real (ex.: preco nacional = US$ * dolar * k,
           com k medido em 2 itens onde existem os dois lados)
  [EST]  = referencia propria de mercado, SEM fonte ao vivo -> tratar como ordem
           de grandeza, nao como cotacao

Saida: orcamento_detalhado.csv, orcamento_por_bloco.csv, custo_por_bloco.png, ORCAMENTO.md
"""
import csv, io, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = os.path.join(BASE, "fase0_especificacao", "lista_componentes_fase0.csv")
OUT = os.path.join(BASE, "orcamento")

# ---------------------------------------------------------------- parametros
DOLAR = 5.1312          # [COT] Bloomberg Linea 11/09/2026
K_NAC = 3.20            # [CALC] markup medio do mercado nacional sobre (preco LCSC * dolar)
K_NAC_MIN, K_NAC_MAX = 2.70, 3.70
MOQ_FACTOR = 1.15       # [EST] folga de compra minima / arredondamento de lote
FRETE_INT_USD = 35.0    # [EST] frete internacional (LCSC/JLCPCB, DHL/4PX)
II, DEDUCAO_USD, ICMS, IOF = 0.60, 30.0, 0.17, 0.035
FRETE_NAC_BRL = 50.0    # [EST] frete nacional somado (Mercado Livre, varios vendedores)
FAB_USD_MIN, FAB_USD_MAX = 70.0, 150.0   # [EST] 5 pcs, 4 camadas, 2 oz, 352 cm2 -- COTAR DE VERDADE
JOINTS = 800            # [EST] juntas SMD (board v6: 889 pads, dos quais ~90 PTH)
SETUP_USD, STENCIL_USD, EXT_PART_USD, N_EXT_PARTS = 8.0, 1.5, 3.0, 10
PIOR_CASO = 1.25        # [EST] reserva de engenharia (retrabalho, peca queimada, respin de stencil)

# ------------------------------------------------------- tabela de precos
# Ordem = ordem exata das linhas do CSV da Fase 0.
# linha = (item_no_csv, preco_unit_USD, conf, fonte/observacao)
PRECOS = [
 ("Conector de bateria",              0.58, "[CALC]", "ML: XT60 3 pares R$28,78 -> R$9,59/par / (5,1312*3,2)"),
 ("TVS unidirecional",                0.12, "[EST]",  "SMBJ33A SMB, ~US$0,10-0,15 no LCSC"),
 ("P-FET anti-inversao",              0.55, "[EST]",  "P-ch 40V TO-252, ~US$0,4-0,8"),
 ("Resistor de gate do P-FET + zenner",0.03,"[EST]",  "kit de passivos"),
 ("Capacitor de entrada",             1.10, "[EST]",  "polimero SMD 470uF/35V (PTH radial low-ESR = R$1,67 COT moduloeletronica)"),
 ("Ceramico de alta freq.",           0.14, "[EST]",  "10uF/50V X7R 1206"),
 ("Ceramico de alta freq.",           0.006,"[EST]",  "100nF/50V X7R 0402"),
 ("MOSFET N",                         0.45, "[EST]",  "N-ch 40V ~2-3 mOhm TO-252; NCE3050K (30V) = US$0,09 COT LCSC, 40V e' mais caro"),
 ("Dissipador / area de cobre",       0.00, "[-]",    "GERADO NO LAYOUT (custo no preco do cobre da PCB)"),
 ("Driver half-bridge single-input",  0.30, "[EST]",  "EG2134/EG2133: EG2133 = US$0,2222 COT (LCSC)"),
 ("Resistor de gate",                 0.010,"[EST]",  "10 ohm 0805"),
 ("Resistor de gate (desliga)",       0.010,"[EST]",  "2,2 ohm 0805"),
 ("Capacitor de bootstrap",           0.03, "[EST]",  "1uF/25V X7R 0805"),
 ("Diodo de bootstrap",               0.02, "[EST]",  "ultrarrapido 100V SOD-123"),
 ("Capacitor local do driver",        0.14, "[EST]",  "10uF/25V X7R 1206"),
 ("Shunt de fase",                    0.30, "[EST]",  "0,5 mOhm 2W 2512 manganina; eBay 50pcs US$13,30 = US$0,27 COT"),
 ("Amplificador diferencial",         2.60, "[EST]",  "INA240A2; modulo breakout = US$7,80 COT (7semi); CI ~US$2,5-3,3"),
 ("Divisor de referencia",            0.03, "[EST]",  "2x R 0603 1% + 100nF"),
 ("Divisor de fase",                  0.02, "[EST]",  "2x R 0603 1% por fase"),
 ("Filtro + clamp",                   0.04, "[EST]",  "1nF 0402 + zener clamp"),
 ("ADC externo SPI",                  8.00, "[EST]",  "ADS7953 16ch 12b 1Msps (Mouser single = US$13,56 COT)"),
 ("Mux analogico (se usar 2x CI de 8 canais)", 1.20, "[EST]", "alternativa barata: 2x MCP3208 ~US$2,60 cada -> ver nota"),
 ("Modulo ESP32-S3-WROOM-1",          3.50, "[CALC]", "ML modulo N16R8 R$56,91 COT / (5,1312*3,2)"),
 ("Botao BOOT + EN",                  0.05, "[EST]",  "tatico SMD"),
 ("Pull-ups de I2C",                  0.02, "[EST]",  "2x 4,7k 0603 (kit)"),
 ("Pads de programacao",              0.00, "[-]",    "test points sem custo no BOM (qtd '-')"),
 ("IMU 6 eixos",                      4.91, "[COT]",  "ICM-42688-P US$4,91 (DigiKey, 11/09/2026)"),
 ("Barometro",                        3.50, "[EST]",  "BMP390 LGA-10 (BMP581 vizinho = US$3,07 COT DigiKey)"),
 ("Buck 12 V",                        2.20, "[EST]",  "CI buck 36V/3A tipo TPS5430 (modulo = EUR6,30 COT)"),
 ("Buck 5 V",                         2.20, "[EST]",  "idem"),
 ("Buck 3,3 V",                       2.20, "[EST]",  "idem"),
 ("LDO 3,3 V_A",                      0.60, "[EST]",  "SOT-23 baixo ruido tipo TPS7A2033"),
 ("Indutor de saida",                 0.65, "[EST]",  "media 12x12mm 89uH / SRR1210A 17uH / SRN8040 5uH"),
 ("Capacitor de saida",               0.35, "[EST]",  "22uF/25V X7R 1210"),
 ("Conector de motor",                0.35, "[EST]",  "MR30 3 pinos (XT60/XT30 reais: ~US$0,3-0,6 COT)"),
 ("Receptaculo USB-C",                0.60, "[EST]",  "GCT USB4085 16p, so' programacao"),
 ("Protecao ESD USB",                 0.12, "[EST]",  "USBLC6-2SC6 SOT-23-6"),
 ("Ideal diode do VBUS",              0.50, "[EST]",  "P-FET + controlador SOT-23-6 (LM66100)"),
 ("LED de status",                    0.04, "[EST]",  "LED 0805 + R 1k"),
 ("Buzzer",                           0.60, "[EST]",  "SMD 4 kHz CPT-9019S + transistor"),
 ("Watchdog externo (opcional)",      0.70, "[EST]",  "SOIC-8 -- opcional, decisao do Jailton"),
 ("Fusivel/e-fuse de entrada",        0.30, "[EST]",  "fusivel 30A 1206 (e-fuse TPS2594x ~US$0,90)"),
 ("PCB",                              0.00, "[-]",    "custo tratado no bloco FAB (nao e' componente)"),
]

# ---------------------------------------------------------------- leitura BOM
with io.open(BOM, encoding="utf-8-sig") as fh:   # utf-8-sig: o CSV tem BOM no cabecalho
    bom = list(csv.DictReader(fh, delimiter=";"))

assert len(bom) == len(PRECOS), "BOM=%d linhas, PRECOS=%d -- dessincronizado" % (len(bom), len(PRECOS))
for i, (row, (nome, usd, conf, fonte)) in enumerate(zip(bom, PRECOS)):
    if row["item"].strip() != nome:
        raise SystemExit("Linha %d: BOM diz %r, PRECOS diz %r" % (i + 1, row["item"].strip(), nome))

linhas = []
for row, (nome, usd, conf, fonte) in zip(bom, PRECOS):
    qtxt = row["qtd"].strip()
    qtd = int(qtxt) if re.match(r"^\d+$", qtxt) else 0
    linhas.append(dict(bloco=row["bloco"], item=row["item"], valor=row["valor_especificacao"],
                       qtd=qtd, usd=usd, conf=conf, fonte=fonte, total_usd=round(qtd * usd, 4)))

# ---------------------------------------------------------------- totais
comp_usd = round(sum(l["total_usd"] for l in linhas), 2)
comp_usd_moq = round(comp_usd * MOQ_FACTOR, 2)

# cenario A -- compra nacional (preco unit = usd * dolar * k)
for l in linhas:
    l["brl_nac"] = round(l["qtd"] * l["usd"] * DOLAR * K_NAC, 2)
comp_brl_nac = round(sum(l["brl_nac"] for l in linhas), 2)   # so' componentes
comp_brl_nac_total = round(comp_brl_nac + FRETE_NAC_BRL, 2)  # componentes + frete nacional

# cenario B -- importacao direta (LCSC + impostos)
base_imp = comp_usd_moq + FRETE_INT_USD
ii = max(0.0, II * base_imp - DEDUCAO_USD)
icms = (base_imp + ii) / (1 - ICMS) * ICMS
iof = IOF * (base_imp + ii + icms)
imp_usd = base_imp + ii + icms + iof
comp_brl_imp = round(imp_usd * DOLAR, 2)

# banda de incerteza do cenario nacional (k e' o maior erro sistematico)
banda_min = round(comp_usd * DOLAR * K_NAC_MIN + FRETE_NAC_BRL, 2)
banda_max = round(comp_usd * DOLAR * K_NAC_MAX + FRETE_NAC_BRL, 2)

# ---------------------------------------------------------------- PCB + montagem
fab_med = (FAB_USD_MIN + FAB_USD_MAX) / 2
mont_usd = SETUP_USD + JOINTS * 0.0017 + STENCIL_USD + EXT_PART_USD * N_EXT_PARTS
# montagem importada tambem paga imposto sobre componentes; aqui isolamos o servico
fab_brl_min, fab_brl_max = round(FAB_USD_MIN * DOLAR, 2), round(FAB_USD_MAX * DOLAR, 2)

# ---------------------------------------------------------------- por bloco
blocos = {}
for l in linhas:
    b = blocos.setdefault(l["bloco"], dict(usd=0.0, brl_nac=0.0, itens=0))
    b["usd"] += l["total_usd"]; b["brl_nac"] += l["brl_nac"]; b["itens"] += 1

# ---------------------------------------------------------------- saidas
def esc(s):
    return str(s)

with io.open(os.path.join(OUT, "orcamento_detalhado.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["bloco","item","valor_especificacao","qtd","usd_unit","usd_total","brl_nacional","conf","fonte"])
    for l in linhas:
        w.writerow([l["bloco"], l["item"], l["valor"], l["qtd"], "%.4f" % l["usd"],
                    "%.4f" % l["total_usd"], "%.2f" % l["brl_nac"], l["conf"], l["fonte"]])

with io.open(os.path.join(OUT, "orcamento_por_bloco.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["bloco","linhas_bom","usd_total","brl_nacional","pct_do_total"])
    for k in sorted(blocos, key=lambda x: -blocos[x]["brl_nac"]):
        b = blocos[k]
        w.writerow([k, b["itens"], "%.2f" % b["usd"], "%.2f" % b["brl_nac"],
                    "%.1f%%" % (100 * b["brl_nac"] / comp_brl_nac)])

# ---------------------------------------------------------------- grafico
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ordem = sorted(blocos, key=lambda x: blocos[x]["brl_nac"])
    vals = [blocos[k]["brl_nac"] for k in ordem]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(ordem, vals, color="#2b6cb0")
    for b, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.01, b.get_y() + b.get_height() / 2, "R$ %.0f" % v,
                va="center", fontsize=9)
    ax.set_xlabel("Custo de componentes (BRL, cenario nacional, 1 placa)")
    ax.set_title("Orcamento por bloco -- drone ESC 4x + ESP32-S3\n(componentes apenas; PCB/montagem fora)")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "custo_por_bloco.png"), dpi=130)
    grafico = "ok"
except Exception as e:                                     # pragma: no cover
    grafico = "falhou: %s" % e

# ---------------------------------------------------------------- markdown
n_cot = sum(1 for l in linhas if l["conf"] in ("[COT]", "[CALC]"))
n_est = sum(1 for l in linhas if l["conf"] == "[EST]")
md = io.StringIO()
P = lambda s="": md.write(s + "\n")
P("# Orcamento de componentes -- drone (ESC 4x + ESP32-S3 numa PCB)")
P()
P("Gerado por `orcamento.py` em 11/09/2026. Quantidades vindas de")
P("`fase0_especificacao/lista_componentes_fase0.csv` (43 linhas, 1 placa).")
P()
P("**Dolar usado:** R$ %.4f (Bloomberg Linea, 11/09/2026)." % DOLAR)
P()
P("## 1. Resumo")
P()
P("| Cenario | O que e' | Total |")
P("|---|---|---|")
P("| A -- compra nacional | Mercado Livre / lojas BR, componentes + frete | **R$ %.0f** |" % comp_brl_nac_total)
P("| A -- banda honesta | k de markup entre %.1f e %.1f | R$ %.0f a R$ %.0f |" % (K_NAC_MIN, K_NAC_MAX, banda_min + 0, banda_max))
P("| B -- importacao direta | LCSC + frete + II 60%% (menos US$30) + ICMS 17%% + IOF 3,5%% | **R$ %.0f** |" % comp_brl_imp)
P("| Cenario A + PCB | 5 placas nuas, 4 camadas, 2 oz (220x160 mm) | + R$ %.0f a R$ %.0f |" % (fab_brl_min, fab_brl_max))
P("| Cenario B + montagem | PCBA JLCPCB (setup + joints + stencil + partes extendidas) | + R$ %.0f (US$ %.0f) |" % (mont_usd * DOLAR, mont_usd))
P()
P("- Componentes, valor de catalogo (US$ LCSC-equivalente): **US$ %.2f**" % comp_usd)
P("- Com folga de lote/MOQ (x%.2f): **US$ %.2f**" % (MOQ_FACTOR, comp_usd_moq))
P("- Linhas com preco cotado agora: %d de %d | apenas estimativa: %d" % (n_cot, len(linhas), n_est))
P()
P("## 2. Custo por bloco (cenario nacional)")
P()
P("| Bloco | Linhas | US$ | R$ | % |")
P("|---|---:|---:|---:|---:|")
for k in sorted(blocos, key=lambda x: -blocos[x]["brl_nac"]):
    b = blocos[k]
    P("| %s | %d | %.2f | %.0f | %.1f%% |" % (k, b["itens"], b["usd"], b["brl_nac"], 100 * b["brl_nac"] / comp_brl_nac))
P("| **TOTAL** | %d | **%.2f** | **%.0f** | 100%% |" % (len(linhas), comp_usd, comp_brl_nac))
P()
P("## 3. Detalhe linha a linha")
P()
P("| Bloco | Item | Qtd | US$/un | US$ tot | R$ nac | Conf. | Fonte |")
P("|---|---|---:|---:|---:|---:|---|---|")
for l in linhas:
    q = l["qtd"] if l["qtd"] else "-"
    P("| %s | %s | %s | %.4f | %.2f | %.2f | %s | %s |" % (l["bloco"], l["item"], q, l["usd"], l["total_usd"], l["brl_nac"], l["conf"], l["fonte"]))
P()
P("## 4. Contas dos cenarios (para conferir)")
P()
P("```")
P("Importacao: base = componentes(US$ %.2f) + frete(US$ %.0f) = US$ %.2f" % (comp_usd_moq, FRETE_INT_USD, base_imp))
P("            II    = 60%% x base - US$30 = US$ %.2f" % ii)
P("            ICMS  = (base+II)/(1-0,17) x 0,17 = US$ %.2f" % icms)
P("            IOF   = 3,5%% sobre (base+II+ICMS) = US$ %.2f" % iof)
P("            total = US$ %.2f -> R$ %.0f" % (imp_usd, comp_brl_imp))
P("Nacional:   componentes x US$ %.4f x k(3,2) + frete R$%.0f = R$ %.0f" % (DOLAR, FRETE_NAC_BRL, comp_brl_nac_total))
P("Montagem:   setup US$%.0f + %d joints x US$0,0017 + stencil US$%.2f + %d partes extendidas x US$%.0f = US$ %.2f" % (SETUP_USD, JOINTS, STENCIL_USD, N_EXT_PARTS, EXT_PART_USD, mont_usd))
P("```")
P()
P("## 5. O que NAO esta' cotado de verdade")
P()
P("1. **PCB nua** -- US$ %.0f-%.0f para 5 pcs e' estimativa; a cotacao real exige subir o" % (FAB_USD_MIN, FAB_USD_MAX))
P("   Gerber de `fase3_pcb/v6/` no site do fabricante. Area medida hoje: 220,1 x 160,1 mm =")
P("   352 cm2 em 4 camadas -- board grande e' o maior alavanca de custo (ver nota 6).")
P("2. **Preco unitario de %d das %d linhas e' [EST]** -- ordem de grandeza, nao cotacao." % (n_est, len(linhas)))
P("   LCSC e Mercado Livre bloqueiam leitura automatica daqui (LCSC/Akamai devolveu")
P("   'Access Denied'; Mercado Livre devolveu pagina de erro). Script usado: `orcamento.py`,")
P("   tentativas registradas na conversa de 11/09/2026.")
P("3. **Disponibilidade/lead time** nao verificado em nenhum item (0 de 43).")
P("4. **Imposto de importacao**: as fontes divergem na faixa ate US$ 50 (0% por MP 1.357/2026")
P("   vs 20% em material mais antigo). Acima de US$ 50 todas concordam: 60% com deducao de")
P("   US$ 30 + ICMS 17%. O cenario B esta' na faixa acima de US$ 50, entao o numero vale.")
P("5. **MOQ/partes extendidas** da JLCPCB: assumi 10 partes fora da biblioteca basica a US$ 3.")
P("6. **Nao incluso:** bateria 6S, helice, motores (ja existem), bancada (fonte, osciloscopio,")
P("   ferro/hot-air, termopar), consumiveis (pasta, estanho, fluxo, malha).")
P()
P("## 6. Observacoes de engenharia que mexem no custo")
P()
P("- **Board de 220x160 mm e' 5 placas de 100x100 em area.** O layout v6 esta' espalhado")
P("  (238 footprints, 367 nets ainda nao roteadas). Se a versao final couber em ~120x80 mm,")
P("  a fabricacao cai de faixa de US$ 70-150 para poucos dolares por lote de 5. Antes de")
P("  fechar compra, vale terminar o roteamento e recotar.")
P("- **BOM duplica indutores e capacitores de saida**: as linhas 'Buck 12/5/3,3 V' ja'")
P("  incluem L e Cout na descricao, e as linhas 'Indutor de saida' (3x) e 'Capacitor de")
P("  saida' (6x) repetem os mesmos componentes. Precifiquei o CI do buck e os passivos")
P("  separados -> se for pedir direto do CSV, o pedido vira' 6 indutores e 12 capacitores.")
P("- **12x INA240 = o item mais caro do projeto** (US$ 31,20, ~31% do BOM). Alternativa:")
P("  INA181/INA241 mais barato ou medicao de shunt low-side com amp simples, ao custo de")
P("  perder rejeicao de PWM. Decisao de engenharia, nao de compra.")
P("- **ADC**: ADS7953 (US$ 8) contra 2x MCP3208 (~US$ 5,20) -- a segunda opcao ja' esta'")
P("  prevista no BOM como 'mux analogico' e sai mais barata, com 2 chips a mais de firmware.")
P("- **Cenarios A e B empatam dentro da barra de erro** (R$ %.0f vs R$ %.0f). A diferenca real" % (comp_brl_nac_total, comp_brl_imp))
P("  e' tempo: importar = 3-6 semanas + risco de alfandega; nacional = dias, porem com markup")
P("  de ~3,2x sobre o preco de catalogo.")
P("- **Reserva de engenharia x%.2f** (~R$ %.0f) e' obrigatoria numa placa de 30 A com 24" % (PIOR_CASO, comp_brl_nac * (PIOR_CASO - 1)))
P("  MOSFETs, 4 half-bridges e pegada propria do ESP32-S3: o primeiro power-up queima coisa.")
P()

with io.open(os.path.join(OUT, "ORCAMENTO.md"), "w", encoding="utf-8") as fh:
    fh.write(md.getvalue())

print("=" * 74)
print("ORCAMENTO -- drone ESC 4x + ESP32-S3 (1 placa)")
print("=" * 74)
print("linhas BOM                :", len(linhas))
print("componentes (catalogo)    : US$ %.2f" % comp_usd)
print("componentes (com MOQ x%s): US$ %.2f" % (MOQ_FACTOR, comp_usd_moq))
print("CENARIO A nacional        : R$ %.0f   (banda R$ %.0f - R$ %.0f)" % (comp_brl_nac_total, banda_min, banda_max))
print("CENARIO B importacao      : R$ %.0f   (US$ %.2f all-in)" % (comp_brl_imp, imp_usd))
print("PCB 5 pcs 4L 2oz (est.)   : R$ %.0f - R$ %.0f  [EST, cotar com Gerber v6]" % (fab_brl_min, fab_brl_max))
print("Montagem PCBA JLC (est.)  : US$ %.2f = R$ %.0f" % (mont_usd, mont_usd * DOLAR))
print("precos COT/CALC           : %d / %d   (EST: %d)" % (n_cot, len(linhas), n_est))
print("grafico                   :", grafico)
print("=" * 74)
for k in sorted(blocos, key=lambda x: -blocos[x]["brl_nac"]):
    b = blocos[k]
    print("  %-12s %6.2f US$   R$ %7.2f   %5.1f%%" % (k, b["usd"], b["brl_nac"], 100 * b["brl_nac"] / comp_brl_nac))
print("=" * 74)
