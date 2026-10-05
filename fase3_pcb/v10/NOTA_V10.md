# NOTA v10 — correções da auditoria de 2026-10-04

Data: 2026-10-05. Gerador: `fase3_pcb/gera_pcb_v10.py` (deriva do `gera_pcb_v9.py`,
que fica somente-leitura). Netlist: `fase3_pcb/gera_pcb_v7.py` **corrigido**
(typo `RBM###`→`RB_M###` e ferrite `3V3_IMU`). Verificação:
`fase3_pcb/verifica_fase3_v10.py` → `fase3_pcb/v10/verificacao_v10.txt`.
pcbnew 5.1.9. Motivação e evidência completa de cada erro:
[`AUDITORIA_ERROS_2026-10-04.md`](../AUDITORIA_ERROS_2026-10-04.md).

---

## 1. O que a v10 corrige em relação à v9

| | v9 (medido) | v10 (medido) |
|---|---:|---:|
| pads fora do contorno | **199** (27 footprints, incl. U_MCU inteiro e 14 MOSFETs) | **0** (gate G1) |
| curtos reais pad×pad | **14** (+16 pares críticos) | **0** (gate G3, SAT) |
| nets de 1 pad (abertas) | **13** (12 BEMF órfãs + 3V3_A_F) | **0** (gate G2) |
| vias dentro do keepout de borda | **8** | **0** (gate G4) |
| zonas de cobre vazias | **57 de 102** | **0 de 173** (gate G5) |
| nets de potência SEM cobre | **26** (VBAT, VBAT_F, 12×PHM, 12×SNM) | **0** — 34 zonas novas (gate C6) |
| keepouts de borda | 3 (faltava o superior) | **4** (esq/dir/topo/inf) |
| ocupação | 60,05 % (bbox **com texto de silk**) | **23,44 % elétrica** (pads) |
| nets no board | 191 | 179 (= 202 − 12 RBM fundidas − 12 SDM + 1 SD_MCU + 3V3_IMU) |
| conectividade BEMF | ADC **órfão** (typo `RBM###` vs `RB_M###`) | divisor→nó→ADC fechado (4 pads/net) |
| rail do IMU | ferrite órfão; IMU/baro na 3V3 digital | LDO→3V3_A→FLDO→**3V3_IMU**→IMU+baro+CIMU |
| A4 stitch (centro 1,6 mm) | 34 pads sem via | 18 (critério equivalente do GATES_REVISADOS em revisão) |

## 2. Bugs corrigidos (causa → efeito)

1. **`gera_pcb_v9.py:252` — sinal invertido**: `placed = X − dx` deslocava cada
   footprint centrado uma bbox inteira para a esquerda/cima. A v9 colocou a
   fileira de MOSFETs em y = −3,16 mm (fora da placa) e o U_MCU em x = −13,25 mm.
   Prova numérica do mecanismo: `y' = LIVRE_EDGE + 0 − dy` com `dy = 4,157`
   (texto de referência em −3,4 + fonte 1 mm) = −3,157 — exato ao centésimo o
   valor do arquivo.
2. **`fp_box_at` media o texto de silkscreen**: `GetBoundingBox()` incluía o
   value "NVMFS6H824NT1G" (~13,6 mm) — o espaçamento entre MOSFETs da v9 era
   14,08 mm (texto + GAP). Agora a bbox é a união dos **pads** (círculo
   circunscrito por pad + 0,15 mm).
3. **`gera_pcb_v7.py` — typo de net**: seção do motor `"RB%s" % t` (RBM101) vs
   seção do ADC `"RB_M%d01"` (RB_M101). As 12 entradas BEMF do ADC estavam
   órfãs e os divisores, sem consumidor. Padronizado `RB_%s`.
4. **`gera_pcb_v7.py:374` — ferrite órfão**: `FLDO.2` na net `3V3_A_F` (1 pad);
   IMU/barômetro na 3V3 digital. Criada `3V3_IMU` (FLDO.2 + U_IMU VDD/VDDIO +
   U_BARO VDD/VDDIO/CSB + CIMU.1).
5. **`acha_via`**: limite 0,8 mm < keepout (0,9 mm + folga 0,3 mm) gerava vias
   DENTRO da faixa proibida; agora respeita `keepout + clearance + raio`.
6. **Faltava o keepout da borda superior** — agora as 4 bordas têm faixa de
   0,9 mm.
7. **Zonas de potência**: só GND/VBAT_PROT/12V/5V/3V3/3V3_A tinham cobre.
   Adicionadas **VBAT, VBAT_F e as 24 nets de fase PHM\*/SNM\*** (F.Cu local,
   prioridade 60): o caminho de 30 A e as 24 fases agora têm condutor planejado
   (o refinamento fino continua no roteamento).

## 3. Pipeline FreeRouting — bug 1.h RESOLVIDO (prova executada)

Correções no `dsn_export.py`:
- **P1 — `0 == False`**: `pcbnew.PAD_SHAPE_CIRCLE == shape_enum` comparava o
  enum 0 com o **bool** retornado por `shape_is_circle()` → sempre True →
  **todo pad virava círculo Ø=max(w,h)**; o ramo `(rect …)` era inalcançável.
  Pads SOIC-8 Ø1,95 mm em pitch 1,27 mm **sobrepunham nets diferentes** — cada
  CI era um blob selado; o maze router falhava instantaneamente em toda
  conexão (as 9 nets do corte têm endpoint SOIC-8). Corrigido: `(rect …)` com
  envelope rotacionado por pad; círculo só para pads realmente circulares.
- **P2 — via nunca declarada**: acrescentado **`(via VIA1)`** na structure — o
  FR 1.9.0 só registra vias desse escopo (`Structure.java:866-868`); sem isso o
  board ficava **sem nenhuma via** (prova: `(library_out)` vazio nos SES
  antigos). Via alinhada à regra do board: 0,6/0,3 mm (era 0,8/0,4).
- **P3 — rotação dupla**: os offsets iam **já rotacionados** e o FR reaplicava
  a rotação do `(place …)`. Agora os pins vão em offsets **locais** (truque:
  orientação zero temporária no módulo durante a leitura) e o FR aplica a
  rotação — 51/105 pads do corte estavam em posição errada (até 4,4 mm).
- **P4 — pins duplicados**: a image recebia os pads de TODAS as instâncias do
  pacote (SOIC-8 com 96/384 entradas; projeção de ~39.000 pinos no board).
  Agora 1× por pacote (DSN completo: 40,5 KB vs 66,3 KB).
- **P5 — THT multicomada**: pads thru-hole recebem shape em todas as camadas.

**Prova E2E (corte de 16 módulos, motor 4 — mesmo corte que reproduzia o bug):**

| | corte v9 (bug 1.h) | corte v10 (corrigido) |
|---|---:|---:|
| "Auto-routing completed" | 0,82 s (fake) | **11,21 s** |
| wires no SES | **0** | **46** |
| vias no SES | 0 | **8** |
| nets roteadas | 0 de 9 | **9 de 9** (0 pads sem trilha — verificado) |
| trilhas importadas no KiCad | 0 | **83** (+ 8 vias) |
| `(library_out)` | vazio | com padstack de via |

**Prova E2E (placa COMPLETA, 319 footprints, 151 nets roteáveis no DSN):**

| | v9 (bug 1.h) | v10 (corrigido) |
|---|---:|---:|
| "Auto-routing completed" | 0,82 s (fake; 34,9 s no run antigo com DSN quebrado → 0 wires) | **49 min 47 s REAIS** (+ 7 min 48 s de otimização) |
| SES | 15 KB, **0 wires** | **252 KB, 1.410 wires, 404 vias** |
| nets roteadas | 0 | **149 de 151 do DSN** (ficaram `IMU_CS` e `IMU_INT` — conferir pinagem LGA-14/janela) |
| importado no KiCad | 0 | **3.909 trilhas + 404 vias** (4.711 elementos; 0 nets sem match) |
| conexões abertas | 627 | **363** (fechamento fino das nets de potência + 2 nets do IMU continua no worker) |

Artefatos: `freerouting_run/v10_dsn_input.dsn` (40,5 KB), `v10_final.ses` (252 KB),
`v10_pass3.frb` (checkpoint de 3 passadas, 481 KB — prova de retomada), logs
`freerouting_full.log`/`freerouting_full2.log`, board roteado **`v10_roteada.kicad_pcb`** (2,5 MB).

Bugs latentes adicionais corrigidos no `ses_import.py` (o importador **nunca
tinha completado uma execução**): `NETINFO_ITEM.GetNetCode()` → `GetNet()`;
`PCB_TRACK/PCB_VIA/VIATYPE_THROUGH` → nomes da API 5.1 (`TRACK/VIA/VIA_THROUGH`);
`walk_net` esperava wires direto sob `network_out` — o formato real é
`(network_out (net NOME (wire …)))`; linha morta `re.search(…, "")` removida.

## 4. Gates novos (verifica_fase3_v10.py)

G1 pads no contorno · G2 nets ≥2 pads · G3 curtos pad×pad (SAT) ·
G4 vias fora de keepout · G5 zonas preenchidas · G6 A4 stitch (critério
equivalente documentado) · G7 ocupação elétrica.

**Veredito da v10: G1–G5 e G7 = OK.** G6 (A4): 18 pads sem via — mesmos casos
duros de sempre (Cblk1–6, U_MCU.41, D1…). O gerador v10 agora estende o raio de
busca do `acha_via` para pads grandes (a busca antiga parava em 1,6 mm do centro,
menos que extent+RVIA para pads grandes) e o gate mede **borda-a-borda** conforme
o critério equivalente do `GATES_REVISADOS.md` A4. Nota: esses pads NÃO estão
desconectados — estão no pour de GND de F.Cu; a via adiciona robustez
inter-camada. A regeneração com o stitch novo ficou adiada de propósito: o
board roteado (`v10_roteada.kicad_pcb`) foi produzido contra as vias de stitch
atuais (as vias novas poderiam colidir com as trilhas importadas); a próxima
geração (v10.1/v11) já nasce com o acha_via estendido.

## 5. Pendências que a v10 NÃO resolve (decisão humana)

1. **Margem do MOSFET vencedor (auditoria C3)**: pior caso 25,2 + 60 = **85,2 V
   > 80 V** pelo critério interno de spike. Opções: aceitar o risco, reduzir o
   spike (snubber/layout) ou subir para FET ≥ 100 V. A `BOM_FABRICACAO_v10.csv`
   compra o vencedor com a pendência registrada na própria linha.
2. **Watchdog externo (D-07)** e **2× ADS7953 (D-12)**: decididos, mas ausentes
   do board (auditoria E-8) — o board v10 mantém 4× MCP3208 e não tem CI
   supervisor. A BOM v10 compra o que o board tem e registra a pendência.
3. Roteamento de sinal completo: o autorroteador roda agora sobre um DSN são;
   o resultado (nº de nets fechadas) define o trabalho manual restante.
