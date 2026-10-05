/* ===========================================================================
 * m1_vbat.c — modulo M1: leitura de VBAT pelo divisor resistivo
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F1/F5/F6); AINDA NAO
 * COMPILADO — precisa de idf.py build para validar. O ESP-IDF nao esta
 * instalado nesta maquina; existe apenas o compilador C Xtensa testado com
 * um arquivo de 5 linhas sem framework (firmware/build_log.txt), o que nao
 * valida este codigo. As assinaturas de adc_oneshot/adc_cali abaixo foram
 * conferidas contra os headers reais do ESP-IDF v5.4
 * (components/esp_adc/include/esp_adc/adc_oneshot.h e adc_cali_scheme.h):
 * nao existe handle de canal; adc_oneshot_config_channel() recebe a unidade
 * e o numero do canal.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M1.
 *
 * O que M1 tem que entregar, segundo o criterio de aceite da §5:
 *   VBAT medido = 2,385752 V @ 19,8 V · 2,674934 V @ 22,2 V · 3,036412 V @
 *   25,2 V, com erro < 2 % (fase4_entrega/PLANO_TESTE_BANCADA.md, passo 10).
 *
 * Todos os numeros desta secao vem de fase4_entrega/calcs_fase4.txt, lido nesta
 * maquina. O criterio nao e satisfeito aqui: os valores abaixo sao o que a
 * conta da, nao o que o conversor mediu. Nenhuma leitura foi feita em hardware.
 * ======================================================================== */

#include "m1_vbat.h"
#include "board_pins.h"

#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_err.h"

/* --- Divisor resistivo ---------------------------------------------------
 * Layout v7: RVB1 = 100 k entre VBAT_PROT e VBAT_SENSE, RVB2 = 13,7 k entre
 * VBAT_SENSE e GND (fase3_pcb/gera_pcb_v7.py, linhas 419-428). */
#define RVB1_OHM        100000.0f
#define RVB2_OHM         13700.0f

/* Razao do divisor, ja calculada por calcs_fase4.txt nesta maquina:
 *   13,7k / (100k + 13,7k) = 0,1204925242
 * Esta e a mesma razao cuja saida a fase 2 mediu em 3,036412 V para 25,2 V. */
#define VBAT_DIV_RATIO  (RVB2_OHM / (RVB1_OHM + RVB2_OHM))   /* 0,1204925242 */

/* --- ADC interno ---------------------------------------------------------
 * VBAT_SENSE entra pelo pad 39 do modulo = IO1 = GPIO1 = ADC1_CH0 (tabela
 * "Pin Definitions" do datasheet do WROOM-1, conferida na auditoria de
 * 2026-10-04; ver board_pins.h). O canal abaixo nao e mais um palpite. */
#define VBAT_ADC_UNIT           ADC_UNIT_1
#define VBAT_ADC_CHANNEL        ADC_CHANNEL_0   /* GPIO1 = ADC1_CH0 */
#define VBAT_ADC_ATTEN           ADC_ATTEN_DB_12 /* fundo de escala ate ~3,1 V */

/* --- Conversao para volts de bateria ------------------------------------
 * 1 LSB do ADC de 12 bits: 4095 e o ultimo degrau, nao 4096 (corrigido pela
 * auditoria de 2026-10-04, baixos):
 *   3,3 V / 4095 = 805,86 uV por LSB no pino
 * isso da 6,69 mV por LSB referred a VBAT depois do divisor.
 * ATENCAO (baixo da auditoria): este fator so e usado no FALLBACK, quando a
 * calibracao de fabrica falha. Com atenuacao de 12 dB o fundo de escala real
 * e ~3,1 V (nao 3,3 V), entao o fallback le ALTO por ~6 % — o passo 10 do
 * plano de bancada so fecha com a cali de fabrica funcionando. */
#define VBAT_VREF_VOLTS         3.3f
#define VBAT_LSB_AT_PIN         (VBAT_VREF_VOLTS / 4095.0f)   /* 805,86 uV */

static const char *TAG_M1 = "m1_vbat";

/* Estado do modulo. tudo estatico por enquanto: o M1 e single-task.
 * Nao existe mais handle de canal: na API oneshot do v5.4 o canal e um
 * argumento de adc_oneshot_config_channel()/adc_oneshot_read(). */
static adc_oneshot_unit_handle_t s_vbat_unit   = NULL;
static adc_cali_handle_t         s_vbat_cali   = NULL;
static bool                      s_vbat_ready  = false;

/* ---------------------------------------------------------------------------
 * m1_vbat_init — configura o ADC1 e a calibracao de fabrica.
 *
 * Nao testado. O canal ADC1_CH0 tem que bater com o GPIO1 do board_pins.h;
 * se um dia mudarem um sem o outro, o criterio do passo 10 falha em bancada
 * (o driver nao tem como validar a correspondencia GPIO<->canal por conta
 * propria: adc_oneshot_config_channel so recebe o canal).
 * ------------------------------------------------------------------------ */
esp_err_t m1_vbat_init(void)
{
    ESP_LOGI(TAG_M1, "M1: init VBAT (GPIO%d, divisor %.7f)", VBAT_SENSE_GPIO,
             (double)VBAT_DIV_RATIO);

    adc_oneshot_unit_init_cfg_t unit_cfg = {
        .unit_id = VBAT_ADC_UNIT,
    };
    ESP_RETURN_ON_ERROR(adc_oneshot_new_unit(&unit_cfg, &s_vbat_unit),
                        "m1_vbat", "falha ao criar a unidade do ADC1");

    adc_oneshot_chan_cfg_t chan_cfg = {
        .atten = VBAT_ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_RETURN_ON_ERROR(adc_oneshot_config_channel(s_vbat_unit, VBAT_ADC_CHANNEL,
                                                   &chan_cfg),
                        "m1_vbat", "falha ao configurar o canal de VBAT");

    /* Calibracao de fabrica. ATEN de 12 dB e o unico que cobre 3,036412 V
     * com margem: com 11 dB o fundo de escala (~2,5 V) cortaria a leitura de
     * bateria cheia. O campo .chan existe na adc_cali_curve_fitting_config_t
     * do v5.4 (calibracao por canal nos chips que suportam). */
    adc_cali_curve_fitting_config_t cali_cfg = {
        .unit_id  = VBAT_ADC_UNIT,
        .chan     = VBAT_ADC_CHANNEL,
        .atten    = VBAT_ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    if (adc_cali_create_scheme_curve_fitting(&cali_cfg, &s_vbat_cali) != ESP_OK) {
        s_vbat_cali = NULL;   /* segue sem calibracao; a leitura passa a ser bruta */
        ESP_LOGW(TAG_M1, "M1: sem curva de calibracao, leitura sera bruta");
    }

    s_vbat_ready = true;
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m1_vbat_read_volts — uma leitura de VBAT, em volts da bateria.
 *
 * Devolve false se o modulo nao foi inicializado ou se a leitura falhou. O
 * criterio de aceite da §5 pede erro < 2 %; o codigo nao mede erro nenhum, ele
 * so converte. O unico jeito de saber se acerta e o passo 10 do plano de
 * bancada, com a fonte em 19,8 / 22,2 / 25,2 V.
 * ------------------------------------------------------------------------ */
bool m1_vbat_read_volts(float *out_volts)
{
    if (!s_vbat_ready || out_volts == NULL) {
        return false;
    }

    int raw = 0;
    if (adc_oneshot_read(s_vbat_unit, VBAT_ADC_CHANNEL, &raw) != ESP_OK) {
        return false;
    }

    int mv = 0;
    float v_pino;
    if (s_vbat_cali != NULL && adc_cali_raw_to_voltage(s_vbat_cali, raw, &mv) == ESP_OK) {
        v_pino = (float)mv / 1000.0f;
    } else {
        /* Fallback bruto: le ~6 % alto por ignorar a escala da atenuacao de
         * 12 dB (fundo de escala ~3,1 V, nao 3,3 V) — ver o aviso no topo. */
        v_pino = (float)raw * VBAT_LSB_AT_PIN;
    }

    *out_volts = v_pino / VBAT_DIV_RATIO;
    return true;
}

/* ---------------------------------------------------------------------------
 * Tabela de conferencia contra o passo 10 do plano de bancada.
 *
 * Estes NAO sao valores medidos em hardware: sao as tres entradas de
 * calcs_fase4.txt, que a §5 transformou em criterio de aceite. A coluna do
 * meio e o que o firmware deve imprimir quando a fonte estiver no valor da
 * esquerda.
 * ------------------------------------------------------------------------ */
/*   VBAT de entrada | VBAT esperado no pino | volts que o firmware deve ler  */
/*        19,8 V     |      2,385752 V      |    19,8 V (criterio M1)        */
/*        22,2 V     |      2,674934 V      |    22,2 V (criterio M1)        */
/*        25,2 V     |      3,036412 V      |    25,2 V (criterio M1)        */

/* ---------------------------------------------------------------------------
 * m1_vbat_log — imprime uma leitura. M1 tambem cobre LED, buzzer, botoes e
 * temperatura em regime; so a parte de VBAT esta esboçada aqui, porque e a
 * unica com criterio de aceite fechado na §5.
 * ------------------------------------------------------------------------ */
void m1_vbat_log(void)
{
    float v = 0.0f;
    if (m1_vbat_read_volts(&v)) {
        ESP_LOGI(TAG_M1, "VBAT = %.6f V (divisor %.7f)", (double)v,
                 (double)VBAT_DIV_RATIO);
    } else {
        ESP_LOGE(TAG_M1, "falha na leitura de VBAT");
    }
}
