# firmware/ — ESQUELETO DE FIRMWARE. NADA AQUI FOI COMPILADO.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  NADA NESTE DIRETORIO FOI COMPILADO. NENHUM DESTES ARQUIVOS .c E .h PASSOU   ║
║  PELO PREPROCESSADOR, PELO COMPILADOR OU PELO LINKER DO ESP32-S3.           ║
║                                                                            ║
║  ESTE ESQUELETO NAO FOI TESTADO EM BANCADA, NAO RODOU EM NENHUM ESP32-S3    ║
║  E NAO DEVE SER GRAVADO NUM ESP32-S3 CONECTADO A UMA BATERIA.               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Estado após a auditoria de 2026-10-04** (`../AUDITORIA_ERROS_2026-10-04.md`,
seção F): os erros F1–F9 e os baixos foram corrigidos — API ESP-IDF v5.4
verificada chamada por chamada contra os headers reais, 20 kHz exatos no M2,
canais LEDC únicos, protocolo MCP3208 corrigido, `app_main` chamando os init,
GPIOs reais em `board_pins.h` e `CONFIG_FREERTOS_HZ=1000`. O estado de
**AINDA NÃO COMPILADO** não mudou: não há ESP-IDF nesta máquina, e é o
`idf.py build` que valida o resto. Cada arquivo carrega no cabeçalho o
carimbo "corrigido pela auditoria de 2026-10-04 … AINDA NÃO COMPILADO".

## O que existe de verdade nesta máquina

Uma coisa, e ela é real: **um compilador C Xtensa para o ESP32-S3 está instalado
e foi testado.** Ele compila um `.c` para `.o`, linka para `.elf` de 32 bits
(`Machine: Tensilica Xtensa Processor`) e gera `.bin`. A saída real está em
[`build_log.txt`](build_log.txt). Isso prova que a máquina tem um compilador
capaz de gerar código para o ESP32-S3. **Não prova nada sobre o código deste
diretório**, que não passou por esse compilador.

O que **não** existe: o ESP-IDF. Sem ele não há `idf.py`, não há
`esp32s3.project.ld`, não há startup, não há os componentes de driver contra os
quais estes `.c` include. Por isso nenhum build de `main/*.c` foi tentado — não
seria um build, seria um erro de configuração.

Se alguém te disser que "o firmware do drone compila", peça o `build_log.txt`
dele. O daqui é [`build_log.txt`](build_log.txt) e ele deixa bem claro o que é
e o que não é.

## O que este diretório é

Um esqueleto de quatro módulos de `plano/WP4_FIRMWARE.md` §5, escritos para
servirem de ponto de partida — com todas as decisões que vieram do plano
carimbadas no código e todos os números sem lastro marcados como tal.

| Arquivo | Módulo da §5 | O que é |
|---|---|---|
| `main/board_pins.h` | — | mapa de pinos: pads do netlist v7 + GPIOs do datasheet do WROOM-1 |
| `main/m1_vbat.c/.h` | **M1** | leitura de VBAT pelo divisor 100 k / 13,7 k |
| `main/m2_pwm_mcpwm.c/.h` | **M2** | PWM dos motores 1 e 2 no MCPWM (2 timers × 3 operadores × 2 geradores, 20 kHz exatos) |
| `main/m3_pwm_ledc.c/.h` | **M3** | PWM dos motores 3 e 4 no LEDC (canais 0–5), defasagem por hpoint |
| `main/m4_adc_spi.c/.h` | **M4** | leitura dos 4× MCP3208 por SPI full-duplex, round-robin |
| `main/app_main.c` | — | ponto de entrada; **não comuta motor nenhum** |
| `CMakeLists.txt`, `main/CMakeLists.txt` | — | estrutura de projeto ESP-IDF v5 |
| `sdkconfig.defaults` | — | tick de 1 kHz, clock de 240 MHz, brownout ligado, UART0 a 115200 |
| `build_log.txt` | — | o que **realmente** foi compilado: um hello world de 5 linhas |

## As duas coisas que ninguém deve pular

**1. Os GPIOs agora são GPIOs de verdade — mas continuam sem bancada.** Os
números de *pad* vêm do netlist do layout v7 (`fase3_pcb/gera_pcb_v7.py`,
linhas 400-411) e a tradução pad → GPIO vem da tabela "Pin Definitions" do
datasheet do módulo, **extraída na auditoria de 2026-10-04** (achado F6: a
premissa da RF-07 era falsa — comparavam-se pads com GPIOs; o layout
*confirma* a Fase 0 §8: motor 1 = GPIO 4-6, 2 = 7-9, 3 = 10-12, 4 = 13-15).
A armadilha que derruba revisão: ADC_CS2 está no pad 15, que é o **IO3**, não
o IO17 (que é o SPI_SCK do pad 10). "Conferido" aqui significa conferido
contra o datasheet e o netlist — **não** significa testado num módulo real.

**2. O dead-time dos QUATRO motores é do IR2104, não do firmware.** Cada
IR2104 tem **um único pino IN** e gera HO/LO complementares com dead-time
interno fixo (400/520/650 ns, RF-14). São 12 sinais single-ended: não existe
par complementar de geradores no MCU, e o dead-time programável do MCPWM não
tem o que atrasar nessa topologia — por isso foi **removido** do M2 (achado
F8; "M2 = MCPWM por causa do dead-time" era erro de concepção). A função
`m3_pwm_deadtime_e_fixo()` continua devolvendo 0 de propósito — para o fato
ficar no código, e não só num comentário. A consequência elétrica do estado
seguro também está documentada nos fontes: IN baixo = HO baixo e LO alto
(low-side conduzindo), e os 12 SD estão presos ao 3V3 por 10k sem GPIO (F12)
— o firmware não pode desligar os gate drivers.

## Como compilar isto, quando houver ESP-IDF

```bash
# 1. Instalar o ESP-IDF (procedimento oficial na documentacao da Espressif;
#    ver fase4_entrega/FIRMWARE_BUILD.md secao 5)
. $HOME/esp/esp-idf/export.sh

# 2. Build de teste deste diretorio — o comando que o Jailton vai rodar
cd /opt/jupyter/work/drone/firmware && idf.py set-target esp32s3 && idf.py build
```

O primeiro build honesto agora não tem erro esperado em `board_pins.h` (os
GPIOs estão preenchidos). O que o `idf.py build` pode ainda pegar, nesta
ordem: divergência fina de assinatura entre v5.3/v5.4/v5.5 (as chamadas foram
conferidas contra a v5.4 exata — `driver/mcpwm_prelude.h`,
`esp_adc/adc_oneshot.h`, `driver/ledc.h`, `driver/spi_master.h`), opções de
Kconfig renomeadas no `sdkconfig.defaults`, e nada mais que os fontes não
expliquem. O build que compilar ainda **não** valida: frequência, níveis e
protocolo só existem no osciloscópio, com a placa em bancada **sem helices**.

## O que este firmware não faz, e por que isso importa

Não existe comutação de motor (M8), não existe link de comando (M9), não
existe failsafe (M10), não existe watchdog (M11). Sem o M10, perder o controle
do transmissor **não corta os motores** — o critério de aceite do M10 na §5
exige corte em 200 ms, e nada aqui chega perto disso. Por isso o `app_main.c`
deixa isso escrito no log de boot, na primeira linha que ele imprime.

A ordem do plano (`plano/WP4_FIRMWARE.md` §5, fatia de bancada de 160 h) é
M0–M6 + M10 + M11. Este esqueleto cobre quatro células dessa fatia: M1, M2, M3
e M4. Não cobre M0, M5, M6, M10 e M11, e a soma está em 320 h **[EST]**, não
medida.
