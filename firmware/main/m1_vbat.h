/* ===========================================================================
 * m1_vbat.h — modulo M1: leitura de VBAT pelo divisor resistivo
 *
 * ESQUELETO NAO VERIFICADO. ESTE CABECALHO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado. Ver firmware/README.md e
 * fase4_entrega/FIRMWARE_BUILD.md.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M1.
 * ======================================================================== */

#ifndef M1_VBAT_H
#define M1_VBAT_H

#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Configura ADC1 e a calibracao. Chamar uma vez, antes do loop. */
esp_err_t m1_vbat_init(void);

/* Le VBAT e devolve a tensao da bateria em volts (nao a tensao no pino).
 * Devolve false se o modulo nao foi inicializado ou se a leitura falhou. */
bool m1_vbat_read_volts(float *out_volts);

/* Imprime uma leitura no log. */
void m1_vbat_log(void);

#ifdef __cplusplus
}
#endif

#endif /* M1_VBAT_H */
