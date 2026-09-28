/* ===========================================================================
 * m2_pwm_mcpwm.c — modulo M2: PWM dos motores 1 e 2 (periferico MCPWM)
 *
 * ESQUELETO NAO VERIFICADO. ESTE ARQUIVO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado, entao nao existe idf.py nem os
 * headers do componente driver (mcpwm_prelude.h, mcpwm_timer.h, mcpwm_motor.h)
 * contra os quais conferir este codigo. Existe nesta maquina apenas o
 * compilador C Xtensa, testado com um .c de 5 linhas sem framework
 * (firmware/build_log.txt) — isso nao valida este codigo.
 *
 * AVISO SOBRE A API: os nomes das structs e das funcoes do driver MCPWM
 * abaixo foram escritos de memoria da API do ESP-IDF v5. Nao ha, nesta
 * maquina, um unico header do ESP-IDF para conferir assinatura, e nenhuma das
 * funcoes abaixo foi linkada. A assinatura pode divergir da versao do ESP-IDF
 * que o Jailton escolher. Ajustar aqui e o primeiro trabalho de quem pegar
 * este arquivo, e e a razao pela qual ele e declarado esqueleto e nao codigo
 * pronto para gravar.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M2.
 *
 * Criterio de aceite da §5 para o M2, que NENHUM dos numeros abaixo cumpre:
 *   osciloscopio em 2 canais, periodo 50 000 ns +- 0,1 %; dead-time entre
 *   250 ns e 2 us; sobreposicao dos dois gates = 0 (PLANO_TESTE_BANCADA.md
 *   passo 9).
 * ======================================================================== */

#include "m2_pwm_mcpwm.h"
#include "board_pins.h"

#include "driver/mcpwm_prelude.h"
#include "driver/mcpwm_timer.h"
#include "driver/mcpwm_motor.h"
#include "esp_log.h"
#include "esp_err.h"

/* --- Periodo e resolucao --------------------------------------------------
 * 20 kHz vem do RTL validado na fase 2
 * (fase2_simulacao/verilog/RELATORIO_VERILOG.md §4.3): 20 kHz = periodo de
 * 50 000 ns, e a §5 exige 50 000 ns +- 0,1 %. O periodo, em ticks, sai de
 * resolution_hz / freq; com 4096 e 20 000 Hz isso da 204,8 ticks por periodo,
 * ou seja 20,48 kHz — 2,4 % acima do alvo, acima da tolerancia de 0,1 %.
 * Por isso o codigo abaixo fixa clk_src e resolution_hz em vez de usar o
 * exemplo de 50 Hz, e o valor final de periodo precisa ser conferido no
 * osciloscopio antes de qualquer motor girar. */
#define PWM_FREQ_HZ            20000
#define PWM_RESOLUTION_BITS    12

/* --- Dead-time ------------------------------------------------------------
 * Janela do criterio do M2: 250 ns a 2 us, com sobreposicao dos dois gates
 * igual a zero. O valor abaixo e um PLACEBO dentro da faixa, nao um valor
 * justificado: nao ha medicao de bancada que escolha entre 250 ns e 2 us, e o
 * RF-10 do plano avisa que o atraso real do driver e desconhecido e pode somar
 * a isso. O que for medido no osciloscopio precisa substituir este numero. */
#define PWM_DEADTIME_TICKS     0x00C0   /* 192 counts; a escala depende do clock do timer */

/* --- Clamp de duty --------------------------------------------------------
 * O M3 tem clamp explicito de 2 % a 95 % (criterio da §5). O M2 nao declara
 * clamp na §5, mas o mesmo clamp e aplicado aqui de proposito: o RF-08 do
 * plano avisa que um duty de repouso mal aplicado pode fechar caminho de
 * fase, e limitar o duty e a defesa mais barata contra isso. */
#define PWM_DUTY_MIN_PERCENT   2
#define PWM_DUTY_MAX_PERCENT   95

static const char *TAG_M2 = "m2_pwm";

static mcpwm_timer_handle_t s_timer     = NULL;
static mcpwm_motor_handle_t s_motor     = NULL;
static mcpwm_oper_handle_t  s_comparador = NULL;   /* handle do comparador do grupo */
static bool                 s_m2_ready  = false;

/* ---------------------------------------------------------------------------
 * m2_pwm_on_timer_zero — ISR de fim de periodo.
 *
 * E aqui que a defasagem e o controle de velocidade entrariam no M2. Neste
 * esqueleto ela nao faz nada de proposito: sem taxa de passo definida e sem
 * medicao de bancada, escrever uma rampa aqui seria inventar numero.
 * ------------------------------------------------------------------------ */
static bool m2_pwm_on_timer_zero(mcpwm_timer_handle_t timer)
{
    (void)timer;
    return true;   /* true = nao reinicia o timer; a ESP-IDF documente o uso */
}

/* ---------------------------------------------------------------------------
 * m2_pwm_init — cria o timer MCPWM e um motor com 6 saidas (2 motores x 3
 * fases), com dead-time em hardware.
 *
 * Nao testado. Os GPIOs chegam como -1 de board_pins.h ate o mapa pad -> GPIO
 * ser conferido contra o datasheet do modulo; com -1 a propria ESP-IDF falha
 * na criacao do operador, que e o comportamento desejado.
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_init(void)
{
    ESP_LOGI(TAG_M2, "M2: init MCPWM %d Hz, %d bits, dead-time %d ticks",
             PWM_FREQ_HZ, PWM_RESOLUTION_BITS, PWM_DEADTIME_TICKS);

    mcpwm_timer_config_t timer_config = {
        .group_id      = 0,
        .clk_src       = MCPWM_TIMER_CLK_SRC_DEFAULT,
        .resolution_hz = (uint32_t)(1 << PWM_RESOLUTION_BITS),
        .count_mode    = MCPWM_TIMER_COUNT_MODE_UP,
        .period_ticks  = ((1u << PWM_RESOLUTION_BITS) - 1u),
    };
    ESP_RETURN_ON_ERROR(mcpwm_new_timer(&timer_config, &s_timer),
                        "m2_pwm", "falha ao criar o timer MCPWM");

    mcpwm_motor_handle_t motor;
    mcpwm_motor_config_t motor_config = {
        .group_id       = 0,
        .clk_src        = MCPWM_TIMER_CLK_SRC_DEFAULT,
        .intr_priority  = 0,
        .flags.use_dual_motor = true,
    };
    ESP_RETURN_ON_ERROR(mcpwm_new_motor(s_timer, &motor_config, &motor),
                        "m2_pwm", "falha ao criar o motor MCPWM");

    /* Motor 1: PWM_M101/M102/M103 (pads 4, 5, 6 do modulo). */
    const mcpwm_oper_config_t ops[] = {
        { .group_id = 0, .gen_gpio_num = PWM_M101_GPIO },
        { .group_id = 0, .gen_gpio_num = PWM_M102_GPIO },
        { .group_id = 0, .gen_gpio_num = PWM_M103_GPIO },
        { .group_id = 0, .gen_gpio_num = PWM_M201_GPIO },
        { .group_id = 0, .gen_gpio_num = PWM_M202_GPIO },
        { .group_id = 0, .gen_gpio_num = PWM_M203_GPIO },
    };
    for (int i = 0; i < M2_PWM_CANAIS; i++) {
        ESP_RETURN_ON_ERROR(mcpwm_new_operator(ops[i].group_id, motor, &ops[i]),
                            "m2_pwm", "falha ao criar um operador do M2");
    }

    mcpwm_cmpr_handle_t comparador = NULL;
    mcpwm_cmpr_config_t cmpr_config = { .flags.update_cmp_on_tez = true };
    ESP_RETURN_ON_ERROR(mcpwm_new_comparator(s_timer, &cmpr_config, &comparador),
                        "m2_pwm", "falha ao criar o comparador");
    s_comparador = comparador;

    mcpwm_deadtime_handle_t deadtime = NULL;
    mcpwm_deadtime_config_t dt_config = {
        .flags.update_deadtime_on_tez = true,
        .clk_src = MCPWM_TIMER_CLK_SRC_DEFAULT,
        .ticks   = PWM_DEADTIME_TICKS,
    };
    ESP_RETURN_ON_ERROR(mcpwm_new_deadtime(s_timer, &dt_config, &deadtime),
                        "m2_pwm", "falha ao criar o dead-time");

    ESP_RETURN_ON_ERROR(
        mcpwm_motor_register_event(motor, MCPWM_EVENT_TIMER_ZERO,
                                   m2_pwm_on_timer_zero, NULL),
        "m2_pwm", "falha ao registrar o evento TIMER_ZERO");

    ESP_ERROR_CHECK(mcpwm_timer_start_stop(s_timer, MCPWM_TIMER_START_NO_STOP));

    s_motor    = motor;
    s_m2_ready = true;
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m2_pwm_set_duty — escreve o duty de um dos 6 canais, em porcentagem.
 *
 * O clamp de 2 % a 95 % e aplicado aqui e nao no chamador, para que nenhum
 * caminho futuro escape dele por esquecimento.
 *
 * Os 6 canais compartilham UM unico comparador neste esqueleto, entao esta
 * funcao nao aceita indice de canal: ela escreve o mesmo duty nos 6. Um duty
 * independente por canal exige um segundo grupo MCPWM ou um segundo timer, e
 * essa decisao de arquitetura nao foi tomada — ela depende de quantos timers
 * o ESP32-S3 da a este padrao, o que so se confirma lendo o TRM (que nao esta
 * no disco).
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_set_duty(uint8_t duty_percent)
{
    if (!s_m2_ready) {
        return ESP_ERR_INVALID_STATE;
    }
    if (duty_percent < PWM_DUTY_MIN_PERCENT) {
        duty_percent = PWM_DUTY_MIN_PERCENT;
    }
    if (duty_percent > PWM_DUTY_MAX_PERCENT) {
        duty_percent = PWM_DUTY_MAX_PERCENT;
    }

    const uint32_t top     = (1u << PWM_RESOLUTION_BITS) - 1u;
    const uint32_t compare = (top * (uint32_t)duty_percent) / 100u;

    return mcpwm_timer_set_compare(s_timer, s_comparador, compare);
}

/* ---------------------------------------------------------------------------
 * m2_pwm_set_all — aplica um duty aos 6 canais de uma vez.
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_set_all(uint8_t duty_percent)
{
    return m2_pwm_set_duty(duty_percent);
}

/* ---------------------------------------------------------------------------
 * m2_pwm_shutdown — leva os 6 canais ao clamp minimo. Chamar no boot, antes de
 * qualquer outra coisa: enquanto o firmware nao assumiu o controle, os 6 sinais
 * do driver precisam estar em nivel baixo.
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_shutdown(void)
{
    return m2_pwm_set_all(PWM_DUTY_MIN_PERCENT);
}
