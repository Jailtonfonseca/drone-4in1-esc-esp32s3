#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_pwm.py -- parser VCD simples + plot das formas de onda do pwm_deadtime.
Gera pwm_deadtime.png com 3 paineis:
  (a) zoom na borda de SUBIDA do canal 0  -> mostra o dead-time
  (b) zoom na borda de DESCIDA do canal 0 -> mostra o dead-time
  (c) as 4 portadoras defasadas (grupos 0,3,6,9) em 2 periodos

Nao usa vcdvcd (nao instalado): parser proprio.
"""
import sys, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VCD = "tb_pwm.vcd"
# ids dos vetores no escopo tb_pwm (12 bits cada): pwm_o, lo_o, hi_o
IDS = {"!": "pwm_o", '"': "lo_o", "#": "hi_o"}

def parse_vcd(path):
    """retorna (timescale_ps, {nome: list[(t,codigo)]}, {nome: largura})"""
    vals = {n: [] for n in IDS.values()}
    widths = {}
    last_t = 0
    ts_scale = 1  # ps
    in_ts = False
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = line[0]
            if c == "$":
                if line.startswith("$var"):
                    p = line.split()
                    if len(p) >= 5 and p[3] in IDS:
                        try:
                            widths[IDS[p[3]]] = int(p[2])
                        except ValueError:
                            pass
                    continue
                if line.startswith("$timescale"):
                    in_ts = True
                    rest = line[len("$timescale"):].strip()
                    if rest in ("$end", ""):
                        continue
                    m = re.match(r"(\d+)\s*([a-z]*)", rest)
                    if m:
                        ts_scale = int(m.group(1))
                        in_ts = False
                elif line.startswith("$end"):
                    in_ts = False
                continue
            if in_ts:
                m = re.match(r"(\d+)\s*([a-z]*)", line)
                if m:
                    ts_scale = int(m.group(1)); in_ts = False
                continue
            if c == "#":
                try:
                    last_t = int(line[1:])
                except ValueError:
                    pass
            elif c == "b" or c == "B":
                try:
                    v, sid = line[1:].split(None, 1)
                except ValueError:
                    continue
                sid = sid.strip()
                if sid in IDS:
                    v = v.replace("x", "0").replace("z", "0")
                    v = v.lstrip("0") or "0"
                    vals[IDS[sid]].append((last_t, int(v, 2)))
            elif c in "01" or c in "xXzZ":
                sid = line[1:].strip()
                if sid in IDS:
                    vals[IDS[sid]].append((last_t, 1 if c in "1xXzZ" else 0))
            # ignora r (real) e $dumpoff/$dumpon
    return ts_scale, vals, widths

def bits(vals_list, lsb_index, nbits=12):
    """extrai o bit lsb_index de um vetor embutido -> list[(t,b)]"""
    out = []
    prev = None
    for t, w in vals_list:
        b = (w >> lsb_index) & 1
        if b != prev:
            out.append((t, b))
            prev = b
    return out

def to_step(times_vals, t0, t1):
    xs, ys = [], []
    cur = 0
    for t, b in times_vals:
        if t <= t0:
            cur = b
        elif t < t1:
            xs.append(t); ys.append(cur)
            xs.append(t); ys.append(b)
            cur = b
        else:
            break
    if not xs:
        return [t0, t1], [cur, cur]
    xs = [t0] + xs + [t1]
    ys = [ys[0]] + ys + [ys[-1]]
    return xs, ys

def first_edge(vals_list, want, after=None):
    for t, b in vals_list:
        if b == want and (after is None or t >= after):
            return t
    return None

def edge_before(vals_list, want, t):
    """ultima transicao para 'want' antes de t (ou em t)"""
    res = None
    for tt, b in vals_list:
        if tt > t:
            break
        if b == want:
            res = tt
    return res

def main():
    ts, vals, widths = parse_vcd(VCD)
    print("timescale = 1/%g s ; larguras = %s" % (ts*1e-12, widths))

    N = 1000.0  # ps -> ns
    hi0 = bits(vals["hi_o"], 0)
    lo0 = bits(vals["lo_o"], 0)
    pm0 = bits(vals["pwm_o"], 0)
    if not hi0:
        sys.exit("sem dados de hi_o[0] no VCD")

    t_start = hi0[0][0]
    # primeira subida de hi_o[0] (0->1) depois do inicio da janela
    t_rise = first_edge(hi0, 1, after=t_start + 100)
    t_fall = first_edge(hi0, 0, after=t_rise + 100)
    print("t_rise = %.3f ns ; t_fall = %.3f ns" % (t_rise/N, t_fall/N))

    # dead-time medido a partir do VCD (nao do log): lo cai -> hi sobe
    lo_fall = edge_before(lo0, 0, t_rise)          # lo caiu logo antes de hi subir
    lo_rise = first_edge(lo0, 1, after=t_fall)     # lo subiu logo apos hi cair
    dt_up = (t_rise - lo_fall) / N
    dt_dn = (lo_rise - t_fall) / N
    print("VCD: dt_subida = %.3f ns ; dt_descida = %.3f ns" % (dt_up, dt_dn))

    fig, ax = plt.subplots(3, 1, figsize=(14, 12))

    # ---------- (a) zoom subida ----------
    a = ax[0]
    w0, w1 = t_rise - 900*N, t_rise + 900*N
    for seq, lbl, col, off in ((pm0, "pwm_o[0] (comando logico)", "#888888", 2.4),
                               (lo0, "lo_o[0] (low-side)", "#1f77b4", 1.4),
                               (hi0, "hi_o[0] (high-side)", "#d62728", 0.4)):
        xs, ys = to_step(seq, w0, w1)
        a.plot([x/N for x in xs], [y+off for y in ys], color=col, lw=1.8, label=lbl)
    a.axvline(lo_fall/N, color="#1f77b4", ls=":", lw=1.2)
    a.axvline(t_rise/N, color="#d62728", ls=":", lw=1.2)
    a.annotate("", xy=(lo_fall/N, 3.15), xytext=(t_rise/N, 3.15),
               arrowprops=dict(arrowstyle="<->", color="k", lw=1.3))
    a.text((lo_fall+t_rise)/(2*N), 3.25,
           "dead-time = %.3f ns" % dt_up, ha="center", fontsize=11, weight="bold")
    a.set_title("(a) Borda de SUBIDA - canal 0 - inserção de dead-time (83 ciclos @160 MHz)")
    a.set_xlim(w0/N, w1/N); a.set_ylim(-0.3, 3.9)
    a.set_yticks([0.4, 1.4, 2.4]); a.set_yticklabels(["hi_o[0]", "lo_o[0]", "pwm_o[0]"])
    a.grid(alpha=0.3); a.set_xlabel("tempo (ns)")

    # ---------- (b) zoom descida ----------
    b = ax[1]
    w0, w1 = t_fall - 900*N, t_fall + 900*N
    for seq, lbl, col, off in ((pm0, "pwm_o[0]", "#888888", 2.4),
                               (hi0, "hi_o[0]", "#d62728", 1.4),
                               (lo0, "lo_o[0]", "#1f77b4", 0.4)):
        xs, ys = to_step(seq, w0, w1)
        b.plot([x/N for x in xs], [y+off for y in ys], color=col, lw=1.8, label=lbl)
    b.axvline(t_fall/N, color="#d62728", ls=":", lw=1.2)
    b.axvline(lo_rise/N, color="#1f77b4", ls=":", lw=1.2)
    b.annotate("", xy=(t_fall/N, 3.15), xytext=(lo_rise/N, 3.15),
               arrowprops=dict(arrowstyle="<->", color="k", lw=1.3))
    b.text((t_fall+lo_rise)/(2*N), 3.25,
           "dead-time = %.3f ns" % dt_dn, ha="center", fontsize=11, weight="bold")
    b.set_title("(b) Borda de DESCIDA - canal 0 - hi e lo nunca altos juntos (0 violações)")
    b.set_xlim(w0/N, w1/N); b.set_ylim(-0.3, 3.9)
    b.set_yticks([0.4, 1.4, 2.4]); b.set_yticklabels(["lo_o[0]", "hi_o[0]", "pwm_o[0]"])
    b.grid(alpha=0.3); b.set_xlabel("tempo (ns)")

    # ---------- (c) 4 portadoras defasadas ----------
    c = ax[2]
    period = 50000.0 * N  # 50 us em ps
    t_ref = t_rise
    w0, w1 = t_ref - 6000*N, t_ref + 2.0*period
    groups = [(0, "#1f77b4"), (3, "#ff7f0e"), (6, "#2ca02c"), (9, "#9467bd")]
    for gi, (ch, col) in enumerate(groups):
        seq = bits(vals["hi_o"], ch)
        xs, ys = to_step(seq, w0, w1)
        c.plot([(x-t_ref)/N for x in xs], [y*0.8 + (3-gi)*1.1 for y in ys],
               color=col, lw=1.6, label="hi_o[%d]  (motor %d)" % (ch, gi+1))
    for k in range(0, 4):
        dx = k*period/4
        c.axvline(dx/N, color="k", ls=":", lw=0.9, alpha=0.55)
        c.text(dx/N + 700, 4.28, "%d°" % (90*k), fontsize=9, color="k")
    c.annotate("", xy=(0, -0.35), xytext=(period/N, -0.35),
               arrowprops=dict(arrowstyle="<->", color="#444", lw=1.1))
    c.text((period/N)/2, -0.32, "T = 50 µs  ->  20 kHz", ha="center", fontsize=9, color="#444")
    c.set_title("(c) 4 portadoras defasadas 90\u00B0 entre si (2 períodos = 100 µs, 20 kHz)")
    c.set_xlim(-6000, 2.0*period/N); c.set_ylim(-0.4, 4.5)
    c.set_yticks([0.4, 1.5, 2.6, 3.7])
    c.set_yticklabels(["hi_o[9]\nmotor 4", "hi_o[6]\nmotor 3", "hi_o[3]\nmotor 2", "hi_o[0]\nmotor 1"])
    c.set_xlabel("tempo relativo à subida de hi_o[0] (ns)")
    c.grid(alpha=0.3); c.legend(loc="upper right", fontsize=9)

    plt.tight_layout(rect=[0.02, 0.02, 1, 1])
    plt.savefig("pwm_deadtime.png", dpi=110)
    print("OK -> pwm_deadtime.png")

if __name__ == "__main__":
    main()
