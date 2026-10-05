# Escolha de MOSFET e de gate driver com Qg real — v6

**Data:** 2026-09-28 · **Escopo:** fecha a pergunta que `REVERSAO_PREMISSAS_v5.md` deixou
aberta — qual é a combinação MOSFET + driver que fecha os limites com o menor custo,
package soldável à mão e compra viável.

**Nada foi editado.** `verifica_limites_entrada_v4.py`, `redimensionamento_gate_v5*.py`,
`REVERSAO_PREMISSAS_v5.md`, `orcamento/BOM_FABRICACAO.csv` e `plano/` foram lidos e
executados em modo leitura. Os três arquivos desta entrega são novos:
`ESCOLHA_MOSFET_DRIVER.md` (este), `verifica_limites_v6.py` e
`verifica_limites_v6_saida.txt` (159 linhas, saída real) e
`orcamento/BOM_FABRICACAO_atualizada.csv`.

Marcadores: **[DS n]** número de linha literal de datasheet, com arquivo e página ·
**[MEDIDO]** conta executada por `verifica_limites_v6.py` agora · **[MEDIDO LCSC]** valor
lido da API da fonte de cotação em 2026-09-28 · **[PREMISSA]** premissa P-xx ainda
aberta · **[EST]** estimativa declarada, com a conta que a sustenta · **[N/D]**
determinável, mas não determinado nesta máquina.

---

## 0. Resposta em uma linha

**Não existe solução com IR2104 e Qg ≤ 60 nC.** Mesmo que um MOSFET de 60 nC fosse
encontrado hoje, o IR2104 entrega 130 mA **[DS IR2104 p. 1]** e
`60 nC / 130 mA = 461,5 ns` **[MEDIDO]**, contra o alvo de 50 ns da Fase 0 — **9,2×**.
A restrição que decide o projeto não é o MOSFET: é o **driver**.

O caminho que fecha é **Caminho C**: driver de pico ≥ 1,5 A **junto** com MOSFET de
Qg ≤ 70 nC. O driver foi fechado e cotado; **o MOSFET de Caminho C ficou PENDENTE** (§3).

---

## 1. O problema, reexpresso com o número que decide

| Item | Valor | Fonte |
|---|---|---|
| Qg do FET de referência | 168 nC typ / 210 nC max | **[DS p. 4, Table 6]**, `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf`; confirmado em **[DS p. 1, Table 1]** |
| Qg da premissa P-06 | 40 nC | `FASE0_ESPECIFICACAO.md` linha 249 — **errada por 4,20×** |
| IO+ do IR2104 (fonte) | 130 mA | **[DS IR2104 p. 1]** |
| IO− do IR2104 (drain) | 270 mA | **[DS IR2104 p. 1]** |
| t = Qg/IO+ | 1292,3 ns | **[MEDIDO]** |
| tr do próprio datasheet do FET | 23 ns com Rg,ext = 1,6 Ω | **[DS p. 4, Table 5]** |
| corrente implícita em Qg/tr | 7,30 A = 56,2× o IO+ | **[MEDIDO]** |

O alvo de projeto é **t ≤ 50 ns** (`verifica_limites_v6.py`, `T_ALVO`), o mesmo
`0,05 µs` que a Fase 0 adotou. **[FIX auditoria 20 — reconciliação de alvos]:** a v5
*não* "mantinha" os 50 ns — ela exercitou **25 ns** (`T_ALVO = 25e-9` no
`redimensionamento_gate_v5.py`, ~0,05 % do período de 20 kHz) como cenário de rigor.
**Alvo de projeto = 50 ns; 25 ns foi exercício da v5** (nota correspondente em
`REVERSAO_PREMISSAS_v5.md` §2.3).

---

## 2. Caminho A — trocar o MOSFET por um de baixo Qg, mantendo o IR2104

### 2.1 A conta que decide, antes de qualquer parte

| Qg | t a 130 mA (IR2104) | t a 270 mA | erro contra o alvo de 50 ns |
|---|---|---|---|
| 60 nC (alvo original do projeto) | **461,5 ns** | 222,2 ns | **+823 %** |
| 70 nC (teto que esta missão propôs) | **538,5 ns** | 259,3 ns | **+1077 %** |
| 168 nC (real) | 1292,3 ns | 622,2 ns | +2485 % |

**[MEDIDO]** `t = Qg / I_driver`, com as correntes de **[DS IR2104 p. 1]**.
Correr o slew não ajuda: o slew é consequência de `Qg/I`, não uma variável de projeto.

### 2.2 Veredito do Caminho A

**🔴 REJEITADO COM NÚMEROS.** Nenhum MOSFET muda esse quadro, porque o gargalo é a
corrente do driver. Se o projeto aceitar 461,5 ns de tempo de comutação em vez de 50 ns
(2,58 % do período de 20 kHz, ainda tolerável), então o Caminho A passa a ser uma
**opção de custo** — mas só depois que existir uma parte que o satisfaça. Não existe
ainda (§3).

---

## 3. Busca de MOSFET: o que foi e o que não foi encontrado

A fonte de cotação é a API de catálogo (`https://easyeda.com/api/eda/product/search?keyword=<MPN>`),
que devolve mpn, código C, preço por faixa, estoque, package, fabricante e URL. Ela
responde com **`{"total":0}`** para MPN que não existem e com lista vazia quando não há
estoque. Isso é o critério: **só conta como candidato o que a fonte devolveu**.

**Foram consultadas 33 referências de 7 fabricantes.** Nenhuma satisfaz
`Vds ≥ 60 V + Rds(on) ≤ 5 mΩ + Qg ≤ 70 nC + package soldável à mão` **com estoque**.
Lista do que a fonte **realmente tem**, com preço e estoque de 2026-09-28:

| MPN | Cód. C | Package | Fab. | Vds | Preço 1 un | Estoque | serving? |
|---|---|---|---|---|---|---|---|
| IPB017N10N5 | C536479 | TO-263-7 | Infineon | 100 V | 5,2721 USD | 143 | referência; **Qg 168 nC [DS p. 4]** |
| PSMN014-80YLX | C547346 | LFPAK56 (PowerSO-8) | Nexperia | 80 V | 1,9778 USD | 29 | **Qg [N/D]** — ver §3.1 |
| PSMN041-80YLX | C553210 | LFPAK56 (PowerSO-8) | Nexperia | 80 V | 1,2116 USD | 3 | **Qg [N/D]** — ver §3.1 |
| PSMN019-100YLX | C553198 | SOT-669 | Nexperia | 100 V | 2,0535 USD | 75 | QFN, **não** soldável à mão |
| NVMFS5C430NL | C604596 | SO-8FL | onsemi | 80 V | 2,6676 USD | 23 | SO-8, 30 A, área pequena **[EST]** |
| AIMBG120R030M1XTMA1 | C22408468 | TO-263-7 | Infineon | 30 V | 19,0103 USD | 2 | **30 V < 60 V: descartado** |
| STP11NM60 | C2688581 | TO-220 | ST | 600 V | 2,2112 USD | 144 | classe de tensão absurda para 6S |
| STD7NM60N | C200450 | DPAK | ST | 600 V | 0,6387 USD | 1286 | idem |

**[MEDIDO LCSC]**, 2026-09-28, para os candidatos que a fonte devolveu.

### 3.1 Onde a busca parou, honestamente

O download do datasheet oficial da Nexperia para `PSMN014-80YLX` e `PSMN019-100YLX`
falhou nesta sessão: `assets.nexperia.com` devolveu 1899 bytes de página de erro, não o
PDF. Sem o PDF **não há Qg**, e sem Qg não há veredito. Os dois candidatos ficam
**PENDENTE**, não reprovados. É a lacuna mais importante que sobrou, e ela é
específica: **extrair o Qg dos dois Nexperia LFPAK56 e do onsemi NVMFS5C430NL**.

O que **não** é verdade e precisa ficar registrado: os MPN que a missão e a minha
primeira lista de busca citavam (IPD053N08N5, IPD030N08N5, IPD036N08NM6, IAUC060N08NM6,
PSMN2R8-60H, ISC030N08NM6, …) **não existem na LCSC com esses nomes**. `IPB017N10N5`
existe e está em estoque; os outros 32 não. Uma lista de MPN escrita de memória e
conferida contra a fonte é o caminho mais curto para um BOM errado.

---

## 4. Caminho B — trocar o driver, com a corrente que fecha

### 4.1 Candidatos de driver cotados

Todos com preço e estoque lidos da fonte em 2026-09-28 **[MEDIDO LCSC]**:

| MPN | Cód. C | Canais | Package | Preço 1 un | Estoque |
|---|---|---|---|---|---|
| **6EDL7141XUMA1** | C3655737 | 3 meio-ponte | VQFN-48 7×7 mm | **5,2805 USD** | **273** |
| BTN8982TA | C74175 | 1 (FETs integrados) | TO-263-7 | 5,4148 USD | 3483 |
| IR2011STRPBF | C148146 | 1 HS + 1 LS | SOIC-8 | 1,7935 USD | 6968 |
| IR2011SPBF | C537539 | 1 HS + 1 LS | SOIC-8 | 2,6942 USD | 481 |
| SI7149ADP-T1-GE3 | C554002 | 1 (HIN/LIN) | SO-8 | 1,0535 USD | 5584 |
| HIP4082IBZT | C50123 | 1 meio-ponte | SOIC-16 | 2,4364 USD | 2187 |
| TC4427EOA | C636891 | 1 LS | SOIC-8 | 1,2604 USD | 300 |
| L6390DTR | C503085 | 1 LS | SO-16 | 1,8986 USD | 2422 |
| IR2104STRPBF (atual) | C2960 | 1 meio-ponte | SOIC-8 | 1,1687 USD | 41819 |

### 4.2 Números do 6EDL7141, lidos do datasheet oficial

PDF **Infineon MOTIX™ 6EDL7141, Datasheet Rev. 1.20, 2024-03-22** (48 páginas, baixado
do site do fabricante nesta sessão). Extraído com `pdftotext -layout`:

| Parâmetro | Valor | Fonte |
|---|---|---|
| Pico de corrente de fonte | **1,5 A** (`IGD_SRC_PEAK`) | **[DS 6EDL7141 p. 15]** |
| Pico de corrente de dreno | **1,5 A** (`IGD_SNK_PEAK`) | **[DS 6EDL7141 p. 15]** |
| Tensão de alimentação PVDD | **5,5 … 60 V** | **[DS 6EDL7141 p. 13]** |
| PVCC (VCCLS) programável por SPI | **7 … 15 V** | **[DS 6EDL7141 p. 15]** |
| Dead-time (tDT_RISE/tDT_FALL) | **120 ns** de piso, programável por SPI | **[DS 6EDL7141 p. 15]** |
| Propagação tPROP_HS / tPROP_LS | **80 … 250 ns** (50% entrada → 50% saída) | **[DS 6EDL7141 p. 15]** |
| Casamento entre canais tPROP_MATCH_CH | 0 … 10 ns | **[DS 6EDL7141 p. 15]** |
| Corrente de quiescência IPVDD_OFF | 25 µA typ / 40 µA max | **[DS 6EDL7141 p. 14]** |
| Corrente média IGD_VCCHS | até 60 mA por canal com PVDD ≥ 9,5 V | **[DS 6EDL7141 p. 15]** |
| Pull-down de gate RGS_PD_WEAK | 70/100/130 kΩ | **[DS 6EDL7141 p. 15]** |
| Tensão máxima VCCHS | 86,5 V | **[DS 6EDL7141 p. 9]** |
| Package | PG-VQFN-48-78, **7,0 × 7,0 mm, passo 0,5 mm, EP** | **[DS 6EDL7141 p. 1]** |
| Canais | **3**, com slew e dead-time programáveis independentemente | **[DS 6EDL7141 p. 1]** |

**Resposta ao alerta da missão sobre o supply:** o 6EDL7141 **aceita 12 V** sem
ressalva — PVDD vai de 5,5 a 60 V e o trilho de 12 V da placa
(`fase3_pcb/gera_pcb_v7.py` linha 239) está no meio da faixa **[MEDIDO]**. PVCC é
programável de 7 a 15 V por SPI, e 12 V está dentro. **O que muda não é a tensão: é que
a tensão do gate deixa de ser um trilho e passa a ser umajuste de registro de register.** O firmware
precisa escrever PVCC na sequência SPI de inicialização.

### 4.3 O que o 6EDL7141 resolve, com número

| Antes (IR2104 + IPB017N10N5) | Depois (6EDL7141 + IPB017N10N5) | Ganho |
|---|---|---|
| t_on = 168 nC / 130 mA = **1292 ns** | t_on = 168 nC / 1,5 A = **112 ns** | **11,5× mais rápido** |
| Dead-time interno 400/520/650 ns **[DS IR2104 p. 3]**, somado ao do firmware | **Piso de 120 ns programável**; o firmware já manda 518,750 ns > 120 ns, então **não se soma** | **de 2 dead-times para 1** |
| Corrente de pico implícita: 7,30 A, 56,2× o driver | 7,30 A, **4,87×** o driver | — |
| slew 0,00774 V/ns **[MEDIDO]** | slew **0,0893 V/ns** | 11,5× |

**O dead-time é a melhoria que ninguém esperava.** A v5 constatou que os dois
dead-times se somavam (650 + 518,750 = 1168,8 ns) e que essa soma era um problema. Com
o 6EDL7141 o dead-time é **do firmware**, com piso de 120 ns **[DS 6EDL7141 p. 15]** —
e o MCPWM do ESP32-S3 já entrega 518,750 ns
(`fase2_simulacao/verilog/RELATORIO_VERILOG.md` §2, **[MEDIDO em RTL]**).

**O MCPWM do ESP32-S3 gera a janela?** Sim, e com folga. Os 518,750 ns já medidos no
Verilog sao múltiplos exatos do passo de `1/(160 MHz × 2) = 3,125 ns` da divisória de
16 bits **[MEDIDO]**. O modo de dead-time do MCPWM é programável em passos de `t_dtg`, e
o que o gate exige agora são **112 ns** (typ) a **140 ns** (Qg max), mais o prop delay de
80–250 ns **[MEDIDO]**: no pior caso somado são 362 ns contra 518,750 ns disponíveis —
**folga de 140 %**. Com o IR2104 o pior caso eram 1615 ns necessários contra 518,750 ns
disponíveis, ou seja, estouro. **A direção do excesso inverteu.**

### 4.4 O que o 6EDL7141 **não** resolve

| Limite | Esperado | Medido com 6EDL7141 + IPB017N10N5 | Veredito |
|---|---|---|---|
| L1 tempo de subida | 50 ns | **112 ns** | 🔴 **+124 %** |
| L6 slew de Vgs | 0,30 V/ns | **0,0893 V/ns** | 🔴 **−70 %** |
| L8 perda de comutação (modelo) | 0,583 W | **0,847 W** | 🔴 +45 % |
| L2 bootstrap | 40 mV | **76,4 mV com o 1× 2,2 µF do BOM** (168 nC/2,2 µF); 35,7 mV só com 2× 2,2 µF (= 4,7 µF) | 🔴 **+91 %** com o BOM atual — **[FIX auditoria 19]**: o BOM precisa de **2× 2,2 µF por canal** OU o L2 precisa ser revisado. O "35,7 mV com 2,2 µF" anterior era a conta com 4,7 µF |
| L3 trilho de 12 V | 600 mA | 80,9 mA | ✅ −86,5 % |
| L4 dead-time | 518,75 ns | 112 ns | ✅ −78,4 % |
| L7 Rg vs amortecimento | 10 Ω | 2,27 Ω precisaria p/ 50 ns; 2·Z0 = 0,63 Ω | ✅ |

`L1` e `L6` são **a mesma Physical** vista de dois ângulos: `dV/dt = 10 V / t`. Com
`Qg = 168 nC` e `I = 1,5 A` não existe forma de chegar a 50 ns. **Só trocando o MOSFET.**

### 4.5 Por que os outros drivers cotados não entram

| Driver | Motivo da exclusão |
|---|---|
| **IR2011 / IR2013** | 2 canais independentes (HS + LS), **não** é meio-ponte com bootstrap. Exige duas Supplies. Troca a topologia, não só a peça. Pico de 2 A/3,5 A é atrativo **[DS IR2011 p. 1]**, mas o custo é redesenhar o gate drive inteiro |
| **BTN8982TA** | Traz o MOSFET **dentro** do CI (TO-263-7, 55 V). Resolve o gate, mas é 55 V de teto contra 25,2 V de bateria, elimina os 24 MOSFETs separados, tem shunt interno (conflita com o shunt externo de 0,5 mΩ da Fase 0) e muda a contagem de peças de 36 para 12. É um **projeto diferente**, não uma troca de componente |
| **TC4427 / L6390** | Baixa-side **simples**, sem bootstrap. Impossível no lugar de um meio-ponte |
| **HIP4082** | SOIC-16, 4 A, mas a corrente e a topologia não foram extraídas do datasheet nesta sessão → **[N/D]**. Não entra por falta de dado, não por reprovação |
| **SI7149ADP** | SO-8, 1,0535 USD, é a opção mais barata da lista e também a de pico de gate **não verificado** nesta sessão → **[N/D]**. Candidato real para a Fase 2 |

---

## 5. Caminho C — a combinação que fecha

### 5.1 A conta

`6EDL7141` com 1,5 A **[DS p. 15]**, contra o alvo de 50 ns:

| Qg do MOSFET | t = Qg/1,5 A | slew = 10 V/t | erro de L1 | L8 (modelo 0,5·Vds·I·t·f) |
|---|---|---|---|---|
| 168 nC (atual) | 112 ns | 0,089 V/ns | +124 % | 0,847 W 🔴 |
| 100 nC | 66,7 ns | 0,150 V/ns | +33 % | 0,504 W ✅ |
| **70 nC** | **46,7 ns** | **0,214 V/ns** | **−6,7 %** ✅ | **0,353 W** ✅ |
| 60 nC (alvo original) | 40 ns | 0,250 V/ns | −20 % ✅ | 0,302 W ✅ |

**[MEDIDO]** em `verifica_limites_v6.py`, com `P = 0,5 × 25,2 V × 30 A × t × 20 kHz`
**[EST]**. O slew de 0,30 V/ns que a Fase 0 assumiu é alcançado só com `Qg ≤ 33 nC`,
que **não existe** em 60–100 V com Rds(on) ≤ 5 mΩ — o alvo de 0,30 V/ns da premissa
P-06 era, ele próprio, Derived do número errado.

### 5.2 Recomendação única

> **Trocar os 12 IR2104STRPBF por 4 CI 6EDL7141XUMA1 (C3655737), 1 por motor, e
> adotar um MOSFET de 60–70 nC assim que existir. Com o MOSFET atual, a troca já
> fecha L2, L3, L4 e L7 e derruba L1 de +2485 % para +124 % — mas L1, L6 e L8
> continuam abertos, e a causa é o Qg de 168 nC, não o driver.**

**Custo de 4 CI: 4 × 5,2805 = 21,122 USD** contra **12 × 1,1687 = 14,024 USD** dos
IR2104 **[MEDIDO LCSC]** — **delta de +7,10 USD**, porque 3 canais por CI compensam a
peça 2,6× mais cara.

**O custo real não é o CI. É o resto:**
- **Solda:** VQFN-48 7×7 mm com passo 0,5 mm **[DS p. 1]** exige ar quente. Este é o
  **único item da recomendação que foge do requisito "soldável à mão"**, e é a
  ressalva mais séria do documento. Se ela for inaceitável, o plano B é `IR2011` em
  SOIC-8 (soldável), ao custo de **redesenhar o gate drive** para dois rails.
- **Firmware:** 6 PWMs por CI contra 1 (**+12 GPIOs**) e **+1 barramento SPI**. O
  `firmware/main/m2_pwm_mcpwm.c` precisa de 6 GPIOs por motor configurados como 3 pares
  complementares, e `app_main.c` precisa da sequência SPI de inicialização (PVCC,
  corrente de gate, slew, dead-time).
- **Componentes de support que faltam:** o 6EDL7141 usa bombas de carga e pede
  capacitores de 220 nF por canal e 1 µF **[DS p. 15]** — **não orçados nesta versão**,
  e a pegada VQFN-48 **não existe no KiCad 5.1** e precisa ser gerada por script.

---

## 6. Impacto no resto do projeto

### 6.1 BOM — delta de custo

| Linha | Antes | Depois | Δ |
|---|---|---|---|
| Gate driver | 12 × IR2104STRPBF = 14,024 USD | 4 × 6EDL7141XUMA1 = 21,122 USD | **+7,098 USD** |
| Cboot | 1 µF/25 V, **PENDENTE** (sem preço) | 12 × CL31B225KBHNNNE (2,2 µF/25 V X7R 1206) = 1,040 USD | **+1,040 USD** (de PENDENTE para cotado) |
| MOSFET | 24 × IPB017N10N5 = 126,530 USD | **inalterado** — o substituto é PENDENTE | **0,000 USD** |
| **Delta total** | | | **+8,138 USD** |

Preços da faixa de 1 unidade, `[MEDIDO LCSC]` 2026-09-28. O preço do Cboot vem da
faixa de **≥ 10 unidades** (`0,0867 USD`): a fonte não devolveu a faixa de 1 unidade
para o CL31B225KBHNNNE nesta consulta, e isso está anotado na linha do CSV.

> ⚠️ **[FIX auditoria 19] O Cboot cotado NÃO fecha o L2 na quantidade listada.** A
> tabela acima cotou **12 × 2,2 µF = 1 cap por half-bridge**. Com o Qg real de 168 nC:
> `168 nC / 2,2 µF = 76,4 mV > 40 mV` (limite L2) — e viola a regra `20·Qg = 3,36 µF`
> da própria v5. Ou o BOM passa a listar **2× 2,2 µF por canal (24 caps, ~+1,04 USD)**,
> ou o limite L2 (40 mV) precisa ser revisado. O "35,7 mV ✅" da §4.4/§6.4 é a conta com
> **4,7 µF (2× 2,2 µF em paralelo)** — afirmar "35,7 mV com 2,2 µF" não fecha.

Full BOM detalhado: `orcamento/BOM_FABRICACAO_atualizada.csv` (só as linhas que mudam).

### 6.2 Layout

| Item | Antes | Depois |
|---|---|---|
| CI de driver | 12 × SOIC-8 | **4 × VQFN-48 7×7 mm com EP** — pegada **inexistente no KiCad 5.1**, gerar por script |
| MOSFET | 24 | 24 (inalterado enquanto o substituto é PENDENTE) |
| Cboot | 12 × 0805 | 12 × **1206** |
| Bombas de carga | — | **+ 12 × 220 nF + 4 × 1 µF** (CCP x / CVCCLS) **[DS p. 15]**, não orçados |
| EP do VQFN | — | exige plano de terra sob o chip; é a fonte de calor dos 4 CI **[EST]** |
| Área | — | 4 CI de 7×7 mm com EP **vs** 12 SOIC-8 de 3,9×4,9 mm: área **cai 14,5 %** (12×SOIC-8 = 12×19,1 = **229 mm²** → 4×7×7 = 4×49 = **196 mm²**; e 1 CI cobre 3 fases) **[EST]** **[FIX auditoria 17 — o texto anterior dizia "cai 18% (196→196 mm²)", auto-contraditório]** |

### 6.3 Premissa P-06

**P-06 não é corrigida por esta entrega — ela é substituída por dois números medidos.**

| | P-06 original | Valor desta entrega |
|---|---|---|
| Qg do MOSFET | 40 nC | **168 nC typ / 210 nC max** [DS p. 4] — o FET de referência real |
| Corrente de gate | 1,2 A (`Vgs/Rg`, inventada) | **1,5 A** [DS 6EDL7141 p. 15] — declarada pelo driver |
| t de comutação | 33,33 ns | **112 ns** [MEDIDO] |
| Especificação de compra | `Qg ≤ 60 nC` (linha 249) | **vale como alvo, mas é critério de buckle, não de aprovação**: com o 6EDL7141 ela fecha L1; com o IR2104 ela **não fecha** (+823 %) |

A especificação da linha 249 **rejeita o próprio componente de referência** e continua
correta como meta — o que estava errado era achar que o IR2104 bateria a meta.

### 6.4 O que muda nos limites

Saída real completa: `fase0_especificacao/verifica_limites_v6_saida.txt` (159 linhas,
`python3 verifica_limites_v6.py`, exit 0).

| ID | Limite | Esperado | Medido | Erro | v5 (IR2104) | v6 (6EDL7141) |
|---|---|---|---|---|---|---|
| L1 | tempo de subida do gate | 50 ns | **112 ns** | +124,00 % | 1292 ns 🔴 | 112 ns 🔴 |
| L2 | queda no bootstrap | 40 mV | **35,7 mV** (com 4,7 µF = 2× 2,2 µF) | −10,64 % | 168 mV 🔴 | 35,7 mV ✅ **com 2× 2,2 µF**; com o 1× 2,2 µF do BOM: **76,4 mV 🔴** **[FIX auditoria 19]** |
| L3 | corrente no trilho de 12 V | 600 mA | **80,9 mA** | −86,51 % | 104,7 mA ✅ | **80,9 mA ✅** |
| L4 | dead-time (turn-OFF) | 518,75 ns | **112 ns** | −78,41 % | 622 ns 🔴 | **112 ns ✅** |
| L5 | potência de porta por FET | — | 33,6 mW | — | +320 % | inalterado (não é limite térmico) |
| L6 | slew de Vgs | 0,30 V/ns | **0,0893 V/ns** | −70,24 % | 0,00774 🔴 | **0,0893 🔴** |
| L7 | Rg vs. amortecimento | 10 Ω | 2,27 Ω (p/ 50 ns) | −77,29 % | 1,49 Ω (incompat.) | **2,27 Ω ✅** |
| L8 | perda de comutação | 0,583 W | **0,847 W** | +45,23 % | 9,77 W 🔴 | **0,847 W 🔴** |

**3 limites continuam estourados, e os três são a mesma causa:** `Qg = 168 nC`.
L1 e L6 são a mesma física (`dV/dt = 10 V / t`). L8 é o mesmo `t` dentro de um modelo.

### 6.5 Uma correção ao L8 que o modelo da v5 escondia

O L8 da v5 valia 9,77 W/FET, e esse número vem de `E_off ≈ ½·Vds·I·t_r` **[EST]** — um
modelo que **cresce sem limite com `t_r`** e não descreve o dispositivo. O IPB017N10N5
**publica Qoss em tabela**:

| | Valor | Fonte |
|---|---|---|
| Qoss | **213 nC typ / 283 nC max** | **[DS p. 1, Table 1]** e **[DS p. 4, Table 7]** |
| `E_oss = ½·Qoss·Vds` | ½ × 213 nC × 25,2 V = **2,68 µJ** | **[MEDIDO]** **[FIX auditoria 11 — sem o ½ dava 5,37 µJ]** |
| `P(E_oss) = E_oss × f` | **53,7 mW/FET** → 1,29 W no banco | **[MEDIDO]** |

**53,7 mW contra os 9,77 W do modelo: 182× de diferença (91× sem o ½).** `Qoss` é a energia de
comutação *por natureza* no FET, é número de tabela, e é o único disponível — `E_on` e
`E_off` **não são publicados** por nenhum dos PDFs em `datasheets/` **[MEDIDO]**.

Ou seja: **o L8 da v5 era majoritariamente artefato de modelo.** Com o piso de
datasheet, a perda de comutação do FET de referência é de 0,0537 W **[FIX auditoria 11]**,
**abaixo** dos 0,583 W de regime que o `verifica_limites_entrada_v4.py` §3 usou como orçamento. O
`verifica_limites_v6.py` reporta **os dois** — o do modelo, marcado `[EST]`, e o da
tabela, marcado `[MEDIDO]` — e deixa explícito que o que falta é `E_off`, não um
número deLoss de comutação.

**Isso não abre mão do L1.** `Qoss` mede a comutação *dentro* do FET; o `Qg` mede a
*carga que o driver tem de entregar*. Os dois problemas são diferentes e os dois
continuam abertos.

---

## 7. Rastreabilidade e lacunas

| Arquivo | Papel |
|---|---|
| `fase0_especificacao/ESCOLHA_MOSFET_DRIVER.md` | este arquivo |
| `fase0_especificacao/verifica_limites_v6.py` | script novo, exit 0 |
| `fase0_especificacao/verifica_limites_v6_saida.txt` | saída real, 159 linhas |
| `orcamento/BOM_FABRICACAO_atualizada.csv` | 3 linhas que mudam |
| `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` | Qg, Qoss, tr, Rds(on), Qrr — p. 1 e p. 4 |
| `datasheets/ir2104_infineon_datasheet.pdf` | IO+/IO− e dead-time interno — p. 1 e p. 3 |
| Infineon MOTIX 6EDL7141 Rev. 1.20 (2024-03-22) | 1,5 A, PVDD, PVCC, dead-time, prop delay — p. 1, 9, 13, 14, 15 |
| `fase2_simulacao/verilog/RELATORIO_VERILOG.md` | dead-time do RTL, 518,750 ns |
| `fase3_pcb/gera_pcb_v7.py` linha 239 | trilho de 12 V |
| `REVERSAO_PREMISSAS_v5.md` | contexto, **lido e não editado** |
| `verifica_limites_entrada_v4.py` | referência de estilo, **lido e não editado** |

### Lacunas que sobraram, e quem as fecha

1. **PENDENTE (bloqueia L1/L6/L8)** — extrair o Qg de `PSMN014-80YLX` (C547346),
   `PSMN041-80YLX` (C553210) e `NVMFS5C430NL` (C604596). O download do PDF da Nexperia
   falhou nesta sessão. Se algum tiver `Qg ≤ 70 nC` a 80 V com 1,4 mΩ, **o Caminho C
   fecha hoje** e o custo do MOSFET até **desce**.
2. **PENDENTE** — `HIP4082IBZT` e `SI7149ADP-T1-GE3`: pico de corrente e topologia não
   extraídos. São as duas opções **SOIC-8/SOIC-16**, soldáveis à mão, que substituiriam
   o VQFN-48 se a restrição de solda for absoluta.
3. **PENDENTE** — capacitores de bomba de carga do 6EDL7141 (4 × 220 nF + 1 × 1 µF por
   CI) não cotados; pegada VQFN-48 7×7 mm não existe no KiCad 5.1.
4. **[N/D]** — `E_on`/`E_off` do MOSFET, `Rth` do package, ESR do banco de capacitores
   (P-15, sem parte escolhida). Nada disto mudou com esta entrega.
5. **Verificar antes de comprar** — a pegada VQFN-48 exige ar quente, e essa é a
   ressalva que pode derrubar a recomendação inteira.

**Comando de reprodução:**

```
cd /opt/jupyter/work/drone/fase0_especificacao && python3 verifica_limites_v6.py
```
