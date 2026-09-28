# Gates revisados para esta máquina

Documento novo, escrito em 2026-09-28 contra a árvore do commit `0c4fb57`.
**Nenhum gate foi apagado.** `plano/DO_PROJETO.md`, `PLANO_FINAL.md` e
`fase3_pcb/v8/verificacao_v8.txt` não foram editados. Para cada gate está aqui:

1. o critério original, com o comando que o mede;
2. **se é satisfazível nesta máquina** (KiCad 5.1.9 headless, sem `kicad-cli`) — sim
   ou não, com a saída real;
3. o **critério equivalente e verificável aqui**, quando o original não é;
4. o que fica **para outra ferramenta** e o que isso significa para quem decide.

O que decide se o plano muda continua sendo o Jailton. Este arquivo registra o que a
máquina consegue e o que ela não consegue provar.

## O ambiente, medido

```
$ /usr/bin/python3.9 -c "import pcbnew; print(pcbnew.GetBuildVersion())"
5.1.9+dfsg1-1+deb11u1
$ which kicad-cli || echo NAO_EXISTE
NAO_EXISTE
$ python3 -V
Python 3.12.13          # sem pcbnew: ModuleNotFoundError: No module named 'pcbnew'
```

Três coisas que esta máquina **não tem** e que mudam o critério de vários gates:
`kicad-cli` (exportação e DRC oficial), DRC de KiCad (não existe por script no 5.1.9
headless) e o formato de arquivo do KiCad ≥ 6 (stackup, rule areas nomeadas).

---

# Bloco A — `plano/DO_PROJETO.md` §2 (A1..A20)

| # | Critério original | Satisfazível aqui? | Evidência real | Critério equivalente aqui / o que fica de fora |
|---|---|---|---|---|
| **A1** | `ls fase3_pcb/v*/-drone_F_Cu.gtl \| wc -l` = 1 | **SIM** | **7** | ✅ verificável. É decisão de limpeza de pasta, não de ferramenta. O nome com o prefixo `-drone_` herdado da v7 é a causa; a correção é o pacote de `fase3_pcb/gera_pacote_fab.py` com nome versionado. |
| **A2** | `fase3_pcb/v8/verificacao_v8.txt` com 0 nets sem trilha | **SIM** | `nets NAO roteadas : 189` | ✅ verificável. É o que o worker de roteamento está fechando. Sem mudança de critério. |
| **A3** | `fase3_pcb/v8/clearance_v8.txt` com `pares abaixo de 0,15 mm: 0` | **PARCIAL** | o arquivo **não existe** (`test -e` → 0). O dado está dentro de `verificacao_v8.txt`: `pares trilha x pad (net diferente) proximos: 0` | ⚠️ **o número já é medido, o nome do arquivo não é.** Equivalente verificável aqui: `grep -c "pares trilha x pad (net diferente) proximos: 0" fase3_pcb/v8/verificacao_v8.txt`. O que fica fora: **DRC real** (clearance pad×pad, via×via, trilhas cruzadas entre camadas) — só com `kicad-cli` ou GUI. |
| **A4** | todo pad de GND/VBAT_PROT tem via a < 1,6 mm | **SIM como número, NÃO como alvo** | 68 no commit `0c4fb57`; **37** com o gerador revisado (medido em cópia, `fase3_pcb/v8/STITCH_v8.md` §3) | ⚠️ o critério **não é satisfazível** nesta geometria: 85 dos 249 pads não têm nenhum espaço livre a ≤ 1,6 mm do centro (ensaio sem concorrência, §4 do STITCH). Equivalente honesto: **via ≤ 1,6 mm do centro OU ≤ 0,5 mm da borda do cobre**, mais malha de stitch com passo ≤ 5 mm verificada pelo DRC do fabricante. O gate fica **adiado com número**, não removido. |
| **A5** | `test -e fase3_pcb/v8/verificacao_v8.txt` | **SIM** | **1** | ✅ verificável. Já passa. |
| **A6** | existe `*.kicad_sch` ou `*.sch` | **PARCIAL** | `find . -name '*.kicad_sch' -o -name '*.sch' \| wc -l` → **0** | ⚠️ esta máquina **não tem Eeschema** para gerar esquema nativo KiCad: só há PNG em `fase1_esquema/`. O que é verificável aqui: a **netlist de produção** já existe (`fase3_pcb/gera_netlist_v7.py`, `fase1_esquema/`), e o esquema nativo é para o usuário abrir no KiCad ≥ 6. **Fica de fora: a placa não vai com esquema nativo; a casa precisa abrir o `.kicad_sch` no KiCad do Desktop antes de fabricar.** |
| **A7** | existe `*.net` | **SIM** | `find . -name '*.net' \| wc -l` → **1** | ✅ verificável. Já passa. |
| **A8** | `find . -name '*.pos' \| wc -l` > 0 | **SIM** | **2** | ✅ verificável. Já passa. **Cuidado:** o A8 de `PLANO_FINAL.md` §5 é outro gate (keepouts) — ver abaixo. Os dois não se misturam. |
| **A9** | `grep -c EST orcamento/orcamento_detalhado.csv` = 0 | **SIM** | **37** | ✅ verificável. Não é ferramenta: é compras e cotação — exige os 37 `[EST]` virarem preço real de fornecedor. |
| **A10** | `find . -name '*.lib' \| wc -l` > 0 | **PARCIAL** | **0** | ⚠️ esta máquina **não tem `kicad-cli export`**, que é quem gera biblioteca a partir do board. Equivalente verificável: os footprints estão embutidos no `.kicad_pcb` (319 módulos, 30 libs distintas embutidas) e a fonte está em `/usr/share/kicad/modules/`. **Fica fora: a biblioteca exportada precisa de KiCad ≥ 6 no Desktop** (`kicad-cli fp export`). Sem ela a casa re-importa do `.kicad_pcb`. |
| **A11** | `grep -c stackup` no `.kicad_pcb` > 0 | **NÃO** | **0** | ❌ **insatisfazível no KiCad 5.1.9.** O token `(stackup ...)` foi introduzido no KiCad 6; injetá-lo no arquivo deixa o board **ilegível** — medido 3 vezes: `pcbnew.LoadBoard()` → `OSError Unexpected "stackup" in input/source`. **Critério equivalente verificável aqui:** (a) `fase3_pcb/v8/v8_drone_stackup.txt` existe e tem o bloco de 6 camadas; (b) a soma das espessuras confere: `grep -c copper_thickness fase3_pcb/v8/v8_drone_stackup.txt` → **1**; (c) os 6 layers aparecem no board (`b.GetCopperLayerCount()` → **6**) **e** nos 6 Gerbers de cobre: `ls fase3_pcb/v8/*_In?_Cu.g* fase3_pcb/v8/*_F_Cu.gtl fase3_pcb/v8/*_B_Cu.gbl \| wc -l` → **6**. **O que fica fora:** a casa cola o stackup no pedido e o DRC de impedância é feito pela casa, com o Gerber/ODB++. |
| **A12** | `find . -name '*.drr' \| wc -l` > 0 | **NÃO** | **0** | ❌ o `.drr` (drill report do Pcbnew) é gerado pela GUI. Equivalente: os 2 arquivos de furo existem — `fase3_pcb/v8/v8_drone-PTH.drl` e `fase3_pcb/v8/v8_drone-NPTH.drl` — e o `.gbrjob` declara as ferramentas. **Fica fora:** o desenho dos furos legível para o operador vem da casa. |
| **A13** | `find . -name '*.gbrjob' \| wc -l` > 0 | **SIM** | **1** | ✅ verificável. Já passa. |
| **A14** | contorno em Edge.Cuts é `gr_line` fechado, não `gr_poly` | **SIM** | `grep -c 'gr_line.*Edge.Cuts' fase3_pcb/v8/v8_drone.kicad_pcb` → **0** (o contorno é `gr_poly`) | ✅ verificável **e hoje falha por escolha do gerador**, não por limite de ferramenta. O Pcbnew 5.1.9 grava o retângulo como `gr_poly` e o Pcbnew 6 lê os dois. Equivalente mais forte e que o `gr_line` não dá: `pcbnew.LoadBoard(...).GetBoardEdgesBoundingBox()` → **162,10 × 145,02 mm**, e o polígono tem 4 cantos. **Fica fora:** a casa confirma se o CAM dela aceita `gr_poly` no contorno — a maioria aceita. |
| **A15** | `grep -c title_block` > 0 | **SIM** | **0** | ✅ verificável. Falha por omissão do gerador: o `title_block` é um bloco de texto no arquivo e o Pcbnew 5.1.9 o grava. Corrigível aqui. |
| **A16** | `(zones N)` do cabeçalho bate com as zonas reais | **SIM** | cabeçalho: `(zones 0)`; reais: `grep -c '^  (zone '` → **3** | ✅ verificável. É contador do próprio gerador. |
| **A17** | Gerbers da pasta de envio nasceram **deste** `.kicad_pcb` | **SIM** | `head -3 fase3_pcb/v8/v8_drone-drone_F_Cu.gtl` traz `TF.CreationDate`; comparação com `md5sum` | ✅ verificável. Correção: o nome do Gerber da v8 é `v8_drone-drone_F_Cu.gtl` (**dois** `-drone`), herdado do gerador; é o que faz o A1 dar 7. |
| **A18** | 9 Gerbers + 2 `.drl` na pasta de envio | **SIM** | `ls fase3_pcb/v8/*.g* fase3_pcb/v8/*.drl \| wc -l` → **13** | ✅ verificável. Os 6 de cobre, 2 de máscara, 2 de silk e 1 de contorno + 2 `.drl`. Passa. |
| **A19** | 4 documentos de montagem/teste existem | **SIM** | **4** | ✅ verificável. Já passa. |
| **A20** | `grep -c "Não fabrique esta placa ainda" README.md` = 0 | **SIM** | **1** | ✅ verificável. É decisão do Jailton, não da máquina. |

---

# Bloco G1 — `PLANO_FINAL.md` §5 (A1..A8, layout fechado)

| # | Critério original | Satisfazível aqui? | Evidência real | Critério equivalente aqui / o que fica de fora |
|---|---|---|---|---|
| **G1-A1** | nets com pad e zero trilha = 0 | **SIM** | `nets NAO roteadas : 189` | ✅ verificável. Caminho crítico do projeto. Sem mudança. |
| **G1-A2** | pares trilha×pad de nets diferentes com folga crítica = 0 | **SIM** | `pares trilha x pad (net diferente) proximos: 0` | ✅ verificável, com a ressalva do A3 do Bloco A: é só **trilha×pad na mesma camada**. |
| **G1-A3** | pads de nets diferentes com bbox sobreposto = 0 | **SIM** | medível com `SHAPE_POLY_SET.Collide` no Pcbnew 5.1.9 | ✅ verificável. **Não** é o mesmo que DRC: bbox sobreposto não é clearance real. O DRC de pad×pad entre camadas fica fora. |
| **G1-A4** | pads de GND/VBAT_PROT sem via a < 1,6 mm = 0 | **NÃO** | 68 → **37** com o gerador revisado; teto geométrico sem concorrência: 85 pads sem espaço | ❌ **o alvo 0 é insatisfazível nesta geometria.** Ver `fase3_pcb/v8/STITCH_v8.md` §4 e §5. Equivalente proposto: via ≤ 1,6 mm do centro **ou** ≤ 0,5 mm da borda do cobre. **Fica fora:** malha de stitch com passo ≤ 5 mm, verificada pelo DRC do fabricante. |
| **G1-A5** | trilhas em In1.Cu / In2.Cu = 0 (mantidas como plano) | **SIM** | `b.GetTracks()` sobre `In1_Cu` / `In2_Cu` → contagem | ✅ verificável. |
| **G1-A6** | largura da trilha de fase do motor ≥ 6,29 mm | **SIM** | `mede_v7_wp1.py` em `/usr/bin/python3.9` | ✅ verificável. **Atenção ao interpretador:** só o `/usr/bin/python3.9` tem `pcbnew`. |
| **G1-A7** | nome dos Gerbers **não** começa com `-drone_` | **SIM** | hoje começam: `v8_drone-drone_F_Cu.gtl` | ✅ verificável. É o mesmo defeito do A1 e do A17. |
| **G1-A8** | ≥ 1 `rule_area` no arquivo | **NÃO** | `grep -c rule_area fase3_pcb/v8/v8_drone.kicad_pcb` → **0**; `grep -c '(keepout'` → **3** | ❌ **insatisfazível no KiCad 5.1.9**, testado 3 vezes: injetar `(rule_area ...)`, `(name ...)` ou `(title ...)` em `zone` deixa o board **ilegível** (`pcbnew.LoadBoard()` → `OSError`). As 3 keepouts existem **de verdade**: o Pcbnew 5.1 grava uma rule area como `zone` com `(keepout ...)`, e `SetIsKeepout(True) + SetDoNotAllowTracks/Vias/CopperPour` é o que dá. **Critério equivalente verificável aqui:** `grep -c '(keepout' fase3_pcb/v8/v8_drone.kicad_pcb` → **3** **e** `z.GetDoNotAllowTracks()/GetDoNotAllowVias()/GetDoNotAllowCopperPour()` em cada uma das 3, mais a camada: as 6. **O que fica fora:** dar **nome** às rule areas, que o formato 5.1 não tem — o nome vive no sidecar `fase3_pcb/v8/NOTA_E3.md` §4 até o projeto ser aberto no KiCad ≥ 6. |

---

# Bloco G2 — `PLANO_FINAL.md` §5 (pacote de fabricação)

| Critério | Satisfazível aqui? | Evidência | Equivalente / o que fica fora |
|---|---|---|---|
| esquema nativo presente | **NÃO** | `find . -name '*.kicad_sch' -o -name '*.sch' \| wc -l` → 0 | fora: Eeschema. O `.kicad_sch` precisa ser aberto e salvo no Desktop. |
| netlist de produção | **SIM** | `find . -name '*.net' \| wc -l` → 1 | ✅ |
| CPL (pick-and-place) | **SIM** | `find . -name '*.pos' \| wc -l` → 2 | ✅ |
| bibliotecas exportadas | **NÃO** | `find . -name '*.lib' \| wc -l` → 0 | fora: `kicad-cli fp export` (KiCad ≥ 6). Os footprints embutidos no `.kicad_pcb` servem de insumo. |
| drill report (`.drr`) | **NÃO** | `find . -name '*.drr' \| wc -l` → 0 | fora: GUI. Equivalente: os 2 `.drl` + o `.gbrjob`. |
| `.gbrjob` com unidade e zero | **SIM** | `find . -name '*.gbrjob' \| wc -l` → 1 | ✅ |
| BOM com designator, MPN e fabricante em 43/43 | **PARCIAL** | `grep -c EST orcamento/orcamento_detalhado.csv` → **37** | ⚠️ 37 itens com `[EST]`. Não é ferramenta: é compras. Bloqueia a cotação. |
| stackup / dielectric / copper_thickness / impedance no `.kicad_pcb` | **NÃO** | 0 no board; sidecar `fase3_pcb/v8/v8_drone_stackup.txt` com 1 `copper_thickness` | ❌ token inexistente no formato 5.1 (ver A11). Fora: DRC de impedância da casa. |
| zip de envio com **uma** versão só | **SIM** | `ls fase3_pcb/v*/-drone_F_Cu.gtl \| wc -l` → 7 | ✅ verificável. |
| nenhum arquivo inválido de datasheet no pacote | **SIM** | `fase3_pcb/gera_pacote_fab.py` valida antes de empacotar | ✅ |

---

# Bloco G3 e G4 — bancada e voo

`PLANO_FINAL.md` §5 define G3 (bancada) e G4 (voo) como **medição**, não como
comando. Eles **não são verificáveis nesta máquina** e nenhum substituto computacional
existe para eles: um `PLANO_TESTE_BANCADA.md` executado não vira prova.

- **G3** — 15 passos de `fase4_entrega/PLANO_TESTE_BANCADA.md`, cada um com critério
  de aceite medido em bancada. Hoje `fase4_entrega/logs/` **não existe** (`ls` →
  `No such file or directory`). Equivalente verificável hoje: **nenhum** — só
  `test -e` do arquivo de log de cada passo, que prova que o passo foi executado, não
  que passou. Os `[PREMISSA]` de 30 A e 15 A **não** viram medido por comando.
- **G4** — voo com PID, comutação, ESP-NOW, proteção e failsafe medidos. Idem: só
  bancada/voo. Fora de qualquer máquina sem sensor.

Nada de G3/G4 foi contado como aprovado.

---

# Resumo — o que essa máquina decide e o que ela não decide

**Verificável aqui, sem ressalva:** A1, A2, A5, A7, A9, A13, A14, A15, A16, A17, A18,
A19, A20, G1-A1, G1-A2, G1-A3, G1-A5, G1-A6, G1-A7, netlist, CPL, `.gbrjob`, zip
único, integridade do pacote.

**Verificável aqui, com critério reescrito e número:** A3 (existe o número, não o
nome do arquivo), A4/G1-A4 (o alvo 0 é insatisfazível; o número medido é 37), A8/G1-A8
(`(keepout` em vez de `rule_area`), A11 (sidecar + 6 layers no board + 6 Gerbers),
A12 (`.drl` + `.gbrjob` em vez de `.drr`), A14 (bbox + 4 cantos em vez de `gr_line`),
A6/A10 (artefato gerado no Desktop).

**Não verificável aqui, em nenhuma hipótese:** DRC real (clearance entre camadas,
pad×pad, via×via), impedância do barramento, malha de stitch com passo, drill report
legível, biblioteca de footprint exportada, esquema nativo salvo, e tudo de G3/G4.

**O que isso significa para quem decide:** a placa **pode** sair daqui com Gerbers,
drills, netlist, CPL, BOM, stackup escrito e três keepouts reais — e isso já é o
pacote que a casa lê. O que ela **não** pode sair daqui com é o **atestado**: os DRC
que provam que nada está curtado, que a impedância do barramento de potência está
correta e que o retorno de GND é contínuo são do KiCad ≥ 6 em desktop ou do DRC do
fabricante. Nenhum desses três é substituível por `grep` nesta máquina, e as três
tentativas de forçá-los aqui (injetar `stackup`, `name` e `rule_area` no board) já
foram medidas e **deixam o arquivo ilegível**. O caminho honesto é fechar o que dá
para fechar aqui — o layout, o pacote, a stitch — e dizer à casa, no pedido, que o
atestado de DRC e de impedância é dela.
