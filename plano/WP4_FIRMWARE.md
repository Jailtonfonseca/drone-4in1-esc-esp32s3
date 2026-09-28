# WP4 — ESCOPO E PLANO DO FIRMWARE DE BORDO

**Projeto:** drone 4×ESC trifásico + ESP32-S3 na mesma PCB
**Documento:** US-004 · **Data:** 2026-09-27 · **Pasta:** `plano/` · **TZ:** America/Bahia
**Este documento entrega:** inventário do software do projeto, escopo mínimo de firmware por
módulo e a recomendação de escopo. **Não entrega firmware** (nenhuma linha de código de voo
escrita aqui).

---

## 0. Como ler este documento (obrigatório)

Cada número tem etiqueta de origem, no mesmo estilo do resto do projeto
(`fase0_especificacao/FASE0_ESPECIFICACAO.md` §0):

| Etiqueta | Significado |
|---|---|
| **[MEDIDO]** | saiu de um arquivo de log gerado por ferramenta real já executada nesta máquina |
| **[CALC]** | calculei nesta máquina com um comando registrado na §9 |
| **[DATASHEET]** | número lido do PDF que está no disco do projeto, com o caminho |
| **[EST]** | estimativa de engenharia minha, **não medida** |
| **[PREMISSA]** | premissa herdada do projeto (P-01…P-15) que não foi confirmada |
| **[N/D offline]** | dado que precisa de um documento que **não está no disco** (o TRM da Espressif) |

Nenhum caminho citado neste documento está inventado: todos foram conferidos com `test -e`
(o critério de extração e o comando estão na §9.3, o resultado linha a linha na §10 —
**44 testados, 44 existem, 0 inexistente**).

---

## 1. VEREDITO EM UMA LINHA

> ### O drone **não tem uma única linha de firmware**. O que existe de software é **RTL em
> > Verilog** (12 canais de PWM com dead-time), que **não roda dentro do ESP32-S3** — é um
> > modelo de referência, não um programa. O firmware de voo real **não está no escopo desta
> > entrega** e custa **320 h** [EST] — e, antes de existir, exige **3 correções de hardware**
> > que nenhum código contorna (§7.2, §7.3, §7.4).

---

## 2. INVENTÁRIO — O QUE **JÁ EXISTE** DE SOFTWARE

Tudo nesta seção está em `fase2_simulacao/verilog/` e é verificável abrindo os arquivos.

### 2.1 O RTL do PWM de 12 canais

| Arquivo | Bytes | O que é | Origem do número |
|---|---:|---|---|
| `fase2_simulacao/verilog/pwm_deadtime.v` | 7 697 | 2 módulos: `pwm_deadtime` (topo) e `pwm_dt_channel` (1 half-bridge) | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §1 |
| `fase2_simulacao/verilog/tb_pwm.v` | 9 591 | testbench: varredura de duty, monitor de shoot-through, medidas, VCD | idem |
| `fase2_simulacao/verilog/tb_pwm.log` | 2 022 | saída real do Icarus | idem |
| `fase2_simulacao/verilog/tb_pwm.vcd` | 10 429 328 | dump de ondas de 150 µs | idem |
| `fase2_simulacao/verilog/compile.log` | **0** | vazio = **nenhum warning** de compilação | idem §1 |
| `fase2_simulacao/verilog/yosys.log` | 115 297 | síntese completa, exit 0 | idem §6 |
| `fase2_simulacao/verilog/yosys_stat.log` | 79 886 | fluxo sem ABC (1ª estimativa) | idem |
| `fase2_simulacao/verilog/pwm_deadtime.png` | 134 433 | formas de onda em 3 painéis | idem §5 |
| `fase2_simulacao/verilog/plot_pwm.py` | 8 750 | parser de VCD próprio (independente do testbench) | idem |
| `fase2_simulacao/verilog/RELATORIO_VERILOG.md` | — | o relatório com esperado × medido × erro | idem |

### 2.2 A interface do RTL — o que o firmware teria que reproduzir

Lido direto de `fase2_simulacao/verilog/pwm_deadtime.v` (declaração do módulo, linhas 31–48):

| Item | Valor | Origem |
|---|---|---|
| Clock | 160 MHz (6,25 ns) | cabeçalho do `.v` e parâmetro do teste |
| `PERIOD` | 8 000 ciclos = 50 µs → **20 kHz** | `.v` linha 32; medido em `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4.3 |
| Portadora | triângulo 0…4000…0 a partir de **um** contador mestre | `.v` linhas 65–72 e 84–89 |
| Defasagem entre motores | `φ_g = (contador + g·2000) mod 8000` → **90° exatos**, sem *drift* | `.v` linhas 78–82 |
| Comparação | `tri_w < dthr`, `dthr = (duty_cl · 4000) / 4095` | `.v` linha 90 |
| Resolução de duty | 12 bits (0…4095) | `.v` linha 33 |
| `DUTY_MIN_CODE` | 82 → **2,0 %** (o pulso high-side tem de ser maior que o dead-time, 520 ns = 1,04 %) | `.v` linha 34; `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2 |
| `DUTY_MAX_CODE` | 3890 → **95,0 %** (garante 2,5 µs de low-side para o bootstrap) | `.v` linha 35 |
| Dead-time | `DEADTIME_CYCLES = 83` = 518,75 ns, **programável em runtime** por `deadtime_i[15:0]` | `.v` linhas 32 e 75–80 |
| Saídas | `pwm_o[11:0]`, `hi_o[11:0]`, `lo_o[11:0]` — **36 pinos** no RTL | `.v` linhas 39–42 |
| Semântica de repouso | `duty_i = 0` → "sem pulso, `lo` fica ligado" | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2 (e §7.10) |
| Garantia anti-shoot-through | **estrutural**: `hi=1` exige `pwm_in=1` estável, `lo=1` exige `pwm_in=0` estável — não é `$assert` | `.v` linhas 20–26 e 118–150 |

### 2.3 O que o Icarus e o Yosys **provaram** [MEDIDO]

Todas as linhas vêm de `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4 e §6.

| Grandeza | Esperado | **Medido** | Erro |
|---|---|---|---|
| Dead-time nas **duas** bordas | 83 ciclos = 518,750 ns | **518,750 ns** | **0,000 ns (0,000 %)** |
| Contra a referência de projeto de 520 ns | 520 ns | 518,750 ns | −1,250 ns (−0,240 %) |
| Dead-time reprogramado (`deadtime_i` = 40) | 250,000 ns | **250,000 ns** | 0,000 ns |
| Frequência da portadora | 20 kHz | **20 000,0 Hz** | **0,0000 %** |
| Violações `hi & lo != 0` | 0 | **0** em **362 060 ciclos** checados (2 262,872 µs), incluindo 60 000 ciclos de estresse com duty e dead-time pseudo-aleatórios | — |
| Defasagem entre grupos | 0/90/180/270° | **0,000° / 90,000° / 180,000° / 270,000°** | **0,000°** |
| Duty 100 % pedido | saturado a 95 % | **94,963 %** (clamp) | — |
| Duty 49,988 % | 49,988 % | **49,962 %** | viés de truncamento inteiro, ~0,02 pp |
| Síntese (Yosys) | exit 0, sem latch | **exit 0 · 0 WARNING · 0 ERROR · 0 latch · 0 memória · 248 FF · 22 831 células genéricas** | — |

O parser `fase2_simulacao/verilog/plot_pwm.py`, que **re-lê o `.vcd` de forma independente do testbench**, bate com o
`fase2_simulacao/verilog/tb_pwm.log` nos dois lados: `dt_subida = 518.750 ns` e `dt_descida = 518.750 ns`
(`fase2_simulacao/verilog/RELATORIO_VERILOG.md` §3).

### 2.4 O que esse RTL **não** é (e isso decide a §6)

1. **Não roda no ESP32-S3.** O ESP32-S3 é um microcontrolador: não recebe netlist Verilog.
   O relatório diz textualmente: *"**Não** é mapa para FPGA/CPLD real: nenhuma tecnologia
   foi alvo"* (`fase2_simulacao/verilog/RELATORIO_VERILOG.md` §6) e *"Nada foi gravado em FPGA/CPLD/ASIC. Tudo é
   simulação funcional em Icarus Verilog"* (§7.1).
2. **A placa não tem CPLD/FPGA.** O plano B declarado em `fase0_especificacao/FASE0_ESPECIFICACAO.md`
   §4.1 — *"CPLD/FPGA gerando as 24 saídas com dead-time programável"* — **não foi
   implementado**: `grep -ci "cpld\|fpga\|lattice\|altera" fase3_pcb/gera_pcb_v7.py` devolve
   **0**. Não há onde gravar o RTL, e ele roda a 160 MHz porque foi *escrito* para 160 MHz, não
   porque o chip faz isso.
3. **O RTL tem 36 saídas e a placa tem 12 pinos de PWM.** Como o gate driver é *single-input*
   (IR2104, `fase3_pcb/gera_pcb_v7.py` linhas 8–9: `1 VCC, 2 IN, 3 SD, 4 COM, 5 LO, 6 VS,
   7 HO, 8 VB`), o complementar e o dead-time ficam no driver. Então **1 PWM por half-bridge,
   12 pinos** — que é a conta que a Fase 0 §4.1 já fazia.
4. **A semântica de repouso do RTL não é a do hardware.** O RTL diz `duty = 0` → `lo` ligado
   (`fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2). O firmware precisa ser escrito contra o **IR2104**, não contra
   o RTL. Ver risco RF-03 na §7.3.
5. **Jitter, atraso de GPIO e sincronismo com o ADC não foram modelados** (`fase2_simulacao/verilog/RELATORIO_VERILOG.md`
   §7.2, §7.3 e §7.4 — *"Nada garante que o disparo do ADC caia fora da janela de dead-time"*).

### 2.5 O resto do software do projeto (ferramentas, não firmware)

| Família | Arquivos | O que faz |
|---|---|---|
| Dimensionamento | `fase0_especificacao/dimensionamento_fase0.py`, `fase0_especificacao/verifica_limites_entrada_v4.py`, `fase0_especificacao/diagrama_blocos_v3.py` | cálculo dos estágios, verificação de limites, diagrama |
| Simulação SPICE | `fase2_simulacao/gera_tabela.py`, `fase2_simulacao/minimiza_ripple.py` + 8 netlists `.cir` | buck 12/5/3,3 V, gate drive, shunt+amp, VBAT, BEMF, anti-inversão |
| PCB | `fase3_pcb/gera_pcb_v1.py` … `fase3_pcb/gera_pcb_v7.py`, `fase3_pcb/rota_v7.py` | layout por código, KiCad 5.1 headless |
| Verificação | `fase3_pcb/verifica_fase3_v6.py` | verificação geométrica/elétrica |
| Orçamento | `orcamento/orcamento.py` | custos |
| Plot do PWM | `fase2_simulacao/verilog/plot_pwm.py` | PNG das formas de onda |
| Saídas de cálculo | `fase0_especificacao/dimensionamento_fase0_saida_v2.txt`, `fase2_simulacao/RESULTADOS_FASE2_SPICE.md`, `fase4_entrega/calcs_wifi_controle.txt` | os números de todos os relatórios |
| Artefatos da Fase 0 | `fase0_especificacao/lista_componentes_fase0.csv` (43 linhas), `fase0_especificacao/diagrama_blocos_fase0_v3.png` | BOM de origem e diagrama de blocos |

Tudo isso é **software de projeto**, roda nesta máquina, e é o que já está 100 % "entregue" no
sentido de "`fase0_especificacao/FASE0_ESPECIFICACAO.md` §0" (número vem de log real).

---

## 3. INVENTÁRIO — O QUE **NÃO EXISTE**

Comando executado nesta máquina, em `/opt/jupyter/work/drone`:

```console
$ find . -type f \( -name '*.c' -o -name '*.cpp' -o -name '*.cc' -o -name '*.h' \
      -o -name '*.hpp' -o -name '*.ino' -o -name '*.ld' -o -name 'CMakeLists.txt' \
      -o -name 'Makefile' -o -name 'platformio.ini' -o -name '*.S' -o -name '*.s' \)
$
$ find . -type f \( -name '*.c' -o -name '*.cpp' -o -name '*.h' -o -name '*.ino' \
      -o -name 'CMakeLists.txt' -o -name '*.ld' \) | wc -l
0
```

**Resultado: 0 arquivos. Saída vazia, contagem 0.** Não há firmware, não há linker script,
não há build system, não há `main()`.

E o toolchain também não existe nesta máquina [MEDIDO]:

```console
$ which idf.py          →  (vazio)
$ ls -d /opt/esp* ~/esp ~/.espressif  →  "sem instalacao do ESP-IDF"
$ which xtensa-esp32s3-elf-gcc        →  AUSENTE
```

Consequência direta: **as 320 h da §5 incluem instalar e manter o ESP-IDF.** Nenhuma hora do
plano pode ser executada hoje sem esse passo prévio.

### 3.1 O mapa do que falta, por camada

| Camada | Existe? | Onde está a prova |
|---|---|---|
| Geração de PWM com dead-time | ⚠️ **só como RTL de referência** — não executável no MCU | §2.4 |
| Leitura de corrente/BEMF (ADC externo) | ❌ não existe | `find` acima |
| Malha de PID / lógica de voo | ❌ não existe — e está **fora de escopo por decisão registrada** | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §9.6 |
| Comutação de motor / ESC | ❌ não existe | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §7.10: *"Não há lógica de comutação (sequência de 6 passos), BEMF, sensor Hall"* |
| Pilha de rádio (ESP-NOW) | ❌ não existe | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §8.6: *"PID, IMU, failsafe e pilha de rádio **não existem**"* |
| Failsafe / watchdog | ❌ não existe | `fase4_entrega/RISCOS.md` R-08 |
| Proteções (sobrecorrente, *trip*, *blanking*) | ❌ não existe | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §7.11: *"Não há detecção de sobrecorrente, trip de falha, nem blanking"* |
| Calibração de shunt/divisores | ❌ não existe | `fase4_entrega/PLANO_TESTE_BANCADA.md` passos 10 e 12 exigem o firmware para dar o número |
| Build, CI e gravação | ❌ não existe | `find` acima |

---

## 4. RESTRIÇÕES DE SOFTWARE **JÁ DECIDIDAS** (com a origem de cada uma)

O firmware não é um campo livre: ele já está preso por decisões que vieram de números.

| # | Restrição | Valor | Origem |
|---:|---|---|---|
| 1 | Frequência do PWM | 20 kHz (50 µs) | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4.3 **[MEDIDO]**; premissa P-07 em `fase0_especificacao/FASE0_ESPECIFICACAO.md` §2 |
| 2 | Malha de PID | **1–4 kHz a bordo** | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §3; `fase0_especificacao/FASE0_ESPECIFICACAO.md` §3.2.1 |
| 3 | Comandos pelo link | **20–50 Hz**, via **ESP-NOW** (sem IP, sem ARQ) | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §3.1 |
| 4 | Telemetria | 10–50 Hz, prioridade baixa, nunca bloqueia o laço | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §3 e `fase0_especificacao/FASE0_ESPECIFICACAO.md` §3.2.5 |
| 5 | **TCP está descartado** | — | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §3.2.4 |
| 6 | Failsafe de link | **200 ms** sem comando → cortar motores / descida controlada | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §3.2.3; `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §5.2 |
| 7 | Duração do failsafe | 200 ms = **19,62 cm** de queda, 1,96 m/s | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §2.4 **[CALC]** |
| 8 | Contagem do failsafe | **10 quadros consecutivos** a 50 Hz, não "um buraco de tempo" | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §5.2 |
| 9 | Ação em duas etapas | estabilizar → descer; corte duro aos **500 ms** (= 1,23 m de queda) | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §5.2 e §2.4 |
| 10 | Amostragem de corrente | **sincronizada com o PWM**, janela de **2 µs = 4 %** do período de 50 µs | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §4.5 **[CALC]** |
| 11 | Canais analógicos | 12 corrente + 12 BEMF + VBAT + temperatura = **26** | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §4.2 **[CALC]** |
| 12 | Defasagem das portadoras | **90°** entre os 4 motores (ganho de 4,46× no ripple RMS do banco) | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §4.3 **[CALC]**; medido 0,000° de erro em `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4.4 |
| 13 | Duty | igual nas 3 fases de um motor; clamp de 2 % e 95 % | `fase2_simulacao/verilog/pwm_deadtime.v` linhas 34–35 e 90–96 |
| 14 | Duty=0 | sem pulso — **atenção: no RTL o `lo` fica ligado** | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2 |
| 15 | LEDC não tem dead-time em HW | por isso o driver *single-input* é obrigatório | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §4.1 |
| 16 | 10 ações de firmware obrigatórias | modem sleep off, IRAM, peer-to-peer, descartar pacotes velhos, etc. | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §6 (tabela de 10 linhas) |
| 17 | Never: laço de atitude não pode depender do link | — | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §6 item 10 |

### 4.1 O que os números da Fase 0 diziam ser `[N/D offline]` **e eu consegui fechar**

O projeto registrou vários números como desconhecidos porque o TRM da Espressif não estava no
disco. **O datasheet do ESP32-S3 está no disco** (`datasheets/esp32-s3_datasheet_en.pdf`,
v2.2) e resolve os três mais importantes [DATASHEET]:

| Parâmetro | O que a Fase 0 registrou | **O que o datasheet v2.2 diz** | Efeito |
|---|---|---|---|
| Canais de ADC | "ADC1 tem ~10 canais, ADC2 é compartilhado com o rádio" `[PREMISSA]` | *"Two 12-bit SAR ADCs, up to 20 channels"* (seção 1) | **20 no máximo.** São necessários 26 → **faltam 6 canais mesmo usando os dois ADC.** O ADC externo por SPI vira obrigatório, e agora por número fechado, não por “[PREMISSA]”. |
| Cobertura do MCPWM | "MCPWM: 2 unidades × 3 operadores → 6 canais → **2 motores**" | *"two MCPWMs… each has one clock divider, three PWM timers, three PWM operators"* (seção 4.2.1.10) | **Confirma exatamente: 2 × 3 = 6 saídas com dead-time em HW = 2 motores.** Os outros 2 vão por LEDC, sem dead-time em HW. |
| Canais de LEDC | "LEDC: 8 canais" | *"LED PWM controller, up to 8 channels"* (seção 1) | **8 canais confirmados** → 6 para os motores 3 e 4, sobram 2. |
| Clock da CPU | não registrado | *"Clock speed: up to 240 MHz"*; *"1329.92 CoreMark"*; 5,54 CoreMark/MHz | Referência real para o orçamento de CPU (RF-12, §7.1). |
| ADC2 × rádio | `[PREMISSA] a confirmar no TRM` | o datasheet v2.2 **não menciona** a exclusão ADC2/WiFi | Segue **[N/D offline]**: o TRM não está no disco. Não uso esse número. |

Isto **fecha parcialmente o risco R-14** de `fase4_entrega/RISCOS.md` ("Contagem de
periféricos do ESP32-S3"), cuja própria coluna de detecção pedia: *"Conferir no TRM da Espressif."*

---

## 5. ESCOPO MÍNIMO DE FIRMWARE PARA O DRONE VOAR

Uma linha de âncora por módulo. Esforços em horas são **[EST]** (minha estimativa de engenharia,
somados com `python3 -c` na §9.2 — não são medidos, e isso está dito na tabela). A ordem é a de
execução: cada módulo só faz sentido com o anterior medindo.

Os pinos de PWM na tabela abaixo são **pads do módulo ESP32-S3-WROOM-1**, não números de GPIO: o pin map do firmware tem de ser extraído do netlist do layout (`fase3_pcb/gera_pcb_v7.py` linhas 400–411), e não da §8 da Fase 0 — ver RF-07. Fica dito aqui para não repetir o erro.

| # | Módulo | O que faz (1 linha) | Entrada → Saída | Critério de aceite (verificável) | h **[EST]** |
|---|---|---|---|---|---:|
| M0 | Toolchain e harness | Instalar ESP-IDF, criar o projeto CMake, gravar por USB-C e ler o log de boot pela UART0 | repositório vazio → binário que roda no MCU | build reproduzível a partir de um comando só, registrado no `README.md`; boot log pela UART0 lido em bancada | 12 |
| M1 | Bring-up de placa | Clock, GPIO, LED, buzzer, botões, VBAT sense e temperatura em regime | binário → LED piscando, botão lido, VBAT medido | **VBAT medido: 2,385752 V @ 19,8 V · 2,674934 V @ 22,2 V · 3,036412 V @ 25,2 V** com erro < 2 % (`fase4_entrega/PLANO_TESTE_BANCADA.md` passo 10) | 16 |
| M2 | PWM dos motores 1 e 2 (MCPWM) | 6 saídas com dead-time **em hardware**, 20 kHz, 12 bits | `duty[6]` → pads 4, 5, 6, 7, 12 e 17 do módulo | osciloscópio em 2 canais: período 50 000 ns ± 0,1 %; dead-time entre 250 ns e 2 µs; **sobreposição dos dois gates = 0** (passo 9) | 24 |
| M3 | PWM dos motores 3 e 4 (LEDC) + defasagem | 6 saídas **sem** dead-time em HW + as 4 portadoras defasadas 90° | `duty[6]` → pads 18, 19, 20, 21, 22 e 8 do módulo | **janela de dead-time própria, diferente da do M2**: 400–650 ns (piso/máx de catálogo do `DT`, RF-14) e **não** 250 ns–2 µs — nos motores 3 e 4 o dead-time é **fixo no driver, não programável por firmware**, porque vão por LEDC; período 50 000 ns ± 0,1 %; defasagem entre grupos medida **90,000° ± 1°**; clamp de duty em 2 % e 95 % verificado | 28 |
| M4 | Leitura dos 4× MCP3208 | 12 canais de corrente + 12 de BEMF por SPI, com *round-robin* e disparo na janela de 2 µs | `4×MCP3208` → corrente (A) e BEMF (V) | linearidade < 2 % entre 5 e 30 A, com **offset a 0 A anotado e subtraído** (passo 12); BEMF com erro < 1 % em 3 pontos (passo 11); 1 mV de saída ≈ 40 mA | 32 |
| M5 | IMU ICM-42688-P | Leitura de rate e atitude por SPI a 1–4 kHz, com filtro | SPI → taxa angular (°/s) e atitude | IMU **estável com o motor parado**; com motor a 100 % de duty o ruído do giroscópio não cresce > 10× (critério `[EST]` de `fase4_entrega/RISCOS.md` R-07) | 16 |
| M6 | Barômetro | Leitura de altitude a dezenas de Hz por I²C | I²C → altitude (m) | leitura estável em bancada; deriva < 1 m/10 min parado | 8 |
| M7 | PID de atitude | 6 eixos (3 ângulos + 3 taxas) a 1–4 kHz, com anti-*windup* e filtro de derivada | IMU + setpoint → 4 misturadores | pousar e pairar sem divergir; **a 4 kHz são 80 iterações de PID por setpoint de 50 Hz** (`fase4_entrega/ANALISE_WIFI_CONTROLE.md` §3) | 40 |
| M8 | Comutação do motor | Sequência de 6 passos por BEMF, com limite de corrente | BEMF + setpoint → sentido e duty | 4 motores em 4 sentidos, corrente de partida dentro do limite da fonte, sem pico > 2× a de regime, FET < 60 °C em 5 min (passo 14) | 40 |
| M9 | ESP-NOW | RX de comandos a 20–50 Hz, TX de telemetria a 10–50 Hz, com as 10 ações da §4.1 | rádio 2,4 GHz → setpoint | latência por quadro medida e registrada; **o receptor descarta pacotes velhos**; tempo de ar de 32 B = 672 µs a 1 Mbps, 3,36 % de ocupação a 50 Hz (`fase4_entrega/ANALISE_WIFI_CONTROLE.md` §4) | 24 |
| M10 | Failsafe de link | 200 ms / 10 quadros → 2 etapas → corte duro aos 500 ms | perda de link → corte dos motores | desligar o transmissor **com o motor girando** corta em **≤ 200 ms** (passo 15 e R-08); corte falso não ocorre em 30 min de log | 16 |
| M11 | Watchdog | TWDT interno alimentado pelo laço + registro do motivo do reset | laço de controle → reset controlado | matar o laço provoca reset ≤ 1 s e o motivo do reset é legível (R-09) | 8 |
| M12 | Proteções | Sobrecorrente, subtensão de VBAT, temperatura, *blanking*, *trip* | sensores → corte de motor | corrente > limite por mais de N amostras corta o motor e registra o evento; subtensão de 3,3 V/célula alarme | 24 |
| M13 | Integração em bancada | Calibração, ajuste de PID e logs persistentes | tudo acima → voo em bancada | **todos os passos de `fase4_entrega/PLANO_TESTE_BANCADA.md` aprovados**, com hélices removidas | 32 |

**Total: 320 h [EST]** = 40 dias de 8 h = 8,0 semanas de 40 h **[CALC na §9.2]**.
Duas fatias:

| Fatia | Módulos | Horas | Serve para quê |
|---|---|---:|---|
| **Firmware de bancada** | M0–M6 + M10 + M11 | **160 h** | Fazer os passos 9, 10, 11, 12, 14 e 15 de `fase4_entrega/PLANO_TESTE_BANCADA.md` serem executáveis. Sem ele, o plano de teste de bancada é letra morta. |
| **Desenvolvimento de voo** | M7 + M8 + M9 + M12 + M13 | **160 h** | Fazer o drone **voar** com link de comando. |

---

## 6. O FIRMWARE ENTRA OU NÃO NO ESCOPO DESTE PROJETO?

### 6.1 Veredito

> ## O firmware de voo real fica **FORA** do escopo desta entrega.
> ## O **firmware de bancada** (M0–M6 + M10 + M11, 160 h) **ENTRA**, porque sem ele o próprio
> ## plano de teste de bancada que já está escrito no repositório não pode ser executado.

### 6.2 As 3 razões, com a origem de cada uma

**(a) O próprio briefing original já retirou a lógica de voo do escopo, por escrito.**
`PROMPT_AGENTE_DRONE.md`, item 6 do "ESCOPO DA PLACA": *"**Firmware:** apenas o que for
verificável aqui (ex.: geração de PWM com dead-time em Verilog, testado em simulação). Deixe
claro que a lógica de voo real não está no escopo desta placa."*
`fase0_especificacao/FASE0_ESPECIFICACAO.md` §9.6 repete: *"**O firmware de voo real não está no
escopo.**"*
`fase4_entrega/ANALISE_WIFI_CONTROLE.md` §7 fecha: *"Onde fica a lógica de voo? A bordo — e a
Fase 0–3 não a entrega."*
Três documentos, a mesma frase. Isso não é omissão: é decisão registrada.

**(b) O que existe não é executável no MCU, e a placa não tem onde executar.**
Ver §2.4. O RTL foi sintetizado para primitivas genéricas do Yosys, sem tecnologia alvo, e não há
CPLD/FPGA no layout (`grep` = 0 ocorrências em `fase3_pcb/gera_pcb_v7.py`) — e o próprio layout ainda está em aberto: `fase3_pcb/rota_v7.py` não fecha e `fase3_pcb/v6/verificacao_v6.txt` registra 367 de 426 nets sem rota. As 248 células e os
248 flip-flops do §2.3 não vão virar gate driver de MOSFET por software.

**(c) Três bloqueios de hardware são anteriores ao firmware e nenhum código os resolve.**
Ver §7.2, §7.3 e §7.4. Em resumo: a taxa do ADC externo é insuficiente para a amostragem
sincronizada que a Fase 0 §4.5 exige; o *shutdown* dos 12 gate drivers está preso em 3V3; e não
existe watchdog externo. Escrever firmware antes de resolver isso é escrever firmware que vai ser
reescrito.

### 6.3 A consequência de cada escolha

| Opção | O que a entrega passa a ser | Horas | O que fecha | O que fica aberto |
|---|---|---:|---|---|
| **A — Fora (veredito, recomendado)** | **Hardware + documentação de interface.** Gerbers, esquema, BOM, `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md`, `fase4_entrega/SEGURANCA_E_REGULATORIO.md` e a especificação de firmware que é este documento | **0** | Especificação de PWM validada (518,750 ns, 0 violações em 362 060 ciclos), layout, custo, riscos, regulatório | 320 h de firmware; **o drone não voa**; 3 bloqueios de hardware a resolver |
| **B — Firmware de bancada dentro (o mínimo que eu defendo)** | Idem A **+ firmware que roda na placa e é testado** | **160 h** | também os passos 9, 10, 11, 12, 14, 15 de `fase4_entrega/PLANO_TESTE_BANCADA.md`; a placa sai do papel | 160 h de PID + comutação; **o drone ainda não voa**; precisa dos 3 bloqueios resolvidos |
| **C — Firmware completo dentro** | Drone que voa | **320 h** | tudo | precisa dos 3 bloqueios resolvidos **antes** de começar; nenhuma validação em bancada foi feita até hoje (`fase4_entrega/RISCOS.md` §5) |

**Em uma frase para quem perguntar "então o projeto termina quando?":** na opção A, quando o
layout fechar e o Gerber final sair; na opção C, quando voar. São projetos com nomes diferentes,
e o repositório hoje tem o nome do segundo e o conteúdo do primeiro.

### 6.4 O que muda no repositório se você escolher B

Três arquivos novos, nada editado, e nenhum deles é firmware:

1. `plano/WP4_FIRMWARE.md` (este documento) — o escopo, já escrito.
2. Uma seção nova no `README.md` apontando para cá — **mas o `README.md` é um arquivo
   existente e o briefing proíbe editar arquivo existente; então a alteração fica registrada
   como pendência, não executada.**
3. Um registro de "bloqueadores de firmware" para as três correções de hardware da §7.

---

## 7. RISCOS TÉCNICOS CONCRETOS NESTE HARDWARE

### 7.1 Tabela de riscos (todos com a origem de cada afirmação)

| ID | Risco | Evidência | Origem | Consequência no firmware | Gravidade |
|---|---|---|---|---|---|
| **RF-01** | **A taxa do ADC externo não comporta 1 leitura por canal por período de PWM** | 6 canais por CI × 20 kHz = **120 ksps por CI**. O MCP3208 entrega **100 ksps a 5 V** e **50 ksps a 2,7 V** | `datasheets/mcp3208_microchip_ds21298e.pdf` (Electrical Characteristics, `fSAMPLE`); canais em `fase3_pcb/gera_pcb_v7.py` linhas 384–385; 20 kHz em `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4.3 **[CALC §9.1]** | **120 % do datasheet a 5 V e 240 % a 2,7 V.** Numa comutação normal, os canais sharing o CI ficam com taxa menor e as leituras saem de fase. | 🔴 **Crítica** |
| **RF-02** | **O MCP3208 multiplexa: não há amostragem simultânea** | MUX interno de 8 canais; *"The MCP3208 is programmable to provide four pseudo-differential input pairs or eight single-ended inputs"* | `datasheets/mcp3208_microchip_ds21298e.pdf` (descrição) | A Fase 0 §4.2 vendeu como *bônus* do ADC externo que *"permite **amostragem simultânea** das 3 fases"*. Com 4× MCP3208 por motor isso **não se materializa**: as 3 fases são lidas em 3 instantes diferentes. FOC e detecção de pico de corrente ficam com erro. | 🔴 **Crítica** |
| **RF-03** | **O *shutdown* dos 12 drivers está preso em 3V3 — não há corte de gate por software** | `Rsd%s` vai de `SD%s` a `3V3`; a rede `SD%s` só aparece nessas 2 linhas e **não chega a nenhum GPIO do MCU** | `fase3_pcb/gera_pcb_v7.py` linhas 238–239 e 401–412 (`MCU_NETS`, sem nenhuma entrada `SDx`) | Não existe instrução de firmware capaz de desligar os 12 IR2104. O corte depende de zerar o duty — e a semântica de repouso do RTL (`duty=0` → `lo` ligado, `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2) **não é** a do IR2104 com `IN=0`. Firmware escrito contra o RTL pode deixar dois low-sides ligados. | 🔴 **Crítica** |
| **RF-04** | **Não há watchdog externo no layout** | `WD_FEED` aparece em exatamente 2 lugares: pad 25 do MCU e o test point `TP_WD`. Nenhum CI de watchdog no layout: buscar por `U_WD`, `MAX706`, `TPS3813` ou `watchdog` no gerador devolve **0** | `fase3_pcb/gera_pcb_v7.py` linhas 406 e 444; mitigação declarada em `fase4_entrega/RISCOS.md` R-08 | A mitigação que a Fase 4 declarou para R-08 não está na placa. Se o firmware travar, os motores ficam no **último duty** até o fim de bateria. A única defesa é o TWDT interno, que morre junto com o firmware. | 🔴 **Crítica** |
| **RF-05** | **Só 2 dos 4 motores têm dead-time em hardware** | MCPWM: 2 unidades × 3 operadores = 6 saídas; LEDC: até 8 canais, **sem** dead-time em HW | `datasheets/esp32-s3_datasheet_en.pdf` §1 e §4.2.1.10 **[DATASHEET]**; `fase0_especificacao/FASE0_ESPECIFICACAO.md` §4.1; dead-time do driver em `datasheets/ir2104_infineon_datasheet.pdf` p. 1 (*"Internally set deadtime — Deadtime (typ.) 520 ns"*) e p. 3, *Dynamic Electrical Characteristics*, símbolo `DT` = **400 / 520 / 650 ns** **[DATASHEET]** | Nos motores 3 e 4 o dead-time **existe, é interno ao IR2104 e é typ. 520 ns** — o firmware não o programa, mas também não o elimina. A afirmação anterior — que tratava isto como premissa pelo argumento *"sem datasheet no disco"* — estava **errada**: `datasheets/ir2104_infineon_datasheet.pdf` tem 142 488 bytes no disco. A proteção contra condução cruzada existe nos 4 motores; o que o firmware não consegue é *aumentá-la* além do que o driver entrega. O risco residual é o piso de 400 ns, agora isolado na RF-14. | 🟢 Média |
| **RF-06** | **O MCP3208 é alimentado a 3,3 V — condição não especificada no datasheet** | A placa liga `VDD` e `VREF` em `3V3`; o datasheet só especifica throughput a **2,7 V (50 ksps)** e **5 V (100 ksps)** | `fase3_pcb/gera_pcb_v7.py` linhas 389–390; `datasheets/mcp3208_microchip_ds21298e.pdf` | O throughput real a 3,3 V é **desconhecido**. O projeto já tem um precedente: o próprio script registra que a escolha ficou *"abaixo dos 200 ksps desejados: registrado como limitacao"* (linha 18). O firmware não pode dimensionar taxa em cima de um número que ninguém mediu. | 🟡 Alta |
| **RF-07** | **O mapa de pinos do firmware não existe ainda — e o da Fase 0 não bate com o layout** | Fase 0 §8: motor 1 = GPIO4,5,6 · motor 2 = GPIO7,8,9 · motor 3 = GPIO10,11,12 · motor 4 = GPIO13,14,15. Layout v7: motor 1 = pads 4,5,6 · motor 2 = pads 7,12,17 · motor 3 = pads 18,19,20 · motor 4 = pads **8**,21,22 | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §8 (e o desenho em `fase1_esquema/esq7_mcu.png`) vs. `fase3_pcb/gera_pcb_v7.py` linhas 400–411, que é o gerador do arquivo `fase3_pcb/v7/v7_drone.kicad_pcb` **[MEDIDO]** | Divergem os motores 2, 3 e 4 inteiro, e o pad 8 (que a Fase 0 dava ao motor 2) está no layout como `PWM_M403`. A Fase 0 também previa **1 CS + IRQ/DRDY** para o ADC; o v7 tem **4 CS** (`ADC_CS1..4`, pads 23, 15, 33, 34). Escrever firmware contra a §8 agora produz um binário que não funciona na placa. | 🟡 Alta |
| **RF-08** | **O duty de repouso e a comutação de 6 passos podem fechar caminho no motor** | O RTL implementa *chopping* sincronizado (3 fases com o mesmo duty, sem defasagem de 120° entre elas) e nenhuma comutação | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §7.10 e §2 | O M8 (6 passos) é o que decide o sentido; se ele definir fase alta e fase baixa com erro, o aterramento fecha a fase. `fase4_entrega/RISCOS.md` R-05 já avisa: *"Correção: trocar duas fases, nunca inverter no firmware (inverte o BEMF junto)"*. | 🟡 Alta |
| **RF-09** | **O barramento SPI é um recurso único e disputado** | 24 canais × 20 kHz × 24 clocks = **11 520 000 clocks/s**. A 10 MHz isso é **115,2 %**; a 8 MHz, 144 %; a 20 MHz, 57,6 % | **[CALC §9.1]**, com 24 clocks por conversão de `datasheets/mcp3208_microchip_ds21298e.pdf` (`tCONV = 12 clocks` + 3 bytes de quadro) e SCK de IMU 4–8 MHz em `fase0_especificacao/FASE0_ESPECIFICACAO.md` §8 | O mesmo barramento serve para os 4 MCP3208, o IMU (que precisa de leitura a 1–4 kHz **sincronizada com o PID**) e o barômetro. A 8 MHz não dá nem para os ADCs. | 🟡 Alta |
| **RF-10** | **Jitter e atraso de GPIO não estão no modelo** | *"Jitter do PLL… **não** existe neste modelo"*; *"O atraso entre a saída do registrador e o pino físico, o skew entre os 12 pinos… **não** foram modelados"* | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §7.2 e §7.3 | O dead-time **real no MOSFET** = 518,750 ns do RTL **+ atraso do driver**, e o atraso do driver *"pode ser maior que 520 ns"* (mesmo §8). A folga de segurança do firmware tem de ser dimensionada com o valor de bancada, não com o do RTL. | 🟡 Alta |
| **RF-11** | **A fase 0 e o layout não concordam sobre a arquitetura do ADC** | Fase 0 §4.2: *"ADC externo por SPI (16 canais, ou 2×8)"*; orçamento: 1× ADS7953 16 canais 1 Msps. Layout v7: 4× MCP3208 de 8 canais | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §4.2; `orcamento/ORCAMENTO.md` §6; `fase3_pcb/gera_pcb_v7.py` linhas 377–394 | A escolha de 4× MCP3208 foi feita por custo (`fase3_pcb/gera_pcb_v7.py` linhas 15–18) e é a que **falha em RF-01 e RF-02**. Trocar de ADC é decisão de hardware, não de firmware. | 🔴 Crítica |
| **RF-12** | **O gargalo do projeto é a aquisição, não o PID** | PID a 4 kHz × 6 eixos × 25 FLOP = 600 000 FLOP/s ≈ **0,4 %** de um núcleo a 160 MHz. Em paralelo, 12 leituras de corrente a 2,4 µs consomem **28,8 µs dos 50 µs** do período (57,6 %) | **[CALC §9.1]**; 160 MHz de `fase2_simulacao/verilog/pwm_deadtime.v` cabeçalho; 240 MHz e 5,54 CoreMark/MHz de `datasheets/esp32-s3_datasheet_en.pdf` | Se alguém otimizar o PID achando que ele é o problema, perde tempo. O que tem de ser otimizado é o disparo do ADC, o *buffering* por DMA e a prioridade das tarefas. | 🟢 Média (o risco é de *alocação de esforço*) |
| **RF-13** | **Brownout do MCU passa por dentro do firmware** | Pico de TX WiFi 0,50 A sobre um buck de 3,3 V dimensionado para 1,50 A (folga 2,9×) | `fase0_especificacao/FASE0_ESPECIFICACAO.md` §7; `fase4_entrega/RISCOS.md` R-09 | O firmware tem de **registrar o motivo do reset** para distinguir brownout de watchdog — já é uma das 10 ações de `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §6 item 8. Sem isso, um brownout em voo é indistinguível de um travamento. | 🟡 Alta |
| **RF-14** | **O dead-time dos motores 3 e 4 tem piso de 400 ns — 118,75 ns abaixo do RTL** | `DT` = **mín 400 / typ 520 / máx 650 ns**, especificado a `VBIAS` (VCC, VBS) = 15 V, `CL` = 1000 pF, `TA` = 25 °C. O layout alimenta o `VCC` dos 12 drivers em **12 V** (pin 1 = `12V`), **abaixo** do ponto de caracterização, e as Figuras 11A/11B mostram o dead-time variando com temperatura e com tensão | `datasheets/ir2104_infineon_datasheet.pdf` p. 3 (tabela *Dynamic Electrical Characteristics*) e p. 8 (Figuras 11A e 11B) **[DATASHEET]**; 12 V em `fase3_pcb/gera_pcb_v7.py` linha 239 **[MEDIDO]**; 518,750 ns em `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2 **[MEDIDO]** | Pelo próprio RF-05, esse é o **único** dead-time dos motores 3 e 4. O piso garantido de **400 ns é 118,75 ns (22,89 %) menor** que os **518,750 ns** do RTL — então o firmware **não pode** derivar o orçamento de dead-time dos 6 pinos de LEDC do valor do RTL: no pior caso ele **sobrestima** a proteção. Nenhum ajuste de software fecha isso. **Mitigação** (nenhuma delas é de firmware): (a) **medir o dead-time real de um motor em bancada** e usar o valor medido, não o de projeto, antes de qualquer voo; (b) usar as resistências de gate `Rgo`/`Rgf` já presentes no layout (`fase3_pcb/gera_pcb_v7.py` linha 236) para limitar a corrente e o `dI/dt` de comutação, que é o mecanismo que converte dead-time curto em condução cruzada; (c) se a medição ficar abaixo do aceitável, mover os motores 3 e 4 para MCPWM e reduzir a contagem de motores por placa. | 🟡 Alta |

### 7.2 RF-01 em detalhe: a conta que fecha

Comando executado nesta máquina (saída na §9.1):

```
Canais por CI (1 motor) = 3 corrente + 3 BEMF = 6      → fase3_pcb/gera_pcb_v7.py:382-385
Requisito do firmware   = 1 leitura por canal por período de 20 kHz
                           → 6 × 20 000 = 120 000 conversões/s por CI
Throughput do MCP3208   = 100 ksps a 5 V / 50 ksps a 2,7 V
                           → datasheets/mcp3208_microchip_ds21298e.pdf
120 ksps ÷ 100 ksps     = 120 %   (melhor caso, VDD = 5 V)
120 ksps ÷  50 ksps     = 240 %   (a 2,7 V)
```

O layout alimenta os MCP3208 com **3,3 V** (linhas 389–390), condição intermediária que o
datasheet **não especifica** — logo o número real é desconhecido e fica **entre** 50 e 100 ksps,
e ainda assim abaixo dos 120 ksps exigidos.

**A saída de software que fecha o gargalo é o *round-robin*:** os 4 MCP3208 são lidos **um por
período de PWM**, escalonados. Cada motor é amostrado a 20 kHz ÷ 4 = **5 kHz**, e cada CI
passa a precisar de 6 × 5 kHz = **30 ksps** — abaixo dos 50 ksps garantidos a 2,7 V, com 40 % de
folga, e com `fCLK = 20 × fSAMPLE` = **0,60 MHz** bem dentro do que o MCP3208 aceita.

O custo dessa escolha, que precisa estar escrito no documento: a BEMF passa a 5 kHz por motor.
Com a premissa P-01 (2207 1750 KV, 6S 22,2 V → 38 850 rpm teóricos **[CALC §9.1]**), a
frequência elétrica dá:

| Pares de polos | f elétrica | Amostras de BEMF por ciclo elétrico a 5 kHz |
|---:|---:|---:|
| 7 (14N14P) | 4 532 Hz | 1,10 |
| 11 (22N22P) | 7 122 Hz | **0,70** |
| 14 (28N28P) | 9 065 Hz | **0,55** |

O número de polos **não foi informado** (pergunta 1 da §11 da Fase 0, sem resposta). Em qualquer
um dos três casos fica **abaixo de 1 amostra por ciclo elétrico** — que é o mínimo para comutar
sem sensor. Ou seja: **com 4× MCP3208, a comutação sem sensor em regime de cruzeiro não fecha.**
O firmware entregável com este hardware é ESC de **duty com sentido definido** (não sensorless),
e isso tem de estar escrito na especificação, não descoberto em voo.

### 7.3 RF-03 em detalhe: por que o `duty = 0` do RTL é perigoso

O RTL, medido e correto, diz que com `duty_i = 0` o canal não gera pulso e **o `lo` fica ligado**
(`fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2). Isso é a física de um half-bridge em *chopping* sincronizado, e é
inofensivo no modelo. Mas o hardware é o **IR2104**, um driver *single-input* que gera o
complementar e o dead-time internamente. E o layout **amarra o `SD` em 3V3 por 10 kΩ**
(`fase3_pcb/gera_pcb_v7.py` linha 238), sem rota para o MCU.

Três consequências que precisam virar decisão de hardware antes do firmware:

1. **Não existe "corta tudo" por software.** O firmware pode zerar o duty, mas não pode desligar
   os drivers. Num quadricóptero, com dois low-sides do mesmo motor ligados, a fase está em curto
   sobre o barramento de 19,8–25,2 V.
2. **O firmware tem de ser escrito contra o datasheet do IR2104, não contra o RTL.** O datasheet
   **está no disco** (`datasheets/ir2104_infineon_datasheet.pdf`, p. 1 *features* e p. 3 *Dynamic
   Electrical Characteristics*), então a instrução é acionável e não uma recomendação vaga
   **[DATASHEET]**. A semântica de repouso do modelo e a do driver divergem, e o modelo é o que
   foi verificado — então a divergência é o risco.
3. **A proteção de R-01 (shoot-through) deixa de ter a camada de software.** A mitigação que
   `fase4_entrega/RISCOS.md` R-01 creditou ao RTL — *"garantia estrutural no RTL"* — **não
   existe no produto final**, porque o RTL não está no produto final.

### 7.4 RF-04 em detalhe: a mitigação declarada que não está na placa

`fase4_entrega/RISCOS.md` R-08 (Perda de link, severidade 🔴) lista como mitigação: *"Watchdog
externo **opcional** no BOM"*. `fase0_especificacao/FASE0_ESPECIFICACAO.md` §8 previa
*"Watchdog externo — GPIO48 (feed) — opcional: corte de motores independente do firmware"*.
No layout v7 existe o pino de *feed* e o test point — **e nenhum circuito**. A mitigation
declarada não foi implementada, e o plano de bancada (`fase4_entrega/PLANO_TESTE_BANCADA.md`
passo 15) continua exigindo que o failsafe *"testa e corta os motores"*.

### 7.5 O que eu **não** consigo fechar nesta máquina

1. **Nenhuma validação em bancada existe** — nem PWM, nem dead-time, nem corrente, nem failsafe
   (`fase4_entrega/RISCOS.md` §5 item 1). Todo critério de aceite da §5 é um **critério
   projetado**, não um resultado.
2. **Throughput do MCP3208 a 3,3 V** — não é especificado no datasheet que está no disco, e não é
   medível sem bancada (RF-06).
3. **Contagem de pinos por *GPIO matrix* do MCPWM/LEDC** — `fase0_especificacao/FASE0_ESPECIFICACAO.md`
   §8 afirma que *"qualquer GPIO pode ser roteado para MCPWM/LEDC pelo GPIO matrix"*, e isso é
   `[PREMISSA]`: o TRM da Espressif **não está no disco**. Dado que RF-07 mostra os pinos
   divergirem entre a §8 e o layout, este é o número que mais precisa de conferência antes de
   escrever a primeira linha de PWM.
4. **Tempo real de execução do laço de PID** — a conta de FLOPs da RF-12 é estimativa de primeira
   ordem, não medição. O número real de ContextMark por núcleo do ESP32-S3 é 1 330
   (5,54 CoreMark/MHz × 240 MHz, `datasheets/esp32-s3_datasheet_en.pdf`), mas converter FLOP em
   CoreMark exigiria um benchmark no silício, que não existe aqui.

---

## 8. DECISÕES QUE SÓ O DONO DO PRODUTO PODE TOMAR

Nenhuma delas é técnica; todas mudam o escopo. As três primeiras estão **bloqueando**.

| # | Decisão | Por que bloqueia | O que a resposta muda |
|---:|---|---|---|
| 1 | **Trocar o ADC externo?** (RF-01, RF-02, RF-11) | 4× MCP3208 não sustentam a amostragem sincronizada que a Fase 0 §4.5 exige, e não têm amostragem simultânea | Trocar por 2× ADS7953 (16 ch cada, 1 Msps) fecha RF-01 e RF-02 e devolve comutação sem sensor; custa **+US$ 5,60**, e não +US$ 8,00 — a conta é 2 × US$ 8,00 = **US$ 16,00** contra 4 × US$ 2,60 = **US$ 10,40** dos 4× MCP3208 que estão no layout, com os preços unitários vindos de `orcamento/ORCAMENTO.md` linhas 68–69 e 134 (que compara 1× ADS7953 contra 2× MCP3208 = 8,00 − 5,20 = +2,80) **[EST]**, a extrapolação para 2× e 4× sendo minha. O BOM só tem 1 ADS7953, então o segundo CI também precisa entrar. E **é uma respin** (`fase4_entrega/RISCOS.md` R-11 já avisa que a v7 ainda tem nets em aberto) |
| 2 | **Rotar o `SD` dos 12 drivers para um GPIO** (RF-03) | Sem isso não existe corte de gate por software | Acrescenta 1 pino e 1 net ao layout; é a correção mais barata e a mais séria |
| 3 | **Fazer o watchdog externo que o R-08 já dá como mitigação** (RF-04) | Sem ele, um travamento do firmware deixa os motores no último duty | Acrescenta 1 CI supervisor + 1 pino; fecha a mitigação que a Fase 4 declarou |
| 4 | **O firmware entra no escopo? (§6.3)** | Define se a entrega é placa ou drone | A = 0 h · B = 160 h · C = 320 h |
| 5 | **Prazo de link do failsafe** — a pergunta 9 da §11 da Fase 0 (*"Prazo de link aceitável para o failsafe (sugero 200 ms)?")* segue **sem resposta** desde 2026-09-11 | Define o que o M10 implementa | 200 ms (o padrão de `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §5.3) ou outro |
| 6 | **Comutação sem sensor ou duty com sentido definido?** (§7.2) | Define se o M8 é comutação por BEMF ou duty | Com BEMF em 0,55–1,10 amostras por ciclo elétrico, a resposta honesta é a segunda |
| 7 | **Número de polos do motor** — pergunta 1 da §11 da Fase 0, sem resposta | Define a f elétrica e, portanto, a viabilidade do item 6 | Muda a conta de 4 532 / 7 122 / 9 065 Hz da §7.2 |

---

## 9. REPRODUTIBILIDADE

### 9.1 Comandos executados nesta máquina (saídas reais)

**Confirmação de que não há firmware:**

```console
$ cd /opt/jupyter/work/drone
$ find . -type f \( -name '*.c' -o -name '*.cpp' -o -name '*.cc' -o -name '*.h' \
      -o -name '*.hpp' -o -name '*.ino' -o -name '*.ld' -o -name 'CMakeLists.txt' \
      -o -name 'Makefile' -o -name 'platformio.ini' -o -name '*.S' -o -name '*.s' \)
EXIT_FIND=0            # saída vazia: nenhum arquivo encontrado
$ find . -type f \( -name '*.c' -o -name '*.cpp' -o -name '*.h' -o -name '*.ino' \
      -o -name 'CMakeLists.txt' -o -name '*.ld' \) | wc -l
0
```

**Ausência de CPLD/FPGA no layout e de watchdog externo:**

```console
$ grep -c -i "cpld\|fpga\|lattice\|altera" fase3_pcb/gera_pcb_v7.py
0
$ grep -n "WD_FEED" fase3_pcb/gera_pcb_v7.py
406:    "22": "PWM_M402", "23": "ADC_CS1", "24": "IMU_INT", "25": "WD_FEED",
444:                   ("TP_3V3A", "3V3_A", 114), ("TP_GND", "GND", 120), ("TP_WD", "WD_FEED", 126),
$ grep -c "U_WD\|MAX706\|TPS3813\|watchdog" fase3_pcb/gera_pcb_v7.py
0
```

**Gargalo do MCP3208 e do barramento SPI:**

```console
$ python3 -c "CH_CI=6; FSW=20000; TPS_5V=100000; TPS_27V=50000; ..."
requisito 1 leitura/canal/periodo PWM: 120 ksps por CI
  vs 100 ksps (VDD=5V)   : VIOLA em 120 %
  vs  50 ksps (VDD=2,7V) : VIOLA em 240 %
round-robin: 1 motor por periodo de PWM (4 motores) -> 5000 Hz por canal
   20000 Hz/canal ->  120.0 ksps/CI | fCLK=20x =   2.40 MHz | VIOLA a 2,7V
   10000 Hz/canal ->   60.0 ksps/CI | fCLK=20x =   1.20 MHz | VIOLA a 2,7V
    5000 Hz/canal ->   30.0 ksps/CI | fCLK=20x =   0.60 MHz | OK a 2,7V
    2500 Hz/canal ->   15.0 ksps/CI | fCLK=20x =   0.30 MHz | OK a 2,7V
```

```console
$ python3 -c "CH_EXT=24; FSW=20000; ..."
amostras/s agregadas      = 480000
clocks SPI/s necessarios  = 11520000
  SCK   4.0 MHz -> ocupacao do bus  288.0 %
  SCK   8.0 MHz -> ocupacao do bus  144.0 %
  SCK  10.0 MHz -> ocupacao do bus  115.2 %
  SCK  20.0 MHz -> ocupacao do bus   57.6 %
  SCK  40.0 MHz -> ocupacao do bus   28.8 %
```

**Frequência elétrica com a premissa P-01:**

```console
$ python3 -c "KV=1750; VNOM=22.2; ..."
P-01 2207 1750 KV x 22.2 V -> 38850 rpm (teorico, sem carga)
  7 pares de polos -> f_eletrica =   4532 Hz  (amostra BEMF a 5000 Hz/canal = 1.10 amostras por ciclo eletrico)
 11 pares de polos -> f_eletrica =   7122 Hz  (amostra BEMF a 5000 Hz/canal = 0.70 amostras por ciclo eletrico)
 14 pares de polos -> f_eletrica =   9065 Hz  (amostra BEMF a 5000 Hz/canal = 0.55 amostras por ciclo eletrico)
```

**Orçamento de CPU e contagem de canais:**

```console
$ python3 -c "CLK=240e6; T=50e-6; ..."
ciclo de CPU por periodo de PWM (50 us @240 MHz) = 12000
12 leituras de corrente a 2,4 us  -> 28.8 us = 6912 ciclos de CPU
PID 1 kHz -> periodo 1000 us = 240000 ciclos de CPU por iteracao
PID 4 kHz -> periodo 250 us = 60000 ciclos de CPU por iteracao
CoreMark por nucleo = 1330 (datasheet 2.2: 5,54 CoreMark/MHz x 240 MHz; 1329,92 nos dois)
canais analogicos: 26 necessarios (F0 4.2) vs 20 maximos no S3 -> faltam 6
```

**Extração dos datasheets que estão no disco:**

```console
$ pdftotext -layout datasheets/mcp3208_microchip_ds21298e.pdf /tmp/mcp3208.txt
  "100 ksps max. sampling rate at VDD = 5V"
  "50 ksps max. sampling rate at VDD = 2.7V"
  "Conversion Time  tCONV  — — 12 clock cycles"
  "Throughput Rate  fSAMPLE — — 100 ksps  VDD = VREF = 5V"
                         —  —  50 ksps  VDD = VREF = 2.7V"
$ pdftotext -layout datasheets/esp32-s3_datasheet_en.pdf /tmp/s3.txt
  "LED PWM controller, up to 8 channels"
  "Two 12-bit SAR ADCs, up to 20 channels"
  "Two Motor Control PWM (MCPWM)"
  "Clock speed: up to 240 MHz"
  "ESP32-S3 integrates two MCPWMs ... Each MCPWM peripheral has one clock divider
   (prescaler), three PWM timers, three PWM operators, and a capture module."
$ pdftotext -layout datasheets/ir2104_infineon_datasheet.pdf /tmp/ir.txt
$ grep -n -i 'deadtime' /tmp/ir.txt
17:  Internally set deadtime         Deadtime (typ.)    520 ns                    <- p.1, features
113: DT  Deadtime, LS turn-off to HS turn-on &   400     520    650             <- p.3, Dynamic Elec. Char.
255: Figure 4. Deadtime Waveform Definitions
456: Deadtime (ns)
458: Deadtime (ns)
478: Figure 11A. Deadtime vs Temperature   Figure 11B. Deadtime vs Voltage       <- p.8
$ pdfinfo datasheets/ir2104_infineon_datasheet.pdf | grep -i pages
Pages:          14
$ for p in $(seq 1 14); do r=$(pdftotext -layout -f $p -l $p datasheets/ir2104_infineon_datasheet.pdf - | grep -c "Figure 11"); echo "p$p: $r"; done
p1: 0
p2: 0
p3: 0
p4: 0
p5: 0
p6: 0
p7: 0
p8: 1
p9: 0
p10: 0
p11: 0
p12: 0
p13: 0
p14: 0
$ stat -c '%n %s bytes' datasheets/ir2104_infineon_datasheet.pdf
datasheets/ir2104_infineon_datasheet.pdf 142488 bytes
$ stat -c '%y' datasheets/ir2104_infineon_datasheet.pdf
2026-09-27 23:50:19.315519303 -0300
$ git log --diff-filter=A --format='%H %ad %s' --date=iso -- plano/WP4_FIRMWARE.md
9784e2e5b78ff1e29dc40647a807c7cfa90bac20 2026-09-28 00:17:27 -0300 docs: WP1 auditoria de roteamento da Fase 3
$ python3 -c "import datetime; a=datetime.datetime(2026,9,27,23,50,19); b=datetime.datetime(2026,9,28,0,17,27); print('delta =', int((b-a).total_seconds()//60), 'min')"
delta = 27 min
$ grep -n '"1": "12V"' fase3_pcb/gera_pcb_v7.py
239:        setnets("U%s" % t, {"1": "12V", "2": "PWM_%s" % t, "3": "SD%s" % t, "4": "GND",
$ python3 -c "print('delta min vs RTL = %.2f ns (%.2f %%)' % (518.75-400,(518.75-400)/518.75*100));
           print('2x ADS7953 = %.2f ; 4x MCP3208 = %.2f ; delta = +%.2f' % (2*8.00, 4*2.60, 2*8.00-4*2.60))"
delta min vs RTL = 118.75 ns (22.89 %)
2x ADS7953 = 16.00 ; 4x MCP3208 = 10.40 ; delta = +5.60
```

### 9.2 Soma dos efforts

```console
$ python3 -c "h={...14 módulos...}; t=sum(h.values()); ..."
total escopo minimo = 320 h
subtotal firmware de bancada (M0-M6 + M10 + M11) = 160 h
voo completo = 320 h = 40 dias de 8 h = 8.0 semanas de 40 h
sem o firmware de bancada sobram 160 h de desenvolvimento de voo
```

### 9.3 Conferência de todos os caminhos citados neste documento

**Critério de extração, declarado para que a conferência não seja auto-referente.** Neste
documento um caminho só conta como *citado* se cumprir as três regras abaixo, e o comando de
conferência aplica as três:

1. está **entre crases** (`caminho`) — é a convenção de citação de arquivo do §0;
2. está no **texto corrido**: o comando remove antes tudo o que está dentro de bloco cercado por
   cercas (os exemplos de shell e as saídas de console), de modo que o bloco onde o próprio
   comando mora **não pode se citar**;
3. é um caminho **relativo à raiz do projeto** (`/opt/jupyter/work/drone`), nunca absoluto.

Com esse critério, o comando abaixo foi executado nesta máquina e testou cada caminho extraído
contra a raiz do projeto:

```console
$ cd /opt/jupyter/work/drone
$ awk '/^```/{f=!f; next} !f' plano/WP4_FIRMWARE.md \
    | grep -oE '`[A-Za-z0-9_./-]+\.(md|txt|csv|png|v|log|vcd|py|cir|pdf|kicad_pcb|json|ini)`' \
    | tr -d '`' | sort -u > /tmp/wp4_caminhos.txt
$ for p in $(cat /tmp/wp4_caminhos.txt); do
>   test -e "/opt/jupyter/work/drone/$p" && echo "OK   $p" || echo "FALTA $p"
> done > /tmp/wp4_val.txt
$ echo "OK: $(grep -c '^OK' /tmp/wp4_val.txt)  FALTA: $(grep -c '^FALTA' /tmp/wp4_val.txt)  TOTAL: $(wc -l < /tmp/wp4_val.txt)"
OK: 44  FALTA: 0  TOTAL: 44
```

**Resultado apurado: 44 caminhos testados, 44 existem, 0 inexistente.** A lista completa, com o
resultado do `test -e` de cada um, está na §10 deste arquivo — 44 linhas, uma por caminho, na
mesma ordem que o comando acima produz. O total subiu de 42 para 44 em 2026-09-28 porque dois
caminhos que **já eram citados** no texto passaram a ser escritos entre crases, em vez do truque
de escrevê-los sem crase para não alterar a contagem (ver §12.5, C1).

**Por que uma varredura sem exigir as crases dá 8 falsos positivos.** Um `grep` que casa a
extensão sem exigir as crases pega também o **texto do próprio exemplo de comando**: nomes de
arquivo de um projeto ESP-IDF hipotético e arquivos temporatórios do `/tmp`, que nunca foram
caminhos do projeto. Medido nesta máquina **sobre a versão anterior deste arquivo** (commit
`35c1177`, o estado que o verificador mediu) — a varredura frouxa roda sobre o arquivo
extraído com `git show` (o /tmp/wp4_antes.md do exemplo), e não sobre este arquivo, porque
aplicá-la aqui faria ela varrer esta própria demonstração, que é justamente o defeito:

```console
$ git show 35c1177:plano/WP4_FIRMWARE.md > /tmp/wp4_antes.md
$ for p in $(grep -oE '[A-Za-z0-9_./-]+\.(md|txt|csv|png|v|log|vcd|py|cir|pdf|kicad_pcb|json|ini)' /tmp/wp4_antes.md | tr -d '` ' | sort -u); do test -e "/opt/jupyter/work/drone/$p" && echo "OK   $p" || echo "FALTA $p"; done > /tmp/wp4_frouxo.txt
$ echo "OK: $(grep -c '^OK' /tmp/wp4_frouxo.txt)  FALTA: $(grep -c '^FALTA' /tmp/wp4_frouxo.txt)  TOTAL: $(wc -l < /tmp/wp4_frouxo.txt)"
OK: 44  FALTA: 8  TOTAL: 52
$ grep '^FALTA' /tmp/wp4_frouxo.txt
FALTA CMakeLists.txt
FALTA h.v
FALTA idf.py
FALTA platformio.ini
FALTA /tmp/ir.txt
FALTA /tmp/mcp3208.txt
FALTA /tmp/s3.txt
FALTA /tmp/val2.txt
$ sort /tmp/wp4_caminhos.txt > /tmp/wp4_estrito.txt
$ grep '^OK' /tmp/wp4_frouxo.txt | sed 's/^OK   //' | sort > /tmp/wp4_frouxo_ok.txt
$ echo "caminhos reais que a frouxa perdeu: $(comm -23 /tmp/wp4_estrito.txt /tmp/wp4_frouxo_ok.txt | wc -l)"
caminhos reais que a frouxa perdeu: 0
$ echo "OK da frouxa fora do estrito: $(comm -13 /tmp/wp4_estrito.txt /tmp/wp4_frouxo_ok.txt | wc -l)"
OK da frouxa fora do estrito: 0
```

Os 8 são artefato do comando, não citações: CMakeLists.txt, h.v, idf.py e platformio.ini estão
dentro de `-o -name '...'` no `find` da §9.1 que prova que **não há** firmware nenhum no projeto
— são extensões do que a busca procurava; e ir.txt, mcp3208.txt, s3.txt e val2.txt são arquivos
temporários de `pdftotext` e da própria conferência, fora da árvore do projeto. O essencial está nas duas últimas linhas
de `comm`: os 44 `OK` da varredura frouxa são **exatamente** os 44 caminhos que o comando da
§9.3 lista hoje — a frouxa erra ao **incluir** 8 artefatos, e não ao excluir nenhum caminho real.

---

## 10. ÍNDICE DE CAMINHOS CITADOS NESTE DOCUMENTO

Gerado pelo **mesmo comando da §9.3**, sem critério próprio: são **44 linhas, uma por caminho
extraído** — caminho entre crases, no texto corrido (fora de bloco cercado por cercas), relativo à
raiz do projeto. A tabela abaixo está na ordem exata que o `sort -u` produziu, e o ✅ é o
`test -e` real contra `/opt/jupyter/work/drone/<caminho>`.

| Caminho | `test -e` |
|---|---|
| `PROMPT_AGENTE_DRONE.md` | ✅ |
| `README.md` | ✅ |
| `datasheets/esp32-s3_datasheet_en.pdf` | ✅ |
| `datasheets/ir2104_infineon_datasheet.pdf` | ✅ |
| `datasheets/mcp3208_microchip_ds21298e.pdf` | ✅ |
| `fase0_especificacao/FASE0_ESPECIFICACAO.md` | ✅ |
| `fase0_especificacao/diagrama_blocos_fase0_v3.png` | ✅ |
| `fase0_especificacao/diagrama_blocos_v3.py` | ✅ |
| `fase0_especificacao/dimensionamento_fase0.py` | ✅ |
| `fase0_especificacao/dimensionamento_fase0_saida_v2.txt` | ✅ |
| `fase0_especificacao/lista_componentes_fase0.csv` | ✅ |
| `fase0_especificacao/verifica_limites_entrada_v4.py` | ✅ |
| `fase1_esquema/esq7_mcu.png` | ✅ |
| `fase2_simulacao/RESULTADOS_FASE2_SPICE.md` | ✅ |
| `fase2_simulacao/gera_tabela.py` | ✅ |
| `fase2_simulacao/minimiza_ripple.py` | ✅ |
| `fase2_simulacao/verilog/RELATORIO_VERILOG.md` | ✅ |
| `fase2_simulacao/verilog/compile.log` | ✅ |
| `fase2_simulacao/verilog/plot_pwm.py` | ✅ |
| `fase2_simulacao/verilog/pwm_deadtime.png` | ✅ |
| `fase2_simulacao/verilog/pwm_deadtime.v` | ✅ |
| `fase2_simulacao/verilog/tb_pwm.log` | ✅ |
| `fase2_simulacao/verilog/tb_pwm.v` | ✅ |
| `fase2_simulacao/verilog/tb_pwm.vcd` | ✅ |
| `fase2_simulacao/verilog/yosys.log` | ✅ |
| `fase2_simulacao/verilog/yosys_stat.log` | ✅ |
| `fase3_pcb/gera_pcb_v1.py` | ✅ |
| `fase3_pcb/gera_pcb_v7.py` | ✅ |
| `fase3_pcb/rota_v7.py` | ✅ |
| `fase3_pcb/v6/verificacao_v6.txt` | ✅ |
| `fase3_pcb/v7/v7_drone.kicad_pcb` | ✅ |
| `fase3_pcb/verifica_fase3_v6.py` | ✅ |
| `fase4_entrega/ANALISE_WIFI_CONTROLE.md` | ✅ |
| `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` | ✅ |
| `fase4_entrega/PLANO_TESTE_BANCADA.md` | ✅ |
| `fase4_entrega/RISCOS.md` | ✅ |
| `fase4_entrega/SEGURANCA_E_REGULATORIO.md` | ✅ |
| `fase4_entrega/calcs_wifi_controle.txt` | ✅ |
| `orcamento/ORCAMENTO.md` | ✅ |
| `orcamento/orcamento.py` | ✅ |
| `orcamento/orcamento_detalhado.csv` | ✅ |
| `plano/mede_v7_wp1.py` | ✅ |
| `plano/WP1_ROTEAMENTO.md` | ✅ |
| `plano/WP4_FIRMWARE.md` | ✅ |
---

## 11. O QUE ESTE DOCUMENTO **NÃO** É

1. **Não é firmware.** Nenhuma linha de código de voo foi escrita. O §5 descreve o que precisa
   existir, não o que existe.
2. **Não é validação.** Nenhum número aqui veio de bancada. Todos os critérios de aceite da §5
   são **projetados** — o que `fase4_entrega/RISCOS.md` §5.1 reforça: *"Nenhum risco foi
   observado ocorrer. Zero bancada, zero voo, zero termopar."*
3. **Não mexe em nenhum arquivo existente**, inclusive no `LICENSE` nem no `README.md`. Este arquivo é o único criado. O `README.md` não
   foi alterado (§6.4 item 2 registra a pendência em vez de executá-la).
4. **Não fecha o `fase4_entrega/RISCOS.md`.** Acrescentei RF-01 a RF-14, que são de firmware; os riscos
   R-01 a R-22 de `fase4_entrega/RISCOS.md` continuam abertos e não editados.
5. **Não substitui o TRM.** Três números continuam `[N/D offline]`: throughput do MCP3208 a 3,3 V
   (RF-06), a exclusão ADC2×WiFi e a contagem de pinos por *GPIO matrix* (§7.5 item 3).

---

## 12. CORREÇÕES APÓS VERIFICAÇÃO ADVERSARIAL (2026-09-28)

Duas falhas reais foram encontradas neste documento depois de escrito. As duas estão corrigidas
aqui; o resto do texto não foi reescrito.

### 12.1 RF-05 classificava o dead-time do IR2104 como premissa, com um datasheet no disco

**O que estava errado.** O RF-05 dizia: *"Os motores 3 e 4 dependem **inteiramente** do dead-time
interno do IR2104 (~520 ns, rotulado como premissa, sem datasheet no disco para confirmar)."*

**Por que estava errado.** `datasheets/ir2104_infineon_datasheet.pdf` tem **142 488 bytes** no disco
e o `mtime` do arquivo é `2026-09-27 23:50:19` — **o datasheet já estava no disco antes de este
documento ser escrito e commitado**. (Uma versão anterior deste texto afirmava *"11 minutos antes"*;
essa precisão foi removida em 2026-09-28 — ver §12.4, C3: o intervalo real apurado pelo `git` é de
**27 minutos**, e a §9 não continha nenhum comando que sustentasse os 11.) O valor de catálogo não
era premissa: é dado de catálogo.

**O que mudou.**

1. A etiqueta `[PREMISSA]` → **`[DATASHEET]`**, com arquivo e página: p. 1, *features*, *"Internally set
   deadtime — Deadtime (typ.) 520 ns"*; p. 3, *Dynamic Electrical Characteristics*, símbolo `DT` =
   **400 / 520 / 650 ns**. Comandos e saídas na §9.1.
2. **O mínimo de 400 ns virou risco próprio (RF-14).** Pelo próprio RF-05 esse é o **único**
   dead-time dos motores 3 e 4, e 400 ns é **menor** que os 518,750 ns do RTL: **−118,75 ns,
   −22,89 %**. Isso **rebaixa** o RF-05, que foi de 🟡 Alta para **🟢 Média** — a proteção contra
   condução cruzada existe nos 4 motores, ela simplesmente não é programável pelo firmware — e
   **eleva o resíduo**, que agora é um risco nomeado com mitigação: medir o dead-time real em
   bancada, usar as resistências de gate `Rgo`/`Rgf` já no layout para limitar `dI/dt`, ou mover
   os motores 3 e 4 para MCPWM. A RF-14 registra também que os drivers rodam a **12 V**
   (`fase3_pcb/gera_pcb_v7.py` linha 239), **abaixo** dos 15 V de caracterização do datasheet, cujas
   Figuras 11A/11B mostram o dead-time variando com tensão e temperatura.
3. **Contradição do §7.3 resolvida.** O item 2 mandava escrever o firmware *"contra o datasheet do
   IR2104"* enquanto o §7.1 afirmava que esse datasheet não existia. Agora o item 2 cita o caminho e
   a página, então a instrução ficou acionável em vez de genérica.
4. A §11 item 4 passou de *"RF-01 a RF-13"* para *"RF-01 a RF-14"*.

### 12.2 §8 tinha um custo de ADC sem fonte

**O que estava errado.** A decisão nº 1 da §8 dizia que trocar por 2× ADS7953 *"custa +US$ 8,00"*.
Esse número não corresponde a nenhuma leitura possível de `orcamento/ORCAMENTO.md`, que traz
US$ 8,00 como preço **unitário de 1** ADS7953 (linha 68) e enquadra o delta contra a alternativa
como `8,00 − 5,20 = +2,80` (linha 134, sobre 2× MCP3208).

**O que mudou.** A conta foi refeita na escala correta, que é a do layout (4× MCP3208 = 32 canais
contra 2× ADS7953 = 32 canais): `2 × 8,00 = 16,00` contra `4 × 2,60 = 10,40`, delta
**+US$ 5,60**. Marcado como **`[EST]`**, porque a extrapolação de 1→2 e de 2→4 CIs é minha — os
preços unitários vêm de `orcamento/ORCAMENTO.md` linhas 68–69 e 134. O texto registra também que o
+US$ 2,80 do orçamento é a comparação de 16 canais, não a de 32, e que o BOM tem só 1 ADS7953, então
o segundo CI também precisa entrar.

### 12.3 Efeito colateral honesto na contagem de caminhos

Citar o datasheet (§12.1) acrescentou **1 caminho** ao documento. A conferência da §9.3 é
**re-executada**, nunca editada à mão — o comando abaixo é o da §9.3 e a saída é a de hoje
(quando a §12.5 foi escrita o total era 42):

```console
$ cd /opt/jupyter/work/drone
$ awk '/^```/{f=!f; next} !f' plano/WP4_FIRMWARE.md \
    | grep -oE '`[A-Za-z0-9_./-]+\.(md|txt|csv|png|v|log|vcd|py|cir|pdf|kicad_pcb|json|ini)`' \
    | tr -d '`' | sort -u > /tmp/wp4_caminhos.txt
$ for p in $(cat /tmp/wp4_caminhos.txt); do
>   test -e "/opt/jupyter/work/drone/$p" && echo "OK   $p" || echo "FALTA $p"
> done > /tmp/wp4_val.txt
$ echo "OK: $(grep -c '^OK' /tmp/wp4_val.txt)  FALTA: $(grep -c '^FALTA' /tmp/wp4_val.txt)  TOTAL: $(wc -l < /tmp/wp4_val.txt)"
OK: 44  FALTA: 0  TOTAL: 44
```

A propriedade que importa — **todo caminho citado existe** — continua valendo, e agora é verificável
por um critério declarado, não por um número escrito à mão; o total foi de 41 para 42 com a
correção do RF-05 e depois para 44 com a §12.5. A §0, a §9.3 e a §10 foram atualizadas junto.
Nenhum outro número do documento foi tocado: 13 → 14 riscos (um rebaixado, um criado), e os 12
canais, os 518,750 ns, os 20 kHz e as 320 h intactos.

### 12.4 Correções round 2 (2026-09-28)

Três correções pontuais, todas verificáveis por comando nesta máquina. O resto do documento — 12
canais, 518,750 ns, 20 kHz, 320 h, RF-01 a RF-14, o inventário sem firmware e a tabela da §10 com 42
caminhos — não foi tocado.

#### C1 — página errada das Figuras 11A/11B na RF-14

**O que estava errado.** A RF-14 e o comentário da §9.1 atribuíam as Figuras 11A/11B à **p. 14** de
`datasheets/ir2104_infineon_datasheet.pdf`. A p. 14 é a *Leadfree Part Marking Information / Order
Information*. As figuras estão na **p. 8**. Era um erro novo, introduzido no reparo anterior — o
`grep` da §9.1 é feito sobre o texto extraído do PDF inteiro e por isso **não produz número de
página**; a anotação `<- p.14` foi escrita à mão, e foi escrita errada.

**Como se confirma.** Varredura página a página contando a ocorrência de `Figure 11`:

```console
$ cd /opt/jupyter/work/drone
$ for p in $(seq 1 14); do r=$(pdftotext -layout -f $p -l $p datasheets/ir2104_infineon_datasheet.pdf - | grep -c "Figure 11"); echo "p$p: $r"; done
p1: 0
p2: 0
p3: 0
p4: 0
p5: 0
p6: 0
p7: 0
p8: 1
p9: 0
p10: 0
p11: 0
p12: 0
p13: 0
p14: 0
```

`p8: 1` e nenhuma outra página — a Figura 11 aparece uma única vez no documento, na **p. 8**. E a
p. 14 confirma o que é:

```console
$ pdftotext -layout -f 8 -l 8 datasheets/ir2104_infineon_datasheet.pdf - | grep -A1 "Figure 11A"
                        Figure 11A. Deadtime vs Temperature             Figure 11B. Deadtime vs Voltage
$ pdftotext -layout -f 14 -l 14 datasheets/ir2104_infineon_datasheet.pdf - | head -5
                        IR2104(S) & (PbF)
                        LEADFREE PART MARKING INFORMATION
                        Part number          IRxxxxxx
                        Date code            YWW?                              IR logo
```

**O que mudou.** `p. 14` → `p. 8` em dois lugares: a coluna de origem da **RF-14** (§7.1) e o
comentário `<- p.14` → `<- p.8` do `grep` na §9.1. A varredura de páginas foi acrescentada à §9.1
como evidência, para que a próxima anotação de página venha de um comando e não da memória.

#### C2 — critério de aceite do M3 incoerente com a RF-14

**O que estava errado.** O M3 (dead-time dos 6 canais de LEDC) dizia *"mesmo critério do M2"*, e o
M2 exige dead-time entre **250 ns e 2 µs**. Isso é irrealizável no M3 por dois motivos ao mesmo
tempo, e a própria RF-14 já os dizia: (a) nos motores 3 e 4 o dead-time é **fixo dentro do
IR2104**, não programável por firmware — vão por LEDC, que não tem dead-time em HW (RF-05), então
nenhum ajuste de software muda o valor; (b) o piso de **250 ns** do critério do M2 fica **abaixo do
mínimo de catálogo de 400 ns** do `DT`. Um critério que não pode ser atingido nem medido não é um
critério de aceite, e medir o dead-time real em bancada é justamente a mitigação (a) da RF-14 — o
critério antigo apontava para a medição errada.

**De onde vêm os dois números.** `DT` na tabela *Dynamic Electrical Characteristics* da p. 3, com
`VBIAS (VCC, VBS) = 15V, CL = 1000 pF and TA = 25°C`:

```console
$ pdftotext -layout -f 3 -l 3 datasheets/ir2104_infineon_datasheet.pdf - | grep -E "VBIAS \(VCC, VBS\) = 15V, CL|^    DT  "
 VBIAS (VCC, VBS) = 15V, CL = 1000 pF and TA = 25°C unless otherwise specified.
    DT       Deadtime, LS turn-off to HS turn-on &                400     520    650
```

400 ns (mín) / 520 ns (typ) / 650 ns (máx). E o layout alimenta o `VCC` dos 12 drivers em **12 V**,
**abaixo** dos 15 V de caracterização — por isso a janela de catálogo 400–650 ns é o que o projeto
tem à disposição, e não uma faixa programável:

```console
$ grep -n '"1": "12V"' fase3_pcb/gera_pcb_v7.py
239:        setnets("U%s" % t, {"1": "12V", "2": "PWM_%s" % t, "3": "SD%s" % t, "4": "GND",
```

**O que mudou.** O critério do M3 passou a ter **duas janelas distintas**, uma por tipo de PWM:

| | Motores 1 e 2 (**MCPWM**) — critério do M2 | Motores 3 e 4 (**LEDC + IR2104**) — critério do M3 |
|---|---|---|
| Onde o dead-time é gerado | MCPWM, **em hardware e programável** (`deadtime_i[15:0]`, 518,750 ns) | **IR2104, interno e fixo** — o firmware não o programa (RF-05) |
| Janela de aceite | **250 ns – 2 µs**, programável pelo firmware | **400 – 650 ns**, conforme o `DT` de catálogo |
| Origem do número | faixa escolhida por projeto | `datasheets/ir2104_infineon_datasheet.pdf` **p. 3** e RF-14 |
| Tensão | — | `VBIAS` do projeto = **12 V**, abaixo dos **15 V** de caracterização |

O texto do M3 agora diz, na íntegra: *"**janela de dead-time própria, diferente da do M2**: 400–650 ns
(piso/máx de catálogo do `DT`, RF-14) e **não** 250 ns–2 µs — nos motores 3 e 4 o dead-time é
**fixo no driver, não programável por firmware**, porque vão por LEDC; período 50 000 ns ± 0,1 %;
defasagem entre grupos medida **90,000° ± 1°**; clamp de duty em 2 % e 95 % verificado"*. O
período, a defasagem e o clamp de duty do M3 ficaram como estavam.

#### C3 — "11 minutos" sem lastro

**O que estava errado.** A §12.1 afirmava que o datasheet foi modificado *"11 minutos antes"* deste
arquivo ser escrito. Não há lastro para os 11: a §9 não tinha nenhum comando que produzisse esse
número, e o `git` mede outra coisa. Entre o `mtime` do datasheet e o commit que **adicionou** o
WP4 vão **27 minutos**.

```console
$ cd /opt/jupyter/work/drone
$ stat -c '%y' datasheets/ir2104_infineon_datasheet.pdf
2026-09-27 23:50:19.315519303 -0300
$ git log --diff-filter=A --format='%H %ad %s' --date=iso -- plano/WP4_FIRMWARE.md
9784e2e5b78ff1e29dc40647a807c7cfa90bac20 2026-09-28 00:17:27 -0300 docs: WP1 auditoria de roteamento da Fase 3
$ python3 -c "import datetime; a=datetime.datetime(2026,9,27,23,50,19); b=datetime.datetime(2026,9,28,0,17,27); print('delta =', int((b-a).total_seconds()//60), 'min')"
delta = 27 min
```

O `commit` é o mesmo que adicionou os arquivos do WP1 — `plano/WP1_ROTEAMENTO.md` e
`plano/mede_v7_wp1.py`, ambos existentes (`test -e` na §10). O WP4 entrou no mesmo commit do WP1, o
que também explica por que o assunto do commit fala em WP1. Até 2026-09-28 esses dois nomes eram
escritos aqui **sem crases**, com a intenção declarada de não mexer na contagem da §10. O truque
não funcionava — ver §12.5, C1.

**O que mudou.** A precisão falsa saiu; o que os dados sustentam ficou, com o comando ao lado:

> ...e o `mtime` do arquivo é `2026-09-27 23:50:19` — **o datasheet já estava no disco antes de
> este documento ser escrito e commitado**. (Uma versão anterior deste texto afirmava *"11 minutos
> antes"*; essa precisão foi removida em 2026-09-28 — ver §12.4, C3: o intervalo real apurado pelo
> `git` é de **27 minutos**, e a §9 não continha nenhum comando que sustentasse os 11.)

A **conclusão** da §12.1 não muda: o RF-05 estava errado ao classificar o dead-time do IR2104 como
premissa, porque o datasheet **estava** no disco antes do documento. Só a precisão sem evidência
saiu. Os comandos de `stat` e `git log` foram acrescentados à §9.1 para que a afirmação daqui
tenha lastro no documento.

### 12.5 Correções round 3 (2026-09-28)

Uma correção só, mas de fundo: a validação da §9.3 era **auto-referente**, e por isso o número que
o documento afirmava — `FALTA: 0` — não era o que o comando produzia. Nada mais do documento foi
tocado: 12 canais, 518,750 ns, 20 kHz, 320 h, RF-01 a RF-14, a C1 (p. 8), a C2 (janelas do M2/M3) e a
C3 (27 min) seguem como estavam.

#### C1 — a conferência de caminhos se citava sozinha

**O que estava errado.** A §9.3 extraía caminhos com um `grep` que exigia crases, mas **não
excluía os blocos de exemplo**. Um verificador independente que varre a versão anterior do arquivo
sem exigir as crases (commit `35c1177`) encontra 8 nomes a mais — todos vindos do texto dos
próprios exemplos de comando — e diverge da tabela da §10 em 2 linhas, para o lado oposto:

```console
$ git show 35c1177:plano/WP4_FIRMWARE.md > /tmp/wp4_antes.md
$ for p in $(grep -oE '[A-Za-z0-9_./-]+\.(md|txt|csv|png|v|log|vcd|py|cir|pdf|kicad_pcb|json|ini)' /tmp/wp4_antes.md | tr -d '` ' | sort -u); do test -e "/opt/jupyter/work/drone/$p" && echo "OK   $p" || echo "FALTA $p"; done > /tmp/wp4_frouxo.txt
$ echo "OK: $(grep -c '^OK' /tmp/wp4_frouxo.txt)  FALTA: $(grep -c '^FALTA' /tmp/wp4_frouxo.txt)  TOTAL: $(wc -l < /tmp/wp4_frouxo.txt)"
OK: 44  FALTA: 8  TOTAL: 52
$ grep '^FALTA' /tmp/wp4_frouxo.txt
FALTA CMakeLists.txt
FALTA h.v
FALTA idf.py
FALTA platformio.ini
FALTA /tmp/ir.txt
FALTA /tmp/mcp3208.txt
FALTA /tmp/s3.txt
FALTA /tmp/val2.txt
$ awk '/^```/{f=!f; next} !f' plano/WP4_FIRMWARE.md \
    | grep -oE '`[A-Za-z0-9_./-]+\.(md|txt|csv|png|v|log|vcd|py|cir|pdf|kicad_pcb|json|ini)`' \
    | tr -d '`' | sort -u > /tmp/wp4_caminhos.txt
$ for p in $(cat /tmp/wp4_caminhos.txt); do test -e "/opt/jupyter/work/drone/$p" && echo "OK   $p" || echo "FALTA $p"; done > /tmp/wp4_val.txt
$ echo "OK: $(grep -c '^OK' /tmp/wp4_val.txt)  FALTA: $(grep -c '^FALTA' /tmp/wp4_val.txt)  TOTAL: $(wc -l < /tmp/wp4_val.txt)"
OK: 44  FALTA: 0  TOTAL: 44
$ wc -l < /tmp/wp4_caminhos.txt
44
```

Duas coisas diferentes estavam erradas, e as duas precisam ser ditas:

1. **Os 8 "FALTA" são artefato do comando, não caminhos do projeto.** CMakeLists.txt, h.v, idf.py
   e platformio.ini aparecem dentro de `-o -name '...'` no `find` da §9.1 que prova que **não há**
   firmware na árvore; ir.txt, mcp3208.txt, s3.txt e val2.txt são temporários de `pdftotext` e da
   própria conferência. Nenhum deles é uma citação de caminho — e nenhum é o que a §10 promete
   indexar.
2. **O truque de "escrever sem crases" não funcionava.** A §12.4 (C3) escrevia
   `plano/WP1_ROTEAMENTO.md` e `plano/mede_v7_wp1.py` sem crases, declarando que era para não
   alterar a contagem. Não alterava: o `tr -d '`'` do verificador só remove crases **depois** do
   casamento do padrão, e um verificador que casa a extensão sem exigir crase pega esses dois
   nomes do mesmo jeito. Resultado: os 2 estavam no disco, existiam, e mesmo assim a tabela da §10
   não os declarava — a tabela subdeclarava por 2, para um total real de 44.

**O que mudou.** Adotada a **abordagem (a)**: a §9.3 agora **declara o critério de extração** em
três regras (entre crases, no texto corrido, relativo à raiz do projeto) e o comando passa a
**descartar os blocos cercados por cercas antes do `grep`**, com um `awk` que alterna um booleano a
cada cerca. Efeito: o comando não consegue mais casar o próprio bloco onde mora, e o resultado
**real** é `OK: 44  FALTA: 0  TOTAL: 44` — 44 caminhos, todos existentes, verificados por
`test -e` contra a raiz do projeto, na ordem que o `sort -u` produz.

Os dois caminhos que estavam sem crases passaram a ser citados **como deve ser**, entre crases, e
entraram na §10 (que agora tem 44 linhas, uma por caminho extraído, e é gerada pelo mesmo
comando — sem critério próprio). A divergência de 2 linhas entre tabela e comando **não existe
mais**: as duas contagens saem do mesmo `sort -u`, o que se confirma comparando a tabela com a
saída do `test -e`, linha a linha:

```console
$ awk '/^```/{f=!f; next} !f' plano/WP4_FIRMWARE.md \
    | grep -oE '`[A-Za-z0-9_./-]+\.(md|txt|csv|png|v|log|vcd|py|cir|pdf|kicad_pcb|json|ini)`' \
    | tr -d '`' | sort -u > /tmp/wp4_caminhos.txt
$ sed -n '/^## 10\./,/^## 11\./p' plano/WP4_FIRMWARE.md \
    | grep -oE '^\| `[A-Za-z0-9_./-]+\.(md|txt|csv|png|v|log|vcd|py|cir|pdf|kicad_pcb|json|ini)`' \
    | sed 's/^| `//; s/`$//' | sort -u > /tmp/wp4_tabela.txt
$ echo "tabela: $(wc -l < /tmp/wp4_tabela.txt) linhas  |  comando: $(wc -l < /tmp/wp4_caminhos.txt) caminhos"
tabela: 44 linhas  |  comando: 44 caminhos
$ diff /tmp/wp4_caminhos.txt /tmp/wp4_tabela.txt && echo "IDENTICAS: nenhuma divergencia entre a §10 e o comando"
IDENTICAS: nenhuma divergencia entre a §10 e o comando
$ while read -r p; do test -e "/opt/jupyter/work/drone/$p" || echo "FALTA $p"; done < /tmp/wp4_tabela.txt; echo "falhas: $(while read -r p; do test -e "/opt/jupyter/work/drone/$p" || echo FALTA; done < /tmp/wp4_tabela.txt | wc -l)"
falhas: 0
```

**Números corrigidos.** Todas as afirmações de contagem do documento foram para o número verdadeiro
— `OK: 42  FALTA: 0  TOTAL: 42` e as quatro frases em volta (a §0, a §9.3, a §12.3 e a C3 da
§12.4) agora dizem **44 caminhos testados, 44 existem, 0 inexistente**, e a passagem "41 → 42
caminhos" virou "41 → 42 → 44". A contagem dos riscos continua **13 → 14**, e o resto dos números
conferidos (12 canais, 518,750 ns, 20 kHz, 320 h, RF-01 a RF-14) não foi tocado.
