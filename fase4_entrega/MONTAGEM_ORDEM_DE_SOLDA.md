# MONTAGEM — ORDEM DE SOLDA (FASE 4)

**Projeto:** drone 4×ESC trifásico + ESP32-S3 em PCB única · pack LiPo 6S (19,8 / 22,2 / 25,2 V)
**Pasta:** `/opt/jupyter/work/drone/fase4_entrega/` · **Data:** 2026-09-11
**Máquina:** Orange Pi 3B, Debian Bullseye aarch64 (headless)

## Como ler este documento (etiquetas)

| Etiqueta | Significado |
|---|---|
| `[DISCO]` | fato conferido em arquivo do projeto, com caminho:linha ou comando |
| `[FONTE]` | fonte externa consultada ao vivo nesta sessão, com URL e data |
| `[EST]` | estimativa de engenharia minha — não medida, não confirmada |
| `[PREMISSA]` | suposição do projeto (P-01…P-15 da Fase 0) |
| `[VERIFICAR]` | **não confirmado** — depende de dado que só o Jailton tem (ex.: a pasta de solda) |

---

## 0. AVISO QUE VEM ANTES DE TUDO: a placa ainda NÃO está pronta para fabricar

Isto é obrigatório ler antes de comprar estêncil ou pasta.

`[DISCO]` `/opt/jupyter/work/drone/fase3_pcb/v6/verificacao_v6.txt`:

```
nets com pad      : 426
nets roteadas     : 59
nets NAO roteadas : 367
```

**367 de 426 nets não estão roteadas** (grupos `MCU` 41, `CSAM10..40` 24 cada, `DRVM10..40`
24 cada, `IMU` 24, `USB` 17, `BARO` 8). A placa v6 tem 238 footprints, 220,1 × 160,1 mm,
4 camadas, mas o roteamento **está incompleto**. A própria verificação também aponta
12 pares "trilha × pad de net diferente próximos" (ex.: `trilha PHM101 × pad QM101H.2 (VBAT_PROT)`),
que precisam ser resolvidos no DRC final.

> **Conclusão honesta:** este documento é o **plano de montagem** para quando a placa estiver
> roteada e com DRC limpo. **Não mande fabricar nem compre estêncil com o v6 como está.**
> Ordem de serviço: fechar roteamento → DRC/ERC → gerar Gerber novo → só então montar.

---

## 1. O que a placa tem, por tipo de pegada

`[DISCO]` `fase0_especificacao/lista_componentes_fase0.csv` (43 linhas) + detalhamento do
`orcamento/orcamento_detalhado.csv`. Contagem por **tipo de pegada** (calculada a partir da
coluna `qtd` do CSV):

| Pegada | Qtd. | Componentes |
|---|---:|---|
| **0402** | 60 | 48× 100 nF/50 V X7R (snubber por par de MOSFET) + 12× 1 nF (filtro BEMF) |
| **0603** | ~52 | 24× R 1 % do divisor de referência da corrente (10k/10k) · 24× R 1 % divisor BEMF (8,2k/1,0k) · 2× 10k do P-FET + zener · 2× pull-up I²C 4,7k |
| **0805** | 61 | 24× Rg = 10 Ω · 24× Rg(off) = 2,2 Ω · 12× Cboot 1 µF/25 V X7R · 1× LED 0805 + R 1k |
| **1206** | 25 | 12× 10 µF/50 V X7R (banco) · 12× 10 µF/25 V X7R (local do driver) · 1× fusível 1206 |
| **1210** | 6 | 6× 22 µF/25 V X7R (saída dos bucks) |
| **2512** | 12 | shunt 0,5 mΩ 2 W manganina |
| **SMB** | 1 | TVS unidirecional (standoff ≥ 30 V) |
| **TO-252 (DPAK)** | 25 | 24× MOSFET N + 1× P-FET anti-inversão |
| **SOD-123** | 12 | diodo de bootstrap ultrarápido 100 V |
| **SOD-323** | 12 | clamp 3,3 V do BEMF (a pegada do diodo é `[EST]` — o CSV lista o footprint da linha como o do capacitor de 1 nF) |
| **SOIC-8** | 12 | driver half-bridge single-input (dead-time interno ~520 ns) |
| **SOIC-8-EP** | 12 | amplificador diferencial de corrente (G=50) |
| **SOIC-16** | 2 | mux analógico (alternativa ao ADC de 16 canais) |
| **QFN-24 3×3 P0,4 mm** | 1 | IMU 6 eixos |
| **LGA-8 / LGA-10** | 1 | barômetro |
| **DFN/SO (config. CI)** | 1 | ADC externo SPI |
| **SOT-23 / SOT-23-6** | 3 | LDO 3,3 V_A + ESD USB + ideal-diode do VBUS |
| **Módulo** | 1 | ESP32-S3-WROOM-1 (41 pads castelados; **pegada gerada por script**, não existe no KiCad 5.1) |
| **Eletrolítico 8×10** | 6 | 470 µF/35 V polímero low-ESR |
| **Indutor 12×12 / 8×8** | 3 | 89 µH (buck 12 V) · 17 µH SRR1210A (buck 5 V) · 5 µH SRN8040 (buck 3,3 V) |
| **Through-hole** | 5 | 1× XT60 (bateria) + 4× MR30 3 pinos (motor) |
| **Diversos** | ~10 | USB-C 16p, 2 botões, buzzer SMT, test points, watchdog opcional |

**Lado da placa:** `[DISCO]` comando
`grep -A3 '^\s*(module ' v6_drone.kicad_pcb | grep -o 'layer [FB]\.Cu' | sort | uniq -c`
→ `238 layer F.Cu`. **Os 238 footprints estão TODOS na face superior (F.Cu).**

> Consequência prática: **uma única passada de reflow**. Não há face B para soldar,
> logo não existe o clássico "segunda passada que derruba o que já está em cima".
> Isso protege o módulo ESP32-S3. `[DISCO]`

---

## 2. Perfis de reflow — e por que o definitivo é o da SUA pasta

> ### ⚠️ O perfil abaixo é **típico de mercado**, não o da sua pasta.
> **O perfil definitivo é o que estiver no datasheet da pasta que você comprar.** As ligas
> mudam (algumas SAC305 "low-void" pedem soak mais curto, outras pedem pico 5 °C menor), e
> cada fabricante publica a janela própria. **`[VERIFICAR]` — me mande o datasheet da pasta
> ou o nome exato do produto que eu fecho os números.**

### 2.1 SAC305 — Sn96,5 / Ag3,0 / Cu0,5 (sem chumbo, líquidus ≈ 217 °C)

`[FONTE]` JLC PCB, "Reflow Soldering Profile Explained" — https://jlcpcb.com/blog/reflow-soldering-profile-explained
(consultado 2026-09-11); `[FONTE]` S&M/Chuxin, https://www.chuxin-smt.com/reflow-oven-temperature-profiles-complete-guide-to-solder-types-zone-settings-and-best-practices
(consultado 2026-09-11).

| Zona | Faixa | Duração / taxa |
|---|---|---|
| Pré-aquecimento (rampa) | ambiente → 150 °C | 1,0–3,0 °C/s |
| Soak (ativação do fluxo) | 150–200 °C | 60–120 s |
| Reflow / TAL (acima de 217 °C) | > 217 °C | 60–90 s |
| **Pico** | **235–250 °C** | 20–40 s dentro de 5 °C do pico |
| Resfriamento | pico → ambiente | −2 a −4 °C/s |
| 25 °C → pico | — | ≤ 8 min |

Limite de classificação do componente (`[FONTE]` J-STD-020, resumido em
https://pcbsync.com/j-std-020, consultado 2026-09-11): rampa TL→Tp **máx. 3 °C/s**,
TAL 60–150 s, resfriamento **máx. −6 °C/s**. Tp depende da espessura/volume da cápsula:
para cápsulas acima de 2,5 mm ou volume > 2 mm³, Tp cai para 245 °C; abaixo de 1,6 mm vale 260 °C.
`[FONTE]` TI, "MSL Ratings and Reflow Profiles" — https://www.ti.com/lit/pdf/spraby1 (consultado 2026-09-11).

### 2.2 Sn63Pb37 (com chumbo, líquidus ≈ 183 °C)

`[FONTE]` CompuPhase, "Reflow soldering profiles" — https://www.compuphase.com/electronics/reflowsolderprofiles.htm
(consultado 2026-09-11).

| Zona | Faixa | Duração |
|---|---|---|
| Pré-aquecimento | → 150 °C | 60 s |
| Soak | 150 → 165 °C | 120 s |
| **Pico** | **225–235 °C** (janela 210–235 °C) | ~20 s |
| TAL (> 183 °C) | — | 30–60 s |
| Resfriamento | — | ~ −4 °C/s (ar livre serve) |

### 2.3 Qual usar nesta placa

| Critério | SAC305 | Sn63Pb37 |
|---|---|---|
| Pico | 235–250 °C | 225–235 °C |
| Estresse térmico no módulo ESP32-S3 | maior | **menor** |
| Janela de processo | estreita | larga |
| Legalidade/reparo (Pb) | ok para uso próprio | ok para uso próprio; evite inalar — use exaustão |
| Recomendação para **montagem manual em casa** | funciona | **mais fácil e mais seguro para o módulo** |

`[EST]` Para montagem manual, com hot-air e sem forno de perfil, **Sn63Pb37 é mais
tolerante** ao erro humano (janela de 25 °C em vez de 15 °C) e agride menos o módulo.
Se você já tem SAC305, também funciona — mas respeite o pico de 245 °C, não 260 °C.
`[VERIFICAR]` — depende do que você tem.

### 2.4 Ajuste obrigatório por causa DESTA placa

`[EST]` Esta placa tem **352 cm² (220 × 160 mm), 4 camadas e 2 oz de cobre nas faces
externas** `[DISCO]` (`orcamento/ORCAMENTO.md` §Observações, e `fase3_pcb/calc_trilhas_vias_saida.txt`:
"2 oz = 2,756 mil = 70 um"). Massa térmica é alta. Implicações:

1. **Use o topo do soak** (100–120 s), não o mínimo — o ΔT entre a borda (onde estão os
   conectores) e o centro (onde está o ESP32-S3) é o que estraga.
2. **Rampa no limite baixo** (1,0–1,5 °C/s) até 150 °C.
3. Placa desse tamanho **não cabe em forno de reflow de bancada pequeno** sem gradiente.
   `[EST]` O caminho realista é **pré-aquecimento + hot-air por região**, não forno.
4. Para hot-air manual: **pré-aqueça a placa inteira a 100–120 °C** antes de atacar qualquer
   região (estação de pré-aquecedor ou hot plate). Sem isso, você vai dar 300 °C na
   superfície para a solda derreter embaixo, e é assim que se descola pad. `[EST]`

---

## 3. ORDEM DE SOLDA — 4 ETAPAS

A ordem vale para os **dois métodos**:

- **Método A (pasta + estêncil + reflow/hot-air):** a ordem é ordem de **posicionamento**
  (você posiciona tudo antes de aquecer). Coloque na sequência abaixo para não derrubar
  peça pequena com a pinça depois.
- **Método B (hot-air manual + ferro, sem estêncil):** a ordem é **ordem de aquecimento** —
  do menor para o maior. Aqui a ordem é crítica: o que já está soldado recebe calor de novo.

### Etapa A — FINOS E MIÚDOS PRIMEIRO (0402, QFN, LGA, SOIC fino)

Por quê: são os que exigem mais precisão, o menor tempo de aquecimento e a melhor visão.
Depois que os TO-252 e os indutores estão na placa, eles **bloqueiam a ponta do ar e a
visão** e o passo fino fica impossível.

| Ordem | Componente | Qtd | Pegada | Nota de execução |
|---:|---|---:|---|---|
| A1 | Barômetro | 1 | LGA-8/10 | menor de todos; pasta mínima (estêncil manda) |
| A2 | IMU 6 eixos | 1 | QFN-24 3×3 **P0,4 mm** | passo crítico; conferir alinhamento com lupa **antes** de aquecer |
| A3 | ADC externo | 1 | DFN/SOIC | — |
| A4 | Amplificador de corrente | 12 | SOIC-8-EP | **pad térmico embaixo**: precisa de pasta no EP + via de calor |
| A5 | Driver half-bridge | 12 | SOIC-8 P1,27 mm | passo folgado; é o mais fácil dos CI |
| A6 | Mux analógico | 2 | SOIC-16 | — |
| A7 | LDO 3,3 V_A, ESD USB, ideal-diode | 3 | SOT-23 / SOT-23-6 | — |
| A8 | Capacitores 0402 | 60 | C_0402 | 48× 100 nF + 12× 1 nF |
| A9 | Resistores 0603 | ~52 | R_0603 | divisores 1 % de corrente e BEMF; pull-ups |
| A10 | Diodos SOD-123 e SOD-323 | 24 | SOD-123 / SOD-323 | 12× bootstrap + 12× clamp BEMF |
| A11 | TVS | 1 | SMB | — |

> **A1–A7 são CI.** Regra de ouro: **CI nunca por último em hot-air manual.** Se você soldar
> os passivos primeiro, o ar quente vai ressecar a pasta dos CI e eles vão "flutuar".

### Etapa B — PASSIVOS GRANDES

| Ordem | Componente | Qtd | Pegada |
|---:|---|---:|---|
| B1 | Resistor de gate + resistor de desliga | 48 | R_0805 (10 Ω e 2,2 Ω) |
| B2 | Capacitor de bootstrap | 12 | C_0805 (1 µF/25 V) |
| B3 | LED de status + R 1k | 1+1 | LED_0805 |
| B4 | Cerâmicos 1206 | 24 | 12× 10 µF/50 V + 12× 10 µF/25 V |
| B5 | Cerâmicos 1210 | 6 | 22 µF/25 V (saída dos bucks) |
| B6 | Fusível | 1 | Fuse_1206 |
| B7 | **Shunts 0,5 mΩ** | 12 | R_2512 | peça crítica: valor medido muda se solda ficar ruim (ver §7) |
| B8 | Capacitores eletrolíticos 470 µF/35 V | 6 | CP_Elec_8x10 | **polaridade**; massa grande, aquecer por igual |

### Etapa C — TO-252 E INDUTORES (massa térmica)

| Ordem | Componente | Qtd | Pegada | Nota de execução |
|---:|---|---:|---|---|
| C1 | MOSFETs N | 24 | **TO-252-3** (DPAK) | o **tab é o dreno** e é área de cobre; precisa de pasta e de aquecimento por baixo |
| C2 | P-FET anti-inversão | 1 | TO-252-2 | — |
| C3 | Indutores | 3 | 12×12 / 8×8 | terminais grossos; aquecer primeiro pelo corpo, depois soldar cada terminal |
| C4 | Buzzer SMT | 1 | CPT-9019S | — |
| C5 | Botões BOOT/EN | 2 | SW_SPST | — |
| C6 | Receptáculo USB-C | 1 | GCT USB4085 | SMD com abas de fixação; soldar as abas por último |

> **Por que TO-252 depois dos CI:** o DPAK dissipa calor pelo tab (dreno) e o layout usa
> cobre como dissipador `[DISCO]` (`lista_componentes_fase0.csv`: "Dissipador / area de cobre;
> 2 oz, poligono no dreno; GERADO NO LAYOUT"). Soldar isso exige mais energia que qualquer
> CI — e se você tentar fazer antes dos 0402, o cobre quente fica tempo demais exposto.

### Etapa D — THROUGH-HOLE POR ÚLTIMO, COM FERRO (nunca com ar quente)

| Ordem | Componente | Qtd | Nota |
|---:|---|---:|---|
| D1 | **XT60** (bateria) | 1 | 2 pinos grossos. Ferro ≥ 60 W, ponta larga, preencher o barril. **Por último.** |
| D2 | **MR30** de motor | 4 | 3 pinos cada. Mesma técnica. |
| D3 | Test points / pads de programação | — | — |
| D4 | Watchdog externo (se decidir usar) | 1 | SOIC-8 — decisão pendente do Jailton `[DISCO]` (`ORCAMENTO.md`) |

**Regra dura:** o ferro de solda **não encosta** na placa com o módulo ESP32-S3 já soldado
sem dissipação. Ferro a 350 °C no pad do XT60 injeta calor no plano de GND/VBAT, que é
contínuo por toda a placa. `[EST]` Solde os THT **antes** do módulo, ou use ferro com
ponta grande + tempo curto (≤ 3 s por pino) e deixe o módulo para o fim.

---

## 4. O MÓDULO ESP32-S3-WROOM-1 — cuidados específicos

Este é o componente mais caro em risco de perda. `[DISCO]` ele **não existe no KiCad 5.1** —
a pegada foi gerada por script (`lista_componentes_fase0.csv`, coluna `existe_no_kicad = NAO`).
Logo, **confira a pegada contra o mechanical drawing antes de mandar o estêncil.**

1. **NÃO REFLOWAR DUAS VEZES.** O módulo deve passar por **uma única** exposição a pico.
   Nesta placa isso é natural: todos os 238 footprints estão na face superior `[DISCO]`,
   logo há **uma só passada**.
2. Se por qualquer motivo a placa precisar de uma segunda passada, **solde o módulo na
   segunda** e proteja o que já está montado. `[FONTE]` a J-STD-020 classifica os componentes
   para **até 3 ciclos** de reflow (TI, https://www.ti.com/lit/pdf/spraby1, consultado
   2026-09-11) — mas isso é o limite de qualificação do padrão, **não** uma recomendação de
   processo. Na dúvida, menos ciclos é melhor. `[PREMISSA]`
3. **Umidade (MSL).** Módulo guardado fora do envelope absorve umidade e "pipoca" no reflow.
   `[VERIFICAR]` — **não confirmei o MSL do ESP32-S3-WROOM-1** (não há datasheet no disco).
   Procedimento padrão a consultar no datasheet do módulo: se o nível MSL exige floor life
   curta e o módulo ficou exposto, **bake antes de soldar** (tipicamente 24 h a 125 °C).
   **Confirme no datasheet da Espressif antes de assar.**
4. **Can (blindagem metálica).** É uma massa de metal sobre o módulo: puxa calor e demora
   mais para o pad castelado inferior aquecer. `[EST]` Pré-aqueça e use ar quente circulando
   pelos **lados** (pads castelados), não soprando por cima do can.
5. **Antena de PCB.** `[EST]` não deixe pasta, fluxo ou estanho sobre a região da antena.
   Não lixe, não cubra com verniz. `[DISCO]` a Fase 0 já registra que o rádio 2,4 GHz precisa
   estar homologado e que "a antena/PCB não pode ser alterada sem reavaliação" (FASE0 §10.4).
6. **Limpeza ultrassônica: NÃO.** `[EST]`/`[VERIFICAR]` — módulos com cristal a quartzo podem
   sofrer com ultrassom. Não achei fonte confirmando para este módulo específico;
   **limpe com pincel + álcool isopropílico**, que é seguro em qualquer caso.
7. **ESD.** IMU, ADC, módulo e drivers são sensíveis. Pulseira + bancada aterrada
   obrigatórios. `[EST]`

---

## 5. LIMPEZA

1. `[EST]` Pasta com fluxo **no-clean**: não lave, não há necessidade elétrica. Se a placa
   ficar pegajosa em área de passo fino, limpe só a região.
2. Pasta com fluxo **solúvel em água**: lavar com água deionizada + escova antiestática,
   secar com ar quente **antes** de energizar. Resíduo ativo + umidade = fuga e corrosão.
3. **Álcool isopropílico (IPA) + pincel** para resíduo localizado. É o método seguro para o
   módulo.
4. **Nunca** lave a placa com o buzzer SMT e o barômetro sem conferir se são laváveis —
   `[VERIFICAR]` sensores de pressão têm orifício e podem reter líquido.
5. Depois de lavar: **inspeção de continuidade de novo** (§6 do plano de teste). Água entre
   planos de cobre dá leitura de "curto" falsa no multímetro.

---

## 6. INSPEÇÃO VISUAL E ELÉTRICA (antes de energizar)

| # | O que checar | Instrumento | Critério |
|---:|---|---|---|
| 1 | Alinhamento de QFN (IMU) e dos 41 pads do módulo | lupa 10× ou microscópio | pino deslocado **rejeita** |
| 2 | Ponte de solda entre pinos de SOIC-8 / QFN | lupa + multímetro em continuidade | **0 pontes** |
| 3 | Todas as 60 peças 0402 presentes | lupa | 0 faltando, 0 tombada |
| 4 | Polaridade dos 6 eletrolíticos e do LED | lupa | faixa do negativo no pad marcado |
| 5 | Orientação dos CI (pino 1) | lupa | 100 % conferido |
| 6 | Tobery/offset dos TO-252 | lupa, visão lateral | terminal central em cima do pad |
| 7 | Solda do tab do DPAK (por baixo, por via) | lupa + microscópio | sem vazio grosseiro |
| 8 | Shunts 2512 | multímetro (mΩ) | dentro de ~1 % de 0,5 mΩ |
| 9 | Continuidade XT60 / MR30 | multímetro | pino no pad, sem deslocamento |

---

## 7. RESUMO DA ORDEM (cola de bancada)

```
[A] finos/miudos   : barômetro → IMU(QFN 0,4 mm) → ADC → 12× SOIC-8-EP → 12× SOIC-8
                     → 2× SOIC-16 → 3× SOT-23 → 60× 0402 → ~52× 0603 → 24× SOD → TVS
[B] passivos       : 48× 0805(Rg) → 12× 0805(Cboot) → LED → 24× 1206 → 6× 1210
                     → fusível → 12× 2512(shunt) → 6× eletrolítico 470 µF
[C] massa térmica  : 24× TO-252 MOSFET + 1× P-FET → 3× indutor → buzzer → botões → USB-C
[D] through-hole   : XT60 + 4× MR30 + test points  (FERRO, por último)
[ ] MÓDULO ESP32-S3: UMA passada só. Se houver 2ª, ele vai na 2ª.
```

---

## 8. O QUE NÃO ESTÁ VERIFICADO NESTE DOCUMENTO

1. **Nenhuma destas soldas foi executada.** Isto é plano, não registro de execução. Não
   existe nenhuma placa montada nesta máquina.
2. **A placa v6 não está roteada** (§0) — o plano não é executável hoje.
3. **O perfil de reflow definitivo é o da pasta do Jailton** — `[VERIFICAR]`. Os perfis das
   §2.1/2.2 são típicos de mercado, de fontes web citadas, **não** da sua pasta.
4. **MSL / temperatura máxima do ESP32-S3-WROOM-1** — `[VERIFICAR]`, sem datasheet no disco.
5. **Nenhum dado de datasheet de qualquer componente está neste disco.** `[DISCO]`
   `FASE0_ESPECIFICACAO.md` P-15: "**[N/D offline]** todos os parâmetros de datasheet".
   Tudo que dependa de datasheet (temperatura de pico do CI, MSL, tempo de molhagem) tem de
   ser conferido por você.
6. Térmica real, EMI e comportamento dos 30 A **não se validam em bancada de solda** —
   ver `PLANO_TESTE_BANCADA.md` §"O que NÃO se valida".
