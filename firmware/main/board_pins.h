/* ===========================================================================
 * board_pins.h — mapa de pinos do modulo ESP32-S3-WROOM-1 do drone
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F1/F6/RF-07); AINDA NAO
 * COMPILADO — precisa de idf.py build para validar. O ESP-IDF nao esta
 * instalado nesta maquina (ver fase4_entrega/FIRMWARE_BUILD.md); o que existe
 * e um compilador C Xtensa testado com um .c de 5 linhas (firmware/
 * build_log.txt), o que nao valida este arquivo.
 *
 * ORIGEM DOS NUMEROS (duas fontes, ambas no repo, ambas lidas nesta maquina):
 *   1. Net -> pad do modulo: netlist do layout v7, dict MCU_NETS em
 *      fase3_pcb/gera_pcb_v7.py linhas 400-411.
 *   2. Pad -> GPIO: tabela "Pin Definitions" (Table 2) do datasheet do modulo,
 *      datasheets/esp32-s3-wroom-1_datasheet_en.pdf, secao 3.2; texto extraido
 *      em datasheets/esp32-wroom-1.txt, linhas 653-760.
 * Tabela pad -> GPIO usada abaixo (41 pads; 1/40/41 = GND, 2 = 3V3, 3 = EN):
 *      4=IO4  5=IO5  6=IO6  7=IO7  8=IO15 9=IO16 10=IO17 11=IO18 12=IO8
 *      13=IO19(USB_D-) 14=IO20(USB_D+) 15=IO3 16=IO46 17=IO9 18=IO10
 *      19=IO11 20=IO12 21=IO13 22=IO14 23=IO21 24=IO47 25=IO48 26=IO45
 *      27=IO0 31=IO38 32=IO39 33=IO40 34=IO41 35=IO42 36=GPIO44(U0RXD)
 *      37=GPIO43(U0TXD) 38=IO2(ADC1_CH1) 39=IO1(ADC1_CH0)
 *
 * ---------------------------------------------------------------------
 * RF-07 ESTA REFUTADA (achado F6 da auditoria). A "divergencia" entre a
 * Fase 0 §8 e o layout v7 era artefato de comparar NUMERO DE PAD com
 * NUMERO DE GPIO. Traduzido pela tabela acima, o layout CONFIRMA a §8:
 * motor 1 = GPIO 4,5,6 · motor 2 = GPIO 7,8,9 · motor 3 = GPIO 10,11,12 ·
 * motor 4 = GPIO 13,14,15 (o pad 8, que a RF-07 apontava como "divergencia",
 * e o IO15 — fase 3 do motor 4, exatamente como na §8).
 * ---------------------------------------------------------------------
 *
 * ARMADILHA QUE JA DERRUBOU UMA REVISAO: ADC_CS2 esta no PAD 15, e o pad 15
 * e o IO3 (GPIO3). NAO confundir com o pad 10 (IO17), que e o SPI_SCK.
 * CS do ADC1..4 = GPIO 21, 3, 40, 41 — ver a secao SPI abaixo.
 *
 * AVISO DE SEGURANCA QUE CONTINUA VALENDO: nada aqui foi testado em bancada.
 * Nao energizar a placa com helices; ver firmware/README.md.
 * ======================================================================== */

#ifndef BOARD_PINS_H
#define BOARD_PINS_H

#include <stdint.h>

/* Macro herdada da epoca em que os GPIOs eram palpite. NENHUM pino abaixo a
 * usa mais depois da auditoria de 2026-10-04; ela fica definida porque e a
 * politica do projeto: pino novo sem conferencia contra o datasheet entra
 * como GPIO_NAO_CONFERIDO e o build quebra em gpio_config()/GPIO matrix. */
#define GPIO_NAO_CONFERIDO (-1)

/* --- VBAT_SENSE -----------------------------------------------------------
 * Saida do divisor RVB1 (100 k) / RVB2 (13,7 k). Pad 39 do modulo = IO1 =
 * GPIO1 = ADC1_CH0 (datasheet Table 2). Fase 1 e Fase 0 §8 concordam. */
#define VBAT_SENSE_PAD       39
#define VBAT_SENSE_GPIO      1          /* GPIO1 = ADC1_CH0, conferido */

/* --- TEMP_SENSE -----------------------------------------------------------
 * NTC, pad 38 = IO2 = GPIO2 = ADC1_CH1 (datasheet Table 2). */
#define TEMP_SENSE_PAD       38
#define TEMP_SENSE_GPIO      2          /* GPIO2 = ADC1_CH1, conferido */

/* --- Motor 1 e 2: MCPWM, 6 sinais IN do IR2104, dead-time em HW -----------
 * Pads lidos do dict MCU_NETS do layout v7; GPIOs pela tabela do datasheet.
 * A ordem das 3 entradas de cada motor e a ordem das 3 nets do gerador, nao
 * uma convencao de fase. Motor 1 = GPIO 4,5,6; motor 2 = GPIO 7,8,9 — igual
 * a Fase 0 §8 (a RF-07 que acusava divergencia aqui foi refutada, F6). */
#define PWM_M101_PAD          4
#define PWM_M102_PAD          5
#define PWM_M103_PAD          6
#define PWM_M201_PAD          7
#define PWM_M202_PAD         12
#define PWM_M203_PAD         17

#define PWM_M101_GPIO         4          /* pad 4  = IO4  */
#define PWM_M102_GPIO         5          /* pad 5  = IO5  */
#define PWM_M103_GPIO         6          /* pad 6  = IO6  */
#define PWM_M201_GPIO         7          /* pad 7  = IO7  */
#define PWM_M202_GPIO         8          /* pad 12 = IO8  */
#define PWM_M203_GPIO         9          /* pad 17 = IO9  */

/* --- Motor 3 e 4: LEDC, 6 sinais IN do IR2104, dead-time fixo no driver ---
 * Pads do layout v7; GPIOs pela tabela do datasheet. Motor 3 = GPIO 10,11,12;
 * motor 4 = GPIO 13,14,15 — igual a Fase 0 §8. O pad 8 que a RF-07 apontava
 * como anomalia e o IO15: fase 3 do motor 4, em conformidade com a §8. */
#define PWM_M301_PAD         18
#define PWM_M302_PAD         19
#define PWM_M303_PAD         20
#define PWM_M401_PAD         21
#define PWM_M402_PAD         22
#define PWM_M403_PAD          8

#define PWM_M301_GPIO        10         /* pad 18 = IO10 */
#define PWM_M302_GPIO        11         /* pad 19 = IO11 */
#define PWM_M303_GPIO        12         /* pad 20 = IO12 */
#define PWM_M401_GPIO        13         /* pad 21 = IO13 */
#define PWM_M402_GPIO        14         /* pad 22 = IO14 */
#define PWM_M403_GPIO        15         /* pad 8  = IO15 */

/* --- SPI dos 4x MCP3208 --------------------------------------------------
 * Barramento unico, disputado: RF-09 conta 24 canais x 20 kHz x 24 clocks =
 * 11 520 000 clocks/s, que estoura a 8 MHz e a 10 MHz e so cabe a 20 MHz.
 * A solucao de saida que o proprio plano aponta e o round-robin com um CI por
 * vez (RF-09), com fCLK = 20 x fSAMPLE = 0,60 MHz.
 * GPIOs: MOSI pad 9 = IO16; SCK pad 10 = IO17; MISO pad 11 = IO18.
 * CS por dispositivo: ADC_CS1 pad 23 = IO21; ADC_CS2 pad 15 = IO3;
 * ADC_CS3 pad 33 = IO40; ADC_CS4 pad 34 = IO41. */
#define ADC_SPI_SCK_PAD      10
#define ADC_SPI_MOSI_PAD      9
#define ADC_SPI_MISO_PAD     11
#define ADC_CS1_PAD          23
#define ADC_CS2_PAD          15
#define ADC_CS3_PAD          33
#define ADC_CS4_PAD          34

#define ADC_SPI_SCK_GPIO     17         /* pad 10 = IO17 */
#define ADC_SPI_MOSI_GPIO    16         /* pad 9  = IO16 */
#define ADC_SPI_MISO_GPIO    18         /* pad 11 = IO18 */
#define ADC_CS1_GPIO         21         /* pad 23 = IO21 */
#define ADC_CS2_GPIO          3         /* pad 15 = IO3  — GPIO3, NAO GPIO17 */
#define ADC_CS3_GPIO         40         /* pad 33 = IO40 */
#define ADC_CS4_GPIO         41         /* pad 34 = IO41 */

/* --- Demais nets do MCU (ainda nao usadas por M1..M4) ---------------------
 * Listadas para deixar visivel o que existe no netlist e o que os modulos
 * M1..M4 deste esqueleto ainda nao cobrem. GPIOs pela tabela do datasheet.
 *
 * STRAPPING (conferir sempre antes de mudar nivel em reset/boot):
 *   GPIO0  (BOOT_N): selecao de modo de boot; botao SW1 + pull-up RBOOT.
 *   GPIO3  (ADC_CS2): selecao da fonte do JTAG.
 *   GPIO45 (LED_K): selecao da tensao da VDD_SPI (0 = flash a 3,3 V).
 *   GPIO46 (BUZZER): controle do log do ROM no boot.
 * A auditoria de 2026-10-04 (secao F, baixos) registra que LED no GPIO45 e
 * buzzer no GPIO46 estao em pinos de strapping SEM analise de margem. */
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
#define USB_DM_PAD           13
#define USB_DP_PAD           14
#define EN_MCU_PAD            3

#define IMU_INT_GPIO         47         /* pad 24 = IO47 (ICM-42688-P INT)   */
#define IMU_CS_GPIO          42         /* pad 35 = IO42 (ICM-42688-P CS_N)  */
#define WD_FEED_GPIO         48         /* pad 25 = IO48 (supervisor externo)*/
#define LED_K_GPIO           45         /* pad 26 = IO45 — strapping VDD_SPI*/
#define BOOT_N_GPIO           0         /* pad 27 = IO0  — strapping de boot*/
#define BUZZER_GPIO          46         /* pad 16 = IO46 — strapping de log */
#define I2C_SDA_GPIO         38         /* pad 31 = IO38 (barometro)        */
#define I2C_SCL_GPIO         39         /* pad 32 = IO39 (barometro)        */
#define UART_TX_GPIO         43         /* pad 37 = GPIO43 = U0TXD          */
#define UART_RX_GPIO         44         /* pad 36 = GPIO44 = U0RXD          */
#define USB_DM_GPIO          19         /* pad 13 = IO19 = USB_D-           */
#define USB_DP_GPIO          20         /* pad 14 = IO20 = USB_D+           */

/* EN_MCU (pad 3) e o pino EN do modulo, NAO um GPIO: a net so liga ao
 * pull-up REN, ao botao SW2 e ao capacitor CEN (gera_pcb_v7.py linhas
 * 415-424; o valor ohmico do REN nao esta especificado no gerador — so o
 * footprint R_0603 — entao nao se afirma numero aqui). O firmware nao
 * controla e nem precisa controlar: EN alto = chip habilitado sempre que
 * ha 3V3. Nao existe define "EN_MCU_GPIO" de proposito. */

/* Nota do IMU (sem driver — baixo da auditoria F): o ICM-42688-P compartilha
 * o barramento SPI dos MCP3208 (MOSI/SCK/MISO acima) sem arbitragem, com
 * CS proprio (GPIO42) e INT no GPIO47. Checklist do datasheet para quem for
 * implementar o M5: WHO_AM_I = reg 0x75 (resposta 0x47), REG_BANK_SEL = 0x76. */

#endif /* BOARD_PINS_H */
