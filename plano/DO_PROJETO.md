# Definition of Done — Projeto Drone (4×ESC trifásico + ESP32-S3)

> **Data da conferência: 2026-09-28.** Todos os estados desta tabela foram medidos nesta
> máquina, com os comandos da coluna 3, **nesta sessão de 2026-09-28, contra a árvore no
> momento da leitura** (referência: `git rev-parse --short HEAD`, que avança a cada commit —
> por isso nenhum commit é citado aqui). Onde o estado não pôde ser conferido por máquina,
> está escrito **não conferido** — e o motivo está na própria linha.
> Effort marcado `[EST]`. Nenhum prazo é prometido aqui.

## 1. Como usar este documento

Existem três portões diferentes, e confundi-los é o que faz um projeto virar indefinitely. **"Pronto para fabricar"** significa que existe um conjunto de arquivos que um fabricante aceita e que não volta com "faltou o arquivo X" — é uma condição de *arquivo*, verificável no seu próprio PC, semelete. **"Pronto para bancada"** significa que a placa chegou, tem energia e todos os trilhos medidos, com registro de log — é uma condição de *medição*, e nada de um portão pode substituir o anterior. **"Pronto para voar"** significa que há firmware embarcado compilável, proteções testadas e decisão regulatória — é uma condição de *sistema*, que só existe depois que os dois portões anteriores passaram. Um portão só é declarado fechado quando **todos** os critérios dele estão ✅: não vale "está quase", não vale 14 de 15, não vale a média. Quando um portão fecha pela primeira vez, o `README.md` para de dizer *"Não fabrique esta placa ainda"* (hoje em `README.md:28`) e essa linha passa a ser o marcador visível de que o portão correspondente virou.

Ordem de leitura recomendada: `PLANO_FINAL.md` (visão geral) → este arquivo (o que falta) →
`plano/WP1_ROTEAMENTO.md` a `plano/WP5_DECISOES.md` (como fazer cada item).

---

## 2. Bloco A — Pronto para enviar à fabricação

Portão de **arquivo**. Nenhum destes critérios exige bancada; todos são verificáveis no PC.

| # | Critério binário (pergunta de sim/não) | Comando que verifica | Estado hoje | Quem resolve |
|---|---|---|---|---|
| A1 | Existe **exatamente uma** pasta de envio, e ela é a versão boa? | `ls fase3_pcb/v*/-drone_F_Cu.gtl \| wc -l` retorna `1` | ❌ **retorna 7** (v1…v7, mesmo nome `-drone_*` em todas) — `plano/WP2_FABRICACAO.md` §3.1 | você |
| A2 | Nenhuma net com pad ficou sem cobre? | `fase3_pcb/v8/verificacao_v8.txt` contém `0` em "nets sem trilha" | ❌ **138 nets com pad e zero trilha**; `fase3_pcb/v8/` está vazia (0 arquivos) — `plano/WP1_ROTEAMENTO.md` §1.5 | roteamento |
| A3 | Nenhum par de nets diferentes tem folga menor que 0,15 mm? | `test -e fase3_pcb/v8/clearance_v8.txt` com a linha `pares abaixo de 0,15 mm: 0`; hoje, `grep -c rule_area fase3_pcb/v7/v7_drone.kicad_pcb` | ❌ **o painel de clearance não existe**; e o arquivo de hoje nem declara regra alguma: `grep -c rule_area` → **0** keepouts — `plano/WP1_ROTEAMENTO.md` §5 | roteamento |
| A4 | Todo pad de GND e VBAT_PROT tem via a menos de 1,6 mm? | `cd /opt/jupyter/work/drone && /usr/bin/python3.9 plano/mede_v7_wp1.py` → `0` de `309` (tem de rodar com `/usr/bin/python3.9`, **não** com `python3` — ver a nota do interpretador abaixo da tabela) | ❌ **309 de 309** sem via próxima: `GND pads=207 vias=296 pads_sem_via_perto=207` e `VBAT_PROT pads=102 vias=21 pads_sem_via_perto=102` — `plano/WP1_ROTEAMENTO.md` §3.2 | roteamento |
| A5 | Existe o painel de verificação da versão enviada? | `test -e fase3_pcb/v8/verificacao_v8.txt` | ❌ **não existe**; o painel mais recente é `fase3_pcb/v6/verificacao_v6.txt` | roteamento |
| A6 | Existe esquema elétrico **nativo** KiCad? | `find . -name '*.kicad_sch' -o -name '*.sch' \| wc -l` > `0` | ❌ **0** — só há PNG em `fase1_esquema/` | você / fab |
| A7 | Existe netlist de produção? | `find . -name '*.net' \| wc -l` > `0` | ❌ **0** — `plano/WP2_FABRICACAO.md` §2.1 | você / fab |
| A8 | Existe arquivo de **pick-and-place** (CPL)? | `find . -name '*.pos' \| wc -l` > `0` | ❌ **0** — é o arquivo que a máquina de montagem lê para colocar os 319 módulos | assembler |
| A9 | Todo item de BOM tem **part number e preço reais**? | `grep -c EST orcamento/orcamento_detalhado.csv` retorna `0` | ❌ **37 itens** com `[EST]` de 43 — `plano/WP2_FABRICACAO.md` §2.5 | compras |
| A10 | Bibliotecas de símbolo/footprint exportadas? | `find . -name '*.lib' \| wc -l` > `0` | ❌ **0**; 30 footprints distintos estão embutidos no `.kicad_pcb` | você |
| A11 | O stackup da placa está declarado no arquivo? | `grep -c stackup fase3_pcb/v7/v7_drone.kicad_pcb` > `0` | ❌ **0**; sem isso a casa assume Defaults e pode errar a impedância do barramento de potência | você |
| A12 | Existe drill map / desenho dos furos? | `find . -name '*.drr' \| wc -l` > `0` | ❌ **0**; só há 2 `.drl` por versão | você / fab |
| A13 | Existe `.gbrjob` (unidade e zero declarados)? | `find . -name '*.gbrjob' \| wc -l` > `0` | ❌ **0** — desligado em `fase3_pcb/gera_pcb_v7.py:545` | você / CAM |
| A14 | O contorno em Edge.Cuts é `gr_line` fechado (não `gr_poly`)? | `grep -c "gr_line.*Edge.Cuts" fase3_pcb/v7/v7_drone.kicad_pcb` > `0` | ❌ **0** `gr_line`, **9** `gr_poly` — `plano/WP2_FABRICACAO.md` §2.3 | você |
| A15 | O `title_block` do board está preenchido? | `grep -c title_block fase3_pcb/v7/v7_drone.kicad_pcb` > `0` | ❌ **0** — placa sem identificação, sem revisão, sem data | você |
| A16 | O contador `(zones N)` do cabeçalho bate com as zonas reais? | comparar `(zones 0)` com `grep -c "^  (zone "` | ❌ cabeçalho diz **0**, existem **3** zonas reais | você |
| A17 | Os Gerbers da pasta de envio foram gerados **deste** `.kicad_pcb`? | `md5sum` do `.kicad_pcb` + `TF.CreationDate` de `head -3` do `.gtl` | ❌ não conferido: hoje o `.gtl` diz `2026-09-11T22:33:21-03:00` e o board é `md5 3dd3b23c…`; a comparação só vale quando existir v8 única | você / CAM |
| A18 | Os 9 Gerbers + 2 `.drl` existem na pasta de envio? | `ls fase3_pcb/v8/*.g* fase3_pcb/v8/*.drl \| wc -l` retorna `11` | ❌ **0 na v8**; os 11 existem em `fase3_pcb/v7/` — `plano/WP2_FABRICACAO.md` §2.1 | você / CAM |
| A19 | A documentação de montagem e teste acompanha o envio? | `test -e fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md -a -e fase4_entrega/PLANO_TESTE_BANCADA.md -a -e fase4_entrega/RISCOS.md -a -e fase4_entrega/SEGURANCA_E_REGULATORIO.md` | ✅ **os 4 existem** | — |
| A20 | O `README.md` autoriza a fabricação? | `grep -c "Não fabrique esta placa ainda" README.md` retorna `0` | ❌ **1**, em `README.md:28` | você |

**Portão A: 1 de 20 critérios passam.** Custo para fechar os 19 restantes: **30,0 h** `[EST]`
de geração de arquivos (`plano/WP2_FABRICACAO.md` §2) — mas o caminho crítico não é o arquivo, é
o roteamento (A2–A5), que bloqueia tudo. Prazos não são prometidos aqui.

> **Nota do interpretador (A4).** O único critério deste documento que depende de Python é o
> A4, e ele **precisa do interpretador 3.9 do sistema**, não do `python3` do PATH:
>
> ```sh
> $ python3 -V            # 3.12.13 (venv do agente)
> $ /usr/bin/python3 -V   # 3.9.2
> $ python3 plano/mede_v7_wp1.py
>   File "/opt/jupyter/work/drone/plano/mede_v7_wp1.py", line 19, in <module>
>       import pcbnew
>   ModuleNotFoundError: No module named 'pcbnew'
> $ /usr/bin/python3.9 -c "import pcbnew; print(pcbnew.GetBuildVersion())"
> 5.1.9+dfsg1-1+deb11u1
> ```
>
> O módulo `pcbnew` (KiCad 5.1.9, Debian Bullseye) está instalado **só** no 3.9. Nenhum outro
> critério do documento usa Python — todos os outros são `ls`, `find`, `grep`, `test` ou
> `md5sum`, que não têm esse problema.

---

## 3. Bloco B — Pronto para bancada

Portão de **medição**. Exige que o Portão A esteja fechado e a placa montada. A ordem dos
ensaios já está escrita em `fase4_entrega/PLANO_TESTE_BANCADA.md` (passos 1 a 15); aqui está
apenas o que precisa ser **verdade** para chamar a bancada de vencida.

| # | Critério binário (pergunta de sim/não) | Comando que verifica | Estado hoje | Quem resolve |
|---|---|---|---|---|
| B1 | Existe plano de bancada escrito e numerado? | `test -e fase4_entrega/PLANO_TESTE_BANCADA.md`; contagem real: `grep -cE '^## [0-9]+\. PASSO' fase4_entrega/PLANO_TESTE_BANCADA.md` | ✅ **existe**, 24 228 B, **15 passos** (`grep -cE '^## [0-9]+\. PASSO'` → `15`). ⚠️ o próprio plano tem uma referência órfã: `fase4_entrega/PLANO_TESTE_BANCADA.md:62` manda o termopar I8 para o "passo 16 (térmica)", que não existe — nenhum passo numerado é térmico. Isso é defeito do plano de bancada, corrigido aqui | — |
| B2 | Existe a ordem de solda? | `test -e fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` | ✅ **existe** | — |
| B3 | Existe análise de riscos? | `test -e fase4_entrega/RISCOS.md` | ✅ **existe** | — |
| B4 | Existe documento de segurança e regulatório? | `test -e fase4_entrega/SEGURANCA_E_REGULATORIO.md` | ✅ **existe** | — |
| B5 | Os instrumentos exigidos pelo plano estão fisicamente disponíveis? | `test -e fase4_entrega/logs/inventario_instrumentos.txt` com uma linha por instrumento **I1 a I11** de `fase4_entrega/PLANO_TESTE_BANCADA.md` §1, marcada presente/ausente e conferida **em bancada** | **não conferido** — **não reproduzível hoje**: o inventário de instrumentos é um dado físico da sua bancada e **não está no repositório**; o registro é `fase4_entrega/logs/inventario_instrumentos.txt`, que ainda não existe | você |
| B6 | Passo 1 (inspeção visual) executado e registrado? | existe log em `fase4_entrega/logs/passo1.txt` | ❌ não existe pasta `fase4_entrega/logs/` | bancada |
| B7 | Passo 2 (continuidade) executado, sem curto entre trilhos? | `test -e fase4_entrega/logs/passo2.txt` com veredito escrito | ❌ sem log | bancada |
| B8 | Passo 3 (resistência entre trilhos) medido e aprovado? | `test -e fase4_entrega/logs/passo3.txt` com valores em Ω | ❌ sem log | bancada |
| B9 | Passo 4 (primeira energização com fonte limitada, hélices removidas) passou? | `test -e fase4_entrega/logs/passo4.txt` com veredito | ❌ sem log | bancada |
| B10 | Passo 5: VBAT medido em 19,8 / 22,2 / 25,2 V com erro < 2 %? | `test -e fase4_entrega/logs/passo5.txt` com as 3 leituras e o erro | ❌ sem log | bancada |
| B11 | Passo 6: ripple de cada trilho medido dentro do limite? | `test -e fase4_entrega/logs/passo6.txt` | ❌ sem log | bancada |
| B12 | Passo 7: PWM sem potência, 20 kHz, período 50 000 ns ± 0,1 %? | `test -e fase4_entrega/logs/passo7.txt` | ❌ sem log | bancada |
| B13 | Passo 8: gate com subida e droop de bootstrap medidos? | `test -e fase4_entrega/logs/passo8.txt` | ❌ sem log | bancada |
| B14 | O Qg real do MOSFET foi medido no osciloscópio, não estimado? | `test -e fase4_entrega/logs/passo8.txt` com o **Qg em nC** (integral da corrente de gate), no bloco **8a do PASSO 8 — Teste de gate** — e não `passo9.txt`, que é o PASSO 9 de dead-time | ❌ **40 nC está `[CONTRADITO]`** pelo datasheet: real 168 nC (typ) / 210 nC (max) — `plano/WP3_PREMISSAS_DATASHEETS.md` P-06 | bancada |
| B15 | Existe a medição de corrente que substitui 30 A / 15 A? | `test -e fase4_entrega/logs/passo_corrente.txt` com A medidos | ❌ **nada foi medido**; 30 A/15 A são `[PREMISSA]` | bancada |

**Portão B: 4 de 15 critérios passam** — e os 4 que passam são documentos, não medições.
**Zero medições foram feitas.** Nenhum item de B5 a B15 pode ser marcado sem execute de bancada.

---

## 4. Bloco C — Pronto para o primeiro voo

Portão de **sistema**. Exige A e B fechados.

| # | Critério binário (pergunta de sim/não) | Comando que verifica | Estado hoje | Quem resolve |
|---|---|---|---|---|
| C1 | Existe firmware embarcado em C/C++? | `find . -name '*.c' -o -name '*.cpp' -o -name '*.h' \| wc -l` > `0` | ❌ **0 arquivos** — `plano/WP4_FIRMWARE.md` §3 | firmware |
| C2 | O firmware compila por **um** comando reproduzível? | `cd firmware && idf.py build` retorna 0 | ❌ não existe pasta `firmware/` | firmware |
| C3 | O mapa de pinos do firmware bate com o netlist do layout? | diff entre o pin map e `fase3_pcb/gera_pcb_v7.py` linhas 400–411 | ❌ **motores 2, 3 e 4 divergem inteiros e o pad 8 está trocado** — `plano/WP4_FIRMWARE.md` RF-07 | firmware + roteamento |
| C4 | A decisão do ADC externo foi tomada **e medida**? | `grep -rn "MCP3208\|ADS7953" firmware/` com veredito registrado | ❌ **NÃO DETERMINADO** (D-12 não traz horas) — 26 canais necessários, ADC1 do ESP32-S3 dá no máximo 20 | você + firmware |
| C5 | A limitação de corte por software foi decidida por escrito? | `grep -rn "D-13" plano/WP5_DECISOES.md` com resposta | ❌ pendente D-13 | você |
| C6 | Existe CI de watchdog externo no layout? | `grep -c "watchdog\|WATCHDOG" fase3_pcb/v7/v7_drone.kicad_pcb` > `0` | ❌ não há CI; `WD_FEED` só aparece no pad 25 e no `TP_WD` (D-07) | roteamento + você |
| C7 | O dead-time do motor que vai por LEDC foi medido em bancada? | `test -e fase4_entrega/logs/ensaio_M3.log` com o dead-time dos 6 canais **LEDC** (motores 3 e 4), 12 V, e a defasagem de 90° | ❌ **o valor de 518,750 ns é de RTL Verilog, não de firmware**, e ele é o do M2/MCPWM; no M3 a janela é 400–650 ns e não é programável — `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4.3 e `plano/WP4_FIRMWARE.md` RF-14 | bancada + firmware |
| C8 | O corte por perda de link é ≤ 200 ms, medido? | `test -e fase4_entrega/logs/ensaio_M10.log` com o instante de perda e o instante de corte | ❌ sem firmware | firmware |
| C9 | O reset por watchdog é ≤ 1 s e grava motivo legível? | `test -e fase4_entrega/logs/ensaio_M11.log` com o tempo de reset e o motivo impresso | ❌ sem firmware | firmware |
| C10 | A IMU fica estável com motor a 100 %? | `test -e fase4_entrega/logs/ensaio_M5.log` com a taxa angular antes/depois — **M5 é a IMU (ICM-42688-P); M6 é o barômetro** (`plano/WP4_FIRMWARE.md` §5) | ❌ sem firmware | bancada + firmware |
| C11 | Os 14 módulos de firmware estão com critério de aceite medido? | `grep -c "M0\|M1\|…\|M13" firmware/modulos.md` = 14, cada um com log | ❌ **14 módulos, 0 implementados** — `plano/WP4_FIRMWARE.md` §5 | firmware |
| C12 | A corrente de um motor é linear (< 2 %) entre 5 A e 30 A? | `test -e fase4_entrega/logs/ensaio_M4.log` com os pontos de 5 A a 30 A e o erro de linearidade | ❌ sem bancada; e 30 A é `[PREMISSA]` | bancada |
| C13 | As decisões do `plano/WP5_DECISOES.md` foram todas respondidas por você? | `grep -c 'Resposta do Jailton' plano/WP5_DECISOES.md` retorna `0`; e `grep -cE '^\| \*\*D-[0-9]+\*\*' plano/WP5_DECISOES.md` | ❌ **0** — hoje o WP5 traz opção e recomendação do agente, mas **nenhuma resposta sua**; e são **15** decisões (D-01..D-15), não 14 | você |
| C14 | O orçamento tem preço real em todos os itens? | `grep -c "EST" orcamento/orcamento_detalhado.csv` retorna `0` | ❌ **37 de 43** itens `[EST]` | compras |
| C15 | Os limites de corrente e o comportamento térmico saíram de `[PREMISSA]`? | `grep -n "PREMISSA" fase4_entrega/logs/*.txt` retorna vazio para corrente e térmica | ❌ **é `[PREMISSA]`** — `README.md` e `PLANO_FINAL.md` §1 | bancada |
| C16 | A conformidade regulatória brasileira está resolvida (registro/SISANT, peso, distância)? | `grep -n "SISANT\|ANAC" fase4_entrega/SEGURANCA_E_REGULATORIO.md` com veredito | **não conferido** — o documento existe, mas a decisão depende de você e de consulta externa | você |
| C17 | A bateria LiPo 6S real foi caracterizada e registrada? | `test -e fase4_entrega/logs/caracterizacao_bateria_6S.log` com a tensão por célula em carga e a capacidade em Ah | **não conferido** — **não reproduzível hoje**: nenhum pacote físico está no repositório; o registro será `fase4_entrega/logs/caracterizacao_bateria_6S.log` | você |
| C18 | Existe log de voo de um voo de teste sem carga útil? | `test -e fase4_entrega/logs/voo1.txt` | ❌ sem log | você |

**Portão C: 0 de 18 critérios passam.** Esforço rastreado: **320 h** `[EST]` de firmware
(160 h bancada + 160 h voo) = 8,0 semanas de 40 h `[CALC na plano/WP4_FIRMWARE.md §9.2]`.
Somando V2 (4–6 h) e os 34,0 h de arquivos, o total do plano é o que está em `PLANO_FINAL.md`.

---

## 5. O que **não** pode ser declarado pronto

Esta seção é a mais importante do documento. Ela existe para impedir que um número plausível
seja narrado como resultado.

**5.1 — Nada foi medido. Os limites de corrente são `[PREMISSA]`.**
Os números **30 A contínuo e 15 A** de `PLANO_FINAL.md` §1 **não** vieram de bancada nem de
datasheet: são premissas de projeto. Enquanto `fase4_entrega/logs/passo_corrente.txt` não
existir, é proibido escrever que a placa "entrega 30 A", "aguenta 15 A" ou "não aquece".
O mesmo vale para térmica, ripple e efficiency. `README.md` já registra esse aviso.

**5.2 — O Qg de 40 nC está errado por um fator ~4.**
O único MOSFET de referência (`datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf`,
p.4) traz `Qg = 168 nC (typ) / 210 nC (max)`, contra os 40 nC assumidos na Fase 0. O
dimensionamento de resistor de gate e de dissipação do IR2104 feito com 40 nC está
**subdimensionado ~4×** (`plano/WP3_PREMISSAS_DATASHEETS.md` P-06). Nenhum número de gate
derivado de 40 nC pode ser tratado como válido.

**5.3 — Quatro grandezas de projeto não têm fonte nenhuma.**
Ciss, ESR, ESL, a corrente nominal do XT60 e o Vf do diodo não têm fonte
(`plano/WP3_PREMISSAS_DATASHEETS.md` P-01 a P-15). Qualquer dimensionamento que dependa
delas é hipótese, não dado.

**5.4 — O dead-time de 518,750 ns não é uma medida do produto.**
Ele vem de simulação RTL (`fase2_simulacao/verilog/pwm_deadtime.v`, 0 violações em 362 060
ciclos, `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4.3). É um modelo de referência
validado — **não** é o dead-time do firmware embarcado. Pior: o MCPWM do ESP32-S3 cobre só
**2 motores**; os outros 2 vão por LEDC, **sem dead-time em hardware**, e ficam com dead-time
fixo de 400–650 ns no driver, não programável (`plano/WP4_FIRMWARE.md` RF-14, M3). Não diga
que os 4 motores têm o mesmo dead-time.

**5.5 — Nenhuma de readiness 1, 2 ou 3 existe ainda.**
Zero firmware, zero bancada, zero voo. Tudo acima da Fase 2 é plano, não resultado.

**5.6 — Um arquivo de 539 bytes na pasta `datasheets/` não é um datasheet.**
`datasheets/icm-42688-p.pdf.INVALIDO_HTML` é `HTML document, ASCII text` — foi baixado por
erro. Foi renomeado (não apagado) e está fora do glob `*.pdf`
(`plano/WP3_PREMISSAS_DATASHEETS.md` §3.1). Não conte-o como fonte do ICM-42688-P.

**5.7 — As decisões pendentes são 15, não 14.**
`plano/WP5_DECISOES.md` vai de **D-01 a D-15**, confirmado por
`grep -oE "D-[0-9]{2}" plano/WP5_DECISOES.md | sort -u | wc -l` → `15`. Mas
`PLANO_FINAL.md:77`, `PLANO_FINAL.md:235` e `PLANO_FINAL.md:281` dizem **14 (D-01..D-14)**.
A discrepância está em `PLANO_FINAL.md`; este documento usa **15** porque é o número
verificável. Corrigir `PLANO_FINAL.md` fica como tarefa do Jailton — aqui nada foi editado
além deste arquivo.

**Prova de que nenhuma decisão foi respondida — e por que o `✅` não vale como prova.**
O `✅` do WP5 marca a **opção recomendada do agente**, não uma decisão sua, e a contagem de `✅`
**muda conforme o arquivo muda**, então ela não pode ser usada como evidência. Duas contagens
independentes, nenhuma delas dependente de `✅`, ambas rodadas agora:

```sh
$ grep -cE '^\| \*\*D-[0-9]+\*\*' plano/WP5_DECISOES.md
15
$ grep -c 'Resposta do Jailton' plano/WP5_DECISOES.md
0
```

A primeira conta as decisões (15 linhas de tabela, uma por D-xx). A segunda conta as suas
respostas: **0**. Um `grep -c "✅"` aqui devolveria hoje `17` (16 opções recomendadas + 1 linha de
resumo que se auto-referencia) e não prova nada — é exatamente o número que muda a cada edição do
WP5.

### 5.8 — O que fazer com os Gerbers enquanto a placa não fecha

Os Gerbers que existem hoje **não são de produção**. São de desenvolvimento intermediário.
Cinco regras enquanto o Portão A estiver aberto:

1. **Não enviar a nenhuma casa.** Nenhum arquivo de `fase3_pcb/v1/` a `v7/` vai para o
   fabricante. Um Gerber de v7 com 138 nets sem cobre produz uma placa que não funciona e
   custa dinheiro.
2. **Nomear a pasta como rascunho, nunca como envio.** Nenhuma pasta nova deve se chamar
   `fab`, `envio`, `producao` ou `release` antes de o Portão A fechar. Hoje as 7 pastas se
   chamam `v1…v7` e todas gravam arquivos com o **mesmo nome** (`-drone_F_Cu.gtl` etc.) — é
   por isso que A1 retorna 7.
3. **Nunca renomear os arquivos `-drone_*` por conta própria.** O prefixo vem do campo
   `Comment` do `title_block`, e como o `title_block` está vazio (A15) o KiCad 5.1 cai no
   nome do arquivo. Consertar A15 muda o nome de todos os Gerbers — faça os dois juntos, e
   **versione o nome**: `v8_drone_F_Cu.gtl`, com a revisão no `title_block` e na data.
4. **Uma pasta de envio por vez, e só ela vai para o git.** Enquanto houver 7 versões com
   gerber, qualquer pessoa que rodar `ls fase3_pcb/v*/-drone_F_Cu.gtl` recebe 7 respostas e
   não sabe qual é a boa. O critério A1 existe exatamente para fechar essa ambiguidade.
5. **Manter o histórico, não a confusão.** Os `.gitignore` já excluem `.ipynb_checkpoints/`
   e `__pycache__/`. Não exclua versões antigas de Gerbers do git: elas são o registro de
   que a placa evoluiu. O que se faz é não misturá-las com a pasta de envio.

O aviso `README.md:28` — *"Não fabrique esta placa ainda"* — **permanece até A2, A4 e A20
passarem**. Ele não é burocracia: é o critério A20.

---

## 6. Contagem final

Conferido em **2026-09-28**, nesta sessão, contra a árvore no momento da leitura, branch `main`,
sem push. Referência da árvore: `cd /opt/jupyter/work/drone && git rev-parse --short HEAD` — é um
ponteiro que **avança a cada commit**, então nenhum hash é congelado aqui e nenhuma contagem
deste documento (número de commits, de linhas, de arquivos) é válida para outra árvore.

| Portão | Critérios | Passam hoje | % |
|---|---|---|---|
| A — Pronto para fabricar | 20 | **1** (A19, documentação) | 5 % |
| B — Pronto para bancada | 15 | **4** (B1–B4, os quatro documentos) | 27 % |
| C — Pronto para primeiro voo | 18 | **0** | 0 % |
| **Total** | **53** | **5** | **9 %** |

Leitura honesta do número: os 5 critérios que passam são **documentos escritos**, não
medições e não artefatos de fabricação. Nenhuma das 3 portas de hardware foi atravessada.
**Nenhum porte de tensão, de corrente ou de voo foi demonstrado nesta máquina, porque esta
máquina não tem bancada** — logo, tudo acima da Fase 2 continua sendo plano.

O caminho crítico hoje é o roteamento (**A2 → A4**), não a geração de arquivos: fechar os
30,0 h `[EST]` de artefatos sobre uma placa com 138 nets sem cobre entrega ao fabricante um
arquivo completo e inutilizável.

### 6.1 Os 20 comandos do Portão A, um por critério

Um portão só fecha com **todos** os seus critérios em ✅ (§1). A receita antiga checava 4
números e agregava quatro critérios num só — com isso, um `.gbrjob` sozinho fazia A6, A7 e A8
parecerem resolvidos, e 14 dos 20 critérios (incluindo A2 e A4) nunca eram olhados. A receita
abaixo é a correção: **20 comandos, uma linha de saída por critério.** Nunca some dois critérios
no mesmo número.

Rode **os 20** a partir de `/opt/jupyter/work/drone`. A saída esperada são **20 linhas, uma por
critério** (mais o `md5sum` do A17, que também é uma linha só). O valor "passa" está no comentário
de cada linha; hoje só o A19 passa.

```sh
# A1  passa = 1        | hoje 7 (v1..v7 gravam o mesmo nome)
ls fase3_pcb/v*/-drone_F_Cu.gtl | wc -l
# A2  passa = 1 linha  | hoje 0: o arquivo da v8 nao existe
cat fase3_pcb/v8/verificacao_v8.txt 2>/dev/null | grep -c "ZERO trilha *: 0"
# A3  passa = 1 linha  | hoje 0: o painel de clearance da v8 nao existe
cat fase3_pcb/v8/clearance_v8.txt 2>/dev/null | grep -c "pares abaixo de 0,15 mm: 0"
# A4  passa = 0        | hoje 2 linhas: 207 GND + 102 VBAT_PROT sem via perto
/usr/bin/python3.9 plano/mede_v7_wp1.py | grep -c "pads_sem_via_perto"
# A5  passa = 1        | hoje 0
ls fase3_pcb/v8/verificacao_v8.txt 2>/dev/null | wc -l
# A6  passa > 0        | hoje 0
find . -name '*.kicad_sch' -o -name '*.sch' | wc -l
# A7  passa > 0        | hoje 0
find . -name '*.net' | wc -l
# A8  passa > 0        | hoje 0
find . -name '*.pos' | wc -l
# A9  passa = 0        | hoje 37 itens [EST]
grep -c EST orcamento/orcamento_detalhado.csv
# A10 passa > 0        | hoje 0
find . -name '*.lib' | wc -l
# A11 passa > 0        | hoje 0 (o cabecalho declara 0)
grep -c stackup fase3_pcb/v7/v7_drone.kicad_pcb
# A12 passa > 0        | hoje 0
find . -name '*.drr' | wc -l
# A13 passa > 0        | hoje 0
find . -name '*.gbrjob' | wc -l
# A14 passa > 0        | hoje 0 gr_line (sao 9 gr_poly)
grep -c "gr_line.*Edge.Cuts" fase3_pcb/v7/v7_drone.kicad_pcb
# A15 passa > 0        | hoje 0
grep -c title_block fase3_pcb/v7/v7_drone.kicad_pcb
# A16 passa = 1        | hoje 0: o cabecalho diz (zones 0) e existem 3
grep -m1 "(zones" fase3_pcb/v7/v7_drone.kicad_pcb | grep -c "(zones 3)"
# A17 o .gtl tem de nascer deste .kicad_pcb | hoje gtl de 2026-09-11, board md5 3dd3b23c
md5sum fase3_pcb/v7/v7_drone.kicad_pcb
# A18 passa = 11       | hoje 0 na v8 (os 11 existem na v7)
ls fase3_pcb/v8/*.g* fase3_pcb/v8/*.drl 2>/dev/null | wc -l
# A19 passa = 4        | hoje 4  <-- o unico criterio do Portao A em ✅
ls fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md fase4_entrega/PLANO_TESTE_BANCADA.md \
   fase4_entrega/RISCOS.md fase4_entrega/SEGURANCA_E_REGULATORIO.md | wc -l
# A20 passa = 0        | hoje 1, em README.md:28
grep -c "Não fabrique esta placa ainda" README.md
```

O A19 é o único que passa hoje. Para o Portão A fechar, **todos os 20** precisam chegar ao valor
"passa" — o que fecha o arquivo é A19 mais os outros 19, não A19 mais uma média. Os 15 comandos
do Portão B (`test -e fase4_entrega/logs/…`, um por log) e os 18 do Portão C estão nas colunas 3
das §3 e §4 e se lêem do mesmo jeito: um comando, um critério, um arquivo.

---

## 7. Correções round 2 (2026-09-28)

Seis defeitos deste próprio documento, encontrados por conferência e corrigidos aqui. Nenhum
número de estado mudou: a contagem final continua **5 de 53** (1/20 + 4/15 + 0/18), e nenhum
❌ foi inflado.

| # | Defeito | Correção | Evidência rodada |
|---|---|---|---|
| F1 | 🔴 O comando do A4 (`python3 plano/mede_v7_wp1.py`) **não roda**: `pcbnew` só existe no Python 3.9 do sistema | A4 passou a usar `/usr/bin/python3.9`; a saída real foi colada na linha do critério, e há uma nota abaixo da tabela do Portão A sobre o interpretador | `python3` → `ModuleNotFoundError: No module named 'pcbnew'`; `/usr/bin/python3.9 -c "import pcbnew; print(pcbnew.GetBuildVersion())"` → `5.1.9+dfsg1-1+deb11u1`; o script imprime `GND pads=207 vias=296 pads_sem_via_perto=207` e `VBAT_PROT pads=102 vias=21 pads_sem_via_perto=102`. **A4 era o único critério com Python** — os outros 52 são `ls`/`find`/`grep`/`test`/`md5sum` |
| F2 | 🔴 A §5.7 afirmava `grep -c "✅" plano/WP5_DECISOES.md` → `15`; o real é `17`, e esse número muda a cada edição do WP5 | Trocado por duas contagens **não auto-referentes**: uma conta as decisões, a outra conta as suas respostas. A mesma correção foi aplicada no C13, que tinha o mesmo `grep -c` com o valor trocado | `grep -cE '^\| \*\*D-[0-9]+\*\*' plano/WP5_DECISOES.md` → `15`; `grep -c 'Resposta do Jailton' plano/WP5_DECISOES.md` → `0` |
| F3 | 🔴 Proveniência impossível: o documento congelava um **hash de commit** como origem das medições, e esse commit era o **pai** do commit que criou o próprio `DO_PROJETO.md` — o arquivo nem existia na árvore citada. O HEAD já tinha avançado antes disso: o commit mais recente alterou 232 linhas do `plano/WP5_DECISOES.md`, que é a fonte do número da §5.7 | Removida **toda** citação de hash — inclusive desta linha, que descreve o defeito sem repeti-lo. Agora é "medido nesta sessão, em 2026-09-28, contra a árvore no momento da leitura", com `git rev-parse --short HEAD` citado como **referência que avança a cada commit**. Nenhuma contagem que o próprio commit do documento invalide (commits, linhas, arquivos) é impressa | `grep -cE '\b[0-9a-f]{7}\b' plano/DO_PROJETO.md` → **0** (nenhum hash de commit no documento); `git rev-parse --short HEAD` → ponteiro móvel, que já avançou **durante esta própria rodada** |
| F4 | 🟠 A §6 contradizia a §1: a receita tinha 4 comandos, agregava A6+A7+A8+A13 num único `find` (um `.gbrjob` só faria os três parecerem resolvidos) e deixava 14 dos 20 critérios sem checagem, entre eles A2 e A4 | §6.1 reescrita: **20 comandos, uma linha de saída por critério**, sem agregação. O texto diz explicitamente que a saída esperada são 20 linhas | `ls fase3_pcb/v*/-drone_F_Cu.gtl \| wc -l` → `7`; A19 → `4`; A4 → `2`; os outros 18 critérios, cada um com sua linha |
| F5 | 🟠 B1 e o §1 diziam "16 passos"; o plano de bancada tem **15** seções de passo. E o B14 apontava o Qg para `passo9.txt`, que é o PASSO 9 de **dead-time** — o Qg é medido no PASSO 8 (teste de gate) | §1 e B1 corrigidos para 15; a referência órfã "passo 16 (térmica)" de `PLANO_TESTE_BANCADA.md:62` foi registrada como defeito **do plano de bancada**, sem editar esse arquivo; B14 passou a `fase4_entrega/logs/passo8.txt` (bloco 8a) | `grep -cE '^## [0-9]+\. PASSO' fase4_entrega/PLANO_TESTE_BANCADA.md` → `15`; `sed -n '62p'` → `\| I8 \| Termopar tipo K ou câmera térmica \| −50…+300 °C \| passo 16 (térmica) \|` |
| F6 | 🟡 Sete critérios sem comando nem arquivo (A3, C7, C8, C9, C10, C12, C17) diziam "log do ensaio M10" sem dizer qual arquivo; e B5 dependia de um inventário que não está no repositório | Cada um ganhou um caminho específico, no mesmo padrão de B6–B13 e B15. A3 aponta `fase3_pcb/v8/clearance_v8.txt`; C7→`ensaio_M3.log`; C8→`ensaio_M10.log`; C9→`ensaio_M11.log`; C10→`ensaio_M5.log`; C12→`ensaio_M4.log`; C17→`caracterizacao_bateria_6S.log`; B5→`inventario_instrumentos.txt`, conferido em bancada e marcado como **não reproduzível hoje** | `plano/WP4_FIRMWARE.md` §5: **M5 é a IMU (ICM-42688-P)** e M6 é o barômetro — o C10 apontava para o módulo errado; M3 é o PWM dos motores 3 e 4 por LEDC; `PLANO_TESTE_BANCADA.md` §1 lista I1–I11. Nenhum dos caminhos existe ainda: `ls fase4_entrega/logs` → `No such file or directory` |

O que **não** foi tocado nesta rodada: a contagem 5/53, a honestidade dos estados (nenhum "não
conferido" contado como aprovado), os 14 números de coerência com os WPs, a §5 inteira ("o que
não pode ser declarado pronto") e a regra dos 7 Gerbers homônimos da §5.8.

---

*Documento gerado por medição direta no repositório. Nenhum número aqui foi estimado sem
comando; os estados não conferíveis estão marcados como "não conferido" e não foram contados
como aprovados.*
