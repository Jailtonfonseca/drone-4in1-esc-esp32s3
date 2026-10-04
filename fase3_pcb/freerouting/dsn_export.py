#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
dsn_export.py -- Converte um .kicad_pcb em Specctra DSN aceito pelo FreeRouting 1.9.0.

Roda com:  /usr/bin/python3.9 dsn_export.py entrada.kicad_pcb saida.dsn [--only-net PREFIX]
           [--max-modules N]

O formato DSN aqui emitido foi deduzido lendo o parser do proprio FreeRouting 1.9.0
(app/freerouting/designforms/specctra/*.java) e validado contra o parser real.
Pontos que o 1.9.0 exige e que nao sao o "Specctra DSN" popular:

  1. O arquivo PRECISA comecar com "(pcb <nome>"  (DsnFile.read le 3 tokens: (, pcb, nome)
  2. (resolution mm 1000) + (unit mm)  -> coordenadas em mm no DSN
  3. (place <nome> <x> <y> front <rot>)  -> UM so numero de rotacao (o DSN "classico"
     tem dois: rot e mirror; o segundo faz o parser reclamar ") expected").
  4. (polygon <layer> <aperture> x1 y1 x2 y2 ...) -> lista PLANA, sem (pts ...)
  5. (circle <layer> <diametro> <x> <y>) ; (rect <layer> x1 y1 x2 y2)
     (a ordem do circulo e a do Shape.read_circle_scope do FR 1.9.0: diametro ANTES)
  6. (padstack ...) fica DENTRO de (library ...), NAO em (structure ...)
  7. (pin <padstack> <pin_name> <x> <y>) dentro de (image ...)
  8. (boundary (rect pcb x1 y1 x2 y2)) dentro de (structure ...)
"""
import sys
import os
import math
import re
import argparse

import pcbnew

MM = 1000000.0  # nm por mm

# ---------------------------------------------------------------------------
# Politica de roteamento (medida contra o board v9, ver NOTA_V9.md):
#   * In1.Cu e In4.Cu sao PLANOS (GND / VBAT_PROT) -> (type power) no DSN,
#     o autorroteador nao poe trilha neles.
#   * Nets de alta corrente ficam FORA do DSN: cobre delas vem de zonas do
#     KiCad (PHM* = no de fase 30 A; SNM* = source->shunt 30 A; GND/VBAT*
#     = planos). O roteador nao sabe fazer cobre de 6 mm.
#   * Restante: trilha padrao 0,25 mm, folga 0,20 mm (4 camadas 2 oz, JLCPCB ok).
# ---------------------------------------------------------------------------
POWER_LAYERS = {"In1.Cu", "In4.Cu"}
RAIL_NETS = {"GND", "VBAT", "VBAT_F", "VBAT_PROT"}
HI_CURRENT_RE = re.compile(r"^(PHM|SNM)\d{3}$")
DEFAULT_WIDTH = 0.25
DEFAULT_CLEAR = 0.20
BOUNDARY_INSET = 0.95  # banda de keepout da borda (v9_rule_areas.txt: 0,90 mm)


def is_skipped_net(name):
    return (name in RAIL_NETS) or bool(HI_CURRENT_RE.match(name))


def fnum(v):
    """Formata float sem notacao cientifica, sem ponto decimal inutil."""
    s = "%.4f" % (v,)
    s = s.rstrip("0").rstrip(".")
    if s in ("", "-"):
        s = "0"
    return s


def q(s):
    return '"%s"' % str(s).replace('"', "'")


def sanitize_net(name):
    """O FreeRouting nao likes de '/' e outros chars em nomes de net."""
    out = []
    for ch in str(name):
        out.append(ch if (ch.isalnum() or ch in "_-.") else "_")
    s = "".join(out)
    return s if s else "NET"


def copper_layers(board):
    """Camadas de cobre na ordem de indice do FreeRouting (F.Cu, In1..InN, B.Cu)."""
    # CuStack devolve exatamente as camadas de cobre ativas do board, ja em ordem
    # de empilhamento (F.Cu, In1.Cu ... InN.Cu, B.Cu) -- e so elas.
    ids = list(board.GetEnabledLayers().CuStack())
    return [board.GetLayerName(i) for i in ids]


def pad_shape_scope(layer, shape_enum, size, drill, is_tht):
    """Emite (shape ...) para um pad, aceito pelo Shape.java do FreeRouting 1.9.

    ORDEM DOS ARGUMENTOS DO CIRCULO (medida no Shape.read_circle_scope do
    FreeRouting 1.9.0): (circle <layer> <DIAMETRO> <x> <y>). A ordem antiga
    (x y diam) fazia o leitor pegar o x como diametro -> pads de diametro ZERO
    ("not an area") -> autorroteador sem alvos -> 0 rotas.
    """
    w = size.x / MM
    h = size.y / MM
    cx = 0.0
    cy = 0.0
    if is_tht or pcbnew.PAD_SHAPE_CIRCLE == shape_enum:
        d = w if w >= h else h
        return "(circle %s %s %s %s)" % (layer, fnum(d), fnum(cx), fnum(cy))
    # demais shapes (rect, oval, roundrect, trapezoid, custom) -> envelope retangular
    return "(rect %s %s %s %s %s)" % (layer, fnum(cx - w / 2.0), fnum(cy - h / 2.0),
                                       fnum(cx + w / 2.0), fnum(cy + h / 2.0))


def build(board, only_net_prefix=None, max_modules=None):
    layers = copper_layers(board)
    lname = [str(x) for x in layers]

    # --- placements e nets ------------------------------------------------
    modules = list(board.GetModules())
    if max_modules:
        modules = modules[:max_modules]

    # chaves unicas de padstack -> nome de padstack
    padstack_defs = []          # [(nome, layer, shape_scope, is_tht)]
    padstack_index = {}

    def padstack_for(pad, layer):
        size = pad.GetSize()
        is_tht = pad.GetDrillSize().x > 0
        key = (layer, int(size.x), int(size.y), int(pad.GetDrillSize().x),
               int(shape_is_circle(pad)), is_tht)
        if key in padstack_index:
            return padstack_index[key]
        name = "PAD%d" % (len(padstack_defs) + 1)
        padstack_index[key] = name
        padstack_defs.append((name, layer, pad_shape_scope(
            layer, shape_is_circle(pad), size, pad.GetDrillSize(), is_tht), is_tht))
        return name

    def shape_is_circle(pad):
        try:
            return pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
        except Exception:
            return True

    # image/package por footprint lib name
    images = {}      # pkg_name -> (outline_pts, [ (pin_name, padstack, x, y) ])
    placements = {}  # pkg_name -> [(ref, x, y, front, rot)]
    net_pins = {}    # net_name -> [ "REF-PADNUM" ]

    for m in modules:
        ref = str(m.GetReference())
        if ref.startswith("#"):
            continue
        try:
            pkg = str(m.GetFPID().GetLibItemName().wx_str())
        except AttributeError:
            pkg = str(m.GetFPID().GetLibItemName())
        if not pkg:
            pkg = "PKG_" + ref
        pos = m.GetPosition()
        x = pos.x / MM
        y = pos.y / MM
        front = (m.GetLayer() == pcbnew.F_Cu)
        rot = round(m.GetOrientation() / 10.0, 4) % 360.0

        placements.setdefault(pkg, []).append((ref, x, y, front, rot))

        if pkg not in images:
            # outline = retangulo do bounding box do footprint, em coords relativas.
            # (Antes: concatenava TODAS as linhas da silkscreen num unico poligono
            #  -> autointerseccao -> "winding number != 0" em cascata no leitor.)
            bbm = m.GetBoundingBox()
            x1r = (bbm.GetX() - pos.x) / MM
            y1r = (bbm.GetY() - pos.y) / MM
            x2r = x1r + bbm.GetWidth() / MM
            y2r = y1r + bbm.GetHeight() / MM
            pts = [(x1r, y1r), (x2r, y1r), (x2r, y2r), (x1r, y2r), (x1r, y1r)]
            images[pkg] = {"outline": pts, "pins": []}

        for pad in m.Pads():
            pnum = str(pad.GetName())
            if not pnum:
                continue
            ppos = pad.GetPosition()
            # relativo ao centro do modulo, ja rotacionado pelo pcbnew
            rx = (ppos.x - pos.x) / MM
            ry = (ppos.y - pos.y) / MM
            # nome de camada tem que ser IDENTICO ao declarado em (structure ...)
            pl = lname[0] if front else lname[-1]
            ps = padstack_for(pad, pl)
            images[pkg]["pins"].append((pnum, ps, rx, ry))
            net = str(pad.GetNetname())
            if net and net != "":
                net_pins.setdefault(sanitize_net(net), []).append("%s-%s" % (ref, pnum))

    # --- bounding box do board (Edge.Cuts) ---------------------------------
    bb = board.GetBoardEdgesBoundingBox()
    bx1, by1 = bb.GetX() / MM, bb.GetY() / MM
    bx2 = (bb.GetX() + bb.GetWidth()) / MM
    by2 = (bb.GetY() + bb.GetHeight()) / MM

    # via padstack generico
    via_d = 0.8

    out = []
    w = out.append
    w('(pcb %s' % q(os.path.splitext(os.path.basename(board.GetFileName()))[0] or "board"))
    w('  (parser')
    w('    (string_quote ")')
    w('    (space_in_quoted_tokens on)')
    # NAO usar a palavra "kicad" aqui: o leitor tem um aviso especifico para
    # "host_cad kicad + versao < 6" e QUALQUER warning abre um JOptionPane
    # modal que trava o modo batch headless (ninguem clica no OK).
    w('    (host_cad "dsn_export.py (pcbnew 5.1.9)")')
    w('    (host_version "2")')
    w('    (write_resolution mm 1000)')
    w('  )')
    w('  (resolution mm 1000)')
    w('  (unit mm)')
    w('  (structure')
    for i, ln in enumerate(lname):
        ltype = "power" if ln in POWER_LAYERS else "signal"
        w('    (layer %s (type %s) (property (index %d)))' % (ln, ltype, i))
    # banda de protecao da borda (equivale aos 3 rule_areas de 0,90 mm da v9)
    w('    (boundary (rect pcb %s %s %s %s))' % (
        fnum(bx1 + BOUNDARY_INSET), fnum(by1 + BOUNDARY_INSET),
        fnum(bx2 - BOUNDARY_INSET), fnum(by2 - BOUNDARY_INSET)))
    # regra padrao de trilha/folga para TODAS as nets roteaveis
    w('    (rule (width %s) (clear %s))' % (fnum(DEFAULT_WIDTH), fnum(DEFAULT_CLEAR)))
    # padstack da via em nivel de board: o FreeRouting procura a via do design
    # em (structure ...), e nao dentro de (library ...). Sem isto ele aborta com
    # "board padstack not found at 'VIA1'".
    w('    (padstack VIA1')
    for ln in lname:
        w('      (shape (circle %s %s 0 0))' % (ln, fnum(via_d)))
    w('      (attach off)')
    w('    )')
    w('  )')

    # placement
    w('  (placement')
    for pkg in sorted(placements.keys()):
        w('    (component %s' % q(pkg))
        for (ref, x, y, front, rot) in placements[pkg]:
            w('      (place %s %s %s %s %s)' % (
                ref, fnum(x), fnum(y), "front" if front else "back", fnum(rot)))
        w('    )')
    w('  )')

    # library
    w('  (library')
    for pkg in sorted(images.keys()):
        info = images[pkg]
        w('    (image %s' % q(pkg))
        if info["outline"]:
            flat = []
            for (px, py) in info["outline"]:
                flat.append(fnum(px))
                flat.append(fnum(py))
            w('      (outline (polygon %s 0.1 %s))' % (lname[0], " ".join(flat)))
        for (pnum, ps, rx, ry) in info["pins"]:
            w('      (pin %s %s %s %s)' % (ps, pnum, fnum(rx), fnum(ry)))
        w('    )')
    for (name, layer, shape_scope, is_tht) in padstack_defs:
        w('    (padstack %s' % name)
        w('      (shape %s)' % shape_scope)
        if is_tht:
            w('      (attach on)')
        else:
            w('      (attach off)')
        w('    )')
    # padstack da via, em todas as camadas
    w('    (padstack VIA1')
    for ln in lname:
        w('      (shape (circle %s %s 0 0))' % (ln, fnum(via_d)))
    w('      (attach off)')
    w('    )')
    w('  )')

    # network
    skipped = []
    routed = 0
    w('  (network')
    for name in sorted(net_pins.keys()):
        pins = net_pins[name]
        if only_net_prefix and not name.startswith(only_net_prefix):
            continue
        if len(pins) < 2:
            continue
        if is_skipped_net(name):
            skipped.append(name)
            continue
        routed += 1
        w('    (net %s (pins %s))' % (q(name), " ".join(pins)))
    w('  )')
    w('  (wiring)')
    w(')')
    return ("\n".join(out) + "\n", len(placements), routed,
            sum(len(v) for v in net_pins.values()), skipped)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pcb")
    ap.add_argument("dsn")
    ap.add_argument("--only-net", default=None)
    ap.add_argument("--max-modules", type=int, default=0)
    a = ap.parse_args()
    board = pcbnew.LoadBoard(a.pcb)
    txt, npkg, nrouted, npins, skipped = build(board, a.only_net, a.max_modules or None)
    with open(a.dsn, "w") as f:
        f.write(txt)
    print("DSN escrito: %s (%d bytes)" % (a.dsn, len(txt)))
    print("  packages        : %d" % npkg)
    print("  nets roteaveis   : %d" % nrouted)
    print("  pins (total)     : %d" % npins)
    print("  nets fora do DSN : %d -> %s" % (
        len(skipped), " ".join(sorted(skipped)) if skipped else "(nenhuma)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
