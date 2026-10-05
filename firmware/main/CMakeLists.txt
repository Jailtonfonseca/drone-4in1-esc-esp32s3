# ===========================================================================
# firmware/main/CMakeLists.txt — componente de aplicacao
#
# ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
# AUDITORIA_ERROS_2026-10-04.md, secao F); AINDA NAO COMPILADO — precisa de
# idf.py build para validar. Ver ../../fase4_entrega/FIRMWARE_BUILD.md.
#
# As dependencias abaixo sao as que o codigo usa. Nenhuma delas foi resolvida
# nesta maquina, porque nao ha arvore de componentes do ESP-IDF no disco para
# resolver contra. Os nomes foram conferidos contra a arvore do ESP-IDF v5.4:
#
#   driver          -> meta-componente que puxa esp_driver_gpio (gpio),
#                      esp_driver_mcpwm (mcpwm_*), esp_driver_ledc (ledc_*)
#                      e esp_driver_spi (spi_*) — e o caminho publico estavel
#                      "driver/xxx.h" nos tres casos;
#   esp_adc         -> adc_oneshot (M1) e adc_cali (curva de calibracao);
#   freertos        -> tarefa de leitura (xTaskCreate/vTaskDelay).
#
# esp_timer foi REMOVIDO: nenhum modulo usava esp_timer_* (o include antigo
# em m4_adc_spi.c nao chamava nada dele), e dependencia sem consumidor e
# declaracao falsa. Quem precisar de microssegundos (ex.: timestamp do M5)
# adiciona de volta NAQUELE momento.
#
# Sobre a nota antiga de M2 ("a ESP-IDF exige ligar CONFIG_MCPWM_ISR_DEBUG ou
# similar para a ISR do timer disparar"): isso NAO EXISTE. As opcoes reais do
# componente esp_driver_mcpwm no v5.4 (components/esp_driver_mcpwm/Kconfig)
# sao CONFIG_MCPWM_ISR_IRAM_SAFE (ISR a prova de cache desabilitado) e
# CONFIG_MCPWM_CTRL_FUNC_IN_IRAM (coloca funcoes de controle como
# mcpwm_comparator_set_compare_value na IRAM). Nenhuma das duas e necessaria
# aqui: este firmware nao chama controle de MCPWM em ISR nem com flash
# desabilitado, e nenhum callback de timer e registrado (o callback inutil do
# esqueleto antigo foi removido — ver m2_pwm_mcpwm.c). Por isso nenhuma das
# duas aparece no sdkconfig.defaults.
# ========================================================================

idf_component_register(
    SRCS
        "app_main.c"
        "m1_vbat.c"
        "m2_pwm_mcpwm.c"
        "m3_pwm_ledc.c"
        "m4_adc_spi.c"
    INCLUDE_DIRS "."
    REQUIRES
        driver
        esp_adc
)
