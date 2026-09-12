# Drone — 4×ESC trifásico + ESP32-S3 na mesma PCB

Projeto de **uma única PCB** que concentra: 4 inversores trifásicos (ESC), gate drivers,
sensoriamento de corrente, MCU com WiFi (ESP32-S3), IMU, barômetro, USB e toda a regulação
de energia a partir de pack LiPo 6S (25,2 V máx / 19,8 V mín).

Todo o projeto foi feito **100 % headless** nesta máquina (Orange Pi 3B, Debian Bullseye
aarch64, sem desktop): script + CLI + PNG, com KiCad 5.1.9 via `pcbnew` (Python), ngspice 34,
Icarus Verilog 11, Yosys 0.9, gerbv 2.7.0 e matplotlib.

> **Regra de honestidade do projeto:** todo número afirmado nos relatórios vem de um arquivo
> de log gerado de verdade por uma ferramenta executada nesta máquina, e cada afirmação tem
> etiqueta de origem (`[MEDIDO]`, `[CALC]`, `[DATASHEET]`, `[PREMISSA]`, `[EST]`). Nada foi
> estimado "no papel" e apresentado como medido.

---

## ⚠️ Status: projeto EM ANDAMENTO

| Fase | Escopo | Estado |
|---|---|---|
| 0 | Especificação e dimensionamento | ✅ concluída |
| 1 | Esquema elétrico (8 figuras) | ✅ concluída |
| 2 | Simulação SPICE + PWM em Verilog | ✅ concluída |
| 3 | PCB (4 camadas) + Gerber | ⚠️ **em andamento — roteamento não finalizado** |
| 4 | Entrega: montagem, teste, riscos, regulatório | ⚠️ documentação em andamento |

**Não fabrique esta placa ainda.** O layout da Fase 3 ainda tem nets não roteadas
(ver `fase3_pcb/v6/verificacao_v6.txt`) e o roteador `fase3_pcb/rota_v7.py` não fechou.
Os Gerbers presentes são **versões intermediárias de desenvolvimento**.

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
├── PROMPT_AGENTE_DRONE.md          # briefing original do projeto
├── datasheets/                     # datasheets usados (ESP32-S3-WROOM-1 etc.)
├── fase0_especificacao/            # Fase 0 — especificação
├── fase1_esquema/                  # Fase 1 — esquema elétrico (PNG + geradores Python)
├── fase2_simulacao/                # Fase 2 — SPICE (ngspice) + Verilog (PWM/dead-time)
├── fase3_pcb/                      # Fase 3 — PCB KiCad + Gerber (v1 … v7)
├── fase4_entrega/                  # Fase 4 — documentação de entrega
└── orcamento/                      # Orçamento de componentes (nacional e importação)
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

- `gera_pcb_v1.py` … `gera_pcb_v7.py` — geradores do board (o board é gerado por código).
- `rota_v7.py` — roteador da versão 7 (**não finalizado**).
- `calc_trilhas_vias.py` / `_saida.txt` — cálculo de largura de trilha e vias.
- `verifica_fase3*.py` + `vN/verificacao_vN.txt` — verificação geométrica/elétrica.
- `v1/` … `v7/` — cada versão com `vN_drone.kicad_pcb`, Gerber (F_Cu, B_Cu, In1_Cu, In2_Cu,
  máscaras, silkages, Edge_Cuts), furos PTH/NPTH e renders PNG.
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

---

## Reproduzir

Nada aqui precisa de desktop. Exemplo:

```sh
# simulação SPICE
cd fase2_simulacao && ngspice -b buck12.cir

# esquema (requer schemdraw + matplotlib)
cd fase1_esquema && python3 gera_fase1_c.py

# PCB / Gerber (requer KiCad 5.1 com módulo pcbnew do sistema)
cd fase3_pcb && python3 gera_pcb_v7.py

# orçamento
cd orcamento && python3 orcamento.py
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
