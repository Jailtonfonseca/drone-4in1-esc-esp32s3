`timescale 1ns/1ps
//=====================================================================
// tb_pwm.v -- testbench do pwm_deadtime
//---------------------------------------------------------------------
//  1) clock 160 MHz
//  2) varredura de duty: 0 / 5 / 50 / 94 / 100 %  (e 10/4095 p/ DUTY_MIN)
//  3) monitor de shoot-through: conta qualquer ciclo com hi&lo != 0
//  4) medicao do dead-time efetivo (subida e descida) em ns
//  5) medicao da frequencia real e da defasagem entre os 4 grupos
//  6) VCD (dump somente na janela de analise)
//=====================================================================
module tb_pwm;

    // ---------------- clock 160 MHz ----------------
    reg clk = 1'b0;
    always #3.125 clk = ~clk;          // periodo = 6,25 ns

    reg          rst_n      = 1'b0;
    reg [143:0]  duty_i     = 144'd0;  // 12 canais x 12 bits
    reg [15:0]   deadtime_i = 16'd83;  // 83 ciclos = 518,75 ns

    wire [11:0] pwm_o, hi_o, lo_o;

    pwm_deadtime #(.DEADTIME_CYCLES(83), .PERIOD(8000)) dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .duty_i    (duty_i),
        .deadtime_i(deadtime_i),
        .pwm_o     (pwm_o),
        .hi_o      (hi_o),
        .lo_o      (lo_o)
    );

    // ---------------- observaveis globais ----------------
    integer shot_count = 0;            // violacoes de shoot-through
    integer duty_in_val;               // auxiliar do sweep
    integer i;
    real    duty_meas;
    integer high_cnt;

    // ---------------------------------------------------------------
    // PROVA 1 -- ausencia de shoot-through em TODO o tempo de simulacao
    // ---------------------------------------------------------------
    always @(posedge clk) begin
        if ((hi_o & lo_o) != 12'd0) begin
            shot_count = shot_count + 1;
            $display("[SHOOT-THROUGH] t=%0t ns  canal hi&lo=%b", $time, hi_o & lo_o);
        end
    end

    // ---------------------------------------------------------------
    // Captura de bordas para medida de dead-time (via flags, sem race)
    // ---------------------------------------------------------------
    reg   dt_en     = 1'b0;
    reg   got_lof   = 1'b0, got_hir = 1'b0;
    real  t_lof, t_hir;
    always @(negedge lo_o[0]) if (dt_en && !got_lof) begin
        t_lof = $realtime; got_lof = 1'b1;
    end
    always @(posedge hi_o[0]) if (dt_en && got_lof && !got_hir) begin
        t_hir = $realtime; got_hir = 1'b1;
    end

    reg   dt_en2    = 1'b0;
    reg   got_hif   = 1'b0, got_lor = 1'b0;
    real  t_hif, t_lor;
    always @(negedge hi_o[0]) if (dt_en2 && !got_hif) begin
        t_hif = $realtime; got_hif = 1'b1;
    end
    always @(posedge lo_o[0]) if (dt_en2 && got_hif && !got_lor) begin
        t_lor = $realtime; got_lor = 1'b1;
    end

    // ---------------------------------------------------------------
    // Captura da 1a borda de subida de cada grupo (0,3,6,9) apos armar
    // ---------------------------------------------------------------
    reg  ph_en = 1'b0;
    reg  g0=1'b0, g3=1'b0, g6=1'b0, g9=1'b0;
    real t0, t3, t6, t9;
    always @(posedge hi_o[0])  if (ph_en && !g0) begin t0 = $realtime; g0 = 1'b1; end
    always @(posedge hi_o[3])  if (ph_en && !g3) begin t3 = $realtime; g3 = 1'b1; end
    always @(posedge hi_o[6])  if (ph_en && !g6) begin t6 = $realtime; g6 = 1'b1; end
    always @(posedge hi_o[9])  if (ph_en && !g9) begin t9 = $realtime; g9 = 1'b1; end

    // ---------------------------------------------------------------
    // Task: aplica um duty nos 12 canais e mede o duty real do canal 0
    //       (conta ciclos de clk com pwm_o[0]=1 em 5 periodos = 40000 ciclos)
    // ---------------------------------------------------------------
    task sweep_one;
        input [11:0] d;
        begin
            duty_i = {12{d}};
            @(posedge clk);
            repeat (3) @(posedge clk);      // deixa estabilizar
            high_cnt = 0;
            for (i = 0; i < 40000; i = i + 1) begin
                if (pwm_o[0]) high_cnt = high_cnt + 1;
                @(posedge clk);
            end
            duty_meas = 100.0 * high_cnt / 40000.0;
            $display("[SWEEP] duty_in=%4d/4095 (%7.3f %%) -> pwm_o[0] alto %5d/40000 = %7.3f %%  (max=%0d)",
                     d, 100.0*d/4095.0, high_cnt, duty_meas, high_cnt/5);
        end
    endtask

    real per_a, per_b, period_ns, freq_hz;
    real d3, d6, d9;

    // ---------------------------------------------------------------
    initial begin
        $dumpfile("tb_pwm.vcd");
        $dumpvars(0, tb_pwm);
        $dumpoff;                          // liga so na janela de analise
        $timeformat(-9, 3, " ns", 12);     // $realtime em ns

        $display("================================================================");
        $display(" tb_pwm -- pwm_deadtime  (clk 160 MHz, PERIOD=8000 -> 20 kHz)");
        $display(" dead-time programado = 83 ciclos = %0.2f ns", 83*6.25);
        $display("================================================================");

        // reset
        rst_n = 1'b0;
        repeat (10) @(posedge clk);
        rst_n = 1'b1;
        repeat (10) @(posedge clk);

        // ---------- PROVA 2: varredura de duty ----------
        $display("\n--- Varredura de duty (12 canais iguais) ---");
        sweep_one(12'd0);      // 0 %
        sweep_one(12'd10);     // 0,24 % -> deve ser limitado por DUTY_MIN
        sweep_one(12'd205);    // 5 %
        sweep_one(12'd2047);   // 50 %
        sweep_one(12'd3850);   // 94 %
        sweep_one(12'd4095);   // 100 % -> deve ser limitado por DUTY_MAX

        // ---------- PROVA 3: dead-time ----------
        $display("\n--- Dead-time efetivo (canal 0 @ 50%% duty) ---");
        duty_i = {12{12'd2047}};
        dt_en = 1'b1; dt_en2 = 1'b1;
        repeat (4) @(posedge clk);
        wait (got_hir && got_lor);
        $display("[DEADTIME] subida : lo cai em %0.3f ns, hi sobe em %0.3f ns -> dt = %0.3f ns",
                 t_lof, t_hir, t_hir - t_lof);
        $display("[DEADTIME] descida: hi cai em %0.3f ns, lo sobe em %0.3f ns -> dt = %0.3f ns",
                 t_hif, t_lor, t_lor - t_hif);
        dt_en = 1'b0; dt_en2 = 1'b0;

        // ---------- PROVA 4: frequencia real ----------
        $display("\n--- Frequencia real (periodo entre subidas de hi_o[0]) ---");
        @(posedge hi_o[0]); per_a = $realtime;
        @(posedge hi_o[0]); per_b = $realtime;
        period_ns = per_b - per_a;
        freq_hz   = 1.0e9 / period_ns;
        $display("[FREQ] periodo medido = %0.3f ns  ->  f = %0.1f Hz  (%0.4f kHz)",
                 period_ns, freq_hz, freq_hz/1000.0);

        // ---------- PROVA 5: defasagem entre os 4 grupos ----------
        $display("\n--- Defasagem das 4 portadoras (grupos 0,3,6,9) ---");
        ph_en = 1'b1;
        wait (g0 && g3 && g6 && g9);
        ph_en = 1'b0;
        // normaliza em [0, periodo)
        d3 = t3 - t0;  if (d3 < 0)      d3 = d3 + period_ns;  if (d3 >= period_ns) d3 = d3 - period_ns;
        d6 = t6 - t0;  if (d6 < 0)      d6 = d6 + period_ns;  if (d6 >= period_ns) d6 = d6 - period_ns;
        d9 = t9 - t0;  if (d9 < 0)      d9 = d9 + period_ns;  if (d9 >= period_ns) d9 = d9 - period_ns;
        $display("[PHASE] grupo0->3 = %0.3f ns (%0.3f graus)", d3, 360.0*d3/period_ns);
        $display("[PHASE] grupo0->6 = %0.3f ns (%0.3f graus)", d6, 360.0*d6/period_ns);
        $display("[PHASE] grupo0->9 = %0.3f ns (%0.3f graus)", d9, 360.0*d9/period_ns);

        // ---------- PROVA 6: dead-time programavel (40 ciclos) ----------
        $display("\n--- Programabilidade do dead-time (40 ciclos = 250 ns) ---");
        deadtime_i = 16'd40;
        got_lof = 1'b0; got_hir = 1'b0; dt_en = 1'b1;
        repeat (4) @(posedge clk);
        wait (got_hir);
        $display("[DEADTIME] 40 ciclos -> medido %0.3f ns", t_hir - t_lof);
        dt_en = 1'b0;
        deadtime_i = 16'd83;
        repeat (4) @(posedge clk);

        // ---------- PROVA 7: estresse (duty e dead-time mudando a cada ciclo) ----------
        $display("\n--- Estresse: duty pseudo-aleatorio (12 canais) + dead-time 0..255 ciclos ---");
        for (i = 0; i < 60000; i = i + 1) begin
            duty_i = {$random, $random, $random, $random, $random};  // 144 bits
            deadtime_i = $random & 16'h00FF;                        // 0..255
            @(posedge clk);
        end
        $display("[STRESS] 60000 ciclos com duty/dead-time aleatorios -> violacoes ate aqui = %0d",
                 shot_count);
        deadtime_i = 16'd83;

        // ---------- Janela de VCD ----------
        duty_i = {12{12'd2047}};           // 50 %
        repeat (4) @(posedge clk);
        $dumpon;                            // ~3 periodos de portadora
        repeat (24000) @(posedge clk);
        $dumpoff;

        // ---------- RESULTADO ----------
        $display("\n================================================================");
        $display(" [RESULTADO] violacoes de shoot-through (hi & lo) = %0d", shot_count);
        $display(" [RESULTADO] tempo total simulado = %0.3f us  (%0.0f ciclos de 6,25 ns @160 MHz)",
                 $realtime/1000.0, $realtime/6.25);
        $display(" [RESULTADO] checagem executada em TODOS os %0.0f ciclos", $realtime/6.25);
        $display("================================================================");
        $finish;
    end

    // timeout de seguranca
    initial begin
        #5000000;                           // 5 ms
        $display("[TIMEOUT] a simulacao nao terminou em 5 ms");
        $finish;
    end

endmodule
