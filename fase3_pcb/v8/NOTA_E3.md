# NOTA E3 — board v8 de 6 camadas

**Data:** 2026-09-28 · **Máquina:** Orange Pi, Debian Bullseye aarch64 · **pcbnew:** 5.1.9+dfsg1-1+deb11u1
**Gerador:** `fase3_pcb/gera_pcb_v8.py` · **Verificador:** `fase3_pcb/verifica_fase3_v8.py`
**Board:** `fase3_pcb/v8/v8_drone.kicad_pcb` · **Relatório:** `fase3_pcb/v8/verificacao_v8.txt`
**Sidecar do stackup:** `fase3_pcb/v8/v8_drone_stackup.txt`

> Regra desta nota: todo número aqui foi medido nesta máquina por comando executado.
> Onde o critério não fecha, o número é o que é. Nada foi arredondado para "verde".

---

## 1. Resultado medido (saída real do verificador)

```
nets NAO roteadas : 189
pares trilha x pad (net diferente) proximos: 0
pads de GND/VBAT_PROT sem via a menos de 1.6 mm: 68
rule_area (keepouts): 3
camadas de cobre: 6
dimensoes: 162.10 x 145.02 mm
footprints / pads / tracks / vias: 319 / 1093 / 0 / 180
menor distancia pad GND/VBAT_PROT -> via : 0.818 mm (limite 1.60)
```

## 2. v7 → v8, o que mudou

| Item | v7 (medido) | v8 (medido) | Como |
|---|---|---|---|
| camadas de cobre | 4 | **6** | `SetCopperLayerCount(6)`; F/In1/In2/In3/In4/B |
| contorno (Edge.Cuts) | 220,10 × 160,10 mm | **162,10 × 145,02 mm** | reposicionamento dos 319 footprints |
| footprints | 319 | **319** | nenhum apagado; nenhum criado |
| pads | 1093 | **1093** | MOSFET 3 pads com net × 24 = mesmo total |
| nets declaradas | 202 | **191** | ver §3 (consequência do D-13) |
| MOSFET (24 un.) | `TO-252-3_TabPin2` | **`SOIC-8_3.9x4.9mm_P1.27mm`** | D-03 / NVMFS6H824NT1G |
| driver (12 un.) | IR2104 SOIC-8 | **IR2104 SOIC-8 (mantido)** | D-04 |
| F1 | `Fuse_Blade_Mini_directSolder` | **`Fuse_1206_3216Metric`** | D-15 |
| SD dos 12 IR2104 | 12 nets `SDM101..SDM403` | **1 net `SD_MCU`** | D-13 |
| tracks / vias | 252 / 353 | **0 / 180** | trilhas da v7 removidas (ver §5) |
| keepouts | 0 | **3** | `SetIsKeepout` → 3 tokens `(keepout` |

**Footprints movidos: 319 de 319** (100 %). Nenhum permaneceu na posição da v7.
O movimento é **só translação e rotação** — pegada nunca é escalada, porque
escalar de 220,10 para 162,10 mm deformaria pad de 0402 e quebraria a
integridade do footprint (seria placa falsa).

## 3. Decisões de componente

**MOSFET: `NVMFS6H824NT1G`** (onsemi, SO-8FL, 80 V, Qg 38 nC, Rds(on) 3,7/4,5 mΩ).
Pegada KiCad 5.1 usada: `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` — a mesma do IR2104.
Nos 24 MOSFETs o mapeamento de pad é o do datasheet: **pad 1 = gate**, **pad 2 =
dreno**, **pad 3 = source**; pads 4–8 ficam **sem net** (NC do SO-8FL). O pad de
tab do TO-252 foi redistribuído sobre o dreno correspondente, de modo que a
topologia elétrica da v7 se mantém.

**Driver: `IR2104` mantido.** O `6EDL7141` foi rejeitado: VQFN-48 exige ar quente
e viola a decisão de montagem caseira. Consequência aceita e registrada em §7.

**D-13 (SD → 1 GPIO).** Pads usados, exatamente:
- os **12 pads "3"** (SD) de `UM101, UM102, UM103, UM201, UM202, UM203,
  UM301, UM302, UM303, UM401, UM402, UM403` (os 12 IR2104);
- os **12 pads "1"** dos `RsdM1xx..RsdM4xx` (pull-up para 3V3 — os 12 ficam em
  paralelo no mesmo net, o que reforça o pull-up do GPIO, ~1 kΩ no total);
- **`U_MCU` pad "28"** — pino 28 não aparece em `MCU_NETS` da v7 (lá vão 1–27 e
  31–41), portanto é um GPIO livre do ESP32-S3.
Net criada: **`SD_MCU`**. Efeito colateral honesto: as 12 nets `SDM101..SDM403`
ficaram sem pad e o pcbnew as removeu no salvamento — por isso 202 → 191 nets, e
não 203. **O critério "202 nets com os mesmos nomes" não fecha: 191 fecham.** A
contagem de 202 só voltaria se o D-13 fosse desfeito.

**D-15 (fusível).** `F1` → `Fuse.pretty:Fuse_1206_3216Metric`, valor `FUSE-30A-1206`.
Pads usados: **pad "1" = `VBAT`** (entrada do pack) e **pad "2" = `VBAT_F`**
(saída para `Q1` e para a ponte de rearme `Rz1`). Fica no polo positivo do VBAT,
entre o conector e o barramento `VBAT_PROT`.

## 4. O que NÃO fechou, e por quê

**a) Contorno 150 × 110 mm — não fecha, e a área já prova que não fecha.**
Soma das áreas dos bounding boxes dos 319 footprints = **16 562,9 mm²**
contra **16 500 mm²** de um retângulo 150 × 110 — **100,4 %**, ou seja, precisaria
de densidade acima de 100 % *antes* de qualquer corredor de rota, keepout ou
folga. Não é falha do empacotador: é impossibilidade geométrica.
O empacotador (shelf, com escolha de rotação) foi varrido em 9 larguras e o
melhor retângulo medido é **162,10 × 145,02 mm**, que é o que está no board.
Para caber em 150 × 110 seria preciso mexer na **lista de Bill of Materials**
(remover componente), não no empacotador.

**b) Gate A8 — `rule_area` não existe no formato do KiCad 5.1.9.** As 3 rule areas
são **reais** (`SetIsKeepout(True)` + `SetDoNotAllowTracks/Vias/CopperPour`,
que viram 3 tokens `(keepout` no arquivo). Mas o token literal `rule_area` — e
também `(name ...)` dentro de `zone` e `(stackup ...)` — **não são reconhecidos
pelo parser 5.1.9**, e injetá-los deixa o board **ilegível**. Medido, um por um:
```
(stackup ..) -> OSError: Unexpected "stackup" in input/source
(name    ..) -> OSError: Expecting "net, layer/layers, tstamp, hatch, ..."
(title   ..) -> OSError: Unknown token "title" in input/source
```
Escolha feita: **board carregável e verdadeiro > board bonito e quebrado**.
O bloco `(setup (stackup ...))` do `STACKUP_PROPOSTO.md` foi extraído e gravado
inteiro em `fase3_pcb/v8/v8_drone_stackup.txt`, pronto para colar em projeto
KiCad ≥ 6.0 ou no pedido ao fabricante. O gate A8, se ler `grep -c rule_area` no
`.kicad_pcb`, dá **0** — e isso é limitação de formato, não ausência de
keepout.

**c) Gate A4 — 68 pads de GND/VBAT_PROT a mais de 1,6 mm de uma via.**
Foram criadas **180 vias de stitch** cobrindo 181 dos 249 pads; a **menor
distância medida** é **0,818 mm**. Sobraram **68 pads** sem via dentro de 1,6 mm,
concentrados em pads whose vizinhos occupied the 8 direções candidatas (o
empacotador com 0,45 mm de folga entre peças não deixa ângulo livre). Fechar
isso exige aumentar o `GAP` do empacotador, o que aumenta a área e piora o item
(a) — é um compromisso, não um bug.

**d) Roteamento: 189 nets sem trilha.** Ver §5.

**e) Larguras de potência: mantidas por constante, não aplicadas.**
`calc_trilhas_vias_saida.txt` confere fase do motor 6,29 mm, VBAT 4/6/8 mm,
12 V 0,07 mm, 5 V 0,39 mm, 3V3 0,26 mm. As constantes `W_PHASE=6.29`,
`W_VBAT=6.0`, `W_GATE=0.40`, `W_FASE_CU=4.0` da v7 estão **inalteradas** no
gerador v8. Como não há trilha gerada, elas ainda não foram aplicadas a um
objeto do board — estão prontas para o roteador, nenhuma foi reduzida.

## 5. Por que há 0 trilhas

As 605 trilhas/vias da v7 foram desenhadas para as **posições antigas** dos
footprints. Como a v8 reposiciona os 319 footprints para fechar o contorno menor,
manter as trilhas deixaria **605 segmentos soltos no ar**, sem_pad em ponta —
isto é, um board que abre bonito no KiCad e não funciona. Elas foram removidas
(`BRD.Remove(t)`, 605 itens, medido) e o roteamento precisa ser refeito com
`fase3_pcb/rota_v7.py` (roteador A* caseiro, entrada v7 → saída v8) como etapa
seguinte. **Não rodei o roteador dentro do E3** — o tempo da etapa estourou, e
rodar o A* sobre 191 nets sem antes decidir o `GAP` do empacotador produziria um
número que não se sustentaria.

## 6. Estado dos gates

| Gate | Critério | Medido | |
|---|---|---|---|
| A4 | pads GND/VBAT_PROT sem via < 1,6 mm = 0 | **68** | 🔴 |
| A8 | `rule_area` > 0 no `.kicad_pcb` | **0** (3 keepouts reais) | 🔴 |
| A8b | keepouts reais (`(keepout`) > 0 | **3** | 🟢 |
| — | camadas de cobre = 6 | **6** | 🟢 |
| — | footprints = 319 | **319** | 🟢 |
| — | pads = 1093 | **1093** | 🟢 |
| — | trilha × pad (net diferente) a < 0,15 mm = 0 | **0** | 🟢 |
| — | contorno ≈ 150 × 110 | **162,10 × 145,02** | 🔴 |
| — | nets com os mesmos nomes = 202 | **191** | 🔴 |
| — | vias de stitch > 0 | **180** | 🟢 |

## 7. As 3 folgas que permanecem (de `fase0_especificacao/verifica_limites_v7_saida.txt`)

| Folga | Alvo | Medido | Erro | Consequência na v8 |
|---|---|---|---|---|
| **L1** tempo de subida do gate | 50 ns | **292,3 ns** | **+484,6 %** | O IR2104 entrega 0,25 A de pico contra 1,2 A necessários; o FET entra em regime linear devagar e a comutação perde ~240 ns. A v8 **não muda isso** — é limite de corrente do driver, não de layout. Agrava-se: sem Rg ajustado, o slew fica no pior caso. |
| **L6** slew de Vgs no turn-ON | 0,30 V/ns | **0,03421 V/ns** | **−88,6 %** | Com 0,034 V/ns, levar 4,5 V de Vgs até o ponto de resistência do canal leva ~131 ns; somado a L1 dá ~423 ns de atraso. A v8 mantém `Rgo/Rgf` de 0805 sem valor de resistencia alterado, logo a folga é **idêntica à v7**. |
| **L8** perda total por FET no pico | 0,583 W | **1,022 W** | **+75,2 %** | 1,022 W por MOSFET × 24 MOSFETs = **24,5 W** dissipados no pico, contra 0,583 W especificado por FET. Com Rds(on) de 4,5 mΩ do NVMFS6H824, o calor vai para o pad do SO-8FL, que tem ~1/4 da área de dissipação do TO-252 que a v7 usava. **A troca MOSFET→SO-8FL agrava L8** e exige cobre do pad de dreno ligado a `VBAT_PROT`/`PH*` por cobre generoso — que é justamente o que falta rotear. |

**Leitura honesta:** L1 e L6 só fecham com o `6EDL7141` (1,5 A → 25,3 ns e
0,3947 V/ns, ambos verdes), que foi **rejeitado** por decisão de montagem.
L8 é a folga que a v8 torna **pior**, e ela é a razão de o roteamento de
potência ser o item nº 1 da próxima etapa. As três são vermelhas e nenhuma foi
declarada verde aqui.

## 8. O que falta para o gate G1

1. **Rotear as 189 nets** com `rota_v7.py` aplicando `W_PHASE=6,29`,
   `W_VBAT=4/6/8`, trilhos 12 V/5 V/3V3 — e refazer o plano de `VBAT_PROT`
   como **polígono** (regra de ouro de `calc_trilhas_vias_saida.txt`), não trilha.
2. **Fechar o gate A4** (68 pads): aumentar `GAP` do empacotador ou aceitar
   via-em-pad nos 68 casos.
3. **Decidir o contorno**: ou aceitar 162,10 × 145,02 mm, ou cortar BOM.
4. **Levar o stackup ao fabricante** por `v8_drone_stackup.txt`, já que o
   KiCad 5.1.9 não o aceita no `.kicad_pcb`.
5. **Resolver L8** com dissipação do SO-8FL antes de qualquer gerber de produção.
