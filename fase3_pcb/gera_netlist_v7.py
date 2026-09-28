#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""Gera o netlist de producao (.net) da placa v7 a partir do board v7.

Entrada : fase3_pcb/v7/v7_drone.kicad_pcb   (somente LEITURA, nunca alterado)
Saida  : fase3_pcb/v7/v7_drone.net

Formato: s-expression de netlist do KiCad/Eeschema, com os blocos
(components ...), (libraries ...), (libparts ...) e (nets ...).

Como o .kicad_pcb da versao 20171130 (KiCad 5.1) NAO grava o "lib nickname"
do footprint (GetLibNickname() devolve vazio para os 319 modulos), a biblioteca
de cada footprint e resolvida por nome consultando /usr/share/kicad/modules.
Os footprints desenhados a mao no gerador (nome vazio) recebem a biblioteca
sintetica HandDrawn_Inline.

Os nomes das nets sao lidos do proprio arquivo do board, na ordem em que o
board as declara, e comparados com o que o pcbnew reporta. Divergencia aborta.

Indentacao: as entradas "(net ...)" usam 2 espacos (e nao os 4 do gerador
nativo do Eeschema) para que o gate do plano,
    grep -c "^  (net " v7_drone.net
conte as nets. A s-expresao resultante e semanticamente identica.

Uso: /usr/bin/python3.9 fase3_pcb/gera_netlist_v7.py
"""

import os
import re
import sys
import datetime
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "v7", "v7_drone.kicad_pcb")
SAIDA = os.path.join(HERE, "v7", "v7_drone.net")
RAIZ_MODULES = "/usr/share/kicad/modules"
# footprints sem nome no board: desenhados a mao dentro de gera_pcb_v7.py
LIB_SINTETICA = "HandDrawn_Inline"


def log(*a):
    print(" ".join(str(x) for x in a))


def indice_bibliotecas(raiz):
    """nome do footprint -> lista ordenada de nicknames de biblioteca."""
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


def bloco_modulo_por_ref(caminho):
    """Extrai, na ordem do arquivo, os modulos: ref, tstamp, nome, tem (at)."""
    linhas = open(caminho, "r", encoding="utf-8").read().split("\n")
    saida, profundidade, atual, dentro = [], 0, [], False
    for ln in linhas:
        s = ln.strip()
        if s.startswith("(module "):
            dentro, profundidade, atual = True, 0, []
        if dentro:
            atual.append(ln)
            profundidade += ln.count("(") - ln.count(")")
            if profundidade == 0:
                dentro = False
                bloco = "\n".join(atual)
                m_ref = re.search(r"fp_text reference (\S+)", bloco)
                m_ts = re.search(r"^\s*\(tstamp (\S+)\)", bloco, re.M)
                m_nm = re.search(r"^\s*\(module\s+(\S+)\s", bloco, re.M)
                saida.append({
                    "ref": m_ref.group(1) if m_ref else None,
                    "tstamp": m_ts.group(1) if m_ts else None,
                    "nome": m_nm.group(1) if m_nm else None,
                    "tem_at": re.search(r"^\s*\(at ", bloco, re.M) is not None,
                })
    return saida


def aspa(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    if not os.path.isfile(BOARD):
        sys.exit("board nao encontrado: %s" % BOARD)
    board = pcbnew.LoadBoard(BOARD)
    modulos = list(board.GetModules())
    fonte = open(BOARD, "r", encoding="utf-8").read()

    # --- 1. nets: nomes e ordem exatamente como o board declara ---
    # o board aceita o nome com ou sem aspas: net 0 vem como "" e as demais
    # vem cruas, ex.: (net 1 VBAT_PROT)
    declaradas = []
    for cod, nome_q, nome_cru in re.findall(
            r'^  \(net (\d+) (?:"([^"]*)"|(\S+))\)\s*$', fonte, re.M):
        declaradas.append((int(cod), nome_q if nome_q != "" or nome_cru == "" else nome_cru))
    if not declaradas:
        sys.exit("nenhuma declaracao '(net ...)' encontrada no board")
    log("board            : %s" % os.path.relpath(BOARD, HERE))
    log("modulos          : %d" % len(modulos))
    log("nets declaradas  : %d" % len(declaradas))

    # --- 2. conferencia nome/netcode: pcbnew vs arquivo ---
    divergencias = []
    for cod, nome in declaradas:
        ni = board.FindNet(nome) if nome else None
        if nome and ni is not None and ni.GetNet() != cod:
            divergencias.append((cod, nome, ni.GetNet()))
    if divergencias:
        sys.exit("divergencia netcode pcbnew/arquivo: %r" % divergencias[:5])
    log("conferencia pcbnew x arquivo: OK (netcodes identicos)")

    # --- 3. componentes, na ordem do board ---
    blocos = bloco_modulo_por_ref(BOARD)
    if len(blocos) != len(modulos):
        sys.exit("divergencia: %d modulos no arquivo x %d no pcbnew" % (len(blocos), len(modulos)))

    idx_libs = indice_bibliotecas(RAIZ_MODULES)
    componentes = []
    libs_usadas = {}
    ambiguos = []
    for mod, bl in zip(modulos, blocos):
        ref = mod.GetReference()
        if ref != bl["ref"]:
            sys.exit("ordem divergente: %s != %s" % (ref, bl["ref"]))
        nome = str(mod.GetFPID().GetLibItemName())
        if nome:
            cands = idx_libs.get(nome, [])
            if not cands:
                sys.exit("footprint '%s' (%s) nao encontrado em %s" % (nome, ref, RAIZ_MODULES))
            lib = cands[0]
            if len(cands) > 1:
                ambiguos.append((nome, cands))
        else:
            lib = LIB_SINTETICA
        componentes.append({
            "ref": ref,
            "valor": str(mod.GetValue()),
            "lib": lib,
            "nome": nome or bl["ref"],
            "tstamp": bl["tstamp"],
        })
        libs_usadas.setdefault(lib, set()).add(nome or bl["ref"])

    # --- 4. nos das nets: (netcode -> [(ref, pinho)]) na ordem do board ---
    nos = {}
    for mod in modulos:
        ref = mod.GetReference()
        for p in mod.Pads():
            nos.setdefault(p.GetNetCode(), []).append((ref, str(p.GetName())))
    log("nos de rede      : %d" % sum(len(v) for v in nos.values()))

    # --- 5. emissao ---
    agora = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    versao = pcbnew.GetBuildVersion()
    L = []
    a = L.append
    a("(export (version D)")
    a("  (design")
    a('    (source "%s")' % os.path.relpath(BOARD, os.path.dirname(HERE)).replace("\\", "/"))
    a('    (date "%s")' % agora)
    a('    (tool "pcbnew %s - gera_netlist_v7.py")' % versao)
    a('    (comment (rev "v7"))')
    a('    (comment (comment "1"))')
    a('    (comment (comment "netlist de PRODUCAO derivado do board v7 '
      '(%s); %d footprints, %d nets com pad; geometria nao alterada")'
      % (os.path.basename(BOARD), len(componentes),
         sum(1 for c, _ in declaradas if c != 0)))
    a('    (comment (comment "pintype passive: o board nao carrega esquematico, '
      'entao nao ha tipo eletrico disponivel"))')
    a("  )")

    a("  (components")
    for c in componentes:
        a("  (comp (ref %s)" % aspa(c["ref"]))
        a('    (value %s)' % aspa(c["valor"]))
        a('    (footprint %s)' % aspa("%s:%s" % (c["lib"], c["nome"])))
        a('    (tstamps "/%s")' % (c["tstamp"] or "0"))
        a("  )")
    a("  )")

    a("  (libraries")
    for lib in sorted(libs_usadas):
        a('  (library (logical %s) (source %s) (descr %s))'
          % (aspa(lib), aspa(lib),
             aspa("biblioteca de footprints instantiate pela placa v7")))
    a("  )")

    a("  (libparts")
    for lib in sorted(libs_usadas):
        for nome in sorted(libs_usadas[lib]):
            a('  (libpart (libsource %s) (part %s)' % (aspa(lib), aspa(nome)))
            a('    (fields (name (at 0 0 0) (size 0 0) (effects hide)))')
            a('    (pintype "passive")')
            a("  )")
    a("  )")

    a("  (nets")
    escritas = 0
    for cod, nome in declaradas:
        if cod == 0:
            continue  # net 0 = pads sem net, nao e uma rede de producao
        a('  (net (code "%d") (name %s)' % (cod, aspa(nome)))
        for ref, pino in nos.get(cod, []):
            a('    (node (ref %s) (pin %s) (pintype "passive"))' % (aspa(ref), aspa(pino)))
        a("  )")
        escritas += 1
    a("  )")
    a(")")

    with open(SAIDA, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    # --- 6. validacao final ---
    gerado = open(SAIDA, "r", encoding="utf-8").read().split("\n")
    cnt = sum(1 for ln in gerado if ln.startswith("  (net "))
    esperado = sum(1 for c, _ in declaradas if c != 0)
    log("")
    log("saida            : %s" % os.path.relpath(SAIDA, HERE))
    log("components       : %d" % len(componentes))
    log("libraries        : %d" % len(libs_usadas))
    log("libparts         : %d" % sum(len(v) for v in libs_usadas.values()))
    log("grep -c '^(net ' : %d  (esperado %d)" % (cnt, esperado))
    if cnt != esperado:
        sys.exit("FALHA: contagem de nets divergente (%d != %d)" % (cnt, esperado))
    if ambiguos:
        log("footprints ambiguos (escolhido o 1o candidato, ordem alfabetica): %d" % len(ambiguos))
        for nome, cands in ambiguos:
            log("   %-34s -> %s" % (nome, cands))
    log("RESULTADO: OK")


if __name__ == "__main__":
    main()
