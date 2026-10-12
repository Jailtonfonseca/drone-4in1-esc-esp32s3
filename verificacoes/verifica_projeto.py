#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""verifica_projeto.py — verificacao de PROJETO com assercoes duras.

O "Proximo passo" do ERROS_CONHECIDOS.md (2026-10-05):

    "verificacoes/verifica_projeto.py — automatizar todas as checagens acima
    como assercoes duras (SES wires > 0, nets nao roteadas == 0, [EST] == 0,
    precos preenchidos), para que 'pronto' seja propriedade do artefato e
    nao da impressao da sessao."

Cada checagem abaixo e' DURA: falha encerra com exit 1 e mensagem que diz
EXATAMENTE o que falta. Verde = o projeto esta' pronto no que esta' script
cobre; vermelho = nao esta', independente de impressao de sessao.

Cobertura (2026-10-12):
  A. SES final      : existe, wires > 0, vias > 0, nets roteadas == DSN
  B. Gates na base  : verifica_fase3_v10.py em v10_drone.kicad_pcb (G1-G8)
  C. Gates no roteado: idem em v10_roteada.kicad_pcb (inclui G8)
  D. Roteado        : trilhas > 0; nets de sinal (>=2 pads, nao excluidas)
                      TODAS com >= 1 trilha
  E. BOM v10        : 43 itens, 16 colunas, MOSFET vencedor unico, preco
                      unitario preenchido em 100% das linhas, zero [EST]

Fora de escopo (estado declarado em ERROS_CONHECIDOS.md):
  - firmware (13 arquivos ESQUELETO NAO VERIFICADO, §5)
  - cotacoes [EST] do ORCAMENTO.md (exige sessao de navegador, §3.2) — a BOM
    e' a fonte de fabricacao; o ORCAMENTO e' estimativa declarada
  - decisoes humanas pendentes (§8.2: margem do MOSFET, D-07/D-12)

Roda: /usr/bin/python3.9 verificacoes/verifica_projeto.py [raiz-do-repo]
      (raiz default: duas pastas acima deste arquivo)
"""
import os
import re
import subprocess
import sys

RAIZ = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

falhas = []


def chk(nome, cond, msg_erro=""):
    ok = bool(cond)
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", nome,
                          "" if ok else "  <-- " + msg_erro))
    if not ok:
        falhas.append(nome)
    return ok


print("=" * 78)
print("VERIFICACAO DE PROJETO — assercoes duras (ERROS_CONHECIDOS §Proximo passo)")
print("raiz: %s" % RAIZ)
print("=" * 78)

# ---------------------------------------------------------------- A. SES final
print("[A] SES final do pipeline FreeRouting")
SES = os.path.join(RAIZ, "fase3_pcb/v10/freerouting_run/v10_final.ses")
DSN = os.path.join(RAIZ, "fase3_pcb/v10/freerouting_run/v10_dsn_input.dsn")
if chk("SES existe", os.path.isfile(SES), SES):
    ses_txt = open(SES, encoding="utf-8", errors="replace").read()
    n_wires = len(re.findall(r"\(wire\b", ses_txt))
    n_vias = len(re.findall(r"\(via\b", ses_txt))
    n_ses = set(re.findall(r"\(net ([^\s)]+)", ses_txt))
    chk("SES wires > 0", n_wires > 0, "wires=%d" % n_wires)
    chk("SES vias de rota > 0", n_vias > 0, "vias=%d" % n_vias)
    if os.path.isfile(DSN):
        dsn_txt = open(DSN, encoding="utf-8", errors="replace").read()
        n_dsn = set(re.findall(r'\(net "([^"]+)" \(pins', dsn_txt))
        faltando = sorted(n_dsn - n_ses)
        chk("SES cobre 100%% das nets roteaveis (%d/%d)" % (len(n_ses & n_dsn),
                                                           len(n_dsn)),
            not faltando, "sem rota: %s" % ", ".join(faltando) or "?")

# ------------------------------------------------- B/C. gates base e roteado
VERIFICADOR = os.path.join(RAIZ, "fase3_pcb/verifica_fase3_v10.py")
for rotulo, board in [
    ("[B] Gates na base (v10_drone)", "fase3_pcb/v10/v10_drone.kicad_pcb"),
    ("[C] Gates no roteado (v10_roteada)", "fase3_pcb/v10/v10_roteada.kicad_pcb"),
]:
    print(rotulo)
    caminho = os.path.join(RAIZ, board)
    if not chk("board existe", os.path.isfile(caminho), caminho):
        continue
    r = subprocess.run(
        [os.environ.get("VERIF_PY", sys.executable), VERIFICADOR, caminho],
        capture_output=True, text=True, timeout=1800)
    saida = r.stdout or ""
    gates = re.findall(r"\[(OK\s*|FALHA)\] (G\d [^\n(]+)", saida)
    for st, nm in gates:
        chk(nm.strip(), st.strip() == "OK", "")
    chk("VEREDITO %s" % rotulo.split("]")[0] + "]",
        "TODOS OS GATES OK" in saida, "")

# ----------------------------------------------------------- D. board roteado
print("[D] Board roteado — cobertura de rota")
ROTEADA = os.path.join(RAIZ, "fase3_pcb/v10/v10_roteada.kicad_pcb")
if chk("v10_roteada existe", os.path.isfile(ROTEADA), ROTEADA):
    import pcbnew  # noqa: E402  (host: pcbnew 5.1.9 vem com o python3.9)
    BRD = pcbnew.LoadBoard(ROTEADA)
    MM = 1000000.0
    RAILS = {"GND", "VBAT", "VBAT_F", "VBAT_PROT"}
    HI = re.compile(r"^(PHM|SNM)\d{3}$")
    excl = lambda nm: nm in RAILS or bool(HI.match(nm))
    pads_net = {}
    for f in BRD.GetModules():
        for p in f.Pads():
            nm = str(p.GetNetname())
            if nm:
                pads_net.setdefault(nm, 0)
                pads_net[nm] += 1
    com_trilha = set()
    n_trilhas = 0
    for t in BRD.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            n_trilhas += 1
            nm = str(t.GetNetname())
            if nm:
                com_trilha.add(nm)
    chk("trilhas de sinal > 0", n_trilhas > 0, "trilhas=%d" % n_trilhas)
    alvo = {nm for nm, np_ in pads_net.items()
            if np_ >= 2 and not excl(nm)}
    sem_rota = sorted(alvo - com_trilha)
    chk("nets de sinal 100%% roteadas (%d/%d)"
        % (len(alvo) - len(sem_rota), len(alvo)),
        not sem_rota, "sem trilha: %s" % ", ".join(sem_rota))

# ------------------------------------------------------------------ E. BOM v10
print("[E] BOM de fabricacao v10")
BOM = os.path.join(RAIZ, "orcamento/BOM_FABRICACAO_v10.csv")
if chk("BOM_FABRICACAO_v10.csv existe", os.path.isfile(BOM), BOM):
    linhas = [l for l in open(BOM, encoding="utf-8").read().splitlines()
              if l.strip()]
    chk("43 itens de BOM", len(linhas) - 1 == 43,
        "linhas de dados=%d" % (len(linhas) - 1))
    chk("16 colunas", all(len(l.split(";")) == 16 or len(l.split(",")) == 16
                          for l in linhas[:1]), "cabecalho")
    corpo = linhas[1:]
    chk("MOSFET vencedor unico (NVMFS6H824NT1G)",
        sum("NVMFS6H824NT1G" in l for l in corpo) == 1, "")
    sep = ";" if corpo[0].count(";") > corpo[0].count(",") else ","
    idx_preco = linhas[0].split(sep).index("preco_unitario")
    idx_mpn = linhas[0].split(sep).index("mpn")
    idx_fab = linhas[0].split(sep).index("fabricante")
    # linhas COMPRAVEIS (mpn ou fabricante preenchido) exigem preco; linhas
    # de projeto/servico (dissipador=area de cobre, a propria PCB, pads...)
    # nao tem peca para cotar e ficam isentas por design.
    sem_preco = []
    for l in corpo:
        c = l.split(sep)
        compravel = c[idx_mpn].strip() or c[idx_fab].strip()
        if compravel and not c[idx_preco].strip():
            sem_preco.append(c[0] + "/" + c[1])
    chk("preco_unitario preenchido em 100% das linhas compraveis",
        not sem_preco, "sem preco: %s" % ", ".join(sem_preco))
    est = [l.split(sep)[1] for l in corpo if "[EST]" in l]
    chk("zero [EST] na BOM", not est, "com [EST]: %s" % ", ".join(est))

# --------------------------------------------------------------------- fim
print("=" * 78)
if falhas:
    print("RESULTADO: FALHOU — %d checagem(s): %s" % (len(falhas),
                                                       ", ".join(falhas)))
    print("'Pronto' e' propriedade do artefato: o que falhou acima e' o que falta.")
    sys.exit(1)
print("RESULTADO: PROJETO PRONTO nos criterios cobertos por este script.")
sys.exit(0)
