/* ===========================================================================
 * m4_adc_spi.h — modulo M4: leitura dos 4x MCP3208 por SPI
 *
 * ESQUELETO NAO VERIFICADO. ESTE CABECALHO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado. Ver firmware/README.md e
 * fase4_entrega/FIRMWARE_BUILD.md.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M4.
 * ======================================================================== */

#ifndef M4_ADC_SPI_H
#define M4_ADC_SPI_H

#include <stdint.h>
#include "esp_err.h"
#include "driver/spi_master.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Quantidade de MCP3208 no layout v7: 4 CIs, com CS separados
 * (ADC_CS1..ADC_CS4, pads 23, 15, 33 e 34). A RF-07 acusa a Fase 0 de ter
 * previsto 1 CS + IRQ/DRDY para o ADC, o que nao corresponde ao layout. */
#define M4_N_ADCS 4

/* Barramento SPI, host 2. O host 1 ou 3 seria igualmente valido; a escolha
 * aqui e arbitraria e precisa bater com o que o M5 (IMU) e o M6 (barometro)
 * usarem, e essa reserva de canal nao foi feita. */
#define M4_SPI_HOST SPI2_HOST

/* Configura o barramento e anexa os 4 CIs. */
esp_err_t m4_adc_init(void);

/* Uma conversao de um canal de um CI. `channel` vai de 0 a 7. */
esp_err_t m4_adc_read_raw(uint8_t adc_index, uint8_t channel, uint16_t *out_raw);

/* Round-robin: uma leitura por chamada, um CI e um canal por vez. `state`, se
 * nao for NULL, recebe [circuito, canal, raw LSB, raw MSB]. */
esp_err_t m4_adc_poll(uint8_t *state);

/* Conversoes de um LSB para as unidades fisicas. Sao conversoes, nao
 * calibracao: ver o aviso no fim de m4_adc_spi.c. */
float m4_raw_to_ampere(uint16_t raw);
float m4_raw_to_bemf(uint16_t raw);

/* Le o canal de corrente com zero A corrente e devolve o offset em LSB, para
 * ser anotado e subtraido, como o criterio de aceite do M4 exige. */
esp_err_t m4_adc_log_offset_zero(uint8_t adc_index, uint8_t channel,
                                 uint16_t *out_offset_raw);

#ifdef __cplusplus
}
#endif

#endif /* M4_ADC_SPI_H */
