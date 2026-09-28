/* ===========================================================================
 * m2_pwm_mcpwm.h — modulo M2: PWM dos motores 1 e 2 (periferico MCPWM)
 *
 * ESQUELETO NAO VERIFICADO. ESTE CABECALHO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado. Ver firmware/README.md e
 * fase4_entrega/FIRMWARE_BUILD.md.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M2.
 * ======================================================================== */

#ifndef M2_PWM_MCPWM_H
#define M2_PWM_MCPWM_H

#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Numero de canais do M2: 2 motores x 3 fases. */
#define M2_PWM_CANAIS 6

/* Cria o timer, o motor e o dead-time em hardware. Chamar uma vez. */
esp_err_t m2_pwm_init(void);

/* Duty em porcentagem, ja com o clamp de 2 % a 95 % aplicado. */
esp_err_t m2_pwm_set_duty(uint8_t duty_percent);

/* Atalho para m2_pwm_set_duty, explicito sobre a intencao. */
esp_err_t m2_pwm_set_all(uint8_t duty_percent);

/* Leva os 6 canais ao duty minimo. Chamar no boot, antes do resto. */
esp_err_t m2_pwm_shutdown(void);

#ifdef __cplusplus
}
#endif

#endif /* M2_PWM_MCPWM_H */
