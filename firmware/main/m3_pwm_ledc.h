/* ===========================================================================
 * m3_pwm_ledc.h — modulo M3: PWM dos motores 3 e 4 (periferico LEDC) + defasagem
 *
 * ESQUELETO NAO VERIFICADO. ESTE CABECALHO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado. Ver firmware/README.md e
 * fase4_entrega/FIRMWARE_BUILD.md.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M3.
 * ======================================================================== */

#ifndef M3_PWM_LEDC_H
#define M3_PWM_LEDC_H

#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Configura os 6 canais LEDC dos motores 3 e 4, com a defasagem de 90 °. */
esp_err_t m3_pwm_init(void);

/* Duty em porcentagem nos 6 canais, com o clamp de 2 % a 95 % aplicado. */
esp_err_t m3_pwm_set_duty(uint8_t duty_percent);

/* Leva os 6 canais ao duty minimo. Chamar no boot, antes do resto. */
esp_err_t m3_pwm_shutdown(void);

/* Retorna 0 de proposito: o dead-time dos motores 3 e 4 e fixo no driver
 * IR2104 (400 a 650 ns, RF-14) e nao e programavel pelo firmware. Existe essa
 * funcao para deixar o fato no codigo, e nao so em comentario. */
uint32_t m3_pwm_deadtime_e_fixo(void);

#ifdef __cplusplus
}
#endif

#endif /* M3_PWM_LEDC_H */
