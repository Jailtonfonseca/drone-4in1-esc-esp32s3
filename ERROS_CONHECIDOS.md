# ERROS_CONHECIDOS — registro central de erros do projeto

**Drone 4×ESC + ESP32-S3** · atualizado em 2026-10-05 · correções do pipeline no commit `7ee221e` · **auditoria independente + correções v10 em 2026-10-04/05 (seção 8)**

## Como usar este arquivo

- Toda entrada segue: **sintoma → causa raiz (evidência, arquivo:linha) → correção → status**.
- Status: `[CORRIGIDO]` resolvido e verificado · `[CONTORNADO]` mitigado, causa de fundo segue · `[ABERTO]` pendente de resolução · `[SUPERSEDED]` era verdade numa versão anterior, já substituída · `[REGISTRO]` não é erro, é decisão/achado que precisa constar.
- Detalhe técnico completo do pipeline de roteamento: `fase3_pcb/freerouting/FONTE_FREEROUTING.md`.

---

## 1. Pipeline de roteamento FreeRouting (7 corrigidos, 1 aberto)

As duas primeiras execuções (28/09 e 03/10) morreram **travadas**, não "calculando". O pipeline
nunca havia sido validado ponta a ponta antes disso.

| # | Sintoma | Causa raiz | Correção | Status |
|---|---------|-----------|----------|--------|
| 1.a | Batch headless trava logo após "Opening…" sem erro nenhum | `import_design()` (`BoardHandling.java:870`) abre um `JOptionPane` **modal** se a leitura do DSN gerar *qualquer* warning; dentro do Xvfb ninguém clica no OK → `futex_wait` eterno | DSN sem nenhum warning (1.b, 1.d, 1.e) + `fr_watchdog.py`, que detecta o display pelo `/proc` e aperta Return via XTEST | CORRIGIDO |
| 1.b | "Auto-routing completed" com 0 rotas; pads "not an area" | Ordem dos argumentos do círculo: exportávamos `(circle layer x y diam)`, o leitor espera `(circle layer diam x y)` → pads THT e VIA1 liam `x` como diâmetro = pontos de diâmetro zero | `dsn_export.py` emite `(circle layer diam x y)` | CORRIGIDO |
| 1.c | Otimização nunca termina (>400 s num recorte de 9 nets) | `optimization_improvement_threshold: 0.0`; `BatchOptRoute.java:109` faz `while (route_improved >= threshold)` — melhoria nula mantém o loop | threshold 0.05 no `freerouting.json` | CORRIGIDO |
| 1.d | Warnings "winding number != 0" na leitura | Outline concatenava toda a silkscreen do footprint num único polígono autointersectante | Outline = retângulo do bounding box | CORRIGIDO |
| 1.e | Warning "old KiCad has known compatibility issues" | `host_cad "kicad"` com versão baixa disparava aviso (gatilho do modal 1.a) | `host_cad "dsn_export.py (pcbnew 5.1.9)"` | CORRIGIDO |
| 1.f | Trilhas importadas 1000× mais finas que roteadas | Largura do SES vem em µm (`resolution mm 1000`) e era passada sem ×1000 ao `SetWidth` do pcbnew (nm) | `ses_import.py` aplica a escala | CORRIGIDO |
| 1.g | Risco de sinal em plano de massa e regras ausentes | Camadas internas sem `type power`; sem regra global de largura; boundary colado na borda; nets de 30 A dentro do autorroteador | `In1/In4 (type power)`, regra `(width 0.25)(clear 0.20)`, boundary recolhido 0,95 mm, **28 nets de alta corrente fora do DSN** (GND, VBAT, VBAT_F, VBAT_PROT, 12× PHM, 12× SNM — cobre vem de zonas no KiCad) | CORRIGIDO |
| 1.h | SES gravado com **0 wires** apesar de "Auto-routing completed in 0.82 s" | `network_out` vazio (`SpecctraSesFileWriter.write_net` itera `get_connectable_items`) significa que o board não tinha **nenhum** `PolylineTrace`/`Via` no momento da gravação — o roteador não criou rotas. Já descartado: matching (componente, pin) são (`Net.java:101` + `TreeSet`/`compareTo` em `Net.get_pins`) e o split `comp-pin` no primeiro hífen — ambos sãos. Próximo: thread de autoroute batch (por que "conclui" em 0,82 s sem criar nada) | — | **ABERTO** |

- **1.i (armadilha de ambiente):** o `freerouting.json` é lido de `java.io.tmpdir` (`/tmp/`), **não** do diretório corrente (`StartupOptions.java:17`). Reboot apaga o `/tmp` e o app volta aos defaults **em silêncio**. O runbook agora exige `cp freerouting.json /tmp/`. `[CONTORNADO]`
- **1.j (correção de leitura):** o `exit=124` das primeiras rodadas era timeout do meu wrapper, não crash do app. `[REGISTRO]`

---

## 2. Board / PCB — estado da v9 (saída de `fase3_pcb/v9/verificacao_v9.txt`)

1. **189 nets NÃO roteadas, `tracks = 0`** — a placa v9 está posicionada (319 footprints, 1093 pads,
   402 vias de stitch, 102 zonas) mas sem roteamento de sinal. Bloqueado pelo item **1.h**. `[ABERTO]`
2. **A4 `[FALHA]`: 34 pads de GND/VBAT_PROT sem via a <1,6 mm** — ex.: `QM101H.2`…`QM301H.2`,
   `J2.A12`, `J2.A1`, `U_MCU.41`, `U_MCU.1`, `Cblk1..6`, `D1`, `Q1`, `RsM402.2`, `CaM203` (lista
   completa em `verificacao_v9.txt`). `[ABERTO]`
3. **Zonas de cobre não cobrem todos os pads da própria net** (raster 0,25 mm, flood fill):
   12V 12 sem cobertura, 3V3 8, 3V3_A 1, 5V 3, GND 18, VBAT_PROT 9 — "coberta: nao" nas 6 nets. `[ABERTO]`
4. **627 conexões abertas** no ratsnest do pcbnew (consequência do item 2.1). `[ABERTO]`
5. **Histórico (SUPERSEDED pela v9):** v6 — 367 nets não roteadas + 12 folgas críticas trilha×pad;
   v7 — 229 posições puladas em 12 clusters, `rota_v7.py` interrompido; v8 — abandonado vazio.
6. **Gerber sem bloco `(title)` no `.kicad_pcb`** → nome `-drone_F_Cu.gtl`, idêntico em todas as
   versões (risco de sobrescrever pacotes de versões diferentes). A v9 grava `v9_drone-*`. `[CORRIGIDO na v9]`
7. **`kicad-cli` ausente na máquina** → Gerber gerado por script pcbnew (5.1.9). `[CONTORNADO]`
8. **KiCad 5.1 não aceita `(setup stackup)` no arquivo** → stackup mantido em `v9_drone_stackup.txt`. `[CONTORNADO]`

---

## 3. BOM / orçamento

1. **`BOM_FABRICACAO_atualizada.csv` tinha só 4 linhas** (truncada no meio da atualização de preços —
   armadilha: pedir por ela compraria 3 itens). **[CORRIGIDO 2026-10-12]: arquivo REMOVIDO**;
   a fonte única de fabricação é `orcamento/BOM_FABRICACAO_v10.csv` (43 itens × 16 campos,
   MOSFET vencedor). `BOM_FABRICACAO.csv` (43 itens) permanece como registro da fase 0.
2. **`ORCAMENTO.md`: 38 marcadores `[EST]`** — 37/43 itens sem cotação real. Bloqueio medido: LCSC
   retorna Access Denied (Akamai) e o ML devolve páginas de erro; apenas 3 âncoras reais
   (ICM-42688-P US$ 4,91 DigiKey; ESP32-S3-WROOM-1 R$ 56,91 ML; XT60 R$ 9,59/par ML).
   Substituição dos `[EST]` exige sessão de navegador do Jailton. `[ABERTO]`
3. **Preços reais via API EasyEDA na BOM de fabricação: 36/43 itens** com `preco_unitario`
   preenchido (7 sem preço; estado anterior registrado de 29/43 foi superseded). `[PARCIAL]`
4. **BOM de versões antigas duplicava indutores de saída (3→6) e Cout (6→12)** — achado do
   `orcamento.py`; a fonte de verdade de quantidades é `fase0_especificacao/lista_componentes_fase0.csv`
   (43 itens). `[CORRIGIDO no orçamento — conferir na BOM final]`
5. **INA240 (12 un.) = 31% do custo de componentes** (US$ 31,20) — alavanca de custo, não defeito. `[REGISTRO]`
6. **Placa v6 de 220×160 mm (352 cm²)** era a maior alavanca de custo de PCB — v9 reduzida para
   190×145 mm (60,05% de ocupação). `[CORRIGIDO]`

---

## 4. Datasheets (`datasheets/`)

1. **`icm-42688-p.pdf.INVALIDO_HTML`** — download veio HTML em vez de PDF; mantido como registro
   honesto da falha, substituído por versões válidas. `[CORRIGIDO]`
2. **Duas versões válidas do ICM-42688-P coexistem (v1.2 e v1.6)** — padronizar a v1.6 como
   referência única do projeto. `[ABERTO]`
3. **FreeRouting 1.4.4: download de 9 bytes (quebrado)** — substituído pela 1.9.0 (5.044.336 bytes). `[SUPERSEDED]`
4. Decisões registradas nos próprios nomes de arquivo: `PSMN5R2-60YLX…REPROVADO_QG`,
   `NVMFS6H824NT1G…VENCEDOR`, demais `ALTERNATIVA/REFERENCIA`. `[REGISTRO]`

---

## 5. Firmware

1. **13 arquivos marcados "ESQUELETO NAO VERIFICADO"** (10 `.c/.h` de `main/` + 2 `CMakeLists.txt`
   + `sdkconfig.defaults`) — código ainda não compilado nesta máquina; os cabeçalhos declaram isso
   explicitamente. `[ABERTO — estado conhecido e declarado]`
2. Toolchain Xtensa aarch64 instalada e funcional (gera `.elf`) — ver `fase4_entrega/FIRMWARE_BUILD.md`. `[OK]` *(link corrigido em 2026-10-05 — o arquivo está em fase4_entrega/, não em firmware/)*

---

## 6. Ambiente / infraestrutura

1. **Reboot às 04:00 de 04/10 apagou o `/tmp`**: `freerouting.json`, o `.frb` intermediário
   (evidência) e o clone do código-fonte. Mitigações aplicadas: logs e artefatos de teste commitados
   no repositório (`teste/corte_v9.*`), clone do fonte movido para `/opt/fr-src` (fora do tmpfs),
   runbook com o passo `cp …/freerouting.json /tmp/`. `[MITIGADO]`
2. **`cacerts` do JRE**: symlink aponta para `/etc/ssl/certs/java/cacerts`, reconstruído
   (174 KB, 28/09), porém o erro `trustAnchors parameter must be non-empty` **ainda apareceu** no
   log de 03/10 02:29 — não-fatal (só afeta o phone-home de analytics; o roteamento segue).
   Verificar qual truststore o Java 17 efetivamente usa. `[ABERTO — não-fatal]`
3. `kicad-cli` ausente; FreeRouting exige `xvfb-run`; JRE 17 arm64 — runbook completo em
   `FONTE_FREEROUTING.md`. `[CONTORNADO]`

---

## 7. Onde NÃO há erros registrados

- **Fase 2 (SPICE):** 35 resultados com coluna "fonte do valor esperado" e chave de log
  (`fase2_simulacao/resultados_fase2_spice.csv`).
- **Fase 1:** 9 figuras; fig 1 e fig 5 refeitas em v3 por **legibilidade** (escala de texto,
  não defeito elétrico).
- **Fase 4:** 8 documentos de entrega (`MONTAGEM_ORDEM_DE_SOLDA.md`, `PLANO_TESTE_BANCADA.md`,
  `RISCOS.md`, `SEGURANCA_E_REGULATORIO.md`…); pendências regulatórias (SISANT, peso, distância)
  documentadas como verificação **pré-voo**. `[ABERTO por design]`

---

## Próximo passo

`verificacoes/verifica_projeto.py` — automatizar todas as checagens acima como **asserções duras**
(SES `wires > 0`, `nets não roteadas == 0`, `[EST] == 0`, preços preenchidos), para que "pronto"
seja propriedade do artefato e não da impressão da sessão.

---

## 8. AUDITORIA INDEPENDENTE 2026-10-04 — ~110 erros (ver `AUDITORIA_ERROS_2026-10-04.md`)

Uma auditoria externa do repositório inteiro (forense de artefatos + leitura do fonte do
FreeRouting 1.9.0 + 4 subauditorias) encontrou **~110 erros**, sendo 9 bloqueadores, e
**refutou 3 alegações deste registro** (ver 8.R). Relatório completo com evidência
arquivo:linha em [`AUDITORIA_ERROS_2026-10-04.md`](AUDITORIA_ERROS_2026-10-04.md).

### 8.1 — CRÍTICOS novos CORRIGIDOS em 2026-10-04/05 (v10)  `[CORRIGIDO na v10]`

| # | Erro | Causa raiz | Correção aplicada | Prova |
|---|---|---|---|---|
| 1 | 27 footprints/199 pads FORA do contorno (U_MCU inteiro, 14 MOSFETs, USB-C, shunt, bulk) + 14 curtos pad×pad | `gera_pcb_v9.py:252` sinal invertido (`x − dx` em vez de `+ dx`) + `GetBoundingBox()` inflado por texto de silk | `gera_pcb_v10.py`: sinal corrigido, bbox por pads; board v10 regenerada | gate G1/G3: 0 fora, 0 curtos |
| 2 | 12 nets BEMF órfãs + ferrite órfão | **typo de net** no `gera_pcb_v7.py`: `"RB%s"` (RBM101) no motor vs `"RB_M%d01"` no ADC; FLDO.2 em net de 1 pad | `RB_%s` padronizado; `3V3_IMU` criada (IMU+baro pós-ferrite) | gate G2: 0 nets de 1 pad; RB_M### com 4 pads |
| 3 | Nets de potência SEM cobre (VBAT, VBAT_F, 12×PHM, 12×SNM) — **refuta o 1.g "CORRIGIDO"** | só 6 nets tinham zonas; a justificativa do 1.g valia só para GND/VBAT_PROT | 34 zonas novas no gerador v10 | gate G5: 173/173 preenchidas |
| 4 | Bug 1.h (SES com 0 wires) — **causa raiz no `dsn_export.py`, não no roteador** | **P1 `0 == False`**: todo pad virava círculo Ø=max(w,h) → blobs selados; **P2 via nunca declarada** (`(via VIA1)`); P3 rotação dupla; P4 pins duplicados (~39 mil) | P1–P5 corrigidos; via 0,6/0,3 | corte E2E: **46 wires, 8 vias, 9/9 nets, 83 trilhas importadas** (antes 0) |
| 5 | 57 de 102 zonas vazias; 8 vias no keepout; keepout superior faltando | ilhas sem âncora + `acha_via` com limite 0,8 < 0,9+folga; `keepout()` sem a faixa do topo | v10: todas as bordas com keepout; busca de via keepout-aware | gates G4/G5 |
| 6 | BOM mandava comprar MOSFET errado (IPB017N10N5 TO-263-7) + 2 linhas malformadas | linha de referência nunca editada; separador faltando | `orcamento/BOM_FABRICACAO_v10.csv` (vencedor NVMFS6H824NT1G; ADC alinhado ao board: 4× MCP3208) | 43 itens × 16 campos |
| 7 | `ses_import.py` nunca tinha completado 1 execução | `GetNetCode()` inexistente; classes `PCB_TRACK/PCB_VIA` (KiCad 6); `walk_net` não descia ao escopo `(net NOME …)` | API 5.1 correta + parser do formato real | 83 trilhas + 8 vias gravadas no KiCad |
| 8 | Roteamento da placa completa saía vazio | consequência do item 4 | pipeline corrigido + 50 min de roteamento real | **placa completa: 1.410 wires, 404 vias, 149/151 nets, 3.909 trilhas importadas** (`fase3_pcb/v10/freerouting_run/` + `v10_roteada.kicad_pcb`) |

---

## 9. AUDITORIA 2026-10-12 — 3 achados críticos + gate novo G8 + harness

Auditoria independente nº 2 (ferramentas idênticas às do agente: pcbnew 5.1.9, fonte do
FreeRouting, execução real do pipeline). Arquivo-fonte dos achados: execução desta sessão.

### 9.1 — CRÍTICO novo: board roteado com 354 curtos trilha×cobre-excluído  `[CORRIGIDO — re-roteamento em andamento]`

**Sintoma:** a roteagem v10 "passou" na prova E2E (contagens de importação) mas o DSN
exclui 28 nets de potência (GND, VBAT, VBAT_F, VBAT_PROT, 12×PHM, 12×SNM) **com todo o seu
cobre sólido**: 398 vias de stitch + 363 pads. O FreeRouting não os via e roteou trilhas
**por cima** — medição exata (distância segmento×retângulo rotacionado, folga 0,15 mm):
**354 violações** (d até −0,93 mm), ex.: `12V × via (87.75,58.62) d=-0.425`,
`VBM101 × via (149.05,65.60) d=-0.238`. Nenhum gate cobria track×cobre-excluído.

**Causa raiz:** `dsn_export.py` emitia pins de TODOS os componentes no `(library ...)` mas
as nets excluídas não entravam no `(network ...)` — no Specctra, pin sem net não é obstáculo.

**Correção:** `dsn_export.py` agora exporta **cada pad e via de net excluída como
`(keepout (rectangle LAYER x1 y1 x2 y2))`** (cobre + clearance 0,2; SMD no lado, THT/via em
todas as 6 camadas) — **3.167 keepouts**. Parser conferido no fonte (`Structure.java:870`,
`Shape.read_rectangle_scope`). Nova roteagem completa disparada com o DSN novo.

**Prova:** gate novo **G8** em `verifica_fase3_v10.py` (0 violações exigidas, matemática
exata segmento×retângulo rotacionado). No board antigo: G8 = **354 violações [FALHA]**.

### 9.2 — CRÍTICO: o board v10 commitado estava STALE em relação ao próprio gerador  `[CORRIGIDO]`

**Sintoma:** a verificação commitada (`f58c376`, 05/10) mostra G6 com **18 pads sem via**,
mas o `gera_pcb_v10.py` commitado NO MESMO COMMIT já continha o fix `[FIX auditoria G6]`
(raio estendido) e produz apenas **2** pads sem via.

**Causa raiz:** o fix do gerador foi commitado **sem re-rodar** o gerador/verificador —
o board + verificação em `f58c376` são da execução ANTERIOR. Regenerado: +51 vias.

**Correção:** regeneração executada; verificação nova: **TODOS OS GATES OK (G1–G7)**.

### 9.3 — MODERADO: os 2 últimos pads sem via (G6) — modelo de colisão cego para net  `[CORRIGIDO]`

`U_IMU.7` e `U_LDO.GND` falhavam mesmo com o raio estendido, porque o índice de ocupação
trata TODO pad como **círculo circunscrito** e ignora a **net**: um pad GND vizinho bloqueava
uma via GND (via pode tocar cobre da própria net — via-in-pad GND é prática padrão de stitch).
Correção: **3ª passada** no gerador com (a) colisão retangular borda-a-borda para pads de
outra net (o mesmo modelo do gate), (b) isenção de mesma-net, (c) conferência de **via
compartilhada** ≤1,6 mm antes de buscar (o gate conta qualquer via próxima — `U_IMU.7` já
estava a 0,90 mm da via do `U_IMU.9`). Resultado: **resgatados 1, cobertos 1, restam 0**.

### 9.4 — Gate novo G8 + harness `verifica_projeto.py` (o "Próximo passo" §fim, nunca construído)  `[IMPLEMENTADO]`

- **G8** (`verifica_fase3_v10.py`): trilha×cobre de net excluída = **0 violações**, com
  distância exata segmento×retângulo rotacionado (projeção alternada) — o gate que teria
  pego os 354 curtos da 9.1.
- **`verificacoes/verifica_projeto.py`**: o harness de asserções duras pedido no
  "Próximo passo" — SES (wires/vias/cobertura 100% das nets), gates G1–G8 na base E no
  roteado, cobertura de rota das nets de sinal, BOM (43 itens, vencedor único, preço em
  100% das linhas **compráveis**, zero `[EST]`). Exit 1 com lista exata do que falta.
  Estado atual que ele expõe (antes do re-roteamento terminar): IMU_CS/IMU_INT sem rota,
  G6/G8 no board antigo, 1 linha comprável sem preço (ADC/MCP3208).

### 9.5 — Lint (relatório `concise`, não commitado): 10× S110 try-except-pass  `[CORRIGIDO nos vivos]`

2 ocorrências em código vivo (`fr_watchdog.py`) corrigidas (logam em vez de engolir);
as 8 restantes estão em geradores históricos v1–v8 (`gera_pcb_v1..7.py`, `rota_v8.py`),
mantidos **intocados por design** como registro histórico (a v9+ é a linhagem viva).

### 9.6 — Estado do re-roteamento com keepouts

DSN novo (3.167 keepouts) aberto **sem nenhum warning** (sem risco de modal); autorroteamento
em execução. As 2 nets que a roteagem antiga deixou para trás (**IMU_CS, IMU_INT**) são o
termômetro: se completarem, a cobertura vai a 151/151.

### 9.7 — Auditoria dos scripts `ses_import.py` e `orcamento.py` (2026-10-12)  `[CORRIGIDO]`

**ses_import.py** (auditado ANTES do re-import da placa completa):
1. `via_diameter()` usava regex + heurística de min/max: com o padstack VIA1 real do SES
   (`(shape (circle F.Cu 600 0 0))` por camada) o delta max−min dava **0** e o código caía
   no default **por coincidência** (600 é o valor do projeto). Se a via mudasse de tamanho,
   o importador gravaria vias erradas em silêncio. Agora lê o diâmetro da árvore
   s-expression já parseada (`library_out → padstack VIA1 → shape → circle`).
   Prova: import de teste grava via 0,600/0,300 mm ✓.
2. **Sem guarda contra re-import**: o importador ADICIONA trilhas ao board de entrada —
   rodando com um `pcb_in` já roteado, duplicava cada trilha (curto garantido no fill).
   Agora aborta (exit 2) se a entrada tiver trilha de sinal: prova no v10_roteada
   ("ERRO: a entrada já tem 3909 trilha(s)"). A contagem oficial do import de teste:
   3.909 trilhas + 853 vias (449 stitch + 404 de rota), 0 nets sem match.

**orcamento.py**:
3. O `ORCAMENTO.md` gerado ainda descrevia a **placa v6** (220×160 mm, "367 nets não
   roteadas", "cotar com Gerber v6", joints=800 para 889 pads). A v10 mede 190×145 mm
   (275,8 cm², gate G7) com 1093 pads e roteamento G1–G8. Textos e `JOINTS` (800→1000)
   corrigidos; montagem PCBA recalculada: US$ 40,86 → **US$ 41,20** (R$ 211).
4. `esc()` era código morto (definido, nunca chamado) — removido.
5. §3.1 fechado: `BOM_FABRICACAO_atualizada.csv` (4 linhas, truncada) **removida**;
   `BOM_FABRICACAO_v10.csv` é a fonte única.

Gráfico `custo_por_bloco.png`: a regeneração falhou SÓ no ambiente desta auditoria
(matplotlib sem libs de fonte no namespace); no host o script renderiza normalmente
(arquivo commitado intacto). Não é defeito do script.

### 8.2 — CRÍTICOS que exigem decisão humana  `[ABERTO]`

1. **Margem do MOSFET vencedor**: 25,2 V + spike 60 V = **85,2 V > 80 V** pelo critério interno
   (o mesmo que reprovou o FET de 60 V); o "folga de 33%" do `verifica_limites_v7` somava errado.
   Opções: aceitar o risco / snubber+layout / FET ≥ 100 V. A BOM v10 compra o vencedor com a
   pendência registrada na linha.
2. **D-07 (watchdog) e D-12 (2× ADS7953) decididos mas ausentes do board** (E-8): a v10 mantém
   4× MCP3208 e não tem CI supervisor — implementar na v11 ou reabrir a decisão.
3. Firmware: 6 erros críticos concretos (API ESP-IDF, PWM ~1 Hz, LEDC duplicado, MCP3208, init
   nunca chamado, RF-07 falsa) — correção em andamento na auditoria; **validar com idf.py build**.

### 8.3 — Fase 0/2 (39 erros) e documentação (16)  `[CORREÇÃO EM ANDAMENTO]`

Fase 0: perdas de FET 16× erradas, comutação I², IPC-2221 interno nunca aplicado, divisor BEMF
3,07 V (o certo é 2,74 V), Ciss 1000× errado no v6, L×C trocados no loop de gate (veredito L7
invertido), E_oss sem o ½. Fase 2: buck5 simulado com 12 V (não VBAT), gate_drive.cir valida a
premissa P-06 já invalidada, netlists editados pós-log, "sem erros registrados" (§7) refutado.
Docs: PLANO_FINAL obsoleto em ≥10 pontos, fase 4 descreve a placa v6, `[EST]` citado como
`[MEDIDO]`, links quebrados. Ver relatório §B/C/E.

### 8.4 — Refutações deste registro  `[REFUTADO]`

- **§1.g "CORRIGIDO"**: falso para 26 das 28 nets excluídas do DSN (item 3 acima).
- **§3.3 "36/43 com preço"**: real 34/43 (2 linhas malformadas contavam fabricante como preço).
- **§7 "Fase 2: sem erros registrados"**: refutado (12 erros, ver §C do relatório).

### 8.5 — Gates novos obrigatórios (implementados em `verifica_fase3_v10.py`)

G1 pads dentro do contorno · G2 zero nets de 1 pad · G3 zero curtos pad×pad (SAT) ·
G4 vias fora de keepout · G5 zonas preenchidas · G6 A4 (critério equivalente documentado) ·
G7 ocupação **elétrica** (sem texto de silk). A v9 passava nos gates antigos sendo infabricável
— estes teriam pegado tudo.
