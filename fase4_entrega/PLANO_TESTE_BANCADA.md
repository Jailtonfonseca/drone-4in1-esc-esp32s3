# PLANO DE TESTE DE BANCADA (FASE 4)

**Projeto:** drone 4×ESC trifásico + ESP32-S3 na mesma PCB · LiPo 6S (19,8 / 22,2 / 25,2 V)
**Pasta:** `fase4_entrega/` · **Data:** 2026-09-11

## Regra deste documento

**Nenhum valor foi medido.** Todo "esperado" é rastreável:

| Etiqueta | Origem |
|---|---|
| `[F2]` | valor simulado/calculado na Fase 2, com `ngspice-34` — arquivo `fase2_simulacao/RESULTADOS_FASE2_SPICE.md` |
| `[F2V]` | valor medido em simulação Verilog (`iverilog 11`) — `fase2_simulacao/verilog/RELATORIO_VERILOG.md` |
| `[F0]` | valor calculado na Fase 0 — `fase0_especificacao/FASE0_ESPECIFICACAO.md` |
| `[CALC]` | cálculo meu desta sessão, saída real em `fase4_entrega/calcs_fase4.txt` |
| `[EST]` | estimativa de engenharia (não medida) |
| `[PREMISSA]` | suposição registrada do projeto |
| `[VERIFICAR]` | não confirmado |

### ⚠️ A armadilha nº 1 deste plano: tensão de entrada dos bucks

`[F2]` Os três bucks foram simulados **em malha aberta** (duty fixo). A saída deles
**escala com a entrada**. Os valores da Fase 2 só são comparáveis se você testar **no mesmo
Vin do `.cir`**:

`[CALC]` `calcs_fase4.txt`:

```
buck12  D=0.606  Vout(Vin) = 0.6051*Vin     Vin = 19.8 V -> 11.9802 V
buck5   D=0.417  Vout(Vin) = 0.4168*Vin
buck3v3 D=0.660  Vout(Vin) = 0.6597*Vin
```

| Estágio | Vin da simulação | Vout [F2] |
|---|---|---|
| buck 12 V | **19,8 V** (6S descarregado) | 11,98023 V |
| buck 5 V | **12 V** (saída do buck 12 V) | 5,001999 V |
| buck 3,3 V | **5 V** (saída do buck 5 V) | 3,298501 V |

> **Consequência:** para poder comparar com a Fase 2, a bancada tem de começar com
> **19,8 V na entrada** — que é exatamente a tensão de pack vazio (6 × 3,30 V), e por isso
> é uma condição segura e reproduzível. Se você aplicar 25,2 V num estágio aberto, a saída
> do buck12 medida será ~15,25 V `[CALC]` e o teste vai parecer "errado" sem estar errado.
>
> Na **placa real com o CI de buck (malha fechada)**, espera-se o **nominal** (12,0 / 5,0 / 3,3 V)
> com a tolerância do CI. Use os dois critérios, cada um no seu caso — está escrito assim
> nos passos 5 e 6.

---

## 1. Instrumentos necessários

| # | Instrumento | Especificação mínima | Para quê |
|---:|---|---|---|
| I1 | Fonte de bancada ajustável com **limite de corrente** | 0–30 V, ≥ 3 A, com knobs de tensão e corrente | passos 4–14 (primeira energização) |
| I2 | Multímetro | 4½ dígitos, autorange, faixa mΩ | passos 2, 3, 5, 10 |
| I3 | Osciloscópio | ≥ 100 MHz, ≥ 2 canais, **com limitação de banda 20 MHz** | passos 6, 7, 8, 9 |
| I4 | Ponta de osciloscópio com **mola de terra** (ou coax soldado) | — | passo 6 (µV/mV — ponta com jacaré é inútil aqui) |
| I5 | Ponta **diferencial** | ≥ 100 V CM, ≥ 10 MHz | medição de shunt e do barramento |
| I6 | Sonda de corrente DC/AC | ≥ 30 A, ≥ 1 MHz | passo 14 |
| I7 | Gerador de sinal / fonte de corrente | 0–30 A, baixa tensão | passo 12 (injetar corrente no shunt) |
| I8 | Termopar tipo K ou câmera térmica | −50…+300 °C | passo 16 (térmica) |
| I9 | Banco de carga resistivo/indutivo | até 30 A contínuo | **teste que a bancada de solda não faz** (§18) |
| I10 | Lupa 10× / microscópio | — | passo 1 |
| I11 | Régua/paquímetro | — | inspeção mecânica |

**Antes de começar:** hélices **REMOVIDAS**. Bancada limpa, pulseira ESD, extintor por perto
se houver LiPo carregada na sala.

---

## 2. Ordem dos testes (resumo)

```
1  inspeção visual            (SEM energia)
2  continuidade               (SEM energia)
3  resistência entre trilhos  (SEM energia)
4  energização LIMITADA       (fonte, hélices fora)   <-- ponto sem retorno
5  medição por trilho
6  ripple por trilho
7  PWM sem potência
8  gate (subida + bootstrap)
9  dead-time no gate          <-- prova de não shoot-through
10 divisor VBAT + ADC
11 BEMF
12 shunt + amplificador
13 proteção de inversão
14 teste com motor pequeno
15 teste com BATERIA          (só no fim)
16 térmica / o que não se valida
```

**Regra dura:** não pule da etapa 4 para a 15. Cada etapa libera a próxima.

---

## 3. PASSO 1 — Inspeção visual

| Campo | Conteúdo |
|---|---|
| **O que medir** | presença, orientação, alinhamento e solda de todos os componentes |
| **Instrumento** | I10 (lupa/microscópio) |
| **Valor esperado** | 238 footprints montados, 0 faltando; pino 1 de cada CI no marcado; polaridade dos 6 eletrolíticos |
| **Critério de aprovação** | **0** pino deslocado em QFN/ módulo · **0** ponte de solda visível · **0** componente tombado · 100 % da lista conferida contra `fase0_especificacao/lista_componentes_fase0.csv` |
| **Referência** | `MONTAGEM_ORDEM_DE_SOLDA.md` §6 |

Se reprovar aqui: **não energize**. Retrabalhe e repita o passo 1.

---

## 4. PASSO 2 — Continuidade (curto entre trilhos)

| Campo | Conteúdo |
|---|---|
| **O que medir** | continuidade (bipe) entre cada par de trilhos: `VBAT ↔ GND`, `12V ↔ GND`, `5V ↔ GND`, `3,3V ↔ GND`, `3,3V_A ↔ GND`, `5V ↔ 3,3V`, `12V ↔ 5V` |
| **Instrumento** | I2 em modo continuidade |
| **Valor esperado** | **circuito aberto** em todos os pares |
| **Critério de aprovação** | nenhum bipe. **< 50 Ω entre trilhos de tensão diferentes = REPROVADO**, não energize |
| **Atenção** | medir com a placa **desenergizada e capacitores descarregados**. Um bip curto que desaparece é só o capacitor carregando — espere a leitura estabilizar |

---

## 5. PASSO 3 — Resistência entre trilhos (com valor)

| Campo | Conteúdo |
|---|---|
| **O que medir** | resistência DC de cada trilho para GND, com ponta em **mΩ/Ω** |
| **Instrumento** | I2 |
| **Valor esperado** | alto (> 1 kΩ) em todos, exceto: `3,3V_A` e `3,3V` podem ler centenas de Ω (rede de realimentação/divisores). `VBAT ↔ VBAT_PROT` deve medir o **Rds do P-FET no gate em GND** = ~20 mΩ `[F2]` (`Rds_on = 1/(KP·(W/L)·(|Vgs|−|Vto|)) = 20,02 mΩ`) |
| **Critério de aprovação** | nenhum trilho com resistência < 10 Ω para GND · `VBAT→VBAT_PROT` entre 5 e 100 mΩ |
| **Ressalva** | `[EST]` o valor de Rds do P-FET é do **modelo SPICE genérico**, não do seu transistor. O critério é a **ordem de grandeza** (mΩ), não o número exato |

---

## 6. PASSO 4 — Primeira energização com FONTE LIMITADA (hélices removidas)

| Campo | Conteúdo |
|---|---|
| **O que medir** | tensão aplicada e corrente consumida, com o limite de corrente da fonte |
| **Instrumento** | I1 (fonte) + I2 |
| **Valor esperado** | com **19,8 V** e limite de **200 mA**: consumo em vazio `[F0]` "VBAT: … + 0,30 A dos conversores" → **≈ 0,30 A** com lógica ligada (WiFi desligado). Com WiFi TX: +0,5 A no trilho de 3,3 V, refletido no VBAT |
| **Critério de aprovação** | a fonte **NÃO** entra em modo corrente (CC) nos primeiros segundos · consumo < 0,5 A com WiFi off · **nenhum** ponto quente ao toque · nenhum cheiro de queimado |
| **Ordem de subida** | 1) limite 50 mA, tensão 0 → sobe devagar; 2) se ok, limite 200 mA; 3) se ok, limite 500 mA; 4) só então 1 A |
| **Se entrar em CC** | **desligue**. Significa curto ou componente invertido. Volte ao passo 3 |

> `[EST]` Fontes de bancada baratas demoram a reagir a um curto. Se a sua não tem limite de
> corrente rápido, use um resistor de 100 Ω / 5 W em série na primeira subida.
> **Este é o passo mais importante de todo o plano.** Nenhuma etapa seguinte existe se
> esta falhar.

---

## 7. PASSO 5 — Medição por trilho

| Trilho | Instrumento | Vout esperado — **malha aberta @ Vin 19,8 V** `[F2]` | Vout esperado — **CI com realimentação** `[EST]` | Critério |
|---|---|---:|---:|---|
| VBAT_PROT | I2 | 19,794 V `[CALC]` (queda de 6 mV @ 0,3 A no P-FET de 20 mΩ) | idem | 19,7–19,8 V |
| 12 V (gate drivers) | I2 | **11,98023 V** | **12,0 V** | ±2 % do esperado |
| 5 V | I2 | **5,001999 V** | **5,0 V** | ±2 % |
| 3,3 V | I2 | **3,298501 V** | **3,3 V** | ±2 % |
| 3,3 V_A (LDO) | I2 | `[PREMISSA]` ≈ 3,3 V (LDO não foi simulado) | 3,3 V ± LDO | ±3 % |
| VBAT sense (após divisor) | I2 | **2,385752 V** @ 19,8 V `[CALC]` · 3,036412 V @ 25,2 V `[F2]` | idem | ±1 % (resistores 1 %) |

Referência `[F2]`: "buck12 … Medido: 11,98023 V → erro 5,4e-6 %"; "buck5 … medido 5,001999 V";
"buck3v3 … medido 3,298501 V"; "divisor_vbat … medido 3,036412 V".

---

## 8. PASSO 6 — Ripple de cada trilho

| Campo | Conteúdo |
|---|---|
| **O que medir** | ripple pk-pk na saída de cada buck, **em AC, com limitação de banda 20 MHz e mola de terra** |
| **Instrumento** | I3 + I4 |
| **Esperado** | buck12: **634,03 µV** pk-pk · buck5: **2,0451 mV** · buck3v3: **2,6854 mV** `[F2]` |
| **Critério de aprovação (simulação)** | ≤ 1 mV (12 V) · ≤ 3 mV (5 V) · ≤ 4 mV (3,3 V) — margem de ~50 % sobre o simulado |
| **Critério de aprovação (placa real)** | `[EST]` **≤ 20 mV** pk-pk com 20 MHz de banda. Ver aviso abaixo |
| **Checagem de sanidade da ponta** | encoste a ponta na própria mola de terra (curto) → leitura deve ser < 1 mV. Se não for, a medição é da sua ponta, não do circuito |

> **⚠️ Leia antes de se decepcionar.** Os 634 µV do buck12 vêm de um modelo SPICE que tem
> **ESR ideal de 2,5 mΩ** (dois capacitores de 22 µF em paralelo, 5 mΩ cada) e **nenhuma
> indutância de trilha ou de via**. `[F2]` §3.1 explica: "Quem dimensiona é ESR + ESL, não
> os µF". Numa placa real, o ESL do loop e a indutância das vias dominam, e o ripple medido
> será **maior** que o simulado — provavelmente dezenas de mV. **Isso não é falha da
> simulação nem da placa: a simulação nunca prometeu ESL.** `[EST]`
>
> O que a medição de 634 µV **serve para provar**: que o capacitor está soldado e que a
> medição foi feita com técnica decente. O que ela **não** prova: nada sobre EMI.

---

## 9. PASSO 7 — PWM sem potência

**Condição:** barramento de potência **desenergizado** (sem VBAT nos MOSFETs). Apenas lógica
e o trilho de 12 V dos drivers ligados, para que os MOSFETs não possam comutar a fase.
Motores desconectados.

| Campo | Conteúdo |
|---|---|
| **O que medir** | frequência, período e defasagem nos 12 canais PWM, na **entrada** do driver |
| **Instrumento** | I3 (2 canais) |
| **Esperado** | período **50,0000 µs** → f = **20,0000 kHz** `[F2V]` · defasagem entre grupos de motor: **12 500 ns = 90,000°** `[F2V]` |
| **Critério de aprovação** | f = 20,00 kHz ± 2 % · defasagem 90° ± 5° (medida nos 4 grupos: 0°/90°/180°/270°) · duty de 0 % → sem pulso · duty de 100 % → **94,96 %** (clampado por DUTY_MAX) `[F2V]` |
| **Atenção** | `[F2V]` §4.5: o duty efetivo é limitado a **2,0 %–95,0 %** por construção. Medir 95 % e achar que "está faltando 5 %" é ler o datasheet errado. Duty 0 % deixa o **low-side ligado** |

---

## 10. PASSO 8 — Teste de gate (subida + bootstrap)

### 8a — Tempo de subida do gate

| Campo | Conteúdo |
|---|---|
| **O que medir** | tempo de subida 10–90 % no gate do MOSFET (ponta no pino do gate, mola de terra no source do mesmo FET) |
| **Instrumento** | I3 |
| **Esperado** | **87,88888 ns** `[F2]` (fórmula exata: `t = Rg·Ciss·ln(9) = 10 Ω × 4 nF × 2,1972246`) |
| **Critério de aprovação** | `[EST]` **20–200 ns**, e **consistência**: os 24 gates devem medir dentro de ±20 % da mediana. Um gate 3× mais lento que os outros indica solda ruim no Rg |
| **Ressalva dura** | `[PREMISSA]` **Ciss = 4 nF é premissa, não datasheet** (`FASE0_ESPECIFICACAO.md` P-06: Qg total 40 nC). O MOSFET real vai dar outro tempo. **O critério é a faixa, não o número.** |

### 8b — Droop do bootstrap

| Campo | Conteúdo |
|---|---|
| **O que medir** | queda da tensão do capacitor de bootstrap ao longo do tempo de condução do high-side (V no início do pulso menos V no fim) |
| **Instrumento** | I3 (ponta diferencial I5 entre o pino BOOT e o source do high-side) |
| **Esperado** | **65,00000 mV** em 50 µs `[F2]` (`ΔV = (Iq·ton + Qg)/Cboot = (0,5 mA × 50 µs + 40 nC)/1 µF`) |
| **Critério de aprovação** | droop **< 500 mV** em 50 µs (i.e., < 4 % de um Cboot carregado a 12 V). Acima disso o high-side perde Vgs e o MOSFET entra em linear → **superaquece** |
| **Por que importa** | `[F2V]` o RTL limita o duty a 95 % **exatamente** para dar 2,5 µs de low-side por período para recarregar o Cboot. Se você mexer no `DUTY_MAX`, este teste é o que acusa |

### 8c — Tensão de gate

| Campo | Conteúdo |
|---|---|
| **O que medir** | Vgs em nível alto, no high-side **e** no low-side |
| **Instrumento** | I3 |
| **Esperado** | ≈ **12 V** (`[F0]` §7: trilho de 12 V existe porque "gate de MOSFET de potência precisa de ~10–12 V para ficar plenamente ligado") |
| **Critério** | 10–13 V no low-side; high-side = low-side ± 0,5 V (o bootstrap tem de entregar quase o mesmo) |

---

## 11. PASSO 9 — Dead-time no gate (prova de não shoot-through)

**Este é o teste que separa um ESC que funciona de um que solta fumaça.**

| Campo | Conteúdo |
|---|---|
| **O que medir** | com **2 canais**, o gate do high-side e o gate do low-side **do mesmo half-bridge**, na mesma base de tempo |
| **Instrumento** | I3 (2 canais, mesma escala) |
| **Esperado** | `[F2V]` dead-time do RTL = **518,750 ns** nas duas bordas (83 ciclos de 6,25 ns a 160 MHz) · erro medido 0,000 % |
| **Critério de aprovação** | no instante de transição, **os dois gates NUNCA em nível alto ao mesmo tempo** (janela de sobreposição = 0) · dead-time medido **entre 250 ns e 2 µs** |
| **Repetir em** | frio, quente (após 10 min ligado) e nos **12 half-bridges** (24 gates) |
| **Ver também** | `[F2V]` §7.3: "**o dead-time real no MOSFET = dead-time do RTL + atrasos de subida/descida do driver**" — ou seja, o valor medido no gate **será maior** que 518,75 ns. Isso é esperado e é segurança, não erro |

> **Se a sobreposição não for zero: PARE.** Shoot-through em 19,8 V com 24 MOSFETs destrói
> o par de FETs e possivelmente o driver. Reveja o passo 7 (o RTL) e o passo 3 (curto).

---

## 12. PASSO 10 — Divisor VBAT + ADC

| Campo | Conteúdo |
|---|---|
| **O que medir** | tensão no ponto médio do divisor `100k / 13,7k` e a leitura do ADC correspondente |
| **Instrumento** | I2 + firmware de leitura do ADC |
| **Esperado** | `[CALC]` **2,385752 V** @ 19,8 V · **2,674934 V** @ 22,2 V · **3,036412 V** @ 25,2 V `[F2]` |
| **Critério de aprovação** | erro do divisor **< 1 %** (resistores 1 %) · erro de leitura do ADC **< 2 %** |
| **Offset do ADC** | `[F0]` §4.5: "erro de offset do ADC(~3 mV) = 0,13 A"; `[F0]` P-12/P-13: ADC 12 bits, FS 3,300 V, resolução **806 µV/LSB** |
| **Procedimento de calibração** | medir o divisor com o multímetro, **anotar o valor real** e usar esse número na conversão do firmware (não confie no valor nominal dos resistores) |

---

## 13. PASSO 11 — BEMF

| Campo | Conteúdo |
|---|---|
| **O que medir** | tensão na saída do divisor de BEMF `8,2k / 1,0k` com a fase forçada a uma tensão conhecida (fonte de bancada na fase, motor desconectado) |
| **Instrumento** | I2 + I1 |
| **Esperado** | `[CALC]` **2,152174 V** @ 19,8 V · 2,413043 V @ 22,2 V · **2,739130 V** @ 25,2 V `[F2]` |
| **Critério de aprovação** | erro < 1 % em todos os pontos · medir em **3 pontos** (19,8 / 22,2 / 25,2 V) para pegar não-linearidade do clamp |
| **Nota de filtro** | `[F2]` a frequência de corte do filtro é **178 564,1 Hz** (178,6 kHz). Um multímetro comum lê bem; o clamp de 3,3 V protege o ADC acima disso |

---

## 14. PASSO 12 — Shunt + amplificador de corrente

| Campo | Conteúdo |
|---|---|
| **O que medir** | Vshunt e a saída do amplificador diferencial (G=50) para correntes conhecidas injetadas pelo shunt |
| **Instrumento** | I7 (fonte de corrente) + I2 em modo mV (ou I3) |
| **Esperado** | **30 A → Vshunt = 15,00000 mV → Vout = 0,7496177 V** `[F2]` (ideal seria 0,750 V; a diferença é o ganho finito do amp, A=1e5 — **não é erro**) |
| **Pontos de calibração** | `[CALC]` 5 A → 2,500 mV → 0,124936 V · 15 A → 7,500 mV → 0,374809 V · 30 A → 15,000 mV → 0,749617 V |
| **Critério de aprovação** | erro de linearidade **< 2 %** entre 5 e 30 A · **offset a 0 A** anotado e subtraído no firmware (offset do amp-op vira erro de corrente: 1 mV de saída ≈ 40 mA de corrente) |
| **Limite FÍSICO (não é o amplificador)** | `[F0]` §4.5: "shunt no low-side só é válido **enquanto o FET inferior conduz**". Sem PWM sincronizado, a leitura é lixo. O teste de bancada com corrente DC prova o amplificador, **não** prova a amostragem |
| **Potência no shunt** | `[CALC]` 0,450 W a 30 A · 0,113 W a 15 A → resistor 2512 de 2 W tem folga 4,4× no pico |

---

## 15. PASSO 13 — Proteção contra inversão de polaridade

### 13a — Polaridade normal

| Campo | Conteúdo |
|---|---|
| **O que medir** | corrente na carga e queda dreno–source do P-FET |
| **Instrumento** | I1 + I2 |
| **Esperado** | com 19,8 V e carga de 10 Ω: **I = 1,976048 A** · **queda = 39,51546 mV** `[F2]` |
| **Critério** | I dentro de ±5 % de 1,976 A · queda **< 0,5 V** (o simulado é 12,6× menor que o limite) |
| **Checagem adicional** | medir **Vgs** do P-FET: `[F2]` §8 avisa que no modelo o Vgs chega a **−19,8 V**, o que **destruiria um MOSFET real**. Na sua placa o BOM prevê "Resistor de gate do P-FET + zenner; 10k + 12 V; clamp Vgs" `[DISCO]` (`lista_componentes_fase0.csv`). **Confirme que o Vgs medido fica dentro do rating do transistor** |

### 13b — Polaridade invertida

| Campo | Conteúdo |
|---|---|
| **O que medir** | corrente na carga com a fonte invertida (−19,8 V) |
| **Instrumento** | I2 (ou a leitura da própria fonte) |
| **Esperado** | `[F2]` **−4,061e-11 A (41 pA)** — critério do projeto: **< 1 mA** |
| **Critério de aprovação** | corrente **< 1 mA** (margem de 2,5 × 10⁷ sobre o medido em simulação). `[F2]` §3.8 nota que os 41 pA são **piso numérico do solver** (GMIN), não fuga física |
| **Como medir na prática** | o µA de um multímetro comum já é ruído. Use a leitura de corrente da fonte com limite baixo, ou um resistor de 1 kΩ em série e meça a queda (1 mA × 1 kΩ = 1 V) |

---

## 16. PASSO 14 — Teste com motor pequeno

**Condição obrigatória: hélice REMOVIDA. Fonte limitada. Motor pequeno, não o 2207 de voo.**

| Campo | Conteúdo |
|---|---|
| **O que medir** | partida, sentido de rotação, corrente de fase e forma das 3 fases |
| **Instrumento** | I1 (limite de corrente) + I6 (sonda de corrente) + I3 |
| **Esperado** | motor parte sem travar · corrente cresce suave com o duty · **nenhum** pico de corrente no instante da comutação (pico = shoot-through) · 3 fases defasadas |
| **Critério de aprovação** | corrente de partida **dentro do limite da fonte** · sem pico > 2× a corrente de regime · sem disparo do limite de corrente · temperatura dos FETs `< 60 °C` em 5 min `[EST]` |
| **Checagem cruzada** | `[F0]` §7: cruzeiro previsto → hélices 167 W, I_barra 7,5 A, **I_fase pico 12,5 A**; nominal 15 A. Um motor pequeno deve ficar **muito abaixo** disso |
| **Sentido de rotação** | `[EST]` se girar errado, **troque duas fases** — nunca inverta no firmware (inverte também o BEMF) |

---

## 17. PASSO 15 — Teste com BATERIA (só no fim, hélices removidas)

| Campo | Conteúdo |
|---|---|
| **Pré-requisito** | **passos 1 a 14 aprovados.** Sem exceção |
| **O que medir** | tensão do pack, corrente de barramento, temperatura dos FETs, comportamento do failsafe |
| **Instrumento** | I2 + I6 + I8 |
| **Esperado** | pack 6S: **25,2 V cheio / 22,2 V nominal / 19,8 V vazio** `[CALC]` · VBAT sense conforme passo 10 |
| **Critério de aprovação** | tensão dentro de 25,2 V ± 0,1 V por célula · sem queda de tensão inexplicada (indica resistência de contato no XT60) · **failsafe testa e corta os motores** |
| **Obrigatório antes** | alarme de subtensão configurado; **nunca** descarregar abaixo de 3,3 V/célula (ver `SEGURANCA_E_REGULATORIO.md`) |

> Com bateria **não** se valida 30 A contínuo. A bateria não é carga — é fonte.

---

## 18. O QUE **NÃO** SE VALIDA EM BANCADA (leia antes de escrever "está validado")

Isto é a parte mais importante do plano. A Fase 0 §9.3 já avisava: "Dissipação térmica real,
EMI/EMC, 30 A contínuo e fabricação não são simuláveis aqui".

### 18.1 — 30 A contínuo por motor

- **Não se valida** com fonte de bancada (a fonte limita), nem com bateria (a bateria é fonte,
  não carga), nem com motor parado (motor parado não consome).
- **O que seria preciso:** banco de carga resistivo/indutivo capaz de 30 A em 19,8 V (≈ 600 W),
  ou o motor com hélice **em tubo de empuxo**, medindo empuxo × corrente.
- `[F0]` §7: 120 A é **pico de rajada, não contínuo** — "não existe trilha de 120 A contínuo"
  (com 2 oz e ΔT 10 °C a fórmula IPC-2221 pede 110,78 mm de largura). O barramento foi
  dimensionado para "dezenas de ampères" e o pico é absorvido por **massa de cobre e
  capacitância**. Isso é projeto, **não é medição**.

### 18.2 — Térmica real dos MOSFETs

- **Não se valida** medindo a superfície da placa com o dedo.
- `[F0]` §7 dá os números **calculados** com `Rth_ja = 60 °C/W` — e o próprio texto marca
  `[PREMISSA]` para o Rth: "Térmica do MOSFET [CALC] (Rth_ja é [PREMISSA])":
  cruzeiro Tj = 26,0 °C · nominal Tj = 33,7 °C · **pico (30 A) Tj = 60,0 °C**.
- **O que seria preciso:** termopar no tab do MOSFET ou câmera térmica, **sob carga real**.
- O que a bancada **pode** dizer: se o FET esquenta com 2 A, o Rth real é péssimo e o
  número de 60 °C está otimista.

### 18.3 — EMI / EMC

- **Não se valida.** Sem câmara anecoica, sem LISN, sem analisador de espectro nesta máquina.
- O risco concreto: `[F0]` §7 mostra que o **espaçamento entre trilhas** e a separação
  potência/sinal decidem o ruído no ADC e no IMU — e `[F0]` §4.4 calcula que abrir 30 A em
  50 ns com 100 nH de cabo gera **60 V** de spike, "que estoura o MOSFET de 40 V".
- **O que seria preciso:** bancada de pré-conformidade + receptor de vídeo 5,8 GHz ligado perto
  para ver o que morre primeiro.

### 18.4 — Outros

- **Malha de voo / PID:** fora do escopo. A Fase 2 só entrega o gerador de PWM com dead-time
  (`RELATORIO_VERILOG.md` §7.10: "Não há lógica de comutação … BEMF, sensor Hall, nem enable/freio").
- **Sincronismo do ADC com o PWM:** `[F2V]` §7.4: "nada garante que o disparo do ADC caia fora
  da janela de dead-time". Não há ADC no modelo Verilog.
- **Timing do RTL a 160 MHz:** `[F2V]` §7.5: "'Sintetizável' ≠ 'fecha timing a 160 MHz'".
- **Vibração, impacto, corrosão, vida útil** — nenhuma.
- **Alcance de rádio** — ver `ANALISE_WIFI_CONTROLE.md`.

---

## 19. TABELA-RESUMO DE ACEITAÇÃO

| # | Teste | Instrumento | Valor esperado | Aprova se |
|---:|---|---|---|---|
| 1 | Inspeção | lupa | 0 defeito | 0 defeito |
| 2 | Continuidade | multímetro | aberto | sem bipe |
| 3 | Resistência | multímetro | > 10 Ω p/ GND | nenhum < 10 Ω |
| 4 | Energização limitada | fonte | ≈ 0,30 A @ 19,8 V | < 0,5 A, sem CC |
| 5 | Trilhos | multímetro | 11,98023 / 5,001999 / 3,298501 V | ±2 % |
| 6 | Ripple | osciloscópio 20 MHz | 634 µV / 2,0451 mV / 2,6854 mV | ≤ 20 mV na placa real |
| 7 | PWM | osciloscópio | 20,0000 kHz · 90,000° | ±2 % · ±5° |
| 8 | Gate | osciloscópio | 87,889 ns · 65,000 mV | 20–200 ns · < 500 mV |
| 9 | **Dead-time** | osciloscópio | 518,750 ns | **sobreposição = 0** · 250 ns–2 µs |
| 10 | Divisor VBAT | multímetro | 2,385752 V @ 19,8 V | < 1 % |
| 11 | BEMF | multímetro | 2,152174 V @ 19,8 V | < 1 % |
| 12 | Shunt+amp | fonte de corrente | 15,000 mV @ 30 A → 0,749617 V | linearidade < 2 % |
| 13 | Anti-inversão | fonte | 1,976048 A / −41 pA | I < 1 mA invertido |
| 14 | Motor pequeno | sonda de corrente | I baixa, sem pico | sem pico > 2× · < 60 °C |
| 15 | Bateria | multímetro | 25,2 / 22,2 / 19,8 V | failsafe corta |
| 16 | 30 A / térmica / EMI | **não disponível** | — | **NÃO VALIDÁVEL AQUI** |
