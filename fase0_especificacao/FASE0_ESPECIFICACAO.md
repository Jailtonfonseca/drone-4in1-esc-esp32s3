# FASE 0 — ESPECIFICAÇÃO DO DRONE (4x ESC trifásico + MCU WiFi na mesma PCB)

**Projeto:** drone completo em PCB única — 4 inversores trifásicos, gate drivers,
sensoriamento de corrente, MCU com WiFi, IMU, barômetro, USB e toda a regulação de energia.
**Máquina:** Linux aarch64 headless (`/usr/bin/python3.9` + KiCad 5.1.9, ngspice 34, gerbv 2.7.0, iverilog 11).
**Data:** 2026-09-11 · **Pasta:** `fase0_especificacao/`
**Status:** Fase 0 entregue — **aguardando seu OK para a Fase 1**.

---

## 0. Como ler este relatório (obrigatório)

Todo número neste documento tem uma **etiqueta de origem**:

| Etiqueta | Significado |
|---|---|
| **[CALC]** | calculado nesta máquina, por script, com o comando e a saída nos arquivos citados |
| **[PREMISSA]** | suposição declarada (P-01…P-13) que **não** foi confirmada em datasheet nem medida |
| **[N/D offline]** | dado de datasheet que eu **não tenho** neste disco — não foi inventado |
| **[NÃO VERIFICADO]** | não é simulável nem medível nesta máquina (bancada, térmica real, EMI, fabricação) |

Nada aqui foi medido em bancada. **Não existe nenhuma medição experimental neste relatório.**
Todos os números vêm dos três scripts listados abaixo (todos executados com sucesso):

| Script | Saída (log real) | O que produz |
|---|---|---|
| `dimensionamento_fase0.py` | `dimensionamento_fase0_saida_v2.txt` (168 linhas) | estágio de potência, gate drive, shunt, VBAT, bucks, trilhas, orçamento |
| `verifica_limites_entrada_v4.py` | `verifica_limites_saida_v4.txt` | ripple do barramento com PWM resolvido, interleaving, térmica, vias, gate, ADC, balanço |
| `diagrama_blocos_v3.py` | `diagrama_blocos_fase0_v3.png` | diagrama de blocos (imagem conferida com `view_image`) |

Comando executado (exemplo real):
```
$ cd fase0_especificacao && python3 dimensionamento_fase0.py
```
Exemplo de saída real:
```
  Rds_on= 2.0 mOhm -> Irms/FET=15.00 A -> Pcond= 450.0 mW/FET -> 24 FETs =  10.80 W no total
  I_barramento: media =  18.01 A | pico =  30.00 A | RMS(ac) =  13.12 A | I_pk(ac) =  18.01 A
  Conferencia analitica: I_med = (3/4)*m*Ipk = 18.00 A  | erro = 0.042 %
```

---

## 1. O QUE EU PRECISO DE VOCÊ (dados dos motores e do pack)

Você disse que tem os 4 motores e mais nada. Para dimensionar com precisão eu preciso
**exatamente** destes itens — os que não vierem entram como [PREMISSA] e mudam o projeto conforme a §1.3.

### 1.1 Dos motores (crítico)
1. **Modelo / part number** (ex.: 2207 1750 KV, EMAX RS2207…)
2. **KV** (rpm/V) e **número de polos** (ou par de polos) → define frequência elétrica
3. **Resistência de fase** (mΩ) e **indutância de fase** (µH) → define ripple de corrente, perfil de BEMF e tempo de subida de corrente
4. **Corrente contínua** (A) e **corrente de pico** (A) + **duração da rajada** → shunts, MOSFETs, trilhas
5. **Tensão recomendada** (nº de células) e **rpm máximo**
6. Dados da hélice: **diâmetro, passo, nº de pás** → empuxo, corrente de cruzeiro

### 1.2 Da bateria (crítico)
7. **Nº de células (S)** → tensão máxima (define a **classe de Vds do MOSFET** e o partidor de VBAT)
8. **Capacidade (mAh)** e **C-rate** contínuo/pico → corrente máxima do pack
9. **Conector** (XT30/XT60/XT90) e bitola dos cabos

### 1.3 O que muda no projeto se os números reais forem outros

| Se o real for… | O que muda | Onde |
|---|---|---|
| **4S (16,8 V)** | MOSFET 30 V serve; banco 25 V; trilhos mais finos; XT30 | §6, §7 |
| **6S (25,2 V)** *(premissa adotada)* | MOSFET 40–60 V; banco 35 V; XT60/XT90 | §6 |
| **8S–12S (33,6–50,4 V)** | MOSFET 60–100 V; **Vds/Rds sobe** → perdas de condução sobem com Rds maior; precisa checar tensão máx. do gate driver e do buck de 12 V (vin > 30 V); banco 63 V; XT90; isolamento e espaçamento no PCB | §6, §7, Fase 3 |
| **Corrente de pico 60 A/motor** (em vez de 30 A) | shunt cai para ~0,25 mΩ (ou ganho cai); Rds 2 mΩ passa a gerar **1,80 W por FET** (24 FETs = **43,2 W** de calor só em condução — medido por cálculo, `python3 -c` acima) → refazer térmica de tudo; conector vira XT90 | §3, §5, §7 |
| **KV alto (2600 KV) + 6S** | frequência elétrica maior → mais perdas de comutação, amostragem de corrente mais apertada, tempo morto mais crítico | §5 |
| **Indutância de fase baixa (<20 µH)** | ripple de corrente de fase maior; shunts e amp precisam de banda maior; mais ruído | §3 |
| **>= 8 pás / hélice maior** | corrente de cruzeiro sobe → dimensionar trilha contínua pelo cruzeiro real, não pelo meu modelo de 4,5 g/W | §7 |

**Se você não responder, eu sigo com as premissas da §2 e registro tudo.**

---

## 2. PREMISSAS ADOTADAS (todas [PREMISSA], nenhuma confirmada)

| ID | Premissa | Valor | Impacto se errada |
|---|---|---|---|
| P-01 | Motor | 2207, 1750 KV, hélice 5" | alto (perdas, tensão) |
| P-02 | Bateria | LiPo 6S: 25,2 V max / 22,2 V nom / 19,8 V min (3,30 V/célula) | alto (classe de tensão) |
| P-03 | Corrente de pico por motor | 30 A (rajada) | alto (shunt, FET, trilha) |
| P-04 | Corrente contínua por motor | 15 A | alto (térmica) |
| P-05 | Rds(on) do MOSFET | 2,0 mΩ @ 10 V | alto (térmica) |
| P-06 | Qg total do MOSFET | 40 nC | médio (gate driver) |
| P-07 | Frequência de PWM | 20 kHz | médio |
| P-08 | fsw dos bucks | 500 kHz | médio |
| P-09 | Shunt de fase | 0,5 mΩ (2512, 2 W) | alto |
| P-10 | Ganho do amp de corrente | 50 V/V | alto |
| P-11 | Quiescência por gate driver | 2,5 mA | baixo |
| P-12/P-13 | ADC | 12 bits, FS 3,300 V (erro de offset ~3 mV) | médio |
| P-14 | Rendimento de hélice | 4,5 g/W, AUW 750 g | médio (cruzeiro) |
| P-15 | Endereço de projeto | **[N/D offline]** todos os parâmetros de datasheet (Vds, Rds, Qg, Ciss, ESR, ESL, corrente de conector, Vf) | — |

> ⚠️ **Não inventei nenhum dado de datasheet.** Onde a escolha do componente normalmente
> se apoia em número de datasheet, eu escrevi o **critério de escolha** (ex.: "Vds ≥ 40 V,
> Rds ≤ 3 mΩ @ 10 V") e marquei **[N/D offline]**. Se você me mandar os PDFs dos candidatos,
> eu fecho os valores na Fase 2 (simulação) — veja a §9 (lista de dúvidas).

---

## 3. ANÁLISE CRÍTICA DO REQUISITO "CONTROLE VIA WiFi"

Você pediu honestidade aqui. Esta é a parte mais importante da Fase 0.

### 3.1 O que foi calculado **[CALC]**
Orçamento de tempo de ar por quadro (802.11 2,4 GHz, unicast, sem retry):
```
    1 Mbps (DSSS): t_ar ~   1792.0 us por quadro
    6 Mbps (OFDM): t_ar ~    298.7 us por quadro
   54 Mbps (OFDM): t_ar ~     33.2 us por quadro
    50 Hz -> periodo  20.0 ms; jitter de 10 ms =  50% do periodo
   100 Hz -> periodo  10.0 ms; jitter de 10 ms = 100% do periodo
   250 Hz -> periodo   4.0 ms; jitter de 10 ms = 250% do periodo
```
Somando backoff CSMA, fila do driver, PHY e **retry/ARQ**, a latência real por pacote fica
na casa de **poucos ms no melhor caso e dezenas a centenas de ms no pior caso** (retransmissão).
Um canal com cauda de 100 ms é **inaceitável** para pilotagem direta: a 20 ms de atraso um
quadricóptero de 5" já mudou de atitude de forma irreversível.

### 3.2 Veredito
- **"Stick → WiFi → motor" (pilotagem direta): NÃO é viável com segurança.** Não por causa da
  média, mas pela **cauda** de latência e pela perda de link. Além disso, 2,4 GHz é compartilhado
  com o vídeo e sofre desvanecimento por orientação/obstrução.
- **Arquitetura correta (adotada nesta especificação):**
  1. **Estabilização a bordo**: IMU + PID rodando **no ESP32-S3**, a **1–4 kHz**;
  2. **WiFi/ESP-NOW apenas para COMANDOS**: setpoint de atitude/posição/potência a **20–50 Hz**;
  3. **FAILSAFE obrigatório**: watchdog de link (ex.: **200 ms** sem comando) → corta motores
     ou entra em descida controlada;
  4. **ESP-NOW** (sem IP, sem ARQ, quadro curto) em vez de UDP/IP ou TCP quando possível —
     menos overhead e menos jitter; TCP está **descartado** para controle (retransmissão + Nagle);
  5. Telemetria (o que sobe) em taxa baixa (10–50 Hz) e sem bloquear o laço de controle.
- **Sua responsabilidade**: se você quiser pilotar "na visão" com joystick WiFi, o projeto continua
  o mesmo no hardware — mas o firmware precisa rodar a malha de atitude. Nesta placa **a lógica de
  voo não está no escopo** (a Fase 1–3 entrega o hardware; a Fase 2 entrega só o que é
  verificável aqui: PWM com dead-time em Verilog, simulação dos reguladores etc.).
- **Alcance** **[NÃO VERIFICADO]**: premissa de 50–300 m em linha de visada com antena de PCB,
  muito sensível a orientação e altura. Medir isso exige bancada de RF e campo — não existe aqui.

---

## 4. DECISÕES DE ARQUITETURA (com justificativa)

### 4.1 ESC trifásico discreto (o que você pediu) — e por que mantenho
Sua proposta (6 MOSFETs N + gate driver com bootstrap + shunt + BEMF por motor) **é o caminho
certo aqui**, porque:
- não existe ESC pronta no projeto e o controle é seu;
- permite FOC ou trapezoidal indistintamente;
- o bootstrap é simples e barato para 6S.
**Alternativa que eu consideraria se o prazo fosse outro:** gate driver trifásico integrado
(ex.: classe DRV83xx/TMC) — reduz 24 FETs para 3 CI + 6 FETs por motor e traz proteções internas,
mas **não há datasheet offline** e a decisão fica dependente de parâmetro que eu não posso verificar.

**Topologia adotada por motor:** 3 half-bridges N-channel + 3 gate drivers *single-input*
(o driver gera o complementar e o **dead-time em hardware**, ~520 ns [PREMISSA]), o que evita
shoot-through mesmo se o firmware errar.

**Ponto crítico de contagem de PWM [CALC]:** cada motor precisa de **3 sinais PWM** (1 por half-bridge,
porque o complementar vem do driver). São **12 canais PWM**. O ESP32-S3 tem:
- **MCPWM**: 2 unidades × 3 operadores → **6 canais** (com dead-time em HW) → **2 motores**;
- **LEDC**: 8 canais, **sem** dead-time em HW (por isso o driver single-input) → **motores 3 e 4**.
> **[PREMISSA a confirmar no TRM]**: número de canais de MCPWM/LEDC/ADC do ESP32-S3. Não há
> datasheet/TRM no disco → **[N/D offline]**. **Se a contagem real for menor, o plano B é um
> CPLD/FPGA gerando as 24 saídas com dead-time programável — e isso sim eu consigo simular
> em Verilog aqui (iverilog), na Fase 2.**

### 4.2 Descoberta que muda a arquitetura: orçamento de canais de ADC
Canais analógicos necessários **[CALC]**:

| Sinal | Qtd |
|---|---|
| Corrente de fase (3 por motor) | 12 |
| BEMF (3 por motor) | 12 |
| VBAT sense | 1 |
| Temperatura (opcional) | 1 |
| **Total** | **26** |

O ADC1 do ESP32-S3 tem ~10 canais e o **ADC2 é compartilhado com o rádio** (clássico problema
de família ESP32 — **[PREMISSA a confirmar no TRM]**; **[N/D offline]**). **10 canais não cobrem 26.**
**Solução adotada:** **ADC externo por SPI** (16 canais, ou 2×8) para corrente+BEMF, e manter no
ADC1 do MCU só os sinais lentos (VBAT, temperatura). Bônus: o ADC externo permite
**amostragem simultânea** das 3 fases, que é o que um FOC decente exige. Custo: 1 CI + 4 pinos SPI.

### 4.3 Portadoras defasadas 90° entre os 4 motores (achado com número) **[CALC]**
```
  portadoras SINCRONIZADAS   : I_med= 72.03 A | RMS(ac)= 52.47 A | |I_ac|max= 72.03 A
  portadoras INTERCALADAS 90o: I_med= 71.95 A | RMS(ac)= 11.77 A | |I_ac|max= 21.98 A
  Ganho do intercalamento no ripple RMS: 4.46x
```
**Decisão:** defasar as portadoras dos 4 PWMs em 90°. É configuração de timer (custo zero) e
reduz **4,5x** a corrente RMS no banco de capacitores. Sem isso, o banco de entrada vira um forno.

### 4.4 Banco de entrada e o que realmente o dimensiona **[CALC]**
Ripple de tensão no banco para **um** motor a 30 A de pico, modelo com PWM resolvido (250 ns/amostra):
```
    C [uF]  ESR [mOhm] |  dV_C pkpk  dV_ESR pk  dV_TOTAL pkpk |  regra 'I*t/C'
       470        15.0 |       870mV       270mV          1140mV |  3.191 V
      1000        12.0 |       409mV       216mV           625mV |  1.500 V
      2200        10.0 |       186mV       180mV           366mV |  0.682 V
      4400         8.0 |        93mV       144mV           237mV |  0.341 V
```
A regra de "livro" `ΔV = I·t/C` **superestima em ~3 ordens de grandeza** (dá volts; o real é
centenas de mV) porque trata a corrente de pico como DC no período inteiro. **Quem dimensiona é
ESR + ESL, não os µF.**
Spike por indutância do cabo **[CALC]**: `L=100 nH`, `di=30 A`, `dt=50 ns` → **60 V** (estoura o
MOSFET de 40 V). Isso é o argumento definitivo para **100 nF + 10 µF colados a <2 mm de cada par
de MOSFETs**, fechando o loop de comutação localmente.

### 4.5 Sensoriamento de corrente **[CALC]**
```
  I=  30 A -> Vshunt=15.00 mV -> Vout(ganho 50) = 0.750 V  -> saida  0.900 .. 2.400 V
  Dissipacao no shunt: continua 112 mW | pico 0.45 W -> resistor 2512 2 W OK
  Resolucao ADC: 806 uV/LSB -> 32.2 mA/LSB | erro de offset do ADC(~3 mV) = 0.13 A
```
Fundo de escala ~±66 A (margem 2,2× sobre os 30 A de pico) e resolução de 32 mA — suficiente
para FOC em motor de 5". **Limitação real:** shunt no low-side só é válido **enquanto o FET
inferior conduz** → a amostragem do ADC **precisa** ser disparada em sincronia com o PWM
(janela de 2 µs = 4 % do período de 50 µs **[CALC]**). Isso é firmware + timer, não é hardware.

---

## 5. DIAGRAMA DE BLOCOS

Arquivo: **`diagrama_blocos_fase0_v3.png`** (abra; eu **olhei** a imagem com `view_image`,
verifiquei a legibilidade e corrigi duas versões anteriores — v1 com blocos sobrepostos e
v2 com rótulos em cima de linhas; ambas preservadas no disco).

Resumo: XT60 → proteção (TVS + P-FET anti-inversão) → banco de entrada → barramento VBAT →
4× ESC (3 gate drivers + 6 MOSFETs + 3 shunts + divisor de BEMF) → 4 conectores de motor;
ESP32-S3 no centro (MCPWM/LEDC para os drivers, ADC externo para corrente/BEMF, I²C para IMU/barô,
USB-C para programação, failsafe por GPIO); regulação: 12 V / 5 V / 3,3 V / 3,3 V_A.

---

## 6. LISTA DE COMPONENTES COM JUSTIFICATIVA

Detalhe completo e quantidades no CSV: **`lista_componentes_fase0.csv`**.
Pegadas do KiCad 5.1 **verificadas no disco** (`ls /usr/share/kicad/modules/...`):

| Bloco | Componente (critério de escolha) | Footprint (existência verificada) |
|---|---|---|
| Entrada | Conector XT60 (60 A [N/D offline]) | `Connector_AMASS:AMASS_XT60-F_1x02_P7.20mm_Vertical` ✔ |
| Proteção | TVS unidirecional standoff ≥ 30 V, clamp ~38 V [N/D offline] | `Diode_SMD:D_SMB` ✔ |
| Proteção | P-FET canal P, 30 V, Rds < 10 mΩ (ideal diode) [N/D offline] | `Package_TO_SOT_SMD:TO-252-2_TabPin1` ✔ |
| Banco | 6× 470 µF/35 V polímero low-ESR | `Capacitor_SMD:CP_Elec_8x10` ✔ |
| Banco | 10 µF/50 V X7R + 100 nF/50 V X7R (por par de MOSFET) | `Capacitor_SMD:C_1206`, `C_0402` ✔ |
| Potência | MOSFET N, **Vds ≥ 40 V, Rds ≤ 3 mΩ @10 V, Qg ≤ 60 nC** [PREMISSA P-05/P-06] | `Package_TO_SOT_SMD:TO-252-3_TabPin2` (DPAK) ou PowerPAK 5×6 ✔ |
| Gate drive | Driver half-bridge single-input, bootstrap, dead-time interno ~520 ns, Vcc 12 V [N/D offline] | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` ✔ |
| Gate drive | Rg 4,7–22 Ω (adotado 10 Ω, ver §7 amortecimento) | `Resistor_SMD:R_0805_2012Metric` ✔ |
| Gate drive | 1 µF/25 V X7R bootstrap + diodo rápido | `C_0805`, `D_SOD-123` ✔ |
| Corrente | Shunt 0,5 mΩ 2 W 2512 manganina | `Resistor_SMD:R_2512_6332Metric` ✔ |
| Corrente | Amp diferencial ganho 50, CMVR ≥ 30 V [N/D offline] | `Package_SO:SOIC-8-1EP_3.9x4.9mm_EP2.41x3.81mm` ✔ |
| BEMF | Divisor 8,2k/1,0k 1 % + 1 nF + clamp 3,3 V | `R_0603`, `C_0402`, `D_SOD-323` ✔ |
| MCU | **ESP32-S3-WROOM-1** (WiFi 2,4 GHz + USB nativo) | ⚠️ **NÃO existe no KiCad 5.1** → pegada a gerar por script (41 pads castelados) |
| IMU | IMU 6 eixos SPI/I²C | `Sensor_Motion:InvenSense_QFN-24_3x3mm_P0.4mm` ✔ (padrão QFN-24 3×3; **confirmar o CI exato** [N/D offline]) |
| Barômetro | Barômetro I²C LGA-8 | ⚠️ **não existe** (`Sensor_Pressure` tem só Freescale/Honeywell) → gerar LGA-8 |
| ADC externo | ADC SPI 16 canais (corrente+BEMF) [N/D offline] | `Package_SO`/`Package_DFN_QFN` conforme o CI ✔ |
| Energia | Buck 12 V/0,6 A (gate drivers) | `Package_TO_SOT_SMD`, `Inductor_SMD:L_12x12mm_H6mm` ✔ |
| Energia | Buck 5 V/2 A e Buck 3,3 V/1,5 A | idem (`L_Bourns_SRR1210A` ✔) |
| Energia | LDO 3,3 V_A / 150 mA (analógico) | `Package_TO_SOT_SMD:SOT-23` ✔ |
| Motor | Conector MR30 3 pinos (ou bloco 3,5 mm) | `Connector_AMASS:AMASS_MR30PW-FB_1x03_P3.50mm_Horizontal` ✔ |
| USB | USB-C receptáculo 16p | `Connector_USB:USB_C_Receptacle_GCT_USB4085` ✔ |
| Extra | LED, buzzer, botão, pads de UART/I²C/SPI | `LED_0805`, `Buzzer_*`, `TestPoint` ✔ |

**Critério de escolha dos semicondutores (em vez de número inventado):**
- **MOSFET**: precisa aguentar 25,2 V com margem → **Vds ≥ 40 V**; com 30 A de pico por motor e
  24 FETs no total, Rds(on) é o que decide a temperatura: cada 1 mΩ a mais custa
  `(15 A)² × 1 mΩ × 24 = 5,4 W` de calor **[CALC]**. Por isso o requisito é **Rds ≤ 3 mΩ**.
- **Gate driver**: precisa (a) bootstrap para o high-side, (b) gerar o complementar com
  **dead-time** — é isso que permite usar só 1 pino por half-bridge e caber em 12 PWMs.
- **Buck 12 V**: existe porque gate de MOSFET de potência precisa de ~10–12 V para ficar
  plenamente ligado; existe um trilho dedicado porque ruído de carga de gate não pode voltar
  para o MCU.

---

## 7. ORÇAMENTO DE CORRENTE E POTÊNCIA POR TRILHO **[CALC]**

```
  3.3 V : ESP32-S3 pico WiFi TX 0.50 A + IMU 2 mA + baro 1 mA + LED 10 mA + margem 5 mA
          = 0.518 A -> BUCK 3,3 V / 1,50 A (folga 2,9x)
  12 V  : 12 drivers x 2,5 mA + carga de gate 19,2 mA = 0.049 A -> BUCK 12 V / 0,60 A (folga 12x)
  5 V   : entrada do buck 3,3 V 1158 mA + LDO 150 mA + USB/aux 20 mA
          = 1.328 A -> BUCK 5 V / 2,00 A (folga 1,5x)
  VBAT  : motores 60 A contínuo / 120 A pico [PREMISSA] + 0,30 A dos conversores
```
Dimensionamento dos bucks (fsw 500 kHz, ripple 30 %):
```
  BUCK 12 V : L(30%) = 88.9 uH -> adotar 89 uH ; Cout = 3,7 uF -> 2x22 uF ; dV_esr = 0,4 mV
  BUCK 5 V  : L(30%) = 17.0 uH -> adotar 17 uH ; Cout = 6,0 uF -> 2x22 uF ; dV_esr = 1,2 mV
  BUCK 3,3 V: L(30%) =  5.2 uH -> adotar  5 uH ; Cout = 3,4 uF -> 2x22 uF ; dV_esr = 0,9 mV
  LDO 3,3 V_A: Pdiss = 0,255 W (SOT-23 com pad térmico)
```
Balanço no **cruzeiro** (carga real, não nominal) **[CALC]**:
```
  Helice: 167 W | I_barra 7.5 A | I_fase pico 12.5 A
  FETs: 1.88 W | conversores: 4.00 W (entrada) | TOTAL ~ 173 W (3.5 % acima do ideal de helice)
```
Térmica do MOSFET **[CALC]** (Rth_ja é [PREMISSA]):
```
  cruzeiro (5 A fase) : 0.39 W / 24 FETs | Tj(Rth=60C/W, Ta=25C) = 26.0 C
  nominal (15 A)      : 3.50 W / 24 FETs | Tj = 33.7 C
  pico (30 A)         : 13.99 W / 24 FETs | Tj = 60.0 C
```
Trilhas (IPC-2221, 2 oz) **[CALC]**:
```
  I= 10 A, dT=10 C -> largura =  3.60 mm
  I= 30 A, dT=10 C -> largura = 16.37 mm   (dT=30 C -> 8.40 mm)
  I=120 A, dT=10 C -> largura = 110.78 mm  << não existe trilha de 120 A contínuo
```
**Conclusão honesta:** 120 A é **pico de rajada**, não contínuo. O barramento será dimensionado
para dezenas de ampères (cruzeiro ~7,5 A, nominal de projeto até 30 A) em **2 oz + camada
interna dedicada + metal exposto**, e o pico é absorvido por massa de cobre e capacitância —
**isso não se valida em software** (§9).
Vias **[CALC]**: via 0,3 mm (parede 25 µm) = 1,168 mΩ; 40 vias a 30 A → queda 0,88 mV, 26 mW total.
Adotado 40 vias de costura por transição de camada [NÃO MEDIDO].
Gate **[CALC]**: Z0 = 3,16 Ω → Rg ≥ 6,3 Ω (adotado **10 Ω**); f_ring = 25,2 MHz com loop de 20 nH.

---

## 8. MAPA DE PINOS DO MCU (ESP32-S3-WROOM-1)

> **[PREMISSA]**: qualquer GPIO pode ser roteado para MCPWM/LEDC pelo *GPIO matrix*, então este
> mapa é uma escolha de **layout**, não uma imposição do silício. Números de GPIO fixos
> (USB D+/D− = GPIO19/20) são **[N/D offline]** — confirmar no TRM.

| Função | Pinos | Observação |
|---|---|---|
| Motor 1 — 3× PWM | GPIO4,5,6 (MCPWM0 OP0A/1A/2A) | 1 pino por half-bridge; complementar e dead-time no driver |
| Motor 2 — 3× PWM | GPIO7,8,9 (MCPWM1 OP0A/1A/2A) | idem |
| Motor 3 — 3× PWM | GPIO10,11,12 (LEDC ch0/1/2) | mesmo timer LEDC → 3 fases sincronizadas |
| Motor 4 — 3× PWM | GPIO13,14,15 (LEDC ch3/4/5) | idem |
| ADC externo (SPI) | GPIO16=MOSI, 17=SCK, 18=MISO, 21=CS, 47=IRQ/DRDY | 16 canais: 12 corrente + 12 BEMF via 2 mux/2 CI |
| VBAT sense | GPIO1 (ADC1 ch0) | divisor 100k/13,7k + RC 132 Hz |
| Temperatura (opc.) | GPIO2 (ADC1 ch1) | NTC ou sensor interno |
| IMU (SPI) | compartilha 16/17/18, CS = GPIO42 | 4–8 MHz, leitura em rajada |
| Barômetro (I²C) | SDA=GPIO38, SCL=GPIO39 | 400 kHz, pull-ups 4,7 k |
| USB nativo | GPIO19 (D−), GPIO20 (D+) | **fixos no S3** [N/D offline] |
| UART0 (debug/OTA) | TXD0=GPIO43, RXD0=GPIO44 | pads de 1,27 mm |
| LED / Buzzer / Botão | GPIO45 / GPIO46 / GPIO0 | botão BOOT também |
| EN / BOOT | EN, GPIO0 | reset e download |
| Pads extra | I²C/QWIIC, SPI, 1 UART livre, 4 GPIO | para GPS/magnetômetro/futuro |
| **Watchdog externo** | GPIO48 (feed) | opcional: corte de motores independente do firmware |

Total: ~32 pinos usados de 36 disponíveis → cabe, com folga apertada. **A Fase 1 fecha isso com o
número real de GPIOs da cápsula.**

---

## 9. O QUE **NÃO** FOI VERIFICADO (leia antes de confiar em qualquer coisa)

1. **Nenhuma medição de bancada foi feita.** Zero osciloscópio, zero termopar, zero carga real.
2. **Nenhum datasheet está no disco** → todos os parâmetros elétricos de componentes são
   [PREMISSA]. O ngspice da Fase 2 vai simular o que você me der (ou modelos genéricos).
3. **Dissipação térmica real, EMI/EMC, 30 A contínuo e fabricação não são simuláveis aqui.**
   Vou dizer isso de novo na Fase 2 em vez de estimar como se fosse medição.
4. **Contagem de periféricos do ESP32-S3** (MCPWM/LEDC/ADC, uso do ADC2 com o rádio, pinos fixos
   de USB) — [N/D offline].
5. **KiCad 5.1.9** não tem `kicad-cli` nem visualizador 3D instalado; não há auto-router por
   script (roteamento é desenhado). Isso será declarado de novo na Fase 3.
6. **O firmware de voo real não está no escopo.** Na Fase 2 eu entrego (e simulo com iverilog)
   apenas o gerador de PWM com dead-time programável — sem isso, nenhuma afirmação sobre
   "controle" no MCU se sustenta.
7. **Interleaving de portadoras** (§4.3) é resultado de modelo numérico, **não** de medição.
8. **Incidentes de processo (transparência):** o primeiro log do script de dimensionamento ficou
   **truncado** (`tee | head` corta o pipe com SIGPIPE) → refeito em `dimensionamento_fase0_saida_v2.txt`.
   Na revisão achei e corrigi **3 bugs meus**: (a) `np.ptp` inexistente no NumPy 2.x;
   (b) no trilho de 5 V eu somava potência em vez de corrente (0,37 A em vez de 1,33 A);
   (c) no modelo de ripple eu aplicava o **mesmo duty às 3 fases**, o que zerava a corrente de
   barramento — o modelo foi reescrito na v2/v4 com duty por fase e **portadora triangular real**.
   Todos os arquivos antigos foram preservados (nada foi apagado).

---

## 10. SEGURANÇA, LIMITES E REGULATÓRIO (inclua isto no projeto)

### 10.1 Bateria LiPo (risco de incêndio)
- Carregue **sempre com carregador balanceador**, **nunca sem supervisão**, em local não inflamável.
- **Nunca descarregue abaixo de ~3,3 V/célula** (19,8 V neste pack). Implemente alarme/telemetria.
- Nunca deixe pack amassado/inchado em uso; armazene a ~3,8 V/célula.
- **Fusível/e-fuse na entrada** é opcional no meu desenho de hoje — eu recomendo incluir
  (a Fase 1 inclui se você aprovar).

### 10.2 Primeira energização (regra de ouro)
1. **Hélices REMOVIDAS** sempre em bancada.
2. Primeira energização **com fonte de bancada com limite de corrente** (ex.: 1 A, 12 V),
   **não** com a bateria. Só depois de tudo medido, bateria com hélice fora.
3. Corrente limite crescente em etapas; medir consumo em vazio de cada trilho antes de soldar o motor.
4. Só instalar hélice depois de: PWM medido, dead-time medido, corrente de fase coerente,
   failsafe testado e motores girando controladamente nos 4 sentidos.

### 10.3 O que a bancada tem de provar (nada disso é software)
- **Cobre/2 oz, térmica e ruído**: temperatura do FET e do shunt em carga real, com termopar/câmera;
  ripple no barramento com sonda diferencial; ringing nos gates; EMI perto do receptor de vídeo.
- **30 A contínuo**: rajada em banco de cargas resistivo/indutivo ou hélice em tubo de empuxo.
  Sem isso, a spec de corrente continua sendo [PREMISSA].

### 10.4 Regulatório (Brasil) — verifique **antes de voar**
- **SISANT/ANAC (DECEA)**: drones acima de **250 g** exigem cadastro no SISANT; verifique também
  exigências de seguro e, conforme o caso, habilitação.
- Regras de **DECEA** para espaço aéreo (altura máxima, distância de aeródromos, sobrevoo de
  pessoas/áreas sensíveis) — consulte antes de qualquer voo.
- **ANATEL**: o rádio 2,4 GHz do módulo precisa estar **homologado** (módulos certificados já vêm
  com homologação; a antena/PCB não pode ser alterada sem reavaliação).
- Este é um **equipamento caseiro**; em caso de queda, a responsabilidade é sua. Não voe sobre
  pessoas, vias ou patrimônio de terceiros.

---

## 11. MINHAS DÚVIDAS PARA VOCÊ (responda o que puder)

**Motores / hélice (bloqueiam o dimensionamento fino)**
1. Modelo exato do motor, **KV** e **nº de polos**?
2. **R (mΩ)** e **L (µH)** de fase, se tiver datasheet?
3. **Corrente contínua e de pico** (A) e duração da rajada?
4. Hélice: **diâmetro, passo, nº de pás**?
5. Empuxo alvo por motor / **peso total (AUW)** esperado?

**Bateria**
6. **Nº de células (S)** e capacidade (mAh)? Conector (XT30/XT60/XT90)?
7. Você já tem o pack ou vai comprar? (muda o partidor e a classe do MOSFET)

**Arquitetura / firmware**
8. A estabilização vai rodar **a bordo** (recomendo fortemente) ou você quer mesmo tentar
   pilotagem direta por WiFi?
9. Prazo de link aceitável para o **failsafe** (sugiro 200 ms)?
10. Você aceita **ADC externo por SPI** (§4.2) — que eu considero obrigatório — ou prefere reduzir
    os sensores (ex.: 2 shunts por motor) para caber nos ADCs internos?
11. Precisa de **fusível/e-fuse** de entrada? (recomendo sim)

**Componentes / arquivos que você teria de me mandar (não estão no disco)**
12. PDFs dos candidatos a **MOSFET, gate driver, amp de corrente, buck, IMU, barômetro e module
    ESP32-S3** (mesmo que de fornecedor diferente) — sem isso, tudo segue como [PREMISSA] e a
    Fase 2 simula com modelos genéricos.
13. Pegada/drawing do ESP32-S3-WROOM-1 (o KiCad 5.1 não tem) — eu gero por script, mas preciso do
    *mechanical drawing* para não errar o pitch dos pads.
14. Existe restrição de **custo, tamanho de PCB (ex.: 30×30 mm?), nº de camadas ou fabricante**
    (para eu respeitar folgas e permitir 2 oz / via enterrada)?

---

## 12. PRÓXIMO PASSO (parada obrigatória)

**Fase 0 encerrada.** Não vou desenhar esquema nem PCB até seu OK.

Quando você responder, eu sigo para a **Fase 1** (esquema elétrico completo, um PNG por bloco +
geral, com valores e footprint, em `fase1_esquema/`), depois **Fase 2** (ngspice: buck 12/5/3,3 V,
gate drive, shunt+amp, divisor VBAT, filtro ADC, proteção de inversão — com **esperado × medido ×
erro**), depois **Fase 3** (PCB KiCad 5.1 por script + Gerber/Excellon + render gerbv que eu
**olho** antes de declarar pronto) e **Fase 4** (BOM CSV, ordem de solda, plano de teste de bancada,
riscos).
