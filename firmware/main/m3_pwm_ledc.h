/* ===========================================================================
 * m3_pwm_ledc.h — modulo M3: PWM dos motores 3 e 4 (periferico LEDC) + defasagem
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F3/F7/F10); AINDA NAO
 * COMPILADO — precisa de idf.py build para validar. Ver firmware/README.md
 * e fase4_entrega/FIRMWARE_BUILD.md.
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

/* Configura os 6 canais LEDC dos motores 3 e 4 (canais 0..5, um por fase —
 * F3). A defasagem por hpoint fica em 10 de 1024 contagens = 3,52 °, NAO nos
 * 90 ° do criterio da §5 (F10). Os canais nascem com duty 0. */
esp_err_t m3_pwm_init(void);

/* Duty em porcentagem nos 6 canais, com o clamp de 2 % a 95 % aplicado.
 * EXCECAO: 0 % e desligamento de verdade (nivel baixo travado), nao clamp 2 %. */
esp_err_t m3_pwm_set_duty(uint8_t duty_percent);

/* Estado seguro real (F7): duty 0 + ledc_stop() com idle_level 0 = nivel baixo
 * travado em todos os 6 canais. Chamar no boot, depois do init. */
esp_err_t m3_pwm_shutdown(void);

/* Estado seguro por GPIO puro (sem LEDC): os 6 pinos como saida em nivel
 * baixo. Chamar ANTES do init e quando o init falhar. */
void m3_pwm_forca_gpio_baixo(void);

/* Retorna 0 de proposito: o dead-time dos motores 3 e 4 e fixo no driver
 * IR2104 (400 a 650 ns, RF-14) e nao e programavel pelo firmware. Existe essa
 * funcao para deixar o fato no codigo, e nao so em comentario. */
uint32_t m3_pwm_deadtime_e_fixo(void);

#ifdef __cplusplus
}
#endif

#endif /* M3_PWM_LEDC_H */
