/* ===========================================================================
 * app_main.c — ponto de entrada do esqueleto de firmware do drone
 *
 * ESQUELETO NAO VERIFICADO. ESTE ARQUIVO NAO FOI COMPILADO NESTA MAQUINA.
 * Por que: o ESP-IDF nao esta instalado, entao nao existe idf.py, nem
 * esp32s3.project.ld, nem os componentes de driver. Existe nesta maquina
 * apenas o compilador C Xtensa, testado com um .c de 5 linhas sem framework
 * (firmware/build_log.txt) — isso nao valida este arquivo.
 *
 * AVISO SOBRE A API: app_main e o ponto de entrada exigido pelo componente
 * app_main do ESP-IDF. A assinatura e correta, mas nenhum include foi
 * verificado contra um header real desta maquina.
 *
 * O que este arquivo NAO faz, de proposito:
 *   - nao comuta motor nenhum (M8 nao existe);
 *   - nao le o link de comando (M9 nao existe);
 *   - nao implementa o failsafe (M10 nao existe);
 *   - nao alimenta o watchdog externo (M11 nao existe).
 * Portanto, rodar este binario, se algum dia ele compilar, NAO faz o drone
 * voar e NAO e seguro conectar a bateria com helices. Ver README.md.
 *
 * Modulos de origem: plano/WP4_FIRMWARE.md §5, linhas M1, M2, M3 e M4.
 * ======================================================================== */

#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

#include "board_pins.h"
#include "m1_vbat.h"
#include "m2_pwm_mcpwm.h"
#include "m3_pwm_ledc.h"
#include "m4_adc_spi.h"

static const char *TAG = "app_main";

/* Definida no fim do arquivo; declarada aqui porque app_main a cria. */
static void task_de_Leitura(void *arg);

/* ---------------------------------------------------------------------------
 * app_main — o que se pode rodar com seguranca nesta placa hoje.
 *
 * A ordem nao e arbitraria: os sinais dos 12 drivers entram no MCU e, enquanto
 * o firmware nao commande nada, o estado do pad importa. Chamar o shutdown dos
 * dois modulos de PWM ANTES de qualquer log e a unica coisa que este esqueleto
 * faz por seguranca. Se os GPIOs ainda forem -1, como estao em board_pins.h,
 * a ESP-IDF falha aqui e o firmware para com log de erro, que e o resultado
 * desejado: um build que nao sobe e melhor do que um que gira um motor no
 * pad errado.
 * ------------------------------------------------------------------------ */
void app_main(void)
{
    ESP_LOGW(TAG, "esqueleto de firmware — NAO VERIFICADO, NAO VALIDADO");
    ESP_LOGW(TAG, "M1..M4 existem como esqueleto; M8, M10 e M11 nao existem");
    ESP_LOGW(TAG, "nao conectar a bateria com helices: nenhum failsafe existe");

    /* 1. Motores em estado seguro antes de qualquer outra coisa. */
    if (m2_pwm_shutdown() == ESP_OK) {
        ESP_LOGI(TAG, "M2: 6 canais de MCPWM no duty minimo");
    } else {
        ESP_LOGE(TAG, "M2: shutdown falhou — GPIO ainda nao conferido?");
    }
    if (m3_pwm_shutdown() == ESP_OK) {
        ESP_LOGI(TAG, "M3: 6 canais de LEDC no duty minimo (dead-time e do IR2104)");
    } else {
        ESP_LOGE(TAG, "M3: shutdown falhou — GPIO ainda nao conferido?");
    }

    /* 2. Bring-up do M1. */
    if (m1_vbat_init() == ESP_OK) {
        m1_vbat_log();
    } else {
        ESP_LOGE(TAG, "M1: init do ADC de VBAT falhou");
    }

    /* 3. Uma tarefa so, de baixa prioridade, que so le. Nao ha PWM, nao ha
     *    comutacao, nao ha link. Medir VBAT e o maximo de coisa util que
     *    este esqueleto faz. */
    const BaseType_t ok = xTaskCreate(
        task_de_Leitura,          /* nome da funcao, definido abaixo */
        "leitura",                /* nome da tarefa                  */
        2048,                     /* pilha em bytes                  */
        NULL,                     /* sem parametros                  */
        1,                        /* prioridade                      */
        NULL);                    /* sem handle                      */
    if (ok != pdPASS) {
        ESP_LOGE(TAG, "nao foi possivel criar a tarefa de leitura");
    }
}

/* ---------------------------------------------------------------------------
 * task_de_Leitura — laco de leitura, sem efeito sobre nenhuma saida.
 *
 * Ela nao escreve nada nos 12 sinais de PWM. Existe para mostrar onde a
 * cadencia de leitura vai morar, e para nao deixar a tentacao de "ja ligar o
 * PWM aqui" sem commentario: ligar o PWM aqui e o primeiro passo na direcao
 * errada, porque nao existe M8 (comutacao por BEMF), nem M10 (failsafe), nem
 * M11 (watchdog) para conter um erro.
 * ------------------------------------------------------------------------ */
static void task_de_Leitura(void *arg)
{
    (void)arg;
    uint8_t state[4];
    unsigned long leituras = 0;

    for (;;) {
        if (m4_adc_poll(state) == ESP_OK) {
            leituras++;
            if ((leituras % 1000u) == 0u) {
                ESP_LOGI(TAG, "M4: %lu leituras | CI %u canal %u = %u LSB",
                         leituras, (unsigned)state[0], (unsigned)state[1],
                         (unsigned)(state[2] | (state[3] << 8)));
            }
        }
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
