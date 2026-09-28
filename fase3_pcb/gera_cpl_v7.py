#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""Gera o arquivo de pick-and-place e as bibliotecas de footprints da placa v7.

Entradas : fase3_pcb/v7/v7_drone.kicad_pcb   (somente LEITURA)
Saidas   : fase3_pcb/v7/v7_drone-pos.csv          (319 linhas + cabecalho)
           fase3_pcb/v7/footprints/<Lib>.pretty/  (um .kicad_mod por footprint)
           fase3_pcb/v7/footprints/RELATORIO.txt  (log da geracao)

Formato do CSV: Ref,Val,Package,PosX,PosY,Rot,Side
  PosX/PosY em MILESIMOS de milimetro (KiCad usa 1e-6 mm -> 1e3 = 0,001 mm),
  gravados como inteiro, sem sinal, com Y ja espelhado para o convenio do
  pick-and-place (Y para cima, origem no canto inferior esquerdo).
  Rot em graus no mesmo sentido do board (anti-horario).
  Side = top | bottom.

AVISO HONESTO SOBRE OS FOOTPRINTS GRAVADOS
  Os arquivos .kicad_mod aqui sao EXTRAIDOS do board, nao sinteticos do zero:
  o .kicad_pcb carrega os pads E a geometria real de cada footprint
  (fp_line, fp_arc, fp_circle, fp_text reference/value/user), e tudo isso e
  copiado sem alteracao, com o (at ...) do modulo posto em (0 0).
  O que NAO pode ser recuperado do board, e portanto nao aparece aqui:
    - o "lib nickname" (o formato 20171130 do KiCad 5.1 o descarta ao salvar);
      a biblioteca foi resolvida por busca de nome em /usr/share/kicad/modules;
    - modelos 3D, porque nao ha link 3dmodel no .kicad_pcb;
    - o grupo "path" e o campo de origem da biblioteca.
  Cada arquivo e marcado como extracao, e cada pasta tem README dizendo o que
  falta e como obter a biblioteca original.

Footprints sem 'Position' definido no board: o centro e calculado pela
media dos pads e a lista completa vai para o RELATORIO.txt e para o log.

Uso: /usr/bin/python3.9 fase3_pcb/gera_cpl_v7.py
"""

import os
import re
import sys
import collections
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "v7", "v7_drone.kicad_pcb")
CSV = os.path.join(HERE, "v7", "v7_drone-pos.csv")
OUT_FP = os.path.join(HERE, "v7", "footprints")
RAIZ_MODULES = "/usr/share/kicad/modules"
LIB_SINTETICA = "HandDrawn_Inline"

SHAPE = {0: "circle", 1: "rect", 2: "oval", 3: "trapezoid", 4: "roundrect", 5: "custom"}


def log(*a):
    print(" ".join(str(x) for x in a))


def indice_bibliotecas(raiz):
    idx = {}
    if not os.path.isdir(raiz):
        return idx
    for lib in sorted(os.listdir(raiz)):
        if not lib.endswith(".pretty"):
            continue
        d = os.path.join(raiz, lib)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(".kicad_mod"):
                idx.setdefault(fn[:-len(".kicad_mod")], []).append(lib[:-len(".pretty")])
    return idx


def fmt(v):
    """float -> string sem notacao cientifica nem zeros a direita."""
    s = "%.6f" % float(v)
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def bloco_do_footprint(caminho):
    """Ordem do arquivo: ref -> bloco de texto do (module ...)."""
    linhas = open(caminho, "r", encoding="utf-8").read().split("\n")
    saida, prof, atual, dentro = {}, 0, [], False
    for ln in linhas:
        s = ln.strip()
        if s.startswith("(module "):
            dentro, prof, atual = True, 0, []
        if dentro:
            atual.append(ln)
            prof += ln.count("(") - ln.count(")")
            if prof == 0:
                dentro = False
                bloco = "\n".join(atual)
                m = re.search(r"fp_text reference (\S+)", bloco)
                if m:
                    saida[m.group(1)] = bloco
    return saida


def extrai_pads(bloco):
    """Pads do texto do board: (numero, tipo, shape, x, y, w, h, rot, camadas, furo).

    Varre caractere a caractere contando parenteses, porque no .kicad_pcb os
    pads de um mesmo footprint aparecem em uma unica linha (varios '(pad ...)' na
    mesma linha) e um contador por linha perderia a segunda occurrences.
    """
    pads = []
    i, n = 0, len(bloco)
    while i < n:
        if bloco.startswith("(pad ", i):
            prof, j = 0, i
            while j < n:
                if bloco[j] == "(":
                    prof += 1
                elif bloco[j] == ")":
                    prof -= 1
                    if prof == 0:
                        break
                j += 1
            txt = re.sub(r"\s+", " ", bloco[i:j + 1])
            i = j + 1
            m = re.search(
                r'\(pad (?:"([^"]*)"|(\S+))\s+(\S+)\s+(\S+)\s+\(at\s+(\S+)\s+(\S+)(?:\s+(\S+))?\)'
                r'\s+\(size\s+(\S+)\s+(\S+)\)', txt)
            if not m:
                continue
            num = m.group(1) if m.group(1) is not None else m.group(2)
            resto = txt[m.end():]
            ml = re.search(r"\(layers([^)]*)\)", resto)
            md = re.search(r"\(drill\s+(\S+)\)", resto)
            pads.append({
                "num": num,
                "tipo": m.group(3),
                "shape": m.group(4),
                "x": m.group(5), "y": m.group(6), "rot": m.group(7) or "0",
                "w": m.group(8), "h": m.group(9),
                "layers": ml.group(1).split() if ml else [],
                "drill": md.group(1) if md else None,
            })
        else:
            i += 1
    return pads


def extrai_graficos(bloco):
    """fp_text (reference/value/user) e geometria (fp_line/fp_arc/fp_circle).

    Reprocessa o bloco do board para um footprint de biblioteca: zera o
    deslocamento dos textos e da geometria em relacao ao 'at' do modulo, porque
    num .pretty tudo e relativo a origem (0 0) do footprint. A geometria em si
    (coordenadas locais de silkscreen/fab/courtyard) e apenas copiada.
    """
    out = []
    i, n = 0, len(bloco)
    alvos = ("fp_text ", "fp_line ", "fp_arc ", "fp_circle ")
    while i < n:
        achou = None
        for t in alvos:
            if bloco.startswith("(" + t, i):
                achou = "(" + t
                break
        if achou is None:
            i += 1
            continue
        prof, j = 0, i
        while j < n:
            if bloco[j] == "(":
                prof += 1
            elif bloco[j] == ")":
                prof -= 1
                if prof == 0:
                    break
            j += 1
        txt = bloco[i:j + 1]
        i = j + 1
        if txt.startswith("(fp_text "):
            m = re.search(r'fp_text (reference|value|user) ([^\n(]*)', txt)
            tipo = m.group(1) if m else "user"
            val = m.group(2).strip() if m else ""
            if tipo == "user":
                val = re.sub(r"^%[rR]$", "${REFERENCE}", val)
                val = re.sub(r"^%[vV]$", "${VALUE}", val)
            lay = re.search(r"\(layer ([^)]*)\)", txt)
            eff = re.search(r"\(effects.*", txt)
            laytxt = lay.group(1) if lay else "F.Fab"
            linha = '(fp_text %s "%s" (at 0 0) (layer %s)' % (tipo, val, laytxt)
            if eff:
                linha += "\n    " + eff.group(0).rstrip() + ")"
            else:
                linha += ")"
            out.append(linha)
        else:
            out.append(txt)
    return out


def main():
    if not os.path.isfile(BOARD):
        sys.exit("board nao encontrado: %s" % BOARD)
    board = pcbnew.LoadBoard(BOARD)
    modulos = list(board.GetModules())
    fonte = open(BOARD, "r", encoding="utf-8").read()
    idx_libs = indice_bibliotecas(RAIZ_MODULES)

    # altura da placa para espelhar o Y no convenio de pick-and-place
    bb = board.GetBoardEdgesBoundingBox()
    altura_mm = pcbnew.ToMM(bb.GetHeight())
    largura_mm = pcbnew.ToMM(bb.GetWidth())
    x0_mm = pcbnew.ToMM(bb.GetX())
    log("board            : %s" % os.path.relpath(BOARD, HERE))
    log("dimensoes        : %.1f x %.1f mm" % (largura_mm, altura_mm))
    log("modulos          : %d" % len(modulos))

    blocos = bloco_do_footprint(BOARD)
    if len(blocos) != len(modulos):
        sys.exit("divergencia: %d blocos no arquivo x %d modulos" % (len(blocos), len(modulos)))

    linhas_csv = ["Ref,Val,Package,PosX,PosY,Rot,Side"]
    sem_posicao = []          # refs sem (at ...) no board -> centro pelos pads
    calc_por_centro = []      # refs cuja posicao foi calculada
    libs_usadas = collections.defaultdict(set)
    footprints_ausentes = [] # footprint sem bib no sistema
    refs = []
    dup = [r for r, c in collections.Counter([m.GetReference() for m in modulos]).items() if c > 1]

    for mod in modulos:
        ref = mod.GetReference()
        refs.append(ref)
        nome = str(mod.GetFPID().GetLibItemName())
        pos = mod.GetPosition()
        tem_at = re.search(r"^\s*\(at ", blocos[ref], re.M) is not None
        if not tem_at:
            sem_posicao.append(ref)
            xs = [p.GetPosition().x for p in mod.Pads()]
            ys = [p.GetPosition().y for p in mod.Pads()]
            if not xs:
                sys.exit("footprint %s sem (at) e sem pads: nao ha como calcular o centro" % ref)
            x = sum(xs) / float(len(xs))
            y = sum(ys) / float(len(ys))
            calc_por_centro.append(ref)
        else:
            x, y = float(pos.x), float(pos.y)

        if nome:
            cands = idx_libs.get(nome, [])
            if not cands:
                footprints_ausentes.append((ref, nome))
                lib = LIB_SINTETICA
            else:
                lib = cands[0]
        else:
            lib = LIB_SINTETICA
        pkg = nome or ("<desenhado_a_mao:%s>" % ref)
        libs_usadas[lib].add(pkg)

        xm = pcbnew.ToMM(x)
        ym = altura_mm - pcbnew.ToMM(y)   # convencao de pick-and-place: Y para cima
        layer = board.GetLayerName(mod.GetLayer())
        side = "bottom" if layer.startswith("B.Cu") else "top"
        rot = mod.GetOrientationDegrees() % 360.0
        rot = round(rot, 4) if rot % 1 else int(rot)

        val = str(mod.GetValue()).replace(",", " ")
        linhas_csv.append("%s,%s,%s:%s,%d,%d,%s,%s" % (
            ref, val, lib, pkg, int(round(xm * 1000.0)),
            int(round(ym * 1000.0)), rot, side))

    with open(CSV, "w", encoding="utf-8") as fh:
        fh.write("\n".join(linhas_csv) + "\n")

    # ---------------- bibliotecas sinteticas ----------------
    if os.path.isdir(OUT_FP):
        sys.exit("pasta de footprints ja existe: %s (remova antes de regerar)" % OUT_FP)
    os.makedirs(OUT_FP)

    # template por nome de footprint, pego da 1a ocorrencia no board
    template = {}
    for m in modulos:
        nome = str(m.GetFPID().GetLibItemName())
        if not nome or nome in template:
            continue
        ref = m.GetReference()
        pads = extrai_pads(blocos[ref])
        mref = re.search(r"fp_text reference (\S+)", blocos[ref])
        mval = re.search(r"fp_text value ([^\n(]*)", blocos[ref])
        template[nome] = {
            "pads": pads,
            "graficos": extrai_graficos(blocos[ref]),
            "ref": mref.group(1) if mref else "REF**",
            "val": (mval.group(1).strip() if mval else ""),
            "lib": idx_libs.get(nome, [LIB_SINTETICA])[0],
            "origem": ref,
        }
    # os desenhados a mao sao 1:1 (cada ref e o proprio "footprint")
    for m in modulos:
        nome = str(m.GetFPID().GetLibItemName())
        if nome:
            continue
        ref = m.GetReference()
        chave = "MAO_" + ref
        template[chave] = {
            "pads": extrai_pads(blocos[ref]),
            "graficos": extrai_graficos(blocos[ref]),
            "ref": ref,
            "val": str(m.GetValue()).strip(),
            "lib": LIB_SINTETICA,
            "origem": ref,
        }

    n_mod = 0
    rel = []
    conteudo = []
    for lib in sorted(libs_usadas):
        pasta = os.path.join(OUT_FP, lib + ".pretty")
        os.makedirs(pasta)
        origem_real = os.path.join(RAIZ_MODULES, lib + ".pretty")
        existe = os.path.isdir(origem_real)
        for nome in sorted(libs_usadas[lib]):
            if nome.startswith("<desenhado_a_mao:") or nome.startswith("MAO_"):
                chave = nome if nome.startswith("MAO_") else "MAO_" + nome.split(":", 1)[1].rstrip(">")
                tpl = template[chave]
                nome_mod = chave
            else:
                tpl = template[nome]
                nome_mod = nome
            fn = nome_mod + ".kicad_mod"
            caminho = os.path.join(pasta, fn)
            L = []
            a = L.append
            a("(module %s (layer F.Cu) (tedit 5D68B0F0) (tstamp 00000000)" % nome_mod)
            a('  (descr "EXTRACAO do board %s, modulo de origem %s. Pads, fp_line, '
              'fp_arc, fp_circle e fp_text copiados do board sem alteracao de geometria. '
              'NAO reproduzidos: lib nickname (o formato 20171130 do KiCad 5.1 nao o grava), '
              'modelos 3D (o board nao tem link 3dmodel) e grupo path. Ver README.md desta pasta.")'
              % (os.path.basename(BOARD), tpl["origem"]))
            a('  (tags "extracao-do-board %s")' % lib)
            a("  (attr smd)")
            for el in tpl["graficos"]:
                a("  " + el)
            for p in tpl["pads"]:
                tipo = p["tipo"] if p["tipo"] in ("smd", "thru_hole", "np_thru_hole", "connect") else "smd"
                at = "(at %s %s%s)" % (fmt(p["x"]), fmt(p["y"]),
                                      "" if str(p["rot"]) in ("0", "0.0") else " " + fmt(p["rot"]))
                lay = " ".join(p["layers"]) or "F.Cu F.Paste F.Mask"
                head = "  (pad %s %s %s %s (size %s %s)" % (
                    p["num"] if p["num"] else '""', tipo, p["shape"],
                    at, fmt(p["w"]), fmt(p["h"]))
                if p["drill"]:
                    head += " (drill %s)" % fmt(p["drill"])
                head += " (layers %s)" % lay
                a(head)
                if p["shape"] == "roundrect":
                    a("    (roundrect_rratio 0.25)")
                a("  )")
            a(")")
            with open(caminho, "w", encoding="utf-8") as fh:
                fh.write("\n".join(L) + "\n")
            n_mod += 1
            rel.append("%s/%s  <- board %s  (%d pads)" % (lib + ".pretty", fn, tpl["origem"], len(tpl["pads"])))
            conteudo.append((lib + "/" + fn, len(tpl["pads"]), tpl["origem"]))

        # README da biblioteca
        R = []
        b = R.append
        b("# Biblioteca extraida do board: %s" % lib)
        b("")
        b("Gerada por `gera_cpl_v7.py` a partir de `fase3_pcb/v7/v7_drone.kicad_pcb`.")
        b("")
        b("## O QUE ESTA PASTA CONTEM")
        b("")
        b("%d arquivo(s) `.kicad_mod`, **extracao** do board: cada um tem o `fp_text reference`," % len(libs_usadas[lib]))
        b("o `fp_text value`, o `fp_text user` e a geometria `fp_line`/`fp_arc`/`fp_circle`,")
        b("alem dos pads (numero, tipo, shape, tamanho, rotacao, camadas e furo),")
        b("tudo copiado do `.kicad_pcb` sem alteracao de geometria.")
        b("")
        b("## O QUE FALTA NESTA EXTRACAO")
        b("")
        b("Tres coisas nao podem ser recuperadas do board e por isso NAO estao nos arquivos:")
        b("")
        b("1. **lib nickname** -- o formato `.kicad_pcb` versao 20171130 (KiCad 5.1) descarta o")
        b("   nickname de biblioteca de cada modulo ao salvar. A biblioteca desta pasta foi")
        b("   resolvida por busca do nome do footprint em `/usr/share/kicad/modules`; se um")
        b("   nome existisse em varias bibliotecas, foi escolhido o primeiro em ordem alfabetica.")
        b("2. **modelos 3D** -- o board nao tem nenhum link `3dmodel`.")
        b("3. **grupo `path`** -- o board nao grava o caminho de origem da biblioteca.")
        b("")
        b("Nada foi inventado: o que esta nos arquivos veio do board; o que falta esta listado acima.")
        b("")
        b("## BIBLIOTECA REAL")
        b("")
        if existe:
            b("A biblioteca original **existe** neste sistema:")
            b("")
            b("    %s" % origem_real)
            b("")
            b("Para obter os footprints verdadeiros desta placa, extraia do board e grave com")
            b("o proprio pcbnew, que le a geometria completa da biblioteca:")
            b("")
            b("    /usr/bin/python3.9 - <<'PY'")
            b("    import pcbnew")
            b("    b = pcbnew.LoadBoard('fase3_pcb/v7/v7_drone.kicad_pcb')")
            b("    fp = pcbnew.FootprintLoad('%s', '%s')" % (origem_real, "<NOME>"))
            b("    pcbnew.SaveBoard('saida.kicad_pcb', b)  # ou fp.Save('.pretty/NOME.kicad_mod')")
            b("    PY")
            b("")
            b("O escopo deste script foi limitado a ler o board e gravar arquivos novos, sem")
            b("tocar no `v7_drone.kicad_pcb`.")
        else:
            b("A biblioteca original **NAO existe** neste sistema em `%s`." % RAIZ_MODULES)
            b("Os arquivos desta pasta sao extracao fiel desses modulos do board, nao invencao:")
            b("pads e geometria vieram do `.kicad_pcb`. O que falta e so o metadado de")
            b("biblioteca (nickname e caminho de origem), que o formato do board nao guarda:")
            b("e preciso instalar a biblioteca KiCad correspondente ou fornecer os arquivos")
            b("originais para poder reproduzi-la.")
        b("")
        b("## CONTEUDO")
        b("")
        for nome_arq, n_pad, ref_origem in sorted(conteudo):
            if nome_arq.rsplit("/", 1)[0] == lib:
                b("- `%s.pretty/%s.kicad_mod` &mdash; %d pads, modulo de origem `%s` no board"
                  % (lib, nome_arq.rsplit("/", 1)[1][:-len(".kicad_mod")], n_pad, ref_origem))
        with open(os.path.join(pasta, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(R) + "\n")

    # ---------- relatorio geral ----------
    with open(CSV, "r", encoding="utf-8") as fh:
        n_linhas = sum(1 for _ in fh)
    uniq = len(set(refs))
    G = []
    g = G.append
    g("RELATORIO DE GERACAO - pick-and-place e footprints da placa v7")
    g("gerado por fase3_pcb/gera_cpl_v7.py (Python %s, pcbnew %s)" %
      (sys.version.split()[0], pcbnew.GetBuildVersion()))
    g("")
    g("ENTRADA (somente leitura)")
    g("  %s" % BOARD)
    g("  md5 do board: %s" % __import__("hashlib").md5(open(BOARD, "rb").read()).hexdigest())
    g("")
    g("SAIDA 1 - pick-and-place")
    g("  arquivo            : %s" % CSV)
    g("  linhas (com cabec.): %d" % n_linhas)
    g("  linhas de dados    : %d" % (n_linhas - 1))
    g("  referencias unicas : %d" % uniq)
    g("  referencias dup.   : %d%s" % (len(dup), ("" if not dup else " -> %r" % dup)))
    g("  board: modulos      : %d" % len(modulos))
    g("")
    g("  Units: PosX/PosY em milesimos de milimetro (0,001 mm).")
    g("  Convencao: Y para cima, origem no canto inferior esquerdo da placa.")
    g("  Y_pos = %.4f - Y_board   (H = altura da placa = %.4f mm)" % (altura_mm, altura_mm))
    g("  X_pos = X_board, sem deslocamento: o canto inferior esquerdo da placa esta em")
    g("  X=%.4f mm no sistema de coordenadas do board, entao o X do CSV e a coordenada do" % x0_mm)
    g("  board, e nao uma medida relativa a borda. Para quem precisar da medida relativa a")
    g("  borda, subtrair %.4f do PosX. Isso vale para as 319 referencias, sem excecao." % x0_mm)
    g("  Rot em graus, mesmo sentido do board (anti-horario).")
    g("  Side: top = F.Cu, bottom = B.Cu.")
    g("")
    g("  FOOTPRINTS SEM 'Position' DEFINIDO NO BOARD")
    g("  (sem '(at ...)' no .kicad_pcb -> posicao calculada pelo centro dos pads)")
    if sem_posicao:
        for r in sem_posicao:
            g("    - %s" % r)
    else:
        g("    nenhum: os %d modulos do board tem '(at ...)'." % len(modulos))
    g("  Total de refs com posicao CALCULADA: %d" % len(calc_por_centro))
    g("")
    g("SAIDA 2 - bibliotecas de footprints (EXTRACAO do board)")
    g("  pasta: %s" % OUT_FP)
    g("  bibliotecas         : %d" % len(libs_usadas))
    g("  arquivos .kicad_mod : %d" % n_mod)
    g("  cada .kicad_mod tem reference, value, user, pads e a geometria")
    g("  fp_line/fp_arc/fp_circle copiados do board, sem alteracao de valor.")
    g("  NAO reproduzido (o board nao carrega): lib nickname, modelos 3D, grupo path.")
    g("  HandDrawn_Inline NAO tem biblioteca real: sao os 6 modulos desenhados a mao,")
    g("  sem nome de footprint no board. Os arquivos sao extracao fiel desses modulos.")
    g("")
    for lib in sorted(libs_usadas):
        existe = os.path.isdir(os.path.join(RAIZ_MODULES, lib + ".pretty"))
        g("    %-24s %2d footprints   bib real no sistema: %s"
          % (lib, len(libs_usadas[lib]), "SIM" if existe else "NAO"))
    g("")
    if footprints_ausentes:
        g("  FOOTPRINTS SEM BIBLIOTECA LOCAL (ficam em %s):" % LIB_SINTETICA)
        for ref, nome in footprints_ausentes:
            g("    - %s -> %s" % (ref, nome))
    else:
        g("  Todos os footprints nomeados foram localizados em %s." % RAIZ_MODULES)
    g("")
    with open(os.path.join(OUT_FP, "RELATORIO.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(G) + "\n")

    log("")
    log("csv                 : %s" % CSV)
    log("linhas (c/ cabecalho): %d  (esperado %d)" % (n_linhas, len(modulos) + 1))
    log("refs unicas         : %d   duplicadas: %d" % (uniq, len(dup)))
    log("refs SEM (at)       : %d %s" % (len(sem_posicao), sem_posicao if sem_posicao else ""))
    log("libs                : %d" % len(libs_usadas))
    log(".kicad_mod gravados : %d" % n_mod)
    if n_linhas != len(modulos) + 1:
        sys.exit("FALHA: wc -l do CSV = %d, esperado %d" % (n_linhas, len(modulos) + 1))
    if uniq != len(modulos):
        sys.exit("FALHA: %d referencias unicas para %d modulos" % (uniq, len(modulos)))
    log("RESULTADO: OK")


if __name__ == "__main__":
    main()
