#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
ses_import.py -- Le um .ses do FreeRouting e grava as trilhas no .kicad_pcb de entrada.

Roda com:  /usr/bin/python3.9 ses_import.py entrada.kicad_pcb entrada.ses saida.kicad_pcb

ESCALA (medida, nao adivinhada): o DSN que o FreeRouting le esta em mm, mas o SES que
ele escreve esta em micrometros -- `(place R1 4 6 ...)` no DSN vira `(place R1 4000 6000 ...)`
no SES. Logo: x_ses / 1000 = mm.

O SES tem duas formas de trilha:
  (wire (path <layer> <largura> x1 y1 x2 y2 ...))   -> segmento
  (via  <padstack> x y (net <n>))                  -> via
Cada `(path ...)` com N pontos gera N-1 segmentos.
"""
import sys
import os
import re
import argparse

import pcbnew

MM = 1000000.0
SES_TO_MM = 1000.0     # 1 coord de SES = 1 um; o DSN usa mm


def tokenize(text):
    """Tokenizador S-expression simples: ( ) e strings, respecting aspas."""
    i, n = 0, len(text)
    toks = []
    while i < n:
        c = text[i]
        if c in "()":
            toks.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(text[j])
                j += 1
            toks.append(("STR", "".join(buf)))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "()":
                j += 1
            toks.append(text[i:j])
            i = j
    return toks


def parse(toks, pos=0):
    """Retorna (lista_de_filhos, pos_dao_') a partir de um '(' na pos."""
    assert toks[pos] == "("
    pos += 1
    items = []
    while pos < len(toks):
        t = toks[pos]
        if t == ")":
            return items, pos + 1
        if t == "(":
            sub, pos = parse(toks, pos)
            items.append(sub)
        else:
            items.append(t)
            pos += 1
    return items, pos


def is_num(t):
    try:
        float(t)
        return True
    except (TypeError, ValueError):
        return False


def walk_ses(root):
    """Extrai [(kind, layer, width_um, [(x_mm, y_mm), ...], net)] do SES."""
    out = []
    for item in root:
        if not isinstance(item, list):
            continue
        head = item[0] if item and isinstance(item[0], str) else None
        if head == "routes":
            out.extend(walk_routes(item))
    return out


def walk_routes(routes):
    res = []
    for item in routes:
        if not isinstance(item, list):
            continue
        if item and item[0] == "network_out":
            res.extend(walk_net(item))
    return res


def walk_net(net):
    """[FIX 2026-10-04] formato REAL do FR 1.9.0:

        (network_out
          (net NOME
            (wire (path LAYER W x1 y1 ...))
            (via PADSTACK x y (net NOME))
          )
        )

    A versao anterior procurava (wire)/(via) DIRETO sob network_out e o nome
    da net em net[1] -- nunca achava nada (itens no SES: 0). O nome da net
    esta UM nivel abaixo, dentro de cada escopo (net NOME ...), e os
    wires/vias sao filhos DESTE. Strings quotadas chegam como ("STR", valor).
    """
    def _s(tok):
        return tok[1] if isinstance(tok, tuple) else tok

    res = []
    for item in net:
        if not isinstance(item, list) or not item:
            continue
        if item[0] != "net":
            continue
        net_name = _s(item[1]) if len(item) > 1 else None
        for sub in item:
            if not isinstance(sub, list) or not sub:
                continue
            if sub[0] == "wire":
                for s2 in sub:
                    if isinstance(s2, list) and s2 and s2[0] == "path":
                        r = parse_path(s2, net_name)
                        if r:
                            res.append(r)
            elif sub[0] == "via":
                r = parse_via(sub, net_name)
                if r:
                    res.append(r)
    return res


def parse_path(path, net_name):
    """(path LAYER W  x1 y1 x2 y2 ...) -> dict"""
    if len(path) < 3:
        return None
    layer = path[1]
    width = float(path[2])
    nums = [float(x) for x in path[3:] if is_num(x)]
    pts = [(nums[i] / SES_TO_MM, nums[i + 1] / SES_TO_MM)
           for i in range(0, len(nums) - 1, 2)]
    if len(pts) < 2:
        return None
    return {"kind": "wire", "layer": layer, "width_um": width,
            "points": pts, "net": net_name}


def parse_via(v, net_name):
    """(via PADSTACK x y (net NOME)) -> dict"""
    nums = [float(x) for x in v[1:] if is_num(x)]
    if len(nums) < 2:
        return None
    x, y = nums[0] / SES_TO_MM, nums[1] / SES_TO_MM
    # diâmetro: do padstack da via declarado em (library_out ...)
    return {"kind": "via", "layer": None, "x": x, "y": y, "net": net_name}


def via_diameter(ses_text, default_um=600.0):
    """Le o diametro do padstack de via do (library_out ...) do SES, em um.

    [FIX auditoria C9] default era 800 um; a regra do board e' via 0,6/0,3
    (setup ...) — e agora o (library_out) do SES tem o padstack da via (antes
    era vazio: o DSN nao declarava (via VIA1)). A linha re.search(...) morta
    (aplicava o padrao a uma string vazia e o resultado nao era usado) foi
    removida.
    """
    # procura o primeiro polygon de (library_out (padstack ...)
    blocks = re.findall(r'\(padstack[^\n]*\n((?:.*\n)*?)\s*\)', ses_text)
    best = default_um
    for b in blocks:
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', b)]
        pts = [n for n in nums if n > 0.05]
        if pts:
            d = (max(pts) - min(pts))
            if 0.1 < d < 5.0:
                best = d * 1000.0
                break
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pcb_in")
    ap.add_argument("ses")
    ap.add_argument("pcb_out")
    a = ap.parse_args()

    ses_text = open(a.ses).read()
    toks = tokenize(ses_text)
    root, _ = parse(toks, 0)
    items = walk_ses(root)

    board = pcbnew.LoadBoard(a.pcb_in)
    n_existing = len(list(board.GetTracks()))

    # mapa nome-de-net -> netcode do kicad
    # [FIX 2026-10-04] NETINFO_ITEM nao tem GetNetCode() no pcbnew 5.1.9
    # (AttributeError na primeira execucao real deste importador) — o netcode
    # e' GetNet().
    netcode = {}
    ni = board.GetNetInfo()
    for i in range(ni.GetNetCount()):
        code = ni.GetNetItem(i).GetNet()
        name = str(ni.GetNetItem(i).GetNetname())
        netcode[name] = code

    d_via = via_diameter(ses_text)
    n_seg = n_via = n_nonet = 0
    for it in items:
        code = netcode.get(it["net"], 0)
        if it["net"] not in netcode:
            n_nonet += 1
        if it["kind"] == "wire":
            layer_id = board.GetLayerID(it["layer"])
            if layer_id < 0:
                continue
            # largura do SES vem em RESOLUTION units (mm 1000 -> um); KiCad quer nm.
            # Antes: SetWidth(250) = 0,25 um de trilha (mil vezes mais fino).
            w = int(round(it["width_um"] * 1000.0))
            if w <= 0:
                w = 150000
            for i in range(len(it["points"]) - 1):
                (x1, y1), (x2, y2) = it["points"][i], it["points"][i + 1]
                t = pcbnew.TRACK(board)   # [FIX] KiCad 5.1: TRACK, nao PCB_TRACK
                t.SetStart(pcbnew.wxPointMM(x1, y1))
                t.SetEnd(pcbnew.wxPointMM(x2, y2))
                t.SetWidth(w)
                t.SetLayer(layer_id)
                t.SetNetCode(code)
                board.Add(t)
                n_seg += 1
        else:
            v = pcbnew.VIA(board)     # [FIX] KiCad 5.1: VIA, nao PCB_VIA
            v.SetPosition(pcbnew.wxPointMM(it["x"], it["y"]))
            v.SetWidth(int(round(d_via * 1000.0)))
            v.SetDrill(int(round(d_via * 500.0)))
            v.SetViaType(pcbnew.VIA_THROUGH)  # [FIX] 5.1: VIA_THROUGH
            v.SetLayerPair(board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))
            v.SetNetCode(code)
            board.Add(v)
            n_via += 1

    pcbnew.SaveBoard(a.pcb_out, board)

    # validacao: reabrir e contar
    chk = pcbnew.LoadBoard(a.pcb_out)
    total = len(list(chk.GetTracks()))
    t = 0
    vias = 0
    for tr in chk.GetTracks():
        # [FIX] KiCad 5.1: Type() == PCB_VIA_T (GetClass() devolve "VIA"/"TRACK")
        if tr.Type() == pcbnew.PCB_VIA_T:
            vias += 1
        else:
            t += 1
    print("SES: %s" % a.ses)
    print("  itens no SES      : %d" % len(items))
    print("  trilhas gravadas  : %d" % t)
    print("  vias gravadas     : %d" % vias)
    print("  nets sem match    : %d  (cairam na net 0)" % n_nonet)
    print("  tracks antes      : %d" % n_existing)
    print("  GetTracks() total : %d" % total)
    print("  board salvo       : %s" % a.pcb_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
