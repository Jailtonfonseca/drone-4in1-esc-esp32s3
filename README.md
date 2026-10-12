# Drone — 4×ESC trifásico + ESP32-S3 na mesma PCB

> ✅ **Estado real (2026-10-12):** o board corrente é a **v10 ROTEADA** —
> [`fase3_pcb/v10/v10_roteada.kicad_pcb`](fase3_pcb/v10/v10_roteada.kicad_pcb) —
> e passa em **TODOS os gates G1–G8** do verificador
> ([`fase3_pcb/v10/verificacao_v10.txt`](fase3_pcb/v10/verificacao_v10.txt)):
> **0 curtos** (o gate novo G8 pegou 354 violações que a roteagem anterior tinha),
> 0 pads fora do contorno, 0 nets órfãs, 0 vias em keepout, 173/173 zonas preenchidas,
> 0 pads GND/VBAT_PROT sem via de stitch, ocupação elétrica 23,4 %. O pipeline de
> roteamento (FreeRouting 1.9.0) agora exporta o cobre das nets excluídas como
> **keepouts** — a placa é fabricável. Registro central de erros e correções:
> [`ERROS_CONHECIDOS.md`](ERROS_CONHECIDOS.md) (§9 = auditoria de 12/10). A BOM corrente é a
> [`orcamento/BOM_FABRICACAO_v10.csv`](orcamento/BOM_FABRICACAO_v10.csv) (MOSFET
> `NVMFS6H824NT1G`, 24 un — a BOM antiga mandava comprar o FET errado).

Projeto de **uma única PCB** que concentra: 4 inversores trifásicos (ESC), gate drivers,
sensoriamento de corrente, MCU com WiFi (ESP32-S3), IMU, barômetro, USB e toda a regulação
de energia a partir de pack LiPo 6S (25,2 V máx / 19,8 V mín).

Todo o projeto foi feito **100 % headless** nesta máquina (Linux aarch64, sem desktop):
script + CLI + PNG, com KiCad 5.1.9 via `pcbnew` (Python), ngspice 34, Icarus Verilog 11,
Yosys 0.9, gerbv 2.7.0, FreeRouting 1.9.0 (Java 17 + Xvfb) e matplotlib.

> **Regra de honestidade do projeto:** todo número afirmado nos relatórios vem de um arquivo
> de log gerado de verdade por uma ferramenta executada nesta máquina, e cada afirmação tem
> etiqueta de origem (`[MEDIDO]`, `[CALC]`, `[DATASHEET]`, `[PREMISSA]`, `[EST]`). Nada foi
> estimado "no papel" e apresentado como medido. "Pronto" é propriedade do artefato:
> [`verificacoes/verifica_projeto.py`](verificacoes/verifica_projeto.py) faz asserções duras
> e exit 1 com a lista exata do que falta.

---

## ⚠️ Status: projeto EM ANDAMENTO

| Fase | Escopo | Estado |
|---|---|---|
| 0 | Especificação e dimensionamento | ✅ concluída |
| 1 | Esquema elétrico (8 figuras) | ✅ concluída |
| 2 | Simulação SPICE + PWM em Verilog | ✅ concluída |
| 3 | PCB (6 camadas) + roteamento | ⚠️ **board v10 roteado, G1–G8 todos OK** — restam poucas nets de sinal sem rota (air-wires, listadas pelo harness) antes de fechar a Fase 3 |
| 4 | Entrega: montagem, teste, riscos, regulatório | ✅ **documentação escrita** — os 4 documentos de `fase4_entrega/` existem e acompanham o envio (F14 = "já escrito", `plano/WP2_FABRICACAO.md` §1 item 11). O que falta é **executar** a bancada (G3), não escrevê-la |

**A placa v10 roteada está livre de curtos e gates verdes** — o estado
de "pronto da Fase 3" é checado por asserções duras:
[`verificacoes/verifica_projeto.py`](verificacoes/verifica_projeto.py) (SES com wires>0,
nets 100 % roteadas, G1–G8 na base E no roteado, BOM com preço em toda linha comprável).
Hoje ele reprova exatamente no que falta (nets ainda abertas e 1 preço pendente) —
rodá-lo a qualquer momento diz onde o projeto está, sem impressão de sessão.

Para a ordem de execução completa do projeto, do estado atual até o primeiro voo —
o que falta para fabricar, o que falta para voar, a sequência de etapas, os gates e as
decisões pendentes — ver **[`PLANO_FINAL.md`](PLANO_FINAL.md)**.

### Avisos importantes

- **Nada foi validado em bancada.** Os limites de corrente contínua e o comportamento
  térmico do projeto são `[PREMISSA]` até a execução de `fase4_entrega/PLANO_TESTE_BANCADA.md`.
- **Antes de voar:** requisitos regulatórios brasileiros (registro/SISANT, peso, distância)
  precisam ser verificados — ver `fase4_entrega/SEGURANCA_E_REGULATORIO.md`.
- LiPo 6S tem energia suficiente para incêndio. Ver `fase4_entrega/RISCOS.md`.

---

## Estrutura do repositório

```
drone/
├── ERROS_CONHECIDOS.md              # registro central de erros (§9 = auditoria 12/10)
├── AUDITORIA_ERROS_2026-10-04.md    # relatório da 1a auditoria (~110 erros)
├── PROMPT_AGENTE_DRONE.md           # briefing original do projeto
├── verificacoes/                    # asserções duras de projeto (verifica_projeto.py)
├── datasheets/                      # datasheets usados (ESP32-S3-WROOM-1 etc.)
├── fase0_especificacao/             # Fase 0 — especificação
├── fase1_esquema/                   # Fase 1 — esquema elétrico (PNG + geradores Python)
├── fase2_simulacao/                 # Fase 2 — SPICE (ngspice) + Verilog (PWM/dead-time)
├── fase3_pcb/                       # Fase 3 — PCB KiCad + pipeline FreeRouting (v1 … v10)
├── fase4_entrega/                   # Fase 4 — documentação de entrega
├── orcamento/                       # Orçamento de componentes (nacional e importação)
└── plano/                           # Plano de execução — WP1..WP5, DO_PROJETO e scripts
```

### Fase 0 — Especificação (`fase0_especificacao/`)

- `FASE0_ESPECIFICACAO.md` — documento principal da especificação.
- `dimensionamento_fase0.py` / `.json` / `_saida.txt` — cálculo dos estágios.
- `verifica_limites_entrada*.py` / `verifica_limites_saida*.txt` — verificação de limites.
- `lista_componentes_fase0.csv` — **lista de componentes (43 linhas)**; é a fonte de
  quantidades do orçamento.
- `diagrama_blocos_v3.py` / `diagrama_blocos_fase0_v3.png` — diagrama de blocos.

### Fase 1 — Esquema (`fase1_esquema/`)

Oito figuras geradas por código (schemdraw), cada uma com o script que a produz:

| Figura | Assunto |
|---|---|
| `esq1_entrada_protecao.png` | Entrada, proteção e anti-inversão de polaridade |
| `esq2_buck12v.png` | Buck 12 V |
| `esq3_buck5v.png` | Buck 5 V |
| `esq4_buck3v3.png` | Buck 3,3 V |
| `esq4_esc_trifasico.png` | Ponte trifásica (uma fase) |
| `esq5_esc_halfbridge.png` | Half-bridge + gate driver |
| `esq6_esc_visao_geral.png` | Visão geral do ESC 4× |
| `esq7_mcu.png` | MCU ESP32-S3 |
| `esq8_arvore_energia.png` | Árvore de energia |

Scripts: `gera_fase1_a.py`, `gera_fase1_b.py`, `gera_fase1_c.py`, `gera_esq4.py`,
`gera_esquemas_p1.py` (rascunhos em `rascunho/`).

### Fase 2 — Simulação (`fase2_simulacao/`)

- `RESULTADOS_FASE2_SPICE.md` — relatório (uma linha por grandeza, com valor esperado,
  medido, erro e chave no log).
- `resultados_fase2_spice.csv` — a mesma tabela em CSV.
- Netlists: `buck12.cir`, `buck5.cir`, `buck3v3.cir`, `divisor_vbat.cir`, `shunt_amp.cir`,
  `gate_drive.cir`, `prot_inversao.cir`, `bemf_div.cir` (+ `.log` de cada).
- `gera_tabela.py`, `minimiza_ripple.py` — automação e otimização.
- `verilog/RELATORIO_VERILOG.md` — PWM de 12 canais com dead-time em Verilog, simulado com
  Icarus e sintetizado com Yosys.
- `_testes/` — netlists de diagnóstico usadas durante a investigação.

### Fase 3 — PCB (`fase3_pcb/`)

- `gera_pcb_v1.py` … `gera_pcb_v10.py` — geradores do board (o board é gerado por código;
  a linhagem viva é a v10 — as anteriores são registro histórico).
- `freerouting/` — pipeline de roteamento real (FreeRouting 1.9.0):
  - `dsn_export.py` — board → DSN, **com keepouts do cobre das nets excluídas** (§9.1)
    e **wires fixos** das rotas existentes (para completar roteamento parcial);
  - `ses_import.py` — SES → trilhas KiCad (com guarda anti-re-import);
  - `SesFromFrb.java` — extrai o SES de um `.frb` intermediário sem GUI (§9.6);
  - `fr_watchdog.py` — dispensa diálogos modais do FR dentro do Xvfb;
  - `FONTE_FREEROUTING.md` — o runbook: tudo medido, não presumido.
- `verifica_fase3_v10.py` → `v10/verificacao_v10.txt` — os **gates G1–G8**
  (G8 = trilha×cobre de net excluída, o gate dos 354 curtos).
- `v10/` — board base (`v10_drone.kicad_pcb`), **board roteado** (`v10_roteada.kicad_pcb`),
  SES final, logs do run e verificação.
- `verificacoes/verifica_projeto.py` (na raiz do repo) — asserções duras de projeto inteiro.
- `kicad-cli` não existe nesta máquina: os Gerbers são gerados por script `pcbnew`.

### Fase 4 — Entrega (`fase4_entrega/`)

- `PLANO_TESTE_BANCADA.md` — instrumentos e ensaios, com o que medir e critério de aceite.
- `MONTAGEM_ORDEM_DE_SOLDA.md` — ordem de solda e cuidados de montagem.
- `SEGURANCA_E_REGULATORIO.md` — segurança elétrica e requisitos regulatórios (Brasil).
- `RISCOS.md` — matriz severidade × probabilidade, mitigação e detecção.
- `ANALISE_WIFI_CONTROLE.md` — análise do link de controle WiFi.
- `calcs_fase4.txt`, `calcs_wifi_controle.txt` — saídas de cálculo usadas nos documentos.

### Orçamento (`orcamento/`)

- `ORCAMENTO.md` — relatório completo (cenário A: compra nacional; cenário B: importação).
- `orcamento_detalhado.csv` — item a item.
- `orcamento_por_bloco.csv` — agrupado por bloco funcional.
- `custo_por_bloco.png` — gráfico.
- `orcamento.py` — script que gera tudo acima.

As quantidades vêm de `fase0_especificacao/lista_componentes_fase0.csv`. Itens sem cotação
real coletada estão marcados `[EST]` no relatório.

### Plano de execução (`plano/`)

- `WP1_ROTEAMENTO.md` a `WP5_DECISOES.md` — as cinco auditorias consolidadas.
- `DO_PROJETO.md`, `mede_v7_wp1.py` — definition of done e a contagem independente do layout.
- A ordem de trabalho única está em [`PLANO_FINAL.md`](PLANO_FINAL.md), na raiz.

---

## Reproduzir

Nada aqui precisa de desktop. Exemplo:

```sh
# simulação SPICE
cd fase2_simulacao && ngspice -b buck12.cir

# board base v10 (requer KiCad 5.1 com módulo pcbnew do sistema)
cd fase3_pcb && python3.9 gera_pcb_v10.py

# pipeline de roteamento (FreeRouting 1.9.0 + Java 17 + Xvfb; ver FONTE_FREEROUTING.md)
cd fase3_pcb/freerouting && cp freerouting.json /tmp/     # o FR lê do java.io.tmpdir!
python3.9 dsn_export.py ../v10/v10_drone.kicad_pcb ../v10/freerouting_run/v10_dsn_input.dsn
xvfb-run -a java -jar <caminho>/freerouting-1.9.0.jar \
    -de ../v10/freerouting_run/v10_dsn_input.dsn -do ../v10/freerouting_run/v10_final.ses
python3.9 ses_import.py ../v10/v10_drone.kicad_pcb \
    ../v10/freerouting_run/v10_final.ses ../v10/v10_roteada.kicad_pcb

# verificação (gates G1-G8) e asserções duras de projeto
python3.9 fase3_pcb/verifica_fase3_v10.py fase3_pcb/v10/v10_roteada.kicad_pcb
python3.9 verificacoes/verifica_projeto.py

# orçamento
cd orcamento && python3.9 orcamento.py
```

## Licença

Distribuído sob a **licença MIT** — texto completo em [`LICENSE`](LICENSE).

A licença cobre todo o conteúdo do repositório: o software (scripts Python e Verilog),
os arquivos de projeto (esquemas, layout KiCad, Gerbers) e a documentação.

Como toda licença permissiva, a MIT é fornecida **"como está", sem garantia de qualquer
espécie**. Isso pesa aqui mais que o normal: este é um projeto de eletrônica de potência
**em andamento e não validado em bancada**, então a ausência de garantia e a limitação de
responsabilidade valem integralmente (ver os avisos no topo deste README).

> **Nota sobre os datasheets:** os PDFs em `datasheets/` são material de terceiros
> (Espressif, TDK/InvenSense), incluídos apenas como referência de projeto e **não**
> são cobertos pela licença MIT deste repositório.
