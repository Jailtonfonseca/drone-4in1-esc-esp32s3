/* ===========================================================================
 * m3_pwm_ledc.c — modulo M3: PWM dos motores 3 e 4 (periferico LEDC) + defasagem
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F3/F7/F10 e baixos); AINDA
 * NAO COMPILADO — precisa de idf.py build para validar. O ESP-IDF nao esta
 * instalado nesta maquina; existe apenas o compilador C Xtensa testado com um
 * .c de 5 linhas sem framework (firmware/build_log.txt) — isso nao valida este
 * codigo.
 *
 * AVISO SOBRE A API: as assinaturas LEDC abaixo foram conferidas contra o
 * header real do ESP-IDF v5.4 (components/esp_driver_ledc/include/driver/
 * ledc.h) e contra o corpo do driver (esp_driver_ledc/src/ledc.c):
 *   - ledc_update_duty() leva speed_mode E channel (o codigo antigo passava
 *     so o primeiro — F1);
 *   - ledc_stop() e `esp_err_t ledc_stop(ledc_mode_t, ledc_channel_t,
 *     uint32_t idle_level)` — o idle_level e uint32_t e 0 = nivel baixo; o
 *     "LEDC_OUTPUT_IDLE_MODE_LOW" citado no briefing nao existe no header;
 *   - ledc_update_duty() re-habilita a saida do canal, entao o PWM volta a
 *     existir depois de um shutdown via set_duty() nao-nulo.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M3.
 *
 * ----------------------------------------------------------------------------
 * A DIFERENCA ENTRE M2 E M3, DEPOIS DA AUDITORIA (achado F8)
 * ----------------------------------------------------------------------------
 * O bloco antigo deste arquivo dizia que "M2 tem dead-time programavel em
 * hardware e M3 nao". Isso era erro de concepcao: o dead-time do MCPWM nao se
 * aplica a topologia nenhuma das duas metades, porque cada IR2104 tem UM
 * unico pino IN e gera HO/LO complementares com dead-time INTERNO fixo
 * (400 ns min / 520 ns tip / 650 ns max, RF-14, datasheet IR2104 do repo).
 * Sao 12 sinais single-ended; nao existe par complementar no MCU em lugar
 * nenhum. O M2 nao configura mais dead-time nenhum, e aqui nunca houve.
 *
 * O que SOBRA de verdadeiro no paragrafo antigo: o RF-14 esta certo em que o
 * firmware nao pode derivar orcamento de dead-time do valor do RTL
 * (518,750 ns) — mas quem determina o dead-time dos QUATRO motores e o
 * IR2104, e nao o firmware de nenhum deles. Nao ha o que ajustar aqui; ha
 * apenas o duty e a defasagem.
 * ======================================================================== */

#include "m3_pwm_ledc.h"
#include "board_pins.h"

#include "driver/ledc.h"
#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_err.h"

/* --- Periodo --------------------------------------------------------------
 * Mesmos 20 kHz do M2, portanto o mesmo periodo de 50 000 ns com tolerancia de
 * 0,1 % (criterio da §5). Resolucao de duty: LEDC_TIMER_10_BIT = 1024
 * contagens por periodo. O comentario antigo falava "clock de 2 MHz, 40
 * contagens, 2 bits" — a constante de 2 MHz era definida e NUNCA usada, e o
 * calculo dos 2 bits contrariava o proprio LEDC_TIMER_10_BIT do codigo
 * (baixos da auditoria). Com LEDC_AUTO_CLK o driver escolhe o clock e o
 * divisor; a frequencia REAL e logada no init via ledc_get_freq(), e o
 * osciloscopio e que atesta os ±0,1 % (passo 9 do plano de bancada). */
#define LEDC_FREQ_HZ             20000
#define LEDC_RESOLUTION          LEDC_TIMER_10_BIT
#define LEDC_PERIOD_COUNTS       (1u << 10)   /* 1024 contagens por periodo */

/* --- Defasagem ------------------------------------------------------------
 * O comentario antigo prometia "10 de 40 = 90,000 ° exatos". NAO E: com 10
 * bits o periodo tem 1024 contagens, e hpoint = 10 desloca o pulso em 10/1024
 * do periodo = 3,52 ° (achado F10). O criterio da §5 (defasagem de 90,000 °
 * ± 1 ° entre as 4 portadoras, medida) NAO e cumprido por este valor.
 *
 * Nao "corrigimos" para 256 (= 90 °) de graca: com hpoint = 256 e duty de ate
 * 95 % (973 contagens) o pulso atravessaria o fim do periodo e seria
 * truncado, mudando o duty efetivo; e alem disso so existem 2 grupos de
 * portadora aqui (motor 3 e motor 4) — o criterio pede 4 (as outras duas
 * estao no M2). O numero final tem que sair do osciloscopio, nao do teclado.
 *
 * A fase e programada no LEDC via hpoint, nao gerada por software, entao nao
 * ha jitter de ISR introduzido aqui. */
#define LEDC_PHASE_SHIFT_TENTATIVO 10u   /* 10 de 1024 = 3,52 ° (F10) */

/* --- Clamp de duty --------------------------------------------------------
 * 2 % a 95 %, exigido textualmente pelo criterio do M3 na §5. Com 10 bits,
 * 2 % = 20 contagens de 1024 e 95 % = 972 contagens.
 * EXCECAO (F7, mesma regra do M2): 0 % e desligamento de verdade (shutdown),
 * nao clampado para 2 %. */
#define LEDC_DUTY_MIN_PERCENT    2
#define LEDC_DUTY_MAX_PERCENT    95

/* Canais por motor: 3 fases. Canais no total: 6 — um canal LEDC DISTINTO por
 * fase. O codigo antigo fazia `channel = i % 3` (achado F3): rebindava os
 * canais 0-2 no motor 4, deixava o motor 3 sem PWM independente e o ledc_set_pin
 * antigo nao desligava o roteamento previo. O S3 tem 8 canais LEDC
 * (soc_caps.h: SOC_LEDC_CHANNEL_NUM = 8); usamos 6. */
#define M3_FASES_POR_MOTOR       3
#define M3_CANAIS                6

static const char *TAG_M3 = "m3_pwm";

/* Os 6 canais LEDC: 0-2 = motor 3 (PWM_M301/M302/M303, pads 18, 19, 20),
 * 3-5 = motor 4 (PWM_M401/M402/M403, pads 21, 22 e 8). GPIOs conferidos
 * contra o datasheet do WROOM-1 pela auditoria (ver board_pins.h): motor 3 =
 * GPIO 10,11,12; motor 4 = GPIO 13,14,15 — igual a Fase 0 §8. */
static const int s_gpio[M3_CANAIS] = {
    PWM_M301_GPIO, PWM_M302_GPIO, PWM_M303_GPIO,
    PWM_M401_GPIO, PWM_M402_GPIO, PWM_M403_GPIO,
};

/* Defasagem de hpoint por grupo: motor 3 = 0 contagens, motor 4 = 10
 * contagens (3,52 ° — ver o bloco acima). */
static const uint32_t s_defasagem_ticks[2] = {
    0u, LEDC_PHASE_SHIFT_TENTATIVO,
};

static bool s_m3_ready = false;

/* ---------------------------------------------------------------------------
 * m3_pwm_init — cria os 6 canais LEDC dos motores 3 e 4.
 *
 * Nao testado. Nao ha dead-time a configurar aqui, e isso e proposital: ver o
 * bloco de avisos no topo do arquivo. Os canais nascem com duty 0 (saida em
 * nivel baixo) e o app_main chama m3_pwm_shutdown() em seguida; PWM so existe
 * quando um set_duty() nao-nulo chega.
 * ------------------------------------------------------------------------ */
esp_err_t m3_pwm_init(void)
{
    ESP_LOGI(TAG_M3, "M3: init LEDC %d Hz, 10 bits, hpoint motor 4 = %u de %u",
             LEDC_FREQ_HZ, (unsigned)LEDC_PHASE_SHIFT_TENTATIVO,
             (unsigned)LEDC_PERIOD_COUNTS);

    ledc_timer_config_t timer = {
        .speed_mode      = LEDC_LOW_SPEED_MODE,
        .timer_num       = LEDC_TIMER_0,
        .duty_resolution = LEDC_RESOLUTION,
        .freq_hz         = LEDC_FREQ_HZ,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), "m3_pwm",
                        "falha ao configurar o timer LEDC");

    /* Autoverificacao honesta: loga a frequencia que o driver diz ter
     * conseguido. O criterio ±0,1 % e medido no osciloscopio, nao aqui. */
    const uint32_t freq_real = ledc_get_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0);
    ESP_LOGI(TAG_M3, "M3: frequencia real do timer LEDC: %u Hz",
             (unsigned)freq_real);

    for (int i = 0; i < M3_CANAIS; i++) {
        const int motor = (i < M3_FASES_POR_MOTOR) ? 0 : 1;

        ledc_channel_config_t ch = {
            .gpio_num   = s_gpio[i],
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel    = (ledc_channel_t)i,    /* F3: canal = i, 0..5 */
            .intr_type  = LEDC_INTR_DISABLE,
            .timer_sel  = LEDC_TIMER_0,
            .duty       = 0,                    /* nasce desligado */
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
 * EXCECAO (F7): 0 % e desligamento de verdade (shutdown), nao clamp 2 %.
 * ------------------------------------------------------------------------ */
esp_err_t m3_pwm_set_duty(uint8_t duty_percent)
{
    if (!s_m3_ready) {
        return ESP_ERR_INVALID_STATE;
    }
    if (duty_percent == 0u) {
        return m3_pwm_shutdown();   /* 0 = nivel baixo, nao 2 % (F7) */
    }
    if (duty_percent < LEDC_DUTY_MIN_PERCENT) {
        duty_percent = LEDC_DUTY_MIN_PERCENT;
    }
    if (duty_percent > LEDC_DUTY_MAX_PERCENT) {
        duty_percent = LEDC_DUTY_MAX_PERCENT;
    }

    const uint32_t duty =
        ((uint32_t)duty_percent * LEDC_PERIOD_COUNTS) / 100u;

    for (int i = 0; i < M3_CANAIS; i++) {
        ESP_RETURN_ON_ERROR(
            ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, duty),
            "m3_pwm", "falha ao escrever o duty de um canal");
        /* ledc_update_duty tem DOIS argumentos (speed_mode, channel) e cada
         * canal precisa da sua chamada (F1). Esta chamada tambem re-habilita
         * a saida do canal, cobrindo o caso de o canal estar parado por um
         * ledc_stop() do shutdown (comportamento conferido no ledc.c do
         * v5.4: _ledc_update_duty() seta sig_out_en e duty_start). */
        ESP_RETURN_ON_ERROR(
            ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i),
            "m3_pwm", "falha ao aplicar o duty de um canal");
    }

    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m3_pwm_shutdown — estado seguro REAL (achado F7): duty 0 E ledc_stop() com
 * idle_level = 0.
 *
 * So o duty 0 nao basta para "nivel baixo": ledc_stop() desabilita a saida do
 * canal e trava o pino no nivel de repouso (uint32_t idle_level; 0 = baixo).
 * O PWM so volta quando um ledc_set_duty()+ledc_update_duty() futuro
 * re-habilitar o canal — que e o que m3_pwm_set_duty() faz.
 * ------------------------------------------------------------------------ */
esp_err_t m3_pwm_shutdown(void)
{
    if (!s_m3_ready) {
        return ESP_ERR_INVALID_STATE;
    }
    for (int i = 0; i < M3_CANAIS; i++) {
        ESP_RETURN_ON_ERROR(
            ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, 0),
            "m3_pwm", "falha ao zerar o duty no shutdown");
        ESP_RETURN_ON_ERROR(
            ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i),
            "m3_pwm", "falha ao aplicar o duty zero no shutdown");
        ESP_RETURN_ON_ERROR(
            ledc_stop(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, 0),
            "m3_pwm", "falha ao travar o canal em nivel baixo");
    }
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m3_pwm_forca_gpio_baixo — estado seguro por GPIO PURO, sem LEDC.
 *
 * Mesma razao do m2_pwm_forca_gpio_baixo(): os pinos IN dos IR2104 nao tem
 * pull na placa (netlist v7), e IN baixo com SD alto (pull-up de 10k, F12)
 * deixa high-side cortado e low-side fechado — sem shoot-through, sem giro.
 * Usar ANTES de m3_pwm_init() (primeira coisa do boot) e quando o init
 * falhar. Apos init bem-sucedido o caminho e m3_pwm_shutdown().
 * ------------------------------------------------------------------------ */
void m3_pwm_forca_gpio_baixo(void)
{
    for (int i = 0; i < M3_CANAIS; i++) {
        const gpio_num_t gpio = (gpio_num_t)s_gpio[i];
        const gpio_config_t cfg = {
            .pin_bit_mask = (uint64_t)1ULL << (int)gpio,
            .mode         = GPIO_MODE_OUTPUT,
            .pull_up_en   = GPIO_PULLUP_DISABLE,
            .pull_down_en = GPIO_PULLDOWN_DISABLE,
            .intr_type    = GPIO_INTR_DISABLE,
        };
        if (gpio_config(&cfg) != ESP_OK || gpio_set_level(gpio, 0) != ESP_OK) {
            ESP_LOGE(TAG_M3, "M3: GPIO %d nao pode ser forcado a nivel baixo",
                     (int)gpio);
        }
    }
}

/* ---------------------------------------------------------------------------
 * m3_pwm_deadtime_e_fixo — lembrete em forma de funcao.
 *
 * Existe para deixar o fato gravado no codigo e nao so no comentario: o
 * dead-time dos motores 3 e 4 e do IR2104 (400 ns min, 520 ns tipico, 650 ns
 * max, RF-14), e nao do firmware. ATENCAO APOS F8: a mitigacao antiga da §5
 * ("migrar para MCPWM, que tem dead-time programavel") NAO compra dead-time
 * nenhum nesta topologia — cada IR2104 tem UM pino IN e o MCPWM nao tem par
 * complementar de geradores para atrasar aqui. Se um dia a protecao de
 * sobreposicao tiver que ser programavel, a mudanca e na PLACA (driver com
 * entradas H/L separadas), nao no firmware.
 * ------------------------------------------------------------------------ */
uint32_t m3_pwm_deadtime_e_fixo(void)
{
    return 0u;   /* o firmware nao programa dead-time nenhum aqui */
}
