# ===========================================================================
# firmware/CMakeLists.txt — projeto ESP-IDF do firmware de bordo do drone
#
# ESQUELETO NAO VERIFICADO. ESTE ARQUIVO NAO FOI PROCESSADO POR NENHUM
# GERADOR DE BUILD NESTA MAQUINA. Por que: o ESP-IDF nao esta instalado,
# entao nao existe idf.py nem o conjunto de ferramentas que consome este
# CMakeLists.txt. Ver ../fase4_entrega/FIRMWARE_BUILD.md.
#
# A estrutura segue a da ESP-IDF v5, com o componente do usuario em main/.
# Ao rodar `idf.py build`, a ESP-IDF le este arquivo, o de main/CMakeLists.txt
# e o sdkconfig.defaults ao lado. Nada disso foi executado nesta maquina.
#
# cmake_minimum_required de 3.16 e o minimo da ESP-IDF v5. O cmake desta
# maquina e o 3.29.3 em /usr/local/bin (e o 3.25.1 do apt), acima do minimo.
#
# Modulos cobertos: M1, M2, M3 e M4 de plano/WP4_FIRMWARE.md §5.
# ========================================================================

cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(drone_fw)
