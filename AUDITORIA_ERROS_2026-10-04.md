# AUDITORIA INDEPENDENTE DE ERROS — Projeto Drone 4×ESC + ESP32-S3

**Data:** 2026-10-04 · **Auditor:** agente externo ao projeto (não é o agente `eletronica`)
**Escopo:** repositório completo (`/root/extensão/drone/`, cópia idêntica de `/opt/jupyter/work/drone/` — 1.223 arquivos, 99 MB, HEAD `b48cac4`)
**Método:** análise estática (sem python/git neste ambiente — contas verificadas manualmente e com `node`), forense dos artefatos (DSN/SES/logs/Gerbers/.kicad_pcb), leitura do código-fonte do FreeRouting 1.9.0 (`/opt/fr-src`), verificação cruzada de números entre documentos e logs, e verificação das alegações de "CORRIGIDO" do `ERROS_CONHECIDOS.md`.

> Convenção de status: **NOVO** = não consta no `ERROS_CONHECIDOS.md` · **JÁ-REGISTRADO** = consta (confirmação) · **REFUTADO** = o registro afirma algo que a evidência contradiz.

---

## SUMÁRIO EXECUTIVO

Foram encontrados **~110 erros**, dos quais **9 são bloqueadores críticos**:

| # | Erro crítico | Onde |
|---|---|---|
| C1 | **27 footprints (199–201 pads, ~18%) FORA do contorno da placa v9** — 14 MOSFETs, o módulo ESP32-S3 inteiro (41/41 pads), USB-C, shunt, bulk cap. **14 curtos reais pad×pad** decorrem disso. Os Gerbers já contêm esse cobre fora do contorno. O mesmo bug existe na v8. | Fase 3 / `gera_pcb_v9.py` |
| C2 | **Typo de nome de net desconecta o BEMF do ADC**: o divisor existe (`Rb1M/Rb2M/CbeM`), mas a net do nó chama-se `RBM###` no gerador do motor e `RB_M###` no gerador do ADC — duas nets, o ADC órfão. + ferrite `3V3_A_F` órfão e IMU/barômetro na 3V3 sem filtro. | `gera_pcb_v7.py` (ver errata na seção C2) |
| C3 | **O MOSFET vencedor (80 V) está fora de especificação pelo critério interno do projeto**: pior caso 25,2 V + spike 60 V = 85,2 V > 80 V (margem −6%). O mesmo critério reprovou o candidato de 60 V. | `verifica_limites_v7.py`, `MOSFET_BAIXO_QG.md` |
| C4 | **A BOM "válida" manda comprar o MOSFET errado** (`IPB017N10N5` TO-263-7) enquanto a placa v9 usa `NVMFS6H824NT1G` SOIC-8 — compra garantidamente errada. | `orcamento/BOM_FABRICACAO.csv` |
| C5 | **Bug 1.h (SES com 0 wires): causa raiz PROVADA no `dsn_export.py`** — (a) **todo pad vira círculo Ø=max(w,h)** por um `0 == False` (linha 97): pads SOIC-8 Ø1,95 mm em pitch 1,27 mm se sobrepõem entre nets diferentes → componente vira blob selado, o maze router falha instantaneamente em toda conexão; (b) **o via padstack nunca é declarado** (falta `(via VIA1)` na structure) → board sem NENHUMA via (prova: `library_out` vazio nos SES); (c) rotação dupla dos pinos; (d) pinos duplicados por instância (~39.000 pinos vs 1.093 reais). | `fase3_pcb/freerouting/dsn_export.py` |
| C6 | **As nets de potência não têm cobre NENHUM**: o registro 1.g ("CORRIGIDO", "cobre vem de zonas no KiCad") é **falso para 26 das 28 nets excluídas** — não existe zona nem trilha para VBAT, VBAT_F e as 24 fases PHM/SNM. O caminho de 30 A (J1→F1→Q1) não existe no cobre. | `ERROS_CONHECIDOS.md` §1.g — **REFUTADO** |
| C7 | **57 das 102 zonas de cobre estão vazias** (zero `filled_polygon`): todos os pours de 12V/5V/3V3/3V3_A em B.Cu + 20 de VBAT_PROT — ilhas sem conexão removidas pelo KiCad. "Cobre em F e B" das rails não existe. | `v9_drone.kicad_pcb` |
| C8 | **Firmware esqueleto com 6 erros críticos concretos**: API ESP-IDF inventada nos 4 módulos (não compila), PWM de ~1 Hz (fator 20.000×), canal LEDC duplicado (motor 3 sem PWM), protocolo MCP3208 triplo-errado (só lê CH0/CH4), `app_main` nunca chama os init, e a premissa RF-07 é falsa (o mapa pad→GPIO sempre foi derivável — a Fase 0 §8 está correta). | `firmware/main/` |

Além disso: a cadeia de "correções" v5/v6/v7 da Fase 0 contém **3 vereditos de limite invertidos** (achados 15/16/18 da seção Fase 0), a Fase 2 valida uma topologia de buck5 diferente da especificada, `PLANO_FINAL.md` — o "documento único de execução" — está obsoleto em ≥10 afirmações de estado, e **8 vias GND atravessam o keepout de borda** por off-by-one no gerador.

---

## A. ERROS CRÍTICOS (detalhe e evidência)

### C1. [CRÍTICO] 27 footprints / 199 pads FORA do contorno 190×145 mm da v9 — NOVO

**Medição direta no `v9_drone.kicad_pcb`** (contorno = `gr_poly` (0,0)→(190,0)→(190,145)→(0,145), rotação dos módulos aplicada):

- **14 SOIC-8 100% fora**: `QM101H…QM301L` (13 MOSFETs + `QM301H`) em y = −3,16 mm — a fileira inteira de potência dos motores 1–3 fica **acima da borda superior** (corpos em y ∈ [−5,6; −0,7] mm); e `UaM403` (amp-op) em (−3,2; 87,7).
- **U_MCU (ESP32-S3-WROOM-1) 41/41 pads fora**: `(at -13.25 42.384763)` — centro 13,25 mm à esquerda da borda; módulo 18×25,5 mm inteiramente fora.
- **J2 (USB-C) 18/20 pads fora** `(at -1.5575 72.1048)`;
- **10 passivos fora** na borda esquerda: `Cblk6` (capacitor bulk!), `RsM402` (shunt de corrente!), `Rb1M403`, `RgoM303`, `RsdM302`, `Rd2M203`, `CaM203`, `CvM203`, `CoB2a`, `RSDA`.
- Total: **199–201 dos 1.093 pads (~18%)** fora do contorno (contagem com rotação aplicada; variação conforme critério de contorno do pad).

**Os Gerbers fabricáveis carregam o defeito**: `v9/gerbers/v9_drone-F_Cu.gtl` tem 447 linhas com coordenada X negativa (até −12,07 mm — o U_MCU) — um CAM rejeitaria ou cliparia os pads. **O mesmo bug já existe na v8** (28 módulos / 184 pads medidos) e nunca foi registrado. Consequência elétrica imediata: **14 curtos reais pad×pad entre nets diferentes** (ver seção D) e o keepout esquerdo invadido por 21 pads do U_MCU. A "ocupação 60,05%" e a "altura usada 129,35 mm" da `NOTA_V9.md` são fictícias (bboxes infladas por texto + componentes fora da placa).

**Causa raiz (2 bugs no empacotador `gera_pcb_v9.py`):**
1. **Erro de sinal** em `empacota()` (linha ~252): `placed[ref] = (LIVRE_EDGE + x - dx, LIVRE_EDGE + y - dy)`. Como `fp_box_at` retorna `dx = -l`, a bbox-esquerda-topo do footprint cai em `LIVRE_EDGE + x − 2·dx` (deveria ser `+ dx`). Todo footprint cuja origem não coincide com o canto da bbox é empurrado para cima-esquerda do previsto.
2. **`GetBoundingBox()` inclui os textos de silkscreen/fab** (reference em (0,−3,4), value "NVMFS6H824NT1G" ~13 mm de largura): o SOIC-8 é medido como ~13,6×8,3 mm em vez dos 5,2×6,2 mm dos pads. Prova exata: `y' = 1 + 0 − dy` com `dy = 4,157` (texto ref em −3,4 + fonte 1 mm) = **−3,157 mm** — bate com o `(at 8.263095 -3.157499)` do arquivo ao centésimo; o espaçamento observado entre MOSFETs (14,08 mm) = largura do texto do value (13,63) + GAP (0,45).

**Consequências adicionais:** a "ocupação 60,05%" e a "soma dos bounding boxes 16 562,9 mm²" são infladas pelos textos; a real (pads) é menor. Nenhum gate da `verifica_fase3_v9.py` checa se footprint está dentro do contorno — os gates A-OK passaram numa placa impossível. Também afeta o roteamento: no DSN, o boundary é `(rect pcb 0.9 0.9 189.1 144.1)` — todos esses pinos ficam fora da área roteável (contribui para o C5).

### C2. [CRÍTICO] Netlist v7/v8/v9: o ADC nunca enxerga o divisor BEMF (typo de nome de net) + ferrite órfão — NOVO

> **ERRATA (2026-10-04, pós-forense):** a primeira versão deste achado dizia que "o divisor BEMF não existe e os Rd1/Rd2 foram desviados". A investigação durante a correção mostrou uma causa raiz mais precisa: **os divisores BEMF existem** (`Rb1M###` fase→nó, `Rb2M###` nó→GND, `CbeM###` filtro 1 nF, todos presentes desde a v7) e os `Rd1/Rd2M###` são **legitimamente o divisor de referência 10k/10k do INA240** (item separado da lista de componentes: "CORRENTE;Divisor de referência;10k/10k 1% + 100 nF; 12"). O defeito real é um **typo de nome de net**: a seção do motor do gerador criou a net do nó como `"RB%s" % t` (= **`RBM101`**, sem underscore) enquanto a seção do ADC referenciou **`"RB_M%d01"`** (com underscore) — duas nets distintas no board: a `RB_M###` ficou órfã com 1 pad (só o pino do ADC) e a `RBM###` ficou sem consumidor. Consequência funcional idêntica à descrita (o ADC BEMF não lê nada), mas a correção é cirúrgica. O 3V3_A_F órfão confirma-se exatamente como relatado.

**Correção aplicada (2026-10-04):** `gera_pcb_v7.py` padronizou `"RB_%s" % t` (as 12 nets `RB_M###` agora têm 4 pads: Rb1M###.2, Rb2M###.1, CbeM###.1 + pino do ADC) e a saída do ferrite virou `3V3_IMU` (FLDO.2 + U_IMU VDD/VDDIO + U_BARO VDD/VDDIO/CSB + CIMU.1), com IMU/barômetro fora da 3V3 digital. A v10 regenerada tem **zero nets de 1 pad** (gate G2 novo).

### C3. [CRÍTICO] MOSFET vencedor 80 V fora de especificação pelo critério do próprio projeto — NOVO

`verifica_limites_v7.py:109-111` (saída l.13) e `MOSFET_BAIXO_QG.md` §4 (l.120): "barramento 25,2 V + spike medido 60 V = 60 V contra V(BR)DSS de 80 V → folga de 33%". **A soma está errada**: o spike (L·di/dt) soma ao barramento → pior caso **25,2 + 60 = 85,2 V > 80 V** (margem −6%). O mesmo critério havia reprovado o `NVMFS5C628NT1G` de 60 V por "zero margem". Agravante: o spike é `[CALC]` da Fase 0 (§4.4) rotulado de "medido" — violação da política de honestidade.

### C4. [CRÍTICO] BOM de fabricação manda comprar o MOSFET errado — NOVO (agrava §3.1 do registro)

`orcamento/BOM_FABRICACAO.csv:9` = `IPB017N10N5`, **TO-263-7**, US$ 5,2721, "D-11 adotou Qg 168/210 nC" — linha de referência nunca editada (admitido em `BOM_FABRICACAO_mosfet.csv:7`). A placa v9 tem **24× `NVMFS6H824NT1G`** em pegada `SOIC-8` (`NOTA_V9.md:46,52`). `ERROS_CONHECIDOS.md:56` diz que essa BOM é "a fonte válida" → comprar por ela entrega 24 peças que **não cabem na pegada** da placa. Regenerar a BOM a partir da placa antes de qualquer compra.

### C5. [CRÍTICO] Bug 1.h (SES com 0 wires): causa raiz PROVADA no `dsn_export.py` — NOVO

Forense completa com os artefatos reais (`run/`, `teste/`), o fonte do FreeRouting 1.9.0 (`/opt/fr-src`) e verificação independente dupla. **O bug 1.h não é mistério do roteador — é o DSN que o exportador gera:**

**P1 — Todo pad SMD vira CÍRCULO de Ø=max(w,h) (`0 == False`).** `dsn_export.py:97`: `if is_tht or pcbnew.PAD_SHAPE_CIRCLE == shape_enum:` — mas `shape_enum` recebe `shape_is_circle(pad)`, um **bool**. No KiCad 5.1, `PAD_SHAPE_CIRCLE = 0`, e em Python `0 == False` → True → **todo pad não-circular entra no ramo círculo**; o ramo `(rect …)` é inalcançável. Prova nos artefatos: os 40 padstacks do DSN completo e todos do corte são `(circle …)` (a única ocorrência de `(rect` no arquivo é o boundary). **Efeito fatal**: pad SOIC-8 de 0,6×1,95 mm vira círculo Ø1,95 mm com pitch 1,27 mm → círculos de **nets diferentes se sobrepõem** (pior folga −1,14 mm; corredor necessário 0,65 mm) → cada CI fine-pitch vira um blob selado; o maze router falha instantaneamente em toda conexão com endpoint SOIC-8/SOT-23 — **as 9 nets do corte têm todas endpoint SOIC-8**.

**P2 — O via padstack nunca é declarado: falta `(via VIA1)` na `(structure)`.** O FR só registra vias do escopo `(via …)` (`Structure.java:866-868`); como `via_padstack_names` fica null, o board fica **sem nenhuma via** → impossível mudar de camada. **Prova empírica**: `(library_out)` vazio nos dois SES (ele lista os via padstacks do board).

**P3 — Rotação dupla dos pinos.** Os offsets são gravados já rotacionados por instância (`ppos` absoluto − centro) e o `(place … rot)` declara a rotação — que o FreeRouting **reaplica** (`Pin.relative_location()`). 51/105 pads do corte caem em posição errada (até 4,4 mm); nets reais em pontos fantasma. (Correto: offsets locais do footprint; o FR aplica a rotação — padrão KiCad.)

**P4 — Pinos duplicados por instância.** `images[pkg]` é criado 1× mas os pads de **todos** os módulos são anexados (linha 181): imagem SOIC-8 com 96 entradas (corte) / 384 (board completo) → projeção de **~39.000 pinos** no board completo (vs 1.093 reais) — nuvens de pinos-fantasma com nets reais.

**P5 — Pads THT com shape em uma só camada** (`pl = lname[0] if front else lname[-1]`) → J1/J_M*/J2/SW só existem em F.Cu para o roteador.

**Mecanismo do "completed in 0,82 s" (P6):** o pass 1 não insere nada → hash do board inalterado → guard `already_checked_board_hashes` → break após o 1º pass; `BatchAutorouterThread.java:96-99` loga "Auto-routing was completed in Xs" **incondicional**. Os logs mostram exatamente 1 save de `.frb` por rodada (um pass com pendências geraria pass 2). O SES vazio é sintoma: `write_net` itera `get_connectable_items` (nenhuma trilha) e `write_library` itera os via padstacks (nenhum).

**Linha do tempo (por que o registro confundiu):**
- Runs de 03/10 01:15 e 01:35 BRT (placa completa, **DSN antigo**): ainda com 46× "padstack not an area" e warning "old KiCad"; 34,91 s → `v9_final.ses` com 0 wires. **Esses artefatos são da DSN antiga e não descrevem o pipeline atual.**
- DSN "corrigido" (ordem do círculo) regenerado 02:06–02:07; 3 runs do corte às 02:08/02:20 (travaram na otimização com threshold 0,0 = bug 1.c) e 02:29 (com 0,05 completou) — **zero warnings, mas SES com 0 wires**: a correção 1.b estava certa (a ordem `(circle layer diam x y)` é a correta, confirmada em `Circle.java:14-16`), porém os bugs P1–P5 continuam presentes.
- `run/freerouting.json` (cópia dos runs) ainda com `optimization_improvement_threshold: 0.0` e 4 threads — o fix não chegou ao `/tmp` (armadilha 1.i repetida). E `max_passes` do json **nem é lido** pelo FR 1.9.0 (é opção CLI `-mp`).

**Fix mínimo:** `if is_tht or shape_is_circle(pad):` + `(rect …)` para os demais (P1); acrescentar `(via VIA1)` na structure (P2); offsets locais (P3); pins 1× por pkg (P4); shape THT em todas as camadas (P5). Depois re-rodar o corte — e se ainda sair 0 wires, o próximo suspeito é o net-attach silencioso em `Network.insert_component` (`get_nets` vazio **não gera warning**); teste discriminante: screenshot do ratsnest no Xvfb.

### C6. [CRÍTICO] As nets de potência não têm cobre nenhum — REFUTA o "CORRIGIDO" 1.g do registro

O `ERROS_CONHECIDOS.md` §1.g (status CORRIGIDO) exclui 28 nets do DSN com a justificativa "cobre vem de zonas no KiCad". **Verificação no `v9_drone.kicad_pcb`: zonas existem apenas para GND (3), VBAT_PROT (31), 12V (16), 5V (16), 3V3 (26) e 3V3_A (10)** — e tracks = 0. Ou seja: **não existe zona nem trilha para VBAT, VBAT_F e as 24 nets de fase PHM\*/SNM\*** — exatamente as nets de 15 A RMS / 30 A de pico. O caminho de potência J1 (XT60) → F1 → MOSFETs e as ligações fonte→shunt **não têm condutor algum previsto em nenhuma camada**. A justificativa vale só para GND e VBAT_PROT: a alegação 1.g é **falsa para 26 das 28 nets**.

### C7. [CRÍTICO] 57 das 102 zonas de cobre estão vazias (zero `filled_polygon`) — NOVO

Todos os pours de 12V (8), 5V (8), 3V3 (13) e 3V3_A (5) em B.Cu, mais 10 de VBAT_PROT em B.Cu e 10 em F.Cu, e 3 de 5V em F.Cu não têm preenchimento — o KiCad remove ilhas desconectadas (pads SMD só em F.Cu → pour em B.Cu fica ilha sem âncora; e os pads VBAT_PROT dos drains estão fora do contorno por C1). O arquivo tem só 45 fragmentos preenchidos (bate com `verificacao_v9.txt:8`). O "cobre em F e B" das rails **não existe**; as contagens de zonas da verificação (102) contam zonas mortas.

### Observação sobre o watchdog (JÁ-REGISTRADO como mitigação, com ressalva)

`fr_watchdog.py` aperta Return a cada ~2 s em **qualquer** janela com foco que não seja o board (inclusive janelas sem nome — `''`, `FocusProxy`), até 500×. Nos logs ele disparou 185+ vezes por run. Além de dispensar o diálogo de auto-start antes do timeout, pressionar Return às cegas em janelas sem título pode confirmar botões arbitrários. Recomenda-se restringir a janelas identificáveis como `JOptionPane` (título contendo "Freerouting"/"DSN file reader").

---

## B. FASE 0 — 27 erros (subauditoria dedicada; todos NOVOS exceto onde indicado)

Resumo consolidado (evidência completa nas referências citadas):

**Cálculos elétricos/térmicos:**
1. **[MÉDIO]** Perdas de FET no cruzeiro **16× erradas**: `verifica_limites_entrada_v4.py:86` usa `i_bus` total do drone (7,5 A) como pico de fase por motor; correto pico/fase = (7,5/4)/0,6 = 3,125 A → condução total 0,117 W, não 1,88 W. Repetido em FASE0 §7, v6 e v7.
2. **[MÉDIO]** Perda de comutação escala com I² em vez de I (`psw = 0.133*(ipk/30)**2`); e `dimensionamento_fase0.py:59` divide Esw por 2 duas vezes → 133 mW/FET a 30 A em vez de ~266 mW.
3. **[MÉDIO]** Divisor BEMF "3,07 V" errado (correto 2,74 V = 25,2×1,0/9,2) — a própria Fase 2 (`bemf_div.cir/log`) mede 2,739 V. (Confirmado independentemente pela subauditoria de docs: `lista_componentes_fase0.csv:20` e `gera_esq4.py:117` erram contra `calcs_fase4.txt:15` e `PLANO_TESTE_BANCADA.md:278`.)
4. **[MÉDIO]** Tempos de ar WiFi no MD 4× maiores que os logs citados (1792 µs vs 448 µs @1 Mbps — bug de unidade bits/bytes no PLCP).
5. **[MÉDIO]** "I·t/C superestima ~3 ordens de grandeza" — fator real ~3×.
6. **[MÉDIO]** **IPC-2221 com constante de camada externa, mas a decisão é barramento em camada INTERNA**: 30 A internos @ ΔT 10 °C exigem ~42 mm, não 16,37 mm publicados (2,56× otimista).
7–13. [BAIXO] (7) "L(30%)" com ripple real 17,7–23,6%; (8) banco de caps contraditório MD (6×) vs log (4×470 µF) vs CSV (6/12/48); (9) CSV l.34 "22 uH" vs l.30 "L=89 uH"; (10) log "folga 3x" onde é 12×; (11) "13,44 W de entrada" = grandeza sem sentido (corrente de entrada × tensão de saída; correto ≈19,1 W); (12) ADC externo de 16 canais para 24 sinais sem mux no BOM; (13) `dimensionamento_fase0.json` superado sem marcador.

**Erros DENTRO das "correções" v5/v6/v7 (invertem vereditos de limite):**
14. **[MÉDIO]** "173→182 W, folga 9,2% [MEDIDO]" — incremento 12× exagerado (i12_max já é o total; correto ≈173,3 W / 4,0%).
15. **[MÉDIO]** v6 usa **Ciss = 12 pF em vez de 12 nF** (1000×) → t_on L1 otimista (a v5 havia calculado certo: 1,71×).
16. **[MÉDIO]** v6/v7 **trocaram L×C do loop de gate** (20 nF/2 nH vs 2 nF/20 nH do v4) → Z0 10× menor e o "L7 ✅" é artefato; com os valores corretos a incompatibilidade amortecimento×velocidade continua.
17. **[MÉDIO]** v6 imprime "o Cboot de 1 µF original serve" testando o Cboot novo (4,7 µF).
18. **[MÉDIO]** Bootstrap: "35,7 mV com 2,2 µF" não fecha (76,4 mV); o Cboot do BOM (1× 2,2 µF por half-bridge) **viola a regra 20·Qg da própria v5** (3,36 µF) e o limite L2 de 40 mV.
19. **[MÉDIO]** "E_oss = Qoss × Vds" sem o ½ → 107,4 mW/FET deveria ser 53,7 mW (a "contraprova de datasheet" que refutou o modelo da v5 tem erro de fator 2).
20. **[CRÍTICO — ver C3]** Margem de tensão do MOSFET vencedor: 25,2+60 = 85,2 V > 80 V.
21–27. [BAIXO] (21) "42 µF" deveria ser 3,5 µF (faltou ×12 V); (22) "124%" invertido (é 81%); (23) fórmula dimensionalmente quebrada no v7; (24) parágrafo final duplicado no v7; (25) "cai 18% (196→196 mm²)" auto-contraditório (real: 229→196 = −14,5%); (26) "121,1 mA" sem fonte em nenhum log; (27) "3,36 µC" (µF) e alvos 25 ns vs 50 ns sem reconciliação.

---

## C. FASE 2 (SPICE + Verilog) — 12 erros (refuta o §7 do ERROS_CONHECIDOS)

O §7 diz "Fase 2: sem erros registrados". A rastreabilidade dos 35 resultados é verdadeira (todos os "medido" batem com os logs), mas **"sem erros" é falso**:

28. **[MÉDIO]** `buck5.cir` simulado com **entrada de 12 V** — topologia diferente da especificada (buck5 alimentado da VBAT 19,8–25,2 V, D 0,198–0,253 na Fase 0); no projeto real dIL = 0,44 A, não 0,343 A; em cascata, a entrada do buck5 (~0,93 A) estouraria o buck12 de 0,6 A. O relatório não registra o desvio.
29. **[MÉDIO]** `gate_drive.cir` valida a premissa P-06 **já invalidada** (Qg 40 nC / Cboot 1 µF) e nunca foi re-executado após a reversão para 168 nC / 3,36 µF — segue como "evidência verificada" no `RESULTADOS_FASE2_SPICE.md`.
30–35. [BAIXO] (30) intermediário errado no comentário [E2] do `bemf_div.cir` (178583,6 vs 178.564,1 Hz); (31) −18,38179 dB vs −18,38073; (32) precisão declarada abaixo da resolução de impressão do ngspice ("0,4 µV", "4e-5 %", negritos de 1e-6%); (33) "1/(2,8125×17,8) = 20,02 mΩ" (dá 19,98; CSV usa 19,975); (34) **os 3 netlists buck foram editados DEPOIS das simulações** (tamanhos da tabela §6 não batem com os arquivos; mtime 22:58 vs logs 00:41) sem re-run nem nota — cadeia de evidência quebrada (parâmetros atuais ainda reproduzem os valores: edição cosmética); (35) "erro ~0,5 V" na janela de 200 µs sem artefato (logs mostram ≤0,16 V p-p).
36. **[MÉDIO]** `RELATORIO_VERILOG.md` §3 cita como "saída do parser" uma linha que **nenhum artefato produz** ("n eventos hi_o[0]: 6" não existe no `plot_pwm.py` nem no `tb_pwm.log`) — viola a regra declarada no próprio §0 do relatório.
37–39. [BAIXO] (37) "24 half-bridges" — são 12 (24 MOSFETs); (38) "2,5 µs de low-side" no DUTY_MAX — real 2,0 µs (recarga de bootstrap superestimada 25%); (39) o estresse inclui `deadtime_i = 0` (complementar na mesma borda) — o "0 violações" não é segurança física com dt=0.

---

## D. FASE 3 / PCB v9 — demais erros novos (além de C1/C5/C6/C7)

- **[CRÍTICO] 14 curtos reais pad×pad (nets diferentes, F.Cu, teste SAT com rotação)** — consequência direta do bug de posicionamento C1: U9.6/U9.5/U9.2/U9.1 (ADC) × Chf4.2/Chf3.2 (GND); U8.4/U8.3/U8.2 × Chf1.2; J1.1 (VBAT) × RgfM301.1/.2 e J1.2 (GND) × RgfM302.1/.2 (XT60 6×6 sobre os resistores de gate); J_M4.2 (PHM402) × RsdM201.1/.2; J_M3.2 (PHM302) × RsdM101.1. Mais **16 pares com folga < 0,2 mm**. — NOVO
- **[MÉDIO] 8 vias de stitch GND violam o próprio keepout da borda esquerda** (x = 0,819–0,996 mm dentro da faixa [0…0,9] que declara `vias not_allowed`); 21 pads do U_MCU dentro do mesmo keepout. Causa: `acha_via` usa limite 0,8 em vez de 0,9 + folga (`gera_pcb_v9.py:377`). — NOVO
- **[MÉDIO] Keepouts assimétricos**: faltam a faixa da borda superior (y ∈ [0…0,9]) — só existem esquerda/direita/inferior (`gera_pcb_v9.py:428-430`). — NOVO
- **[MÉDIO] In2.Cu a 0,5 oz assimétrico** (In1/In3/In4 = 1 oz) sem justificativa no stackup; e o "ADOTADO: 40 vias por transição" do `calc_trilhas_vias.py` **não existe no board** (~4 vias VBAT_PROT por meio-ponte) — com 1 A/via e 15 A RMS por fase, faltam vias de transferência mesmo após criar o cobre (C6). — NOVO
- **[MÉDIO] Evidências misturadas no runbook**: `run/v9_final.ses` e `run/freerouting_run2.log` são da **DSN antiga** (46× "not an area", warning "old KiCad", 20 min de modal travado) e não descrevem o pipeline atual; a única rodada E2E com o exportador novo é `teste/corte_v9.*` (02:08 e 02:19 travaram na otimização com threshold 0,0 — bug 1.c — e 02:29 com 0,05 completou e gravou SES vazio). — NOVO
- **[BAIXO]** `max_passes` do `freerouting.json` não é lido pelo FR 1.9.0 (é opção CLI `-mp`); `ses_import.py:151` tem linha morta/broken (`re.search(…, "")`) e via default 0,8/0,4 vs 0,6/0,3 do board; o corte de teste contém `UaM403` fora do boundary. — NOVO
- **[OK verificado]** `calc_trilhas_vias.py` está **correto** (IPC-2221: 15 A→6,29 mm; 30 A→16,37 mm @ΔT10 externo 2 oz; via 0,3/0,6→1,0 A ✓); stackup soma 1,6000 mm ✓; In1=GND / In4=VBAT_PROT ✓; 0 vias sobre pads de outra net ✓; 0 curtos entre cobres preenchidos ✓; 0 mismatch netNum/netName; 0 refs duplicados; D-13 (SDM1xx→SD_MCU) confirmado; pads só-pasta do Q1 são divisões de pasta do DPAK — normais. A ordem `(circle layer diam x y)` do fix 1.b está **correta** (confirmada em `Circle.java:14-16`).
- Verificações das correções alegadas do registro (1.b/1.c/1.e/1.f/1.d): **existem no código atual** (linha 99 do dsn_export, host_cad, regra width/clear, `type power`, `SES_TO_MM=1000`, threshold 0,05 no json da raiz, outline bbox, Gerbers `v9_drone-*`) — mas **não resolvem o 1.h** (C5) e a cópia de configuração do run ficou defasada; **1.g é falsa para 26 das 28 nets** (C6).

---

## E. DOCUMENTAÇÃO / ORÇAMENTO / PLANO — 16 erros (subauditoria dedicada)

1. **[CRÍTICO — ver C4]** BOM "válida" com MOSFET errado.
2. **[MÉDIO]** `BOM_FABRICACAO.csv` com colunas deslocadas nas linhas 13–14 (falta 1 separador; "YAGEO"/"Samsung" contados como preço) e o **§3.3 do ERROS_CONHECIDOS repassa o artefato**: real é 34/43 com preço numérico, 9 sem — não "36/43 (7 sem)". — REFUTADO
3. **[MÉDIO]** Divisor BEMF 3,07 V vs 2,74 V (mesmo achado 3/B).
4. **[MÉDIO]** `PLANO_FINAL.md` ("documento único de execução") obsoleto em **≥10 afirmações de estado** (nets 138/202 vs 189/191; "309/309 pads sem via" vs 34/249; "não existe firmware" vs 13 arquivos; "v8 vazio/gera_pcb_v8 AUSENTE" vs existentes; dimensões 220×160 vs 190×145; "0/43 disponibilidade" vs 34 com preço; "A8=0" vs 3; etc.).
5. **[MÉDIO]** README: "8 figuras" na Fase 1 — são **9** (a própria tabela lista 9; ERROS_CONHECIDOS diz 9).
6. **[MÉDIO]** Documentos de entrega da Fase 4 descrevem a **placa v6** (238 footprints, 220×160, 4 camadas, TO-252) — o critério de aceite "238 footprints montados" daria **PASS com 81 footprints faltando** na v9.
7. **[MÉDIO]** Decisões "pendentes do Jailton" (fusível, watchdog, failsafe) já decididas em 28/09 (`DECISOES_TOMADAS.md` D-15/D-07) — docs de fase4 não atualizados; e o watchdog real é SOT-23-6, não SOIC-8.
8. **[MÉDIO]** D-07 (watchdog) e D-12 (2× ADS7953) decididos "para a v8" mas **ausentes da v8 e v9** (boards têm 4× MCP3208 e nenhum CI supervisor) — pendência não registrada; `BOM_FABRICACAO.csv:22` com qtd "1" e nota "a quantidade real e 2".
9. **[BAIXO]** `PLANO_FINAL.md:76`: "ADC1 tem 20 canais" — 20 é o total dos 2 ADCs (ADC1 ≈ 10).
10. **[BAIXO]** `[EST]` citado como `[MEDIDO]` em `PLANO_FINAL.md:251` (fusível US$ 0,30) — violação da política de honestidade.
11. **[BAIXO]** "IMU é 10× o [EST]" — real ~4× (`COTACAO_REAL.md:73`).
12. **[BAIXO]** `GATES_REVISADOS.md:38` cita 189 nets não roteadas como evidência da v8 — o número da v8 é 173 (189 é da v9).
13. **[BAIXO]** `DO_PROJETO §5.7` acusa PLANO_FINAL de "14 decisões" — já corrigido (diz 15).
14. **[BAIXO]** README estrutura desatualizada: "v1…v7" (existem v8/v9), "4 camadas" (v9 = 6), árvore omite `firmware/`, `ERROS_CONHECIDOS.md`, `PLANO_FINAL.md`, `logs/`; orçamento não menciona BOM/COTACAO_REAL.
15. **[BAIXO]** "os 4 documentos de fase4" vs 6 .md existentes / "8 documentos" no registro — contagens 4/5/6/8 divergem; FIRMWARE_BUILD.md fica fora dos gates F14/A19.
16. **[BAIXO]** ERROS_CONHECIDOS §3.2 ainda descreve o bloqueio de cotação ("exige sessão do Jailton") que o §3.3 e o `COTACAO_REAL.md` já derrubaram — internamente inconsistente.

**Links quebrados:** `ERROS_CONHECIDOS.md:89` → `firmware/FIRMWARE_BUILD.md` (não existe; real: `fase4_entrega/FIRMWARE_BUILD.md`); `NOTA_ROTAS_v8.md:32` → `STACKUP_PROPOSO.md` (typo); `PLANO_FINAL.md:330,378` → `prd.json` (inexistente); `ESCOLHA_MOSFET_DRIVER.md:245` → `firmware/m2_pwm_mcpwm.c` (real: `firmware/main/...`); `PLANO_TESTE_BANCADA.md:62` → "passo 16" (é §18; registrado no DO_PROJETO mas ausente do ERROS_CONHECIDOS).

**Cross-check global (10 números-chave):** consistente ✅ — 30 A/15 A por motor; 6S 25,2/22,2/19,8 V; 43 itens. Divergente ❌ — identidade do MOSFET (4 versões: lista TO-252-3 / BOM IPB017 TO-263 / placa NVMFS SOIC-8 / orçamento [EST] genérico); Qg (40/168/38 nC); BEMF (3,07/2,74 V); footprints (238/319); nets (426/202/176/191 — nenhum doc de entrega aponta a v9); custo (US$ 100,88 [EST] vs base real LCSC US$ 222,62 parciais; "INA240 31%" só no mundo [EST] — real 9,5%, topo = MOSFET 57%); ADC (1/2/4 chips).

---

## F. FIRMWARE (ESP-IDF v5.x) — 24 erros (subauditoria dedicada; verificação de cada API contra os headers reais do ESP-IDF v5.4 e protocolo MCP3208 contra DS21298)

### Críticos — NOVOS

- **F1. Os 4 módulos não compilam contra a API real do ESP-IDF v5.** `m2_pwm_mcpwm.c` inclui `driver/mcpwm_motor.h` (header **inexistente**) e usa API inventada (`mcpwm_motor_handle_t`, `mcpwm_new_motor`, `mcpwm_timer_set_compare`, `mcpwm_new_deadtime`); `mcpwm_new_operator` real tem 2 args (código passa 3), `mcpwm_new_comparator` recebe operador (código passa timer), `mcpwm_operator_config_t` não tem `gen_gpio_num`. `m1_vbat.c` inclui `driver/adc_oneshot.h` (real: `esp_adc/adc_oneshot.h`), usa `adc_oneshot_chan_handle_t` (inexistente) e assinaturas erradas de `config_channel`/`read`. `m3_pwm_ledc.c:164`: `ledc_update_duty(LEDC_LOW_SPEED_MODE)` sem o 2º argumento. Os 4 `.c` usam `ESP_RETURN_ON_ERROR` **sem incluir `esp_check.h`**. Extra: o S3 só tem **3 operadores MCPWM por grupo** — o design de "6 operadores no grupo 0" estoura o recurso mesmo consertando os nomes.
- **F2. M2: PWM de ~1 Hz em vez de 20 kHz (fator 20 000×).** `resolution_hz = 4096`, `period_ticks = 4095` → ~1 Hz; o driver só emite *warning* e roda. 20 kHz com 4096 ticks exigiria 81,92 MHz (impossível com 2 divisores inteiros); correto: **80 MHz / 4000 ticks**. Efeito: duty 2–95% a 1 Hz = pulsos de 20–950 ms nas gates — quase CC nas fases.
- **F3. M3: canal LEDC duplicado — motor 3 sem PWM.** `channel = i % 3` para i=0..5 → canais 0,1,2 duas vezes; o S3 tem 8 canais (correto: `channel = i`). O motor 4 rebinda os canais do motor 3; `ledc_set_pin` não desliga o routing antigo → estado indefinido, sem duty independente por fase.
- **F4. M4: protocolo MCP3208 quebrado em 3 pontos independentes.** `command_bits = 24` (deveria ser 0 — manda 24 clocks de DIN=0 antes do frame); montagem do comando colide bits (`0x06 | ((ch&4)<<1) | (ch&3)` → canais 0/2 idênticos, 1/3 idênticos…; correto: `{0x06 | (ch>>2), (ch&3)<<6, 0x00}`); decodificação `((rx[1]<<5)|(rx[2]>>3))&0xFFF` lê os clocks errados (correto: `((rx[1]&0x0F)<<8)|rx[2]`); e `SPI_DEVICE_HALFDUPLEX` onde o CI exige full-duplex. Resultado: só lê CH0/CH4 com escala errada.
- **F5. `app_main` nunca chama `m2_pwm_init`/`m3_pwm_init`/`m4_adc_init`.** Os `shutdown()` falham com `INVALID_STATE` (logam "falhou") e nada vai a nível seguro; a task de leitura falha silenciosamente para sempre. O único efeito real do firmware é o boot + 1 leitura de VBAT.
- **F6. A premissa RF-07 é FALSA (processo): o mapa pad→GPIO sempre foi derivável e a Fase 0 §8 está CORRETA.** A tabela de pinos do WROOM-1 está no PDF do próprio repo; traduzindo o netlist v7: motor 1=GPIO4-6, 2=GPIO7-9, 3=GPIO10-12, 4=GPIO13-15, SPI=16/17/18, VBAT=GPIO1 (ADC1_CH0)… **exatamente a §8 da Fase 0**. A "divergência" era artefato de comparar nº de pad com nº de GPIO. O "bloqueio central do bring-up" (tabela não extraída) não se sustenta; os GPIOs podem ser preenchidos em `board_pins.h` hoje.

### Médios — NOVOS

- **F7.** `shutdown()` = `set_duty(2)` (clamp de 2%, não 0%) → 1 µs alto a cada 50 µs, não "nível baixo" como o docstring exige. Estado seguro real: duty 0 + force-low.
- **F8.** O dead-time do MCPWM é **inaplicável à topologia**: cada IR2104 tem UM pino IN e gera HO/LO complementares com dead-time interno fixo (400/520/650 ns, datasheet do repo). "M2 = MCPWM por causa do dead-time programável" é erro de concepção; M2 e M3 são funcionalmente idênticos (a duplicação multiplicou bugs). A 80 MHz, `PWM_DEADTIME_TICKS=192` = 2,4 µs > teto de 2 µs.
- **F9.** `sdkconfig.defaults` sem `CONFIG_FREERTOS_HZ` → default 100 Hz → `vTaskDelay(pdMS_TO_TICKS(1))` = `vTaskDelay(0)` → yield-loop que faminta a idle da CPU0 e dispara o task watchdog a cada 5 s. Fix: `CONFIG_FREERTOS_HZ=1000`.
- **F10.** M3: a defasagem de "90°" implementada é **3,52°** (hpoint=10 de 1024 counts; a constante de 2 MHz é definida e nunca usada); e só existem 2 grupos de portadora (o critério pede 4).
- **F11.** M3: 20 kHz ± 0,1% é inalcançável com LEDC a 10 bits no S3 (~19,81 kHz, −0,94%); para 20,000 kHz exatos: 8 bits ou MCPWM.
- **F12. Hardware/firmware:** o SD de cada IR2104 está amarrado ao 3V3 via 10k **sem GPIO** — o firmware não pode desligar os gate drivers; todo failsafe depende de zerar PWM (que F7 mostra não acontecer). (Polaridade verificada no datasheet: SD baixo = shutdown; pull-up = habilitado, correto para operar, sem controle.)
- **F13.** M4: cadência real ~1 ksps agregada (~31 Hz/canal) contra os 480 ksps que o plano exige; o "disparo na janela de 2 µs" do WP4 não existe.
- **F14.** A premissa "com GPIO −1 a ESP-IDF falha alto" é falsa para M1 (ADC oneshot não recebe GPIO) e M4 (SPI aceita `spics_io_num<0` documentadamente) — o init "teria sucesso" silencioso com barramento sem pinos.

### Baixos (resumo) — NOVOS

Comentários que contradizem o código (m3 "2 bits" vs 10 bits reais; m1 "4096" vs `/4095`); callback MCPWM com 1 argumento e semântica invertida; `s_circuito/s_canal` não thread-safe; "barramento serve ao barômetro" (é I²C); `xTaskCreate` conta palavras, não bytes; `CONFIG_MCPWM_ISR_DEBUG` inexistente; fallback de VBAT ignora escala de atenuação (~6% de erro se a cali falhar); **IMU ICM-42688-P sem driver** (checklist p/ implementação verificado: WHO_AM_I reg 0x75=0x47, REG_BANK_SEL 0x76, CS=GPIO42, INT=GPIO47, barramento compartilhado com os MCP3208 sem arbitragem); o PDF rotulado "v1.6" do ICM contém "Revision: 1.2"; LED no GPIO45 (strapping VDD_SPI) e buzzer no GPIO46 (strapping de boot) sem análise de margem.

### Verificado OK

`board_pins.h` × netlist (26/26 pads ✓); consistência "12 canais PWM" (não 24 — os pares complementares vêm dos IR2104) ✓; divisor VBAT 100k/13,7k e pontos de aceite ✓; escala 0,5 mΩ × 50 V/V = 25 mV/A ✓; IR2104 dead-time interno 400/520/650 ns ✓; `build_log.txt` é honesto (compilou só um hello-world de 5 linhas sem ESP-IDF — não valida nenhum `main/*.c`, e o próprio log diz isso).

> **ERRATA (2026-10-05, pós-correção):** o achado "app_main.c:84 — `xTaskCreate` usa PALAVRAS" está **errado para o ESP-IDF**: o `task.h` do IDF v5.4 diz textualmente que `usStackDepth` é em **BYTES** ("Note that this differs from vanilla FreeRTOS"). O comentário original do firmware estava certo. A correção do firmware (seção F aplicada em 2026-10-04) também flagrou: `ledc_stop` recebe `uint32_t idle_level` (não bool, e não existe `LEDC_OUTPUT_IDLE_MODE_LOW` no v5.4), e com apenas 3 operadores MCPWM no S3 um canal do M2 corre no timer do outro motor (documentado, sem efeito elétrico pois os timers são idêgeos). O F11 (19,81 kHz) não foi reproduzido — o divisor 3,90625 é representável a partir dos 80 MHz do APB; a frequência real passa a ser logada via `ledc_get_freq()` em vez de afirmada.

> Nota: `FIRMWARE_BUILD.md` **não está em `firmware/`** — está em `fase4_entrega/`; os dois CMakeLists, o README do firmware e o ERROS_CONHECIDOS citam o caminho errado (reforça o link quebrado da seção E).

---

## G. ESTADO DO REPOSITÓRIO / PROCESSO — NOVO

1. **Trabalho não commitado**: o HEAD é `b48cac4` (04/10), mas o `ERROS_CONHECIDOS.md` atual (cita o reboot das 04:00 e a memória das 20:09) é posterior ao commit — alterações não versionadas. Último push: `4a60d41` (28/09).
2. **ERROS_CONHECIDOS.md desatualizado como registro central**: nenhum dos ~70 achados desta auditoria estava registrado; 3 alegações refutadas (§3.3, §3.5 parcial, §7 "Fase 2 sem erros"); 1 link quebrado para `firmware/FIRMWARE_BUILD.md`.
3. **Gates incompletos** (o próprio "próximo passo" do registro já aponta `verifica_projeto.py`): faltam asserções de footprints-dentro-do-contorno, nets-de-1-pad=abertas, pino DSN↔pad real, BOM↔placa, e `[EST]`==0.

---

## H. PRIORIDADES DE CORREÇÃO SUGERIDAS

1. **C1/C5-P3 (gera_pcb_v9.py)** — corrigir o sinal do empacotador (`+dx, +dy` na linha 252), medir a bbox por **pads** (não `GetBoundingBox` com textos), regenerar a v9 e adicionar gates "0 pads fora do contorno" + "0 curtos pad×pad" + "vias fora de keepout" + "zonas com preenchimento > 0". Sem isso a placa é infabricável.
2. **C5 (dsn_export.py)** — corrigir em ordem: P1 (`if is_tht or shape_is_circle(pad):` + `(rect …)` para os demais), P2 (acrescentar `(via VIA1)` na structure), P3 (offsets locais), P4 (pins 1× por pkg), P5 (THT multi-camada); propagar o `freerouting.json` correto ao `/tmp` e re-rodar o corte E2E. Teste discriminante: screenshot do ratsnest no Xvfb; se ainda sair 0 wires, investigar o net-attach silencioso de `Network.insert_component`.
3. **C6** — criar cobre para VBAT/VBAT_F/PHM/SNM (≥10,4 mm equivalentes 2 oz @ΔT20 por caminho de 30 A, ou planos + vias de transferência em quantidade real) **antes** de excluir essas nets do roteador; hoje só GND e VBAT_PROT têm zonas.
4. **C2** — corrigir a netlist: religar os divisores BEMF às fases (ou decidir formalmente abandonar o BEMF e documentar), religar o ferrite/IMU; gate "nets com 1 pad = FALHA".
5. **C3/C4** — reavaliar a margem do MOSFET (85,2 V > 80 V pelo critério interno) e regenerar a `BOM_FABRICACAO.csv` a partir da placa v9 (incluindo Cboot 2×2,2 µF ou revisar o L2) **antes de qualquer compra**.
6. **Firmware (F1–F5)** — antes de qualquer `idf.py build`: corrigir includes/assinaturas, `resolution 80 MHz`/`period 4000` no M2, `channel = i` no M3, `command_bits=0` + framing `{0x06|(ch>>2), (ch&3)<<6, 0}` + decode `((rx[1]&0x0F)<<8)|rx[2]` no M4, chamar os init no `app_main`, `CONFIG_FREERTOS_HZ=1000`, shutdown com duty 0/force-low — e preencher os GPIOs em `board_pins.h` (a tabela é derivável; a Fase 0 §8 está correta).
7. **Fase 0/2** — corrigir os cálculos que alimentam decisões (perdas 16×, comutação I vs I², IPC-2221 interno, buck5 da VBAT, re-executar gate_drive.cir com o Qg real) e re-fazer os netlists editados pós-log.
8. **Documentação** — regenerar `PLANO_FINAL.md`/README/fase4 com os números da v9, corrigir os links quebrados e registrar no `ERROS_CONHECIDOS.md` os ~110 achados desta auditoria (3 alegações atuais estão refutadas: §1.g parcial, §3.3, §7).

---

*Auditoria independente realizada por análise estática (sem python/git no ambiente de auditoria; contas verificadas manualmente e com `node`). Verificação cruzada: 4 subauditorias dedicadas (Fase 0/2, PCB/pipeline, firmware, documentação) com conclusões convergentes e independentes. Números de linha referem-se à cópia auditada (idêntica ao original em `/opt/jupyter/work/drone/`). Nota: o clone do FreeRouting citado no ERROS_CONHECIDOS §6.1 como `/opt/fr-src` está acessível em `/host/opt/fr-src`.*
