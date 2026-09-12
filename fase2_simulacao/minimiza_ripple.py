#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
minimiza_ripple.py -- calculo ANALITICO do ripple de saida dos bucks
(usado como valor ESPERADO no relatorio; nada aqui vem de simulacao).

Modelo exato (CCM, corrente do indutor triangular):

    iL(t) = -dIL/2 + (dIL/tON)*t          para 0 <= t < tON   (chave alta ON)
    iL(t) = +dIL/2 - (dIL/(T-tON))*(t-tON) para tON <= t < T  (chave baixa ON)

    iC(t)  = iL(t) - <iL>            (o valor medio de iL e a corrente de carga)
    vC(t)  = (1/C) * integral(iC dt)  com constante escolhida p/ <vC> = 0
    vESR(t)= ESR * iC(t)
    vout(t)= vC(t) + vESR(t)
    Vpp    = max(vout) - min(vout)

O ponto importante: vC (parabolico) e vESR (triangular) NAO atingem o
maximo no mesmo instante, entao Vpp NAO e a soma dos dois pp.
"""


def ripple_pp(dIL, C, ESR, D, fsw, N=200000):
    T = 1.0 / fsw
    tON = D * T
    dt = T / N

    ic = []
    for k in range(N):
        t = k * dt
        if t < tON:
            i = -dIL / 2.0 + dIL * t / tON
        else:
            i = dIL / 2.0 - dIL * (t - tON) / (T - tON)
        ic.append(i)

    # integra iC para obter vC e retira a media (regime periodico)
    vC = []
    acc = 0.0
    for i in ic:
        acc += i * dt / C
        vC.append(acc)
    m = sum(vC) / N
    vC = [v - m for v in vC]

    vout = [vC[k] + ESR * ic[k] for k in range(N)]
    pp = max(vout) - min(vout)
    pp_C = max(vC) - min(vC)
    pp_E = ESR * (max(ic) - min(ic))
    return pp, pp_C, pp_E


def analitico_cap(dIL, C, fsw):
    """formula de livro: dIL/(8*C*fsw)"""
    return dIL / (8.0 * C * fsw)


CASOS = [
    # nome           dIL [A]      C [F]    ESR [ohm]  D      fsw [Hz]
    ("buck12",  0.1062364, 44e-6, 2.5e-3, 0.606, 500e3),
    ("buck5",   0.3432153, 44e-6, 2.5e-3, 0.417, 500e3),
    ("buck3v3", 0.4488,     44e-6, 2.5e-3, 0.660, 500e3),
]

print("=" * 78)
print("RIPPLE DE SAIDA -- calculo analitico (minimiza_ripple.py)")
print("=" * 78)
print("%-9s %12s %12s %12s %12s %10s" % (
    "caso", "dIL[A]", "Vpp_tot[mV]", "Vpp_C[mV]", "Vpp_ESR[mV]", "soma[mV]"))
for nome, dIL, C, ESR, D, fsw in CASOS:
    pp, pp_C, pp_E = ripple_pp(dIL, C, ESR, D, fsw)
    cap = analitico_cap(dIL, C, fsw)
    print("%-9s %12.7f %12.7f %12.7f %12.7f %12.7f  (Vpp_C formula=%9.7f)"
          % (nome, dIL, pp * 1e3, pp_C * 1e3, pp_E * 1e3,
             pp_C * 1e3 + pp_E * 1e3, cap * 1e3))
print("=" * 78)
print("Vpp_tot  = ripple real (vC + vESR somados ponto a ponto)")
print("soma     = Vpp_C + Vpp_ESR (SOBRESTIMA -- e o que daria somar os pp)")
print("=" * 78)
