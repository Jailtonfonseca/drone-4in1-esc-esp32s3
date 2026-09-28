# ===========================================================================
# firmware/main/CMakeLists.txt — componente de aplicacao
#
# ESQUELETO NAO VERIFICADO. ESTE ARQUIVO NAO FOI PROCESSADO POR NENHUM
# GERADOR DE BUILD NESTA MAQUINA. Por que: o ESP-IDF nao esta instalado.
# Ver ../../fase4_entrega/FIRMWARE_BUILD.md.
#
# As dependencias abaixo sao as que o codigo usa. Nenhuma delas foi resolvida
# nesta maquina, porque nao ha arvore de componentes do ESP-IDF no disco para
# resolver contra. Os nomes vem da API do ESP-IDF v5, escritas de memoria e nao
# conferidas contra headers reais.
#
#   driver          -> gpio, ledc, mcpwm_*, spi_master
#   esp_adc         -> adc_oneshot (M1) e adc_cali (curva de calibracao)
#   freertos, esp_timer -> tarefa de leitura e temporizacao
#
# Um detalhe de M2: o driver MCPWM do ESP-IDF v5 e experimental e a ESP-IDF
# exige ligar CONFIG_MCPWM_ISR_DEBUG ou similar para a ISR do timer disparar
# corretamente. Nada disso foi testado.
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
        esp_timer
)
