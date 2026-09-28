#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
"""
gera_pacote_fab.py -- Pacote de fabricacao completo de uma placa KiCad.

Roda SOMENTE com o interpretador que tem o modulo pcbnew desta maquina:

    /usr/bin/python3.9 fase3_pcb/gera_pacote_fab.py <board.kicad_pcb> --out <pasta>

O que o script corrige (defeito herdado da v1..v7):
    O .kicad_pcb nao tem 'title_block', e o pcbnew 5.1 nomeia o plot como
    "<basename-do-board>-<plotname>.<ext>".  Sem basename (board construido em
    memoria e nunca salvo) o resultado e "-drone_F_Cu.gtl": hifen na frente e
    nome igual em todas as versoes.  Aqui o title_block e preenchido EM MEMORIA
    (nunca salvo de volta no .kicad_pcb do repositorio) e o nome final de cada
    arquivo e normalizado para "<projeto>_<rev>_<Camada>.<ext>", sem hifen e
    com a versao embutida.

O que o script produz:
    gerbers    F_Cu, In1_Cu, In2_Cu, B_Cu, F_Mask, B_Mask, F_SilkS, B_SilkS,
               Edge_Cuts            (extensao de protel: .gtl .g2 .g3 .gbl ...)
    furos      Excellon PTH e NPTH separados (-PTH.drl / -NPTH.drl)
    gbrjob     .gbrjob (KiCad Job File, JSON) via GERBER_JOBFILE_WRITER
    mapa furos PDF do proprio KiCad + PNG legivel feito com matplotlib
    P&P        .pos e .csv no formato do KiCad (PosX/PosY em milesimos de mm,
               lados Top/Bottom separados)
    relatorios DRC_RPC_PCB.rpt (ou a nota de indisponibilidade) e
               README_GERBER.txt

Nao faz: nao altera e nao salva o .kicad_pcb de entrada; nao faz push; nao
chama o DRC pela GUI (indisponivel headless no 5.1).
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import traceback

import pcbnew

# --------------------------------------------------------------------------
# Constantes de layout do KiCad 5.1
# --------------------------------------------------------------------------
# Em 5.1.9 nao existe PAD_ATTRIB_PTH: o Through Hole e PAD_ATTRIB_STANDARD (0).
ATTR_PTH = pcbnew.PAD_ATTRIB_STANDARD
ATTR_NPTH = pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED

# Copo, mascaras, silk e perfil: IDs sao fixos no KiCad 5.1.
# As camadas de COBRE sao descubtas em tempo de execucao (a v7 tem 4, a v8
# tem 6) -- por isso a lista completa e montada por camadas_cobre_do_board().
LAYERS_NAO_COBRE = [
    (pcbnew.F_Mask, "F_Mask"),
    (pcbnew.B_Mask, "B_Mask"),
    (pcbnew.F_SilkS, "F_SilkS"),
    (pcbnew.B_SilkS, "B_SilkS"),
    (pcbnew.Edge_Cuts, "Edge_Cuts"),
]

# Candidatas a camada interna, na ordem em que o KiCad as numera.
_COPRE_IN = [getattr(pcbnew, "In%d_Cu" % i, None) for i in range(1, 31)]


def camadas_cobre_do_board(board):
    """Devolve [(id, 'F_Cu'/'In1_Cu'/.../'B_Cu')] de cobre, na ordem F->B,
    filtrando pelas camadas realmente habilitadas no arquivo.

    A v7 tem 4 camadas e a v8 tem 6 (F, In1..In4, B): fixar a lista deixaria
    camadas de fora do pacote.
    """
    nomes = {"F_Cu": "F_Cu", "B_Cu": "B_Cu"}
    out = []
    if board.IsLayerEnabled(pcbnew.F_Cu):
        out.append((pcbnew.F_Cu, "F_Cu"))
    for n, lid in enumerate(_COPRE_IN, start=1):
        if lid is not None and board.IsLayerEnabled(lid):
            out.append((lid, "In%d_Cu" % n))
    if board.IsLayerEnabled(pcbnew.B_Cu):
        out.append((pcbnew.B_Cu, "B_Cu"))
    return out


def camadas_do_board(board):
    """Lista completa de camadas a plotar: cobre (dinamico) + as fixas."""
    lst = list(camadas_cobre_do_board(board))
    lst += [(lid, nm) for lid, nm in LAYERS_NAO_COBRE if board.IsLayerEnabled(lid)]
    return lst

# O que cada camada e, para o README e para o checklist da casa de fabricacao.
PAPEL_CAMADA = {
    "F_Cu": "cobre superior (sinal)",
    "In1_Cu": "cobre interno 1 (sinal)",
    "In2_Cu": "cobre interno 2 (sinal)",
    "B_Cu": "cobre inferior (sinal)",
    "F_Mask": "mascara de solda superior (verniz)",
    "B_Mask": "mascara de solda inferior (verniz)",
    "F_SilkS": "silk top (identificacao dos componentes)",
    "B_SilkS": "silk bottom (identificacao dos componentes)",
    "Edge_Cuts": "perfil/contorno da placa ( Edge.Cuts )",
}


def log(msg):
    print(msg, flush=True)


# --------------------------------------------------------------------------
# Nome versionado
# --------------------------------------------------------------------------
def nome_base(board_path):
    """Deriva o nome versionado do pacote a partir do nome do .kicad_pcb.

    v8_drone.kicad_pcb  ->  drone_v8
    v7_drone.kicad_pcb  ->  drone_v7
    meu_board.kicad_pcb ->  meu_board
    """
    stem = os.path.splitext(os.path.basename(board_path))[0]
    m = re.match(r"^v(\d+)_(.+)$", stem)
    if m:
        return "drone_v%s" % m.group(1)
    m = re.match(r"^(.+)_v(\d+)$", stem)
    if m:
        return "%s_v%s" % (m.group(1), m.group(2))
    return stem


def renomear_para_limpo(caminho, nome_final):
    """Renomeia <saida>/<qualquer>.gbr para <saida>/<nome_final>.

    O pcbnew 5.1 sempre interpoe um separador entre o basename do board e o
    nome do plot; normalizar aqui e o que garante o nome limpo e versionado.
    """
    d = os.path.dirname(caminho)
    final = os.path.join(d, nome_final)
    if os.path.abspath(caminho) != os.path.abspath(final):
        if os.path.exists(final):
            os.remove(final)
        os.rename(caminho, final)
    return final


# --------------------------------------------------------------------------
# 1) Title block em memoria
# --------------------------------------------------------------------------
def aplicar_title_block(board, nome, projeto, rev, data, autor):
    """Grava (title) e (comment 1..4) no board SOMENTE em memoria.

    Nada disso e salvo no .kicad_pcb do repositorio: o board so existe aqui
    para que o gbrjob e o cabecalho dos arquivos carreguem a identificacao.
    """
    tb = board.GetTitleBlock()
    tb.SetTitle(nome)
    tb.SetComment1("projeto: %s" % projeto)
    tb.SetComment2("revisao: %s" % rev)
    tb.SetComment3("data: %s" % data)
    tb.SetComment4("autor: %s" % autor)
    log("  title_block (em memoria): title=%s | c1=%s | c2=%s | c3=%s | c4=%s"
        % (tb.GetTitle(), tb.GetComment1(), tb.GetComment2(),
           tb.GetComment3(), tb.GetComment4()))


# --------------------------------------------------------------------------
# 2) Gerbers
# --------------------------------------------------------------------------
def gerar_gerbers(board, out, nome, silk_refs=False, silk_valores=False):
    camadas = camadas_do_board(board)
    pc = pcbnew.PLOT_CONTROLLER(board)
    po = pc.GetPlotOptions()
    po.SetOutputDirectory(out)
    po.SetPlotFrameRef(False)          # sem moldura/tabela nao entra no plot
    po.SetAutoScale(False)
    po.SetScale(1)
    po.SetMirror(False)
    po.SetUseGerberAttributes(False)   # formato classico, aceito por toda fab
    po.SetUseGerberProtelExtensions(True)
    po.SetExcludeEdgeLayer(False)
    po.SetSubtractMaskFromSilk(True)
    po.SetPlotViaOnMaskLayer(False)
    # Padrao de producao: silk SEM referencia e SEM valor (com 319 footprints
    # a serigrafia fica ilegivel e a casa nao precisa dela). As flags
    # --silk-com-refs / --silk-com-valores religam para inspecao/montagem.
    po.SetPlotReference(silk_refs)
    po.SetPlotValue(silk_valores)
    # KiCad 5.1: o SetCreateGerberJobFile e aceito mas nao emite .gbrjob
    # headless (verificado: 0 arquivos .gbrjob). O .gbrjob e escrito na
    # funcao gerar_gbrjob() pela GERBER_JOBFILE_WRITER.
    po.SetCreateGerberJobFile(True)

    gerados = {}
    for layer_id, layer_name in camadas:
        pc.SetLayer(layer_id)                      # antes de OpenPlotfile:
        pc.OpenPlotfile(nome, pcbnew.PLOT_FORMAT_GERBER, layer_name)  # a
        ok = bool(pc.PlotLayer())                 # extensao depende da layer
        pc.ClosePlot()
        # No 5.1 GetPlotFileName() ja devolve o caminho completo com a extensao
        # de protel correta (.gtl .g2 .g3 .gbl .gts .gbs .gto .gbo .gm1)
        bruto = pc.GetPlotFileName()
        if not ok or not os.path.isfile(bruto):
            raise RuntimeError("falha ao plotar a camada %s (PlotLayer=%s, "
                               "esperado=%s, existe=%s)"
                               % (layer_name, ok, bruto, os.path.isfile(bruto)))
        ext = os.path.splitext(bruto)[1]
        final = renomear_para_limpo(bruto, "%s_%s%s" % (nome, layer_name, ext))
        gerados[layer_name] = final
        log("  gerber %-10s -> %s" % (layer_name, os.path.basename(final)))
    return gerados


# --------------------------------------------------------------------------
# 3) .gbrjob
# --------------------------------------------------------------------------
def gerar_gbrjob(board, out, nome, gerbers):
    """Escreve o .gbrjob com a GERBER_JOBFILE_WRITER (unico caminho que
    funciona no 5.1 headless -- SetCreateGerberJobFile nao emite nada)."""
    destino = os.path.join(out, "%s.gbrjob" % nome)
    if os.path.exists(destino):
        os.remove(destino)
    w = pcbnew.GERBER_JOBFILE_WRITER(board)
    for layer_id, layer_name in camadas_do_board(board):
        caminho = gerbers.get(layer_name)
        if caminho:
            w.AddGbrFile(layer_id, os.path.basename(caminho))
    ok = bool(w.WriteJSONJobFile(destino))
    existe = os.path.exists(destino)
    log("  gbrjob: WriteJSONJobFile=%s arquivo=%s (%d bytes)"
        % (ok, os.path.basename(destino) if existe else "AUSENTE",
           os.path.getsize(destino) if existe else 0))
    if not existe:
        raise RuntimeError("a GERBER_JOBFILE_WRITER nao gerou o .gbrjob")
    return destino


# --------------------------------------------------------------------------
# 4) Excellon (PTH e NPTH) + mapa de furos
# --------------------------------------------------------------------------
def gerar_furos(board, out, nome):
    dw = pcbnew.EXCELLON_WRITER(board)
    # SetOptions(mirror=False, minimalHeader=False, offset, mergePTHNPTH=False)
    # mergePTHNPTH=False => dois arquivos separados, como a casa de fab pede.
    dw.SetOptions(False, False, pcbnew.wxPoint(0, 0), False)
    dw.SetFormat(True, pcbnew.EXCELLON_WRITER.DECIMAL_FORMAT, 3, 3)
    dw.SetRouteModeForOvalHoles(False)
    dw.CreateDrillandMapFilesSet(out, True, False)   # gera .drl, sem mapa ainda

    dris = {}
    for tag, sufixo in (("PTH", "-PTH.drl"), ("NPTH", "-NPTH.drl")):
        achado = [f for f in os.listdir(out) if f.endswith(sufixo)]
        if not achado:
            log("  drl %s: NAO encontrado" % tag)
            continue
        final = renomear_para_limpo(os.path.join(out, achado[0]),
                                    "%s%s" % (nome, sufixo))
        dris[tag] = final
        log("  drl  %-4s       -> %s" % (tag, os.path.basename(final)))
    return dris


def gerar_mapa_furos(board, out, nome, dris):
    """Mapa de furos. Usa o gerador do proprio KiCad (PS/PDF) e, alem disso,
    um PNG com matplotlib porque o PDF do 5.1 sai sem legibilidade em tela."""
    resultado = {}

    # (a) mapa do proprio KiCad -> PDF (nome: <board>-PTH-drl_map.pdf)
    dw = pcbnew.EXCELLON_WRITER(board)
    dw.SetOptions(False, False, pcbnew.wxPoint(0, 0), False)
    dw.CreateMapFilesSet(out)
    for f in sorted(os.listdir(out)):
        if "drl_map" not in f:
            continue
        # "v7_drone-PTH-drl_map.pdf" -> "drone_v7-PTH-drl_map.pdf"
        tag = f.split("-drl_map")[0].rsplit("-", 1)[-1]      # PTH / NPTH
        final = os.path.join(out, "%s-%s-drl_map.pdf" % (nome, tag))
        if os.path.abspath(os.path.join(out, f)) != os.path.abspath(final):
            if os.path.exists(final):
                os.remove(final)
            os.rename(os.path.join(out, f), final)
        resultado[tag + "_pdf"] = final
        log("  mapa de furos (KiCad) -> %s" % os.path.basename(final))

    # (b) PNG matplotlib, com furos PTH/NPTH separados e buracos de montagem
    #     destacados. Usa Circle() em unidades de dado (mm) para o diametro
    #     desenhado bater com o diametro real do furo.
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from matplotlib.patches import Circle

        buckets = {}
        for pad in board.GetPads():
            attr = pad.GetAttribute()
            if attr not in (ATTR_PTH, ATTR_NPTH):
                continue
            drill = pad.GetDrillSize()
            dia = pcbnew.ToMM(min(drill.x, drill.y))
            if dia <= 0.0:
                continue
            pos = pad.GetPosition()
            chave = (attr, round(dia, 3))
            buckets.setdefault(chave, []).append((pcbnew.ToMM(pos.x),
                                                 pcbnew.ToMM(pos.y)))

        fig, ax = plt.subplots(figsize=(12.5, 9.0), dpi=150)
        cores = {ATTR_PTH: "#1f77b4", ATTR_NPTH: "#d62728"}
        # desenha do maior para o menor, para os pequenos ficarem visiveis
        for (attr, dia), pts in sorted(buckets.items(), key=lambda k: -k[0][1]):
            for x, y in pts:
                ax.add_patch(Circle((x, y), dia / 2.0, fill=False,
                                    edgecolor=cores[attr], linewidth=0.8,
                                    linestyle="-" if attr == ATTR_PTH else "--"))

        bb = board.GetBoardEdgesBoundingBox()
        ax.set_xlim(pcbnew.ToMM(bb.GetX()) - 8, pcbnew.ToMM(bb.GetX() + bb.GetWidth()) + 8)
        ax.set_ylim(pcbnew.ToMM(bb.GetY()) - 8, pcbnew.ToMM(bb.GetY() + bb.GetHeight()) + 8)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        total_furos = sum(len(v) for v in buckets.values())
        ax.set_title("%s -- mapa de furos: %d furos em %d diamentros\n"
                     "circulo = diametro real do furo; tracejado vermelho = NPTH"
                     % (nome, total_furos, len(buckets)), fontsize=10)
        ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.6)

        handles = [Line2D([0], [0], color=cores[ATTR_PTH], lw=1.6,
                          label="PTH (metalizado)"),
                   Line2D([0], [0], color=cores[ATTR_NPTH], lw=1.6,
                          linestyle="--", label="NPTH (isolado)")]
        for (attr, dia), pts in sorted(buckets.items(), key=lambda k: -k[0][1]):
            tag = "" if attr == ATTR_PTH else " NPTH"
            handles.append(Line2D([0], [0], color=cores[attr], lw=0.8,
                                  linestyle="-" if attr == ATTR_PTH else "--",
                                  label="%.3f mm%s  x%d" % (dia, tag, len(pts))))
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0),
                  fontsize=7.5, framealpha=0.95, borderpad=0.8)
        fig.tight_layout()
        png = os.path.join(out, "%s_mapa_furos.png" % nome)
        fig.savefig(png, bbox_inches="tight")
        plt.close(fig)
        log("  mapa de furos (matplotlib PNG) -> %s (%d furos em %d diamentros: %s)"
            % (os.path.basename(png), total_furos, len(buckets),
               ", ".join("%.3fmm x%d" % (d, len(v))
                         for (_a, d), v in sorted(buckets.items(), key=lambda k: -k[0][1]))))
        resultado["png"] = png
    except Exception as exc:                                  # pragma: no cover
        log("  AVISO: matplotlib indisponivel ou falhou: %s" % exc)
    return resultado


# --------------------------------------------------------------------------
# 5) Pick-and-place
# --------------------------------------------------------------------------
def _mil(mm):
    """mil(esimo de mm) -> string inteiro, como o KiCad escreve no .pos"""
    return str(int(round(mm * 1000.0)))


def gerar_pnp(board, out, nome):
    top, bottom, sem_flag = [], [], []
    for mod in board.GetModules():
        ref = mod.GetReference()
        if not ref:
            continue
        pos = mod.GetPosition()
        rot = mod.GetOrientationDegrees() % 360.0
        x = pcbnew.ToMM(pos.x)
        y = pcbnew.ToMM(pos.y)
        lado = "Bottom" if mod.GetLayer() == pcbnew.B_Cu else "Top"
        # KiCad 5.1: IsPlaced() == False equivale ao checkbox "Not in position
        # files" do editor. Os footprints gerados por script NAO trazem esse
        # bit setado, o que zeraria o P&P inteiro. Aqui todos saem no arquivo
        # (a fab precisa deles) e a lista dos que estao marcados e reportada
        # em <nome>-PNA-FLAGS.txt para conference manual.
        if not mod.IsPlaced():
            sem_flag.append(ref)
        (bottom if lado == "Bottom" else top).append((ref, x, y, rot, mod.GetValue()))

    def linhas(lista):
        return ["%s\t%s\t%s\t%s\t%s" % (r, _mil(x), _mil(y),
                                         "%.4f" % rot, v)
                for r, x, y, rot, v in sorted(lista)]

    arquivos = {}
    for tag, lista in (("Top", top), ("Bottom", bottom)):
        cab = ["# P&P generated by gera_pacote_fab.py",
               "# Units: mils of mm (PosX/PosY) and degrees (Rot)",
               "# Ref       PosX        PosY        Rot       Value",
               "##"]
        pos = os.path.join(out, "%s-%s.pos" % (nome, tag))
        with open(pos, "w") as fh:
            fh.write("\n".join(cab + linhas(lista)) + "\n")
        arquivos["pos_" + tag] = pos
        log("  pick-and-place %-6s -> %s (%d componentes)"
            % (tag, os.path.basename(pos), len(lista)))

    # CSV agregado, os dois lados no mesmo arquivo
    csv = os.path.join(out, "%s-pos.csv" % nome)
    with open(csv, "w") as fh:
        fh.write("Designator,Value,PosX_mm,PosY_mm,Rotation_deg,Side\n")
        for lado, lista in (("Top", top), ("Bottom", bottom)):
            for r, x, y, rot, v in sorted(lista):
                fh.write('"%s","%s",%.4f,%.4f,%.4f,%s\n' % (r, v, x, y, rot, lado))
    arquivos["csv"] = csv
    log("  pick-and-place CSV    -> %s (%d linhas de dados)"
        % (os.path.basename(csv), len(top) + len(bottom)))
    if sem_flag:
        flag_txt = os.path.join(out, "%s-PNA-FLAGS.txt" % nome)
        with open(flag_txt, "w") as fh:
            fh.write("Footprints SEM o bit 'placed' (KiCad: 'Not in position files')\n")
            fh.write("=%s*%d de %d footprints.\n"
                     % ("=" * 70, len(sem_flag), len(top) + len(bottom)))
            fh.write("Eles SAIRAM no .pos/.csv mesmo assim; se algum destes nao deve\n")
            fh.write("ser montado, remova a linha a mao antes de mandar a casa.\n\n")
            for i in range(0, len(sem_flag), 8):
                fh.write("  " + " ".join("%-10s" % r
                                         for r in sem_flag[i:i + 8]) + "\n")
        arquivos["flags"] = flag_txt
        log("  P&P flags: %d de %d footprints sem bit 'placed' -> %s"
            % (len(sem_flag), len(top) + len(bottom), os.path.basename(flag_txt)))
    return arquivos, top, bottom, sem_flag


# --------------------------------------------------------------------------
# 6) DRC
# --------------------------------------------------------------------------
def gerar_drc(board, out, nome, board_path, gerbers, dris, n_top, n_bot, n_sem_flag):
    """KiCad 5.1.9 nao expoe API de DRC no Python e o pcbnew e GTK: nao ha
    como rodar o DRC headless nesta maquina.  Em vez de inventar um relatorio,
    o script escreve a nota com o motivo e o workaround."""
    rpt = os.path.join(out, "%s-DRC.rpt" % nome)
    tem_api = any(k in dir(pcbnew) for k in ("DRC", "DRC_ENGINE", "RunDRC"))
    linhas = [
        "RELATORIO DE DRC -- %s" % nome,
        "gerado em: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "board: %s" % board_path,
        "pcbnew: %s" % pcbnew.GetBuildVersion(),
        "",
        "RESULTADO: NAO DISPONIVEL NESTA MAQUINA (DRC nao executado).",
        "",
        "MOTIVO:",
        "  1. O modulo Python do pcbnew 5.1.9 nao exporta nenhuma API de DRC.",
        "     Varredura de dir(pcbnew) nao encontra DRC, DRC_ENGINE nem RunDRC;"
        " a API Python visivel e %s."
        % ", ".join(sorted(k for k in dir(pcbnew) if "DRC" in k.upper())),
        "  2. O pcbnew 5.1 so roda o DRC pela interface grafica (wxWidgets/GTK).",
        "     Nao existe kicad-cli nesta maquina para o 'kicad-cli pcb drc'.",
        "",
        "COMO GERAR O DRC NO v8 (nao automatizavel aqui):",
        "   /usr/bin/pcbnew %s" % board_path,
        "   menu 'Inspect' -> 'Design Rules Checker' -> 'Run DRC' -> 'Save Report'",
        "",
        "VERIFICACOES FEITAS PELO SCRIPTO (substituem parcialmente o DRC):",
    ]
    board_saida = os.path.join(out, "_inspecao", "board_para_drc.kicad_pcb")
    os.makedirs(os.path.dirname(board_saida), exist_ok=True)
    pcbnew.SaveBoard(board_saida, board)
    linhas += [
        "  - board gravado em %s para inspecao manual" % board_saida,
        "  - %d camadas de cobre plotadas sem erro" % sum(
            1 for k in gerbers if k.endswith("_Cu")),
        "  - %d arquivos de furo gerados" % len(dris),
        "  - %d footprints exportados para pick-and-place (Top %d + Bottom %d)"
        % (n_top + n_bot, n_top, n_bot),
        "  - %d desses %d footprints nao tem o bit 'placed' setado no board "
        "(KiCad: 'Not in position files'); entraram assim mesmo no .pos/.csv e"
        % (n_sem_flag, n_top + n_bot),
        "    foram listados em %s-PNA-FLAGS.txt para conference manual."
        % nome,
        "",
        "ISTO NAO SUBSTITUI O DRC DA CASA: regras de clearance, largura de",
        "trilha e mascara continuam NAO VERIFICADAS por este arquivo.",
    ]
    with open(rpt, "w") as fh:
        fh.write("\n".join(linhas) + "\n")
    log("  DRC: %s (API presente no pcbnew? %s -> relatorio de indisponibilidade)"
        % (os.path.basename(rpt), tem_api))
    return rpt


# --------------------------------------------------------------------------
# 7) README do pacote
# --------------------------------------------------------------------------
def gerar_readme(out, nome, projeto, rev, data, autor, board_path, stats,
                 gerbers, dris, job, mapas, pnp_files, n_top, n_bot, rpt, camadas):
    txt = os.path.join(out, "README_GERBER.txt")
    L = []
    a = L.append
    a("PACOTE DE FABRICACAO -- %s" % nome)
    a("=" * 60)
    a("projeto ........: %s" % projeto)
    a("revisao ........: %s" % rev)
    a("data ...........: %s" % data)
    a("autor ..........: %s" % autor)
    a("board de origem : %s" % board_path)
    a("gerado em ......: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    a("pcbnew .........: %s" % pcbnew.GetBuildVersion())
    a("")
    a("CONTEUDO DO PACOTE")
    a("-" * 60)
    a("GERBERS (RS-274X, extensao de protel, na ordem F -> B):")
    for _lid, k in camadas:
        if k not in gerbers:
            continue
        a("  %-26s %-42s %d bytes"
          % (os.path.basename(gerbers[k]), PAPEL_CAMADA.get(k, ""),
             os.path.getsize(gerbers[k])))
    a("")
    a("FUROS (Excellon, PTH e NPTH separados):")
    for k in ("PTH", "NPTH"):
        if k in dris:
            a("  %-26s furos %s, %d bytes"
              % (os.path.basename(dris[k]), " plated thru-hole "
                 if k == "PTH" else "nao plated thru-hole",
                 os.path.getsize(dris[k])))
    a("")
    a("JOB FILE:")
    a("  %-26s %d bytes" % (os.path.basename(job), os.path.getsize(job)))
    a("")
    a("MAPA DE FUROS:")
    for k, v in sorted(mapas.items()):
        a("  %-26s %d bytes" % (os.path.basename(v), os.path.getsize(v)))
    a("")
    a("PICK-AND-PLACE (PosX/PosY em milesimos de mm, rot em graus):")
    a("  %-26s %d componentes (camada Top)"
      % (os.path.basename(pnp_files["pos_Top"]), n_top))
    a("  %-26s %d componentes (camada Bottom)"
      % (os.path.basename(pnp_files["pos_Bottom"]), n_bot))
    a("  %-26s %d componentes (Top+Bottom)"
      % (os.path.basename(pnp_files["csv"]), n_top + n_bot))
    a("")
    a("RELATORIOS:")
    a("  %-26s ver o arquivo: o DRC nao roda nesta maquina" % os.path.basename(rpt))
    a("")
    a("RESUMO DO BOARD")
    a("-" * 60)
    for k, v in stats.items():
        a("  %-34s %s" % (k, v))
    a("")
    a("COMO ESTE PACOTE FOI NOMEADO")
    a("-" * 60)
    a("  O .kicad_pcb de origem NAO tem bloco 'title_block'. O pcbnew 5.1 monta o")
    a("  nome do plot como '<basename do board>-<plot>.<ext>'; sem basename ele")
    a("  emite '-drone_F_Cu.gtl' (hifen na frente, mesmo nome em v1..v7).")
    a("  Aqui o title_block e preenchido EM MEMORIA antes do plot e cada arquivo")
    a("  e renomeado para '%s_<Camada>.<ext>', sem hifen e com a versao." % nome)
    a("  O .kicad_pcb do repositorio NAO foi alterado: o title block serve so ao")
    a("  plot e ao .gbrjob desta pasta.")
    a("")
    a("NOTA SOBRE O .gbrjob")
    a("-" * 60)
    a("  O pcbnew 5.1 aceita SetCreateGerberJobFile(True) mas nao emite nenhum")
    a("  arquivo .gbrjob em modo headless (verificado: 0 arquivos). O job file")
    a("  desta pasta foi escrito pela GERBER_JOBFILE_WRITER.WriteJSONJobFile(),")
    a("  que e o unico caminho que produz o arquivo nesta versao.")
    a("")
    a("NOTA SOBRE O .drr")
    a("-" * 60)
    a("  EXCELLON_WRITER.GenDrillReportFile() ABORTA o processo (terminate:")
    a("  throwing an instance of 'IO_ERROR' / Aborted) no pcbnew 5.1.9 headless.")
    a("  Por isso nao ha .drr: no lugar entraram o PDF de mapa de furos gerado")
    a("  pelo proprio KiCad (CreateMapFilesSet) e um PNG equivalente em matplotlib.")
    a("")
    a("NOTA SOBRE O DRC")
    a("-" * 60)
    a("  O modulo Python do pcbnew 5.1.9 nao expoe API de DRC e o pcbnew e GTK,")
    a("  sem display: o DRC so roda na interface grafica. Ver %s." % os.path.basename(rpt))
    a("  A copia do board com o title_block preenchido, pronta para abrir no")
    a("  pcbnew e rodar o DRC na mao, esta em:")
    a("    _inspecao/board_para_drc.kicad_pcb")
    a("")
    a("NOTA SOBRE A SERIGRAFIA")
    a("-" * 60)
    a("  A serigrafia foi plotada SEM referencia e SEM valor dos componentes")
    a("  (padrao de producao: com %d footprints o texto fica ilegivel). Para"
      % stats.get("footprints", 0))
    a("  inspecao ou montagem use as flags --silk-com-refs e --silk-com-valores.")
    with open(txt, "w") as fh:
        fh.write("\n".join(L) + "\n")
    log("  README_GERBER.txt -> %s" % os.path.basename(txt))
    return txt


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Gera o pacote de fabricacao completo de um .kicad_pcb")
    ap.add_argument("board", help="caminho do .kicad_pcb de entrada")
    ap.add_argument("--out", required=True, help="pasta de saida do pacote")
    ap.add_argument("--projeto", default="drone (FPGA/controlador de voo)")
    ap.add_argument("--rev", default="v1")
    ap.add_argument("--data", default=datetime.date.today().isoformat())
    ap.add_argument("--autor", default="Jailton")
    ap.add_argument("--silk-com-refs", action="store_true",
                    help="plota a referencia dos footprints na serigrafia "
                         "(desligado por padrao: bom para producao)")
    ap.add_argument("--silk-com-valores", action="store_true",
                    help="plota o valor dos footprints na serigrafia")
    args = ap.parse_args()

    board_path = os.path.abspath(args.board)
    if not os.path.isfile(board_path):
        sys.exit("ERRO: board nao encontrado: %s" % board_path)
    out = os.path.abspath(args.out)
    if os.path.isfile(out):
        sys.exit("ERRO: --out aponta para arquivo, nao pasta: %s" % out)
    os.makedirs(out, exist_ok=True)

    nome = nome_base(board_path)
    log("PACOTE DE FABRICACAO")
    log("  board   : %s" % board_path)
    log("  saida   : %s" % out)
    log("  nome    : %s" % nome)
    log("  pcbnew  : %s" % pcbnew.GetBuildVersion())

    board = pcbnew.LoadBoard(board_path)
    # board anonimo: o pcbnew nao deve herdar 'v8_drone' e gerar 'v8_drone-drone_v8'
    board.SetFileName("")

    mods = list(board.GetModules())
    pads = list(board.GetPads())
    n_pth = sum(1 for p in pads if p.GetAttribute() == ATTR_PTH)
    n_npth = sum(1 for p in pads if p.GetAttribute() == ATTR_NPTH)
    n_smd = sum(1 for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD)
    bb = board.GetBoardEdgesBoundingBox()
    stats = {
        "footprints": len(mods),
        "pads": len(pads),
        "pads PTH (com furo metalizado)": n_pth,
        "pads NPTH (furo isolado)": n_npth,
        "pads SMD (sem furo)": n_smd,
        "nets": board.GetNetCount(),
        "camadas de cobre": board.GetCopperLayerCount(),
        "dimensoes da placa (mm)": "%.2f x %.2f" % (pcbnew.ToMM(bb.GetWidth()),
                                                     pcbnew.ToMM(bb.GetHeight())),
        "espessura do substrato (mm)": "%.2f"
                                       % (board.GetDesignSettings()
                                          .GetBoardThickness() / 1e6),
    }
    log("  resumo  : %d footprints, %d pads (%d PTH, %d NPTH, %d SMD), %d nets, %d camadas de cobre"
        % (len(mods), len(pads), n_pth, n_npth, n_smd, board.GetNetCount(),
           board.GetCopperLayerCount()))

    log("  -- title_block --")
    aplicar_title_block(board, nome, args.projeto, args.rev, args.data, args.autor)

    log("  -- gerbers --")
    gerbers = gerar_gerbers(board, out, nome, args.silk_com_refs,
                             args.silk_com_valores)

    log("  -- job file --")
    job = gerar_gbrjob(board, out, nome, gerbers)

    log("  -- furos --")
    dris = gerar_furos(board, out, nome)
    mapas = gerar_mapa_furos(board, out, nome, dris)

    log("  -- pick-and-place --")
    pnp_files, top, bottom, sem_flag = gerar_pnp(board, out, nome)

    log("  -- relatorios --")
    rpt = gerar_drc(board, out, nome, board_path, gerbers, dris,
                    len(top), len(bottom), len(sem_flag))

    readme = gerar_readme(out, nome, args.projeto, args.rev, args.data, args.autor,
                          board_path, stats, gerbers, dris, job, mapas, pnp_files,
                          len(top), len(bottom), rpt, camadas_do_board(board))

    log("  -- inventario final --")
    total = 0
    for f in sorted(os.listdir(out)):
        p = os.path.join(out, f)
        if os.path.isfile(p):
            log("    %-34s %9d bytes" % (f, os.path.getsize(p)))
            total += 1
    insp = os.path.join(out, "_inspecao")
    if os.path.isdir(insp):
        for f in sorted(os.listdir(insp)):
            p = os.path.join(insp, f)
            if os.path.isfile(p):
                log("    _inspecao/%-27s %9d bytes" % (f, os.path.getsize(p)))
                total += 1
    log("  TOTAL: %d arquivos em %s" % (total, out))
    log("  manifest: %s" % readme)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
