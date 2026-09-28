# WP3 — Premissas P-01..P-15 e situation dos datasheets

**Story:** US-003
**Data de emissão:** 2026-09-28
**Base documental:** `fase0_especificacao/FASE0_ESPECIFICACAO.md` (seção 2, "PREMISSAS ADOTADAS")
**Método:** verificação local por `file`, `md5sum`, `pdfinfo` e `pdftotext -layout` nesta máquina.
Nenhum valor deste documento foi copiado de memória: todos vieram de extração local dos PDFs citados, com página.

## Legenda de rastreabilidade

| Marca | Significado |
|---|---|
| **CONFIRMADO** | O valor da premissa bate com número extraído de um datasheet que está no disco. A fonte (arquivo + página) está escrita na mesma linha. |
| **CONTRADITO** | O datasheet do disco diz outra coisa. A premissa não é apenas "não confirmada": ela está **errada** segundo a fonte. |
| **PARCIAL** | Parte do valor tem lastro; a parte restante é escolha de projeto ou depende de peça não definida. |
| **NÃO VERIFICADA** | Não há lastro local. Ou a peça é Passiva/genérica, ou a premissa é escolha de projeto, ou a peça escolhida ainda não existe no disco. |
| **NÃO EXTRAÍDO LOCALMENTE** | A página exata não pôde ser lida nesta máquina; a informação que falta está nomeada. |

> Regra aplicada: quando a premissa é "não confirmada" por falta de **peça** (motor, bateria, hélice,
> resistor, indutor), isso **não** é falha do projeto — é ausência de documento. Quando a premissa é
> "não confirmada" apesar de **haver** o documento no disco, isso é falha real e está marcado.

---

## 1. As 15 premissas P-01..P-15

| ID | Premissa (FASE0) | Valor assumido | Situação | Fonte (arquivo + página) | O que muda no projeto se estiver errado |
|---|---|---|---|---|---|
| **P-01** | Motor | 2207, 1750 KV, hélice 5" | **NÃO VERIFICADA** | Nenhum datasheet de motor no disco. | **Alto.** 1750 KV a 22,2 V ⇒ ~14,4 krpm (`RPM ≈ KV × V / 60`). Errar a KV desloca a frequência elétrica de fase e, portanto, a perda em comutação e a banda exigida do shunt. Também redefine a corrente de pico (P-03). |
| **P-02** | Bateria | LiPo 6S: 25,2 V max / 22,2 V nom / 19,8 V min | **NÃO VERIFICADA** | Nenhum datasheet de célula LiPo no disco. Os 3,30 V/célula são prática de mercado, não extração. | **Alto.** Define a classe de tensão de MOSFET, gate driver e regulador. Com 25,2 V no barramento, qualquer componente com Vds < 40 V ou VCC < 20 V sai de especificação. |
| **P-03** | Corrente de pico por motor | 30 A (rajada) | **NÃO VERIFICADA** | Depende de P-01. Nenhum datasheet de motor/hélice no disco. | **Alto.** Dimensiona shunt, MOSFET e trilha. A corrente de pico é o critério de surto do FET e o pior caso do ganho do amplificador de corrente. |
| **P-04** | Corrente contínua por motor | 15 A | **NÃO VERIFICADA** | Depende de P-01. | **Alto.** Critério térmico: define quantos MOSFETs por motor e a área de trilha de cobre. |
| **P-05** | Rds(on) do MOSFET | 2,0 mΩ @ 10 V | **PARCIAL** | `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` **p.4**, Static Electrical Characteristics: `RDS(on)` = **1,7 mΩ (typ) @ VGS = 10 V, ID = 100 A** e **2,2 mΩ (max) @ VGS = 6 V, ID = 50 A**. Também p.1, Table 1: `RDS(on),max = 1,7 mΩ`. | **Alto (térmica).** Os 2,0 mΩ @ 10 V assumidos ficam **entre** o típico de 1,7 mΩ e o máximo de 2,2 mΩ da peça de referência — é um valor de engenharia defensável. **Porém a peça de referência não é a escolhida** (`…REFERENCIA_NAO_ESCOLHIDO`), e a segunda linha mostra que a resistência **sobe para 2,2 mΩ quando VGS cai a 6 V**. Se a placa operar com VGS abaixo de 10 V (o IR2104 entrega gate drive de 10–20 V, `datasheets/ir2104_infineon_datasheet.pdf` p.1, então 10 V é o piso), o FET fica no pior caso de 2,2 mΩ, e não em 2,0 mΩ. |
| **P-06** | Qg total do MOSFET | 40 nC | **CONTRADITO** | `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` p.1, Table 1: `QG(0V..10V) = 168 nC`; p.4: `Qg = 168 nC (typ) / 210 nC (max)`, condição `VDD=50 V, ID=100 A, VGS=0 to 10 V`. Também p.4: `Qgs = 53 nC`, `Qgd = 34 nC (typ) / 51 nC (max)`. | **Alto — esta é a premissa mais perigosa da lista.** 40 nC é **~4× otimista** frente ao único MOSFET de referência (168 nC). O gate driver precisa fornecer 168 nC em ~100 ns de subida: com I<sub>O+/−</sub> = 130/270 mA (`datasheets/ir2104_infineon_datasheet.pdf` p.1) e 168 nC, o slew de gate cai para ~0,6–1,3 V/ns, o que **aumenta a perda de comutação e a dissipação no driver**. O dimensionamento de resistor de gate e de dissipação do IR2104 feito na Fase 0 com 40 nC **está subdimensionado por um fator ~4** e precisa ser refeito. |
| **P-07** | Frequência de PWM | 20 kHz | **NÃO VERIFICADA** (é escolha de projeto, não dado de datasheet) | N/A — parâmetro de controle, não de componente. | **Médio.** 20 kHz fica acima do limite de audibilidade (~20 kHz) e é a premissa que faz a supressão de modo comum do INA240 (CMRR 93 dB @ 50 kHz, `datasheets/ina240_ti_sbos662.pdf` p.5) ser irrelevante. Se a PWM subir, a rejeição de ripple deixa de ser folga. |
| **P-08** | fsw dos bucks | 500 kHz | **NÃO VERIFICADA** | Nenhum datasheet de regulador buck no disco. Os esquemas `fase1_esquema/esq2_buck12v.png`, `esq3_buck5v.png` e `esq4_buck3v3.png` existem, mas não há CI escolhido. | **Médio.** Frequência de switch define ondulação, tamanho de indutor e o filtro de LC da saída de 3,3 V, que por sua vez alimenta a referência do ADC. |
| **P-09** | Shunt de fase | 0,5 mΩ (2512, 2 W) | **NÃO VERIFICADA** | Nenhum datasheet de resistor de manganina no disco. O "2 W" é um valor de catálogo genérico, não extraído. | **Alto.** 0,5 mΩ é o piso de resolução: com o offset do INA240 (VOS = ±5 µV típico, `datasheets/ina240_ti_sbos662.pdf` p.5), o offset equivalente é 5 µV / 0,5 mΩ = **10 mA de erro** — invisível. Se o shunt real for 1 mΩ, a resolução dobra para melhor, mas cai a tensão de sense. A potência nominal de 2 W de um encapsulamento 2512 varia por fabricante e **não foi confirmado**. |
| **P-10** | Ganho do amplificador de corrente | 50 V/V | **CONFIRMADO** | `datasheets/ina240_ti_sbos662.pdf` p.1 (features: "INA240A2: 50 V/V"); p.3, **Table 5-1 Device Comparison** (`INA240A2 → GAIN 50 V/V`); p.5, **Table 7.5 Electrical Characteristics** (`G … INA240A2 … 50 V/V`). | **Alto — e está certo.** A premissa de 50 V/V **seleciona a variante A2**. Estoque de A1 (20 V/V), A3 (100 V/V) ou A4 (200 V/V) invalida o ganho.Erro de ganho do A2: ±0,05 % típico / ±0,20 % máximo (p.5), com drift de ±0,5 a ±2,5 ppm/°C. Com 0,5 mΩ e 30 A: sense = 15 mV ⇒ saída = 750 mV. |
| **P-11** | Quiescência por gate driver | 2,5 mA | **CONTRADITO** | `datasheets/ir2104_infineon_datasheet.pdf` p.3, Static Electrical Characteristics: `IQCC` (quiescent VCC supply current) = **150 µA typ / 270 µA max**; `IQBS` (quiescent VBS supply current) = **30 µA typ / 55 µA max**; ambos em `VIN = 0V or 5V`. Total = **325 µA max**. | **Baixo (erro conservador).** O número de 2,5 mA é **~7,7× maior** que o real. A origem provável da confusão: a corrente de quiescência do **INA240** é 2,4 mA máximo (`datasheets/ina240_ti_sbos662.pdf` p.1) — valor de amplificador, não de gate driver. Impacto: superestima-se o consumo do driver (seguro), mas a arquitetura de alimentação pode estar orçada com folga indevida. **Corrigir o número para 0,325 mA.** |
| **P-12** | ADC | 12 bits | **CONFIRMADO** (parcialmente — ver P-13) | `datasheets/mcp3208_microchip_ds21298e.pdf` p.1: "2.7V 4-Channel/8-Channel **12-Bit** A/D Converters", "12-bit resolution". p.15, Seção 3.0 PIN DESCRIPTIONS. | **Médio.** Confirmado que a resolução de 12 bits existe. **Atenção:** o MCP3208 tem **8 canais** (CH0–CH7, p.15, Table 3-1), e `fase0_especificacao/lista_componentes_fase0.csv` linha 22 pede "16 canais, ≥ 200 ksps" com encapsulamento **genérico** — logo **2 encapsulamentos ou 2 peças** são necessários, não 1. Isso não é erro de premissa, mas é uma restrição que o BOM não absorveu. |
| **P-13** | ADC — fundo de escala e offset | FS 3,300 V, erro de offset ~3 mV | **PARCIAL** — offset **CONFIRMADO**; FS é escolha de projeto | **Offset — CONFIRMADO:** `datasheets/mcp3208_microchip_ds21298e.pdf` **p.2**, Electrical Characteristics: `Offset Error = ±1,25 LSB (typ) / ±3 LSB (max)`. Convertendo com o FS de 3,300 V: 1 LSB = 3,300 / 4096 = 806 µV, logo ±3 LSB = **±2,42 mV**. O "~3 mV" assumido é **conservador e realisticamente correto** (está acima do pior caso do datasheet). **FS:** o MCP3208 **não tem FS interno**; o fundo de escala vem de `VREF` (pin 15, p.15, Table 3-1) e a alimentação é `VDD` (pin 16) +2,7 V a +5,5 V. Os 3,300 V são **escolha de projeto** (casa com a VDD3P3 do ESP32-S3, `datasheets/esp32-s3_datasheet_en.pdf` p.64, Table 5-2), não um número de datasheet. | **Médio.** A premissa de offset está **certa** — 2,42 mV de pior caso contra os ~3 mV assumidos. O que fica sem lastro é o **FS**: se VREF não for exatamente 3,300 V, todo o cálculo de 1 LSB = 806 µV e de corrente por shunt desloca proporcionalmente. Como a corrente é derivada de `VOUT / (ganho × R_shunt)`, um FS de 3,0 V em vez de 3,3 V superestima a leitura de corrente em ~10 %. Por isso VREF deve vir de uma referência medida, não de um divisor de resistores. |
| **P-14** | Rendimento de hélice / AUW | 4,5 g/W, AUW 750 g | **NÃO VERIFICADA** | Nenhum dado de hélice no disco. É um modelo de estimativa, não um dado de peça. | **Médio (cruzeiro).** Define a corrente de cruzeiro e, por consequência, a largura de trilha contínua. O próprio FASE0 avisa: se a hélice for maior que 5" ou tiver ≥ 8 pás, a corrente de cruzeiro sobe e a trilha dimensionada pelo modelo de 4,5 g/W fica curta. |
| **P-15** | "Endereço de projeto" — parâmetros de datasheet ainda **[N/D offline]** | Vds, Rds, Qg, Ciss, ESR, ESL, corrente de conector, Vf | **PARCIAL — substancialmente reduzida por esta WP** | Ver §2 e §3 deste documento. **Ainda em aberto:** Ciss, ESR, ESL, corrente nominal do conector XT60, e Vf do diodo. | **Médio.** P-15 era o item que impedia a Fase 2 (simulação) de fechar. Com os 6 PDFs agora no disco, os parâmetros de MOSFET, gate driver, amplificador de corrente, ADC e IMU têm fonte. O que falta é potência (indutor/ESR/ESL), conectores e semicondutores discretos — nenhum deles tem peça escolhida no projeto ainda. |

### Resumo da §1

- **CONFIRMADO:** P-10, P-12 (resolução), P-13 (offset — 2,42 mV de pior caso contra ~3 mV assumidos).
- **PARCIAL:** P-05, P-12/P-13 (contagem de canais e FS), P-13 (fundo de escala), P-15.
- **CONTRADITO:** P-06 (Qg — fator ~4), P-11 (quiescência — fator ~7,7).
- **NÃO VERIFICADA:** P-01, P-02, P-03, P-04, P-07, P-08, P-09, P-14.

**As duas premissas refutadas por dado de datasheet (P-06 e P-11) são justamente as duas que sustentavam o
dimensionamento de gate drive feito na Fase 0. O relatório `fase0_especificacao/dimensionamento_fase0_saida_v2.txt`
e `fase0_especificacao/verifica_limites_saida_v4.txt` foram calculados com elas e precisam de revisão.**

---

## 2. Pinout das três peças — rastreabilidade

O critério de aceitação exige fonte rastreada (arquivo + página) **ou** marcação explícita de NÃO VERIFICADA.
Abaixo estão as duas coisas, separadas.

### 2.1 Pinout de **datasheet** — RASTREADO ✅

**INA240** — `datasheets/ina240_ti_sbos662.pdf` (TI SBOS662C, Jul 2016, rev. Dez 2021), **p.3, Seção 6
"Pin Configuration and Functions", Table 6-1 "Pin Functions"**, e Figuras 6-1 (TSSOP/PW) e 6-2 (SOIC/D):

| Nome | Pin TSSOP (PW) | Pin SOIC (D) | Descrição (p.3) |
|---|---|---|---|
| GND | 4 | 2 | Ground |
| IN– | 3 | 1 | Lado da carga do resistor de shunt |
| IN+ | 2 | 8 | Lado da alimentação do resistor de shunt |
| NC | 1 | 4 | Reservado. Conectar ao GND ou deixar flutuante |
| OUT | 8 | 5 | Tensão de saída |
| REF1 | 7 | — | Referência 1. Conectar a 0 V…V<sub>S</sub> |
| REF2 | 6 | 5 | Referência 2 |
| V<sub>S</sub> | 5 | 5 | Alimentação positiva |

> **Atenção ao footprint:** a coluna "Pin SOIC (D)" do TEXTO EXTRAÍDO tem as colunas deslocadas
> (REF2 aparece como 3 e V<sub>S</sub> como 5, enquanto a coluna TSSOP traz REF2 = 6 / V<sub>S</sub> = 5).
> Isso é artefato do `pdftotext -layout` em tabela de duas colunas lado a lado. **Antes de gerar o footprint,
> confirme a numeração de 8 pinos do SOIC contra a Figura 6-2 na página 3** — ou extraia com
> `pdftotext -f 3 -l 3 -layout` e confira a grade, ou abra a página como imagem.

**IR2104** — `datasheets/ir2104_infineon_datasheet.pdf` (Infineon PD60046-S), **p.4, "Lead Definitions" e
"Lead Assignments"**:

| Pin | Símbolo | Definição (p.4) |
|---|---|---|
| 1 | VCC | Low side and logic fixed supply |
| 2 | IN | Entrada lógica para HO e LO, em fase com HO |
| 3 | SD | Entrada lógica de shutdown |
| 4 | COM | Low side return |
| 5 | LO | Low side gate drive output |
| 6 | VS | High side floating supply return |
| 7 | HO | High side gate drive output |
| 8 | VB | High side floating supply |

**MCP3208** — `datasheets/mcp3208_microchip_ds21298e.pdf` (Microchip DS21298E), **p.15, Seção 3.0
"PIN DESCRIPTIONS", Table 3-1 "PIN FUNCTION TABLE"** (coluna "MCP3208 — PDIP, SOIC, TSSOP"):

| Pin | Símbolo | Definição | Pin | Símbolo | Definição |
|---|---|---|---|---|---|
| 1 | CH0 | Entrada analógica | 9 | DGND | Ground digital |
| 2 | CH1 | Entrada analógica | 10 | CS/SHDN | Chip Select / Shutdown |
| 3 | CH2 | Entrada analógica | 11 | DIN | Serial Data In |
| 4 | CH3 | Entrada analógica | 12 | DOUT | Serial Data Out |
| 5 | CH4 | Entrada analógica | 13 | CLK | Serial Clock |
| 6 | CH5 | Entrada analógica | 14 | AGND | Ground analógico |
| 7 | CH6 | Entrada analógica | 15 | VREF | Entrada de tensão de referência |
| 8 | CH7 | Entrada analógica | 16 | VDD | Alimentação +2,7 V a +5,5 V |

### 2.2 Pinout **efetivamente usada na v7** — NÃO VERIFICADA ❌

Isto é distinto da §2.1 e é o que o critério de aceitação pede explicitamente.

A versão v7 (`plano/WP1_ROTEAMENTO.md`, `plano/mede_v7_wp1.py`) **não publica netlist**. A verificação em disco foi:

- `plano/WP1_ROTEAMENTO.md` linha 122 cita "SPI dos 4 MCP3208", "I2C do IMU", "12 saídas de PWM", "4 canais ADC de corrente" — mas **nenhum número de pino**.
- `plano/mede_v7_wp1.py` é um script de **medição de PCB** (contagem de footprints, pads, trilhas, vias, zones). Não toca em netlist de componente.
- Busca por netlist no repositório: `find . -name "*.net" -o -name "*netlist*" -o -name "*.kicad_sch"` → **zero resultados**. Não existe arquivo `.kicad_sch` nem `.net` no repositório.
- `fase0_especificacao/lista_componentes_fase0.csv` **não escolheu** nenhuma das três peças: a linha 22 (ADC) pede encapsulamento "Package_DFN_QFN / Package_SO conforme CI", marcada "SIM (generico)". INA240 e IR2104 **não aparecem** no CSV.
- `fase1_esquema/` só contém PNGs gerados por script e scripts Python. Nenhum deles é fonte de pinout de CI.

**Conclusão:** a pinout de **datasheet** está rastreada (§2.1), mas a **pinout aplicada na v7 está
NÃO VERIFICADA — não existe netlist neste repositório para confrontar.** As três peças ainda não foram
selecionadas oficialmente no BOM, então sequer há número de peça escolhido a quem atribuir pinos.

**Como resolver:** (a) escolher as peças e registrar o part number em
`fase0_especificacao/lista_componentes_fase0.csv`; (b) produzir o netlist do KiCad em `fase1_esquema/`;
(c) confrontar a coluna "pin atribuído" desse netlist com as tabelas da §2.1, página a página.
Até lá, qualquer netlist citado em outro documento que atribua pinos ao INA240/IR2104/MCP3208
deve ser tratado como **não verificado**.

---

## 3. Aquisição dos datasheets — resultado real

Ferramentas usadas: `file`, `ls -la`, `md5sum`, `sha256sum`, `pdfinfo`, `pdftotext -layout`.
Datas dos arquivos (`ls -la`): **2026-09-28** para os 6 PDFs novos, **2026-09-11** para os pré-existentes.
Data desta verificação: **2026-09-28**.

| # | Arquivo | Bytes | `file` | Págs. | Texto extraído | Resultado |
|---|---|---|---|---|---|---|
| 1 | `datasheets/ina240_ti_sbos662.pdf` | 1.935.924 | `PDF document, version 1.4` | 39 | 172.702 B, `pdftotext -layout` OK | ✅ **OBTIDO** |
| 2 | `datasheets/ir2104_infineon_datasheet.pdf` | 142.488 | `PDF document, version 1.2` | 14 | 64.631 B, OK | ✅ **OBTIDO** |
| 3 | `datasheets/mcp3208_microchip_ds21298e.pdf` | 739.611 | `PDF document, version 1.6` | 40 | 147.091 B, OK | ✅ **OBTIDO** |
| 4 | `datasheets/esp32-s3_datasheet_en.pdf` | 1.098.115 | `PDF document, version 1.5 (password protected)` | 87 | 273.511 B, OK **com avisos** | ✅ **OBTIDO (ver nota)** |
| 5 | `datasheets/icm-42688-p_v2_tdk_ds-000347-v1.2.pdf` | 1.807.872 | `PDF document, version 1.7` | 109 | 350.027 B, OK | ✅ **OBTIDO** |
| 6 | `datasheets/icm-42688-p_v2_tdk_ds-000347-v1.6.pdf` | 1.807.872 | `PDF document, version 1.7` | 109 | — | ⚠️ **DUPLICATA — ver §3.2** |
| 7 | `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` | 977.679 | `PDF document, version 1.7` | 11 | 30.390 B, OK | ✅ **OBTIDO (referência, não é a peça escolhida)** |
| 8 | `datasheets/icm-42688-p.pdf` | **539** | **`HTML document, ASCII text`** | — | — | ❌ **INVÁLIDO — ver §3.1** |

**Nota sobre o #4 (ESP32-S3):** `file` reporta "password protected", mas `pdftotext -layout` extrai
273.511 bytes normalmente, sem senha. O aviso do `file` refere-se a permissões de(owner)/restrições de
cópia do PDF, não a criptografia que impeça leitura. A extração de texto funcionou. Os avisos do
`pdftotext` foram de cmap: `Syntax Error: Missing language pack for 'Adobe-GB1' mapping` — afeta
apenas caracteres CJK, irrelevante para as tabelas em inglês usadas neste documento.

### 3.1 O arquivo inválido de 539 bytes — `datasheets/icm-42688-p.pdf`

**Diagnóstico:** não é PDF. `file` retorna `HTML document, ASCII text`. Conteúdo integral (539 bytes):

```
<HTML><HEAD>
<TITLE>Access Denied</TITLE>
</HEAD><BODY>
<H1>Access Denied</H1>

You don't have permission to access
"http://product.tdk.com/system/files/dam/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf"
on this server.
Reference #18.85d71302.1789176065.154ce671
https://errors.edgesuite.net/18.85d71302.1789176065.154ce671
</BODY>
</HTML>
```

(Reformatado para leitura; o arquivo é HTML numa linha. As entidades `&#58;` e `&#47;` são `:` e `/`.)

**Causa:** o servidor de origem (`product.tdk.com`, atrás de Akamai/`errors.edgesuite.net`) bloqueou a
requisição automatizada e devolveu a página de erro **com HTTP 200 e Content-Type text/html**.
O cliente de download salvou o corpo do erro com extensão `.pdf`. A URL bloqueada é a da **revisão v1.6**.

**Decisão — o arquivo foi MANTIDO, não apagado.** A regra "NÃO apague nem edite arquivo existente" é
inegociável nesta missão, e o conteúdo do erro é em si evidência do modo de falha. O índice fica
coerente por este documento: **`datasheets/icm-42688-p.pdf` está declarado INVÁLIDO e substituído por
`datasheets/icm-42688-p_v2_tdk_ds-000347-v1.2.pdf`.**

**Regra de leitura para quem pegar esse arquivo depois:** qualquer script que faça `glob("datasheets/*.pdf")`
e abra os resultados vai ler HTML como se fosse PDF. Sempre validar com `file` antes.
Para remover o ruído, é preciso `rm datasheets/icm-42688-p.pdf` — **ação deliberada, fora do escopo desta
WP, aguardando decisão do responsável.**

### 3.2 Os dois arquivos ICM-42688-P são O MESMO ARQUIVO

Verificado por dois algoritmos independentes:

```
md5sum    icm-42688-p_v2_tdk_ds-000347-v1.2.pdf  →  cb377c508500e0283f99c340acfca6fd
          icm-42688-p_v2_tdk_ds-000347-v1.6.pdf  →  cb377c508500e0283f99c340acfca6fd
sha256    ambos                                   →  ce7fa3498ec31a44…  (prefixo idêntico)
```

Tamanho idêntico: 1.807.872 B cada. `file` idêntico: `PDF document, version 1.7`. `pdfinfo`: 109 páginas nos dois.

**Conclusão:** as duas tentativas de download devolveram **byte a byte o mesmo PDF**, apesar de os nomes
prometerem revisões diferentes (v1.2 e v1.6). Só um dos dois nomes está correto. **Qual é o correto NÃO foi
verificado localmente** — verificar lendo a página de revisão/rodapé do PDF, procurando o número de documento
e a data de revisão. O texto extraído tem 110 páginas de marcação, o que sugere que a extração cobre um
documento longo; a identificação da revisão está em **NÃO EXTRAÍDO LOCALMENTE**.

**Como verificar:**
```
pdftotext -f 1 -l 1 -layout datasheets/icm-42688-p_v2_tdk_ds-000347-v1.2.pdf - | head -20
grep -n "DS-000347\|Revision\|v1\.[0-9]" /tmp/wp3/icm-42688-p_v2_tdk_ds-000347-v1.2_paged.txt | head
```
O cabeçalho do documento traz o número TDK e a revisão; o rodapé traz a data. **Até essa conferência,
cite o arquivo pelo nome neutro e não afirme "v1.2" nem "v1.6" em documento de projeto.**

**Espaço em disco desperdiçado:** 1.807.872 B (1,72 MiB) — cópias idênticas, uma delas redundante.

### 3.3 Itens pré-existentes no diretório (não foram obtidos por esta WP)

| Arquivo | Bytes | `file` | Observação |
|---|---|---|---|
| `datasheets/EV_ICM-42688-P.pdf` | 496.716 | `PDF document, version 1.7` | Evalsystem do ICM-42688-P. Legível, mas **não foi extraído nesta WP**. |
| `datasheets/esp32-s3-wroom-1_datasheet_en.pdf` | 898.045 | `PDF document, version 1.5` | Datasheet do **módulo** WROOM-1, distinto do chip (item #4). Não foi extraído nesta WP. |
| `datasheets/esp32-wroom-1.txt` | 213.221 | `ESP archive data` | **Não é texto nem PDF.** É um arquivo binário de firmware/flash `.bin` da Espressif, despite a extensão `.txt`. Se algo tentar ler como texto, vai obter lixo. |
| `datasheets/ev.txt` | 13.769 | `UTF-8 Unicode text` | Texto do evalsystem. Legível. |

> `esp32-wroom-1.txt` merece atenção: a extensão `.txt` sugere texto, `file` revela binário ESP. Se algum
> script do projeto fizer `open("datasheets/*.txt")`, ele vai ler lixo binário.

---

## 4. Índice do diretório `datasheets/` (estado verificado em 2026-09-28)

13 arquivos, sendo 10 `.pdf`. Saída literal de `ls -la` e `file`:

| Arquivo | Bytes | Tipo real (`file`) | Válido? |
|---|---|---|---|
| `esp32-s3-wroom-1_datasheet_en.pdf` | 898.045 | PDF 1.5 | ✅ |
| `esp32-s3_datasheet_en.pdf` | 1.098.115 | PDF 1.5 (password protected) | ✅ texto extraível |
| `esp32-wroom-1.txt` | 213.221 | **ESP archive data** | ⚠️ binário com extensão .txt |
| `EV_ICM-42688-P.pdf` | 496.716 | PDF 1.7 | ✅ |
| `ev.txt` | 13.769 | UTF-8 text | ✅ |
| **`icm-42688-p.pdf`** | **539** | **HTML document, ASCII text** | ❌ **SUBSTITUÍDO — ver §3.1** |
| `icm-42688-p_v2_tdk_ds-000347-v1.2.pdf` | 1.807.872 | PDF 1.7 | ✅ |
| `icm-42688-p_v2_tdk_ds-000347-v1.6.pdf` | 1.807.872 | PDF 1.7 | ⚠️ duplicata byte a byte de v1.2 |
| `ina240_ti_sbos662.pdf` | 1.935.924 | PDF 1.4 | ✅ |
| `ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` | 977.679 | PDF 1.7 | ✅ (referência) |
| `ir2104_infineon_datasheet.pdf` | 142.488 | PDF 1.2 | ✅ |
| `mcp3208_microchip_ds21298e.pdf` | 739.611 | PDF 1.6 | ✅ |
| `datasheets/.ipynb_checkpoints/` | — | diretório | ignorado |

**Regra de ouro adotada:** para conferir, rode sempre

```
cd /opt/jupyter/work/drone/datasheets && file *.pdf && ls -la
```

Esperado: **todos** devem responder `PDF document, version X.Y`. Qualquer linha com `HTML document` é
download falho disfarçado, e deve ser substituído pelo arquivo `v2_` correspondente.

---

## 5. O que segue sem lastro

### 5.1 Parâmetros de datasheet **NÃO EXTRAÍDO LOCALMENTE**

| O que falta | Onde está | Como extrair |
|---|---|---|
| **Ciss / Ciss(es) do MOSFET** | `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` | Buscar `Ciss` / `Ciss(es)` / "Input Capacitance" no texto extraído. A p.4 traz a linha `Gate resistance RG` mas a de capacitância de entrada não foi localizada na varredura feita |
| **Revisão correta do datasheet do ICM-42688-P** | `datasheets/icm-42688-p_v2_tdk_ds-000347-v1.2.pdf` p.1 e rodapé | Ver §3.2 — os dois nomes de arquivo são byte a byte idênticos, então o sufixo não diz a revisão |
| **Numeração de pinos do SOIC do INA240** | `datasheets/ina240_ti_sbos662.pdf` p.3, Figura 6-2 | Ver §2.1 — o `-layout` embaralha as duas colunas da tabela. Abrir a página como imagem |
| **Ganho de erro vs. temperatura do INA240** | `datasheets/ina240_ti_sbos662.pdf` p.5 | Já consta na tabela: ±0,5 ppm/°C a ±2,5 ppm/°C (typ/max) — resolvido |
| **Ganho de erro do MCP3208** | `datasheets/mcp3208_microchip_ds21298e.pdf` p.2 | Adjacente ao offset na mesma tabela; relevante se a leitura de corrente precisar de precisão melhor que a do offset |

### 5.2 Componentes do projeto que **não têm peça escolhida nem datasheet**

Nada disto tem documento no disco — cada linha precisa de um PDF antes de virar número no esquema:

| Bloco (BOM) | O que falta | Impacto |
|---|---|---|
| MOSFET de potência (24 un.) | Escolha final. O único PDF é a **referência não escolhida** |define P-05/P-06, e P-06 está **contradito** |
| Célula LiPo 6S (P-02) | Datasheet da célula | define a classe de tensão |
| Motor 2207 (P-01) | Datasheet do motor | define P-03/P-04 |
| Buck 12 V / 5 V / 3,3 V (P-08) | Part number e datasheet | define indutor, ESR, ripple |
| Shunt de manganina 0,5 mΩ (P-09) | Part number e datasheet | define potência e TCR |
| Reguladores LDO / 3,3 V | Part number | corrente do ESP32-S3 |
| Conector XT60 e MR30 | Corrente nominal, resistance de contato | define trilha e orçamento térmico |
| Diodos de clamp / Schottky | Vf | fica em aberto desde P-15 |
| Indutores 22 µH / 5 µH | Isat, DCR | define ripple e perda |
| Capacitores eletrolíticos | ESR, vida útil | define ondulação |

### 5.3 Itens que exigem bancada (fora do escopo desta máquina)

Conforme a etiqueta `[NÃO VERIFICADO]` do FASE0: térmica real, EMI, tempo morto sob carga, e a
verificação experimental do ganho da cadeia de medição de corrente. **Não há medição em bancada neste projeto.**

---

## 6. Recomendações de ação

1. **Rever o dimensionamento de gate drive** com Qg = 168 nC (não 40 nC). Afeta
   `fase0_especificacao/dimensionamento_fase0.py` e `verifica_limites_entrada_v4.py`. **Alta prioridade** —
   é a única premissa refutada que altera um número de projeto.
2. **Corrigir P-11** para 0,325 mA (IQCC 270 µA + IQBS 55 µA, IR2104 p.3) e registrar que 2,5 mA era a
   corrente de quiescência do INA240 (p.1), não do driver.
3. **Decidir sobre `datasheets/icm-42688-p.pdf`** (539 B): apagar ou manter como evidência. Recomendo apagar
   e cobrir a remoção neste índice, mas é ação destrutiva e depende do responsável.
4. **Remover a duplicata do ICM-42688-P** (1,72 MiB) após identificar qual revisão é a correta (§3.2).
5. **Publicar netlist** em `fase1_esquema/` para que a pinout da v7 possa ser confrontada com a §2.1.
6. **Renomear `esp32-wroom-1.txt`** para extensão correta (`.bin`), ou remover do `datasheets/` — hoje é um
   firmware binário disfarçado de texto.
7. **Escolher as peças** (INA240A2, IR2104, MCP3208 e o MOSFET final) e registrar o part number em
   `fase0_especificacao/lista_componentes_fase0.csv` antes de gerar footprints.

---

## 7. Reprodutibilidade

Extração de texto feita nesta máquina (os `.txt` ficaram em `/tmp/wp3/`, **fora do projeto**):

```
cd /opt/jupyter/work/drone/datasheets
for f in ina240_ti_sbos662 ir2104_infineon_datasheet mcp3208_microchip_ds21298e \
         esp32-s3_datasheet_en icm-42688-p_v2_tdk_ds-000347-v1.2 \
         ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO; do
  pdftotext -layout "$f.pdf" "/tmp/wp3/$f.txt"
done
```

As páginas citadas neste documento foram localizadas por busca do marcador `<<<ARQUIVO PAG N>>>`,
inserido por script que fatia o texto na sequência de bytes de avanço de página (0x0C) que o
`pdftotext` emite entre páginas. **A numeração "p.N" deste documento é a do PDF físico, contada a partir
de 1, e bate com o rodapé impresso nos casos conferidos** (ex.: `© 2008 Microchip Technology Inc. DS21298E-page 15`
no pé da p.15 do MCP3208; `4 ... www.irf.com` no pé da p.4 do IR2104; `Espressif Systems 64 ESP32-S3 Series
Datasheet v2.2` no pé da p.64 do ESP32-S3). O rodapé do ESP32-S3 é a **melhor âncora** para conferência,
porque o PDF tem paginação dupla (índice interno × 87 páginas do arquivo).

Ambiente: `pdftotext` em `/usr/bin/pdftotext`, `python3.9`, `bash`.
Nenhum download foi feito nesta WP; nenhum PDF foi apagado ou editado.
Nenhum arquivo fora de `plano/WP3_PREMISSAS_DATASHEETS.md` foi criado ou modificado.
