# Reversão de premissas — v5 (gate drive com Qg real)

**Escopo desta versão:** a premissa **P-06** (Qg = 40 nC) e a premissa **P-11** (quiescência de
2,5 mA por driver) estavam erradas. Este documento reabre a tabela de premissas da Fase 0,
marca as duas correções com a página exata de PDF de onde veio cada número, e lista o que
cada correção **invalida**. Nenhuma premissa além de P-06 e P-11 mudou de valor: as outras
treze continuam exatamente como estavam, com a mesma fonte e o mesmo status.

**Nada foi editado.** `dimensionamento_fase0.py`, `verifica_limites_entrada_v4.py`,
`FASE0_ESPECIFICACAO.md` e `plano/` foram lidos e executados em modo leitura. Os três
arquivos desta entrega são novos:

- `fase0_especificacao/redimensionamento_gate_v5.py` — o redimensionamento
- `fase0_especificacao/redimensionamento_gate_v5_saida.txt` — a saída real dele, 500 linhas
- `fase0_especificacao/REVERSAO_PREMISSAS_v5.md` — este arquivo

**Extratos usados para a verificação.** Ambos foram extraídos com
`pdftotext -layout` e a página citada é a do PDF (o rodapé `Final Data Sheet N` confere
com o índice da página do PDF, e o `www.irf.com N` do IR2104 também):

```
pdftotext -layout datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf /tmp/ipb017.txt
pdftotext -layout datasheets/ir2104_infineon_datasheet.pdf /tmp/ir2104.txt
```

| Fonte | Arquivo | Páginas do PDF | Rodapé conferido |
|---|---|---|---|
| MOSFET de referência | `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` | 1, 4 | `Final Data Sheet 1` e `Final Data Sheet 4` |
| Gate driver | `datasheets/ir2104_infineon_datasheet.pdf` | 1, 3 | `www.irf.com 1` e `3` |

Marcadores usados nas tabelas:

| Marca | Significado |
|---|---|
| **[DS]** | linha literal do PDF, com arquivo e página |
| **[MEDIDO]** | conta executada por `redimensionamento_gate_v5.py` agora |
| **[PREMISSA]** | continua sem fonte, como estava |
| **[N/D offline]** | continua sem fonte **e** sem meio de obter a fonte nesta máquina |
| **[EST]** | estimativa declarada do redator, com a conta que a sustenta |

---

## 1. Tabela de premissas P-01…P-15

| # | Premissa | Valor original | Valor corrigido | Fonte | Status | O que a correção invalida |
|---|---|---|---|---|---|---|
| **P-01** | Motor | 2207, 1750 KV, hélice 5"/3 pás | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 82; o usuário nunca forneceu curva real | **[PREMISSA]** | nada nesta versão. Continua pendente de dados que o PROJETO precisa pedir ao usuário — não é documento que falta extrair |
| **P-02** | Bateria | LiPo 6S: 25,2 V max / 22,2 V nom / 19,8 V min | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 83 | **[PREMISSA]** | nada nesta versão |
| **P-03** | Corrente de pico por motor | 30 A | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 84 | **[PREMISSA]** | nada nesta versão. Mas é a entrada do pior caso de §4 do `verifica_limites_entrada_v4.py`, e com Qg real a perda de comutação escala com ela |
| **P-04** | Corrente contínua por motor | 15 A | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 85 | **[PREMISSA]** | nada nesta versão |
| **P-05** | Rds(on) do MOSFET | 2,0 mΩ @ 10 V | **2,0 mΩ — MANTIDA** | `FASE0_ESPECIFICACAO.md` linha 86. Para o FET de *referência*: 1,5/1,7 mΩ @ VGS=10 V, ID=100 A **[DS IPB017N10N5 p. 4, Table 4]**; 1,7/2,2 mΩ @ VGS=6 V | **[PREMISSA] mantida por decisão** | Nada é invalidado, e é a decisão certa: 2,0 mΩ é mais pessimista que os 1,7 mΩ de máximo do IPB017N10N5, então a conta térmica não melhora por causa do datasheet novo. **Ressalva registrada:** o FET de referência é um 100 V, e a placa é 6S (25,2 V) — a escolha de classe de tensão continua em aberto |
| **P-06** | Qg total do MOSFET | **40 nC** | **168 nC (typ) / 210 nC (max)** | `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` **p. 4, Table 6 "Gate charge characteristics"**, linha `Gate charge total  Qg — 168 210 nC VDD=50V, ID=100A, VGS=0 to 10V`. Confirmado também na **p. 1**, caixa de highlights: `QG(0V..10V) 168 nC` | **[DS] — ERRADA por 4,20× (typ) e 5,25× (max)** | **§2 do `dimensionamento_fase0.py` inteiro**: corrente de pico de gate (1,2 A), tempo de subida (33,33 ns), Cboot (800 nF), queda de bootstrap (0,040 V) e corrente do trilho de 12 V (19,2 mA). **§3 do `verifica_limites_entrada_v4.py`**: a perda de comutação de 0,133 W/FET. **Dead-time**: os 518,750 ns do RTL. **Especificação de compra** da linha 249 de `FASE0_ESPECIFICACAO.md` (`Qg ≤ 60 nC`), que **rejeita** o próprio componente de referência. Detalhe em §2 deste documento |
| **P-07** | Frequência de PWM | 20 kHz | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 88; implementada como `20 kHz` no PWM de 12 canais | **[MEDIDO em RTL]** | nada nesta versão. Mas note: é ela que transforma 1,29 µs de tempo de comutação em 2,58 % do período |
| **P-08** | fsw dos bucks | 500 kHz | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 89 | **[PREMISSA]** | nada nesta versão |
| **P-09** | Shunt de fase | 0,5 mΩ (2512, 2 W) | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 90 | **[PREMISSA]** | nada nesta versão |
| **P-10** | Ganho do amp de corrente | 50 V/V | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 91 | **[PREMISSA]** | nada nesta versão |
| **P-11** | Quiescência por gate driver | **2,5 mA** | **180 µA (typ) / 325 µA (max)** | `datasheets/ir2104_infineon_datasheet.pdf` **p. 3, "Static Electrical Characteristics"**: `IQBS — 30 55 µA` e `IQCC — 150 270 µA`. Soma **[MEDIDO]**: 180 µA typ, 325 µA max | **[DS] — ERRADA por 13,9× (era pessimista, ou seja, folga)** | Nada é invalidado no sentido de risco: a premissa era **otimista demais em consumo**, o que dava folga. Mas três números mudam: a corrente de quiescência do trilho de 12 V (30 mA → 2,16 mA), o total de dissipation no driver e o orçamento de corrente do buck de 12 V. Detalhe em §3 |
| **P-12** | ADC | 12 bits, FS 3,300 V | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 93 | **[MEDIDO no ESP32-S3]** | nada nesta versão |
| **P-13** | Referência do ADC | 3,300 V | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 93 | **[PREMISSA]** | nada nesta versão |
| **P-14** | Rendimento de hélice | 4,5 g/W, AUW 750 g | *inalterado* | `FASE0_ESPECIFICACAO.md` linha 94 | **[PREMISSA]** | nada nesta versão |
| **P-15** | Endereço de projeto | **[N/D offline]** para Ciss, ESR, ESL, corrente nominal do XT60 e Vf do diodo | **[N/D offline] — MANTIDO** | Ver §4 deste documento | **[N/D offline]** | Nada foi resolvido, e é honesto dizer por quê: o P-15 é uma **lista de componentes não escolhidos**, não uma lacuna de extração. Ciss, ESR e ESL são de três componentes diferentes (MOSFET, capacitor eletrolítico, indutor); a corrente do XT60 é do conector; o Vf é do diodo de bootstrap. Abrir o PDF do IPB017N10N5 resolve **um** deles e só para o MOSFET de referência |

### O que continua `[N/D offline]` e por quê

| Item | Motivo |
|---|---|
| **ESR** dos capacitores eletrolíticos do banco de entrada | O `verifica_limites_entrada_v4.py` §1 varre 8/10/12/15 mΩ como cenário, mas o valor real depende do capacitor **que ainda não foi escolhido** (linha 267 de `FASE0_ESPECIFICACAO.md` diz "4× 470 µF/35 V low-ESR (polímero)", sem parte). Nenhum PDF de capacitor está em `datasheets/`. O ripple do barramento **não** pode ser fechado sem isso |
| **ESL** do mesmo banco e das trilhas de potência | Depende do layout da Fase 3 e do encapsulamento do capacitor. Não é número de catálogo, é número de geometria |
| **Corrente nominal do XT60** | `FASE0_ESPECIFICACAO.md` linha 241 cita XT90, o `dimensionamento_fase0.py` §9 calcula `VBAT: motores 120 A pico`. Nenhum datasheet de conector está em `datasheets/`. Com 120 A de pico, a corrente nominal do conector **é um limite de projeto, não um detalhe** — mas a fonte não existe nesta máquina |
| **Vf do diodo de bootstrap** | `FASE0_ESPECIFICACAO.md` linha 252 especifica `D_SOD-123` "diodo rápido" sem parte. `dimensionamento_fase0.py` §1 adota 0,5 V como **estimativa** ao comparar Schottky × P-FET. Com Qg = 168 nC o diodo de bootstrap conduz mais carga por ciclo, então o Vf entra no balanço do bootstrap — mas o número continua sem fonte |
| **Ciss** | Ver nota de precisão abaixo |

**Nota de precisão sobre Ciss — onde eu discordo da formulação `[N/D offline]`.** O P-15
agrupa Ciss com ESR, ESL, corrente de conector e Vf. Para o **MOSFET de referência** o Ciss
**existe e está no PDF**:

| Parâmetro | Valor | Fonte |
|---|---|---|
| Ciss | 12 000 pF (typ) / 15 600 pF (max), VGS=0 V, VDS=50 V, f=1 MHz | **[DS] IPB017N10N5 p. 4, Table 5 "Dynamic characteristics"** |
| Coss | 1 810 pF (typ) / 2 353 pF (max) | **[DS] IPB017N10N5 p. 4, Table 5** |
| Crss | 80 pF (typ) / 140 pF (max) | **[DS] IPB017N10N5 p. 4, Table 5** |

O que permanece `[N/D offline]` é o Ciss **do MOSFET que for efetivamente comprado**, que
pode ser um 40 V com Ciss três vezes maior. O P-15 continua `[N/D offline]` no sentido
correto — a premissa do *projeto* não foi fechada — mas registrar "Ciss é desconhecido"
depois de extraí-lo do PDF seria False. O `redimensionamento_gate_v5.py` §3 usa o Ciss
typ (12 nF) para mostrar que a corrente reativa no nó durante a comutação é **1,71×** a
corrente de gate, subindo para **1,93×** com o Ciss max **[MEDIDO]**.

---

## 2. P-06 em detalhe: o que 168 nC invalida

Números todos de `redimensionamento_gate_v5_saida.txt`, gerado por execução real.

### 2.1 Tempo de comutação de gate

`t = Qg / I_gate`, com as duas correntes que o IR2104 declara na **p. 1** do Product Summary:
`IO+/- 130 mA / 270 mA` **[DS IR2104 p. 1]**.

| Qg | I = 130 mA (fonte) | I = 270 mA (drain) | Esperado | Erro |
|---|---|---|---|---|
| 168 nC (typ) | **1,2923 µs** = 1292,3 ns | **0,6222 µs** = 622,2 ns | 0,05 µs (alvo de projeto) | **+2484,62 %** |
| 210 nC (max) | 1,6154 µs | 0,7778 µs | 0,05 µs | +3129,58 % |

O `dimensionamento_fase0.py` §2 imprimiu `Tempo de subida estimado t_r = Qg/Ipk = 33.33 ns
com Rg=10 ohm`, porque supôs `Ipk = Vgs/Rg = 10/10 = 1,2 A`. Esse 1,2 A é **9,2×** a corrente
que o driver declara **[MEDIDO]**. A conta não fechava porque a premissa do driver era
otimista, não porque o Rg fosse pequeno.

### 2.2 A contradição que fecha o argumento

O rise time do próprio datasheet resolve o impasse sem modelo nenhum:

| Item | Valor | Fonte |
|---|---|---|
| Qg | 168 nC | **[DS] IPB017N10N5 p. 4, Table 6** |
| tr | 23 ns, medido com Rg,ext = 1,6 Ω | **[DS] IPB017N10N5 p. 4, Table 5** |
| Corrente média implícita = Qg/tr | **7,30 A** | **[MEDIDO]** |
| IO+ que o IR2104 entrega | 0,130 A | **[DS] IR2104 p. 1** |
| Razão | **56,2×** | **[MEDIDO]** |

As duas linhas estão em **páginas diferentes do mesmo par de PDFs**, e o resultado não
depende de nenhum modelo de circuito. O IPB017N10N5, como o Infineon o mediu, **não é
comutável por um IR2104** sem pre-driver.

### 2.3 Slew e corrente de pico

`dV/dt = ΔV / t` com ΔV = 10 V (a mesma excursão que o datasheet usa para characterizing Qg,
`VGS=0 to 10V` **[DS] p. 4, Table 6**) **[MEDIDO]**:

| Caso | dV/dt |
|---|---|
| Qg typ, 130 mA | 0,00774 V/ns |
| Qg typ, 270 mA | 0,01607 V/ns |
| Qg max, 130 mA | 0,00619 V/ns |
| Qg max, 270 mA | 0,01286 V/ns |
| implicito no tr do DS (10 V / 23 ns) | 0,4348 V/ns |

Corrente de pico para comutar em **25 ns** (0,05 % do período de 20 kHz; alvo de projeto
**[EST]**): `I = Qg/t` = **6,72 A** (Qg typ) e **8,40 A** (Qg max) **[MEDIDO]**. Isso é
**51,7×** o IO+ e **24,9×** o IO−. A premissa de 40 nC exigiria 1,60 A — e é por isso que o
projeto original "fechava": ele nunca viu o número 168.

**E o Rg de 10 Ω não conserta isso.** `Rg_total = 10 + 1,3` (RG interno do FET, 1,3 Ω typ,
**[DS] p. 4, Table 4**) = 11,3 Ω. Corrente que o Rg pediria com um driver ideal:
10/11,3 = 0,885 A **[MEDIDO]**. O Rg só limitaria a corrente se fosse **maior** que 76,9 Ω
(10 V / 130 mA), não menor. Para os 25 ns de alvo seria preciso `Rg_total < 1,49 Ω`, o que
**viola** o amortecimento já especificado (`Rg ≥ 6,3 Ω` para `Z0 = 3,16 Ω`, §7 de
`FASE0_ESPECIFICACAO.md` e linha de saída do `verifica_limites_entrada_v4.py` §3). **Duas
exigências incompatíveis, um só resistor** **[MEDIDO]**.

### 2.4 Perda de comutação

`P = Qg × Vgs × f` com Qg = 168 nC, Vgs = 10 V, f = 20 kHz:

| Qg | P por FET | No banco (24 FETs) | Contra a premissa |
|---|---|---|---|
| 40 nC (P-06 original) | 8,00 mW | 0,192 W | — |
| **168 nC (typ)** | **33,60 mW** | **0,806 W** | **+320,00 % (4,20×)** |
| 210 nC (max) | 42,00 mW | 1,008 W | +425,00 % (5,25×) |

Erro absoluto de orçamento: **614 mW** no banco (typ), 816 mW (max) **[MEDIDO]**.

**Ressalva metodológica, e ela importa.** `Qg × Vgs × f` é a **potência de porta** — a
energia que o sinal de controle entrega e que o resistor de gate dissipa. **Não** é a perda
dentro do MOSFET. A perda no MOSFET é `E_off × f`, e o IPB017N10N5 **não publica E_on/E_off**
nas Tabelas 4 a 7 (tem tr, tf, td(on), td(off) e figuras, não tabela de energia de
comutação) **[MEDIDO]**. Logo: **perda real de comutação = NÃO DETERMINADA** nesta máquina.
Com o modelo clássico `E_off ≈ ½·Vds·I·t_r` **[EST]**, e o `t_r` que o IR2104 realmente
consegue:

| t_r usado | E_off a 25,2 V / 30 A | P/FET | Banco |
|---|---|---|---|
| 23 ns (o do datasheet) | 8,69 µJ | 0,174 W | 4,17 W |
| 1292 ns (o que o IR2104 leva) | 488,5 µJ | 9,77 W | 234 W |

O modelo é grosseiro, mas a **razão de t_r (56×) é real** e independe dele. Com
`Rth = 60 °C/W` e `Ta = 25 °C` — os mesmos do `verifica_limites_entrada_v4.py` §3 — isso
daria `Tj = 611 °C` contra os 60,0 °C que o v4 reportou **[EST]**.

### 2.5 Dissipação e corrente do gate driver

`E/FET = Qg × Vtrilho` com Vtrilho = 12 V (valor do layout, `fase3_pcb/gera_pcb_v7.py`
linha 239) — **atenção**: o Qg de 168 nC foi medido até 10 V, então a 12 V o Qg efetivo é
maior e **NÃO DETERMINADO**. Estes números são um **lower bound** **[MEDIDO]**.

| | E/FET | E/driver (2 FETs) | P/driver a 20 kHz | 12 drivers |
|---|---|---|---|---|
| Qg typ | 2,02 µJ | 4,03 µJ | 80,6 mW | 967,7 mW |
| Qg max | 2,52 µJ | 5,04 µJ | 100,8 mW | 1209,6 mW |

Reparto por driver: **82,8 mW** (Qg typ) e **104,7 mW** (Qg max), somando o quiescente de
12 V × 180/325 µA **[MEDIDO]**.

Corrente no trilho de 12 V: `12 × 180 µA + 24 × Qg × 20 kHz` = **82,8 mA** (typ) /
**104,7 mA** (max) **[MEDIDO]**, contra os 49,2 mA que a Fase 0 orçou. **O buck de 12 V /
0,60 A continua dimensionando certo**: 104,7 mA é 17,5 % do que ele entrega, folga de 5,7×.
O trilho **não** é o item que quebra **[MEDIDO]**.

### 2.6 Dead-time

`[MEDIDO em fase2_simulacao/verilog/RELATORIO_VERILOG.md §2 e plano/WP4_FIRMWARE.md]`
dead-time do RTL do MCPWM = **518,750 ns**. `[DS IR2104 p. 3, "Dynamic Electrical
Characteristics", símbolo DT]` dead-time interno = **400 / 520 / 650 ns** (min/typ/max,
caracterizado a VBIAS = 15 V, CL = 1000 pF, TA = 25 °C).

O dead-time tem de ser ≥ o tempo de o gate do FET que está **desligando** ser descarregado.
O turn-off sai pelo lado **drain**, então usa-se 270 mA:

| Caso | Necessário | Contra 518,750 ns | Margem |
|---|---|---|---|
| Qg typ, 270 mA (turn-off) | 622,2 ns | **+19,95 %** | estoura em 103,5 ns |
| Qg typ, 130 mA (turn-on, pior) | **1292,3 ns** | **+149,12 %** | estoura em 773,5 ns |
| Qg max, 270 mA | 777,8 ns | +49,93 % | estoura em 259,0 ns |
| Qg max, 130 mA (pior absoluto) | 1615,4 ns | **+211,40 %** | estoura em 1096,6 ns |

O número de **1,29 µs** citado na missão é exatamente `168 nC / 130 mA` **[MEDIDO]**.

Os dois dead-times **se somam** — o do IR2104 é interno e fixo, o firmware não o programa.
Pior caso: 650 + 518,750 = **1168,8 ns** de janela, contra 1292,3 ns necessários para o
turn-on a 130 mA (1,11×) **[MEDIDO]**.

Custo do dead-time longo: **1,04 % do período** e **2,08 % do tempo de ON** a 518,750 ns;
subir para 1615 ns custa **4,39 % de duty** **[MEDIDO]**. Isso é aceitável e não é o
problema. O problema é a condução cruzada.

**E o Qg de 210 nC não é um limite garantido.** O rodapé da Table 6 diz, nas notas 1 e 2:
`Defined by design. Not subject to production test` **[DS] IPB017N10N5 p. 4]**. Nem o 210 nC
nem o 168 nC são garantidos em produção. **O orçamento de dead-time não fecha com nenhum dos
dois** — tem de ser medido em bancada.

### 2.7 Quantas vezes o Qg real excede o que o IR2104 entrega

Pergunta operacional: `Q_entregue = I_driver × t_janela`, e o excesso é
`Qg_real / Q_entregue` **[MEDIDO]**:

| Janela | 130 mA | 270 mA |
|---|---|---|
| RTL 518,750 ns | entrega 67,4 nC → **2,49×** | entrega 140,1 nC → **1,20×** |
| IR2104 interno typ 520 ns | 67,6 nC → 2,49× | 140,4 nC → 1,20× |
| IR2104 interno max 650 ns | 84,5 nC → 1,99× | 175,5 nC → 0,96× |
| **somados, typ (1038,8 ns)** | 135,0 nC → **1,24×** | 280,5 nC → 0,60× |
| **somados, max (1168,8 ns)** | 151,9 nC → **1,11×** | 315,6 nC → 0,53× |

Leitura honesta, e é esta: **o IR2104 é marginal, não hopeless.** No lado de **drain** a
conta fecha na janela somada com folga (0,53× a 270 mA); no lado de **fonte** não fecha em
nenhuma janela (1,11× no melhor caso). Ou seja: o turn-off funciona, o turn-on falha à
corrente nominal. Isso não fecha especificação nenhuma — mas o diagnóstico é mais preciso
que "o driver não dá conta", e ele aponta a correção certa (pre-driver, ou capacitor local
de gate, ou MOSFET com Qg menor), em vez de uma troca cega.

### 2.8 Consequência prática

1. **O gate não sobe em tempo.** Em 518,750 ns a 130 mA o gate carrega 67 nC de 168 nC =
   40 %. Se o comando dura 518,750 ns, o FET chega a **Vgs = 4,0 V**. O datasheet diz
   `VGS(th) = 2,2 / 3,0 / 3,8 V` (min/typ/max) e `Vplateau = 4,4 V`
   **[DS IPB017N10N5 p. 4, Tables 4 e 6]**. Ou seja: **acima** do VGS(th) máximo de 3,8 V,
   **abaixo** do patamar, e muito abaixo dos 10 V onde Rds(on) foi medido **[MEDIDO]**.

2. **O FET passa a dissipar em estado intermediário.** Com Vgs no meio da curva o ponto de
   operação sai da região ôhmica: a potência passa a ser `Vds × I_load`, não `I²·Rds(on)`.
   Teto do modelo `Vds × I` com 25,2 V e 30 A (P-03): **756 W** num dispositivo durante
   773,5 ns, o que a 20 kHz dá 11,7 W médios por FET **[EST]**, contra os 450 mW de regime
   ôhmico do mesmo FET a 30 A de pico (P-05, `(30/2)² × 2,0 mΩ`) — **26×** maior **[MEDIDO]**.
   O valor real depende da curva de transferência, que o datasheet dá como **figura** (p. 7),
   não como tabela: **NÃO DETERMINADO**. O que é sólido é a ordem de grandeza.

3. **O duty efetivo cai.** 1292,3 ns de subida contra 50 µs de período: 2,58 % do período
   fora de regime após o comando, mais 773,5 ns de dead-time além dos 518,750 ns já
   orçados — 3,09 % de duty adicional nos 50 µs de ON **[MEDIDO]**.

4. **O dano é cumulativo.** A perda intermediária ocorre a 960 000 vezes por segundo no banco
   (24 FETs × 2 × 20 kHz), sempre no mesmo ponto da curva térmica **[MEDIDO]**. Não é um
   evento raro que a média térmica esconda.

---

## 3. P-11 em detalhe

| | Original | typ | max |
|---|---|---|---|
| IQCC | — | 150 µA | 270 µA |
| IQBS | — | 30 µA | 55 µA |
| **Soma** | 2 500 µA (P-11) | **180 µA** | **325 µA** |
| Erro | — | **−92,80 %** | **−87,00 %** |

Fonte: **[DS] IR2104 p. 3, "Static Electrical Characteristics"**, linhas `IQBS` e `IQCC`
dentro da tabela. **[MEDIDO]** a soma.

Direção do erro: a premissa era **pessimista** (7,7× acima do máximo real), então **não
invalida nada** — dá folga onde se pensava que havia consumo. O que muda:

| Item | Com P-11 (2,5 mA) | Com Qg real + P-11 corrigida |
|---|---|---|
| Quiescência dos 12 drivers | 30 mA | 2,16 mA (typ) / 3,90 mA (max) |
| Carga de gate no trilho | 19,2 mA | 80,64 mA (typ) / 100,8 mA (max) |
| **Total no trilho de 12 V** | 49,2 mA | **82,8 / 104,7 mA** |
| Folga sobre o buck de 0,60 A | 12,2× | **5,7×** |

Todos **[MEDIDO]**. O buck adotado **não** precisa mudar.

Correção de direção já relevante: `dimensionamento_fase0.py` linha 163 imprime
`12 V : 12 drivers x 2.5 mA + carga de gate = 0.049 A -> buck 0.6 A`, e
`FASE0_ESPECIFICACAO.md` linha 284 diz `12 drivers x 2,5 mA + carga de gate 19,2 mA = 0.049 A`.
Os dois números mudam, e ambos os arquivos ficam desatualizados em relação a este
documento. **Não os editei** — regra 3 da missão.

---

## 4. Reexecução da Fase 0: que limite estourou

Os scripts originais **não foram modificados**. Para não sobrescrever as evidências
versionadas (`dimensionamento_fase0.json`, `verifica_limites_saida_v4.txt`), foram
executados a partir de uma cópia fora do repositório:

```
cp fase0_especificacao/dimensionamento_fase0.py fase0_especificacao/verifica_limites_entrada_v4.py /tmp/f0ro/
cd /tmp/f0ro && python3.9 dimensionamento_fase0.py          # exit 0, 168 linhas
cd /tmp/f0ro && python3.9 verifica_limites_entrada_v4.py    # exit 0, 41 linhas
```

> **Nota sobre `verifica_limites_saida_v4.py`: este arquivo NÃO EXISTE.** O que existe é
> `fase0_especificacao/verifica_limites_saida_v4.txt`, que é a **saída** produzida por
> `verifica_limites_entrada_v4.py` (última linha do script: `open(...).write(...)` apontando
> para esse `.txt`). Não há script de saída separado para a v4, ao contrário de v2 e v3, que
> também só têm `.txt`. Verificado com `ls` e `git ls-files`. [MEDIDO]

### 4.1 Saída real do `dimensionamento_fase0.py`, §2 (transcrita, sem edição)

```
Potencia de gate por FET: Qg*Vgs*f = 40 nC * 12.0 V * 20 kHz = 9.60 mW
Por driver (2 FETs) = 19.20 mW | 12 drivers = 230.40 mW
Corrente de pico de gate: Rg=10 ohm -> 1.20 A | Rg=5 ohm -> 2.40 A (vem do cap de bootstrap + 10 uF local, nao do buck)
Tempo de subida estimado t_r = Qg/Ipk = 33.33 ns com Rg=10 ohm
Capacitor de bootstrap: Cboot >= 20*Qg = 800 nF -> adotar 1 uF/25 V X7R
Queda no bootstrap a cada ciclo: dV = Qg/Cboot = 0.040 V
Trilho 12 V: quiesciencia 12*2.5 mA = 30 mA + 19.2 mA (carga de gate) = 49 mA -> BUCK 12 V / 0.60 A com folga 3x
```

### 4.2 Saída real do `verifica_limites_entrada_v4.py`, §3 e §4 (transcrita, sem edição)

```
  cruzeiro (5 A fase) : P/FET=0.016 W -> 24 FETs= 0.39 W | Tj(Rth=60C/W, Ta=25C) = 26.0 C
  nominal (15 A)      : P/FET=0.146 W -> 24 FETs= 3.50 W | Tj(Rth=60C/W, Ta=25C) = 33.7 C
  pico (30 A)         : P/FET=0.583 W -> 24 FETs=13.99 W | Tj(Rth=60C/W, Ta=25C) = 60.0 C
  Via 0.3 mm: R=1.168 mOhm -> 40 vias a 30 A: queda 0.876 mV, P=26 mW total
  Gate: Z0=3.16 ohm -> Rg>=6.3 ohm (adotado 10 ohm) | f_ring=25.2 MHz
  ADC: janela 2 us = 4.0 % do periodo de 50 us | dead-time 520 ns = 1.0 % de duty

  Helice: 167 W | I_barra 7.5 A | I_fase pico 12.5 A
  FETs: 1.88 W | conversores: 4.00 W (entrada) | TOTAL ~ 173 W (3.5 % acima do ideal de helice)
```

### 4.3 Veredito por limite

| ID | Limite | Esperado | Medido com Qg real | Erro | Veredito |
|---|---|---|---|---|---|
| **L1** | Tempo de subida de gate (33,33 ns orçados) | 33,33 ns | **1292,3 ns** | **+3777,31 %** | 🔴 **ESTOURADO** — 39× mais lento. O script não checava este limite |
| **L2** | Bootstrap: queda `dV = Qg/Cboot` com 1 µF | 40 mV | **168 mV** | **+320,00 %** | 🔴 **ESTOURADO** — o 1 µF adotado não serve mais. Mínimo passa a 3,36 µF (20×Qg), ou aceita-se 168 mV/comutação = 1,7 % da tensão de gate |
| **L3** | Corrente no trilho de 12 V (buck de 0,60 A) | 49,2 mA | 104,7 mA | +112,80 % | 🟢 **NÃO ESTOURADO** — 17,5 % do buck, folga 5,7× |
| **L4** | Dead-time do RTL (medido em Verilog) | 518,75 ns | **622,2 ns** | **+19,95 %** | 🔴 **ESTOURADO** — e em +211,40 % no turn-on com Qg max a 130 mA |
| **L5** | Potência de gate por FET | 8,0 mW | 33,6 mW | +320,00 % | 🟢 **NÃO ESTOURADO** termicamente — é energia dissipada no Rg, não perda de FET. Pico no Rg: 0,191 W sustentado por 1,2923 µs; média 4,94 mW/FET no período de 50 µs **[MEDIDO]** |
| **L6** | Slew de gate | 0,3000 V/ns (assumido) | **0,00774 V/ns** | **−97,42 %** | 🟡 **sem veredito** — o v4 não fixa limite de slew. O que existe é incompatibilidade de projeto com L7 |
| **L7** | Rg total (10 Ω já especificados, linha 251) | 10 Ω | 1,49 Ω seria preciso para 25 ns | −85,12 % | 🟡 **sem veredito numérico** — é incompatibilidade: o alvo de 25 ns pede `Rg < 1,49 Ω` e o amortecimento já especificado pede `Rg ≥ 6,3 Ω` |
| **L8** | Perda de comutação no MOSFET (0,583 W/FET é o que o v4 §3 usou) | 0,583 W | **9,77 W** | **+1575,79 %** | 🔴 **ESTOURADO — o grave.** `Tj = 611 °C` contra 60,0 °C **[EST, modelo grosseiro]**. Com o t_r do DS (23 ns) o mesmo modelo daria 0,174 W, abaixo do limite |

### 4.4 O que **não** mudou (verificado item a item)

| Bloco do `verifica_limites_entrada_v4.py` | Depende de | Mudou? |
|---|---|---|
| §1 e §2 — ripple de barramento, banco de capacitores, interleaving | fpwm (P-07, inalterado), Ipk (P-03, inalterado), C e ESR | **Não** — nenhum dos quatro mudou. As saídas são idênticas **[MEDIDO]** |
| §3 — térmica de regime | Rds(on) (P-05 mantida em 2,0 mΩ) e corrente | **Não** |
| §3 — vias, Z0, f_ring, ADC | geometria e temporização, não Qg nem Iq | **Não** |
| §4 — balanço no cruzeiro | parcela "conversores" usa 12 × 0,049 A | **Sim, e não estoura**: o total vai de 173 W para 182 W, e a folga de 3,5 % vira 9,2 % **[MEDIDO]** |

### 4.5 Onde o ripple **não** pode ser fechado

Os blocos §1 e §2 do v4 giram em torno de valores de **ESR** que são cenário, não
datasheet: ele varre 15/12/10/8 mΩ para 470/1000/2200/4400 µF. Com o P-15 em aberto
(`[N/D offline]`, sem parte de capacitor escolhida), **esse limite continua não verificado** —
e é o limite que mais pesa na escolha do banco de capacitores. Nada nesta versão do
dimensionamento muda isso, e o registro explícito é melhor que um número inventado.

---

## 5. O que muda no projeto, em lista

1. **A escolha do MOSFET precisa ser refeita.** A especificação de compra da linha 249 de
   `FASE0_ESPECIFICACAO.md` exige `Qg ≤ 60 nC`. O FET de referência tem 168 nC: a própria
   especificação **rejeita** o componente de referência. Ou a especificação relaxa, ou o
   FET muda, ou aceita-se um FET de baixa frequência de comutação (menor Rds(on), maior Qg —
   é o trade-off clássico de FOM). **Decisão de projeto, não de cálculo.**
2. **O gate driver precisa mudar ou ganhar um pre-driver.** O IR2104 é marginal: fecha no
   drain, falha no source.
3. **A fonte de corrente de gate precisa de um capacitor local.** Com C_local de 1 µF a
   queda por comutação é 168 mV, 16,8 mV com 10 µF e 1,68 mV com 100 µF **[MEDIDO]**. Com
   o capacitor no circuito, quem carrega o gate é ele, e o IR2104 só repõe a perda de
   `Qg/Cboot` no bootstrap. Isso reordena a seção 2 do `dimensionamento_fase0.py` inteiro,
   que já afirmava que a corrente vem do bootstrap, mas calculava `Ipk = Vgs/Rg`.
4. **O Cboot de 1 µF não serve.** Precisa de 3,36 µF para a regra de 20×Qg, ou de um valor
   maior se a queda for tolerável.
5. **O orçamento de dead-time tem de vir de bancada**, não do RTL. Nem o 168 nC nem o
   210 nC são garantidos em produção ("not subject to production test"), e os dois dead-times
   se somam.
6. **Rg precisa de duas contas, não uma.** O de 10 Ω está dimensionado para amortecer o
   ringing (Z0 = 3,16 Ω) e não para comutar rápido. Os dois objetivos pedem o mesmo
   resistor em direções opostas.
7. **O buck de 12 V / 0,60 A continua certo** e não precisa de revisão.

---

## 6. Rastreabilidade

| Arquivo | Papel |
|---|---|
| `fase0_especificacao/redimensionamento_gate_v5.py` | script novo, 647 linhas; produz a saída abaixo |
| `fase0_especificacao/redimensionamento_gate_v5_saida.txt` | saída real, 500 linhas, colada na íntegra |
| `fase0_especificacao/REVERSAO_PREMISSAS_v5.md` | este arquivo |
| `fase0_especificacao/dimensionamento_fase0.py` | **lido e executado, não editado** |
| `fase0_especificacao/verifica_limites_entrada_v4.py` | **lido e executado, não editado** |
| `fase0_especificacao/FASE0_ESPECIFICACAO.md` | **lido, não editado** |
| `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` | fonte de P-06 e P-05, páginas 1 e 4 |
| `datasheets/ir2104_infineon_datasheet.pdf` | fonte de P-11 e das correntes de gate, páginas 1 e 3 |
| `fase2_simulacao/verilog/RELATORIO_VERILOG.md` | fonte do dead-time de 518,750 ns |
| `fase3_pcb/gera_pcb_v7.py` | fonte da tensão de 12 V do trilho de gate (linha 239) |
| `plano/WP4_FIRMWARE.md` | RF-05 e RF-14 já registram que o dead-time do IR2104 é interno e fixo; este documento **quantifica** o que isso significa com Qg = 168 nC |

**Comando de reprodução:**

```
cd /opt/jupyter/work/drone/fase0_especificacao && python3.9 redimensionamento_gate_v5.py
```
