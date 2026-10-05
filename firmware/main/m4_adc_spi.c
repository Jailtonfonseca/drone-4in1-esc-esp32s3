/* ===========================================================================
 * m4_adc_spi.c — modulo M4: leitura dos 4x MCP3208 por SPI
 *
 * ESQUELETO corrigido pela auditoria de 2026-10-04 (ver
 * AUDITORIA_ERROS_2026-10-04.md, secao F, achados F4 e baixos); AINDA NAO
 * COMPILADO — precisa de idf.py build para validar. O ESP-IDF nao esta
 * instalado nesta maquina. As structs e chamadas SPI foram conferidas contra
 * os headers reais do ESP-IDF v5.4 (components/esp_driver_spi/include/driver/
 * spi_master.h e spi_common.h): spi_device_interface_config_t NAO tem campo
 * de "fase de comando" separada aqui — o protocolo MCP3208 inteiro via no
 * buffer de dados da transacao full-duplex (command_bits = 0, F4).
 *
 * AVISO SOBRE A API (permanece): spi_bus_initialize/spi_bus_add_device/
 * spi_device_polling_transmit estao com as assinaturas do v5.4, mas nada
 * foi linkado nesta maquina.
 *
 * Modulo de origem: plano/WP4_FIRMWARE.md §5, linha M4.
 *
 * ----------------------------------------------------------------------------
 * OS TRES PROBLEMAS QUE O M4 ENFRENTA, todos registrados no plano
 * ----------------------------------------------------------------------------
 * RF-01: a taxa exigida nao cabe. 6 canais por CI x 20 kHz = 120 ksps por CI.
 * O MCP3208 entrega 100 ksps a 5 V e 50 ksps a 2,7 V (datasheet, Electrical
 * Characteristics, fSAMPLE). A placa alimenta os MCP3208 com 3,3 V
 * (fase3_pcb/gera_pcb_v7.py, linhas 389-390), condicao que o datasheet nao
 * especifica, logo entre 50 e 100 ksps e desconhecida. O numero de 120 ksps
 * fica em 120 % a 240 % do que o CI garante.
 *
 * RF-02: o MCP3208 multiplexa 8 canais e nao tem amostragem simultanea. As
 * "3 fases" de um motor sao lidas em 3 instantes diferentes.
 *
 * RF-09: o barramento SPI e um recurso unico e disputado. 24 canais x 20 kHz
 * x 24 clocks = 11 520 000 clocks/s, que estoura a 8 MHz (144 %) e a 10 MHz
 * (115 %) e so cabe a 20 MHz (57,6 %). Neste barramento mora tambem o IMU
 * (ICM-42688-P, CS = GPIO42, INT = GPIO47), que precisa de leitura a 1-4 kHz
 * sincronizada com o PID. O BAROMETRO NAO esta aqui: ele e I2C (pads 31/32 =
 * GPIO38/GPIO39) — o comentario antigo dizia o contrario (baixo da auditoria).
 *
 * A saida que o proprio plano aponta e o round-robin: ler UM CI por vez, um
 * canal por vez, com fCLK = 20 x fSAMPLE = 0,60 MHz, bem dentro do que o
 * MCP3208 aceita. E isso que a funcao m4_adc_poll abaixo faz.
 *
 * Criterio de aceite da §5 para o M4, que NENHUM dos numeros abaixo cumpre:
 * linearidade < 2 % entre 5 e 30 A com o offset a 0 A anotado e subtraido
 * (passo 12); BEMF com erro < 1 % em 3 pontos (passo 11); 1 mV de saida
 * aproximadamente 40 mA.
 * ======================================================================== */

#include "m4_adc_spi.h"
#include "board_pins.h"

#include "driver/spi_master.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_err.h"

static const char *TAG_M4 = "m4_adc";

/* --- Relogio SPI ----------------------------------------------------------
 * 0,60 MHz, que e 20 x fSAMPLE com fSAMPLE = 30 ksps por CI. O fator 20 vem
 * da propria saida de round-robin do RF-09 e garante a folga de setup/hold do
 * MCP3208 sem disputar o barramento com o IMU. */
#define M4_SPI_CLK_HZ            (600 * 1000)

/* --- Protocolo do MCP3208 (corrigido pela auditoria F4) --------------------
 * Quadro full-duplex de 1 transacao / 3 bytes (24 clocks), modo SPI 0, MSB
 * primeiro. O CI exige full-duplex: a conversao roda NOS MESMOS clocks em
 * que o comando ainda esta saindo no MOSI — SPI_DEVICE_HALFDUPLEX estava
 * errado (F4).
 *
 * Bytes transmitidos para o canal `ch` (0-7), single-ended:
 *   tx[0] = 0x06 | (ch >> 2)   0000 0 1 1 D2  (start=1, SGL/DIFF=1, D2)
 *   tx[1] = (ch & 0x03) << 6   D1 D0 000000
 *   tx[2] = 0x00               clocks de leitura do resultado
 * A montagem antiga (0x06 | ((ch&4)<<1) | (ch&3)) colidia bits e fazia os
 * canais 0/2, 1/3, 4/6 e 5/7 lerem iguais; command_bits = 24 mandava ainda
 * 24 clocks de DIN=0 ANTES do quadro, deslocando o enquadramento do CI.
 *
 * Decodificacao: apos o bit nulo, os 12 bits uteis caem nos 4 bits baixos do
 * rx[1] (B11..B8) e no rx[2] inteiro (B7..B0):
 *   raw = ((rx[1] & 0x0F) << 8) | rx[2]
 * O decode antigo ((rx[1]<<5)|(rx[2]>>3))&0xFFF leria os clocks errados e
 * so funcionava (com escala errada) para CH0/CH4.
 * Referencia: datasheets/mcp3208_microchip_ds21298e.pdf; framing conferido
 * pela auditoria de 2026-10-04 contra o DS21298. */
#define M4_SPI_FRAME_BITS       24
#define M4_SPI_FRAME_BYTES      3
#define M4_MCP3208_ADC_CHANNELS  8

/* Ganho do INA240A2 (50 V/V) e do shunt de 0,5 mOhm (fase4_entrega/
 * calcs_fase4.txt e WP3 P-10). Da a sensibilidade de corrente:
 *   1 A -> 0,5 mV no shunt -> 25,0 mV na saida do amplificador
 *   1 mV de saida -> 40 mA   <- e o criterio de aceite do M4, e este valor. */
#define M4_SHUNT_OHM             0.0005f
#define M4_AMP_GAIN              50.0f
#define M4_AMP_A_POR_VOLT        (1.0f / (M4_SHUNT_OHM * M4_AMP_GAIN))  /* 40,0 A/V */

/* Divisor de BEMF do layout: 1,0 k sobre 8,2 k + 1,0 k
 * (fase4_entrega/calcs_fase4.txt, razao 0,1086956522). */
#define M4_BEMF_RATIO            (1.0f / (8.2f + 1.0f))                /* 0,1086956522 */

/* Os 4 CIs, um handle de dispositivo por CS. */
static spi_device_handle_t s_dev[M4_N_ADCS];
static bool                 s_m4_ready = false;

/* ---------------------------------------------------------------------------
 * m4_adc_init — configura o barramento SPI e anexa os 4 MCP3208.
 *
 * Nao testado. O barramento e o mesmo do IMU (o barometro e I2C, nao mora
 * aqui), e o plano reconhece que essa disputa e um problema em aberto
 * (RF-09); aqui ele e ocupado integralmente pelos 4 ADCs, o que e uma
 * escolha de esqueleto e nao uma decisao de arquitetura fechada.
 * ------------------------------------------------------------------------ */
esp_err_t m4_adc_init(void)
{
    ESP_LOGI(TAG_M4, "M4: init SPI a %d Hz para %d MCP3208", M4_SPI_CLK_HZ,
             M4_N_ADCS);

    spi_bus_config_t bus = {
        .mosi_io_num     = ADC_SPI_MOSI_GPIO,
        .miso_io_num     = ADC_SPI_MISO_GPIO,
        .sclk_io_num     = ADC_SPI_SCK_GPIO,
        .quadwp_io_num   = -1,
        .quadhd_io_num   = -1,
        .max_transfer_sz = M4_SPI_FRAME_BYTES,
    };
    ESP_RETURN_ON_ERROR(spi_bus_initialize(M4_SPI_HOST, &bus, SPI_DMA_CH_AUTO),
                        "m4_adc", "falha ao inicializar o barramento SPI");

    const int cs_gpio[M4_N_ADCS] = {
        ADC_CS1_GPIO, ADC_CS2_GPIO, ADC_CS3_GPIO, ADC_CS4_GPIO,
    };

    for (int i = 0; i < M4_N_ADCS; i++) {
        spi_device_interface_config_t dev = {
            .command_bits   = 0,    /* F4: nada de fase de comando — o quadro
                                      * inteiro do MCP3208 vai no buffer de
                                      * dados da transacao full-duplex.     */
            .address_bits   = 0,
            .dummy_bits     = 0,
            .mode           = 0,   /* MCP3208: CPOL=0, CPHA=0, MSB primeiro */
            .clock_source   = SPI_CLK_SRC_DEFAULT,  /* APB 80 MHz no S3      */
            .clock_speed_hz = M4_SPI_CLK_HZ,
            .spics_io_num   = cs_gpio[i],  /* CS por dispositivo, do board_pins */
            .queue_size     = 1,
            .flags          = 0,   /* F4: full-duplex; SPI_DEVICE_HALFDUPLEX
                                      * foi REMOVIDO — o MCP3208 devolve o
                                      * dado nos mesmos clocks do comando.  */
        };
        ESP_RETURN_ON_ERROR(spi_bus_add_device(M4_SPI_HOST, &dev, &s_dev[i]),
                            "m4_adc", "falha ao anexar um MCP3208");
    }

    s_m4_ready = true;
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m4_adc_read_raw — uma conversao de um canal de um CI.
 *
 * Sem multiplexacao entre CS: o protocolo do MCP3208 fixa o canal nos 3
 * primeiros bits do quadro, entao cada transacao carrega o endereco do canal.
 * ------------------------------------------------------------------------ */
esp_err_t m4_adc_read_raw(uint8_t adc_index, uint8_t channel, uint16_t *out_raw)
{
    if (!s_m4_ready || out_raw == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    if (adc_index >= M4_N_ADCS || channel >= M4_MCP3208_ADC_CHANNELS) {
        return ESP_ERR_INVALID_ARG;
    }

    /* Quadro single-ended do canal `channel` — ver o bloco de protocolo no
     * topo do arquivo (F4): start+SGL+D2 no byte 0, D1/D0 no byte 1. */
    const uint8_t tx[M4_SPI_FRAME_BYTES] = {
        (uint8_t)(0x06u | (channel >> 2)),
        (uint8_t)((channel & 0x03u) << 6),
        0x00u,
    };
    uint8_t rx[M4_SPI_FRAME_BYTES] = { 0u, 0u, 0u };

    spi_transaction_t trans = {
        .length    = M4_SPI_FRAME_BITS,   /* 24 bits, full-duplex       */
        .rxlength  = 0,                   /* 0 = recebe `length` bits   */
        .tx_buffer = tx,
        .rx_buffer = rx,
    };
    ESP_RETURN_ON_ERROR(spi_device_polling_transmit(s_dev[adc_index], &trans),
                        "m4_adc", "falha na transacao SPI");

    /* B11..B8 nos 4 bits baixos de rx[1]; B7..B0 em rx[2] (F4). */
    *out_raw = (uint16_t)((((uint16_t)(rx[1] & 0x0Fu) << 8) | rx[2]) & 0x0FFFu);
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * m4_adc_poll — round-robin: uma leitura por chamada, de um canal por vez.
 *
 * Esta e a saida que o RF-09 aponta: nao tentar as 24 leituras de uma vez, e
 * intercalar uma leitura por ciclo, com o barramento ocupado pelo menor tempo
 * possivel. O chamador e que decide a cadencia; a funcao nao bloqueia por mais
 * que uma conversao.
 *
 * Nao ha leitura simultanea de fase possivel aqui (RF-02): o MCP3208 multiplexa
 * e as 3 fases sao lidas em 3 instantes diferentes. Qualquer algoritmo de
 * controle que dependa de amostragem simultanea nao pode ser escrito em cima
 * desta topologia sem trocar o ADC.
 *
 * Baixo da auditoria (registrado, nao corrigido com armadura): s_circuito e
 * s_canal sao estaticos e assumem UM UNICO chamador. Este esqueleto so tem a
 * task_de_Leitura chamando aqui; se algum dia mais de uma task usar o M4,
 * precisa de exclusao mutua em volta do par (indice, leitura).
 * ------------------------------------------------------------------------ */
esp_err_t m4_adc_poll(uint8_t *state)
{
    static uint8_t s_circuito;   /* indice do CI na varredura round-robin */
    static uint8_t s_canal;      /* canal dentro do CI                   */

    uint16_t raw = 0;
    ESP_RETURN_ON_ERROR(m4_adc_read_raw(s_circuito, s_canal, &raw),
                        "m4_adc", "falha na leitura do MCP3208");

    if (state != NULL) {
        /* state[0] = circuito, state[1] = canal, state[2..3] = raw em LSB-first */
        state[0] = s_circuito;
        state[1] = s_canal;
        state[2] = (uint8_t)(raw & 0xFFu);
        state[3] = (uint8_t)(raw >> 8);
    }

    /* Avanca a varredura: um canal por chamada. */
    s_canal++;
    if (s_canal >= M4_MCP3208_ADC_CHANNELS) {
        s_canal = 0;
        s_circuito++;
        if (s_circuito >= M4_N_ADCS) {
            s_circuito = 0;
        }
    }
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * Conversoes de um LSB para as unidades fisicas.
 *
 * Sao funcoes de CONVERSAO, nao de CALIBRACAO. O criterio de aceite do M4 exige
 * linearity < 2 % entre 5 e 30 A e erro < 1 % em BEMF, e nenhum dos dois e
 * verificavel aqui: o INA240A2 tem erro de ganho de +-0,05 % tipico e ate
 * +-0,20 % maximo, mais um offset de ate 2,42 mV no MCP3208 (WP3 P-13). Esses
 * numeros so fecham com a fonte em bancada.
 * ------------------------------------------------------------------------ */

/* raw (0-4095) -> corrente, em amperes, assumindo VREF = VDD3P3 = 3,300 V. */
float m4_raw_to_ampere(uint16_t raw)
{
    const float v_saida = ((float)raw * 3.300f) / 4095.0f;
    return v_saida * M4_AMP_A_POR_VOLT;
}

/* raw (0-4095) -> tensao de fase (BEMF), em volts, atraves do divisor. */
float m4_raw_to_bemf(uint16_t raw)
{
    const float v_saida = ((float)raw * 3.300f) / 4095.0f;
    return v_saida / M4_BEMF_RATIO;
}

/* ---------------------------------------------------------------------------
 * m4_adc_log_offset_zero — le o canal de corrente com zero A corrente e
 * guarda o resultado como offset a subtrair.
 *
 * O criterio de aceite do M4 exige o offset a 0 A "anotado e subtraido", e
 * o plano registra que o offset do MCP3208 chega a +-2,42 mV no pior caso do
 * datasheet. A funcao existe para tornar esse passo obrigatorio e nao opcional.
 * Nao foi executada: nao ha fonte de corrente nem placa conectada a esta
 * maquina.
 * ------------------------------------------------------------------------ */
esp_err_t m4_adc_log_offset_zero(uint8_t adc_index, uint8_t channel,
                                 uint16_t *out_offset_raw)
{
    uint16_t raw = 0;
    ESP_RETURN_ON_ERROR(m4_adc_read_raw(adc_index, channel, &raw),
                        "m4_adc", "falha na leitura do offset");
    if (out_offset_raw != NULL) {
        *out_offset_raw = raw;
    }
    /* Correcao de unidade (achado ao revisar F4): m4_raw_to_ampere devolve
     * AMPERES (40 A/V — ver M4_AMP_A_POR_VOLT); o log antigo rotulava o
     * valor como "mA", errando o numero em 1000x. */
    ESP_LOGW(TAG_M4, "offset 0 A: CI %u canal %u = %u LSB (%.3f A equivalentes)",
             (unsigned)adc_index, (unsigned)channel, (unsigned)raw,
             (double)m4_raw_to_ampere(raw));
    return ESP_OK;
}
