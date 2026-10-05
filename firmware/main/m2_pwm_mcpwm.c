/* ===========================================================================
 * m2_pwm_mcpwm.c — modulo M2: PWM dos motores 1 e 2 (periferico MCPWM)
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F1/F2/F7/F8 e baixos);
 * AINDA NAO COMPILADO — precisa de idf.py build para validar. O ESP-IDF nao
 * esta instalado nesta maquina (firmware/build_log.txt e honesto sobre o
 * que ele compila), entao nada abaixo passou por compilador nesta maquina.
 *
 * AVISO SOBRE A API: TODAS as chamadas abaixo foram conferidas, uma a uma,
 * contra os headers reais do ESP-IDF v5.4 em components/esp_driver_mcpwm/
 * include/driver/ (mcpwm_prelude.h e os mcpwm_timer.h/mcpwm_oper.h/
 * mcpwm_cmpr.h/mcpwm_gen.h que ele inclui) e em hal/mcpwm_types.h:
 *   - NAO EXISTEM mcpwm_motor.h, mcpwm_motor_handle_t, mcpwm_new_motor,
 *     mcpwm_timer_set_compare, mcpwm_new_deadtime (o dead-time e
 *     mcpwm_generator_set_dead_time, que este modulo nao usa — ver F8);
 *   - mcpwm_new_timer/mcpwm_new_operator/mcpwm_new_comparator/
 *     mcpwm_new_generator tem 2-3 argumentos conforme abaixo;
 *   - gen_gpio_num mora em mcpwm_generator_config_t (nao na do operador);
 *   - ESP_RETURN_ON_ERROR exige esp_check.h (baixo da auditoria).
 *
 * RECURSO DO ESP32-S3 (achado F1): cada grupo MCPWM tem 3 timers, 3
 * operadores e 2 geradores por operador (soc_caps.h: SOC_MCPWM_GROUPS=2,
 * SOC_MCPWM_TIMERS_PER_GROUP=3, SOC_MCPWM_OPERATORS_PER_GROUP=3,
 * SOC_MCPWM_GENERATORS_PER_OPERATOR=2). O design antigo pedia 6 operadores
 * no grupo 0 — estourava o recurso. Layout atual: 2 timers × 3 operadores
 * × 2 geradores = 6 saidas (motores 1 e 2), tudo no grupo 0; motores 3 e 4
 * continuam no M3/LEDC.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M2.
 *
 * Criterio de aceite da §5 para o M2: osciloscopio em 2 canais, periodo
 * 50 000 ns +- 0,1 %; sobreposicao dos dois gates = 0 (PLANO_TESTE_
 * BANCADA.md passo 9). A janela de dead-time de 250 ns a 2 us da §5 cai
 * desta lista: ver o bloco "DEAD-TIME" abaixo (achado F8).
 * ======================================================================== */

#include "m2_pwm_mcpwm.h"
#include "board_pins.h"

#include "driver/mcpwm_prelude.h"   /* meta-header v5.4: inclui mcpwm_timer.h,
                                      * mcpwm_oper.h, mcpwm_cmpr.h, mcpwm_gen.h
                                      * (mais fault/sync/cap/etm)            */
#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_err.h"

/* --- Periodo e resolucao (achado F2) --------------------------------------
 * 20 kHz = periodo de 50 000 ns (fase2_simulacao/verilog/RELATORIO_VERILOG.md
 * §4.3), tolerancia ±0,1 %. Com resolution_hz = 4096 e period_ticks = 4095
 * (o codigo antigo) a frequencia real era de ~1 Hz — fator 20 000× abaixo do
 * alvo, e o driver so emite um warning.
 * Correto no ESP32-S3: o clock fonte padrao do timer MCPWM e
 * MCPWM_TIMER_CLK_SRC_DEFAULT = PLL_F160M, 160 MHz (soc/esp32s3/
 * clk_tree_defs.h). resolution_hz = 80 MHz da prescale exato de 2, e
 *   80 MHz / 4000 ticks = 20 000 Hz EXATOS (tick de 12,5 ns).
 * 4000 degraus de duty (~0,025 % por degrau) bastam com folga para o clamp
 * de 2-95 % do §5. */
#define PWM_FREQ_HZ            20000
#define PWM_RESOLUTION_HZ      (80 * 1000 * 1000)  /* 80 MHz; prescale 160/2 */
#define PWM_PERIOD_TICKS        4000                /* 80 MHz / 20 kHz exatos */

/* --- DEAD-TIME: REMOVIDO DE PROPOSITO (achado F8) ---------------------------
 * O dead-time programavel do MCPWM NAO se aplica a esta topologia. Cada um
 * dos 12 IR2104 tem UM unico pino IN e gera HO/LO complementares com
 * dead-time INTERNO fixo (400 ns min / 520 ns tip / 650 ns max, datasheet
 * IR2104 do repo — apurado pela RF-14 e re-conferido pela auditoria). Ou
 * seja, neste firmware:
 *   - nao existe par complementar de geradores: os 2 geradores de cada
 *     operador carregam FASES DE MOTORES DIFERENTES (ver tabela s_canal), e
 *     nao um par high/low da mesma ponte;
 *   - atrasar bordas de um sinal single-ended (e so isso que
 *     mcpwm_generator_set_dead_time faria aqui) nao compra protecao: quem
 *     garante sobreposicao de gates = 0 e o IR2104, em hardware.
 * "M2 = MCPWM por causa do dead-time programavel" (§5/RF-14) era erro de
 * concepcao — M2 e M3 sao funcionalmente identicos nesta topologia. O
 * codigo antigo ainda carregava PWM_DEADTIME_TICKS = 192 "na escala que
 * der": a 80 MHz isso seria 2,4 us, ACIMA do teto de 2 us do criterio; na
 * resolucao antiga (4096 Hz) seria 46,9 ms de qualquer forma. Sem dead-time,
 * nao ha numero para errar. */

/* --- Clamp de duty ----------------------------------------------------------
 * O M3 tem clamp explicito de 2 % a 95 % (criterio da §5). O M2 nao declara
 * clamp na §5, mas o mesmo clamp e aplicado aqui de proposito: o RF-08 do
 * plano avisa que um duty de repouso mal aplicado pode fechar caminho de
 * fase, e limitar o duty e a defesa mais barata contra isso.
 * EXCECAO (achado F7): duty_percent == 0 NAO e clampado para 2 % — e
 * desligamento de verdade (nivel baixo forçado). O shutdown antigo via
 * "clamp minimo" deixava ~1 us de pulso alto a cada 50 us nas gates. */
#define PWM_DUTY_MIN_PERCENT   2
#define PWM_DUTY_MAX_PERCENT   95

static const char *TAG_M2 = "m2_pwm";

/* --- Estado MCPWM (grupo 0) ------------------------------------------------
 * 2 timers (um por motor), 3 operadores, 2 geradores por operador = 6 saidas.
 * Distribuicao dos 6 canais (2 motores × 3 fases; "fase 1/2/3" e a ordem das
 * 3 nets do gerador no netlist, nao uma convencao U/V/W — ver board_pins.h):
 *
 *   timer 0 (motor 1) -> operador 0: canal 0 = M101, canal 1 = M102
 *                     -> operador 2: canal 2 = M103, canal 5 = M203
 *   timer 1 (motor 2) -> operador 1: canal 3 = M201, canal 4 = M202
 *
 * POR QUE a fase 3 dos dois motores divide o operador 2: um operador se liga
 * a UM timer (mcpwm_operator_connect_timer), e 3 operadores × 2 geradores
 * = 6 e o maximo do grupo no S3. Para deixar cada motor 100 % no seu timer
 * seriam 4 operadores (2 por motor) — o S3 nao tem. Consequencia: M203
 * (fase 3 do motor 2) corre na referencia do timer 0. Como os dois timers
 * sao identicos (80 MHz / 4000 ticks = 20 kHz exatos), a unica diferenca e a
 * FASE da portadora de M203 em relacao as demais fases do motor 2 — sem
 * efeito eletrico nesta topologia single-ended (cada IR2104 gera seu
 * complementar a partir de UM input; nao existe amostragem sincronizada a
 * portadora enquanto o M8/BEMF nao existir). */
typedef struct {
    int gpio;      /* GPIO do pino IN do IR2104                        */
    int timer;     /* 0 = timer do motor 1, 1 = timer do motor 2      */
    int oper;      /* indice do operador no grupo (0..2)               */
    int gen;       /* indice do gerador dentro do operador (0..1)     */
} m2_canal_t;

static const m2_canal_t s_canal[M2_PWM_CANAIS] = {
    /* canal 0 */ { PWM_M101_GPIO, 0, 0, 0 },   /* motor 1, fase 1 */
    /* canal 1 */ { PWM_M102_GPIO, 0, 0, 1 },   /* motor 1, fase 2 */
    /* canal 2 */ { PWM_M103_GPIO, 0, 2, 0 },   /* motor 1, fase 3 */
    /* canal 3 */ { PWM_M201_GPIO, 1, 1, 0 },   /* motor 2, fase 1 */
    /* canal 4 */ { PWM_M202_GPIO, 1, 1, 1 },   /* motor 2, fase 2 */
    /* canal 5 */ { PWM_M203_GPIO, 0, 2, 1 },   /* motor 2, fase 3 — timer 0 */
};

/* Estaticos: zero-inicializados (= NULL) pelo C antes de qualquer init. */
static mcpwm_timer_handle_t s_timer[2];
static mcpwm_oper_handle_t  s_oper[3];
static mcpwm_cmpr_handle_t  s_cmpr[M2_PWM_CANAIS];
static mcpwm_gen_handle_t   s_gen[M2_PWM_CANAIS];
static bool                 s_m2_ready = false;

/* ---------------------------------------------------------------------------
 * m2_pwm_init — cria 2 timers, 3 operadores, 6 comparadores e 6 geradores no
 * grupo 0 do MCPWM, e deixa as 6 saidas em NIVEL BAIXO desde a criacao.
 *
 * Estado seguro por construcao: cada gerador nasce com force level 0 em hold
 * (mcpwm_generator_set_force_level(gen, 0, true)), que sobrepoe qualquer
 * evento do timer ate ser liberado por m2_pwm_set_duty() com level = -1.
 * Assim, mesmo com os timers rodando a 20 kHz, nenhuma gate sobe enquanto
 * nenhum chamador mandar duty > 0.
 *
 * O callback de fim de periodo do esqueleto antigo foi REMOVIDO pela
 * auditoria de 2026-10-04 (baixos): nao fazia nada, tinha assinatura errada
 * (1 argumento; a real e `bool cb(mcpwm_timer_handle_t, const
 * mcpwm_timer_event_data_t *, void *)`) e semantica invertida — e a §5 nao
 * exige nada dele. Quando o M8 (comutacao) existir, quem implementa decide
 * se precisa de ISR de TEZ via mcpwm_timer_register_event_callbacks().
 * Menos codigo agora = menos bug.
 *
 * Nao testado. Os GPIOs vem de board_pins.h (conferidos contra o datasheet
 * do WROOM-1 pela auditoria); um GPIO invalido falha alto aqui, no
 * mcpwm_new_generator, que e o comportamento desejado.
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_init(void)
{
    ESP_LOGI(TAG_M2, "M2: init MCPWM %d Hz (%u MHz / %u ticks), %d canais",
             PWM_FREQ_HZ, (unsigned)(PWM_RESOLUTION_HZ / 1000000u),
             (unsigned)PWM_PERIOD_TICKS, M2_PWM_CANAIS);

    /* 2 timers identicos, um por motor. */
    for (int t = 0; t < 2; t++) {
        mcpwm_timer_config_t timer_config = {
            .group_id      = 0,
            .clk_src       = MCPWM_TIMER_CLK_SRC_DEFAULT,  /* PLL 160 MHz  */
            .resolution_hz = PWM_RESOLUTION_HZ,             /* prescale = 2 */
            .count_mode    = MCPWM_TIMER_COUNT_MODE_UP,
            .period_ticks  = PWM_PERIOD_TICKS,              /* 20 kHz exato */
            .intr_priority = 0,
        };
        ESP_RETURN_ON_ERROR(mcpwm_new_timer(&timer_config, &s_timer[t]),
                            "m2_pwm", "falha ao criar um timer MCPWM");
    }

    /* 3 operadores — o maximo de um grupo no ESP32-S3 (F1). */
    for (int o = 0; o < 3; o++) {
        mcpwm_operator_config_t oper_config = {
            .group_id     = 0,
            .intr_priority = 0,
        };
        ESP_RETURN_ON_ERROR(mcpwm_new_operator(&oper_config, &s_oper[o]),
                            "m2_pwm", "falha ao criar um operador do M2");
    }

    /* Cada operador se liga a UM timer (ver tabela s_canal acima). */
    ESP_RETURN_ON_ERROR(mcpwm_operator_connect_timer(s_oper[0], s_timer[0]),
                        "m2_pwm", "falha ao ligar operador 0 ao timer 0");
    ESP_RETURN_ON_ERROR(mcpwm_operator_connect_timer(s_oper[1], s_timer[1]),
                        "m2_pwm", "falha ao ligar operador 1 ao timer 1");
    ESP_RETURN_ON_ERROR(mcpwm_operator_connect_timer(s_oper[2], s_timer[0]),
                        "m2_pwm", "falha ao ligar operador 2 ao timer 0");

    /* 6 pares comparador+gerador, um por canal, ja segurados em nivel baixo. */
    for (int i = 0; i < M2_PWM_CANAIS; i++) {
        mcpwm_comparator_config_t cmpr_config = {
            .intr_priority = 0,
            .flags.update_cmp_on_tez = true,  /* novo duty entra no TEZ */
        };
        ESP_RETURN_ON_ERROR(
            mcpwm_new_comparator(s_oper[s_canal[i].oper], &cmpr_config,
                                  &s_cmpr[i]),
            "m2_pwm", "falha ao criar um comparador do M2");

        mcpwm_generator_config_t gen_config = {
            .gen_gpio_num = s_canal[i].gpio,   /* campo da GEN config, F1 */
        };
        ESP_RETURN_ON_ERROR(
            mcpwm_new_generator(s_oper[s_canal[i].oper], &gen_config,
                                &s_gen[i]),
            "m2_pwm", "falha ao criar um gerador do M2");

        /* Nivel baixo ANTES de qualquer acao e antes do timer rodar: o force
         * level em hold mantem a saida baixa mesmo depois, ate o -1. */
        ESP_RETURN_ON_ERROR(
            mcpwm_generator_set_force_level(s_gen[i], 0, true),
            "m2_pwm", "falha ao prender o gerador em nivel baixo");

        /* PWM classico edge-aligned: sobe no inicio do periodo (TEZ),
         * desce quando o contador cruza o compare (direcao UP). */
        ESP_RETURN_ON_ERROR(
            mcpwm_generator_set_actions_on_timer_event(
                s_gen[i],
                MCPWM_GEN_TIMER_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP,
                                             MCPWM_TIMER_EVENT_EMPTY,
                                             MCPWM_GEN_ACTION_HIGH),
                MCPWM_GEN_TIMER_EVENT_ACTION_END()),
            "m2_pwm", "falha ao programar a acao de timer do gerador");
        ESP_RETURN_ON_ERROR(
            mcpwm_generator_set_actions_on_compare_event(
                s_gen[i],
                MCPWM_GEN_COMPARE_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP,
                                               s_cmpr[i],
                                               MCPWM_GEN_ACTION_LOW),
                MCPWM_GEN_COMPARE_EVENT_ACTION_END()),
            "m2_pwm", "falha ao programar a acao de compare do gerador");

        ESP_RETURN_ON_ERROR(
            mcpwm_comparator_set_compare_value(s_cmpr[i], 0),
            "m2_pwm", "falha ao zerar o comparador");
    }

    /* Timers ligados por ultimo: as 6 saidas ja estao presas em nivel baixo. */
    for (int t = 0; t < 2; t++) {
        ESP_RETURN_ON_ERROR(mcpwm_timer_enable(s_timer[t]),
                            "m2_pwm", "falha ao habilitar um timer MCPWM");
        ESP_RETURN_ON_ERROR(
            mcpwm_timer_start_stop(s_timer[t], MCPWM_TIMER_START_NO_STOP),
            "m2_pwm", "falha ao arrancar um timer MCPWM");
    }

    s_m2_ready = true;
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m2_pwm_set_duty — escreve o duty dos 6 canais, em porcentagem.
 *
 * O clamp de 2 % a 95 % e aplicado aqui e nao no chamador, para que nenhum
 * caminho futuro escape dele por esquecimento. EXCECAO: 0 % e desligamento
 * de verdade (cai no shutdown, nivel baixo forçado) — achado F7.
 *
 * Os 6 canais recebem o MESMO duty neste esqueleto (nao existe M8/comutacao
 * por fase ainda), mas cada canal tem comparador PROPRIO: quando o M8
 * chegar, a API por canal e acrescentar um indice a esta funcao, nao
 * reescrever o driver.
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_set_duty(uint8_t duty_percent)
{
    if (!s_m2_ready) {
        return ESP_ERR_INVALID_STATE;
    }
    if (duty_percent == 0u) {
        return m2_pwm_shutdown();   /* 0 = nivel baixo, nao clamp de 2 % (F7) */
    }
    if (duty_percent < PWM_DUTY_MIN_PERCENT) {
        duty_percent = PWM_DUTY_MIN_PERCENT;
    }
    if (duty_percent > PWM_DUTY_MAX_PERCENT) {
        duty_percent = PWM_DUTY_MAX_PERCENT;
    }

    const uint32_t compare =
        (PWM_PERIOD_TICKS * (uint32_t)duty_percent) / 100u;

    /* Escreve os comparadores ANTES de soltar o force level, para nao existir
     * janela em que o PWM corre com o duty antigo ou com zero. */
    for (int i = 0; i < M2_PWM_CANAIS; i++) {
        ESP_RETURN_ON_ERROR(
            mcpwm_comparator_set_compare_value(s_cmpr[i], compare),
            "m2_pwm", "falha ao escrever o compare de um canal");
    }
    for (int i = 0; i < M2_PWM_CANAIS; i++) {
        /* level = -1 remove o force level (doc de mcpwm_generator_set_force_
         * level) e devolve o controle as acoes TEZ/compare do init. */
        ESP_RETURN_ON_ERROR(
            mcpwm_generator_set_force_level(s_gen[i], -1, false),
            "m2_pwm", "falha ao liberar o force level de um canal");
    }
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m2_pwm_set_all — aplica um duty aos 6 canais de uma vez.
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_set_all(uint8_t duty_percent)
{
    return m2_pwm_set_duty(duty_percent);
}

/* ---------------------------------------------------------------------------
 * m2_pwm_shutdown — estado seguro REAL (achado F7): comparador em 0 E nivel
 * baixo forçado em hold.
 *
 * So zerar o comparador nao basta: com as acoes "TEZ sobe / compare desce",
 * compare = 0 disputa a mesma borda do TEZ e pode vazar 1 tick alto por
 * periodo (a 80 MHz, 1 tick = 12,5 ns; no codigo antigo, com clamp de 2 %,
 * o vazamento era ~1 us de gate a cada 50 us). O force level 0 em hold
 * sobrepoe qualquer evento e segura a saida baixa ate que um set_duty()
 * nao-nulo a libere. Os timers continuam rodando — sem PWM nas saidas.
 * ------------------------------------------------------------------------ */
esp_err_t m2_pwm_shutdown(void)
{
    if (!s_m2_ready) {
        return ESP_ERR_INVALID_STATE;
    }
    for (int i = 0; i < M2_PWM_CANAIS; i++) {
        ESP_RETURN_ON_ERROR(
            mcpwm_comparator_set_compare_value(s_cmpr[i], 0),
            "m2_pwm", "falha ao zerar o compare no shutdown");
        ESP_RETURN_ON_ERROR(
            mcpwm_generator_set_force_level(s_gen[i], 0, true),
            "m2_pwm", "falha ao forcar nivel baixo no shutdown");
    }
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m2_pwm_forca_gpio_baixo — estado seguro por GPIO PURO, sem MCPWM.
 *
 * Para usar ANTES de m2_pwm_init() (primeira coisa do boot) e quando o init
 * FALHAR: configura os 6 GPIOs como saida em nivel baixo direto pelo
 * driver/gpio, sem passar pelo periferico. E o unico estado seguro que
 * existe antes de mcpwm_new_generator() — e os pinos IN dos IR2104 NAO tem
 * pull-down na placa (netlist v7: a net PWM_Mxxx so liga MCU e IR2104), entao
 * alguem tem que dirigi-los cedo.
 *
 * NAO usar depois de um init BEM-SUCEDIDO: os pinos ja roteados a MCPWM pela
 * GPIO matrix ignoram o gpio_set_level; nesse estado o caminho certo e
 * m2_pwm_shutdown(). Se o init falhou NO MEIO (alguns geradores criados,
 * outros nao), os criados estao presos em nivel baixo pelo force level do
 * init e os demais seguem como GPIO baixo desta funcao — os 6 baixos.
 *
 * Nota eletrica (datasheet IR2104, conferido pela auditoria): IN baixo com
 * SD alto (o SD desta placa e puxado ao 3V3 por 10k — achado F12) deixa HO
 * baixo e LO alto: low-side conduzindo, high-side cortado. Sem shoot-through
 * e sem giro. E o estado que o projeto chama de seguro; nao existe como o
 * firmware desligar os 12 drivers de porta.
 * ------------------------------------------------------------------------ */
void m2_pwm_forca_gpio_baixo(void)
{
    for (int i = 0; i < M2_PWM_CANAIS; i++) {
        const gpio_num_t gpio = (gpio_num_t)s_canal[i].gpio;
        const gpio_config_t cfg = {
            .pin_bit_mask = (uint64_t)1ULL << (int)gpio,
            .mode         = GPIO_MODE_OUTPUT,
            .pull_up_en   = GPIO_PULLUP_DISABLE,
            .pull_down_en = GPIO_PULLDOWN_DISABLE,
            .intr_type    = GPIO_INTR_DISABLE,
        };
        if (gpio_config(&cfg) != ESP_OK || gpio_set_level(gpio, 0) != ESP_OK) {
            ESP_LOGE(TAG_M2, "M2: GPIO %d nao pode ser forcado a nivel baixo",
                     (int)gpio);
        }
    }
}
