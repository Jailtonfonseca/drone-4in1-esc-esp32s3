# ERROS_CONHECIDOS — registro central de erros do projeto

**Drone 4×ESC + ESP32-S3** · atualizado em 2026-10-04 · correções do pipeline no commit `7ee221e`

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

1. **`BOM_FABRICACAO_atualizada.csv` tem só 4 linhas** (truncada no meio da atualização de preços).
   A fonte válida é `BOM_FABRICACAO.csv` (43 itens). Regenerar a "_atualizada" antes de usar. `[ABERTO]`
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
2. Toolchain Xtensa aarch64 instalada e funcional (gera `.elf`) — ver `firmware/FIRMWARE_BUILD.md`. `[OK]`

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
