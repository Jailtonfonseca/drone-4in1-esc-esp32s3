/* ===========================================================================
 * app_main.c — ponto de entrada do esqueleto de firmware do drone
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F5/F9 e baixos); AINDA NAO
 * COMPILADO — precisa de idf.py build para validar. O ESP-IDF nao esta
 * instalado nesta maquina, entao nao existe idf.py, nem esp32s3.project.ld,
 * nem os componentes de driver. Existe apenas o compilador C Xtensa testado
 * com um .c de 5 linhas sem framework (firmware/build_log.txt) — isso nao
 * valida este arquivo.
 *
 * O que a auditoria pegou aqui (F5): o app_main antigo NUNCA chamava
 * m2_pwm_init/m3_pwm_init/m4_adc_init — os shutdown() falhavam com
 * INVALID_STATE, nada ia a nivel seguro e a task de leitura falhava em
 * silencio para sempre. A ordem agora e: (1) nivel baixo por GPIO puro nos 12
 * pinos de PWM, (2) init de TODOS os modulos, (3) shutdown dos modulos cujo
 * init funcionou, e se um init falhar os pinos dele SEGUEM em nivel baixo
 * pela rota 1 — estado seguro real, nao so um log de erro.
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
 * A ordem nao e arbitraria e cada passo existe por um motivo:
 *
 *   1. NIVEL BAIXO POR GPIO PURO primeiro: os 12 pinos IN dos IR2104 nao tem
 *      pull na placa (netlist v7), entao dirigir os 12 para 0 pela GPIO e a
 *      unica forma de estado seguro que existe antes de qualquer driver.
 *   2. Init de TODOS os modulos (F5 exige init antes do shutdown): M2, M3,
 *      M4 e M1. Cada init que roda ja deixa as saidas do modulo presas em
 *      nivel baixo por construcao (force level / duty 0).
 *   3. Shutdown so nos modulos cujo init funcionou (reforcam o nivel baixo
 *      pela rota do periferico). No modulo cujo init FALHOU, os pinos seguem
 *      exatamente como estavam no passo 1: GPIO em nivel baixo. Nos dois
 *      casos o resultado eletrico e o mesmo estado seguro do projeto: IN
 *      baixo = HO baixo e LO alto (high-side cortado, low-side fechado —
 *      sem shoot-through, sem giro; ver a nota eletrica em m2_pwm_mcpwm.c).
 *   4. A task de leitura so nasce se o M4 existir; sem ADC nao ha o que ler.
 * ------------------------------------------------------------------------ */
void app_main(void)
{
    ESP_LOGW(TAG, "esqueleto de firmware — NAO VERIFICADO, NAO VALIDADO");
    ESP_LOGW(TAG, "M1..M4 existem como esqueleto; M8, M10 e M11 nao existem");
    ESP_LOGW(TAG, "nao conectar a bateria com helices: nenhum failsafe existe");

    /* 1. Estado seguro por GPIO puro, antes de qualquer driver (F5). */
    m2_pwm_forca_gpio_baixo();
    m3_pwm_forca_gpio_baixo();

    /* 2. Init de todos os modulos — ANTES dos shutdown (F5). */
    const esp_err_t err_m2 = m2_pwm_init();
    const esp_err_t err_m3 = m3_pwm_init();
    const esp_err_t err_m4 = m4_adc_init();
    const esp_err_t err_m1 = m1_vbat_init();

    /* 3. Shutdown com os drivers de pe — e caminho seguro quando falha. */
    if (err_m2 == ESP_OK) {
        if (m2_pwm_shutdown() == ESP_OK) {
            ESP_LOGI(TAG, "M2: 6 saidas MCPWM em nivel baixo (force level 0)");
        } else {
            ESP_LOGE(TAG, "M2: shutdown falhou apos init com sucesso");
        }
    } else {
        ESP_LOGE(TAG, "M2: init falhou (%d); os 6 pinos seguem como GPIO "
                 "em nivel baixo do passo 1", (int)err_m2);
    }
    if (err_m3 == ESP_OK) {
        if (m3_pwm_shutdown() == ESP_OK) {
            ESP_LOGI(TAG, "M3: 6 saidas LEDC travadas em nivel baixo "
                     "(duty 0 + ledc_stop)");
        } else {
            ESP_LOGE(TAG, "M3: shutdown falhou apos init com sucesso");
        }
    } else {
        ESP_LOGE(TAG, "M3: init falhou (%d); os 6 pinos seguem como GPIO "
                 "em nivel baixo do passo 1", (int)err_m3);
    }

    if (err_m1 == ESP_OK) {
        m1_vbat_log();
    } else {
        ESP_LOGE(TAG, "M1: init do ADC de VBAT falhou (%d)", (int)err_m1);
    }

    /* 4. Task de leitura: so se o M4 subiu. */
    if (err_m4 == ESP_OK) {
        const BaseType_t ok = xTaskCreate(
            task_de_Leitura,          /* nome da funcao, definido abaixo */
            "leitura",                /* nome da tarefa                  */
            2048,                     /* pilha em BYTES — ver comentario  */
            NULL,                     /* sem parametros                   */
            1,                        /* prioridade                       */
            NULL);                    /* sem handle                       */
        if (ok != pdPASS) {
            ESP_LOGE(TAG, "nao foi possivel criar a tarefa de leitura");
        }
    } else {
        ESP_LOGE(TAG, "M4: init do SPI falhou (%d) — sem task de leitura",
                 (int)err_m4);
    }
}

/* ---------------------------------------------------------------------------
 * task_de_Leitura — laco de leitura, sem efeito sobre nenhuma saida.
 *
 * Ela nao escreve nada nos 12 sinais de PWM. Existe para mostrar onde a
 * cadencia de leitura vai morar, e para nao deixar a tentacao de "ja ligar o
 * PWM aqui" sem comentario: ligar o PWM aqui e o primeiro passo na direcao
 * errada, porque nao existe M8 (comutacao por BEMF), nem M10 (failsafe), nem
 * M11 (watchdog) para conter um erro.
 *
 * NOTA SOBRE A PILHA (contra-achado da auditoria): o comentario antigo
 * "pilha em bytes" estava CERTO e NAO foi trocado por "palavras". O header
 * real do ESP-IDF v5.4 (components/freertos/FreeRTOS-Kernel/include/
 * freertos/task.h) diz, no proprio doxygen do xTaskCreate: "usStackDepth:
 * The size of the task stack specified as the NUMBER OF BYTES. Note that
 * this differs from vanilla FreeRTOS." A auditoria de 2026-10-04 listou
 * "xTaskCreate conta palavras, nao bytes" entre os baixos — esse item
 * descreve o FreeRTOS vanilla, nao o port do ESP-IDF, e esta errado.
 *
 * NOTA SOBRE O DELAY: pdMS_TO_TICKS(1) so vira "1 tick de verdade" porque o
 * sdkconfig.defaults agora tem CONFIG_FREERTOS_HZ=1000 (achado F9). Com o
 * default de 100 Hz, 1 ms truncava para 0 tick e o vTaskDelay(0) virava um
 * yield-loop que faminta a idle e dispara o task watchdog.
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
