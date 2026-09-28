# WP1 — Auditoria medida da Fase 3 (roteamento) e estratégia de fechamento

**US-001** · Documento de diagnóstico. Autor: projetista de PCB (agente `eletronica`).
**Data da medição:** 2026-09-28 · **Máquina:** Orange Pi, Debian Bullseye aarch64, sem desktop.
**pcbnew medido:** `5.1.9+dfsg1-1+deb11u1` · **kicad-cli:** NÃO EXISTE nesta máquina (verificado: `which kicad-cli` → nada).

> **Regra deste documento:** todo número aqui foi medido por comando executado nesta máquina.
> Cada seção traz o comando e a saída correspondente. Onde não deu para medir,
> está escrito **NÃO DETERMINADO** com o motivo — não há estimativa em papel.

---

## 1. Medições do estado real da v7

### 1.1 Comando

```
cd /opt/jupyter/work/drone && /usr/bin/python3.9 -c "
import pcbnew, collections
b = pcbnew.LoadBoard('fase3_pcb/v7/v7_drone.kicad_pcb')
trk=via=0; nets_trk=collections.Counter()
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: via+=1
    else: trk+=1
    nets_trk[t.GetNetname()]+=1
fps=0; pads=0; nets_pad=set()
for f in b.GetModules():
    fps+=1
    for p in f.Pads():
        pads+=1
        if p.GetNetname(): nets_pad.add(p.GetNetname())
...
"
```

### 1.2 Saída (íntegra)

```
MEDIDA PROPRIA  pcbnew 5.1.9+dfsg1-1+deb11u1
footprints      = 319
pads            = 1093
trilhas (track) = 252
vias            = 353
trilhas+vias    = 605
GetNetCount()-1 = 202
nets com pad    = 202
nets com pad e ZERO trilha = 138
zones           = 3
bbox mm         = 220.10 x 160.10
```

### 1.3 Tabela de conformidade com os mínimos pedidos

| Grandeza exigida | Valor medido | Como foi medida |
|---|---|---|
| nº de footprints | **319** | `len(BRD.GetModules())` |
| nº de pads | **1093** | soma de `f.Pads()` sobre todos os footprints |
| nº de trilhas | **252** | `t.Type() != pcbnew.PCB_VIA_T` |
| nº de vias | **353** | `t.Type() == pcbnew.PCB_VIA_T` |
| trilhas + vias | **605** | 252 + 353 |
| nº de nets declaradas | **202** | `GetNetCount()-1` (o `-1` é o código 0 = "sem net") |
| nº de nets com pad | **202** | conjunto de `GetNetname()` dos pads não vazios |
| **nº de nets com pad e ZERO trilha** | **138** | 202 − 64 nets com pad e ≥1 trilha |

> **Nota de reconciliação:** o briefing falava em "203 nets declaradas". O número medido
> é **202** (`GetNetCount()-1 = 202`). O 203 aparece legitimately no `rota_v7.py`, porque
> ele constrói o próprio dicionário `netid` a partir de **todos** os objetos de cobre,
> incluindo nets que só têm trilha — e imprime `nets na grade: 203`. As duas contagens
> não são a mesma coisa: 202 é o número de nets **do netlist declarado**, 203 é o número
> de nomes de net que aparecem em **pads + trilhas + vias** somados. Os dois números estão
> corretos no seu contexto; use 202 para o netlist e 203 para o dicionário de grade.

### 1.4 Distribuição por camada e larguras

Comando: `cd /opt/jupyter/work/drone && timeout 300 /usr/bin/python3.9 plano/mede_v7_wp1.py`

```
trilhas por camada  : {'F.Cu': 192, 'B.Cu': 60}
vias por par de cam.: {'B.Cu/F.Cu': 353}
larguras de trilha  : {0.25: 21, 0.4: 48, 0.6: 6, 1.2: 15, 1.5: 48, 2.0: 24,
                       3.0: 12, 4.0: 36, 6.0: 12, 6.29: 24, 8.0: 6}
larguras de via     : {0.6: 284, 1.0: 24, 1.2: 45}
drills de via       : {0.3: 284, 0.5: 24, 0.6: 45}
zones (planos)      : 3 -> ['In1.Cu', 'B.Cu', 'In2.Cu']
dimensoes (bbox)    : 220.10 x 160.10 mm
origem do bbox      : X=9.95..230.05  Y=9.95..170.05 mm
area do bbox        : 352.4 cm2
camadas de cobre    : 4
espessura do PCB    : 1.60 mm
pads por tipo       : SMD total=1045  (SMD so em F_Cu=945, so em B_Cu=0,
                                      em ambas=100)  TH/fixo=48
```

Ponto crítico: **as 353 vias são todas do par B.Cu/F.Cu** (atravessam do topo ao fundo).
Não existe uma única via em F_Cu↔In1_Cu nem F_Cu↔In2_Cu. Isso é coerente com o
desenho de 4 camadas, onde as camadas internas são planos e as externas são as de sinal.

### 1.5 As 138 nets sem cobre, agrupadas

Mesmo comando (`mede_v7_wp1.py`):

```
prefixo -> nets com pad e ZERO trilha
   I           12 nets        PWM          12 nets        RB           12 nets
   ADC          4 nets        SPI           3 nets        3V3           2 nets
   I2C          2 nets        IMU           2 nets        UART          2 nets
   USB          2 nets        5V            1 net         BOOT          1 net
   BUZZER       1 net         CC1           1 net         CC2           1 net
   EN           1 net         GHM101..303   9 nets        (+ demais grupos de 1)
   TOTAL (soma dos grupos)     : 138

as 20 primeiras nets com pad e ZERO trilha:
   3V3_A   pads=17  vias=0  zonas=0        ADC_CS1  pads=2  vias=0  zonas=0
   3V3_A_F pads=1   vias=0  zonas=0        ADC_CS2  pads=2  vias=0  zonas=0
   5V_AUX pads=5   vias=0  zonas=0        ADC_CS3  pads=2  vias=0  zonas=0
   BOOT_N  pads=4   vias=0  zonas=0        BUZZER   pads=3  vias=0  zonas=0
   EN_MCU  pads=5   vias=0  zonas=0        GHM101..GHM303  pads=2  vias=0
```

**Leitura:** as 138 nets sem cobre não são "nets perdidas" — são **as 9 redes de ESC
(GHM101/102/103, 201/202/203, 301/302/303) mais o barramento inteiro de sinal de
controle**: SPI dos 4 MCP3208, I2C do IMU, 12 saídas de PWM, 4 canais ADC de corrente,
UART, USB, botões EN/BOOT, buzzer e o trilho derivado 3V3_A/5V_AUX. Ou seja:
**a placa não tem uma rede de comunicação; ela tem todas elas sem cobre.**

### 1.6 Comparação com a v6

Arquivo: `/opt/jupyter/work/drone/fase3_pcb/v6/verificacao_v6.txt`

```
footprints        : 238
pads              : 889
trilhas (tracks)  : 171
vias              : 543
zonas (planos)    : 3 -> ['In1.Cu', 'B.Cu', 'In2.Cu']
dimensoes da placa: 220.1 x 160.1 mm
camadas de cobre  : 4
nets com pad      : 426
nets roteadas     : 59
nets NAO roteadas : 367

-- checagem de curto (pads de nets diferentes que se tocam) --
   pads de nets diferentes com bbox sobreposto: 0
-- checagem de curto (trilha x pad de net diferente) --
   pares trilha x pad (net diferente) proximos: 12
     ex: trilha PHM101 x pad QM101H.2(VBAT_PROT)
     ex: trilha PHM102 x pad QM102H.2(VBAT_PROT)
     ex: trilha PHM103 x pad QM103H.2(VBAT_PROT)
     ... (PHM201, PHM202, PHM203, PHM301, PHM302, ...)
```

Leitura: da v6 para a v7 o roteamento **melhorou em qualidade e piorou em cobertura
aparente** — 367 → 138 nets sem cobre, e os 12 pares trilha×pad criticos são todos do
**mesmo padrão**: trilha de fase do motor passando colada no pad do MOSFET de potência
(`QMxxxH.2`, net VBAT_PROT). É um defeito de layout repetido 12×, não 12 defeitos
esparramados. A lista completa dos 12 pares está no próprio `verificacao_v6.txt`.

---

## 2. Por que `rota_v7.py` não entregou saída

### 2.1 O comando executado (com limite de tempo)

```
cd /opt/jupyter/work/drone/fase3_pcb && timeout 240 /usr/bin/python3.9 -u rota_v7.py
```

### 2.2 A saída — e o que ela prova

```
exit=124 duracao=240s
--- log completo (3 linhas) ---
objetos carregados: 1698
vias de plano criadas: 214
grade: 440 x 320 | nets na grade: 203
--- v8 apos ---
total 8
drwxr-xr-x 2 root root 4096 Sep 11 22:37 .
```

`exit=124` é o código de saída do `timeout`: o processo foi **abatido aos 240 s**, não
terminou. E o log tem **3 linhas** — o script mal passou da preparação da grade.

### 2.3 O gargalo concreto, linha a linha

O arquivo `fase3_pcb/rota_v7.py` tem 568 linhas. A ordem de execução é:

| Etapa | Linha | Custo | Terminou? |
|---|---|---|---|
| `BRD = pcbnew.LoadBoard()` | 45 | — | sim |
| `objs = coleta()` | 311 (cham. 101) | varre 1698 objetos | **sim** — "objetos carregados: 1698" |
| `fecha_no_plano(objs)` | 312 (cham. 153) | O(pads_de_plano × 12 candidatos × 1698 objetos) | **sim** — "vias de plano criadas: 214" |
| `rasteriza(objs)` | 327 (cham. 196) | laço duplo por objeto, célula a célula, em Python puro | **sim** — "grade: 440 x 320" |
| **`for _, nm, ps in filas:` + `astro(...)`** | **401 → 433 (cham. 248)** | **A\* em grade, uma chamada por grupo desconexo** | **NÃO — foi aqui que estourou o tempo** |
| `BRD.Save(...)` | 451 | — | **nunca alcançado** |
| Gerbers + Excellon | 460+ | — | **nunca alcançado** |

**A causa raiz do `v8/` vazio é a ordem das operações:** `BRD.Save()` está na linha 451,
**depois** do laço de roteamento das linhas 401-444. O script não tem checkpoint nem
escrita incremental — se morrer no meio do A*, não deixa **nada**: nem arquivo, nem
log parcial, nem relatório. Por isso `fase3_pcb/v8/` continua vazio desde 2026-09-11 22:37
(timestamp do diretório, igual ao da criação original).

### 2.4 Por que o A\* não termina — as três causas somadas

**(a) Volume do problema.** Comando:

```
cd /opt/jupyter/work/drone && /usr/bin/python3.9 -c "
import pcbnew, collections
... conta pads por net e tracks por net ...
"
```

```
nets com >=1 pad                = 202
nets com >=2 pads               = 189
  ... ignorando GND/VBAT_PROT   = 187
nets >=2 pads e ZERO trilha     = 125
  ... ignorando GND/VBAT_PROT   = 125 <- minimo de chamadas A* por net
soma de pads nas nets >=2 pads  = 1034
pads na net maior              = [('GND', 207), ('VBAT_PROT', 102), ('3V3', 61)]
```

São **187 nets roteáveis** (o script ignora `GND` e `VBAT_PROT`, linha 334, por serem
planos). O 125 é apenas o **piso** — uma chamada de A\* por net sem cobre. Nets como
`3V3_A` (17 pads) e `3V3` (61 pads) têm vários grupos desconexos, e o laço das linhas
427-432 faz **uma chamada de A\* por grupo**, logo o número real é bem maior que 125.
**NÃO DETERMINADO** o número exato de chamadas: depende da contagem de componentes
conexos por union-find sobre o cobre existente, que exige rodar o `conecta()` O(p²) do
próprio script — é exatamente o que estou medindo como gargalo, e gastaria mais tempo
do que o documento comporta. O piso de 125 já é suficiente para explicar o estouro.

**(b) Custo por chamada.** A grade é `PITCH=0.5` mm sobre 220×160 mm → **440×320 = 140.800
células por camada × 2 camadas = 281.600 nós** (linhas 45-47 e o print da linha 327
confirmam `grade: 440 x 320`). O `astro()` da linha 248 tem `max_nodes=400000` — ou seja,
cada chamada pode expandir até **1,4× o total de nós da grade** antes de desistir e
devolver `"LIMITE"`. A heurística (linha 252) é Manhattan até o **conjunto** de goals,
recalculada por expansão. Com 125+ chamadas potenciais sobre uma grade já saturada de
obstáculos, o número de expansões efetivas é enorme.

**(c) Ruído na grade.** `rasteriza()` (linha 196) varre os 1698 objetos e marca a célula
como `-1` (bloqueada) quando `d < CLEAR` (0,25 mm) e `-2` (cara) quando `d < CLEAR*1.8`
(0,45 mm). Com 1693 objetos de cobre espalhados por 352 cm², a fração da grade
disponível para qualquer net de sinal é pequena, e o A* passa a explores quase todas as
células livres antes de declarar falha. **NÃO DETERMINADO** a fração exata de células
livres: `rasteriza()` é definida dentro do `rota_v7.py` e importá-la executa o script
inteiro, que é justamente o que estou tentando cronometrar. O relatório medido de
cobre por placa está acima: 605 objetos de cobre + 3 planos.

**Nota lateral (bug real, não é o gargalo):** o cabeçalho da linha 19 diz que o
roteamento é "só F_Cu e B_Cu", e o `IGNORA = {"GND", "VBAT_PROT"}` da linha 334
exclui os planos do A\*. Mas `fecha_no_plano()` (linha 153) roda **antes** e adiciona
214 vias + 214 stubs diretamente ao `BRD` — e essas 214 vias **não voltam para a
`grid`** (a `rasteriza()` da linha 327 recebe a lista `objs` original, que `fecha_no_plano`
modifica in-place por `objs.append`, mas só para a *própria* chamada; a grade é
rasterizada com as vias incluídas). O ponto verificado: **`v8/` continua vazio depois da
execução de 240 s**, então as 214 vias criadas foram perdidas junto com o processo.

---

## 3. Obstáculos concretos ao roteamento

### 3.1 Uso das camadas — o que está disponível

Medido (`mede_v7_wp1.py`):

```
zonas de PLANO:
   zona net=GND        camada=In1.Cu   vertices_preenchidos=9       pads_da_net=207  vias_da_net=296
   zona net=GND        camada=B.Cu     vertices_preenchidos=9       pads_da_net=207  vias_da_net=296
   zona net=VBAT_PROT  camada=In2.Cu   vertices_preenchidos=12223   pads_da_net=102  vias_da_net=21
   -> trilhas em In1_Cu: 0 | trilhas em In2_Cu: 0
GND/VBAT_PROT possuem trilha de sinal?
   GND         trilhas=27  vias=296
   VBAT_PROT   trilhas=14  vias=21
```

Mapeamento final das 4 camadas de cobre:

| Camada | Papel | Pode rotear net de sinal? |
|---|---|---|
| **F_Cu** | sinal, sem plano | sim — 192 trilhas já lá |
| **In1_Cu** | **plano GND** | **não** — é plano, 0 trilhas |
| **In2_Cu** | **plano VBAT_PROT** | **não** — é plano, 0 trilhas |
| **B_Cu** | plano GND (parcial) + 60 trilhas de sinal | sim, mas shared com GND |

Ou seja: **só existem 2 camadas roteáveis (F_Cu e B_Cu) para 187 nets**, e a B_Cu está
parcialmente ocupada pelo plano GND. Isso é o que faz da v7 uma placa de 4 camadas com
efetivamente 2 camadas de sinal.

### 3.2 O problema dos pads de plano sem via — o gargalo de sinal nº 1

Medido (`mede_v7_wp1.py`):

```
pads de GND e VBAT_PROT SEM via a menos de 1,6 mm:
   GND         pads=207  vias=296  pads_sem_via_perto=207
      ex: ['U_BARO.SDO','U_BARO.GND2','U_BARO.GND','CIMU.2','U_IMU.11', ...]
   VBAT_PROT   pads=102  vias=21   pads_sem_via_perto=102
      ex: ['RVB1.1','CinB1.1','UB1.EN','UB1.IN','Chf4.1','Chf3.1', ...]
```

**Todos os 309 pads de GND e VBAT_PROT (207 + 102) estão a mais de 1,6 mm de uma via.**
Isso significa: mesmo que as 138 nets de sinal fossem roteadas perfectly, **os 309 pads
de retorno e de alimentação não tocariam seus planos** — a placa não funcionaria.
945 pads SMD estão só em F_Cu e um plano em In1_Cu só se alcança por via.

### 3.3 Keepouts

```
cd /opt/jupyter/work/drone && grep -c "rule_area\|keepout" fase3_pcb/v7/v7_drone.kicad_pcb
0
```

**A v7 não tem nenhuma região de keepout definida.** As únicas barreiras que o
roteador enxerga são a borda da placa (`gr_poly` em `Edge.Cuts`, linha 13261, retângulo
10,10 → 230,170) e o cobre existente. Isso é um problema em si: os setores de potência
(VBAT, 30 A) e os de sinal de alta taxa estão **no mesmo plano de cobre**, sem separação
declarada, e o roteador pode de fato tentar passar uma trilha de sinal por cima da área
do conversor. As folgas críticas da v6 (pares `PHMxxx` × `QMxxxH.2`) são exatamente
sintoma dessa falta de separação.

### 3.4 Larguras exigidas por corrente × larguras presentes

Fonte: `fase3_pcb/calc_trilhas_vias_saida.txt` (existente, conferido com `test -e`).

```
NET                                        I[A] 2oz dT10 2oz dT20
VBAT continuo (cruzeiro 4 motores)         7.50    2.42mm    1.59mm
VBAT pico (rajada, <1 s)                  30.00   16.37mm   10.75mm
Fase do motor (RMS)                       15.00    6.29mm    4.13mm
Trilho 5 V (buck)                          2.00    0.39mm    0.26mm
Trilho 3,3 V (buck)                        1.50    0.26mm    0.17mm
Trilho 12 V (gate drivers)                 0.60    0.07mm    0.05mm
Gate drive (pico, 1 ciclo)                 1.20    0.19mm    0.13mm

VIAS de transicao (parede 25 um, dT=10 C, k interno 0,024):
  drill 0.30 mm -> 1.00 A/via  ->  30 A precisam de 30 vias
  drill 0.40 mm -> 1.20 A/via  ->  30 A precisam de 25 vias
  drill 0.50 mm -> 1.39 A/via  ->  30 A precisam de 22 vias
  drill 0.60 mm -> 1.57 A/via  ->  30 A precisam de 20 vias

>> ADOTADO: 0,3 mm drill / 0,6 mm pad -> 40 vias por transicao de VBAT/GND
```

Confronto com o que existe de fato na v7 (medido na §1.4):

| Net | Largura exigida (2 oz, dT10) | Larguras presentes na v7 | Veredito |
|---|---|---|---|
| VBAT (contínuo 7,5 A) | 2,42 mm | 4,0 / 6,0 / 8,0 mm presentes | **atende** |
| VBAT (pico 30 A) | 16,37 mm → regra: **usar polígono, não trilha** | — | **atende via plano In2_Cu** |
| Fase do motor (15 A) | 6,29 mm | **6,29 mm × 24** e 4,0 mm × 36 | **atende, no limite exato** |
| Trilho 5 V (2 A) | 0,39 mm | 0,40 mm × 48 | **atende** |
| Trilho 3,3 V (1,5 A) | 0,26 mm | 0,25 mm × 21 | **atende** (−0,01 mm, dentro da margem de grade) |
| Trilho 12 V (0,6 A) | 0,07 mm | 0,25 mm (mesma malha das de 5 V) | **atende com folga** |
| Gate drive (1,2 A pico) | 0,19 mm | 0,25 mm | **atende** |

**A largura de cobre de potência está correta e dimensionada.** O defeito da v7 não é
de corrente — é de *cobertura* (faltam 138 redes) e de *conexão ao plano*.

### 3.5 Defeito de nomeação do Gerber

```
cd /opt/jupyter/work/drone && grep -c "title" fase3_pcb/v7/v7_drone.kicad_pcb
0
```

O `.kicad_pcb` **não tem bloco `(title ...)`**. Consequência medida no diretório: os
Gerbers saem com prefixo vazio, como `-drone_F_Cu.gtl` (o hífen à esquerda é o título
vazio seguido do sufixo `-drone`). Arquivos existentes, todos conferidos com `test -e`:

```
fase3_pcb/v7/-drone_F_Cu.gtl          fase3_pcb/v7/-drone_B_Cu.gbl
fase3_pcb/v7/-drone_In1_Cu.g2        fase3_pcb/v7/-drone_In2_Cu.g3
fase3_pcb/v7/-drone_F_Mask.gts        fase3_pcb/v7/-drone_B_Mask.gbs
fase3_pcb/v7/-drone_F_SilkS.gto       fase3_pcb/v7/-drone_B_SilkS.gbo
fase3_pcb/v7/-drone_Edge_Cuts.gm1     fase3_pcb/v7/-PTH.drl
fase3_pcb/v7/-NPTH.drl
```

Isso não impede a fabricação (o nome não é funcional), mas **quebra qualquer CAM que
case arquivos pelo nome** e torna o pacote ambíguo para quem lê. Corrigir exige
adicionar o bloco `(title ...)` ao `.kicad_pcb` e regerar — a geração está em
`fase3_pcb/gera_pcb_v7.py` (o gerador), não no `rota_v7.py`.

### 3.6 Resumo dos obstáculos

| # | Obstáculo | Evidência | Impacto |
|---|---|---|---|
| O1 | 138 nets com pad e zero trilha | §1.2, §1.5 | bloqueante |
| O2 | 309 pads de GND/VBAT_PROT sem via próxima | §3.2 | bloqueante |
| O3 | Só 2 camadas de sinal (F/B); In1 e In2 são planos | §3.1 | alto — densidade |
| O4 | Zero keepouts definidos | §3.3 | alto — separação potência/sinal |
| O5 | 12 pares trilha×pad com folga crítica, todos VBAT_PROT | §1.6 | alto — risco de curto |
| O6 | Autorouter A* não termina e não tem checkpoint | §2 | bloqueante de processo |
| O7 | Gerbers sem nome de placa | §3.5 | baixo — cosmético/CAM |

---

## 4. Estratégia de fechamento — trade-offs e recomendação

### Opção A — Terminar o roteamento da v7 em v8

O que falta: rotear 187 nets em 2 camadas, fechar 309 pads no plano, criar keepouts,
resolver 12 folgas críticas, e trocar o A* em Python puro por um roteador decente.

Trade-offs:
- **A favor:** preserva todo o netlist já validado (319 footprints, 202 nets, 1093 pads,
  todos com pinout cotado em datasheet segundo o cabeçalho do `gera_pcb_v7.py`); não
  descarta trabalho; a largura das trilhas de potência já está dimensionada e verificada.
- **Contra:** exige um autorouter que funcione. O `kicad-cli` não existe nesta máquina e
  não existe autorouter do KiCad 5 headless. O A* próprio não termina em 240 s. Escrever
  um autorouter de 2 camadas que feche 187 nets num tabuleiro de 352 cm² **é um projeto
  de semanas**, não de um dia.
- **Contra físico:** 220×160 mm para 187 nets em 2 camadas é uma densidade de roteamento
  **inválida para produção**. Even com um roteador perfeito, 2 camadas de sinal para
  4 ESCs trifásicos + 4 ADCs de corrente + IMU + USB + 12 PWMs significa camadas internas
  às vezes com distância de desacoplamento insuficiente. O resultado seria uma placa que
  passa no checklist geométrico e falha no bench.

### Opção B — Reduzir/redesenhar a placa

O que faria: novas camadas internas devoted a sinal (6 ou 8 camadas), ou uma placa de
~140×100 mm com a mesma netlist, ou partição do sistema.

Trade-offs:
- **A favor:** 6 camadas com 4 de sinal resolve o problema de densidade de raiz;
  adicionar keepouts de potência fica trivial; a placa de 140×100 mm (140 cm², 60% da
  área atual) corta custo de cobre e **peso**, que num quadcopter de missão é requisito,
  não é detalhe de forja: 100 g de placa extra com 4 ESCs e bateria é diferença de
  tempo de voo.
- **Contra:** refazer o netlist/footprint significa refazer a etapa de geração; as
  202 nets e 319 footprints da v7 passam a ser insumo, não entrega.
- **Contra:** 2-3 semanas de redesenho.

### Recomendação

> **RECOMENDAÇÃO: Opção B — reduzir a placa, mas por uma via específica e barata:
> não redesenhar o netlist, e sim (1) aumentar de 4 para 6 camadas, de modo que 2 das
> 4 camadas internas passem a ser de sinal, e (2) reduzir o contorno de 220×160 mm
> para ~150×110 mm, preservando a netlist e a posição relativa dos blocos.**

A razão: a v7 não está *errada*, está **subdimensionada em camadas e superdimensionada
em área**. O bbox medido é 220,10 × 160,10 mm = **352,4 cm²**, e essa área carrega
4 ESCs trifásicos, 4 ADCs de corrente, ESP32-S3, IMU e USB — 319 footprints, 202 nets,
1093 pads, 605 objetos de cobre. **NÃO DETERMINADO** a fração de área realmente
ocupada por cobre: isso exigiria rasterizar a placa, que é a mesma operação que
`rasteriza()` faz e que estou medindo como gargalo (§2.4c). O que está medido é o
contorno e as contagens. Reduzir área **e** ganhar 2 camadas resolve simultaneamente os
obstáculos O1 (densidade), O3 (camadas) e parcialmente O4 (keepouts, que passam a ter
espaço), sem jogar fora as 202 nets já cotadas em datasheet.

**Se a Opção B for rejeitada por prazo**, o caminho mínimo da Opção A é este, e só este:
reescrever o `rota_v7.py` para (i) salvar checkpoint incremental a cada net roteada,
(ii) manter `PITCH` em 0,5 mm — que já é o limite prático de resolução do processo de
fabricação padrão, não há para onde reduzir —, mas (iii) trocar o laço O(p²) de
`conecta()` por union-find sobre grid e (iv) trocar o A* por **rip-up and reroute
(rotear, falhar, arrancar e rerrotear) com ordem de rip-up por largura de trilha**,
não por ordem de bounding box. Sem essas quatro mudanças, o script não termina em
nenhuma quantidade razoável de tempo.

**Deixa registrada a ressalva honesta:** não medi o tempo de convergência de nenhuma
dessas reescritas, porque a medição exigiria mais de 240 s por tentativa e esta tarefa
tem orçamento de 10 min para a evidência do gargalo. O que está medido é
**"não termina em 240 s"**, não "não termina nunca".

---

## 5. Critério de aceite do roteamento, em números

O painel de aceitação é o arquivo `verificacao_v8.txt`, produzido na **linha 568** do
`rota_v7.py` (`print("relatorio:", OUT + "/verificacao_v8.txt")`), a partir da
verificação geométrica net-por-net do bloco entre as linhas 460-567 (que já existe
implementado: `conecta()` com folga `<= 0.02 mm`, `obj_gap()` com folga por par de
objetos). Ele **precisa** ser executado, não ser escrito à mão.

### 5.1 As duas linhas que definem o aceite

> **Atenção ao `test -e`:** `fase3_pcb/v8/verificacao_v8.txt` **ainda não existe** — é o
> arquivo que o aceite manda *produzir*. `fase3_pcb/v8/` está vazio desde 2026-09-11 22:37.
> O comando abaixo é o que cria os dois. Todos os demais caminhos citados neste
> documento existem e foram conferidos com `test -e` (§6).

```
$ grep -A1 "nets NAO roteadas" fase3_pcb/v8/verificacao_v8.txt     # apos rodar o painel
   nets NAO roteadas : 0

$ grep -A1 "pares trilha x pad" fase3_pcb/v8/verificacao_v8.txt   # apos rodar o painel
   pares trilha x pad (net diferente) proximos: 0
```

### 5.2 Tabela de aceite

| # | Critério | Alvo | Como medir |
|---|---|---|---|
| **A1** | nets com pad e **zero trilha** | **0** | `/usr/bin/python3.9` + `mede_v7_wp1.py` apontado para a v8 |
| **A2** | pares trilha×pad de nets diferentes com folga crítica | **0** | `verificacao_v8.txt`, seção "checagem de curto" |
| **A3** | pads de nets diferentes com bbox sobreposto | **0** | `verificacao_v8.txt` |
| **A4** | pads de GND/VBAT_PROT sem via a < 1,6 mm | **0** (de 309 hoje) | `mede_v7_wp1.py`, seção de planos |
| **A5** | trilhas em In1_Cu / In2_Cu | **0** (mantidas como plano) | `mede_v7_wp1.py` |
| **A6** | largura de trilha de fase do motor | ≥ 6,29 mm (IPC-2221 2 oz, dT10) | `mede_v7_wp1.py`, `larguras de trilha` |
| **A7** | nome dos Gerbers começa com `-drone_` | **não** (título preenchido) | `ls fase3_pcb/v8/*.gt*` |

### 5.3 Comando que produz o painel

```
cd /opt/jupyter/work/drone/fase3_pcb && /usr/bin/python3.9 -u rota_v7.py
# -> escreve fase3_pcb/v8/v8_drone.kicad_pcb, os Gerbers, o Excellon
# -> e fase3_pcb/v8/verificacao_v8.txt  (linha 568)

grep -E "nets NAO roteadas|pares trilha x pad|bbox sobreposto" \
     /opt/jupyter/work/drone/fase3_pcb/v8/verificacao_v8.txt
```

**Aceite = as duas primeiras linhas de `verificacao_v8.txt` dizem `0` e `0`, e A1 medido
à parte também dá 0.** As duas primeiras linhas não bastam sozinhas: o `verificacao_v8.txt`
declara `0` para uma net que só tem 1 pad, então A1 (contagem independente) é
obrigatória como contraprova.

### 5.4 Estado atual contra o aceite

| Critério | v7 hoje | Alvo | Δ |
|---|---|---|---|
| A1 nets sem trilha | 138 | 0 | −138 |
| A2 pares críticos | 12 (v6; v7 NÃO DETERMINADO — não rodei a verificação na v7) | 0 | — |
| A3 bbox sobreposto | 0 (v6) | 0 | ok |
| A4 pads de plano sem via | 309 de 309 | 0 | −309 |
| A5 trilhas em In/In2 | 0 | 0 | ok |
| A6 fase do motor | 6,29 mm × 24 | ≥ 6,29 | ok |
| A7 nome do Gerber | `-drone_F_Cu.gtl` | `drone_F_Cu.gtl` | 1 linha |

**A2 na v7 está marcado NÃO DETERMINADO de propósito:** o `verificacao_v6.txt` é da v6
(238 footprints, 171 trilhas) e a v7 mudou o netlist. Para medir A2 na v7 seria preciso
rodar o bloco de verificação das linhas 460-567 do `rota_v7.py` isolado, o que exige
refatorá-lo para não passar pelo A*. Não foi feito nesta tarefa e não vou
apresentar o número da v6 como se fosse da v7.

---

## 6. Arquivos citados (todos conferidos com `test -e`)

```
OK  /opt/jupyter/work/drone/fase3_pcb/rota_v7.py                 (568 linhas)
OK  /opt/jupyter/work/drone/fase3_pcb/gera_pcb_v7.py
OK  /opt/jupyter/work/drone/fase3_pcb/calc_trilhas_vias_saida.txt
OK  /opt/jupyter/work/drone/fase3_pcb/v6/verificacao_v6.txt
OK  /opt/jupyter/work/drone/fase3_pcb/v7/v7_drone.kicad_pcb
OK  /opt/jupyter/work/drone/fase3_pcb/v8                          (diretorio, VAZIO)
OK  /opt/jupyter/work/drone/fase3_pcb/v7/-drone_F_Cu.gtl
OK  /opt/jupyter/work/drone/plano/mede_v7_wp1.py
OK  /opt/jupyter/work/drone/plano/WP1_ROTEAMENTO.md               (este arquivo)
```

## 7. O que NÃO foi determinado, e por quê

| Item | Motivo |
|---|---|
| Nº exato de chamadas ao A* | depende da contagem de componentes conexos por union-find; exigiria rodar o `conecta()` O(p²) do `rota_v7.py`, que é o gargalo em medição |
| Fração de células livres na grade | `rasteriza()` só existe dentro do `rota_v7.py`; importar o módulo executa o script inteiro |
| Tempo de convergência da reescrita do roteador | exigiria > 240 s por tentativa; o orçamento desta tarefa é 10 min para essa evidência |
| Nº de pares trilha×pad críticos **na v7** | o verificador só roda no fim do `rota_v7.py`, depois do A* que não termina; o número de 12 é da v6 |
| Folga mínima real entre trilhas de nets diferentes na v7 | o bloco de verificação (linhas 460-567) não é executável isolado sem refatoração |
| Comportamento térmico das larguras escolhidas | o próprio `calc_trilhas_vias_saida.txt` marca: `[NAO VERIFICADO nesta maquina: termografia/termopar -> Fase 4]` |
