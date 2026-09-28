/* ===========================================================================
 * board_pins.h — mapa de pinos do modulo ESP32-S3-WROOM-1 do drone
 *
 * ESQUELETO NAO VERIFICADO. ESTE ARQUIVO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado (ver fase4_entrega/FIRMWARE_BUILD.md),
 * entao nao existe idf.py nem o componente driver para compilar contra. O
 * que EXISTE e um compilador C Xtensa instalado e testado com um .c de 5
 * linhas (ver firmware/build_log.txt) — isso nao diz nada sobre este arquivo.
 *
 * Origem dos numeros abaixo: netlist do layout v7, gerador
 * fase3_pcb/gera_pcb_v7.py, linhas 400-411 (dict MCU_NETS), lido nesta maquina
 * com sed -n '395,415p' na auditoria de 2026-09-28.
 *
 * ---------------------------------------------------------------------
 * ALERTA QUE PRECEDE TUDO: estes numeros sao PADS DO MODULO, nao GPIOs.
 * ---------------------------------------------------------------------
 * plano/WP4_FIRMWARE.md, RF-07, registra que o mapa da Fase 0 §8
 * (motor 1 = GPIO 4,5,6 · motor 2 = 7,8,9 · motor 3 = 10,11,12 · motor 4 =
 * 13,14,15) DIVERGE do layout v7 inteiro nos motores 2, 3 e 4, e que o pad 8
 * — que a Fase 0 dava ao motor 2 — e no layout o PWM_M403. Escrever firmware
 * com a §8 produz um binario que nao funciona na placa.
 *
 * A traducao pad -> GPIO do WROOM-1 NAO FOI FEITA aqui de proposito. Ela exige
 * a tabela de pinagem do modulo (datasheets/esp32-s3-wroom-1_datasheet_en.pdf,
 * secao de pin definitions), que nao foi extraida nesta sessao. Todo numero de
 * GPIO abaixo esta marcado como PENDENTE_DE_CONFERIR e vale -1 ate ser lido do
 * datasheet do modulo. Escrever -1 em vez de um palpite e o que impede que
 * este arquivo gere um firmware silenciosamente errado.
 *
 * O TRM da Espressif tambem nao esta no disco (PLANO_FINAL / WP4 §7.5).
 * ======================================================================== */

#ifndef BOARD_PINS_H
#define BOARD_PINS_H

#include <stdint.h>

/* Macro que marca todo GPIO ainda nao conferido contra o datasheet do modulo.
 * Se o valor chegar a um gpio_set_direction() assim, o build quebra de forma
 * barulhenta em vez de piscar o LED errado em voo. */
#define GPIO_NAO_CONFERIDO (-1)

/* --- VBAT_SENSE -----------------------------------------------------------
 * saida do divisor RVB1 (100 k) / RVB2 (13,7 k). O layout liga VBAT_SENSE
 * no pad 39 do modulo. A fase 1 anota "VBAT_SENSE -> ADC1 GPIO1" e a fase 1
 * tambem marca GPIO1 como ADC1_CH0. Este e o unico GPIO com origem declarada
 * em duas fases, mas continua PENDENTE_DE_CONFERIR. */
#define VBAT_SENSE_PAD       39
#define VBAT_SENSE_GPIO      GPIO_NAO_CONFERIDO   /* a fase 1 sugere GPIO1  */

/* --- TEMP_SENSE -----------------------------------------------------------
 * NTC, pad 38. A fase 1 sugere GPIO2 (ADC1_CH1). */
#define TEMP_SENSE_PAD       38
#define TEMP_SENSE_GPIO      GPIO_NAO_CONFERIDO   /* a fase 1 sugere GPIO2  */

/* --- Motor 1 e 2: MCPWM, 6 sinais IN do IR2104, dead-time em HW -----------
 * Pads lidos do dict MCU_NETS do layout v7. A ordem das 3 entradas de cada
 * motor e a ordem das 3 nets do gerador, nao uma convencao de fase. */
#define PWM_M101_PAD          4
#define PWM_M102_PAD          5
#define PWM_M103_PAD          6
#define PWM_M201_PAD          7
#define PWM_M202_PAD         12
#define PWM_M203_PAD         17

#define PWM_M101_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M102_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M103_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M201_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M202_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M203_GPIO        GPIO_NAO_CONFERIDO

/* --- Motor 3 e 4: LEDC, 6 sinais IN do IR2104, dead-time fixo no driver ---
 * Pads do layout v7. Repare que o pad 8 e PWM_M403 (motor 4, fase 3) e nao
 * do motor 2: e exatamente a divergencia que a RF-07 acusa. */
#define PWM_M301_PAD         18
#define PWM_M302_PAD         19
#define PWM_M303_PAD         20
#define PWM_M401_PAD         21
#define PWM_M402_PAD         22
#define PWM_M403_PAD          8

#define PWM_M301_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M302_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M303_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M401_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M402_GPIO        GPIO_NAO_CONFERIDO
#define PWM_M403_GPIO        GPIO_NAO_CONFERIDO

/* --- SPI dos 4x MCP3208 --------------------------------------------------
 * Barramento unico, disputado: RF-09 conta 24 canais x 20 kHz x 24 clocks =
 * 11 520 000 clocks/s, que estoura a 8 MHz e a 10 MHz e so cabe a 20 MHz.
 * A solucao de saida que o proprio plano aponta e o round-robin com um CI por
 * vez (RF-09), com fCLK = 20 x fSAMPLE = 0,60 MHz. */
#define ADC_SPI_SCK_PAD      10
#define ADC_SPI_MOSI_PAD      9
#define ADC_SPI_MISO_PAD     11
#define ADC_CS1_PAD          23
#define ADC_CS2_PAD          15
#define ADC_CS3_PAD          33
#define ADC_CS4_PAD          34

#define ADC_SPI_SCK_GPIO     GPIO_NAO_CONFERIDO
#define ADC_SPI_MOSI_GPIO    GPIO_NAO_CONFERIDO
#define ADC_SPI_MISO_GPIO    GPIO_NAO_CONFERIDO
#define ADC_CS1_GPIO         GPIO_NAO_CONFERIDO
#define ADC_CS2_GPIO         GPIO_NAO_CONFERIDO
#define ADC_CS3_GPIO         GPIO_NAO_CONFERIDO
#define ADC_CS4_GPIO         GPIO_NAO_CONFERIDO

/* --- Demais nets do MCU (ainda nao usadas por M1..M4) ---------------------
 * Listadas para deixar visivel o que existe no netlist e o que os modulos
 * M1..M4 deste esqueleto ainda nao cobrem. */
#define IMU_INT_PAD          24
#define IMU_CS_PAD           35
#define WD_FEED_PAD          25
#define LED_K_PAD            26
#define BOOT_N_PAD           27
#define BUZZER_PAD           16
#define I2C_SDA_PAD          31
#define I2C_SCL_PAD          32
#define UART_TX_PAD          37
#define UART_RX_PAD          36

#endif /* BOARD_PINS_H */
