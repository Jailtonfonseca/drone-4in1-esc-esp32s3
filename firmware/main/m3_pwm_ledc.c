/* ===========================================================================
 * m3_pwm_ledc.c — modulo M3: PWM dos motores 3 e 4 (periferico LEDC) + defasagem
 *
 * ESQUELETO NAO VERIFICADO. ESTE ARQUIVO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado, entao nao existe idf.py nem os
 * headers do componente driver (driver/ledc.h) contra os quais conferir este
 * codigo. Existe nesta maquina apenas o compilador C Xtensa, testado com um
 * .c de 5 linhas sem framework (firmware/build_log.txt) — isso nao valida este
 * codigo.
 *
 * AVISO SOBRE A API: as assinaturas de ledc_timer_config e ledc_channel_config
 * foram escritas de memoria da API do ESP-IDF v5 e nao foram conferidas
 * contra nenhum header desta maquina. Podem divergir da versao escolhida.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M3.
 *
 * ----------------------------------------------------------------------------
 * A DIFERENCA CRITICA ENTRE M2 E M3, que o codigo abaixo precisa respeitar
 * ----------------------------------------------------------------------------
 * M2 (motores 1 e 2, MCPWM) tem dead-time PROGRAMAVEL em hardware. O criterio
 * de aceite e uma janela de 250 ns a 2 us.
 *
 * M3 (motores 3 e 4, LEDC) nao tem dead-time programavel: o LEDC nao gera
 * dead-time. O unico dead-time desses 6 sinais e o do IR2104, fixo no driver,
 * especificado em 400 ns min / 520 ns tipico / 650 ns max (RF-14, apurado pelo
 * datasheet do IR2104). Por isso o criterio do M3 tem uma janela PROPRIA,
 * diferente da do M2: 400 a 650 ns, e nao 250 ns a 2 us.
 *
 * Consequencia pratica, e o RF-14 e explicito sobre isso: o firmware nao pode
 * derivar o orcamento de dead-time dos 6 pinos de LEDC do valor do RTL
 * (518,750 ns), porque o piso de 400 ns do driver e 118,75 ns abaixo disso — ou
 * seja, o firmware SOBREESTIMA a protecao no pior caso. Nenhum ajuste de
 * software fecha isso. A mitigacao e medir o dead-time real em bancada e usar
 * o valor medido, e nao o de projeto.
 *
 * Nenhum ajuste de dead-time aparece neste arquivo por esse motivo: nao ha o
 * que ajustar. Ha apenas o duty e a defasagem.
 * ======================================================================== */

#include "m3_pwm_ledc.h"
#include "board_pins.h"

#include "driver/ledc.h"
#include "esp_log.h"
#include "esp_err.h"

/* --- Periodo --------------------------------------------------------------
 * Mesmos 20 kHz do M2, portanto o mesmo periodo de 50 000 ns com tolerancia de
 * 0,1 %. Frequencia de relogio escolhida como 2 MHz: 2 MHz / (50 000 / 1e6) =
 * 40 contagens por periodo, o que da 2 bits de resolucao de duty. E POCO para
 * um criterio de +-0,1 % de periodo, e suficiente para o clamp de 2 % a 95 %.
 * A resolucao de duty que o M2 tem (12 bits) NAO e replicavel aqui sem mudar
 * o relogio; essa e uma diferenca real entre os dois modulos e esta escrita
 * para que ninguem iguale as duas metades por engano. */
#define LEDC_CLK_FREQ_HZ         (2 * 1000 * 1000)
#define LEDC_FREQ_HZ             20000
#define LEDC_RESOLUTION          LEDC_TIMER_10_BIT

/* --- Defasagem ------------------------------------------------------------
 * O criterio do M3 exige defasagem de 90,000 ° +- 1 ° entre as 4 portadoras,
 * medida. Com 40 contagens por periodo, um deslocamento de 10 contagens da
 * exatamente 90 ° — 10/40 = 0,25 de periodo. A fase e programmed no LEDC, nao
 * gerada por software, entao nao ha jitter de ISR introduzido aqui. */
#define LEDC_TICKS_PER_PERIOD    40u
#define LEDC_PHASE_SHIFT_QUARTER 10u   /* 10 de 40 = 90,000 ° exatos         */

/* --- Clamp de duty --------------------------------------------------------
 * 2 % a 95 %, exigido textualmente pelo criterio do M3 na §5. Com 10 bits de
 * resolucao, 2 % = 10 contagens de 1024 e 95 % = 972 contagens. */
#define LEDC_DUTY_MIN_PERCENT    2
#define LEDC_DUTY_MAX_PERCENT    95

/* Canais por motor: 3 fases. Canais no total: 6. */
#define M3_FASES_POR_MOTOR       3
#define M3_CANAIS                6

static const char *TAG_M3 = "m3_pwm";

/* Os 6 canais LEDC: 0-2 = motor 3 (PWM_M301/M302/M303, pads 18, 19, 20),
 * 3-5 = motor 4 (PWM_M401/M402/M403, pads 21, 22 e 8). */
static const int s_gpio[M3_CANAIS] = {
    PWM_M301_GPIO, PWM_M302_GPIO, PWM_M303_GPIO,
    PWM_M401_GPIO, PWM_M402_GPIO, PWM_M403_GPIO,
};

/* Defasagem de 90 ° entre os grupos, na ordem: motor 3 = 0 ticks de defasagem,
 * motor 4 = 10 ticks. */
static const uint32_t s_defasagem_ticks[2] = {
    0u, LEDC_PHASE_SHIFT_QUARTER,
};

static bool s_m3_ready = false;

/* ---------------------------------------------------------------------------
 * m3_pwm_init — cria os canais LEDC dos motores 3 e 4.
 *
 * Nao testado. Nao ha dead-time a configurar aqui, e isso e proposital: ver o
 * bloco de avisos no topo do arquivo.
 * ------------------------------------------------------------------------ */
esp_err_t m3_pwm_init(void)
{
    ESP_LOGI(TAG_M3, "M3: init LEDC %d Hz, defasagem %u ticks (90 ° em %u)",
             LEDC_FREQ_HZ, (unsigned)LEDC_PHASE_SHIFT_QUARTER,
             (unsigned)LEDC_TICKS_PER_PERIOD);

    ledc_timer_config_t timer = {
        .speed_mode      = LEDC_LOW_SPEED_MODE,
        .timer_num       = LEDC_TIMER_0,
        .duty_resolution = LEDC_RESOLUTION,
        .freq_hz         = LEDC_FREQ_HZ,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), "m3_pwm",
                        "falha ao configurar o timer LEDC");

    for (int i = 0; i < M3_CANAIS; i++) {
        const int motor = (i < M3_FASES_POR_MOTOR) ? 0 : 1;

        ledc_channel_config_t ch = {
            .gpio_num   = s_gpio[i],
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel    = (ledc_channel_t)(i % M3_FASES_POR_MOTOR),
            .timer_sel  = LEDC_TIMER_0,
            .duty       = LEDC_DUTY_MIN_PERCENT * ((1 << 10) / 100),
            .hpoint     = (uint32_t)s_defasagem_ticks[motor],
        };
        ESP_RETURN_ON_ERROR(ledc_channel_config(&ch), "m3_pwm",
                            "falha ao configurar um canal do M3");
    }

    s_m3_ready = true;
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m3_pwm_set_duty — duty em porcentagem nos 6 canais, com o clamp 2 % a 95 %.
 *
 * O duty e o mesmo nos 6 canais porque o esqueleto ainda nao tem o M8
 * (comutacao de 6 passos), que e quem daria um duty por fase. Repor os 6
 * canais a um valor so e o comportamento seguro enquanto isso nao existe.
 * ------------------------------------------------------------------------ */
esp_err_t m3_pwm_set_duty(uint8_t duty_percent)
{
    if (!s_m3_ready) {
        return ESP_ERR_INVALID_STATE;
    }
    if (duty_percent < LEDC_DUTY_MIN_PERCENT) {
        duty_percent = LEDC_DUTY_MIN_PERCENT;
    }
    if (duty_percent > LEDC_DUTY_MAX_PERCENT) {
        duty_percent = LEDC_DUTY_MAX_PERCENT;
    }

    const uint32_t top  = (1u << 10) - 1u;   /* LEDC_TIMER_10_BIT */
    const uint32_t duty = (top * (uint32_t)duty_percent) / 100u;

    for (int i = 0; i < M3_CANAIS; i++) {
        ESP_RETURN_ON_ERROR(
            ledc_set_duty(LEDC_LOW_SPEED_MODE,
                          (ledc_channel_t)(i % M3_FASES_POR_MOTOR),
                          duty),
            "m3_pwm", "falha ao escrever o duty");
    }
    ESP_RETURN_ON_ERROR(ledc_update_duty(LEDC_LOW_SPEED_MODE), "m3_pwm",
                        "falha ao aplicar o duty");

    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m3_pwm_shutdown — leva os 6 canais ao duty minimo. Chamar no boot.
 * ------------------------------------------------------------------------ */
esp_err_t m3_pwm_shutdown(void)
{
    return m3_pwm_set_duty(LEDC_DUTY_MIN_PERCENT);
}

/* ---------------------------------------------------------------------------
 * m3_pwm_deadtime_e_fixo — lembrete em forma de funcao.
 *
 * Existe para deixar o fato gravado no codigo e nao so no comentario: o
 * dead-time dos motores 3 e 4 e do IR2104 (400 ns min, 520 ns tipico, 650 ns
 * max, RF-14), e nao do firmware. Se alguem precisar de um numero de
 * dead-time programavel nesses 6 canais, a resposta e que o caminho e outro:
 * migrar esses motores para MCPWM, que tem dead-time em hardware. A §5 registra
 * essa migracao como a mitigacao (c) do RF-14.
 * ------------------------------------------------------------------------ */
uint32_t m3_pwm_deadtime_e_fixo(void)
{
    return 0u;   /* o firmware nao programa dead-time nenhum aqui */
}
