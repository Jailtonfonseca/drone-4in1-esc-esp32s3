# PACOTE_FAB.md — etapa E4 (pacote de fabricação do board v8)

Data: 2026-09-28 · pcbnew `5.1.9+dfsg1-1+deb11u1` · Python `/usr/bin/python3.9`

---

## 1. O que foi criado

| Caminho | Papel |
|---|---|
| `fase3_pcb/gera_pacote_fab.py` | gerador único do pacote de fabricação (gerbers, furos, `.gbrjob`, mapa de furos, pick-and-place, relatórios) |
| `fase3_pcb/v7_pacote_teste/` | pacote gerado de **prova** contra a v7 (22 arquivos) |
| `fase3_pcb/v8/PACOTE_FAB.md` | este documento |

`gera_pcb_v7.py`, `gera_pcb_v8.py`, `rota_v7.py`, `rota_v8.py`, `v7_drone.kicad_pcb` e
`v8_drone.kicad_pcb` **não foram alterados**.

---

## 2. Comando exato para gerar o pacote final do v8

Assim que `fase3_pcb/v8/v8_drone.kicad_pcb` estiver **definitivo** (roteamento
completo, gates do `verifica_fase3_v8.py` verdes):

```console
cd /opt/jupyter/work/drone && rm -rf fase3_pcb/v8_pacote_fab && /usr/bin/python3.9 fase3_pcb/gera_pacote_fab.py fase3_pcb/v8/v8_drone.kicad_pcb --out fase3_pcb/v8_pacote_fab --rev v8 --autor "Jailton" --data 2026-09-28
```

O nome versionado (`drone_v8`) é deduzido do nome do board (`v8_drone.kicad_pcb`);
não é preciso passar nada além do caminho e de `--out`.

Opções úteis:

| Flag | Efeito |
|---|---|
| `--silk-com-refs` | plota a **referência** dos footprints na serigrafia (padrão: não plota) |
| `--silk-com-valores` | plota o **valor** dos footprints na serigrafia (padrão: não plota) |
| `--rev`, `--data`, `--autor`, `--projeto` | vão para `comment 2..4` e para o `.gbrjob` |

---

## 3. O que o pacote contém (e o que não pode ser gerado nesta máquina)

Gerado **e verificado** contra a v7 — 22 arquivos, nomes reais em
`fase3_pcb/v7_pacote_teste/`:

| Item | Arquivo | Estado |
|---|---|---|
| Cobre (6 ou 4 camadas, conforme o board) | `drone_vN_F_Cu.gtl`, `_In1_Cu.g2` … `_B_Cu.gbl` | ✅ gerado |
| Máscaras de solda | `drone_vN_F_Mask.gts`, `drone_vN_B_Mask.gbs` | ✅ gerado |
| Serigrafia | `drone_vN_F_SilkS.gto`, `drone_vN_B_SilkS.gbo` | ✅ gerado |
| Perfil / contorno | `drone_vN_Edge_Cuts.gm1` | ✅ gerado |
| Furos metalizados (PTH) | `drone_vN-PTH.drl` | ✅ gerado |
| Furos isolados (NPTH) | `drone_vN-NPTH.drl` | ✅ gerado |
| Gerber Job File | `drone_vN.gbrjob` | ✅ gerado (ver §3.1) |
| Mapa de furos | `drone_vN-PTH-drl_map.pdf`, `-NPTH-drl_map.pdf` | ✅ gerado |
| Mapa de furos (legível) | `drone_vN_mapa_furos.png` | ✅ gerado (matplotlib) |
| Pick-and-place | `drone_vN-Top.pos`, `drone_vN-Bottom.pos`, `drone_vN-pos.csv` | ✅ gerado |
| Aviso de footprints sem bit `placed` | `drone_vN-PNA-FLAGS.txt` | ✅ gerado |
| Relatório de DRC | `drone_vN-DRC.rpt` | ⚠️ **escrito como "não disponível"** (ver §3.3) |
| Índice do pacote | `README_GERBER.txt` | ✅ gerado |
| Board para inspeção manual | `_inspecao/board_para_drc.kicad_pcb` | ✅ gerado |

### 3.1 `.gbrjob` — funciona, mas por um caminho diferente do previsto

O plano previa que a chamada `SetCreateGerberJobFile(True)` (desligada em
`gera_pcb_v7.py:545`) bastasse. **Na v7 ela nunca funcionou, e nesta máquina ela
continua não funcionando em modo headless** — o pcbnew aceita a chamada e não
emite nenhum arquivo:

```console
$ /usr/bin/python3.9 -c "... po.SetCreateGerberJobFile(True); ... pc.PlotLayer()"
$ ls /tmp/ft2_job
-drone_v7.gtl          # <- nenhum .gbrjob
```

O `.gbrjob` desta etapa é escrito por `GERBER_JOBFILE_WRITER.WriteJSONJobFile()`,
que existe no 5.1.9 e **funciona**: `drone_v7.gbrjob`, 2937 bytes, JSON válido.
O script ainda chama `SetCreateGerberJobFile(True)` (é inofensivo) e depois
escreve o job file pelo writer.

### 3.2 `.drr` (mapa/relatório de furos em texto) — **não é possível nesta máquina**

`EXCELLON_WRITER.GenDrillReportFile()` **aborta o processo inteiro** no 5.1.9
headless. Não é uma exceção capturável em Python: o C++ lança e o interpretador
morre.

```console
$ /usr/bin/python3.9 -c "import pcbnew; b=pcbnew.LoadBoard('fase3_pcb/v7/v7_drone.kicad_pcb'); \
    dw=pcbnew.EXCELLON_WRITER(b); dw.SetOptions(False,False,pcbnew.wxPoint(0,0),False); \
    dw.CreateDrillandMapFilesSet('/tmp/ft5',True,False); dw.GenDrillReportFile('/tmp/ft5')"
terminate called after throwing an instance of 'IO_ERROR'
Aborted
$ echo $?
134
```

**Substituição entregue:** `EXCELLON_WRITER.CreateMapFilesSet()` — que **funciona** —
gera `drone_v7-PTH-drl_map.pdf` (21457 bytes) e `drone_v7-NPTH-drl_map.pdf` (3983 bytes),
mais um `drone_v7_mapa_furos.png` desenhado por matplotlib a partir das posições
e diâmetros dos 48 furos (2 de 4,500 mm; 4 NPTH de 3,200 mm; 2 de 2,000 mm;
12 de 1,900 mm; 8 de 1,000 mm; 4 de 0,600 mm; 16 de 0,400 mm).

### 3.3 DRC — **não é possível nesta máquina**, nem por API nem por CLI

```console
$ /usr/bin/python3.9 -c "import pcbnew; print([n for n in dir(pcbnew) if 'DRC' in n.upper()])"
['LAYER_DRC']
$ which kicad-cli
(não existe nesta máquina)
```

A varredura de `dir(pcbnew)` não acha `DRC`, `DRC_ENGINE` nem `RunDRC`. No KiCad
5.1 o DRC roda pela interface wxWidgets/GTK do pcbnew, e esta máquina é headless.
`drone_vN-DRC.rpt` é portanto **um relatório de indisponibilidade**, com o motivo e
o procedimento manual — não um DRC. O que ele **é**, e isso está escrito lá dentro:

- o board foi gravado em `_inspecao/board_para_drc.kicad_pcb`, **com** o `title_block`
  preenchido, para abrir no pcbnew e rodar o DRC à mão;
- todas as camadas de cobre foram plotadas sem erro;
- os dois arquivos de furo foram gerados;
- a lista de footprints sem o bit `placed` foi exportada.

**Limite honesto:** clearance, largura de trilha e máscara **não** foram
verificadas por máquina. Isso continua sendo gate do `verifica_fase3_v8.py` e do
DRC manual.

### 3.4 Esquema nativo, BOM e biblioteca de símbolos — fora do escopo desta etapa

O plano (`WP2_FABRICACAO.md` §5.2 B6, §5.3 C2/C4/C5) lista `vN_drone.sch`, BOM com
MPN/fabricante, `.pretty/` e biblioteca de símbolos. Nada disso é gerável a
partir de um `.kicad_pcb` pelo pcbnew 5.1, e nenhum existe hoje no repositório. O
`.gbrjob` e o P&P **não** substituem esses três.

---

## 4. O defeito de nome: o que este script resolve

O `.kicad_pcb` **não tem `title_block`**, e o pcbnew 5.1 nomeia o plot como
`<basename do board>-<plot>.<ext>`. Sem basename (board construído em memória),
saía `-drone_F_Cu.gtl` — hífen na frente e nome idêntico em v1…v7
(`WP2_FABRICACAO.md` §2.3–§2.6 e §3.3).

O script grava `title` e `comment 1..4` **em memória**, antes do plot, e normaliza
o nome final de cada arquivo. Prova real (`head -3` do arquivo gerado):

```console
$ head -3 fase3_pcb/v7_pacote_teste/drone_v7_F_Cu.gtl
G04 #@! TF.GenerationSoftware,KiCad,Pcbnew,5.1.9+dfsg1-1+deb11u1*
G04 #@! TF.CreationDate,2026-09-28T08:55:13-03:00*
G04 #@! TF.ProjectId,,58585858-5858-4585-9858-585858585858,rev?*
```

Comparação com a saída antiga, que continua no repositório:

| Antes | Depois |
|---|---|
| `-drone_F_Cu.gtl` | `drone_v7_F_Cu.gtl` |
| `-drone_In1_Cu.g2` | `drone_v7_In1_Cu.g2` |
| `-drone_Edge_Cuts.gm1` | `drone_v7_Edge_Cuts.gm1` |
| `-PTH.drl` | `drone_v7-PTH.drl` |

**O `.kicad_pcb` do repositório não recebe essa alteração** — o `title_block`
existe só no objeto `BOARD` em memória, para o plot e para o `.gbrjob`. Verificado:
`grep -c title_block fase3_pcb/v7/v7_drone.kicad_pcb` → `0` depois da execução.

Detalhe do 5.1 que quebrou a primeira versão do script e está comentado no código:
`pc.SetLayer(camada)` precisa vir **antes** de `pc.OpenPlotfile(...)`, senão a
extensão de protel sai errada (todas `.gtl`). E `GetPlotFileName()` só é confiável
nessa ordem.

---

## 5. Checklist da casa de fabricação

Estado medido em 2026-09-28. "v8" = `fase3_pcb/v8/v8_drone.kicad_pcb`.

### Fase B — o pacote mínimo

| # | Item | Arquivo | v7 (teste) | v8 (quando o pacote for gerado) |
|---|---|---|---|---|
| B1 | Cobre | `*_F_Cu.gtl`, `*_In1_Cu.g2` … `*_B_Cu.gbl` | ✅ 4 camadas | ✅ 6 camadas (F, In1–In4, B) |
| B2 | Máscaras | `*_F_Mask.gts`, `*_B_Mask.gbs` | ✅ | ✅ |
| B3 | Serigrafia | `*_F_SilkS.gto`, `*_B_SilkS.gbo` | ✅ | ✅ |
| B4 | Perfil | `*_Edge_Cuts.gm1` | ✅ 747 bytes | ✅ 687 bytes |
| B5 | Furos PTH + NPTH | `*-PTH.drl`, `*-NPTH.drl` | ✅ | ✅ |
| B8 | Gerber Job | `drone_v8.gbrjob` | ✅ 2937 bytes | ✅ 3365 bytes |
| B9 | Unidade/zero declarados | `README_GERBER.txt` + header do Gerber | ✅ | ✅ (`%MOMM*%`, absoluto) |
| B10 | Nome versionado | `drone_vN_*` | ✅ | ✅ |
| B6 | Esquema nativo `.sch` | `v8_drone.sch` | ❌ | ❌ **não gerável aqui** |
| B7 | Stackup dentro do `.kicad_pcb` | — | ❌ | ❌ **não gerável no 5.1.9**; ver §5.1 |

### Fase C — montagem / supply

| # | Item | Arquivo | Estado |
|---|---|---|---|
| C1 | Pick-and-place | `drone_v8-Top.pos`, `-Bottom.pos`, `-pos.csv` | ✅ 319 refs (Top 319 / Bottom 0) |
| C6 | Drill map | `drone_v8-PTH-drl_map.pdf`, `_mapa_furos.png` | ✅ |
| C2 | BOM com designator/MPN | `v8_drone_bom.csv` | ❌ não existe |
| C3 | Netlist de produção | `fase3_pcb/v7/v7_drone.net` | ✅ só a v7; o v8 ainda não tem |
| C4 | Biblioteca de footprints | `fase3_pcb/v7/footprints/` | ✅ só a v7 |
| C5 | Biblioteca de símbolos | — | ❌ não existe |
| C7 | Nota de orientação de solda | `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` | ✅ existe fora do pacote |

### Fase D — sempre mandar junto

| # | Item | Caminho | Estado |
|---|---|---|---|
| D1 | Ordem de solda e cuidados | `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` | ✅ |
| D2 | Plano de teste de bancada | `fase4_entrega/PLANO_TESTE_BANCADA.md` | ✅ |
| D3 | Matriz de riscos | `fase4_entrega/RISCOS.md` | ✅ |
| D4 | Segurança/regulatório (BR) | `fase4_entrega/SEGURANCA_E_REGULATORIO.md` | ✅ |
| D5 | Datasheets dos ICs críticos | `datasheets/` | ⚠️ **17** arquivos = 14 `.pdf` + 2 `.txt` + 1 `.pdf.INVALIDO_HTML` → **16 úteis**. O plano (`WP2_FABRICACAO.md` §5.4) diz 12; a contagem atual é outra. |

### Item ainda **não** resolvido: "PILÃO / impSID"

O briefing pedia este item no checklist. Ele **não aparece em nenhum arquivo do
repositório**, e não sei o que é:

```console
$ grep -rn -i "pilao\|impSID" . --include="*.md" --include="*.py" --include="*.net" --include="*.csv" --include="*.txt"
(sem nenhuma saída)
```

Não vou inventar o significado. Se "PILÃO" for um componente, um arquivo de
montagem ou um item de cotação da fab, é preciso **dizer qual** para ele entrar no
pacote. Se for apenas mais um nome para o pick-and-place, já está coberto pelo C1.

### 5.1 Stackup — a limitação mais dura do v8

O `v8_drone_stackup.txt` do outro worker registra que o token `(stackup ...)` **torna
o `.kicad_pcb` ilegível** no KiCad 5.1.9 (`OSError Unexpected "stackup" in input`).
Ou seja: as **6 camadas aparecem nos Gerbers** (o script detecta as camadas
habilitadas por `IsLayerEnabled()`), mas o stackup — espessuras, dielétricos,
impedância — **não cabe dentro do `.kicad_pcb` neste formato**. Ele precisa ser
comunicado à fab por fora: anexar `fase3_pcb/v8/v8_drone_stackup.txt` e
`fase3_pcb/STACKUP_PROPOSTO.md` ao pedido, ou usar um `.kicad_pro` de KiCad ≥ 6.

---

## 6. Estado do v8 no momento desta escrita (e por que o pacote final ainda não deve ser gerado)

`fase3_pcb/v8/verificacao_v8.txt`, medido pelo outro worker em 2026-09-28:

| Métrica | v8 | v7 | Leitura |
|---|---|---|---|
| footprints | 319 | 319 | preservado |
| pads | 1093 | 1093 | preservado |
| **tracks** | **0** | 605 | **roteamento não começou** |
| vias | 180 | — | só stitch, sem trilha |
| zones | 3 | 0 | rule areas presentes |
| camadas de cobre | 6 | 4 | v8 é 6 camadas |
| nets | 191 | 203 | v8 perdeu 12 nets |
| bbox | 162,10 × 145,02 mm | 220,10 × 160,10 mm | contorno mudou |
| gates em falha | A4, A8, contorno, nets | — | `VEREDITO: HA CRITERIOS EM FALHA` |

O script **foi testado contra o v8** (6 camadas, saída descartada em `/tmp/v8_smoke`,
24 arquivos) e funciona, inclusive com as 6 camadas. Mas gerar o pacote **final**
com `0` tracks produziria Gerbers de cobre interno vazios
(`drone_v8_In1_Cu.g2` … `In4_Cu.g5` com 13811 bytes cada — só a máscara de
aperturas, sem cobre). **O comando da §2 só deve ser rodado depois de o
roteamento do v8 terminar e os gates ficarem verdes.**

---

## 7. Resumo: o que ainda não pode ser gerado nesta máquina

1. **DRC** — sem API no Python do 5.1.9 e sem `kicad-cli`; só pela GUI.
2. **`.drr`** — `GenDrillReportFile()` aborta o processo (`IO_ERROR` / `Aborted`, exit 134).
3. **Esquema `.sch`** — não existe e não é reconstituível a partir do `.kicad_pcb`.
4. **BOM com MPN/fabricante** — precisa de escolha de peça humana.
5. **Stackup dentro do `.kicad_pcb`** — o token torna o arquivo ilegível no 5.1.9.
6. **PILÃO / impSID** — significado desconhecido, não existe no repositório.
