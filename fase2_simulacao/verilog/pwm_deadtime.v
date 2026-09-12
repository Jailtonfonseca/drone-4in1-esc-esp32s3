`timescale 1ns/1ps
//=====================================================================
// pwm_deadtime.v  --  12 canais PWM trifasicos com dead-time programavel
//---------------------------------------------------------------------
// Contexto: drone 4x ESC trifasico -> 24 half-bridges -> 12 canais PWM
//           (1 pino PWM por half-bridge) + 12 pares complementares.
//   clk         : 160 MHz  (6,25 ns)
//   PERIOD      : 8000 ciclos = 50 us  -> 20 kHz  [PREMISSA P-07]
//   DEADTIME    : 83 ciclos = 518,75 ns ~ 520 ns (referencia)
//   defasagem   : 90 graus de portadora entre os 4 grupos de motor
//                 (interleaving decidido na Fase 0, secao 4.3)
//
// Arquitetura:
//   - 1 contador mestre de fase 0..PERIOD-1 (sawtooth) que roda 1x por
//     periodo. As 4 portadoras triangulares sao derivadas dele somando
//     g*(PERIOD/4) e dobrando o triangulo -> defasagem exata de 90 graus,
//     sem 4 contadores independentes (nao ha risco de drift entre eles).
//   - comparacao tri_g < dthr  -> pwm logico (1 pulso centrado por periodo)
//   - 1 submodulo de dead-time por canal (12 instancias via generate)
//   - limites de duty: DUTY_MAX protege a reposicao do bootstrap
//     (low-side precisa conduzir um minimo por periodo);
//     DUTY_MIN garante que o pulso do high-side seja maior que o proprio
//     dead-time (senao o pulso seria engolido e nunca apareceria em hi_o).
//
// Garantia estrutural hi/lo: hi=1 SO se pwm_in ficou em 1 por >= dt_cycles
//   ciclos consecutivos; lo=1 SO se pwm_in ficou em 0 por >= dt_cycles
//   ciclos consecutivos. Como pwm_in nao pode ser 1 e 0 ao mesmo tempo,
//   hi e lo nunca podem ser 1 simultaneamente. Nao depende de $assert.
//=====================================================================
module pwm_deadtime #(
    parameter DEADTIME_CYCLES = 83,     // 83/160e6 = 518,75 ns  (~520 ns)
    parameter PERIOD          = 8000,   // ciclos do periodo COMPLETO (50 us)
    parameter DUTY_W          = 12,     // resolucao de duty (0..4095)
    parameter DUTY_MIN_CODE   = 82,     // 2,0 %  -> 82*4000/4095 = 80 ciclos
    parameter DUTY_MAX_CODE   = 3890    // 95,0 % -> reposicao do bootstrap
)(
    input  wire                 clk,        // 160 MHz
    input  wire                 rst_n,      // reset ativo baixo (hi=lo=0)
    input  wire [12*DUTY_W-1:0] duty_i,     // 12 x DUTY_W bits (0..4095)
    input  wire [15:0]          deadtime_i, // dead-time em ciclos (runtime)
    output wire [11:0]          pwm_o,      // PWM logico (ANTES do dead-time)
    output wire [11:0]          hi_o,       // gate high-side do half-bridge
    output wire [11:0]          lo_o        // gate low-side  do half-bridge
);

    localparam integer HALF      = PERIOD / 2;      // 4000
    localparam integer PHOFF     = PERIOD / 4;      // 2000 ciclos = 90 graus
    localparam integer DUTY_FULL = (1 << DUTY_W) - 1; // 4095

    //-----------------------------------------------------------------
    // Contador mestre de fase: 0 .. PERIOD-1, exatamente PERIOD ciclos
    //-----------------------------------------------------------------
    reg [15:0] phase_cnt;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)                     phase_cnt <= 16'd0;
        else if (phase_cnt == PERIOD-1) phase_cnt <= 16'd0;
        else                            phase_cnt <= phase_cnt + 16'd1;
    end

    //-----------------------------------------------------------------
    // Registrador de dead-time (valor de reset = parametro, programavel
    // em runtime pelo port deadtime_i)
    //-----------------------------------------------------------------
    reg [15:0] dt_cycles;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) dt_cycles <= DEADTIME_CYCLES[15:0];
        else        dt_cycles <= deadtime_i;
    end

    //-----------------------------------------------------------------
    // 12 canais: cada canal pertence a um grupo de motor (grupo = c/3)
    //-----------------------------------------------------------------
    genvar c;
    generate
        for (c = 0; c < 12; c = c + 1) begin : g_canal
            localparam integer GRP = c / 3;              // 0..3
            localparam integer OFF = GRP * PHOFF;        // 0/2000/4000/6000

            // porta do canal dentro do periodo mestre
            wire [15:0] ph  = (phase_cnt + OFF >= PERIOD) ?
                              (phase_cnt + OFF - PERIOD) :
                              (phase_cnt + OFF);
            // triangulo 0..HALF..0 (dobra o sawtooth)
            wire [15:0] tri_w = (ph < HALF) ? ph : (PERIOD - ph);

            // duty pedido, com limites aplicados
            wire [DUTY_W-1:0] duty_in = duty_i[c*DUTY_W +: DUTY_W];
            wire [15:0] duty_cl  = (duty_in == 0)               ? 16'd0 :
                                  (duty_in < DUTY_MIN_CODE)     ? DUTY_MIN_CODE :
                                  (duty_in > DUTY_MAX_CODE)     ? DUTY_MAX_CODE :
                                                                  duty_in;
            // limiar do comparador (32 bits: duty*4000 pode passar de 65535)
            wire [31:0] dthr = (duty_cl * 32'd4000) / DUTY_FULL;

            // 1 pulso por periodo (tri_w < dthr ocorre em torno da fase 0)
            assign pwm_o[c] = (tri_w < dthr);

            // insercao do dead-time
            pwm_dt_channel u_dt (
                .clk      (clk),
                .rst_n    (rst_n),
                .pwm_in   (pwm_o[c]),
                .dt_cycles(dt_cycles),
                .hi       (hi_o[c]),
                .lo       (lo_o[c])
            );
        end
    endgenerate

endmodule


//=====================================================================
// pwm_dt_channel -- 1 half-bridge: gera hi/lo complementares com
//                   dead-time entre eles. Saida do reset = ambos em 0.
//---------------------------------------------------------------------
// Regra de operacao (por ciclo de clk):
//   pwm_in = 1 : lo vai a 0 imediatamente; hi so vai a 1 depois de
//                dt_cycles ciclos com pwm_in = 1.
//   pwm_in = 0 : hi vai a 0 imediatamente; lo so vai a 1 depois de
//                dt_cycles ciclos com pwm_in = 0.
// Como hi exige pwm_in=1 estavel e lo exige pwm_in=0 estavel, os dois
// nunca podem estar em 1 no mesmo ciclo.
//=====================================================================
module pwm_dt_channel (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        pwm_in,
    input  wire [15:0] dt_cycles,
    output reg         hi,
    output reg         lo
);
    reg [15:0] dt_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hi     <= 1'b0;
            lo     <= 1'b0;      // estado seguro: os dois FETs desligados
            dt_cnt <= 16'd0;
        end
        else if (pwm_in) begin
            lo <= 1'b0;                                     // low-side OFF
            if (!hi) begin
                if (dt_cnt >= dt_cycles) begin             // dead-time vencido
                    hi     <= 1'b1;
                    dt_cnt <= 16'd0;
                end
                else dt_cnt <= dt_cnt + 16'd1;
            end
            else dt_cnt <= 16'd0;
        end
        else begin
            hi <= 1'b0;                                     // high-side OFF
            if (!lo) begin
                if (dt_cnt >= dt_cycles) begin             // dead-time vencido
                    lo     <= 1'b1;
                    dt_cnt <= 16'd0;
                end
                else dt_cnt <= dt_cnt + 16'd1;
            end
            else dt_cnt <= 16'd0;
        end
    end
endmodule
