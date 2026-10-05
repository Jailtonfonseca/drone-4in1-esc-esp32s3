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


def pad_shape_scope(layer, is_circle, ex, ey):
    """Emite (shape ...) para um pad, aceito pelo Shape.java do FreeRouting 1.9.

    [FIX auditoria P1 — 0 == False] a versao anterior recebia `shape_enum` e
    testava `pcbnew.PAD_SHAPE_CIRCLE == shape_enum`: o argumento era o BOOL
    de shape_is_circle() e PAD_SHAPE_CIRCLE == 0, e `0 == False` e' True em
    Python -> TODO pad virava (circle layer max(w,h) 0 0), o ramo (rect ...)
    era inalcançavel, e pads SOIC-8 de Ø1,95 mm em pitch 1,27 mm se
    sobreponham entre nets diferentes -> blobs selados -> 0 rotas (bug 1.h).

    ORDEM DOS ARGUMENTOS DO CIRCULO (medida no Shape.read_circle_scope do
    FreeRouting 1.9.0): (circle <layer> <DIAMETRO> <x> <y>).
    """
    if is_circle:
        d = 2.0 * max(ex, ey)
        return "(circle %s %s %s %s)" % (layer, fnum(d), fnum(0), fnum(0))
    # demais shapes (rect, oval, roundrect, trapezoid, custom) -> envelope
    # retangular no frame do FOOTPRINT (meio-extensoes ex/ey ja rotacionadas
    # pela orientacao propria do pad relativa ao modulo)
    return "(rect %s %s %s %s %s)" % (layer, fnum(-ex), fnum(-ey),
                                      fnum(ex), fnum(ey))


def pad_halfextents(pad):
    """Meio-extensoes (ex, ey) do envelope do pad NO FRAME DO FOOTPRINT.

    Chamar com o modulo em orientacao ZERO (ver build): aí
    pad.GetOrientation() e' a rotacao PROPRIA do pad relativa ao modulo, e o
    envelope de (w, h) rotacionado por ela e' o rect que o DSN precisa.
    """
    size = pad.GetSize()
    w = size.x / MM
    h = size.y / MM
    ang = math.radians((pad.GetOrientation() / 10.0) % 360.0)
    ca, sa = abs(math.cos(ang)), abs(math.sin(ang))
    ex = (w * ca + h * sa) / 2.0
    ey = (w * sa + h * ca) / 2.0
    return ex, ey


def build(board, only_net_prefix=None, max_modules=None):
    layers = copper_layers(board)
    lname = [str(x) for x in layers]

    # --- placements e nets ------------------------------------------------
    modules = list(board.GetModules())
    if max_modules:
        modules = modules[:max_modules]

    # chaves unicas de padstack -> nome de padstack
    # [FIX P5] um padstack THT ganha shape em TODAS as camadas de cobre (o
    # pad atravessa a placa); SMD continua com shape so na camada do lado.
    padstack_defs = []          # [(nome, [shape_scope,...], is_tht)]
    padstack_index = {}

    def padstack_for(pad, front):
        size = pad.GetSize()
        is_tht = pad.GetDrillSize().x > 0
        # [chave inclui a rotacao PROPRIA do pad: pads de mesmo tamanho com
        # rotacoes diferentes tem envelopes diferentes no frame do footprint]
        own_rot = int(round(pad.GetOrientation()))   # decigraus (modulo em rot 0)
        key = (front, int(size.x), int(size.y), int(pad.GetDrillSize().x),
               int(shape_is_circle(pad)), is_tht, own_rot)
        if key in padstack_index:
            return padstack_index[key]
        name = "PAD%d" % (len(padstack_defs) + 1)
        padstack_index[key] = name
        ex, ey = pad_halfextents(pad)      # modulo esta' em orientacao ZERO aqui
        isc = shape_is_circle(pad)
        if is_tht:
            shapes = [pad_shape_scope(ln, isc, ex, ey) for ln in lname]
        else:
            ln = lname[0] if front else lname[-1]
            shapes = [pad_shape_scope(ln, isc, ex, ey)]
        padstack_defs.append((name, shapes, is_tht))
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
    _first_done = {}  # [FIX P4] marca o pacote cuja image ja foi emitida

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

        # [FIX P3] offsets LOCAIS do footprint: pcbnew guarda os pads no frame
        # do modulo e o FreeRouting APLICA a rotacao do (place ...) aos pins
        # da image (Pin.relative_location -> turn_90_degree). A versao antiga
        # gravava offsets JA rotacionados (pad.GetPosition() e' absoluto) ->
        # rotacao dupla -> 51/105 pads do corte em posicao errada.
        # Truque robusto: orientacao ZERO temporaria -> GetPosition() devolve
        # o offset LOCAL do pad; depois restaura a orientacao original.
        saved_orient = m.GetOrientation()
        m.SetOrientation(0)
        try:
            if pkg not in images:
                # [FIX auditoria] outline por PADS (o GetBoundingBox infla
                # com texto de silk e gerava outlines 2-3x o chip). O outline
                # da image NAO e' obstaculo no FR 1.9 (Package.java separa
                # outline de keepout) -- e' so envelope visual.
                l = t = r = b = None
                for p0 in m.Pads():
                    pp = p0.GetPosition()
                    l = pp.x if l is None else min(l, pp.x)
                    r = pp.x if r is None else max(r, pp.x)
                    t = pp.y if t is None else min(t, pp.y)
                    b = pp.y if b is None else max(b, pp.y)
                if l is not None:
                    mg = 0.5 * MM
                    x1r, y1r = (l - mg) / MM, (t - mg) / MM
                    x2r, y2r = (r + mg) / MM, (b + mg) / MM
                else:
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
                ppos = pad.GetPosition()      # offset LOCAL (modulo em rot 0)
                rx = (ppos.x - pos.x) / MM
                ry = (ppos.y - pos.y) / MM
                # [FIX P4] pins da image so' do PRIMEIRO modulo do pacote: a
                # versao antiga appending os pads de TODAS as instancias
                # (image SOIC-8 com 96/384 entradas; ~39.000 pinos no board).
                ps = padstack_for(pad, front)
                if not _first_done.get(pkg):
                    images[pkg]["pins"].append((pnum, ps, rx, ry))
                net = str(pad.GetNetname())
                if net and net != "":
                    net_pins.setdefault(sanitize_net(net), []).append(
                        "%s-%s" % (ref, pnum))
            _first_done[pkg] = True
        finally:
            m.SetOrientation(saved_orient)

    # --- bounding box do board (Edge.Cuts) ---------------------------------
    bb = board.GetBoardEdgesBoundingBox()
    bx1, by1 = bb.GetX() / MM, bb.GetY() / MM
    bx2 = (bb.GetX() + bb.GetWidth()) / MM
    by2 = (bb.GetY() + bb.GetHeight()) / MM

    # via padstack generico
    # [FIX auditoria C9] era 0,8 mm — a regra do proprio board (setup ...) e'
    # via_size 0,6000 / via_drill 0,3000; o FreeRouting roteou com 0,8 e o
    # ses_import regravava 0,8/0,4 (violando a regra de projeto). Alinhado.
    via_d = 0.6

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
    # [FIX auditoria P2 — bug 1.h] a via padstack estava DEFINIDA mas nunca
    # DECLARADA: o FR 1.9.0 so registra vias do escopo (via ...) da structure
    # (Structure.java:866-868) — sem esta linha, via_padstack_names fica null,
    # set_via_padstacks nunca roda e o board fica SEM NENHUMA via (prova:
    # (library_out) vazio nos SES antigos) — impossivel mudar de camada.
    w('    (via VIA1)')
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
    for (name, shape_scopes, is_tht) in padstack_defs:
        w('    (padstack %s' % name)
        for shape_scope in shape_scopes:
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
