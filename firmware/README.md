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
| `main/board_pins.h` | — | mapa de pinos, extraído do netlist do layout v7 |
| `main/m1_vbat.c/.h` | **M1** | leitura de VBAT pelo divisor 100 k / 13,7 k |
| `main/m2_pwm_mcpwm.c/.h` | **M2** | PWM dos motores 1 e 2 no MCPWM, dead-time em hardware |
| `main/m3_pwm_ledc.c/.h` | **M3** | PWM dos motores 3 e 4 no LEDC, defasagem de 90° |
| `main/m4_adc_spi.c/.h` | **M4** | leitura dos 4× MCP3208 por SPI, round-robin |
| `main/app_main.c` | — | ponto de entrada; **não comuta motor nenhum** |
| `CMakeLists.txt`, `main/CMakeLists.txt` | — | estrutura de projeto ESP-IDF v5 |
| `sdkconfig.defaults` | — | clock de 240 MHz, brownout ligado, UART0 a 115200 |
| `build_log.txt` | — | o que **realmente** foi compilado: um hello world de 5 linhas |

## As duas coisas que ninguém deve pular

**1. Nenhum GPIO aqui é um GPIO de verdade.** Todos estão `-1` em
`board_pins.h`, com a macro `GPIO_NAO_CONFERIDO`. Os números de *pad* vêm do
netlist do layout v7 (`fase3_pcb/gera_pcb_v7.py`, linhas 400-411), mas **pad de
módulo não é GPIO** — e a **RF-07** do plano acusa a Fase 0 §8 de divergir do
layout inteiro nos motores 2, 3 e 4 (inclusive o pad 8, que a Fase 0 dava ao
motor 2 e o layout dá ao motor 4). Traduzir pad → GPIO exige a tabela de
pinagem do `datasheets/esp32-s3-wroom-1_datasheet_en.pdf`, que **não foi
extraída**. Deixei `-1` em vez de palpite: é o que faz o build quebrar alto, em
vez de girar um motor no pad errado.

**2. O dead-time dos motores 3 e 4 não é do firmware.** Os motores 1 e 2 vão
por MCPWM e têm dead-time programável em hardware. Os motores 3 e 4 vão por
LEDC, que **não gera dead-time**: o único deles é o do IR2104, fixo no driver,
de 400 ns a 650 ns (**RF-14**). Por isso o M3 tem janela própria, diferente da
do M2, e `m3_pwm_ledc.c` tem uma função `m3_pwm_deadtime_e_fixo()` que
devolve 0 de propósito — para o fato ficar no código, e não só num comentário.

## Como compilar isto, quando houver ESP-IDF

```bash
# 1. Instalar o ESP-IDF (procedimento oficial na documentacao da Espressif;
#    ver fase4_entrega/FIRMWARE_BUILD.md secao 5)
. $HOME/esp/esp-idf/export.sh

# 2. Build de teste deste diretorio — o comando que o Jailton vai rodar
cd /opt/jupyter/work/drone/firmware && idf.py set-target esp32s3 && idf.py build
```

Depois do `idf.py build`, espere-se **falhar** em `main/board_pins.h` → GPIO.
Isso não é um problema: é o `-1` fazendo o trabalho dele. O primeiro build
honesto é o que documenta os erros da API, e a lista dos que são esperados está
em `fase4_entrega/FIRMWARE_BUILD.md` seção 6.

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
