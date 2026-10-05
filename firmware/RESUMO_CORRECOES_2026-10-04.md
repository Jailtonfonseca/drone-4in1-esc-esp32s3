# RESUMO DAS CORREÇÕES DE FIRMWARE — auditoria de 2026-10-04

**Data:** 2026-10-04/05 · **Escopo:** `firmware/` inteiro (13 arquivos) · **Base:** seção F de
[`../AUDITORIA_ERROS_2026-10-04.md`](../AUDITORIA_ERROS_2026-10-04.md) (achados F1–F14 + baixos)

> **MÉTODO:** toda chamada de API duvidosa foi conferida contra os headers **reais** do
> ESP-IDF **v5.4** no GitHub (raw.githubusercontent.com/espressif/esp-idf/v5.4/...):
> `esp_driver_mcpwm/include/driver/mcpwm_prelude.h` (+ timer/oper/cmpr/gen/types),
> `hal/mcpwm_types.h`, `esp_adc/include/esp_adc/adc_oneshot.h`, `adc_cali_scheme.h`,
> `hal/adc_types.h`, `esp_driver_ledc/include/driver/ledc.h` (+ `src/ledc.c`),
> `esp_driver_spi/include/driver/spi_master.h` e `spi_common.h`, `esp_driver_gpio/include/driver/gpio.h`,
> `esp_common/include/esp_check.h`, `soc/esp32s3/include/soc/soc_caps.h` e `clk_tree_defs.h`,
> `esp_driver_mcpwm/Kconfig` e `freertos/FreeRTOS-Kernel/include/freertos/task.h`.
> **Nada foi compilado** (não há ESP-IDF na máquina) — o estado de "AINDA NÃO COMPILADO"
> permanece declarado em todos os cabeçalhos.

---

## 1. O que mudou, arquivo por arquivo

### `main/board_pins.h` — GPIOs reais (F6/RF-07)
- **Todos os GPIOs deixaram de ser `-1`** e passaram a números reais, derivados de duas fontes
  que estão no repo: (a) netlist v7 (`fase3_pcb/gera_pcb_v7.py`, dict `MCU_NETS`, linhas 400-411)
  e (b) tabela "Pin Definitions" (Table 2) do datasheet do WROOM-1 (texto já extraído em
  `datasheets/esp32-wroom-1.txt`, linhas 653-760). A tabela pad→GPIO usada ficou escrita no
  cabeçalho do arquivo.
- Motor 1 = GPIO 4,5,6 · motor 2 = 7,8,9 · motor 3 = 10,11,12 · motor 4 = 13,14,15 —
  **confirmando a Fase 0 §8**. A RF-07 (que acusava divergência) ficou marcada como **REFUTADA**
  no cabeçalho: era comparação de nº de pad com nº de GPIO (achado F6).
- **SPI:** MOSI=GPIO16, SCK=GPIO17, MISO=GPIO18. **CS do ADC1..4 = GPIO 21, 3, 40, 41** — com
  alerta em destaque: ADC_CS2 está no *pad 15*, que é **IO3** (não o IO17, que é o SPI_SCK do
  pad 10). Foi exatamente o ponto que o briefing pediu para conferir com cuidado.
- Demais pinos preenchidos: IMU_CS=42, IMU_INT=47, I2C SDA/SCL=38/39, WD_FEED=48, LED_K=45,
  BOOT_N=0, UART RX/TX=44/43, VBAT_SENSE=GPIO1 (ADC1_CH0), TEMP_SENSE=GPIO2 (ADC1_CH1),
  USB DM/DP=19/20, BUZZER=46.
- Notas novas: pinos de **strapping** (GPIO0/3/45/46) listados com a ressalva da auditoria
  (LED/buzzer em strapping sem análise de margem); **EN_MCU** documentado como pino EN do
  módulo (pull-up REN + botão SW2 + CEN), **não-GPIO**, sem define inventado — e sem valor
  ohmico afirmado (o gerador não especifica o REN).
- A macro `GPIO_NAO_CONFERIDO` ficou definida como política (pino novo sem conferência entra
  como -1), mas **nenhum pino a usa mais**.

### `main/m1_vbat.c` — API do ADC oneshot real (F1) + baixos
- Include corrigido: `driver/adc_oneshot.h` → **`esp_adc/adc_oneshot.h`**; acrescentado
  **`esp_check.h`** (para o `ESP_RETURN_ON_ERROR`).
- **Handle de canal REMOVIDO** (`adc_oneshot_chan_handle_t` não existe): agora
  `adc_oneshot_config_channel(unit, ADC_CHANNEL_0, &cfg)` e
  `adc_oneshot_read(unit, ADC_CHANNEL_0, &raw)` — assinaturas conferidas no header v5.4.
- Campo `.chan` acrescentado na `adc_cali_curve_fitting_config_t` (existe no v5.4).
- Comentários corrigidos: LSB = **3,3 V / 4095 = 805,86 µV** (o comentário dizia 4096);
  nota nova de que o **fallback bruto ignora a escala da atenuação de 12 dB** (fundo de escala
  real ~3,1 V → le ~6 % alto; o critério do passo 10 só fecha com a cali de fábrica).
- GPIO da leitura documentado como conferido (GPIO1 = ADC1_CH0) — os comentários
  "PENDENTE_DE_CONFERIR" saíram.

### `main/m2_pwm_mcpwm.c` — reescrito para a API real (F1) + 20 kHz exatos (F2) + shutdown real (F7) + dead-time removido (F8)
- **API inventada toda removida** (`mcpwm_motor.h`, `mcpwm_new_motor`, `mcpwm_timer_set_compare`,
  `mcpwm_new_deadtime`). Includes reais: `driver/mcpwm_prelude.h`, `driver/gpio.h`, `esp_check.h`.
- **Nova arquitetura (F1): 2 timers × 3 operadores × 2 geradores = 6 saídas no grupo 0**
  (o S3 tem 3 operadores por grupo — `SOC_MCPWM_OPERATORS_PER_GROUP=3`, conferido no
  `soc_caps.h`; o design antigo pedia 6 operadores e estourava o recurso):
  - timer 0 (motor 1): operador 0 → M101/M102; operador 2 → M103/M203;
  - timer 1 (motor 2): operador 1 → M201/M202.
  - Limitação documentada: com 3 operadores, a fase 3 dos dois motores divide o operador 2,
    e um operador só se liga a UM timer — então **M203 corre na referência do timer 0**.
    Como os dois timers são idênticos (20 kHz exatos), a diferença é só a fase da portadora,
    sem efeito elétrico na topologia single-ended. Isolar 100 % cada motor exigiria 4 operadores.
- **20 kHz exatos (F2):** `resolution_hz = 80 MHz` (prescale exato de 2 sobre o
  `MCPWM_TIMER_CLK_SRC_DEFAULT` = PLL 160 MHz do S3) e `period_ticks = 4000`
  (80 MHz / 4000 = 20 000 Hz, tick de 12,5 ns). O código antigo (4096/4095) gerava ~1 Hz.
- **Dead-time REMOVIDO e documentado (F8):** cada IR2104 tem UM pino IN e gera HO/LO
  complementares com dead-time interno fixo (400/520/650 ns) — não existe par complementar
  de geradores no MCU; `mcpwm_generator_set_dead_time` não compraria proteção nenhuma.
  O valor antigo (192 ticks) estava acima do teto do critério a 80 MHz (2,4 µs > 2 µs).
- **PWM edge-aligned clássico:** cada gerador nasce com **force level 0 em hold**
  (`mcpwm_generator_set_force_level(gen, 0, true)`) — saída baixa desde a criação — e ações
  "TEZ → HIGH / compare → LOW" via `mcpwm_generator_set_actions_on_timer_event` /
  `..._on_compare_event`. 6 comparadores independentes (um por canal; duty por fase quando o
  M8 chegar é acrescentar índice, não reescrever).
- **`m2_pwm_set_duty(0)` = desligamento de verdade** (cai no shutdown; não clampa para 2 %) — F7.
  Duty ≠ 0: escreve os comparadores **antes** de liberar o force (level = -1), sem janela de
  duty velho.
- **`m2_pwm_shutdown()` real (F7):** comparadores em 0 **e** force level 0 em hold —
  zerar só o comparador deixaria vazar ~1 tick alto por período na borda do TEZ.
- **Novo `m2_pwm_forca_gpio_baixo()`:** os 6 GPIOs como saída em nível baixo por GPIO puro
  (sem MCPWM) — para chamar antes do init e quando o init falhar (nota eletrica documentada:
  IN baixo = HO baixo/LO alto, sem shoot-through; os 12 SD estão presos ao 3V3 — F12).
- **Callback de timer REMOVIDO** (baixo da auditoria): não fazia nada, tinha assinatura errada
  (a real é `bool cb(mcpwm_timer_handle_t, const mcpwm_timer_event_data_t *, void *)`) e
  semântica invertida. Menos código = menos bug.

### `main/m3_pwm_ledc.c` — canal LEDC correto (F3) + update_duty com 2 args (F1) + shutdown real (F7) + comentários F10
- **`channel = (ledc_channel_t)i` (0..5)** — o antigo `i % 3` rebindava os canais 0-2 no motor 4
  e deixava o motor 3 sem PWM (F3). O S3 tem 8 canais LEDC (conferido no `soc_caps.h`).
- **`ledc_update_duty(speed_mode, channel)`** com os DOIS argumentos, chamado por canal —
  e comprovado no `ledc.c` do v5.4 que essa chamada **re-habilita a saída** depois de um
  `ledc_stop()` (o PWM volta pelo `set_duty` depois do shutdown).
- **`m3_pwm_shutdown()` real (F7):** `ledc_set_duty(0)` + `ledc_update_duty` +
  **`ledc_stop(mode, ch, 0)`** — assinatura real `uint32_t idle_level` (não `bool`, e a constante
  `LEDC_OUTPUT_IDLE_MODE_LOW` citada no briefing **não existe** no header; usado literal 0).
- `m3_pwm_set_duty(0)` = desligamento (mesma regra do M2, F7). Canais nascem com **duty 0**.
- Comentários que contradiziam o código corrigidos (baixos): o texto do "clock de 2 MHz / 40
  contagens / 2 bits" saiu (a constante de 2 MHz era definida e **nunca usada**); a resolução
  real é 10 bits = 1024 contagens. **F10 documentado como NÃO cumprido:** hpoint=10 de 1024 é
  **3,52°**, não os "90,000° exatos" prometidos; não se inventou 256 (=90°) porque com duty de
  95 % o pulso seria truncado no fim do período, e só existem 2 grupos de portadora (o critério
  pede 4). O init agora **loga a frequência real via `ledc_get_freq()`** — autoverificação
  honesta em vez de afirmação.
- Bloco "diferença crítica M2×M3" reescrito pós-F8: não existe dead-time programável em nenhum
  dos dois; `m3_pwm_deadtime_e_fixo()` mantida (com a ressalva de que migrar p/ MCPWM não
  compraria dead-time nesta topologia).
- **Novo `m3_pwm_forca_gpio_baixo()`** (mesma função/razão do M2).
- `LEDC_AUTO_CLK` mantido; inclui `esp_check.h` e `driver/gpio.h`.

### `main/m4_adc_spi.c` — protocolo MCP3208 corrigido (F4)
- **`command_bits = 0`** (o antigo `M4_SPI_TX_BYTES * 8` empurrava 24 clocks de DIN=0 antes do
  quadro, deslocando o enquadramento).
- **Framing full-duplex de 1 transação / 3 bytes, conferido contra o DS21298:**
  `tx = {0x06 | (ch>>2), (ch&0x03)<<6, 0x00}` (start=1, SGL/DIFF=1 single-ended, D2..D0 = canal).
  A montagem antiga colidia bits e fazia os canais 0/2, 1/3, 4/6 e 5/7 lerem iguais.
- **Decode corrigido:** `raw = ((rx[1] & 0x0F) << 8) | rx[2]` (o antigo
  `((rx[1]<<5)|(rx[2]>>3))&0xFFF` lia os clocks errados e só "funcionava" em CH0/CH4).
- **`SPI_DEVICE_HALFDUPLEX` REMOVIDO** (`.flags = 0`): o MCP3208 devolve o dado nos mesmos
  clocks do comando — full-duplex obrigatório.
- **CS por dispositivo mantido** (`spics_io_num` de cada GPIO do board_pins: 21/3/40/41);
  `clock_source = SPI_CLK_SRC_DEFAULT` explícito; `rxlength = 0` (= length, documentado).
- Barômetro: comentário corrigido — **é I²C (pads 31/32), não mora no SPI** (baixo da auditoria).
  No barramento SPI mora o IMU (RF-09), e isso ficou documentado.
- **Bug de unidade encontrado na revisão:** o log do offset imprimia o valor de
  `m4_raw_to_ampere` (amperes) rotulado como "mA" — erro de 1000× no número impresso. Corrigido.
- Nota nova (baixo registrado): `s_circuito`/`s_canal` do round-robin assumem **um único
  chamador**; multi-task exige exclusão mútua.
- Include `esp_timer.h` **removido** (não chamava nada dele).

### `main/app_main.c` — init antes do shutdown + estado seguro real (F5)
- **Nova ordem de boot, cada passo documentado:**
  1. `m2_pwm_forca_gpio_baixo()` + `m3_pwm_forca_gpio_baixo()` — os **12 pinos PWM em nível baixo
     por GPIO puro, antes de qualquer driver** (os IN dos IR2104 não têm pull na placa — netlist
     v7 — então alguém tem que dirigi-los cedo);
  2. `m2_pwm_init()`, `m3_pwm_init()`, `m4_adc_init()`, `m1_vbat_init()` — **inits TODOS antes dos
     shutdown** (F5; o antigo nunca chamava init e os shutdown falhavam com INVALID_STATE);
  3. shutdown nos módulos cujo init funcionou; **se o init falhou, os pinos dele seguem em
     nível baixo pela rota 1** — estado seguro real, não apenas log de erro;
  4. a task de leitura só nasce se o M4 subiu.
- **"Pilha em bytes" MANTIDO — contra-achado:** o header real do ESP-IDF v5.4
  (`task.h`, doxygen do `xTaskCreate`) diz *"usStackDepth: The size of the task stack specified
  as the NUMBER OF BYTES. Note that this differs from vanilla FreeRTOS."* O baixo da auditoria
  ("xTaskCreate conta palavras, não bytes") **está errado para o ESP-IDF** — mantive "bytes" com
  a citação do header no comentário.
- Nota nova sobre o `vTaskDelay(pdMS_TO_TICKS(1))`: só é "1 tick de verdade" porque o
  `sdkconfig.defaults` agora tem `CONFIG_FREERTOS_HZ=1000` (F9).

### `main/CMakeLists.txt` — baixos
- **`CONFIG_MCPWM_ISR_DEBUG` removido** (não existe). As opções reais do componente
  (`esp_driver_mcpwm/Kconfig` v5.4) estão documentadas: `CONFIG_MCPWM_ISR_IRAM_SAFE` e
  **`CONFIG_MCPWM_CTRL_FUNC_IN_IRAM`** — nenhuma das duas é necessária aqui (nenhum callback de
  timer registrado; controle nunca chamado em ISR) e por isso nenhuma foi ligada.
- **`esp_timer` removido das REQUIRES** (nada usava — dependência sem consumidor é declaração
  falsa); o include correspondente saiu do m4. `driver` (meta-componente que puxa
  esp_driver_gpio/mcpwm/ledc/spi) + `esp_adc` + freertos ficam.

### `sdkconfig.defaults` — F9
- **`CONFIG_FREERTOS_HZ=1000`** acrescentado, com o porquê: sem ele o default é 100 Hz e
  `pdMS_TO_TICKS(1)` trunca para 0 tick → `vTaskDelay(0)` = yield-loop que faminta a idle e
  dispara o task watchdog. Demais chaves mantidas.

### `README.md`
- Banner mantido (NADA FOI COMPILADO — continua verdade) + parágrafo novo do estado pós-auditoria.
- Seção "nenhum GPIO é GPIO de verdade" **reescrita**: GPIOs agora são reais, com a origem
  (netlist v7 + datasheet) e a armadilha do ADC_CS2; RF-07 marcada como falsa.
- Seção dead-time **reescrita** (F8): é do IR2104 nos 4 motores; o dead-time programável do M2
  foi removido; consequência elétrica do estado seguro (IN baixo = low-side fechado; SD preso
  ao 3V3 — F12) documentada.
- Tabela de arquivos e a seção "como compilar" atualizadas (não se espera mais falhar em
  `board_pins.h`; o que pode pegar é assinatura fina entre versões do IDF e Kconfig renomeado).

### Cabeçalhos `.h` (m1/m2/m3/m4) e `firmware/CMakeLists.txt`
- Todos os cabeçalhos "ESQUELETO" atualizados para o estado real:
  **"corrigido pela auditoria de 2026-10-04 (ver AUDITORIA_ERROS_2026-10-04.md seção F);
  AINDA NÃO COMPILADO — precisa de idf.py build para validar"** — avisos de segurança e
  histórico preservados.
- `m2_pwm_mcpwm.h`/`m3_pwm_ledc.h`: documentam a nova arquitetura e declaram as funções novas
  `*_forca_gpio_baixo()`.
- `firmware/CMakeLists.txt`: só o cabeçalho mudou (a estrutura do projeto estava correta).

## 2. O que NÃO mudou (por ser correto — "não reescrever o que funciona")
- Divisor VBAT 100 k / 13,7 k → razão 0,1204925242 e os pontos de aceite do passo 10.
- Escala de corrente 0,5 mΩ × 50 V/V = 25 mV/A (40 A/V) e o critério "1 mV ↔ 40 mA".
- Divisor BEMF 8,2 k/1,0 k (razão 0,1086956522) e as conversões de LSB.
- `board_pins.h` como tabela única de verdade; `M4_SPI_HOST = SPI2_HOST`; round-robin do M4;
  clamps 2–95 %; avisos de segurança ("não energizar", "não é seguro voar") em todos os arquivos.

## 3. Desvios deliberados do briefing (com evidência)
1. **"pilha em bytes → palavras" NÃO foi aplicado.** O header v5.4 diz BYTES (citação no
   `app_main.c`). O item baixo da auditoria descreve o FreeRTOS vanilla, não o port do ESP-IDF.
2. **`ledc_stop(...)` recebe `uint32_t idle_level`**, não `bool`; e **não existe** a constante
   `LEDC_OUTPUT_IDLE_MODE_MODE_LOW`/`LEDC_OUTPUT_IDLE_MODE_LOW` no v5.4 — usado literal `0`.
3. **M2:** com 3 operadores × 2 geradores = 6 saídas, um canal (M203) inevitavelmente fica no
   timer do outro motor (isolar 100 % cada motor exigiria 4 operadores > 3 disponíveis).
   Documentado no arquivo; sem efeito elétrico (timers idênticos).
4. **F10/F11 não "resolvidos por teclado":** hpoint=10 (3,52°) e 10 bits ficaram como estão,
   com o critério marcado como NÃO cumprido e a frequência real logada por `ledc_get_freq()`.
   Inventar 256 ou trocar a resolução sem bancada trunciaria duty e não teria lastro. A alegação
   de "~19,81 kHz (−0,94 %)" do F11 **não foi reproduzida** e por isso não foi copiada para os
   comentários — com APB 80 MHz e 10 bits o divisor 3,90625 é representável; o que vale é a
   medição.
5. REN (pull-up do EN): **sem valor ohmico afirmado** — o gerador não especifica (só footprint).

## 4. O que ainda precisa de validação (por build e por bancada)
**Por `idf.py build` (nada disto foi compilado — não há toolchain/ESP-IDF na máquina):**
1. Compilar contra a v5.4 real: `idf.py set-target esp32s3 && idf.py build`.
2. Conferir se sobrou divergência fina de assinatura (todas as chamadas foram verificadas contra
   a v5.4, mas verificação de leitura não é compilação).
3. Kconfig do `sdkconfig.defaults` (`CONFIG_FREERTOS_HZ`, brownout, clock 240 MHz, partição,
   UART) — nomes conferidos informalmente; o Kconfig real é quem valida.
4. Os avisos de -Werror do IDF (designated initializers, format strings de log com casts).

**Por bancada (com a placa, SEM hélices — ver PLANO_TESTE_BANCADA.md):**
1. **Passo 9:** osciloscópio nos 12 sinais — período 50 000 ns ± 0,1 % (M2 por construção deve
   dar exato; M3 conferir contra o log do `ledc_get_freq`), sobreposição de gates = 0 (é do
   IR2104 — F8), e **os 12 pinos em nível baixo logo após o boot** (valida o `forca_gpio_baixo`
   + force level + `ledc_stop`).
2. **Passo 10:** VBAT em 19,8 / 22,2 / 25,2 V com erro < 2 % (com a cali de fábrica; o fallback
   erra ~6 % — documentado).
3. **Passos 11/12:** BEMF < 1 % (depende do fix C2 da PCB — os divisores BEMF estão órfãos na
   netlist!) e linearidade de corrente < 2 % entre 5 e 30 A com offset a 0 A anotado.
4. **F10/F11:** decidir a defasagem real das 4 portadoras (hpoint medido; hoje 3,52°) e se o
   LEDC fecha 20 kHz ± 0,1 % (senão: 8 bits ou MCPWM — F11).
5. **F12:** hardware não permite desligar os 12 IR2104 por firmware (SD ao 3V3); qualquer
   failsafe real depende de zerar PWM — o caminho agora existe (shutdown real).
6. **F13:** cadência real do M4 (~1 ksps agregado) segue abaixo dos 480 ksps do plano.
7. **M5 (IMU) não existe** — o barramento SPI compartilhado está documentado, mas sem driver e
   sem arbitragem.
8. Os GPIOs derivam do **netlist v7**; quando a v9 for regenerada (fix C1 do PCB), conferir se
   `MCU_NETS` mudou antes de energizar.

---
*Resumo escrito junto com as correções; cada item acima tem o rastro da evidência no arquivo que
mudou. As linhas de todos os cabeçalhos continuam dizendo a verdade: AINDA NÃO COMPILADO.*
