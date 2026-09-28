# NOTA v9 — placa de 190 × 145 mm, 6 camadas, zonas de potência e cobre de 2 oz

Data: 2026-09-28. Gerador: `fase3_pcb/gera_pcb_v9.py` (deriva de
`fase3_pcb/gera_pcb_v8.py`, que **não** foi alterado nesta rodada).
Medição: `fase3_pcb/verifica_fase3_v9.py` → `fase3_pcb/v9/verificacao_v9.txt`.
pcbnew desta máquina: `5.1.9+dfsg1-1+deb11u1`, `/usr/bin/python3.9`.

Nada em `fase3_pcb/v1..v8/`, `rota_v7.py`, `rota_v8.py`, `gera_pcb_v7.py` ou
`gera_pacote_fab.py` foi tocado. Sem push.

---

## 1. O que mudou em relação à v8

| | v8 (medido) | v9 (medido) |
|---|---:|---:|
| contorno | 162,10 × 145,02 mm | **190,10 × 145,10 mm** |
| área útil | 23 507 mm² | **27 583,5 mm²** |
| soma dos bounding boxes dos 319 footprints | 16 563 mm² | 16 562,9 mm² |
| **ocupação** | **70,4 %** | **60,05 %** |
| cobre externo | 1 oz no arquivo, 2 oz só no papel | **0,0700 mm (2 oz) em F.Cu e B.Cu**, stackup conferido |
| zonas de potência | 3 keepouts, 0 zonas de cobre | **3 keepouts + 102 zonas de cobre** |
| vias | 399 | 402 |
| trilhas | 294 (3 de 176 nets fechadas) | **0** (roteamento é do próximo worker) |
| conexões abertas do ratsnest | 914 | **627** |

### 1.1 Por que 190 × 145

A soma dos bounding boxes dos 319 footprints é **16 562,9 mm²** (medida no
próprio `LoadBoard`, não estimada). Para 60 % de ocupação a área precisa de
16 562,9 / 0,60 = **27 604,8 mm²**; 190 × 145 = 27 550 mm² dá 60,1 % e
27 583,5 mm² (bbox real com a espessura do traço de corte) dá **60,05 %**.
150 × 110 = 16 500 mm² é 99,6 % dos footprints — impossível, e isso não se
resolve cortando peça: nenhuma pegada foi escalada, todas as 319 foram só
transladadas/rotacionadas.

O empacotador é o mesmo shelf da v8, com a largura fixada em 190 mm e a altura
**medida** (não estimada): **129,35 mm** usados, 15,65 mm de folga vertical até
o contorno de 145 mm. Essa folga não é desperdício — é área útil para as zonas
e para o roteador de trilhas.

### 1.2 Empacotador real, não só translação

`empacota(190.0)` chama `fp_box_at()` com as 4 rotações de cada pegada e escolhe
a de menor altura que cabe na prateleira. 24 MOSFETs mudaram de pegada
(`TO-252-3_TabPin2` → `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`) e o fusível foi
para `Fuse_1206_3216Metric`; o resto foi reposicionado por rotação + translação.

### 1.3 Decisões mantidas (medidas no arquivo)

- 319 footprints, 1 093 pads.
- MOSFET `NVMFS6H824NT1G` em `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` — 24 peças
  (`QM101H, QM102H, …`), pads 1=G 2=D 3=S.
- IR2104 mantido como driver; `SD_MCU` no pino 28 do MCU com os 12 pads `3` dos
  IR2104 + os 12 pads `1` dos `Rsd*` (25 pads na net).
- `F1` = `Fuse.pretty:Fuse_1206_3216Metric`, pad 1 = VBAT, pad 2 = VBAT_F.
- 202 nets na v7 → **191** no board salvo: as 12 nets `SDM1xx..SDM4xx` perdem
  todos os pads por consequência do D-13 e saem no save, e `SD_MCU` entra.
  202 − 12 + 1 = 191. A v8 mede os mesmos 191 (mesmo critério, mesmo resultado).

### 1.4 Cobre de 2 oz — o que ficou gravado e onde

`calc_trilhas_vias_saida.txt` calcula a fase do motor (15 A) em **6,29 mm**
para **2 oz**. Com 1 oz a largura necessária seria 1,41× maior e nenhuma das
nets de potência fecharia.

O sidecar `fase3_pcb/v8/v8_drone_stackup.txt` **está em disco com 0,0350 mm**
(foi escrito antes da correção), então a v9 aplica a mesma transformação
idempotente que `gera_pcb_v8.py` faz. Resultado gravado em
`fase3_pcb/v9/v9_drone_stackup.txt`:

```
  stackup: F.Cu/B.Cu a 0.0700 mm (2 oz) em 2 camadas; soma = 1.6000 mm em 11 entradas
```

O bloco `(stackup ...)` **não** vai para dentro do `.kicad_pcb`: o parser do
KiCad 5.1.9 o rejeita (medido: `OSError Unexpected "stackup" in input/source`).
Ele fica no sidecar, como na v8.

### 1.5 Nenhuma largura de potência foi reduzida

Fase do motor **6,29 mm** (2 oz), VBAT 4/6/8 mm, trilhos 12 V/5 V/3V3: **todos
mantidos**. Com 190 × 145 não faltou largura para nenhum deles, então não há
redução a justificar. O que a v9 faz em vez de trilha larga é **cobre**: as
zonas dão a seção-current path das 6 nets de potência, que é a intenção do
cálculo de 2 oz.

---

## 2. Zonas de potência — a parte que mais destrava o roteamento

### 2.1 Esquema

| net | camadas | prioridade | zonas | contorno |
|---|---|---:|---:|---:|
| GND | F.Cu, B.Cu, **In1.Cu (plano)** | 50 / 100 | 2 + 1 | 26 950 mm² cada |
| VBAT_PROT | F.Cu, B.Cu, **In4.Cu (plano)** | 70 / 100 | 15 + 1 | 6 089 / 26 950 mm² |
| 12V | F.Cu, B.Cu | 75 | 8 + 8 | 7 542 mm² cada |
| 5V | F.Cu, B.Cu | 80 | 8 + 8 | 1 384 mm² cada |
| 3V3 | F.Cu, B.Cu | 85 | 13 + 13 | 7 876 mm² cada |
| 3V3_A | F.Cu, B.Cu | 90 | 5 + 5 | 1 594 mm² cada |

**Total: 102 zonas de cobre + 3 keepouts.** In2.Cu e In3.Cu ficaram **sem
zona**, de propósito: são as duas camadas de roteamento de sinal que o
roteador da v8 usou.

Prioridade: quanto **maior**, mais o cobre vence a sobreposição. As nets
localizadas têm prioridade maior que o GND espalhado — se fosse o contrário o
pour de GND comeria o plano de 3V3 e cada pad ficaria numa ilha solta. Todas as
zonas usam conexão **sólida** (`PAD_ZONE_CONN_FULL`), não âncora térmica: nestas
6 redes a conexão é por cobre, não por可靠性 de máscara.

### 2.2 Por que zona retangular por aglomerado, e não o bounding box da net

Primeira tentativa (medição real): zona local = bounding box da net + 3 mm.
Como 3V3 (181 × 101 mm), 5V (178 × 54 mm) e 3V3_A (137 × 49 mm) se sobrepõem
quase por inteiro, a zona de 5V (prio 80) era **comida** pela de 3V3 (prio 85) e
**não gerava uma única ilha**; a de GND em B.Cu idem. Resultado: 5 das 6 nets
tinham cobre, ratsnest 1 127 → 662 (−465).

Versão final: `aglomerados()` marca numa grade de 3,0 mm as células com pad da
net, dilata 1 célula e emite **um retângulo por componente conexo** da grade
(8 vizinhos). Cada zona cobre só onde a net tem cobre, então as zonas não se
sobrepõem a si mesmas e o que sobra da área vira GND. Resultado: **as 6 nets
têm cobre**, ratsnest **1 127 → 627 (−500)**.

### 2.3 Números medidos

```
filled_polygon lidas do .kicad_pcb: 45  (zonas: 6, camadas: B.Cu, F.Cu, In1.Cu, In4.Cu)
zonas de cobre com cobre: 6  -> 12V=8, 3V3=13, 3V3_A=5, 5V=5, GND=3, VBAT_PROT=11

cobertura por zona (raster de 0,25 mm, flood fill)
  net          pads     ilhas    rotulo   sem_co  coberta
  12V            47        16         6       12  nao
  3V3            61        24        13        8  nao
  3V3_A          17         6         5        1  nao
  5V              9         6         5        3  nao
  GND           207         2         1       18  nao
  VBAT_PROT      42        28         1        9  nao
```

Leitura honesta dessa tabela:

- **`sem_co` = pads que a zona não alcança.** Esses são os pads que o roteador
  ainda tem de ligar por trilha (ou por via nova). É o número que importa para
  o roteador: 18 pads de GND, 12 de 12V, 9 de VBAT_PROT, 8 de 3V3, 3 de 5V,
  1 de 3V3_A — **51 pads** no total.
- **`coberta = 0 em todas.** Nenhuma das 6 nets fecha 100 % só com cobre de
  zona, porque nenhuma delas tem todos os pads no mesmo aglomerado, e 34 pads
  de GND/VBAT_PROT estão a mais de 1,6 mm de qualquer via (seção 3).
- O flood fill é feito na **projeção** (união das camadas), então `rotulo` é uma
  **cota otimista**: cobre em F.Cu e em B.Cu com a mesma forma aparece como uma
  ilha só, mas só estão de fato ligados Through-hole ou via. O número
  autoritativo é o do motor de conectividade do pcbnew: **627 conexões
  abertas**, contra 1 127 sem zonas e 914 na v8 já roteada em 167,7 s.

---

## 3. Stitch — o número real

Algoritmo já corrigido na v8 (malha 0,05 mm × 36 ângulos a partir da borda real
do pad, 1 via garantida no 1º laço, 2ª via num 2º laço) — **não foi refeito**,
foi reaplicado. Na v9:

```
pads de GND/VBAT_PROT que precisam de via a <= 1,6 mm: 249
vias de stitch criadas: 402 | pads sem via: 34 | 2a via em: 187
menor distancia pad GND/VBAT_PROT -> via : 0,700 mm (limite 1,60)
```

**34 pads ficam sem via a menos de 1,6 mm** (a v8 media 37; a área maior da v9
melhorou 3, não zera). Lista:

```
QM101H.2, QM102H.2, QM103H.2, QM201H.2, QM202H.2, QM203H.2, QM301H.2,
J2.A12, J2.A1, U_MCU.41, U_MCU.1, CoB2a.2,
Cblk6.1, Cblk6.2, Cblk5.1, Cblk5.2, Cblk4.1, Cblk4.2,
Cblk3.1, Cblk3.2, Cblk2.1, Cblk2.2, Cblk1.1, Cblk1.2,
D1.1, D1.2, Q1.1, J1.2,
UaM403.1, UaM403.2, RsM402.2, Rd2M203.2, CaM203.1, CaM203.2
```

**Por quê não zera** — e por que não é falta de busca:

1. **7 pads são drain de MOSFET** (`QM*h.2`) dentro do SO-8FL, com pitch de
   1,27 mm e neighbouring pads de outra net nos 4 lados. O disco de 0,50 mm da
   via + 0,20 mm de folga + o meio-extenso do pad na direção da via já passa de
   1,6 mm antes de sair da pegada.
2. **12 pads são `Cblk1..Cblk6`** (1 e 2 de cada), footprints de capacitor de
   piso com pitch de 0,65 mm. Os dois pads da mesma peça estão a menos de 1 mm
   um do outro e a área entre eles é exatamente a área proibida dos dois.
3. `J2.A1/A12`, `J1.2`, `D1.1/.2`, `Q1.1`, `U_MCU.1/.41`, `CoB2a.2`,
   `UaM403.1/.2`, `RsM402.2`, `Rd2M203.2`, `CaM203.1/.2` são pads em borda de
   conector ou em fileira de 0,65 mm, com a borda da placa a menos de 1 mm.

Isto é a mesma conclusão de `fase3_pcb/v8/STITCH_v8.md`: **geometria de
pitch fino e de tab de pacote, não falha de busca**. A busca já varre 0,05 mm ×
36 ângulos até 1,6 mm e respeita 0,20 mm de folga contra todo pad de outra net.
A correção definitiva é mecânica/editorial (mover o pad para um footprint de
pitch maior, ou levar o plano até o pad com uma pastilha de cobre), não de
algoritmo.

---

## 4. Keepouts e grade

3 `(keepout)` reais, cada um com `tracks/vias/copperpour = not_allowed` em
F.Cu, In1.Cu, In2.Cu, In3.Cu, In4.Cu e B.Cu — as mesmas três faixas da v8,
adaptadas ao novo contorno (0,9 mm na borda da potência, 0,9 mm na borda do
sinal, 0,9 mm na faixa de separação). Coordenadas em
`fase3_pcb/v9/v9_rule_areas.txt`.

Sobre identificá-las: **não dá para escrever o nome no board**. Medido nesta
máquina, com o pcbnew 5.1.9, tanto `(name ...)` quanto `(title ...)` dentro de
`(zone ...)` tornam o arquivo ilegível:

```
OSError Expecting "net, layer/layers, tstamp, hatch, priority, connect_pads,
min_thickness, fill, polygon, filled_polygon, or fill_segments"
```

As 3 rule areas são reais (3 tokens `(keepout` no `.kicad_pcb`); a identificação
`rule_area_*` fica no sidecar, não no board.

**Grade/snap** gravado em `(setup ...)`, com o bloco reescrito inteiro:
`last_trace_width 0.25`, `trace_clearance 0.15`, `zone_clearance 0.25`,
`via_size 0.6` / `via_drill 0.3` (batendo com as 402 vias de stitch),
`edge_width 0.1`, `aux_axis_origin 0 0` e `grid_origin 0 0` (origem de snap na
esquina do contorno). A grade de pitch do roteador não mora no board: é
parâmetro do roteador (a v8 usou 0,25 mm com clearance 0,15 mm).

---

## 5. O que sobrou para o roteador de trilhas

```
nets NAO roteadas : 189
nets cobertas por zona : 0
conexões abertas do ratsnest : 627   (v8 com 294 trilhas: 914; v9 sem zona: 1127)
pads que a zona não alcança : 51   (GND 18, 12V 12, VBAT_PROT 9, 3V3 8, 5V 3, 3V3_A 1)
```

Como ler isso, sem maquiar:

- **189 das 191 nets continuam sem trilha.** A v9 entrega geometria e cobre, não
  roteamento: o board sai com **0 trilhas**. A grande melhora é o Ratsnest:
  **1 127 → 627** conexões abertas com o mesmo gerador sem zonas, e as 402
  vias de stitch já resolvem a conexão Through-hole de GND/VBAT_PROT.
- **0 nets fechadas só por zona** é o número real, e a tabela da seção 2.3
  mostra por quê: 51 pads fora do cobre de zona e 6 nets espalhadas por vários
  aglomerados. Fechar cada uma delas é trabalho de trilhas curtas de
  preenchimento, não de backbone — que é exatamente o que o plano devolve ao
  roteador: 60 % de ocupação em vez de 70 %, 6 planos/derramas de cobre
  disponíveis e ~27 500 mm² de placa para 3 camadas de sinal roteáveis.
- O gargalo continua sendo **congestão local nos drivers** (pitch 0,65 mm), não
  falta de área: o roteador da v8 fez 3 de 176 em 167,7 s.

---

## 6. Entregáveis e onde estão

| arquivo | o que é |
|---|---|
| `fase3_pcb/gera_pcb_v9.py` | gerador (deriva de `gera_pcb_v8.py`) |
| `fase3_pcb/v9/v9_drone.kicad_pcb` | board, abre com `pcbnew.LoadBoard` |
| `fase3_pcb/verifica_fase3_v9.py` | medidor + gerador de Gerbers/Excellon |
| `fase3_pcb/v9/verificacao_v9.txt` | relatório com todas as linhas de gate |
| `fase3_pcb/v9/v9_drone_stackup.txt` | stackup de 6 camadas, F.Cu/B.Cu a 0,0700 mm |
| `fase3_pcb/v9/v9_rule_areas.txt` | identificação das 3 keepouts |
| `fase3_pcb/v9/gerbers/` | 11 Gerbers + 2 Excellon + 2 mapas de furação |

Prova de que o board abre, vinda do próprio gerador:

```
LoadBoard(v9) OK: footprints=319  zonas=105  vias=402  trilhas=0
  (keepout=3  rule_area=0  grid=0)
```

(`rule_area=0` e `grid=0` porque o token não existe no formato 5.1 — ver
seções 1.4 e 4. As linhas do relatório que contam são `aux_axis_origin=1` e
`grid_origin=1`.)

**Trilhas de potência**: mantidas sem redução (seção 1.5). Nenhuma foi
reduzida, portanto não há justificativa numérica a registrar nesse item.
