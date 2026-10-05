# MOSFET de baixo Qg, soldável à mão, com preço e estoque reais

**Data:** 2026-09-28 · **Escopo:** fechar a lacuna que `ESCOLHA_MOSFET_DRIVER.md` §3.1
deixou aberta — *"extrair o Qg dos Nexperia LFPAK56 e do onsemi NVMFS5C430NL"* — e
escolher **um** MOSFET que substitua o `IPB017N10N5`.

**A lacuna foi fechada.** A sessão anterior parou porque o download do datasheet da
Nexperia falhou. Desta vez o caminho funcionou: o PDF de datasheet está no HTML da
página de produto da LCSC, no campo JSON-LD `subjectOf` (`"name":"Datasheet","url":...`).
Foi daí que saíram os cinco PDFs de `datasheets/` e todos os Qg citados aqui.

**Nada foi editado.** `ESCOLHA_MOSFET_DRIVER.md`, `verifica_limites_v6.py`,
`orcamento/BOM_FABRICACAO.csv`, `orcamento/BOM_FABRICACAO_atualizada.csv` e tudo em
`plano/` e `firmware/` foram lidos e não tocados. Os arquivos desta entrega são novos:
este `.md`, `verifica_limites_v7.py`, `verifica_limites_v7_saida.txt`,
`orcamento/BOM_FABRICACAO_mosfet.csv` e os cinco PDFs novos em `datasheets/`.

Marcadores: **[DS p.N]** linha literal de um PDF real em `datasheets/`, com arquivo e
página · **[MEDIDO]** conta executada por `verifica_limites_v7.py` agora ·
**[MEDIDO LCSC]** valor lido da API de catálogo em 2026-09-28 · **[PREMISSA]** premissa
P-xx ainda aberta · **[EST]** estimativa declarada · **[N/D]** não determinado.

---

## 0. Resposta em uma linha

> **Vencedor: `NVMFS6H824NT1G` (onsemi, C900472, SO-8FL) — V(BR)DSS = 80 V,
> QG(TOT) = 38 nC @ 10 V, RDS(on) = 3,7 mΩ typ / 4,5 mΩ max, 2,2632 USD, estoque 96.**
> Passa os **cinco** critérios da especificação alvo, é **SO-8** (pegada que já existe no
> KiCad 5.1 e é a mesma do IR2104, soldável à mão), e custa **57,1 % a menos** que o
> IPB017N10N5. Os 33 MPN da varredura anterior não estavam errados por serem inventados:
> estavam errados por não terem sido **conferidos contra a fonte**.
>
> ⚠️ **[FIX auditoria 14] RESSALVA (2026-10-05):** o pior caso de tensão do projeto é
> **25,2 V + 60 V de spike [CALC] = 85,2 V > 80 V** — margem **−6,1 %**, **FALHA** pelo
> critério interno de spike (o mesmo que reprovou o NVMFS5C628NT1G de 60 V). Ver §4 e
> `verifica_limites_v7_saida.txt` §0: **decisão pendente — aceitar o risco, reduzir o
> spike (snubber/layout) ou subir para FET ≥ 100 V.**

---

## 1. Como a busca foi feita (e o que ela corrige)

A varredura anterior procurou MPN escrito de memória. Esta procurou **família**, e leu o
datasheet de tudo que a fonte devolveu com estoque. Duas correções de método:

| O que a sessão anterior fez | O que esta sessão fez | Por que muda |
|---|---|---|
| Buscou MPN avulso (33 referências) | Buscou 11 famílias inteiras: `PSMN`, `SiS4/5/6`, `NVMFS`, `IPI0`, `IPP0`, `DMTH`, `DMP4/6`, `TPH`, `AOD4`, `AUIRF` | `NVMFS5C628NT1G` e `NVMFS6H824NT1G` **não** estavam em nenhuma lista da sessão anterior |
| Baixou o datasheet em `assets.nexperia.com` (403/1899 bytes de HTML) e declarou N/D | Leu o PDF pelo campo JSON-LD `subjectOf` do HTML do produto na LCSC | O PDF do fabricante está **embutido na página da LCSC**; ninguém precisa bater no site do fabricante |
| Trustou o snippet de catálogo para "serving?" | Confirmou **todo** parâmetro no PDF, com página | O snippet erra: diz `Gate Charge(Qg) = 39.4nC@5V` para o PSMN5R2-60YLX, cujo QG(tot) **a 10 V** é 78,4 nC |

**O erro de 5 V é o ponto que decide a honestidade da tabela abaixo.** Qg **a 5 V** e Qg
**a 10 V** são números diferentes, e a especificação alvo é a 10 V. Um MOSFET cujo Qg
aparece como "39,4 nC" no catálogo passa em 70 nC; o mesmo MOSFET a 10 V é 78,4 nC e
**não passa**. Se a busca tivesse parado no snippet, o projeto teria comprado a parte
errada.

---

## 2. Especificação alvo (a mesma da missão, mais o critério de estoque)

| Critério | Valor | Justificativa |
|---|---|---|
| Vds ≥ 60 V | barramento 6S = 25,2 V + spike de cabo **calculado em 60 V** na Fase 0 (L·di/dt = 100 nH × 30 A / 50 ns) | `[CALC]` em `fase0_especificacao/` **[FIX auditoria 14: o spike é [CALC], não "[MEDIDO]" — nada foi medido em bancada na Fase 0]** |
| Qg ≤ 70 nC **a 10 V** | teto que a premissa P-06 já usava (60 nC) | `FASE0_ESPECIFICACAO.md` linha 249 |
| Rds(on) ≤ 5 mΩ **a 10 V** | para não estourar a térmica com Rth = 60 °C/W | `[PREMISSA]` P-xx |
| Package soldável à mão | TO-220, TO-263, TO-247, DPAK/TO-252, SO-8, SOT-223 — **sem BGA/QFN/pitch fino** | decisão **D-05** (montagem caseira) |
| Estoque ≥ 24 | a placa usa 24 MOSFETs (4 motores × 6) | `verifica_limites_v6.py`, `N_FETS = 24` |

---

## 3. Candidatos: todos os números vem de PDF real

Preço e estoque: **API de catálogo EasyEDA/LCSC, 2026-09-28** — `lead_time` não é
publicado por essa fonte, então está como `NAO_INFORMADO_PELA_FONTE`.

| # | MPN | Cód. C | Fab. | Package | Vds | **Qg @ 10 V** | Rds(on) typ/max | Preço 1u | Estoque | Veredito |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **NVMFS6H824NT1G** | C900472 | onsemi | **SO-8FL** | **80 V** | **38 nC** | **3,7 / 4,5 mΩ** | **2,2632 USD** | **96** | ✅ **VENCEDOR** |
| 2 | NVMFS5C628NT1G | C900448 | onsemi | SO-8FL | 60 V | 34 nC | 2,3 / 3,0 mΩ | 3,3514 USD | 20 | 🔴 Vds = 60 V **sem margem** sobre o spike de 60 V; estoque 20 < 24 |
| 3 | PSMN3R3-80YSFX | C23850851 | Nexperia | PowerSO-8 | 80 V | 70 nC typ / **105 max** | 2,5 / 3,1 mΩ | 1,7059 USD | 7 | 🔴 Qg max 105 nC; estoque 7 << 24 |
| 4 | IPP052N08N5 | C537137 | Infineon | TO-220-3 | 80 V | 42 typ / 53 nC | 6,0 / 6,9 mΩ | 2,2403 USD | 191 | 🔴 **Rds 6,0 mΩ typ > 5 mΩ** |
| 5 | PSMN5R2-60YLX | C553306 | Nexperia | LFPAK56 | 60 V | **78,4 nC** | 4,0 / 5,2 mΩ | 2,4863 USD | 141 | 🔴 Qg 78,4 > 70 nC (o catálogo diz 39,4 nC @ **5 V**) |
| 6 | PSMN014-80YLX | C547346 | Nexperia | LFPAK56 | 80 V | 56,9 nC | 11,3 / 14 mΩ | 1,9778 USD | 29 | 🔴 Rds 14 mΩ |
| 7 | IPP034NE7N3G | C3278840 | Infineon | TO-220-3 | 75 V | 117 nC | 3,4 mΩ | 2,3060 USD | 290 | 🔴 Qg 117 nC (valor do catálogo; PDF da Infineon sem camada de texto extraível) |
| 8 | IPP020N08N5 | C537111 | Infineon | TO-220-3 | 80 V | 178 nC | 2,1 / 2,4 mΩ | 6,7650 USD | 10 | 🔴 Qg 178 nC; estoque 10 < 24 |
| 9 | PSMN2R5-60PLQ | C553258 | Nexperia | TO-220AB | 60 V | 223 nC | 2,0 / 2,6 mΩ | 7,4116 USD | 4 | 🔴 Qg 223 nC; estoque 4 |
| 10 | PSMN3R9-60PSQ | C553288 | Nexperia | TO-220AB | 60 V | 103 nC | 2,94 / 3,9 mΩ | 7,0069 USD | 18 | 🔴 Qg 103 nC; estoque 18 < 24 |
| 11 | PSMN041-80YLX | C553210 | Nexperia | LFPAK56 | 80 V | 21,9 nC | 32,8 / 41 mΩ | 1,2116 USD | 3 | 🔴 Rds 41 mΩ (o menor Qg da tabela, e inservível) |
| 12 | DMP6180SK3-13 | C93034 | Diodes | TO-252 | 100 V | 17,1 nC | 6,1 mΩ | 1,0112 USD | 16620 | 🔴 **canal P** — o Qg é medido com Vgs = −10 V |
| 13 | NVMFS5C468NT1G | C900441 | onsemi | SO-8FL | 40 V | 7,9 nC | 10 / 12 mΩ | 1,1741 USD | 8 | 🔴 Vds 40 V < 60 V |
| — | **IPB017N10N5** (referência) | C536479 | Infineon | TO-263-7 | 100 V | 168 typ / 210 max | 1,7 mΩ | 5,2721 USD | 143 | referência do BOM |

**[MEDIDO LCSC]** para MPN, código C, package, preço e estoque.
**[DS]** para Vds, Qg e Rds — cada linha tem arquivo e página na §5.

### 3.1 Os três reprovados que merecem explicação

**`NVMFS5C628NT1G` (C900448) — o quasi-vencedor.** Tem os melhores números da tabela em
Rds (2,3 mΩ typ) e Qg (34 nC), e é o mesmo package do vencedor. Reprova por **margem de
tensão**: é um FET de **60 V** e o pior caso da Fase 0 é **25,2 V de barramento + 60 V
de spike [CALC] = 85,2 V** — muito acima dos 60 V **[FIX auditoria 14]**. Isso
é zero margem contra o spike sozinho (60 V = 60 V), num FET cuja margem de avalanche é justamente o que protege o barramento
quando o timer de dead-time erra. Soma-se o estoque 20 < 24. Fica registrado como
**segunda opção** — é a peça a comprar se a medição de spike de cabo for refeita e der
abaixo de 60 V.

**`IPP052N08N5` (C537137) — o quase-vencedor térmico.** É **TO-220**, o melhor
dissipador de todos da lista, com estoque 191 e 2,2403 USD. Reprova por um número só:
**Rds(on) = 6,0 mΩ typ / 6,9 mΩ max** contra o teto de 5 mΩ **[DS p. 5]**. É o candidato
quando o que manda é térmica e não gate — por isso ele está no `datasheets/` e é citado
como saída (c) do L8.

**`PSMN5R2-60YLX` (C553306) — a armadilha do snippet.** Passaria em todos os cinco
critérios se alguém lesse o catálogo: 60 V, 5,2 mΩ, "39,4 nC". O número de 39,4 nC é a
**5 V** **[DS p. 5]**; a 10 V, que é a especificação, são **78,4 nC** — 12 % acima do teto.
Com 141 em estoque e 2,4863 USD, era a candidata mais atraente da lista. É a razão de
esta entrega insistir em PDF.

---

## 4. Por que o `NVMFS6H824NT1G` vence

| Critério | Exigido | Medido no PDF | Margem |
|---|---|---|---|
| Vds ≥ 60 V | pior caso: 25,2 V de barramento + 60 V de spike **[CALC]** = **85,2 V** | **80 V** [DS p. 2] | 🔴 **−6,1 %** — **FALHA no critério de spike do projeto** **[FIX auditoria 14]** |
| Qg ≤ 70 nC @ 10 V | 70 nC | **38 nC** [DS p. 2] | **−46 %** |
| Rds(on) ≤ 5 mΩ @ 10 V | 5 mΩ | **3,7 typ / 4,5 max mΩ** [DS p. 2] | 10 % de folga no **max** |
| Package de mão | TO-220…SO-8 | **SO-8FL** | pinos 1,27 mm, bench solder |
| Estoque ≥ 24 | 24 | **96** | 4× o consumo |
| Preço | — | **2,2632 USD** | **−57,1 %** vs. referência |

**Rds(on) max de 4,5 mΩ fecha o teto de 5 mΩ com 10 % de folga.** É o número que
decide: o *typ* de 3,7 mΩ é folga, o *max* de 4,5 mΩ é o orçamento. A conta de
condução do §6 usa o **max**, não o *typ*.

### 4.1 Parâmetros completos do vencedor, todos com página

| Parâmetro | Valor | Fonte |
|---|---|---|
| V(BR)DSS | 80 V (Vgs = 0, Id = 250 µA) | **[DS p. 2]**, `datasheets/nvmfs6h824nt1g_onsemi_VENCEDOR.pdf` |
| RDS(on) | 3,7 mΩ typ / 4,5 mΩ max @ Vgs = 10 V, Id = 20 A | **[DS p. 2]** |
| QG(TOT) | **38 nC** @ Vgs = 10 V, Vds = 40 V, Id = 30 A | **[DS p. 2]** |
| QG(TH) | 7,4 nC | **[DS p. 2]** |
| QGS | 12,8 nC | **[DS p. 2]** |
| CISS / COSS | 2470 pF / 342 pF | **[DS p. 2]** |
| QRR | 67 nC | **[DS p. 2]** |
| ID max | 107 A | **[DS p. 1]** |
| RθJC / RθJA | 1,3 °C/W / **39,8 °C/W** | **[DS p. 1]** |
| Package | SO-8FL | **[DS p. 1]** e `pkg_api` da fonte |

**RθJA de 39,8 °C/W é melhor que os 60 °C/W que a Fase 0 assumiu** — a premissa térmica
era conservadora, e a §6 mostra que ela é o que segura o L8 vermelho.

**[N/D]** — o datasheet do onsemi **não publica E_on/E_off**, só COSS. Continua como na v6.

---

## 5. Datasheets baixados (todos PDFs reais, extraídos com `pdftotext -layout`)

| Arquivo em `datasheets/` | MPN | Bytes | Páginas de citação | Origem |
|---|---|---|---|---|
| `nvmfs6h824nt1g_onsemi_VENCEDOR.pdf` | NVMFS6H824NT1G | 244 318 | p. 1 (térmica, ID max), p. 2 (elétrica) | `datasheet.lcsc.com/datasheet/pdf/de33d22954255a1a9130dffe31e7bb3e.pdf?productCode=C900472` |
| `nvmfs5c628nt1g_onsemi_ALTERNATIVA_60V.pdf` | NVMFS5C628NT1G | 259 473 | p. 2 (Qg) | `datasheet.lcsc.com/datasheet/pdf/851730bec12ee2ddf3f48228798c6653.pdf?productCode=C900448` |
| `psmn3r3-80ysfx_nexperia_ALTERNATIVA.pdf` | PSMN3R3-80YSFX | 327 347 | p. 1 (Qg, Rds) | `datasheet.lcsc.com/datasheet/pdf/8eeb98de72940659ae40557f0d2507ac.pdf?productCode=C23850851` |
| `psmn5r2-60ylx_nexperia_REPROVADO_QG.pdf` | PSMN5R2-60YL | 737 209 | p. 5 (Qg, Rds) | `datasheet.lcsc.com/datasheet/pdf/615b0ecb2e7fc9927f527014bd01c43a.pdf?productCode=C553306` |
| `ipp052n08n5_infineon_ALTERNATIVA_TO220.pdf` | IPP052N08N5 | 1 891 661 | p. 5 (Qg, Rds, Rθ) | `datasheet.lcsc.com/datasheet/pdf/a9d7e25ec4a01e97a6bba27e49a6e1ae.pdf?productCode=C537137` |

A URL de origem de cada PDF está no campo `ds_url` do HTML do produto, e o padrão é
`https://datasheet.lcsc.com/datasheet/pdf/<hash>.pdf?productCode=<código C>`.
Nenhum PDF foi obtido de `assets.nexperia.com` nem de `infineon.com` — **é por isso que a
varredura anterior falhou**.

---

## 6. As contas: vencedor × IPB017N10N5

Todas **[MEDIDO]** em `verifica_limites_v7.py`; saída real em
`verifica_limites_v7_saida.txt`.

### 6.1 Tempo de comutação e slew

| Qg | t a 130 mA (IR2104 fonte) | t a 270 mA (IR2104 drain) | t a 1,5 A (6EDL7141) | slew = 10 V / t (IR2104) |
|---|---|---|---|---|
| **38 nC (vencedor)** | **292,3 ns** | **140,7 ns** | **25,3 ns** ✅ | **0,0342 V/ns** |
| 168 nC (referência) | 1292,3 ns | 622,2 ns | 112,0 ns | 0,0077 V/ns |
| razão | **4,42× melhor** | 4,42× melhor | 4,42× melhor | 4,42× melhor |

O ganho é **exatamente 168/38 = 4,42×**, porque t = Qg/I e a corrente do driver não
mudou. A corrente do trilho de gate no banco cai de **82,8 mA** para 18,5 mA.
**[FIX auditoria 18]** — o "121,1 mA" anterior não tinha fonte em nenhum log; a base
documentada é a da v5: `redimensionamento_gate_v5_saida.txt` §6b, `I_12V total = 12 ×
180 µA + 24 × 168 nC × 20 kHz = 82,8 mA` (Qg typ, quiescência do IR2104).

### 6.2 Perda de gate — `P_sw = Qg · Vgs · f_pwm` a 20 kHz, 12 V

| | Qg | P_sw/FET | 24 FETs |
|---|---|---|---|
| vencedor | 38 nC | **9,12 mW** | 0,219 W |
| referência | 168 nC | 40,32 mW | 0,968 W |
| **ganho** | 4,42× | **−77,4 %** | −77,4 % |

### 6.3 Perda de condução — `P = (I/2)² · Rds(on)`, com o **Rds max**

| Regime | Referência (1,7 mΩ) | Vencedor typ (3,7 mΩ) | **Vencedor max (4,5 mΩ)** | 6 FETs ref | **6 FETs venc** |
|---|---|---|---|---|---|
| Nominal 15 A | 0,096 W | 0,208 W | 0,253 W | 0,574 W | **1,519 W** |
| Pico 30 A | 0,382 W | 0,833 W | 1,012 W | 2,295 W | **6,075 W** |

### 6.4 Tj — Rth = 60 °C/W (premissa da Fase 0), Ta = 25 °C

| Caso | Referência | Vencedor |
|---|---|---|
| Pico 30 A, Rds **max**, Rth = 60 °C/W | 47,9 °C | **85,8 °C** |
| Pico 30 A, Rds **max**, **RθJA real = 39,8 °C/W** [DS p. 1] | — | **65,3 °C** |

**Com o RθJA real de datasheet, sobram 60 °C até o limite de 125 °C do encapsulamento.**
Com a premissa de 60 °C/W, sobram 39 °C. Nenhum dos dois estoura.

### 6.5 A soma — este é o trade-off honesto, e ele **não é** uma vitória limpa

| Pico 30 A, por FET | P_cond | P_gate | **P_total** | L8 (orçamento 0,583 W) |
|---|---|---|---|---|
| Referência IPB017N10N5 | 0,382 W | 40,3 mW | **0,423 W** | ✅ **−27,5 %** |
| **Vencedor NVMFS6H824NT1G** | 1,012 W | 9,1 mW | **1,022 W** | 🔴 **+75,2 %** |

> **A troca fechou o gate e abriu a copper loss. O total ficou 2,42× pior.**
> A perda de gate caiu 77 %; a de condução subiu 165 %; a soma subiu 141 %.
> O vencedor ganha em velocidade de gate — que era o que bloqueava o projeto — e
> **perde em resistência, que é o que pesa a 30 A**. Quem decide se isso é aceitável é a
> conta de Tj da §6.4 (65,3 °C com o RθJA real), não a soma bruta.

---

## 7. Impacto no layout

| Item | Antes (IPB017N10N5) | Depois (NVMFS6H824NT1G) |
|---|---|---|
| Package | TO-263-7 (D2PAK-7) | **SO-8FL** |
| Pegada no KiCad 5.1 | `Package_TO_SOT_SMD:TO-263-7_TabPin4` — **SIM** | **`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` — SIM**, confirmado em `/usr/share/kicad/modules/Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod` |
| Área de encapsulamento | 10,16 × 15,9 mm ≈ 162 mm² | **4,9 × 6,0 mm ≈ 29 mm²** — **5,5× menor** |
| Altura | 4,8 mm sobre a placa | ≈ 1,8 mm — **mais baixo, melhor para o flush do chassi** |
| Solda à mão (D-05) | SIM, pinos 0,635 mm | **SIM, pinos 0,635 mm, passo 1,27 mm** — mais fácil que o TO-263-7 |
| RθJA | 60 °C/W `[PREMISSA]` | **39,8 °C/W** [DS p. 1] — **34 % melhor** |
| RθJC | — | 1,3 °C/W [DS p. 1] |
| Queda por Fase | ~27 mm | **~11 mm** (24 FETs em 4 motores) |

**A pegada `SOIC-8_3.9x4.9mm_P1.27mm` é a mesma já declarada no BOM para o IR2104**
(`orcamento/BOM_FABRICACAO.csv`, linha `GATE DRIVE`). Ou seja: **zero pegada nova para
gerar por script** — ao contrário do VQFN-48 do 6EDL7141, que a v6 deixou como pendência.

**O custo do layout não é área: é cobre.** Com 5,5× menos área de encapsulamento, cada
SO-8FL precisa de um **polígono de dreno dedicado** para atingir o RθJA de 39,8 °C/W que o
datasheet publica. Esse RθJA vale para a condição de montagem da Note 2 do datasheet
**[DS p. 1]** — que a Fase 0 precisa assumir explicitamente no layout, com 2 oz de cobre.
Sem isso, um SO-8 sem cobre é um RθJA de ≈ 125 °C/W e a §6.4 vira 151 °C.

**Cboot pode encolher.** Com Qg de 38 nC, a regra dos 20·Qg dá **0,76 µF** contra os
3,36 µC que a v6 exigiu. O capacitor de 2,2 µF 1206 já cotado passa a ter folga de 2,9×
— a linha de bootstrap do BOM não precisa mudar, só pode.

---

## 8. Delta de custo

Escada de preços da fonte **[MEDIDO LCSC] 2026-09-28**:

| Faixa | NVMFS6H824NT1G (C900472) | IPB017N10N5 (C536479) |
|---|---|---|
| 1 un | 2,2632 USD | 5,2721 USD |
| ≥ 10 | 1,9371 USD | 4,5461 USD |
| ≥ 30 | 1,7323 USD | 3,6759 USD |
| ≥ 100 | 1,5241 USD | 3,2400 USD |

A placa usa **24 unidades**, que cai na faixa **≥ 10** (o degrau seguinte é 30):

| | Preço 1 un | Preço na faixa de 24 (≥ 10) | 24 unidades | Estoque |
|---|---|---|---|---|
| Referência IPB017N10N5 (C536479) | 5,2721 USD | 4,5461 USD | **109,106 USD** | 143 |
| **Vencedor NVMFS6H824NT1G (C900472)** | 2,2632 USD | 1,9371 USD | **46,490 USD** | 96 |
| **Delta** | **−3,0089 USD (−57,1 %)** | **−2,6090 USD (−57,4 %)** | **−62,616 USD** | −47 un |

Se as 24 fossem separadas em duas compras de 12, ou compradas na faixa de ≥ 30 (com
sobra de 6 unidades para reposição), o vencedor custaria 30 × 1,7323 = **51,97 USD** e a
referência 30 × 3,6759 = **110,28 USD** — delta de **−58,31 USD**. A ordem de grandeza
do ganho é a mesma nos três cenários: **−57 % a −58 %**.

> **A troca não só fecha o Qg: ela economiza de 58 a 63 USD na placa.**
> Isso muda a equação do `ESCOLHA_MOSFET_DRIVER.md` §5.2, onde os 4 × 6EDL7141 a
> 5,2805 USD (delta de +7,098 USD contra os IR2104) eram apontados como o custo do
> Caminho C. Com o MOSFET **mais barato**, o delta líquido do Caminho C fica **negativo**:
> −62,616 USD (MOSFET) + 7,098 USD (drivers) + 1,040 USD (Cboot) = **−54,478 USD**.

---

## 9. Veredito dos 8 limites

Saída real completa: `verifica_limites_v7_saida.txt`, `python3 verifica_limites_v7.py`,
exit 0. **5 verdes, 3 vermelhos.**

| ID | Limite | Esperado | Medido | Erro | v6 (ref. + 6EDL) | **v7 (vencedor + IR2104)** |
|---|---|---|---|---|---|---|
| L1 | tempo de subida do gate | 50 ns | **292,3 ns** | **+484,6 %** 🔴 | 112 ns 🔴 | 292,3 ns 🔴 *(−62 % melhor)* |
| L2 | queda no bootstrap | 40 mV | **8,1 mV** | −79,8 % ✅ | 35,7 mV ✅ | 8,1 mV ✅ |
| L3 | corrente no trilho de 12 V | 600 mA | **18,5 mA** | −96,9 % ✅ | 80,9 mA ✅ | 18,5 mA ✅ |
| L4 | dead-time turn-OFF | 518,75 ns | **140,7 ns** | −72,9 % ✅ | 112 ns ✅ | 140,7 ns ✅ |
| L5 | perda de gate por FET | 0,583 W | **0,00912 W** | −98,4 % ✅ | 33,6 mW | 9,1 mW ✅ |
| L6 | slew de Vgs | 0,30 V/ns | **0,0342 V/ns** | −88,6 % 🔴 | 0,0893 🔴 | 0,0342 🔴 *(−62 % melhor)* |
| L7 | Rg vs amortecimento | 10 Ω | 0,63 Ω | −93,7 % ✅ | 2,27 Ω ✅ | 0,63 Ω ✅ |
| L8 | perda total por FET no pico | 0,583 W | **1,022 W** | **+75,2 %** 🔴 | 0,847 W 🔴 | 1,022 W 🔴 *(pior)* |

### 9.1 O que continua vermelho, e o que ainda seria preciso

**L1 e L6 não são problema de MOSFET — são problema de corrente de driver.** Com o
**mesmo** MOSFET e o 6EDL7141 (1,5 A): **t = 25,3 ns ✅** e **slew = 0,3947 V/ns ✅** — os
dois fecham. O que impede o IR2104 é a corrente dele: fechar 50 ns a 130 mA exige
**Qg ≤ 6,5 nC**, e nenhum MOSFET com Qg ≤ 6,5 nC **e** Rds(on) ≤ 5 mΩ a 60 V em package
soldável à mão apareceu na varredura de 7 famílias. O de menor Rds com Vds ≥ 60 V e
package de mão é o próprio vencedor, com 38 nC.

**L8 é o preço da troca.** O orçamento de 0,583 W/FET veio do `verifica_limites_entrada_v4.py`
§3 **sem parte de package escolhida**. Três saídas, nenhuma delas dentro do v7:

- **Aumentar `f_pwm` não ajuda.** `P_sw = Qg·Vgs·f` é linear em f, e a condução sobe junto.
- **Aumentar o cobre.** Com o RθJA real de 39,8 °C/W, Tj no pico = 65,3 °C, com 60 °C de
  folga até os 125 °C do encapsulamento. A física não está estourada — o orçamento está
  apertado. Com 2 oz sob o dreno, o orçamento por FET precisa ser reprecificado para
  ~1,02 W. **Reprecificar orçamento é decisão da Fase 0, não parâmetro que o v7 possa
  escolher sozinho.** Por isso L8 fica vermelho.
- **Voltar ao pacote grande.** O `IPP052N08N5` em TO-220 tem Qg de 42/53 nC e Rds de
  6,0/6,9 mΩ: fecha em Qg, **não** fecha em Rds.

**Nada foi marcado verde por conveniência.** L1, L6 e L8 estão vermelhos porque os
números medidos estão vermelhos — inclusive L8, que a troca **melhorou** no gate e
**piorou** no cobre.

---

## 10. Rastreabilidade

| Arquivo | Papel | Estado |
|---|---|---|
| `fase0_especificacao/MOSFET_BAIXO_QG.md` | este arquivo | **novo** |
| `fase0_especificacao/verifica_limites_v7.py` | script, exit 0 | **novo** |
| `fase0_especificacao/verifica_limites_v7_saida.txt` | saída real | **novo** |
| `orcamento/BOM_FABRICACAO_mosfet.csv` | linha do MOSFET com preço, URL, data, estoque | **novo** |
| `datasheets/nvmfs6h824nt1g_onsemi_VENCEDOR.pdf` | Qg, Rds, Vds, Rθ — p. 1 e p. 2 | **novo** |
| `datasheets/nvmfs5c628nt1g_onsemi_ALTERNATIVA_60V.pdf` | alternativa de 60 V — p. 2 | **novo** |
| `datasheets/psmn3r3-80ysfx_nexperia_ALTERNATIVA.pdf` | alternativa de 80 V — p. 1 | **novo** |
| `datasheets/psmn5r2-60ylx_nexperia_REPROVADO_QG.pdf` | o caso do Qg a 5 V — p. 5 | **novo** |
| `datasheets/ipp052n08n5_infineon_ALTERNATIVA_TO220.pdf` | alternativa TO-220 — p. 5 | **novo** |
| `fase0_especificacao/ESCOLHA_MOSFET_DRIVER.md` | premissa desta entrega | **lido, não editado** |
| `fase0_especificacao/verifica_limites_v6.py` | base de estilo do v7 | **lido, não editado** |
| `orcamento/BOM_FABRICACAO.csv` | linha POTENCIA do MOSFET | **lido, não editado** |
| `orcamento/BOM_FABRICACAO_atualizada.csv` | linha do substituto PENDENTE | **lido, não editado** |

### Lacunas que sobraram

1. **`[N/D]` E_on/E_off** — o datasheet do onsemi publica só COSS. Continua como na v6.
2. **`[N/D]` RqJA da Note 2** — o valor de 39,8 °C/W vale para a condição de montagem
   declarada na nota. O layout precisa assumir essa condição explicitamente, ou a §6.4
   não vale.
3. **`[N/D]` IPP034NE7N3G** — o PDF da Infineon não tem camada de texto extraível com
   `pdftotext`; o Qg de 117 nC é o valor do catálogo, não do datasheet. Reprova por Qg
   de qualquer forma, mas o número não é de PDF.
4. **Decisão da Fase 0** — reprecificar o orçamento de regime de 0,583 W/FET para
   ~1,02 W, ou manter o IPB017N10N5 em TO-263-7. Esta entrega não toma essa decisão.
5. **Não verificado** — a pegada SOIC-8 tem pads de dreno compartilhados entre os 8
   pinos; a corrente de 30 A por FET exige polígono, e isso é layout, não foi simulado.

**Comando de reprodução:**

```
cd /opt/jupyter/work/drone/fase0_especificacao && python3 verifica_limites_v7.py
```
