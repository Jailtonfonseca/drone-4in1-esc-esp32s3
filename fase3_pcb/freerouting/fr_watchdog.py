#!/usr/bin/env python3
"""
fr_watchdog.py -- mantem o FreeRouting 1.9.0 rodando em modo batch headless.

O FreeRouting 1.9.0 abre JOptionPane MODAIS que ninguem clica quando roda
dentro de um Xvfb:
  * "DSN file reader - Freerouting" (import_design: abre se a leitura gerou
    QUALQUER warning ou error; BoardHandling.java:870) -- trava o batch
    inteiro antes do primeiro passe;
  * dialogo de auto-start (tem timeout via freerouting.json);
  * quaisquer dialogos de erro.
Sem este watchdog, o processo fica em futex_wait (Object.wait do AWT) para
sempre e nunca escreve o .ses.  Medido em 2026-10-03: run de 2026-09-28 e
run de hoje, ambos mortos por isso.

Como usa: rodar em background NA MESMA maquina do roteador.  Ele descobre o
display do Xvfb e o Xauthority pelo /proc, e aperta Return na janela que
tiver o foco de teclado sempre que essa janela nao for o board principal.

  /root/.qwenpaw/venv/bin/python3 fr_watchdog.py [--interval 2]

(dispensa pcbnew; precisa de python-xlib, `uv pip install python-xlib`)
"""
import argparse
import os
import re
import subprocess
import sys
import time

from Xlib import display as xdisplay, X
from Xlib.ext import xtest


def find_xvfb():
    """Retorna (display, xauth_path) do Xvfb vivo, ou (None, None)."""
    try:
        out = subprocess.run(["ps", "-eo", "args"], capture_output=True,
                             text=True, timeout=5).stdout
    except Exception:
        return None, None
    for line in out.splitlines():
        if line.startswith("Xvfb ") and "-auth" in line:
            m = re.search(r":(\d+)", line)
            a = re.search(r"-auth\s+(\S+)", line)
            if m and a and os.path.exists(a.group(1)):
                return ":%s" % m.group(1), a.group(1)
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--max-dismiss", type=int, default=500)
    a = ap.parse_args()

    dismissed = 0
    print("watchdog: aguardando Xvfb do FreeRouting...", flush=True)
    while dismissed < a.max_dismiss:
        dnum, xauth = find_xvfb()
        if not dnum:
            time.sleep(a.interval)
            continue
        os.environ["XAUTHORITY"] = xauth
        try:
            d = xdisplay.Display(dnum)
        except Exception:
            time.sleep(a.interval)
            continue
        try:
            root = d.screen().root
            focus = d.get_input_focus().focus
            # python-xlib pode devolver int (id da janela) em vez de Window
            if isinstance(focus, int):
                focus_id = focus
            else:
                focus_id = focus.id
            # nome da janela com foco e das mapeadas
            def wname(w):
                try:
                    return w.get_wm_name() or ""
                except Exception:
                    return ""
            mapped = []
            for wid in root.query_tree().children:
                try:
                    if wid.get_attributes().map_state == 2:
                        mapped.append((wid, wname(wid)))
                except Exception:
                    pass
            board_frames = [w for (w, n) in mapped
                            if "Board Layout" in n or "MainApplication" in n]
            focus_is_board = any(focus_id == w.id for w in board_frames)
            # foco num dialogo (nao no board principal) -> aperta Return
            if mapped and not focus_is_board and focus_id != root.id:
                try:
                    focus_win = d.create_resource_object("window", focus_id)
                    nm = wname(focus_win)
                except Exception:
                    nm = "?"
                xtest.fake_input(d, X.KeyPress, 36)   # Return
                d.sync()
                xtest.fake_input(d, X.KeyRelease, 36)
                d.sync()
                dismissed += 1
                print("watchdog: Return enviado ao dialogo %r (%d/%d)"
                      % (nm, dismissed, a.max_dismiss), flush=True)
                time.sleep(1.0)
        except Exception as e:
            print("watchdog: erro %r (continuando)" % e, flush=True)
        try:
            d.close()
        except Exception:
            pass
        time.sleep(a.interval)
    print("watchdog: encerrado (limite de dispensas)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
