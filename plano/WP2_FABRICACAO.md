# WP2 — Auditoria dos artefatos de fabricação e naming dos Gerbers

**Story:** US-002 — *Auditoria dos artefatos de fabricacao e naming dos Gerbers*
**Projeto:** `/opt/jupyter/work/drone` (branch `main`)
**Data da auditoria:** 2026-09-28
**Escopo:** o que falta no repositório para que uma casa de fabricação produza a placa **sem adivinhar nada**, e qual é o defeito de naming dos Gerbers.

> **Convenção:** todo número citado veio de um comando executado nesta auditoria, com o comando e a saída colados na seção de evidência. Os valores da coluna **Esforço** são **estimativas de engenharia** marcadas como `[EST]` — não são medidos e não são promessa de prazo.

---

## 0. Ambiente e ferramental (verificado)

```console
$ cd /opt/jupyter/work/drone
$ pcbnew --version
00:22:33: Error: Unable to initialize GTK+, is DISPLAY set properly?
/usr/bin/pcbnew
/usr/bin/kicad
$ test -e /usr/bin/kicad-cli && echo "SIM" || echo "NAO"
NAO (test -e /usr/bin/kicad-cli -> falha)
$ python3 -c "import pcbnew; print(pcbnew.GetBuildVersion())"
ModuleNotFoundError: No module named 'pcbnew'
```

O `pcbnew` está instalado como **binário GUI** (`/usr/bin/pcbnew`) e sem `DISPLAY` não abre. O `kicad-cli` **não existe** nesta máquina — coerente com o `README.md:104`: *"`kicad-cli` não existe nesta máquina: os Gerbers são gerados por script `pcbnew`."*

**Consequência prática:** qualquer artefato que dependa de `kicad-cli` (`.gbrjob`, `.pos`/CPL, PDF de_IRQ, step de 3D) **não pode ser gerado pela CLI nesta máquina** e exige o `pcbnew` sob Xvfb ou uma estação KiCad de verdade. Isso entra no esforço estimado de cada linha da tabela.

Versão do formato do board e do gerador, lida do próprio arquivo:

```console
$ head -20 fase3_pcb/v7/v7_drone.kicad_pcb
(kicad_pcb (version 20171130) (host pcbnew 5.1.9+dfsg1-1+deb11u1)

  (general
    (thickness 1.6)
    (drawings 1)
    (tracks 605)
    (zones 0)
    (modules 319)
    (nets 203)
  )
```

`version 20171130` + `pcbnew 5.1.9` = formato **KiCad 5.1**. Isso importa para o item "schematic nativo": no KiCad 5.1 o esquema nativo é `.sch`, não `.kicad_sch` (que só existe a partir do KiCad 6).

---

## 1. Tabela-resumo dos artefatos

| # | Artefato | Existe? | Evidência (comando) | Quem usa | Esforço [EST] | Comando que gera |
|---|----------|---------|----------------------|----------|----------------|------------------|
| 1 | **Esquema nativo KiCad** (`.sch` no 5.1 / `.kicad_sch` no 6+) | ❌ **NÃO** | `find` não retorna nenhum `.sch`/`.kicad_sch` (§2.1) | Fab (conferência de circuito), assembler, **você** (manutenção) | 24 h [EST] | `eeschema` GUI → `File > Save`; ou `cd fase1_esquema && python3 gera_fase1_c.py` gera **PNG**, não `.sch` |
| 2 | **Netlist de produção** (`.net`) | ❌ **NÃO** | `find` não retorna `*netlist*` nem `*.net` (§2.1) | Fab (checagem de rede), assembler | 0,5 h [EST] | `pcbnew` → `File > Export > Netlist`; ou `eeschema` → `Tools > Generate Netlist File` |
| 3 | **Pick-and-place / CPL** (`.pos` ou `.csv` de posições) | ❌ **NÃO** | `find` não retorna `*.pos` (§2.1) | **Assembler** (se SMT) — é o arquivo que a máquina de montagem lê para colocar os 319 módulos | 0,5 h [EST] | `pcbnew` → `File > Fabrication Outputs > Footprint Position File` (unidades mm, lado Top/Bot separados) |
| 4 | **BOM de fabricação amarrado ao board** | ⚠️ **PARCIAL** | Existem 2 CSVs de 43 linhas, mas `conf` mostra 37 `[EST]` e não há PN (§2.5) | Compras, assembler, **você** | 4 h [EST] | `cd orcamento && python3 orcamento.py` gera `orcamento_detalhado.csv`; falta o *join* com o `.kicad_pcb` |
| 5 | **Bibliotecas de símbolos / footprints** (`.lib` / `.pretty/`) | ❌ **NÃO** | `find` não retorna `*.lib` (§2.1); 30 footprints distintos embutidos no `.kicad_pcb` | Fab, assembler, **você** (reabrir o projeto em outra máquina) | 2 h [EST] | `pcbnew` → `File > Archive Footprints`; `eeschema` → `Preferences > Manage Symbol Libraries > Export` |
| 6 | **Stackup da placa** | ❌ **NÃO** | Só `(thickness 1.6)` no cabeçalho; nenhum bloco de stackup/impedância (§0 e §2.2) | **Fab** — sem isso a casa assume Defaults e pode errar a impedância do barramento de potência | 1 h [EST] | `pcbnew` → `File > Board Setup > Physical Stackup` → salvar como `.kicad_pcb` |
| 7 | **Drill map / desenho dos furos** | ❌ **NÃO** | Só 2 `.drl`; nenhum `.drr`, nenhum mapa visual | Fab, **você** (saber onde furar a fixação) | 1 h [EST] | `pcbnew` → `File > Fabrication Outputs > Drill Drawing/Map` |
| 8 | **Unidade e zero declarados (`.gbrjob` + nota)** | ⚠️ **PARCIAL** | `%MOMM*%` e `FORMAT={... absolute / metric / decimal}` presentes, mas **sem** `.gbrjob` (§2.1, §2.4) | Fab, CAM | 0,5 h [EST] | `pcbnew` → `File > Fabrication Outputs > Gerber Job File` (KiCad 5.1 grava `.gbrjob` ao lado dos `.g*`) |
| 9 | **Contorno de placa em Edge.Cuts nativo** | ⚠️ **DEFEITO** | `gr_line` em Edge.Cuts = **0**; `gr_poly` = **1** (§2.3) | Fab (o `.gm1` exportado está bom, o `.kicad_pcb` não) | 0,5 h [EST] | Plotar 4 `gr_line` fechadas em Edge.Cuts no lugar do `gr_poly` |
| 10 | **Gerbers + drill exports** | ✅ **SIM** | 9 `.g*` + 2 `.drl` em `fase3_pcb/v7/` (§2.1) | Fab | — | `cd fase3_pcb && python3 gera_pcb_v7.py` |
| 11 | **Documentação de montagem e teste** | ✅ **SIM** | `MONTAGEM_ORDEM_DE_SOLDA.md`, `PLANO_TESTE_BANCADA.md`, `RISCOS.md`, `SEGURANCA_E_REGULATORIO.md` | Fab, assembler, **você** | — | já escritos à mão |

**Resumo da coluna "Existe?":** de 11 itens, **7 não existem**, **3 existem de forma parcial/defeituosa** e **1 está ok** (os exports). Somando o defeito de naming (§3), a placa **não é fabricável hoje** sem antes resolver os itens 1, 2, 3, 5, 6, 7, 8 e 9.

---

## 2. Evidências

### 2.1 Varredura de artefatos — o que existe de fato no repositório

```console
$ cd /opt/jupyter/work/drone
$ find . -path ./.git -prune -o -type f \( -iname "*.kicad_sch" -o -iname "*.sch" \
    -o -iname "*.lib" -o -iname "*.pos" -o -iname "*.gbrjob" -o -iname "*netlist*" \
    -o -iname "*.net" -o -iname "*.csv" \) -print | grep -v ipynb_checkpoints
./fase0_especificacao/lista_componentes_fase0.csv
./orcamento/orcamento_detalhado.csv
./orcamento/orcamento_por_bloco.csv
./fase2_simulacao/resultados_fase2_spice.csv
```

**Leitura:** em 4 classes de artefato (esquema nativo, biblioteca, pick-and-place, Gerber job / netlist) o `find` devolveu **zero arquivos**. Os únicos `.csv` do repositório são 2 de lista/orçamento e 1 de resultado de simulação — **nenhum deles é BOM de fabricação**.

Inventário completo do que há por versão, para contraste:

```console
$ ls fase3_pcb/v7/
-drone_B_Cu.gbl
-drone_B_Mask.gbs
-drone_B_SilkS.gbo
-drone_Edge_Cuts.gm1
-drone_F_Cu.gtl
-drone_F_Mask.gts
-drone_F_SilkS.gto
-drone_In1_Cu.g2
-drone_In2_Cu.g3
-NPTH.drl
-PTH.drl
v7_drone.kicad_pcb

$ ls -l fase3_pcb/v7/ | awk '{print $5, $9}'
132600 -drone_B_Cu.gbl
2926 -drone_B_Mask.gbs
2929 -drone_B_SilkS.gbo
747 -drone_Edge_Cuts.gm1
375084 -drone_F_Cu.gtl
262928 -drone_F_Mask.gts
879780 -drone_F_SilkS.gbo
162219 -drone_In1_Cu.g2
635727 -drone_In2_Cu.g3
386 -NPTH.drl
7357 -PTH.drl
1216870 v7_drone.kicad_pcb
```

**9 arquivos Gerber + 2 de furo + 1 board.** Faltam, no mínimo, `.pos`/CPL, `.gbrjob`, netlist e esquema — ou seja, **1/4 do pacote canônico**.

### 2.2 Confirmação do cabeçalho: sem `title_block` e sem `rule_area`

O `README.md:28` e o `plano/WP1_ROTEAMENTO.md` já apontavam que o board não tem `(title)` nem keepout. **Confirmado com comando próprio:**

```console
$ head -20 fase3_pcb/v7/v7_drone.kicad_pcb
$ grep -c "rule_area" fase3_pcb/v7/v7_drone.kicad_pcb
0
$ grep -c "title_block" fase3_pcb/v7/v7_drone.kicad_pcb
0
$ grep -nE "\(title |\(rev |\(comment " fase3_pcb/v7/v7_drone.kicad_pcb | head
(sem saída)
```

**Três resultados: 0 `rule_area`, 0 `title_block`, 0 linhas de título/revisão/comentário.** O bloco de identificação do desenho está literalmente vazio — é a causa raiz do §3.

O que **existe** no cabeçalho, para não exaggerar o diagnóstico:

| Parâmetro | Valor medido | Onde |
|---|---|---|
| Camadas | 4 condutoras: `F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu` | `(layers …)` do header |
| Espessura do board | `1.6` mm | `(general (thickness 1.6))` |
| Módulos (footprints) | `319` | `(general (modules 319))` |
| Nets declaradas | `203` | `(general (nets 203))` |
| Tracks | `605` | `(general (tracks 605))` |
| Zonas (copper pour) | `3` reais — GND em In1.Cu e B.Cu, VBAT_PROT em In2.Cu | `grep -n "(zone"` linhas 13869, 14447, 14890 |
| Segmentos de trilha | `253` | `grep -c "(segment"` |
| Vias | `360` | `grep -c "(via"` |
| Footprints distintos | `30` | `grep -oE '\(module [^ ]+' … \| sort -u \| wc -l` |
| Pads SMD / through-hole | `1339` / `48` | `grep -c "smd"` / `grep -c "thru_hole"` |

> **Achado colateral:** o `(general (zones 0))` do cabeçalho **contradiz** as 3 zonas reais do arquivo. É porque o cabeçalho é escrito à mão pelo `gera_pcb_v7.py`, não pelo `pcbnew`. Nenhuma fab lê esse contador, mas é a mesma raiz do defeito de naming: **o cabeçalho do arquivo não é gerado pela ferramenta, é escrito pelo script.** (§3, correção C3.)

### 2.3 Contorno da placa: o `.gm1` está bom, o `.kicad_pcb` está errado

```console
$ grep -c "gr_line.*Edge.Cuts" fase3_pcb/v7/v7_drone.kicad_pcb
0
$ grep -c "gr_poly.*Edge.Cuts" fase3_pcb/v7/v7_drone.kicad_pcb
1
$ grep -E "Edge.Cuts" fase3_pcb/v7/v7_drone.kicad_pcb | sed -E 's/^ +//' | cut -c1-40
(44 Edge.Cuts user)
(gr_poly (pts (xy 10 10) (xy 230 10) (xy
```

O contorno da placa está modelado como **um polígono** (`gr_poly`), e não como o **percurso fechado de linhas** que o KiCad 5.1 e qualquer CAM esperam em `Edge.Cuts`.

**O `.gm1` exportado está correto** — fecha os 4 cantos e volta ao início:

```console
$ cat fase3_pcb/v7/-drone_Edge_Cuts.gm1
G04 #@! TF.FileFunction,Profile,NP*
%FSLAX46Y46*%
G04 Gerber Fmt 4.6, Leading zero omitted, Abs format (unit mm)*
%MOMM*%
%LPD*%
G01*
%ADD10C,0.100000*%
D10*
X10000000Y-10000000D02*
X230000000Y-10000000D01*
X230000000Y-170000000D01*
X100000000Y-170000000D01*
X10000000Y-10000000D01*
M02*
```

Coordenadas lidas em formato 4.6 (coordenadas em 1/1.000.000 mm — na prática `X10000000` = 10,000000 mm): o retângulo vai de **10 → 230 mm** em X e de **10 → 170 mm** em Y. Ou seja, a placa mede **220 × 160 mm**.

> ⚠️ **220 × 160 mm é grande.** Acima de ~100×100 mm a maioria das casas entra em regime de painelização e o preço sobe por área, não por barra. Isso é uma decisão de projeto (placa única, ESC 4× trifásico + ESP32-S3 na mesma), mas o fabricante vai cobrar a área inteira mesmo que você use 15% dela. **Isso deve ser uma decisão consciente, não um número herdado.** [EST] Considerar dividir em 2 boards ou reduzir a área livre.

**Risco:** a fab que receber só o `.kicad_pcb` (em vez do `.gm1`) não vai conseguir derivar o contorno — o outline vem de `gr_line`, não de `gr_poly`. Como todos os outros artefatos do pacote vão ser `.kicad_pcb`/`.g*`, é preciso **corrigir na origem**, não só no export.

### 2.4 Furos: unidades, zero e o que falta

```console
$ head -20 fase3_pcb/v7/-PTH.drl
M48
; DRILL file {KiCad 5.1.9+dfsg1-1+deb11u1} date Fri Sep 11 22:33:22 2026
; FORMAT={-:-/ absolute / metric / decimal}
FMAT,2
METRIC
T1C30.000
T2C40.000
T3C50.000
T4C60.000
T5C100.000
T6C190.000
T7C200.000
T8C450.000
%
G90
G05
T1

$ cat fase3_pcb/v7/-NPTH.drl
M48
; DRILL file {KiCad 5.1.9+dfsg1-1+deb11u1} date Fri Sep 11 22:33:22 2026
; FORMAT={-:-/ absolute / metric / decimal}
FMAT,2
METRIC
T1C320.000
%
G90
G05
T1
X1400.0Y-1400.0
X1400.0Y-16600.0
X22600.0Y-1400.0
X22600.0Y-16600.0
T0
M30
```

O que está **declarado** (e isso é bom): `METRIC`, `absolute`, zero em **canto inferior-esquerdo** (coordenadas negativas em Y = convenção KiCad, absoluta). As 4 coordenadas NPTH em µm dão 1,4 / 16,6 / 22,6 mm nos dois eixos — **4 furos de fixação M3 (3,2 mm)**, 1,4 mm de inset a partir do retângulo da placa. Consistente.

**8 ferramentas PTH** (0,30 a 4,50 mm) e **1 ferramenta NPTH** (3,20 mm).

O que **não** está: nenhum `.drr` (drill report), nenhum drill map, e nenhuma nota escrita dizendo "unidade = mm, coordenadas absolutas, origem = canto inferior-esquerdo, board = 220×160 mm". Hoje essa informação existe **implícita no cabeçalho de cada arquivo** e **em nenhum lugar legível por um humano**. É item 7 e item 8 da tabela.

### 2.5 BOM: o que existe hoje e o que falta

```console
$ wc -l fase0_especificacao/lista_componentes_fase0.csv orcamento/orcamento_detalhado.csv
   44 fase0_especificacao/lista_componentes_fase0.csv
   44 orcamento/orcamento_detalhado.csv
   88 total
```

44 linhas = **1 cabeçalho + 43 itens**, nas duas. Bater os dois arquivos:

```console
$ head -1 fase0_especificacao/lista_componentes_fase0.csv
bloco;item;valor_especificacao;qtd;footprint_kicad_5.1;existe_no_kicad;observacao_de_compra
$ head -2 orcamento/orcamento_detalhado.csv
bloco;item;valor_especificacao;qtd;usd_unit;usd_total;brl_nacional;conf;fonte
ENTRADA;Conector de bateria;XT60 macho+femea, 60 A [N/D offline];1;0.5800;0.5800;9.52;[CALC];ML: XT60 3 pares R$28,78 -> R$9,59/par / (5,1312*3,2)
```

Colunas de origem de preço:

```console
$ awk -F';' 'NR>1{print $8}' orcamento/orcamento_detalhado.csv | sort | uniq -c
      3 [-]
      2 [CALC]
      1 [COT]
     37 [EST]
```

**37 dos 43 itens (86%) têm preço `[EST]`** — estimativa, não cotação. Só **1** é `[COT]` (cotação real) e **2** são `[CALC]` (derivados de lista de preço de terceiros). **3** estão `[-]`, sem valor nenhum.

Status do footprint no KiCad, declarado na lista de componentes:

```console
$ awk -F';' 'NR>1{print $6}' fase0_especificacao/lista_componentes_fase0.csv | sort | uniq -c
      2 N/A
      2 NAO
     35 SIM
      4 SIM (generico)
```

**2 itens com `existe_no_kicad = NAO`** e **4 como `SIM (generico)`** (footprint genérico, não do part number real). Cruzando com os **30 footprints distintos** realmente presentes no `.kicad_pcb`, há divergência entre a lista declarada e o board.

A lista ainda carrega marcações de falta de dado no próprio texto do item:

```console
$ head -3 fase0_especificacao/lista_componentes_fase0.csv
bloco;item;valor_especificacao;qtd;footprint_kicad_5.1;existe_no_kicad;observacao_de_compra
ENTRADA;Conector de bateria;XT60 macho+femea, 60 A [N/D offline];1;Connector_AMASS:AMASS_XT60-F_1x02_P7.20mm_Vertical;SIM;solda em furo - verificar corrente nominal no datasheet do fabricante
PROTECAO;TVS unidirecional;standoff >= 30 V, clamp ~38 V [N/D offline];1;Diode_SMD:D_SMB;SIM;comprar com Vbr acima de 25,2 V (nao conduzir em operacao)
```

O marcador **`[N/D offline]`** aparece dentro do `valor_especificacao` — é a lista se declarando incompleta. Confirmado em 2 linhas de amostra; a coluna existe para registrar exatamente esse tipo de lacuna.

---

## 3. Naming dos Gerbers — o defeito

### 3.1 O defeito

Os arquivos saem assim:

```console
$ ls fase3_pcb/v7/
-drone_F_Cu.gtl
-drone_B_Cu.gbl
-drone_In1_Cu.g2
-drone_In2_Cu.g3
-drone_F_Mask.gts
-drone_B_Mask.gbs
-drone_F_SilkS.gto
-drone_B_SilkS.gbo
-drone_Edge_Cuts.gm1
-NPTH.drl
-PTH.drl
```

**Dois defeitos independentes, ambos confirmados:**

**(a) Prefixo com hífen e board sem `(title)`.** Todo arquivo começa com **`-drone_`**. O hífen é o separador que o `pcbnew` insere entre o campo *vazio* do título e o nome do arquivo. E o nome está vazio porque o board não tem bloco de título:

```console
$ grep -c "title_block" fase3_pcb/v7/v7_drone.kicad_pcb
0
$ grep -nE "\(title |\(rev |\(comment " fase3_pcb/v7/v7_drone.kicad_pcb | head
(sem saída)
```

O próprio Gerber confirma a origem do hífen:

```console
$ head -6 fase3_pcb/v7/-drone_F_Cu.gtl
G04 #@! TF.GenerationSoftware,KiCad,Pcbnew,5.1.9+dfsg1-1+deb11u1*
G04 #@! TF.CreationDate,2026-09-11T22:33:21-03:00*
G04 #@! TF.ProjectId,,58585858-5858-4585-9858-585858585858,rev?*
G04 #@! TF.SameCoordinates,Original*
G04 #@! TF.FileFunction,Copper,L1,Top*
G04 #@! TF.FilePolarity,Positive*
```

`TF.ProjectId,` com o primeiro campo **vazio**, e `rev?` — o `pcbnew` leu o bloco de título, não achou nome nem revisão, e caiu no padrão. O `-drone_F_Cu` é literalmente o resultado de formatar `"-" + "" + "_" + "drone" + "_" + "F_Cu"`.

**(b) Mesmo nome nas 7 versões, conteúdo diferente.** Não é duplicação — são 7 desenhos distintos com **nomes idênticos**:

```console
$ md5sum fase3_pcb/v*/-drone_F_Cu.gtl
c074ed0404fc42ea8ce967a199b8f4b4  fase3_pcb/v1/-drone_F_Cu.gtl
070bb1284b0d689e68b4d961ff896f48  fase3_pcb/v2/-drone_F_Cu.gtl
9ab4f8f2996c94062caab2fe7503b19e  fase3_pcb/v3/-drone_F_Cu.gtl
67cb0ea4d43aabde4d10c822eaabda3d  fase3_pcb/v4/-drone_F_Cu.gtl
c8b9d0a17833b44005874ca570542548  fase3_pcb/v5/-drone_F_Cu.gtl
858b3e33ccf62d43d57dcc797f45eda0  fase3_pcb/v6/-drone_F_Cu.gtl
6d5f3681f541eaddb0443d5a562b264a  fase3_pcb/v7/-drone_F_Cu.gtl
```

**7 hashes distintos, 7 nomes idênticos.** O `.kicad_pcb` também difere a cada versão (11.110 → 17.349 linhas), confirmando que a evolução é real:

```console
$ wc -l fase3_pcb/v*/v*_drone.kicad_pcb
  11110 fase3_pcb/v1/v1_drone.kicad_pcb
  12137 fase3_pcb/v2/v2_drone.kicad_pcb
  15735 fase3_pcb/v3/v3_drone.kicad_pcb
  15831 fase3_pcb/v4/v4_drone.kicad_pcb
  15847 fase3_pcb/v5/v5_drone.kicad_pcb
  15871 fase3_pcb/v6/v6_drone.kicad_pcb
  17349 fase3_pcb/v7/v7_drone.kicad_pcb
 103880 total
```

E a data de criação dos Gerbers **também** é praticamente idêntica entre v1 e v7 (21:34:16 → 22:33:21 do mesmo dia), o que reforça que foram plotados em sequência — o que torna plausível de verdade que alguém **zipe as pastas e envie a errada**.

> Nota: existe `fase3_pcb/v8/`, mas está **vazia** (`ls -l` retorna 0 arquivos) — confirmado por `md5sum: … No such file or directory`. Provavelmente um worker em paralelo. Não é artefato de fabricação e não deve entrar no pacote.

### 3.2 O risco para a fab

1. **Ambiguidade total na recepção.** O pacote da fab é um zip. Se ele contiver `v1/`…`v7/`, o CAM recebe 7 conjuntos de arquivos **com o mesmo nome**. O sistema de upload de praticamente toda casa de fabricação indexa por nome de arquivo — o resultado é uma **sobreposição silenciosa**: ou a v7 sobrescreve as anteriores, ou a v1 é processada como se fosse a atual. Não há como o CAM perguntar qual é a certa, porque a informação **não está no pacote**. Você descobriria o problema quando a placa chegasse errada.

2. **O `-drone_` inicial é um bug de nome, não um detalhe cosmético.** Fabricantes usam o nome do arquivo para montar o nome do projeto no ERP e na etiqueta. Um prefixo `-` é lixo de campo vazio que polui a identificação em toda a cadeia.

3. **A revisão não viaja com a placa.** `rev?` no `TF.ProjectId` significa que a **fab não tem como registrar qual revisão recebeu**. Sem isso, um pedido de correção "reproduza a v7" é impossível de atender com rigor.

4. **A origem dos arquivos é ambígua.** O `(general (zones 0))` do cabeçalho contradiz as 3 zonas reais (§2.2). Uma casa que valida por parser pode acusar divergência e devolver o pacote.

5. **Contorno não recuperável do `.kicad_pcb`.** O `gr_poly` em Edge.Cuts (§2.3) significa que quem só tiver o board não deriva o outline.

### 3.3 Correção proposta (descrita, **não aplicada**)

> Esta seção **descreve** o que fazer. **Nada foi alterado no repositório nesta auditoria.**

**C1 — Pôr identificação no `title_block` do `vN_drone.kicad_pcb`.**
No `pcbnew` → `File > Page Settings`, preencher:

| Campo | Valor |
|---|---|
| Title | `drone` |
| Revision | `v7` |
| Date | `2026-09-28` |
| Company | *(a definir — ver C2)* |
| Comment 1 | `Placa de controle — ESC 4x trifasico + ESP32-S3` |
| Comment 2 | `4 camadas, 1.6 mm, 220 x 160 mm` |
| Comment 3 | `Gerado por codigo — fonte: fase3_pcb/gera_pcb_v7.py` |
| Comment 4 | `Roteamento em andamento — nao fabricate` |

Só o campo **Title** preenche é obrigatório para matar o `-drone_`; os outros existem para que a informação chegue à silk e ao relatório da fab.

**C2 — Tirar o prefixo de hífen do nome de saída.**
Com o `title` preenchido, o `pcbnew` passa a gerar `drone_F_Cu.gtl` (sem hífen). Se ainda assim for undesirable, configurar `Use Protel filename extensions = off` em `Preferences > Plot`, o que produz `drone-F_Cu.gbr` — sufixo `.gbr` padronizado pela Gerber X2, mais portável que a extensão `.gtl` do KiCad.

**C3 — Versionar o nome do arquivo exportado.**
O nome de saída precisa carregar a revisão fora do `pcbnew`, já que o `pcbnew` 5.1 nomeia por `title` e **não** por revisão. Duas formas:

- *Comum:* plotar para `fase3_pcb/v7/` mantendo a pasta como identificador de versão (é o que já existe, e funciona **desde que só uma versão vá no pacote**).
- *Robusta:* renomear na exportação para `drone-v7-F_Cu.gtl` … `drone-v7-PTH.drl`, com `v7` vindo do campo `rev`. É o que garante que, mesmo que alguém erre a pasta, **o nome carrega a versão**.

**C4 — Não mandar o histórico.**
O pacote de envio deve conter **uma única versão**. As pastas `v1`–`v7` são histórico de desenvolvimento e ficam **fora** do zip. Este é o ponto que realmente elimina o risco do §3.2.1.

**C5 — Corrigir o contorno na origem.**
Substituir o `gr_poly` de Edge.Cuts por **4 `gr_line` fechadas** entre (10,10), (230,10), (230,170), (10,170), e replotar o `.gm1`. Assim o outline sobrevive a quem só tenha o `.kicad_pcb`.

**C6 — Não escrever o cabeçalho à mão.**
Arazão do `(zones 0)` falso: `gera_pcb_v7.py` escreve o bloco `general` manualmente. Deixar o `pcbnew` gerar o cabeçalho ao salvar elimina a classe inteira de inconsistência entre header e conteúdo.

---

## 4. BOM: de lista de componentes a BOM de fabricação

### 4.1 O que já existe

| Arquivo | Linhas | Papel | Confirmado |
|---|---|---|---|
| `fase0_especificacao/lista_componentes_fase0.csv` | 43 itens | Lista de projeto: bloco, item, especificação, qtd, footprint, se existe no KiCad, observação de compra | `wc -l` → 44 (com header) |
| `orcamento/orcamento_detalhado.csv` | 43 itens | Lista de projeto **+ preço** em USD e BRL, com `conf` e `fonte` | `wc -l` → 44 (com header) |
| `orcamento/orcamento_por_bloco.csv` | — | Agregado por bloco funcional | `find` localizou |
| `orcamento/ORCAMENTO.md` | — | Relatório em cenários A (nacional) e B (importação) | `test -e` → OK |

**Isso é uma lista de componentes com preços estimados. Não é uma BOM de fabricação.** A diferença é inteiramente o que está na tabela abaixo.

### 4.2 O que falta, campo a campo

| Campo | Situação medida | Impacto na fab |
|---|---|---|
| **Part Number (MPN) do fabricante** | ❌ **Ausente em todas as 43 linhas.** Nenhuma coluna de MPN em nenhum dos dois CSVs (ver §2.5, cabeçalhos). A coluna `observacao_de_compra` traz texto livre ("comprar com Vbr acima de 25,2 V"), não código | **Bloqueante.** Sem MPN a fab **não consegue comprar**. Vão te mandar de volta pedindo "part number" ou, pior, compram um equivalente genérico que pode ter características diferentes — e a placa não funciona. |
| **Fabricante** | ❌ **Ausente.** O `fonte` no orçamento cita origem do *preço* (`ML: …`), não o fabricante do componente | O mesmo: um mesmo part number tem fornecedores compatíveis; sem o nome, a escolha é indefinida. |
| **Preço confiável** | ⚠️ **37 de 43 `[EST]`** (86%), 2 `[CALC]`, 1 `[COT]`, 3 `[-]` | Não é impeditivo para a **fab** (que cobra pela placa, não pelos componentes), mas é impeditivo para **você** decidir se o projeto é viável. Só 1 item tem cotação real. |
| **MOQ (pedido mínimo)** | ❌ **Ausente.** Sem dado de MOQ por linha | Se o MPN existir e a MOQ for 1000 unidades, a compra da peça avulsa sai muito mais cara do que a estimativa da linha. |
| **Lead time** | ❌ **Ausente** | Sem prazo, o orçamento não tem data. Peças de importação com 8–12 semanas de lead mudam a ordem de montagem inteira. |
| **Footprint conferido contra o board** | ⚠️ **Parcial.** 35 `SIM`, 4 `SIM (generico)`, **2 `NAO`**, 2 `N/A`. O board tem **30 footprints distintos** | **Crítico.** Um footprint errado = componente que não encaixa = placa montada inútil. Os 2 `NAO` precisam ser resolvidos antes de qualquer compra, e os 4 `(generico)` precisam ser trocados pelo footprint do MPN real. |
| **Quantidade por tipo** | ✅ `qtd` presente nas 43 linhas | OK |
| **Designator (ref des)** | ❌ **Ausente.** Nenhuma coluna liga o item da BOM ao `R12`/`C7`/`U3` do `.kicad_pcb` | **Bloqueante para o assembler.** Sem o mapeamento item→designator não há como montar, e não há como conferir. |
| **Supplier / URL** | ⚠️ **Parcial.** Só em `fonte` do orçamento, em prosa (`ML: XT60 3 pares R$28,78…`) | Facilita, não é obrigatório. |

### 4.3 O que falta como artefato

O `.kicad_pcb` tem **319 módulos** distribuídos em **30 footprints distintos**, e a lista tem **43 itens**. A BOM de fabricação precisa ser **extraída do próprio board** (designator → footprint → valor), não transcrita da lista de projeto, e então cruzada com a lista para trazer MPN/fabricante/preço.

O caminho é: `pcbnew` → `File > Fabrication Outputs > BOM`, gerando `v7_drone_bom.csv` (com `Ref` e `Value`), depois um `join` por footprint com `lista_componentes_fase0.csv` para adicionar as colunas comerciais. Estimativa: **4 h** [EST] para o script de join, mais o tempo de cotar os 6 itens que hoje não têm preço real (fora do escopo desta WP — é trabalho de compra).

> **Pragmaticamente:** os itens 1–3, 5–9 da tabela §1 somam ~**9,5 h** [EST] de trabalho de arquivo. Sem esses 9,5 h **não existe envio para fabricação**. Esta é a métrica que importa.

---

## 5. Checklist do pacote da fab

Ordem de verificação. **Não enviar enquanto qualquer item marcado com ❌ estiver aberto.** Cada linha tem o comando que confirma o estado real.

### 5.1 Fase A — sanidade do board (bloqueia tudo)

| # | Item | Como verificar | Hoje |
|---|------|----------------|------|
| A1 | Existe **exatamente uma** versão na pasta de envio, e ela é a boa | `ls fase3_pcb/v*/-drone_F_Cu.gtl` deve retornar **1 linha** | ❌ retorna 7 (§3.1) |
| A2 | O `.kicad_pcb` da pasta de envio é o mesmo que originou os Gerbers | `md5sum` do `.kicad_pcb` + comparar com `TF.CreationDate` de `head -3` do `.gtl` | ❌ sem versão para checar (§3.1b) |
| A3 | Contorno em Edge.Cuts é `gr_line` fechado, não `gr_poly` | `grep -c "gr_line.*Edge.Cuts" vN_drone.kicad_pcb` | ❌ retorna **0**; `gr_poly` retorna 1 (§2.3) |
| A4 | Roteamento completo — nenhuma net sem trilha | `grep -c "rule_area"` deve ser > 0 se houver keepout | ❌ 0; e o `README.md:28` diz *"Não fabrique esta placa ainda"* |
| A5 | Contador `(zones N)` do cabeçalho bate com as zonas reais | comparar `(general (zones N))` com `grep -c "^  (zone "` | ❌ diz `0`, existem **3** (§2.2) |

> **A4 é o gate principal.** Enquanto o `README.md:28` afirmar *"Não fabrique esta placa ainda"*, nenhum outro item importa. Esta WP auditou **artefatos**; ela **não** aprova o roteamento (isso é `plano/WP1_ROTEAMENTO.md`).

### 5.2 Fase B — o pacote mínimo (o que a fab exige para cotar/produzir)

| # | Item | Arquivo esperado | Hoje |
|---|------|-------------------|------|
| B1 | Gerbers de cobre — 4 camadas | `-drone_F_Cu.gtl`, `-drone_B_Cu.gbl`, `-drone_In1_Cu.g2`, `-drone_In2_Cu.g3` | ✅ existe (§2.1) |
| B2 |máscaras de solda | `-drone_F_Mask.gts`, `-drone_B_Mask.gbs` | ✅ existe |
| B3 | silk | `-drone_F_SilkS.gto`, `-drone_B_SilkS.gbo` | ✅ existe |
| B4 | perfil da placa | `-drone_Edge_Cuts.gm1` | ✅ existe (fechado, §2.3) |
| B5 | furos PTH + NPTH | `-PTH.drl`, `-NPTH.drl` | ✅ existe, METRIC/absoluto (§2.4) |
| B6 | **Esquema nativo** | `vN_drone.sch` (KiCad 5.1) | ❌ §2.1 |
| B7 | **Stackup documentado** | dentro do `.kicad_pcb` (Board Setup) | ❌ §2.1 |
| B8 | **Gerber Job** | `vN_drone-job.gbrjob` | ❌ §2.1 |
| B9 | **Unidade/zero declarados por escrito** | nota no email ou `README_fab.txt` na pasta | ❌ implícito só no header |
| B10 | **Nome versionado** | `drone-v7-*` | ❌ hoje é `-drone_*` sem versão (§3.1) |

### 5.3 Fase C — se houver montagem / supply (assembler)

| # | Item | Arquivo esperado | Hoje |
|---|------|-------------------|------|
| C1 | **CPL / pick-and-place** | `vN_drone-top.pos`, `vN_drone-bottom.pos` | ❌ §2.1 |
| C2 | **BOM com designator** | `vN_drone_bom.csv` com colunas `Ref,Value,Footprint,MPN,Manufacturer,Qty` | ❌ §2.1 / §4.2 |
| C3 | **Netlist de produção** | `vN_drone.net` | ❌ §2.1 |
| C4 | **Biblioteca de footprints** | `vN_drone.pretty/` | ❌ §2.1 |
| C5 | **Biblioteca de símbolos** | `vN_drone-libs/` | ❌ §2.1 |
| C6 | **Drill map** | `vN_drone-drl_map.*` | ❌ §2.1 |
| C7 | Nota de orientação/inspeção (se alguma borda é "não tocar") | texto | ⚠️ `MONTAGEM_ORDEM_DE_SOLDA.md` existe, mas não está no pacote |

### 5.4 Fase D — o que sempre mandar junto

| # | Item | Existe |
|---|------|--------|
| D1 | Ordem de solda e cuidados | `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` ✅ |
| D2 | Plano de teste de bancada com critério de aceite | `fase4_entrega/PLANO_TESTE_BANCADA.md` ✅ |
| D3 | Matriz de riscos | `fase4_entrega/RISCOS.md` ✅ |
| D4 | Segurança/regulatório (Brasil) | `fase4_entrega/SEGURANCA_E_REGULATORIO.md` ✅ |
| D5 | Datasheets dos ICs críticos | `datasheets/` — 9 arquivos (ESP32-S3, ICM-42688-P, INA240, IR2104, MCP3208) ✅ |

**D1–D5 já existem e são um diferencial** — poucas casas recebem isso. Copiar para a pasta de envio (ou anexar) é o que transforma "pedido de peça" em "pedido de peça com critério de aceite".

---

## 6. Verificação dos caminhos citados

Todo caminho citado neste documento foi conferido:

```console
$ cd /opt/jupyter/work/drone
$ for p in plano/WP1_ROTEAMENTO.md plano/WP3_PREMISSAS_DATASHEETS.md plano/WP4_FIRMWARE.md \
    fase3_pcb/v7/v7_drone.kicad_pcb fase3_pcb/v7/-drone_F_Cu.gtl fase3_pcb/v7/-drone_Edge_Cuts.gm1 \
    fase3_pcb/v7/-PTH.drl fase3_pcb/v7/-NPTH.drl fase3_pcb/v8 fase3_pcb/gera_pcb_v7.py \
    fase3_pcb/rota_v7.py fase3_pcb/verifica_fase3_v6.py fase0_especificacao/lista_componentes_fase0.csv \
    orcamento/orcamento_detalhado.csv orcamento/orcamento_por_bloco.csv orcamento/ORCAMENTO.md \
    orcamento/orcamento.py fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md fase4_entrega/PLANO_TESTE_BANCADA.md \
    fase4_entrega/RISCOS.md fase4_entrega/SEGURANCA_E_REGULATORIO.md fase1_esquema/gera_fase1_c.py \
    fase1_esquema/esq7_mcu.png README.md; do if test -e "$p"; then echo "OK   $p"; else echo "FALTA $p"; fi; done
OK   plano/WP1_ROTEAMENTO.md
OK   plano/WP3_PREMISSAS_DATASHEETS.md
OK   plano/WP4_FIRMWARE.md
OK   fase3_pcb/v7/v7_drone.kicad_pcb
OK   fase3_pcb/v7/-drone_F_Cu.gtl
OK   fase3_pcb/v7/-drone_Edge_Cuts.gm1
OK   fase3_pcb/v7/-PTH.drl
OK   fase3_pcb/v7/-NPTH.drl
OK   fase3_pcb/v8
OK   fase3_pcb/gera_pcb_v7.py
OK   fase3_pcb/rota_v7.py
OK   fase3_pcb/verifica_fase3_v6.py
OK   fase0_especificacao/lista_componentes_fase0.csv
OK   orcamento/orcamento_detalhado.csv
OK   orcamento/orcamento_por_bloco.csv
OK   orcamento/ORCAMENTO.md
OK   orcamento/orcamento.py
OK   fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md
OK   fase4_entrega/PLANO_TESTE_BANCADA.md
OK   fase4_entrega/RISCOS.md
OK   fase4_entrega/SEGURANCA_E_REGULATORIO.md
OK   fase1_esquema/gera_fase1_c.py
OK   fase1_esquema/esq7_mcu.png
OK   README.md
```

**25/25 caminhos existem.** Os arquivos `v1_drone.sch`, `vN_drone-job.gbrjob`, `vN_drone-top.pos` e `vN_drone_bom.csv` citados como **faltantes** (§2.1, §5) são justamente os que o `find` do §2.1 provou **não** existirem — eles aparecem neste documento como alvo, nunca como caminho navigável.

---

## 7. Conclusão

1. **A placa não é fabricável hoje.** Faltam 7 artefatos (§1) e 3 estão em estado defeituoso. O caminho crítico são os **~9,5 h** [EST] de geração de arquivos — mas o **gate real é o roteamento** (`README.md:28`), que é escopo de `plano/WP1_ROTEAMENTO.md`.
2. **O defeito de naming é confirmado e tem duas causas independentes:** `title_block` vazio no board (§3.1a) → gera o `-drone_` com hífen e o `rev?`; e export sem versão no nome (§3.1b) → 7 arquivos com nome idêntico e conteúdo diferente. **A correção que mata o risco é enviar só uma versão** (§3.3 C4) — renomear sozinho não basta se as 7 pastas forem para o mesmo zip.
3. **A BOM atual é uma lista de projeto com preços estimados, não uma BOM de fabricação.** Faltam MPN e fabricante em **43/43** linhas, e designator em **43/43** — sem MPN a fab não compra, sem designator o assembler não monta. 37/43 preços são `[EST]`.
4. **A documentação de Fase 4 (montagem, teste, riscos, regulatório) e os 9 datasheets já existem** e são o ativo mais subutilizado do projeto: estão prontos para ir no pacote e não vão junto hoje.

**Estimativa total para fechar o pacote de fabricacao: ~9,5 h** [EST] de trabalho de arquivo (itens 1, 2, 3, 5, 6, 7, 8, 9 da §1), **fora** cotar MPNs e **fora** resolver o roteamento. Nenhum número de esforço deste documento foi medido — todos marcados `[EST]` são estimativa de engenharia.
