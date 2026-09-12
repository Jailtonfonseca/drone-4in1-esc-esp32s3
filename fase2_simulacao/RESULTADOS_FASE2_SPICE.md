# RESULTADOS FASE 2 — Simulação SPICE (ngspice)

**Projeto:** Drone 4xESC + ESP32-S3 — pack LiPo 6S (25,2 V máx / 19,8 V mín)
**Pasta:** `fase2_simulacao/`
**Máquina:** Linux **aarch64** · **ngspice-34**
**Data da rodada:** 2026-09-11
**Ferramentas usadas:** somente `ngspice -b`. **Não** foram usados LTspice, Proteus,
PSpice, Multisim nem qualquer ferramenta x86/Windows (não existem nesta máquina).

---

## 0. Regra de honestidade seguida

Todo valor **MEDIDO** deste relatório saiu de um `.log` gerado de verdade por
`ngspice -b <circuito>.cir > <circuito>.log 2>&1`. Nada foi digitado à mão: o script
`gera_tabela.py` **lê os logs** e monta a tabela e o CSV; se um valor não estiver no
log, o script **aborta** em vez de inventar. Todo valor **ESPERADO** é calculado
analiticamente com a fórmula escrita dentro do próprio `.cir` (seção de comentários
`FORMULA DO VALOR ESPERADO`).

**Nenhuma simulação falhou por convergência.** As 8 rodadas convergiram. As duas
dificuldades reais que apareceram estão registradas na §5, inclusive as que quase
produziram resultado enganoso.

---

## 1. Resumo executivo da tabela ESPERADO × MEDIDO × ERRO

| Circuito | Grandeza | Esperado | Medido | Erro |
|---|---|---|---|---|
| **buck12** | Vout média (com Ron+DCR) | 11,9802306 V | 11,98023 V | **5,4e-6 %** |
| buck12 | Vout média (D·Vin ideal, valor do enunciado) | 11,9988 V | 11,98023 V | 0,1548 % |
| buck12 | dIL pk-pk | 0,10623657 A | 0,1062386 A | **0,0019 %** |
| buck12 | Ripple de saída pk-pk | 634,21 µV | 634,03 µV | 0,0278 % |
| buck12 | iL média (=Iout) | 0,5990115 A | 0,5990108 A | 0,00012 % |
| buck12 | Vsw média | 11,998201 V | 11,99820 V | 8,2e-6 % |
| buck12 | Corrente diodos de corpo D1/D2 | 0 A | **0 A (exato)** | 0 |
| **buck5** | Vout média (com Ron) | 5,0019992 V | 5,001999 V | **4,0e-6 %** |
| buck5 | Vout média (D·Vin ideal) | 5,004 V | 5,001999 V | 0,040 % |
| buck5 | dIL pk-pk (calculado) | 0,3432155 A | 0,3432523 A | **0,0107 %** |
| buck5 | dIL pk-pk (**número do enunciado: 0,246 A**) | 0,246 A | 0,3432523 A | **39,5 % ⚠ §4.1** |
| buck5 | Ripple de saída pk-pk | 2,0472 mV | 2,0451 mV | 0,0998 % |
| buck5 | iL média (=Iout) | 2,0007997 A | 2,000800 A | 1,6e-5 % |
| **buck3v3** | Vout média (com Ron) | 3,2985007 V | 3,298501 V | **9,7e-6 %** |
| buck3v3 | Vout média (D·Vin ideal) | 3,3 V | 3,298501 V | 0,0454 % |
| buck3v3 | dIL pk-pk (calculado) | 0,4488 A | 0,4489519 A | **0,0338 %** |
| buck3v3 | dIL pk-pk (**número do enunciado: 0,178 A**) | 0,178 A | 0,4489519 A | **152,2 % ⚠ §4.2** |
| buck3v3 | Ripple de saída pk-pk | 2,6875 mV | 2,6854 mV | 0,0801 % |
| buck3v3 | iL média (=Iout) | 1,4993185 A | 1,499318 A | 3,3e-5 % |
| **divisor_vbat** | Vout no `.op` (Vin=25,2 V) | 3,0364116 V | 3,036412 V | **1,3e-5 %** |
| divisor_vbat | Ganho DC | −18,38080 dB | −18,38105 dB | 0,0014 % |
| divisor_vbat | fc (−3 dB) | 132,0870 Hz | 132,0947 Hz | 0,0058 % |
| **bemf_div** | Vout no `.op` (Vin=25,2 V) | 2,7391304 V | 2,739130 V | **1,6e-5 %** |
| bemf_div | Ganho DC | −19,27576 dB | −19,27576 dB | 1,8e-5 % |
| bemf_div | fc (−3 dB) | 178 564,1 Hz | 178 564,2 Hz | **6,6e-5 %** |
| **gate_drive** | Tempo de subida do gate 10–90 % | 87,889 ns | 87,88888 ns | 0,00012 % |
| gate_drive | Droop do bootstrap (50 µs) | 65,000 mV | 65,00000 mV | **0 (exato)** |
| **shunt_amp** | Tensão no shunt | 15,000 mV | 15,00000 mV | **0 (exato)** |
| shunt_amp | Vout (ganho ideal 50 — enunciado) | 0,750 V | 0,7496177 V | 0,0510 % |
| shunt_amp | Vout (com ganho finito A=1e5) | 0,7496177 V | 0,7496177 V | **6,7e-7 %** |
| shunt_amp | Corrente no shunt | 30,000 A | 30,00000 A | 0 |
| **prot_inversao** | (a) corrente na carga | 1,9760528 A | 1,976048 A | 0,00024 % |
| prot_inversao | (a) queda dreno-source | 39,4717 mV | 39,51546 mV | 0,111 % |
| prot_inversao | (b) corrente com polaridade invertida | ~1e-12 A (critério < 1 mA) | **−4,061e-11 A** | ver §3.8 |

*(a tabela completa, com a coluna "fonte do esperado" e a chave de cada medida no log,
está em `resultados_fase2_spice.csv`, 35 linhas, gerado por `gera_tabela.py`)*

---

## 2. O ponto metodológico mais importante desta rodada

**Uma janela de 200 µs não mede regime permanente nestes bucks.**

Os três bucks têm filtro LC de saída **subamortecido**:

| circuito | Q = R·√(C/L) | τ da oscilação de partida | f da oscilação |
|---|---|---|---|
| buck12 | 14,06 | ≈ 1,7 ms | ≈ 2,5 kHz |
| buck5 | 4,02 | ≈ 0,22 ms | ≈ 5,8 kHz |
| buck3v3 | 6,53 | ≈ 0,19 ms | ≈ 10,7 kHz |

Sem realimentação (não há malha de controle nos netlists), a partida excita essa
oscilação e ela leva **milissegundos** para morrer. Medir `AVG` numa janela de
200–400 µs devolveria o **transitório de partida**, não o regime.

**Como isso foi tratado (dois caminhos independentes):**

1. **Condição inicial analítica + prova de regime.** O `.ic` foi calculado *à mão* a
   partir do balanço de volts-segundo (valor médio de Vout e o **vale** da corrente do
   indutor, não a média — usar a média foi um erro que *excitava* o ringing e foi
   detectado e corrigido). A prova de que o regime foi atingido está **no próprio log**:
   as médias de janelas sucessivas coincidem, p.ex. no `buck12.log`:

   ```
   vout_jan1 = 1.198024e+01   (100-110 us)
   vout_jan2 = 1.198027e+01   (1,00-1,01 ms)
   vout_jan3 = 1.198024e+01   (3,00-3,01 ms)
   vout_jan4 = 1.198023e+01   (4,99-5,00 ms)   -> dispersão 0,4 uV em 11,98 V
   ```

2. **Rodada de controle partindo do zero, sem nenhum `.ic`.** `_testes/diag3.cir` roda
   20 ms (1 681 871 pontos) com `uic` e tudo zerado:

   ```
   a5  = 12,24458 V   a10 = 12,02952 V   a15 = 11,99649 V   a20 = 11,99815 V
   ```

   Converge para **11,99815 V**, contra o analítico `<Vsw> = D·Vin = 11,9982 V`
   (erro 4e-5 %). Ou seja: a condição inicial analítica **não maquia** o resultado —
   o valor de regime é o mesmo que a rede encontra sozinha, só que depois de ~15 ms.

---

## 3. Análise circuito por circuito

### 3.1 buck12.cir — 19,8 V → 12 V, 500 kHz, L=89 µH (DCR 30 mΩ), 2×22 µF, 0,6 A

- Esperado ideal: `Vout = D·Vin = 0,606 × 19,8 = 11,9988 V`
- Esperado com perdas (balanço de volts-segundo):
  `Vout = D·Vin / (1 + (Ron+DCR)/R) = 11,9988/1,00155 = 11,9802306 V`, `I = 0,5990115 A`
- **Medido: 11,98023 V → erro 5,4e-6 %.** Os 0,155 % de "erro" contra o 11,99 do
  enunciado são **exatamente** a queda em Ron (1 mΩ da chave) + DCR (30 mΩ), prevista
  na fórmula. A `Vsw` média medida (11,99820 V) confirma o modelo: 11,9988 − 0,599·1m.
- `dIL = 0,1062386 A` vs 0,10623657 A analítico → 0,0019 %.
- **Ripple de saída: 634,03 µV** pk-pk medidos.

  > ⚠️ O enunciado estima "~0,6 mV + ~0,53 mV ≈ 1,1 mV". **Não é 1,1 mV.** Duas razões:
  > (a) os dois capacitores de 22 µF estão em **paralelo**, logo a ESR efetiva é
  > 5 m/2 = **2,5 mΩ** (0,53 mV corresponderia a um único capacitor de 5 mΩ);
  > (b) `v_C` (parabólico) e `v_ESR` (triangular) **não atingem o máximo no mesmo
  > instante** — somar os dois pk-pk sobrestima. O cálculo ponto a ponto
  > (`minimiza_ripple.py`) dá **634,21 µV**, e a simulação deu **634,03 µV** (0,028 %).
  > A soma ingênua daria 869 µV — 37 % acima do real.
- **Diodos de corpo: `id1_max = id2_max = 0,000000e+00 A`.** Com acionamento
  complementar exato (sem dead-time) eles nunca entram em condução — foi medido, não
  suposto.

### 3.2 buck5.cir — 12 V → 5 V, 500 kHz, L=17 µH, 2×22 µF, 2,0 A

- Esperado: `Vout = 0,417 × 12 / (1 + 1m/2,5) = 5,0019992 V`; **medido 5,001999 V → 4,0e-6 %**.
- `dIL = 0,3432523 A` medido (calculado 0,3432155 → 0,0107 %). **Ver §4.1.**
- Ripple: 2,0451 mV medidos vs 2,0472 mV do modelo → 0,0998 %.
- ⚠️ **DCR não informado** para este estágio → indutor modelado ideal (DCR = 0). Se o
  indutor real tiver os mesmos 30 mΩ do buck12, Vout cai mais `I·DCR = 2 A × 30 m =
  60 mV` (1,2 %). Assinalado, não escondido.

### 3.3 buck3v3.cir — 5 V → 3,3 V, 500 kHz, L=5 µH, 2×22 µF, 1,5 A

- Esperado: `Vout = 0,66 × 5 / (1 + 1m/2,2) = 3,2985007 V`; **medido 3,298501 V → 9,7e-6 %**.
- `dIL = 0,4489519 A` medido (calculado 0,4488 → 0,0338 %). **Ver §4.2.**
- Ripple: 2,6854 mV medidos vs 2,6875 mV do modelo → 0,0801 %.
- Mesma ressalva do DCR (não informado → modelado como 0).

### 3.4 divisor_vbat.cir — 100k / 13,7k + 100 nF

- `.op` com 25,2 V: esperado `25,2 × 13,7/113,7 = 3,0364116 V`; **medido 3,036412 V → 1,3e-5 %**.
- `.ac`: `fc = 1/(2π·(100k∥13,7k)·100n)`, `100k∥13,7k = 12 049,2524 Ω`
  → **fc = 132,0870 Hz**. Medido na varredura fina: **132,0947 Hz → 0,0058 %**.
- Ganho DC medido −18,38105 dB vs analítico −18,38080 dB.
- O `.log` traz a varredura completa (101 pontos da `dec 20 1 100k` que o enunciado
  pede, mais a `dec 1000 1 10k` fina).

### 3.5 bemf_div.cir — 8,2k / 1,0k + 1 nF

- `.op`: esperado `25,2/9,2 = 2,7391304 V`; **medido 2,739130 V → 1,6e-5 %**.
- `.ac`: `8,2k∥1k = 891,30435 Ω` → **fc = 178 564,1 Hz** (178,6 kHz, confere com os
  "178 kHz" do enunciado). Medido na varredura fina: **178 564,2 Hz → 6,6e-5 %**.
- A varredura precisa ir bem acima de fc (usou-se 10 MHz); medir fc numa varredura que
  termina perto dela daria erro grosseiro.

### 3.6 gate_drive.cir — Rg=10 Ω, Ciss=4 nF, Cboot=1 µF

**(a) Tempo de subida do gate**

- Fórmula exata: `t_10-90 = Rg·Ciss·ln(9) = 40 ns × 2,1972246 = 87,889 ns`
  (o enunciado usa a aproximação `2,2·Rg·Ciss = 88 ns`; 2,2 é aproximação de ln(9)=2,19722).
- **Medido (TRIG 1,2 V / TARG 10,8 V): 87,88888 ns → erro 0,00012 %.**
- Confirmação: `v(g)` medido em 4,2144 ns = 1,19985 V (teórico 1,2000 V) e em
  92,1034 ns = 10,79999 V (teórico 10,8000 V).

**(b) Droop do bootstrap em 50 µs**

- Fórmula: `ΔV = (Iq·ton + Qg)/Cboot = (0,5 mA×50 µs + 40 nC)/1 µF = 65 nC/1 µF = 65,0 mV`.
- **Medido: `vb_1ns = 12,00000 V` → `vb_50us = 11,93500 V`, droop = 65,00000 mV → erro 0.**
- Detalhe de modelagem registrado no `.cir`: no ngspice a largura `PW` do `PULSE` é o
  trecho de **topo**; as rampas TR/TF são triângulos **adicionais**. Com `PW=50n` e
  rampas de 1 ns a carga sai `0,8 A × 51 ns = 40,8 nC` e o droop daria 65,8 mV. Para
  entregar exatamente os 40 nC do enunciado usou-se `PW=49n` (0,8 A × 50 ns = 40,0 nC).

### 3.7 shunt_amp.cir — shunt 0,5 mΩ, degrau 0→30 A, amplificador diferencial G=50

- `Vshunt = 30 A × 0,5 mΩ = 15,000 mV`; **medido 15,00000 mV → erro 0.**
- `Vout` ideal (ganho 50) = 0,750 V. **Medido: 0,7496177 V.**
- Esse desvio de 0,051 % **não é erro de simulação**: é o ganho **finito** do amp-op
  (fonte E com A=1e5). Com `β = R1/(R1+Rf) = 1/51`, `Aβ = 1960,78`, o ganho de malha
  fechada é `50/(1+1/1960,78) = 49,9745` → **Vout = 0,7496177 V**. O medido bate com
  essa previsão em **6,7e-7 %**.
- Confirmação independente no próprio log: `vdif = 7,496177 µV`, que é exatamente
  `Vout/A = 0,7496177/1e5` — a tensão diferencial de erro que o modelo de ganho
  finito prevê.
- `Ishunt = 30,00000 A` (vetor derivado de `v(sh)/Rsh`; o ngspice não expõe vetor de
  ramo para resistor, por isso está marcado como **derivado**, não medido direto).

### 3.8 prot_inversao.cir — proteção com P-MOSFET (Vto = −2 V)

Topologia: **dreno → Vin**, **source → carga**, **gate → GND**, bulk no source, mais o
diodo de corpo explícito (ânodo no dreno, cátodo no source).

**(a) Polaridade normal, Vin = +19,8 V**

- `Rds_on = 1/(KP·(W/L)·(|Vgs|−|Vto|)) = 1/(2,8125 × 17,8) = 20,02 mΩ`
- Esperado: `I = 19,8/(10 + 0,02002) = 1,9760528 A`; `queda = I·Rds_on = 39,4717 mV`
- **Medido: `@rl[i] = 1,976048 A` (erro 0,00024 %) e `v(vin)−v(load) = 39,51546 mV`
  (erro 0,111 %).** Os dois critérios do enunciado (≈2 A e queda < 0,5 V) são atendidos
  com folga — a queda é **12,6 × menor** que o limite de 0,5 V.
- Corrente no diodo de corpo: `3,65e-12 A` (a queda de 39,5 mV polariza levemente o
  diodo; é desprezível — o canal é quem conduz).

**(b) Polaridade invertida, Vin = −19,8 V**

- **Medido: `@rl[i] = −4,061e-11 A` (41 pA)**, contra o critério **< 1 mA** →
  **margem de 2,5 × 10⁷**.
- `v(load) = −4,06e-10 V`, praticamente 0.
- **Por que o diodo de corpo corta:** é uma junção PN cujo **ânodo está no dreno (lado
  P)** e o **cátodo no corpo/source (lado N)**. Com a bateria invertida o ânodo fica
  ~20 V **negativo** em relação ao cátodo → **polarização reversa → bloqueia**. Na
  polaridade normal é o contrário: o diodo fica **direto**, conduz primeiro e eleva o
  source até ~Vin−0,7 V; aí `Vgs = 0 − 19,1 = −19,1 V`, muito abaixo de `Vto = −2 V`,
  o canal abre e curto-circuita o diodo. E o gate está referenciado ao terminal mais
  positivo: no caso (b) `Vgs = 0 V > Vto = −2 V` → **canal também desligado**. Os dois
  mecanismos somam.

  > Nota de transparência: os 41 pA medidos **não** são a fuga física do diodo
  > (`Is = 1e-12 A` daria 1 pA). São dominados pela condutância `GMIN = 1e-12 S` que o
  > solver põe em paralelo com as junções (`GMIN × 19,8 V ≈ 2e-11 A` por junção).
  > Ou seja: o número é **piso numérico do simulador**, não física do componente — e
  > ainda assim está 7,4 décadas abaixo do critério de 1 mA.
  > Por isso a linha "erro 4161 %" no CSV **não tem significado** (comparar 4e-11 com
  > 1e-12 é comparar ruído numérico); o critério que importa é < 1 mA.

---

## 4. Inconsistências encontradas no enunciado (sinalizadas, não "consertadas")

### 4.1 buck5 — dIL pedido 0,246 A não fecha com os parâmetros dados

Com `Vin = 12 V`, `D = 0,417`, `L = 17 µH`, `fsw = 500 kHz`:

```
dIL = (Vin − Vout)·D/(L·fsw) = (12 − 5,004)·0,417/(17e-6 × 500e3) = 0,3432 A
```

Para dar **0,246 A** seria preciso **L = 23,7 µH** (ou fsw = 698 kHz, ou D = 0,299).
Reporto **0,3432 A** como esperado (é o que a fórmula dá com os dados dados) e o medido
0,34325 A confirma a fórmula, não o número citado.

### 4.2 buck3v3 — dIL pedido 0,178 A não fecha com os parâmetros dados

```
dIL = (5 − 3,3)·0,66/(5e-6 × 500e3) = 0,4488 A
```

Para dar **0,178 A** seria preciso **L = 12,6 µH** (ou fsw = 1,26 MHz). Reporto
**0,4488 A** como esperado; o medido 0,44895 A confirma a fórmula.

### 4.3 buck12 — ripple de saída estimado em 1,1 mV está sobrestimado

Ver §3.1: o valor correto (ESR efetiva de 2,5 mΩ + soma com fase ponto a ponto) é
**≈ 634 µV**, e a simulação deu 634 µV.

### 4.4 gate_drive — "2,2·Rg·Ciss" é aproximação

O valor exato é `ln(9) = 2,19722`, não 2,2. Diferença de 0,13 % (88 ns vs 87,889 ns).
A simulação deu 87,88888 ns, ou seja, confirma a fórmula exata.

*(Nada disso foi "ajustado" para casar: os netlists usam **as fórmulas exatas** com os
parâmetros dados, e as divergências acima estão registradas como divergências.)*

---

## 5. Falhas, dificuldades e pontos de atenção

| # | O que aconteceu | Situação | Como foi tratado |
|---|---|---|---|
| 1 | **Nenhuma** simulação falhou por convergência | ✅ 8/8 convergiram | — |
| 2 | A janela de 200 µs media o **transitório de partida** (ringing LC, τ≈1,7 ms), dando erro de ~0,5 V no buck12 | Resolvido | §2: `.ic` analítico + prova de janelas planas no log + rodada de controle de 20 ms partindo do zero (`_testes/diag3.cir`) |
| 3 | Primeira tentativa de `.ic` usou a corrente **média** do indutor em vez do **vale** — isso **excitava** o ringing (a média não é o estado inicial de um ciclo) | Resolvido | Corrigido para `iL(0) = I − dIL/2`; a prova é a dispersão de 0,4 µV entre as 4 janelas do buck12 |
| 4 | `ngspice -b` retorna **código de saída 1** em qualquer deck com bloco `.control`, **mesmo sem nenhum erro** | Não é falha | Verificado com um deck trivial (`_testes`); os `.log` não têm nenhum erro. Decks sem `.control` retornam 0 |
| 5 | `vp(out)` com `meas ac ... WHEN vp()=-45` falha ("out of interval") | Contornado | A medição de fc usa o critério de −3 dB com o limiar calculado **do ganho DC medido** (`let vth = Hdc_dB - 3.0103`), não de um número fixo |
| 6 | `@l1[i]` devolve 0 e `@rsh[i]` não existe como vetor em `.meas` | Contornado | Uso de `i(L1)` (indutor) para corrente; para o shunt, vetor **derivado** `v(sh)/Rsh`, marcado como derivado |
| 7 | Convenção do `PULSE` do ngspice: `PW` é o topo, TR/TF são triângulos adicionais (entregava 40,8 nC em vez de 40 nC, droop 65,8 mV) | Resolvido | `PW=49n` → 40,0 nC exatos → droop 65,00000 mV. Documentado no `.cir` |
| 8 | No buck12, a chave ideal com acionamento complementar tem **dead-time = 0** | Limitante declarado | Um sincrono real com dead-time de 20–40 ns roda o diodo de corpo nesse intervalo e perde ~1–2 % em Vout. **Não modelado** (e anotado no `.cir`) |
| 9 | Vários componentes são `[N/D offline]` | Assumido e declarado | Diodos de corpo, PMOS, amp-op, driver de gate: modelos **genéricos/ideais**, declarados circuito por circuito nas seções `MODELAGEM` de cada `.cir` |

---

## 6. Verificação dos artefatos

Todos os `.log` foram gerados com exatamente:

```sh
ngspice -b <circuito>.cir > <circuito>.log 2>&1
```

| Arquivo | Tam. | Análises no log | Linhas de dados |
|---|---|---|---|
| `buck12.cir` / `buck12.log` | 5 649 B / 4 660 B | 1 tran (`20n`, 5 ms, `uic`) | 411 692 |
| `buck5.cir` / `buck5.log` | 3 854 B / 2 780 B | 1 tran (`20n`, 2 ms, `uic`) | 163 643 |
| `buck3v3.cir` / `buck3v3.log` | 3 546 B / 2 682 B | 1 tran (`20n`, 2 ms, `uic`) | 162 572 |
| `divisor_vbat.cir` / `.log` | 2 238 B / 5 698 B | op + ac dec 20 + ac dec 1000 | 1 / 101 / 4 001 |
| `bemf_div.cir` / `.log` | 1 973 B / 5 726 B | op + ac dec 20 + ac dec 1000 | 1 / 141 / 7 001 |
| `gate_drive.cir` / `.log` | 3 668 B / 1 102 B | 2 trans (200 ns e 60 µs) | 1 023 / 3 052 |
| `shunt_amp.cir` / `.log` | 2 674 B / 1 034 B | 1 tran (100 µs) | 10 011 |
| `prot_inversao.cir` / `.log` | 4 543 B / 756 B | 2 × op (via `alter`) | 1 / 1 |

O passo máximo pedido (20 ns) foi respeitado nos bucks: 5 ms / 20 ns = 250 000 passos
mínimos e o log registrou **411 692** pontos (o excedente são os breakpoints das fontes
PULSE). Busca por `singular|no convergence|timestep too small|error` em todos os `.log`:
**nenhuma ocorrência**.

**Extras** (não exigidos, usados como apoio e auditoria):
`minimiza_ripple.py` (modelo analítico do ripple), `gera_tabela.py` (monta tabela+CSV
lendo os logs), `_testes/` (testes de sintaxe e a rodada de controle de 20 ms).

---

## 7. Reproduzir

```sh
cd fase2_simulacao
for f in buck12 buck5 buck3v3 divisor_vbat bemf_div gate_drive shunt_amp prot_inversao; do
    ngspice -b $f.cir > $f.log 2>&1
done
python3 minimiza_ripple.py     # ripple analitico dos bucks
python3 gera_tabela.py         # le os .log e escreve resultados_fase2_spice.csv
```

---

## 8. Limites honestos deste trabalho

- Simulação SPICE é de **nível de circuito**. Não substitui bancada: não há parasitários
  de layout, ESL/ESR de trilha, acoplamento térmico, EMI, tolerância de componente nem
  dispersão de lote.
- Os três bucks são **malha aberta** (duty fixo). Não há compensador, então a oscilação
  de partida do LC subamortecido é real e leva milissegundos — num conversor de verdade
  a malha de controle amorteceria isso.
- Modelos genéricos onde o componente é `[N/D offline]`: diodo de corpo, PMOS de
  proteção, amp-op, driver de gate. Os números de `Rds_on` e `KP` são **escolhas
  numéricas declaradas** para chegar a um dispositivo plausível, **não** datasheet.
- No prot_inversao, o `Vgs` de −19,8 V do caso (a) **destruiria um MOSFET real**. O
  modelo nível 1 não rompe óxido e por isso não acusa — está registrado como limitação,
  não como resultado.
- **Não rodei** Proteus, LTspice, Altium, Eagle, Multisim nem PSpice: são x86/Windows e
  não existem nesta máquina. Tudo aqui é `ngspice-34` native aarch64.
