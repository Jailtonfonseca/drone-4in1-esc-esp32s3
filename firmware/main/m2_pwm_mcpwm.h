/* ===========================================================================
 * m2_pwm_mcpwm.h — modulo M2: PWM dos motores 1 e 2 (periferico MCPWM)
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F1/F2/F7/F8); AINDA NAO
 * COMPILADO — precisa de idf.py build para validar. Ver firmware/README.md
 * e fase4_entrega/FIRMWARE_BUILD.md.
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

/* Cria 2 timers de 20 kHz, 3 operadores, 6 comparadores e 6 geradores no
 * grupo 0 do MCPWM — 3 operadores e o maximo do ESP32-S3. As saidas ficam
 * presas em NIVEL BAIXO (force level 0 em hold) ate a primeira chamada de
 * m2_pwm_set_duty() com duty > 0. Chamar uma vez. */
esp_err_t m2_pwm_init(void);

/* Duty em porcentagem nos 6 canais, com clamp de 2 % a 95 % aplicado.
 * EXCECAO: 0 % significa desligado de verdade (nivel baixo forçado) e
 * equivale a m2_pwm_shutdown() — nao e clampado para 2 %. */
esp_err_t m2_pwm_set_duty(uint8_t duty_percent);

/* Atalho para m2_pwm_set_duty, explicito sobre a intencao. */
esp_err_t m2_pwm_set_all(uint8_t duty_percent);

/* Estado seguro real (F7): comparadores em 0 + force level 0 em hold =
 * nivel baixo garantido mesmo com os timers rodando. Chamar no boot, depois
 * do init, e em qualquer falha que exija cortar as gates. */
esp_err_t m2_pwm_shutdown(void);

/* Estado seguro por GPIO puro (sem MCPWM): os 6 pinos como saida em nivel
 * baixo. Chamar ANTES do init e quando o init falhar — ver a nota eletrica
 * no corpo da funcao. NAO usar apos init bem-sucedido (use shutdown()). */
void m2_pwm_forca_gpio_baixo(void);

#ifdef __cplusplus
}
#endif

#endif /* M2_PWM_MCPWM_H */
