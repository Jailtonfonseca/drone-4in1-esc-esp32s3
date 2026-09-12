# RELATÓRIO — Fase 2: PWM 12 canais com dead-time em Verilog

**Data:** 2026-09-11 · **Máquina:** Linux ARM (aarch64)
**Ferramentas:** Icarus Verilog 11.0 (stable), vvp, Yosys 0.9 (git sha1 1979e0b), Python 3 + matplotlib 3.11.1
**Pasta:** `fase2_simulacao/verilog/`

> **Regra cumprida:** nenhum número abaixo foi calculado "no papel". Todos vêm de `tb_pwm.log`,
> `yosys.log` ou do próprio `tb_pwm.vcd` (re-lido por um parser Python independente).

---

## 1. O que foi entregue

| Arquivo | Tamanho | Função |
|---|---|---|
| `pwm_deadtime.v` | 7 697 B | Módulo: 12 canais PWM + 12 pares hi/lo com dead-time |
| `tb_pwm.v` | 9 591 B | Testbench: varredura, assert de shoot-through, medidas, VCD |
| `tb_pwm.log` | 2 022 B | **Log real da simulação** (comando abaixo) |
| `tb_pwm.vcd` | 10 429 328 B | Dump de ondas (janela de 150 µs) |
| `pwm_deadtime.png` | 134 433 B | Formas de onda (3 painéis), conferido com `view_image` |
| `plot_pwm.py` | 8 750 B | Parser VCD próprio + plot matplotlib |
| `yosys.log` | 115 297 B | `yosys -p 'read_verilog pwm_deadtime.v; synth; stat'` (fluxo completo) |
| `yosys_stat.log` | 79 886 B | Fluxo alternativo sem ABC (usado como 1ª estimativa) |
| `sim_pwm` | 159 091 B | Executável iverilog |
| `compile.log` | 0 B | Vazio = compilação sem nenhum warning |

### Comandos exatos executados

```sh
iverilog -g2005 -o sim_pwm tb_pwm.v pwm_deadtime.v && vvp sim_pwm > tb_pwm.log 2>&1
iverilog -g2005 -o /dev/null pwm_deadtime.v
yosys -p 'read_verilog pwm_deadtime.v; synth; stat' > yosys.log 2>&1
python3 plot_pwm.py
```

---

## 2. Arquitetura implementada

- **Clock** 160 MHz (período 6,25 ns).
- **Portadora triangular** `PERIOD = 8000` ciclos = **50 µs → 20 kHz** [PREMISSA P-07].
  Na implementação, `PERIOD` é o período **completo**; o topo do triângulo é `PERIOD/2 = 4000`.
  (Isso é uma escolha de nomenclatura — foi verificada por medição, §4.3, e não assumida.)
- **Uma única contagem mestra** (0…7999) gera as 4 portadoras: para o grupo _g_,
  `φ_g = (contador + g·2000) mod 8000`, dobrada em triângulo. Isso dá defasagem **exata**
  de 90° sem 4 contadores independentes (não há _drift_ entre grupos).
- **Comparação** `tri < dthr` → um pulso por período (duty = `dthr`/4000).
- **Dead-time**: sub-módulo `pwm_dt_channel` instanciado 12×. `hi` só vai a 1 após `dt_cycles`
  ciclos com `pwm_in = 1`; `lo` só vai a 1 após `dt_cycles` ciclos com `pwm_in = 0`.
- **Garantia estrutural** (não é `$assert`, é lógica): `hi = 1` exige `pwm_in = 1`
  estável, `lo = 1` exige `pwm_in = 0` estável; como `pwm_in` não pode ser os dois,
  **hi e lo nunca podem estar em 1 no mesmo ciclo**. No reset, `hi = lo = 0` (estado seguro).
- **Limites de duty**:
  - `DUTY_MAX_CODE = 3890` (95,0 %) → garante mínimo de condução do **low-side** por
    período (2,5 µs) para **reposição do capacitor de bootstrap**;
  - `DUTY_MIN_CODE = 82` (2,0 %) → garante que o pulso do high-side seja **maior que o
    próprio dead-time** (520 ns = 1,04 % do período), senão o pulso seria engolido e nunca
    apareceria em `hi_o`;
  - `duty_i = 0` → sem pulso, `lo` fica ligado (estado natural de um half-bridge em 0 %).

---

## 3. Saída do parser VCD × saída do log

O parser Python (`plot_pwm.py`) é independente do testbench: relê o `tb_pwm.vcd` e refaz as medidas.
**Os dois concordam exatamente** (dead-time 518,750 ns nas duas bordas) — isso descarta um bug
de aritmética dentro do testbench.

```
timescale = 1/1e-12 s ; larguras = {'pwm_o': 12, 'lo_o': 12, 'hi_o': 12}
VCD: dt_subida = 518.750 ns ; dt_descida = 518.750 ns
n eventos hi_o[0]: 6   (janela de 150 µs; período 50 µs)
```

---

## 4. Resultados medidos

### 4.1 Dead-time (esperado × medido × erro)

| Grandeza | Programado | Medido (borda de subida) | Medido (borda de descida) | Erro |
|---|---|---|---|---|
| Dead-time | 83 ciclos = **518,750 ns** | **518,750 ns** | **518,750 ns** | **0,000 ns (0,000 %)** |
| vs. referência de projeto **520 ns** | 520 ns | 518,750 ns | 518,750 ns | **−1,250 ns (−0,240 %)** |

`[DEADTIME] subida : lo cai em 1537571.875 ns, hi sobe em 1538090.625 ns -> dt = 518.750 ns`
`[DEADTIME] descida: hi cai em 1512553.125 ns, lo sobe em 1513071.875 ns -> dt = 518.750 ns`

O dead-time é **programável em runtime** (porta `deadtime_i` + valor de reset por parâmetro):

| `deadtime_i` | Esperado | Medido | Erro |
|---|---|---|---|
| 83 ciclos | 518,750 ns | 518,750 ns | 0,000 ns |
| 40 ciclos | 250,000 ns | **250,000 ns** | 0,000 ns |

### 4.2 Shoot-through — a prova principal

| Métrica | Valor |
|---|---|
| Violações `hi & lo != 0` | **0** |
| Ciclos checados (todo `posedge clk`, do t=0 ao fim) | **362 060** |
| Tempo total simulado | **2 262,872 µs** |
| Inclui 60 000 ciclos de **estresse** (duty pseudo-aleatório nos 12 canais + dead-time 0…255 ciclos mudando a cada ciclo) | **0 violações** |

O monitor roda em **todos** os flanco de clock — não é amostragem. Como `hi_o`/`lo_o` são
registrados, verificar a cada `posedge` cobre 100 % dos estados possíveis.

### 4.3 Frequência real

| Grandeza | Esperado | Medido | Erro |
|---|---|---|---|
| Período de portadora | 50 000,000 ns | **50 000,000 ns** | 0,000 ns |
| Frequência | 20,0000 kHz | **20 000,0 Hz (20,0000 kHz)** | **0,0000 %** |

`[FREQ] periodo medido = 50000.000 ns -> f = 20000.0 Hz (20.0000 kHz)`

### 4.4 Defasagem entre os 4 grupos de motor

Esperado: 90° = 12 500 ns entre grupos adjacentes (decisão de interleaving da Fase 0, §4.3).

| Par | Medido | Em graus | Esperado | Erro |
|---|---|---|---|---|
| grupo 0 → 9 | 12 500,000 ns | 90,000° | 90° | 0,000° |
| grupo 0 → 6 | 25 000,000 ns | 180,000° | 180° | 0,000° |
| grupo 0 → 3 | 37 500,000 ns | 270,000° | 270° | 0,000° |

(Os grupos estão defasados no sentido 0 → 9 → 6 → 3, que é 90° por grupo; a magnitude é o que importa.)

### 4.5 Limitação de duty

| `duty_i` (de 4095) | % pedido | duty efetivo (ciclos altos / 8000) | % medido | Comentário |
|---|---|---|---|---|
| 0 | 0,000 % | 0 | **0,000 %** | low-side fica ligado; canal desligado |
| 10 | 0,244 % | 159 | **1,988 %** | **clampado por DUTY_MIN** |
| 205 | 5,006 % | 399 | **4,987 %** | passa direto |
| 2047 | 49,988 % | 3 997 | **49,962 %** | passa direto |
| 3850 | 94,017 % | 7 519 | **93,987 %** | passa direto |
| 4095 | 100,000 % | 7 597 | **94,963 %** | **clampado por DUTY_MAX (~95 %)** |

Todos os valores batem **exatamente** com a fórmula analítica `duty = (2·dthr − 1)/8000`,
com `dthr = trunc(duty_cl · 4000 / 4095)`:

- 100 % → `duty_cl = 3890` → `dthr = 3799` → `(2·3799−1)/8000 = 94,9625 %` ✓ (medido 94,963 %)
- 94,017 % → `dthr = 3760` → 93,9875 % ✓
- 49,988 % → `dthr = 1999` → 49,9625 % ✓
- 5,006 % → `dthr = 200` → 4,9875 % ✓
- 0,244 % → `dthr = 80` (via DUTY_MIN) → 1,9875 % ✓

O leve viés negativo (~0,02 pp) é o truncamento inteiro de `dthr` e a comparação estrita `<`.
**Não é erro de simulação** — é resolvido pela fórmula acima, ciclo a ciclo.

---

## 5. O que se vê no PNG (`pwm_deadtime.png`)

Conferido abrindo o arquivo com `view_image`. Três painéis:

- **(a) Borda de subida do canal 0** — `pwm_o[0]` (cinza) sobe, `lo_o[0]` (azul) cai **no mesmo
  instante**, e `hi_o[0]` (vermelho) só sobe **518,750 ns depois**. O intervalo inteiro
  aparece com os **dois gates em 0** → é visualmente impossível haver shoot-through.
  A seta dupla marca o dead-time medido.
- **(b) Borda de descida do canal 0** — espelho de (a): `hi` cai imediatamente, `lo` sobe
  518,750 ns depois; de novo a janela dos dois em 0.
- **(c) As 4 portadoras** `hi_o[0]`, `hi_o[3]`, `hi_o[6]`, `hi_o[9]` em 2 períodos (100 µs),
  com linhas verticais rotuladas 0°/90°/180°/270°. As subidas ficam **exatamente** sobre
  as linhas → defasagem de 90° visível a olho nu. A seta inferior marca T = 50 µs → 20 kHz.

**Legibilidade:** eixos rotulados, escalas em ns/µs, durações anotadas em caixa.
Sem sobreposição de traços.

---

## 6. Checagem de síntese

```
$ iverilog -g2005 -o /dev/null pwm_deadtime.v      -> exit 0 (sem erro/warning)
$ yosys -p 'read_verilog pwm_deadtime.v; synth; stat' > yosys.log 2>&1
  -> exit 0, 428 s nesta máquina (ARM), pico de ~1,25 GB de RAM
  -> 0 WARNING, 0 ERROR, 0 latch inferido, 0 memória
```

**Estatística pós-síntese (módulo `pwm_deadtime`):**

```
Number of cells:              22831   (inclui 12 instâncias de pwm_dt_channel)
  $_DFF_PN0_                     28
  $_DFF_PN1_                      4
  (demais são portas combinacionais: AND/OR/XOR/MUX/NAND/NOR/AOI/OAI)
Number of memories:               0
Number of processes:              0
```

**Flip-flops:** 32 no topo (`phase_cnt` 16 + `dt_cycles` 16) + 12 × 18 (por canal:
`hi`, `lo`, `dt_cnt[15:0]`) = **248 FFs**. O contador de dead-time de 16 bits é
obviamente sobredimensionado (por canal, sobra resolução) — dá para cortar para 10 bits
e economizar ~72 FFs; deixei em 16 bits por clareza.

**Interpretação honesta:** isso prova que o RTL é **sintetizável e sem latch acidental**.
**Não** é mapa para FPGA/CPLD real: nenhuma tecnologia foi alvo (`synth_ice40`/`synth_ecp5`/
`synth_gowin` não foram usados porque a família do CPLD/FPGA ainda não está escolhida).
A contagem acima é em primitivas genéricas do Yosys, não em LUTs/LEs do dispositivo.

---

## 7. O que NÃO foi verificado

Esta é a parte que importa para não superestimar o resultado.

1. **Silício real.** Nada foi gravado em FPGA/CPLD/ASIC. Tudo é simulação funcional em
   Icarus Verilog. Não há medida em osciloscópio, nem em bancada.
2. **Jitter.** O clock do testbench é ideal (`#3.125`). Jitter do PLL do ESP32-S3/CPLD,
   *clock jitter* do oscilador, e a variação do dead-time com temperatura e Vcc
   **não** existem neste modelo.
3. **Latência de GPIO.** O atraso entre a saída do registrador e o pino físico, o
   *skew* entre os 12 pinos, e o tempo de propagação pelo gate driver **não** foram
   modelados. O dead-time real no MOSFET = dead-time do RTL **+** atrasos de subida/descida
   do driver, que podem ser maiores que 520 ns.
4. **Sincronismo com ADC.** A janela de amostragem de corrente/BEMF em relação ao PWM
   não foi testada — não há ADC no modelo. Nada garante que o disparo do ADC caia
   fora da janela de dead-time.
5. **Sem análise de timing (SDC).** Não há restrição de período, nem *setup/hold*, nem
   verificação pós-síntese/pós-place-and-route (nenhuma simulação com *back-annotation*).
   "Sintetizável" ≠ "fecha timing a 160 MHz".
6. **Sem verificação formal.** A ausência de shoot-through foi provada por **simulação**
   (362 060 ciclos + 60 000 de estresse). Não houve prova formal (ex.: `symbiyosys`),
   nem *coverage* exaustivo de `duty` × `deadtime` × fase.
7. **Comportamento do PWM com `duty` mudando de forma assíncrona ao meio do período** foi
   exercitado no estresse (mudança a cada ciclo) e **não** gerou shoot-through, mas
   pode gerar pulsos "runt" na saída `pwm_o` — isso **não** foi medido nem caracterizado.
8. **Perda de pulso em duty extremo.** Se o pulso do high-side for mais curto que o
   dead-time (duty abaixo de ~1,04 %), ele não aparece em `hi_o`. O `DUTY_MIN = 2 %`
   mascara isso, mas a resolução útil de duty perto do máximo/mínimo não foi medida.
9. **Bootstrap em regime.** A repoção do capacitor de bootstrap em `duty = 95 %` só está
   **argumentada** (2,5 µs de low-side por período); o tempo de carga real depende do
   valor do capacitor, da resistência do diodo e da corrente do driver — **não** simulado
   aqui (é Fase 2 SPICE, não Verilog).
10. **Encoder de motor / comutação.** Não há lógica de comutação (sequência de 6 passos),
    BEMF, sensor Hall, nem *enable*/freio. O módulo gera apenas as 12 ondas de PWM.
11. **Proteções.** Não há detecção de sobrecorrente, *trip* de falha, nem *blanking*.

---

## 8. Conclusões

- **Dead-time:** 518,750 ns medidos contra 518,750 ns programados (83 ciclos) →
  **erro 0,000 %**. Contra a referência de projeto de 520 ns → **erro −0,240 % (−1,25 ns)**.
- **Frequência:** 20 000,0 Hz medidos contra 20 kHz → **erro 0,0000 %**.
- **Defasagem:** 90,000° / 180,000° / 270,000° medidos → **erro 0,000°**.
- **Shoot-through:** **0 violações** em 362 060 ciclos checados (2,263 ms simulados),
  incluindo 60 000 ciclos de estresse com duty e dead-time aleatórios.
- **Síntese:** 0 warning, 0 latch, 248 flip-flops, 0 memória. Sintetizável em RTL genérico.

**O que ficou duvidoso / não provado:** o número de 520 ns é o do RTL isolado; o dead-time
**no MOSFET** será maior (atraso do gate driver + subida/descida do gate) e não foi medido.
A escolha de `DUTY_MAX = 95 %` está correta para bootstrap, mas o tempo de recarga do
capacitor não foi simulado. E **"sintetizável" não é "fecha timing a 160 MHz"** — falta
a análise de timing com a tecnologia alvo.
