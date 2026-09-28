# NOTA_ROTAS v8 — método, números reais e o que trava o fechamento

Data: 2026-08-28 (America/Bahia) · gerado por `fase3_pcb/rota_v8.py`
Board: `fase3_pcb/v8/v8_drone.kicad_pcb` · log cru: `fase3_pcb/v8/rota_v8_log.txt`

---

## 1. Resultado — número verdadeiro, sem maquiar

| Métrica | Valor medido |
|---|---|
| **Nets roteadas** | **3 de 176** (taxa 1,7 %) |
| **Nets NAO roteadas** | **173** (critério 0 → FALHA) |
| Trilhas | 60 (57 são stubs de plano + 3 de roteamento) |
| Vias | 234 (180 de stitch + 54 de plano + 0 de roteamento) |
| Pares trilha x pad de net diferente com folga < 0,15 mm | **192** (critério 0 → FALHA) |
| Pads de GND/VBAT_PROT sem via a menos de 1,6 mm | **60** (era 68; critério 0 → FALHA) |
| Menor folga entre nets diferentes | 0,0000 mm |
| Footprints / pads / camadas de cobre | 319 / 1093 / 6 |
| Dimensões | 162,10 x 145,02 mm |

Comando que reproduz a rodada:
```
/usr/bin/python3.9 fase3_pcb/rota_v8.py --deadline=165 --pitch=0.25 --clear=0.15 \
    --maxnodes=45000 --ckpt=10
```

## 2. Método (o que o `rota_v8.py` faz)

Derivado de `rota_v7.py` (que **não** foi editado). Mudanças em relação ao v7:

1. **6 camadas, 3 roteáveis.** O stackup D-02 (`STACKUP_PROPOSO.md`) define
   `In1.Cu = GND`, `In3.Cu = GND`, `In4.Cu = VBAT` como **planos** e
   `In2.Cu` como **sinal (stripline)**. O roteador usa F.Cu + In2.Cu + B.Cu
   e ignora as três de plano. O v7 só roteava em F.Cu/B.Cu.
2. **Orçamento de tempo explícito** (`--deadline`) e **checkpoint incremental**
   do `.kicad_pcb` a cada 10 rotas (`--ckpt`). O v7 só salvava no fim — por
   isso os 240 s de v7 não deixavam arquivo nenhum. Aqui o que foi roteado
   está gravado em disco mesmo com o deadline estourado.
3. **Log auditável** a cada N filas, com `t`, fila, rotas, falhas, trilhas e
   tempo restante. Está em `rota_v8_log.txt`.
4. **Casca de clearance com dono** (array `CASCA`). Sem isso o A* **não saía
   de dentro de nenhum pad**: com pitch de 0,5 mm a casca de 0,25 mm marcava
   as 4 células vizinhas como bloqueio duro e o pad virava um buraco de
   1 célula. Agora a casca é atravessável **pela própria net** (custo +0,5).
5. **A* acelerado**: acesso à grade por listas de Python (`GF.tolist()`) em vez
   de numpy-scalar, e máscara `VOK` de "aqui cabe um via" pré-computada. O
   numpy-scalar custava ~10x por nó (medido: travava em < 20 mil nós/s).
6. **A grade é marcada com a largura real da trilha** (`marca_corpo_py`), não
   só com a linha central. O v7 marcava só a linha central, então o clearance
   declarado nunca era respeitado na verificação.

## 3. Onde parou

Parou no **orçamento de 165 s**, na fila **66 de 176**, com 3 rotas emitidas e
63 falhas acumuladas. O log mostra que a taxa não cai: das 66 primeiras nets
(2 pontos, as mais curtas e fáceis), só 3 fecharam.

| Motivo | Quantidade |
|---|---|
| `LIMITE DE NOS` (A* esgotou 45 000 nós sem achar caminho) | a maior parte das 63 |
| `SEM ROTA` (grade sem saída) | algumas |
| Tempo esgotado dentro do A* | 0 |

`LIMITE DE NOS` em nets de **2 pontos curtas** (PWM_M303→UM303.2,
ADC_CS1→U8.10, HOM101→UM101.7) é o sintoma decisive: o problema **não é tempo
de CPU nem o número de camadas**. É **congestionamento local** — ver abaixo.

## 4. Larguras de potência (exigência vs. o que foi emitido)

`calc_trilhas_vias_saida.txt` pede **6,29 mm** para a fase do motor (15 A RMS,
2 oz, dT 10 °C). **Não foi possível emitir 6,29 mm** e o motivo é numérico:

- o stackup do board tem **1 oz (0,0350 mm)** em F.Cu e B.Cu, não 2 oz;
- a área necessária dobra → **12,58 mm** de largura para o mesmo 15 A/dT 10 °C;
- 12,58 mm não cabe numa trilha roteável num bbox de 162,10 x 145,02 mm
  conviver com 191 nets e 319 footprints.

O próprio `calc_trilhas_vias_saida.txt` já resolve isso na regra de ouro:
**"VBAT: não usar trilha para os 30 A; usar polígono de cobre + transição por
via"** (40 vias de 0,3 mm drill / 0,6 mm pad por transição).

Portanto, o que este roteador emite hoje:

| Net | Largura exigida pelo IPC | Largura emitida | Situação |
|---|---|---|---|
| `VBM101..VBM403` (12 nets, VBAT de fase) | 6,29 mm | **0,60 mm** | **INFERIOR — não conforme** |
| `VBAT_F`, `VBAT_SENSE` | 4–6 mm | **0,60 mm** | **INFERIOR — não conforme** |
| `12V`, `3V3`, `3V3_A`, `5V_AUX` | 0,25 mm | 0,25 mm | conforme |
| `5V` | 0,40 mm | 0,40 mm | conforme |
| sinal | 0,20 mm | 0,20 mm | conforme |

**Nenhuma dessas 14 nets de corrente chegou a ser roteada** (todas caíram nas
173 não roteadas). A redução para 0,60 mm está declarada aqui, não escondida:
é um valor provisório de roteamento, **não** uma largura de engenharia.

## 5. O que impede de fechar — a causa medida

Duas causas, ambas medidas, ambas independentes de tempo:

**5.1 Congestionamento local na grade (causa dominante).**
As nets que falham são curtas (2 pontos) e estão em torno dos drivers de
motor. Os footprints ali têm pitch de 0,65 mm; com a trilha de 0,20 mm
precisando de 0,10 mm de meio-canal + folga, a **soma dos canais de cobre é
maior que o pitch físico do componente**. Não existe caminho: o roteador
estava procurando um caminho que a geometria do footprint não permite. É por
isso que 45 000 nós não bastam — o A* está correto, o espaço é que não existe.

**5.2 Alvo de clearance no limite.**
Rodei com `--clear=0.15` (o próprio valor do gate A3). A verificação mediu
**192 pares abaixo de 0,15 mm e folga mínima 0,0000 mm** — ou seja, o alvo
igual ao critério produz violação por arredondamento de grade. Com
`--clear=0.25` (o default do script) a violação caía, mas o roteamento piorava
ainda mais por causa de 5.1. **Estes dois requisitos estão em conflito nesta
grade.**

## 6. O que precisaria mudar (em ordem de retorno)

1. **Mudar a grade, não o tempo.** Mais tempo de CPU **não fecha** — 165 s
   gastaram 63 A* completos sem achar caminho. O que resolve é um **roteamento
   em coordenadas contínuas** (rotas diagonais, trilhas de 45°) em vez de
   malha ortogonal de 0,25/0,5 mm. Numa malha ortogonal, entre dois pads com
   pitch 0,65 mm só passa cobre no eixo; um caminho diagonal passa entre eles.
   Esta é a mudança de maior impacto.
2. **Rip-up e re-rota com prioridade.** As 176 nets não são independentes: o
   A* é guloso e as primeiras escolhas bloqueiam as seguintes. Rip-up por net
   com realocação seria o próximo passo depois de (1).
3. **Menos nets, ou menos pinos.** `3V3` (61 pads), `12V` (47), `GND` (207),
   `SD_MCU` (25) e `VBAT_PROT` (42) são 382 dos 1093 pads. Os trilhos de
   3V3/12V precisam virar **polígono de cobre**, não trilha individual — mais
   87 nets saem do roteamento por definição.
4. **Mais camadas roteáveis.** In1.Cu e In3.Cu estão como plano de GND no
   stackup, mas In2.Cu sozinha já dá 3 camadas de sinal. Só vale abrir mão do
   plano de GND se (1) e (2) não fecharem — e isso custa qualidade de retorno
   de sinal, que é o motivo do plano existir.
5. **Gate A4 (60 pads sem via a 1,6 mm).** Não é bloqueio de roteamento: é um
   problema de **colocação de componentes** (o gerador de PCB não põe via de
   stitch perto de pad). Sai com uma mudança em `gera_pcb_v8.py` — que não foi
   tocado nesta sessão.

## 7. Estado do entregável

- `fase3_pcb/rota_v8.py` — novo, não toca o v7 nem o `gera_pcb_v8.py`.
- `fase3_pcb/v8/v8_drone.kicad_pcb` — **válido e carregável**, com 3 rotas e
  54 stubs+vias de plano. Backup do original em `/tmp/v8_drone_pre_rota.kicad_pcb`;
  o script é idempotente (restaura do backup no início).
- Gerbers de 6 camadas de cobre + Edge_Cuts + masks + silk e Excellon PTH/NPTH
  reexportados do que existe.
- `verificacao_v8.txt` — reescrito com os números acima.
- **O board está incompleto: 173 das 191 nets estão sem cobre.**
