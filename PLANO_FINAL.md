# PLANO_FINAL — do estado atual ao primeiro voo

Documento único de execução. Consolida `plano/WP1_ROTEAMENTO.md`, `plano/WP2_FABRICACAO.md`,
`plano/WP3_PREMISSAS_DATASHEETS.md`, `plano/WP4_FIRMWARE.md` e `plano/WP5_DECISOES.md` numa
ordem de trabalho só. **Data de consolidação: 2026-09-28.**

**Regras de leitura deste documento:**

- Todo número aqui vem de um documento de trabalho citado na coluna "fonte" ou de um comando
  executado nesta máquina. Nada foi estimado "no papel" e apresentado como medido.
- `[EST]` = estimativa de engenharia. Não é medido. Onde não há número, está escrito
  **NÃO DETERMINADO** com o motivo.
- Quando dois documentos divergem, a divergência é citada, não silenciada.
- **Ressalva que vale para o documento inteiro: nada foi validado em bancada.** Os limites de
  30 A (pico) e 15 A (contínuo) por motor continuam sendo `[PREMISSA]`
  (`fase0_especificacao/FASE0_ESPECIFICACAO.md`; confirmado em `fase4_entrega/RISCOS.md` §5).
  **E o roteamento ainda não fecha** — o Gerber existente é de desenvolvimento.

---

## Sumário executivo

1. A placa tem esquema, simulação, layout e documentação, mas **não é fabricável e não voa**:
   o layout da v7 tem **138 das 202 nets sem uma única trilha**, e nenhum roteador automático
   disponível fecha isso (`plano/WP1_ROTEAMENTO.md` §1.2).
2. O gargalo **não é de cobre, é de cobertura**: a largura das trilhas de potência já está
   conferida contra `fase3_pcb/calc_trilhas_vias_saida.txt` e atende (6,29 mm nas fases, 4,0 mm
   no VBAT contínuo), mas **309 dos 309 pads de GND e VBAT_PROT estão a mais de 1,6 mm de uma
   via** — nem tocando os planos eles funcionariam (`plano/WP1_ROTEAMENTO.md` §3.2).
3. **Não existe firmware.** Zero linhas em C/C++ no repositório; o que há é RTL Verilog de PWM
   que não roda no ESP32-S3. O escopo mínimo para voar é **320 h** `[EST]`, das quais 160 h
   são só para tornar o plano de bancada executável (`plano/WP4_FIRMWARE.md` §1 e §5).
4. O pacote de fabricação está em **6 artefatos inexistentes, 3 parciais, 2 ok** — 30,0 h
   `[EST]` de trabalho de arquivo, e esse número **não depende** de nenhuma decisão de layout
   (`plano/WP2_FABRICACAO.md` §1).
5. Duas premissas que sustentavam o projeto foram refutadas por datasheet: **Qg = 168/210 nC**
   (assumido 40 nC, fator ~4) e **quiescência do driver = 325 µA** (assumido 2,5 mA, fator 7,7)
   (`plano/WP3_PREMISSAS_DATASHEETS.md` P-06 e P-11).

### O que falta? — direto

- **Para fabricar:** fechar as 138 nets e os 309 pads de plano (decisão D-02/D-03 primeiro, §7),
  e gerar os 8 artefatos que não existem — 30,0 h `[EST]`, comuns a qualquer escolha de layout.
- **Para voar:** 320 h `[EST]` de firmware, uma revisão de bancada que nunca foi executada, e a
  checagem regulatória que `fase4_entrega/SEGURANCA_E_REGULATORIO.md` exige.
- **Para decidir qualquer uma das duas:** três respostas suas, hoje. D-08 (part numbers),
  D-02+D-03 (roteamento e tamanho) e D-01 (firmware entra ou não). As três destravam quatro
  decisões cada uma — ver `plano/WP5_DECISOES.md` §4.

---

## 1. Estado atual em números

| O que é | Medido | Fonte (arquivo) | O que significa |
|---|---:|---|---|
| Footprints no layout | 319 | `fase3_pcb/v7/v7_drone.kicad_pcb` (`plano/WP1_ROTEAMENTO.md` §1.2) | A netlist está completa em símbolos; falta o cobre. |
| Pads | 1.093 | idem §1.2 | 1.045 SMD (945 só em F.Cu) + 48 TH/fixo. |
| Trilhas | 252 | idem §1.2 (F.Cu 192, B.Cu 60) | Só 2 camadas de sinal; In1.Cu e In2.Cu são planos. |
| Vias | 353 | idem §1.2 | Todas do par B.Cu/F.Cu; nenhuma F.Cu↔In1/In2. |
| Objetos de cobre | 605 | 252 + 353 | — |
| Nets declaradas | 202 | `GetNetCount()-1` | **Divergência de nomenclatura:** o `fase3_pcb/rota_v7.py` imprime `nets na grade: 203` porque conta nomes de net em pads+trilhas+vias. 202 é o netlist, 203 é o dicionário de grade. Os dois estão certainos no seu contexto (`plano/WP1_ROTEAMENTO.md` §1.3). |
| **Nets com pad e zero trilha** | **138** | `plano/WP1_ROTEAMENTO.md` §1.2 | **Bloqueante.** São as 9 redes dos ESCs (GHM101–303) e o barramento inteiro de controle: SPI dos 4 MCP3208, I2C do IMU, 12 PWMs, 4 canais de ADC, UART, USB, EN/BOOT, buzzer, 3V3_A, 5V_AUX. |
| Pads de GND/VBAT_PROT sem via a < 1,6 mm | **309 de 309** (GND 207 + VBAT_PROT 102) | `plano/WP1_ROTEAMENTO.md` §3.2 | **Bloqueante.** A placa não alcança os próprios planos. |
| Pares trilha×pad de nets diferentes com folga crítica | 12 (medido na **v6**); na v7 **NÃO DETERMINADO** | `fase3_pcb/v6/verificacao_v6.txt` | `plano/WP1_ROTEAMENTO.md` §5.4 não usa o número da v6 como se fosse da v7: medir exigiria isolar o bloco de verificação do `fase3_pcb/rota_v7.py`, que passa pelo A*. |
| Keepouts definidos | 0 | `grep -c "rule_area\|keepout" fase3_pcb/v7/v7_drone.kicad_pcb` → 0 | Setor de potência e de sinal dividem o mesmo plano de cobre. |
| Dimensão da placa | 220,10 × 160,10 mm (352,4 cm²) | `plano/WP1_ROTEAMENTO.md` §1.4 | Superdimensionada em área para 187 nets roteáveis. |
| `fase3_pcb/rota_v7.py` | `exit=124` em 240 s; `fase3_pcb/v8/` continua vazio | `plano/WP1_ROTEAMENTO.md` §2.2 | O A* é chamado ≥125 vezes (piso medido) sobre uma grade 440×320. `BRD.Save()` está na linha 451, depois do roteamento: não há checkpoint. |
| Artefatos de fabricação | 6 ❌ / 3 ⚠️ / 2 ✅ (de 11) | `plano/WP2_FABRICACAO.md` §1 | Esquema nativo, netlist, CPL, libs, stackup e drill map não existem. |
| Esforço de artefatos | **30,0 h** `[EST]` (34,0 h com a BOM de fabricação) | `plano/WP2_FABRICACAO.md` §1 | Comum a **todas** as opções de layout — dá para começar antes de decidir D-02. |
| Datasheets | 12 arquivos: 9 `.pdf` + 2 `.txt` + 1 `.INVALIDO_HTML` (539 B) | `datasheets/` | 7 baixados por esta auditoria. **Ressalva:** 1 dos 9 `.pdf` não é PDF, e há um segundo HTML mascarado em `datasheets/.ipynb_checkpoints/icm-42688-p-checkpoint.pdf` (539 B), alcançado só por glob recursivo. |
| Premissas refutadas por datasheet | 2 (P-06 Qg, P-11 quiescência) | `plano/WP3_PREMISSAS_DATASHEETS.md` §1 | Ambas sustentavam o dimensionamento de gate drive da Fase 0. |
| Parâmetros ainda sem fonte | Ciss, ESR, ESL, corrente nominal do XT60, Vf do diodo | `plano/WP3_PREMISSAS_DATASHEETS.md` §5.1 e §5.2 | Nenhuma peça escolhida para MOSFET final, célula, motor, bucks, shunt, indutores e capacitores. |
| Firmware em C/C++ | **0 arquivos** | `plano/WP4_FIRMWARE.md` §3 (`find` real) | Não existe. O que existe é RTL Verilog que não roda no ESP32-S3. |
| RTL do PWM de 12 canais | dead-time **518,750 ns**, 20 kHz, **0 violações** em **362 060 ciclos** | `fase2_simulacao/verilog/RELATORIO_VERILOG.md` §4.3 | Modelo de referência validado, não firmware embarcado. |
| Esforço de firmware | **320 h** `[EST]` = 160 h bancada + 160 h voo | `plano/WP4_FIRMWARE.md` §5 | 8,0 semanas de 40 h `[CALC na §9.2]`. |
| Canais de ADC | ADC1 do ESP32-S3 tem **20 no máximo**; são necessários **26** | `plano/WP4_FIRMWARE.md` §4.1, `datasheets/esp32-s3_datasheet_en.pdf` | ADC externo por SPI é obrigatório por contagem fechada, não por premissa. |
| Decisões pendentes | 15 (D-01..D-15); 4 bloqueantes hoje | `plano/WP5_DECISOES.md` §2 | D-01, D-02, D-06, D-08. |
| Orçamento | nacional R$ 1.706 / importação R$ 1.354; **37 de 43 itens** `[EST]`; **0 de 43** com disponibilidade/lead time | `orcamento/ORCAMENTO.md` | Sem part number (§7, D-08) nenhuma compra é possível. |
| Repositório | GitHub **público**, licença **MIT**, 3 commits no remoto | `LICENSE`, estado verificado em 2026-09-28 | Commits locais à frente, **não enviados**. Ver D-06. |
| Validação em bancada | **nenhuma** | `fase4_entrega/RISCOS.md` §5, `fase4_entrega/PLANO_TESTE_BANCADA.md` | 30 A e 15 A seguem `[PREMISSA]`. |

---

## 2. O que falta para pronto para fabricação

Cada linha tem um critério objetivo: um comando ou um arquivo, não uma opinião.

| # | Falta | Critério objetivo de "pronto" | Documento que detalha | Esforço `[EST]` |
|---|---|---|---|---:|
| F1 | **Roteamento fechado** | `fase3_pcb/v8/verificacao_v8.txt` com `nets NAO roteadas : 0` **e** `pares trilha x pad ... proximos: 0`, mais a contagem independente A1 = 0 (ver §5, gates G1) | `plano/WP1_ROTEAMENTO.md` §5 | incluído em E3 |
| F2 | **309 pads de plano com via próxima** | contagem independente de pads de GND/VBAT_PROT sem via a < 1,6 mm devolve **0** | `plano/WP1_ROTEAMENTO.md` §3.2 e D-10 | incluído em E3 |
| F3 | **Esquema nativo KiCad** (`.sch`/`.kicad_sch`) | `find . -name '*.sch' -o -name '*.kicad_sch'` devolve ≥ 1 arquivo **não vazio** | `plano/WP2_FABRICACAO.md` §1 item 1 | 24 h |
| F4 | **Netlist de produção** (`.net`) | `find . -name '*.net'` devolve o arquivo, e o número de nets dele bate com o painel de F1 | `plano/WP2_FABRICACAO.md` §1 item 2 | 0,5 h |
| F5 | **Pick-and-place / CPL** (`.pos` ou `.csv`) | arquivo de posições com os 319 módulos, lados Top/Bot separados | `plano/WP2_FABRICACAO.md` §1 item 3 | 0,5 h |
| F6 | **Bibliotecas** (`.lib` / diretório .pretty) | `find . -name '*.lib'` e as 30 bibliotecas de footprint distintas extraídas do board | `plano/WP2_FABRICACAO.md` §1 item 5 | 2 h |
| F7 | **Stackup da placa** | o `.kicad_pcb` tem `stackup`, `dielectric`, `copper_thickness` e `impedance` — hoje os quatro têm contagem **0** | `plano/WP2_FABRICACAO.md` §1 item 6 | 1 h |
| F8 | **Drill map / desenho dos furos** | `.drr` e mapa visual gerados, além dos 2 `.drl` existentes | `plano/WP2_FABRICACAO.md` §1 item 7 | 1 h |
| F9 | **`.gbrjob` e unidade/zero declarados** | `po.SetCreateGerberJobFile(True)` em `fase3_pcb/gera_pcb_v7.py:545` e replot; o `.gbrjob` aparece ao lado dos 9 `.g*` | `plano/WP2_FABRICACAO.md` §1 item 8 e §2.6 | 0,5 h |
| F10 | **Contorno em Edge.Cuts nativo** | `gr_line` em Edge.Cuts passa de 0 para 4, fechadas, substituindo o `gr_poly` | `plano/WP2_FABRICACAO.md` §1 item 9 e §3.3 C5 | 0,5 h |
| F11 | **Nome dos Gerbers** | os arquivos começam com `drone_`, não com `-drone_`; e o pacote de envio tem **uma única versão** (as pastas `v1`–`v7` ficam de fora) | `plano/WP1_ROTEAMENTO.md` §3.5 e `plano/WP2_FABRICACAO.md` §3.3 C1–C4 | incluído nos itens acima |
| F12 | **BOM de fabricação amarrada ao board** | CSV com designator, MPN e fabricante em **43/43** linhas; hoje faltam em 43/43 | `plano/WP2_FABRICACAO.md` §4 | 4 h |
| F13 | **Part numbers e cotação real** | disponibilidade e lead time de **0/43 → 43/43**; 37 preços `[EST]` substituídos por preço real | `plano/WP5_DECISOES.md` D-08 e §3.8 | **NÃO DETERMINADO** — nenhuma fonte estima cotação; `plano/WP5_DECISOES.md` só diz que nenhum item foi verificado |
| F14 | **Documentação no pacote** | `fase4_entrega/PLANO_TESTE_BANCADA.md`, `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md`, `fase4_entrega/RISCOS.md` e `fase4_entrega/SEGURANCA_E_REGULATORIO.md` acompanham o envio | `plano/WP2_FABRICACAO.md` §1 item 11 | já escrito |
| F15 | **Datasheets limpos** | o arquivo de 539 B sai do pacote; o `datasheets/.ipynb_checkpoints/icm-42688-p-checkpoint.pdf` sai também | `plano/WP3_PREMISSAS_DATASHEETS.md` §3.1 e §3.4 | **NÃO DETERMINADO** — WP3 não estima o esforço da limpeza |

**Soma rastreada de F3 a F10: 24 + 0,5 + 0,5 + 2 + 1 + 1 + 0,5 + 0,5 = 30,0 h** `[EST]`
(`plano/WP2_FABRICACAO.md` §1). Com F12 (4 h), **34,0 h** `[EST]`.
**Nada nesse total depende de D-01, D-02, D-03, D-04 ou D-05** — dá para executar em paralelo à
decisão de layout.

---

## 3. O que falta para pronto para voar

| # | Falta | Critério objetivo de "pronto" | Documento que detalha | Esforço `[EST]` |
|---|---|---|---|---:|
| V1 | **Firmware de bancada (M0–M6, M10, M11)** | build reproduzível por um comando; VBAT medido em 19,8 / 22,2 / 25,2 V com erro < 2 %; overlap de gate = 0; corrente linear < 2 % entre 5 e 30 A; IMU estável com motor a 100 %; corte de link ≤ 200 ms; reset por watchdog ≤ 1 s com motivo legível | `plano/WP4_FIRMWARE.md` §5 (M0–M6, M10, M11) | **160 h** |
| V2 | **Correção do dimensionamento de gate drive** | Qg = 168 nC (typ) / 210 nC (max) aplicado; `fase0_especificacao/dimensionamento_fase0_saida_v2.txt` e `fase0_especificacao/verifica_limites_saida_v4.txt` reexecutados; P-11 corrigida para 0,325 mA | `plano/WP3_PREMISSAS_DATASHEETS.md` §6 itens 1–2; `plano/WP5_DECISOES.md` D-11 | 4–6 h |
| V3 | **Mapa de pinos oficial** | o pin map vem do netlist do layout (`fase3_pcb/gera_pcb_v7.py` linhas 400–411), **não** da §8 da Fase 0 — hoje os motores 2, 3 e 4 divergem inteiros e o pad 8 está trocado | `plano/WP4_FIRMWARE.md` RF-07 | incluído em V1 |
| V4 | **Decisão do ADC** | 4× MCP3208 ou 2× ADS7953 decidido e **medido**; hoje a taxa exigida é 120 % do datasheet a 5 V e 240 % a 2,7 V, e o MCP3208 multiplexa (não há amostragem simultânea) | `plano/WP4_FIRMWARE.md` RF-01, RF-02, RF-11; `plano/WP5_DECISOES.md` D-12 | **NÃO DETERMINADO** — D-12 não traz horas |
| V5 | **Decisão do corte por software** | `SD` dos 12 IR2104 rotado para 1 GPIO do ESP32-S3, ou a limitação aceita por escrito | `plano/WP4_FIRMWARE.md` RF-03; `plano/WP5_DECISOES.md` D-13 | ~0 h `[EST]` (1 linha no gerador) |
| V6 | **Decisão do watchdog** | watchdog externo presente no layout ou a limitação aceita; hoje não há CI de watchdog e o `WD_FEED` só aparece no pad 25 e no `TP_WD` | `plano/WP4_FIRMWARE.md` RF-04; `plano/WP5_DECISOES.md` D-07 | **NÃO DETERMINADO** — D-07 não traz horas |
| V7 | **Dead-time real medido em bancada** | dead-time medido de um motor que vá por LEDC, a 12 V de alimentação, e o orçamento do firmware sai **do valor medido**, não dos 518,750 ns do RTL | `plano/WP4_FIRMWARE.md` RF-14 | dentro de V8 |
| V8 | **Bancada completa** | todos os passos de `fase4_entrega/PLANO_TESTE_BANCADA.md` aprovados, com hélices removidas | `fase4_entrega/PLANO_TESTE_BANCADA.md`; ordem de solda em `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` | **NÃO DETERMINADO** — o plano de bancada não traz estimativa de horas |
| V9 | **Firmware de voo (M7, M8, M9, M12, M13)** | PID de 6 eixos, comutação de 6 passos, ESP-NOW, proteções e integração em bancada aprovados | `plano/WP4_FIRMWARE.md` §5 (M7, M8, M9, M12, M13) | **160 h** |
| V10 | **Controle por rádio** | orçamento do link conferido: tempo de ar de 32 B = 672 µs a 1 Mbps, 3,36 % de ocupação a 50 Hz | `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §4 | incluído em V9 |
| V11 | **Regulatório e segurança** | registro/SISANT, peso e distância de operação verificados antes do primeiro voo | `fase4_entrega/SEGURANCA_E_REGULATORIO.md` | **NÃO DETERMINADO** |
| V12 | **Limites de corrente validados** | 30 A pico e 15 A contínuo medidos, não `[PREMISSA]` | `fase4_entrega/PLANO_TESTE_BANCADA.md` | dentro de V8 |

**Total firmware rastreado: 320 h** `[EST]` (V1 160 h + V9 160 h) = 8,0 semanas de 40 h
`[CALC — plano/WP4_FIRMWARE.md §9.2]`. Somando V2 (4–6 h) e os 34,0 h de §2, o esforço
**rastreado** do caminho completo até voar é **358,0 h a 360,0 h** `[EST]`, **sem** o redesenho
de layout (E3, 2–3 semanas `[EST]`) e **sem** a cotação (F13, NÃO DETERMINADO).

---

## 4. Sequência de etapas

| Etapa | Depende de | O que é feito | Documento que detalha | Gate de passagem | Esforço `[EST]` |
|---|---|---|---|---|---:|
| **E0** | — | Responder D-08, D-02, D-03 e D-01. As outras 11 decisões vêm depois, mas nenhuma trava a E0. | `plano/WP5_DECISOES.md` §2 e §4 | As 3 respostas estão escritas e datadas | **NÃO DETERMINADO** — é tempo de decisão, não de trabalho |
| **E1** | E0 (D-08 escolhe a peça) | Refazer o dimensionamento de gate drive com Qg = 168/210 nC e corrigir P-11 para 0,325 mA; reexecutar os scripts da Fase 0 | `plano/WP3_PREMISSAS_DATASHEETS.md` §6; `plano/WP5_DECISOES.md` D-11 | `fase0_especificacao/dimensionamento_fase0_saida_v2.txt` e `fase0_especificacao/verifica_limites_saida_v4.txt` reexecutados com o Qg novo | 4–6 h |
| **E2** | E0 | Fechar part numbers, cotar com disponibilidade e lead time, e produzir a BOM de fabricação com MPN/fabricante em 43/43 linhas | `plano/WP5_DECISOES.md` D-08, D-14; `plano/WP2_FABRICACAO.md` §4; `orcamento/ORCAMENTO.md` | 43/43 itens com preço real e lead time | 4 h (BOM) + cotação **NÃO DETERMINADA** |
| **E3** | E0 (D-02 + D-03), E1 | Layout novo: 6 camadas + contorno ~150×110 mm, preservando as 202 nets e os 319 footprints. **Pacote único de correções de layout, tudo na mesma revisão:** (a) stitch vias do D-10; (b) rotação do `SD` dos 12 IR2104 para um GPIO (D-13); (c) **fusível 30 A 1206 no polo positivo do VBAT (D-15, recomendação A)** — 1 footprint de 2 pinos, 0 GPIO, 0 net de sinal; (d) **definir os keepouts de potência e de sinal no gerador** (`rule_area` no `fase3_pcb/gera_pcb_v8.py` — **ainda não existe**: é o gerador da v8, a criar copiando `fase3_pcb/gera_pcb_v7.py`, que existe; hoje a v7 tem 0 `rule_area`); (e) **D-09 fechada antes de começar**: com a recomendação A (manter os 12× INA240A2) **não há respin** — se você escolher B (INA181/INA241), a troca entra neste mesmo pacote e vira um quinto item | `plano/WP1_ROTEAMENTO.md` §4 e §3.3; `plano/WP5_DECISOES.md` §3.2, §3.3, §3.9 e §3.15 | G1 (§5) — as 8 linhas do painel de aceitação | **2–3 semanas** `[EST]` (`plano/WP5_DECISOES.md` §3.2 — em horas: **NÃO DETERMINADO**, nenhuma fonte converte) |
| **E4** | E0, D-01, E2, E3 | Gerar os 8 artefatos que não existem, o `.gbrjob`, o Edge.Cuts nativo, o nome dos Gerbers e a BOM | `plano/WP2_FABRICACAO.md` §1 e §3.3 | G2 (§5) | 30,0 h (34,0 h com a BOM, já contada em E2) |
| **E5** | E3, E4 | Montar a placa seguindo a ordem de solda | `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` | placa montada sem curto; não há estimativa de horas no documento | **NÃO DETERMINADO** |
| **E6** | E3, E4, E5, D-01 = B | Firmware de bancada M0–M6 + M10 + M11 | `plano/WP4_FIRMWARE.md` §5 | critérios de aceite de cada módulo, colados na §5 do WP4 | **160 h** |
| **E7** | E5, E6 | Executar a bancada completa, hélices removidas, medindo inclusive o dead-time real | `fase4_entrega/PLANO_TESTE_BANCADA.md`; riscos em `fase4_entrega/RISCOS.md` | G3 (§5) | **NÃO DETERMINADO** |
| **E8** | E7, E7 (com a decisão de bancada) | Firmware de voo M7 + M8 + M9 + M12 + M13 | `plano/WP4_FIRMWARE.md` §5 | todos os módulos com o critério de aceite medido | **160 h** |
| **E9** | E8 | Voo com o link de comando, com failsafe e watchdog ativos | `fase4_entrega/ANALISE_WIFI_CONTROLE.md`; `fase4_entrega/RISCOS.md` | G4 (§5) | **NÃO DETERMINADO** |
| **E10** | E3, E4 (independe de E6–E9) | Regulatório e segurança: registro/SISANT, peso, distância de operação | `fase4_entrega/SEGURANCA_E_REGULATORIO.md` | requisitos verificados por escrito | **NÃO DETERMINADO** |
| **E0.1** | — | Pode rodar **em paralelo a E3 e E4**, em qualquer ordem: netlist de produção (0,5 h) e sketch do stackup (1 h) são comuns a todas as opções. **As 1,5 h já estão contidas nos 30,0 h de E4** (F4 = 0,5 h + F7 = 1 h, §2) — E0.1 é uma reordenação, **não some duas vezes** | `plano/WP5_DECISOES.md` §3.1 e §3.2 | arquivos gerados | 1,5 h **dentro dos 30,0 h de E4** |

**Ordem de ataque recomendada para a próxima semana:** E0 (as 3 decisões) → E0.1 e E1/E2 em
paralelo → E3 → E4 → E5 → E6 → E7. E10 pode ser feito em qualquer momento depois de E3.

---

## 5. Gates

Cada gate é binário e verificável por comando **ou por medição em bancada/voo**. O projeto só
avança quando o gate inteiro é verdadeiro.

- **G1 e G2 são de comando** — arquivo gerado, contagem e `find` rodam nesta máquina hoje.
- **G3 e G4 são de medição em bancada e em voo** — não existe comando que os substitua, e
  **nenhuma das duas medições foi feita**. É por isso que a ressalva "nada validado em bancada"
  vale para o documento inteiro (§8.1).

### G1 — Layout fechado (`plano/WP1_ROTEAMENTO.md` §5.2)

| ID | Critério | Alvo | Como medir |
|---|---|---:|---|
| A1 | nets com pad e **zero trilha** | **0** | contagem independente com `/usr/bin/python3.9` + `plano/mede_v7_wp1.py` apontado para a v8 |
| A2 | pares trilha×pad de nets diferentes com folga crítica | **0** | `fase3_pcb/v8/verificacao_v8.txt`, seção de checagem de curto |
| A3 | pads de nets diferentes com bbox sobreposto | **0** | `fase3_pcb/v8/verificacao_v8.txt` |
| A4 | pads de GND/VBAT_PROT sem via a < 1,6 mm | **0** (de 309) | `plano/mede_v7_wp1.py`, seção de planos |
| A5 | trilhas em In1.Cu / In2.Cu | **0** (mantidas como plano) | `plano/mede_v7_wp1.py` |
| A6 | largura da trilha de fase do motor | ≥ 6,29 mm | `plano/mede_v7_wp1.py`, `larguras de trilha` |
| A7 | nome dos Gerbers começa com `-drone_` | **não** | `ls fase3_pcb/v8/*.gt*` |
| A8 | keepouts de potência e de sinal definidos | **≥ 1** `rule_area` (hoje **0**) | `grep -c "rule_area" fase3_pcb/v7/v7_drone.kicad_pcb` devolve `0`; na v8 tem de devolver **> 0** |

> **A2 e A1 não se substituem.** As duas primeiras linhas de `fase3_pcb/v8/verificacao_v8.txt` declaram `0`
> também para nets que têm um único pad; por isso A1, medido à parte, é obrigatório como
> contraprova (`plano/WP1_ROTEAMENTO.md` §5.3).
> **Estado hoje:** A1 = 138, A4 = 309, A6 = ok, A5 = ok, A7 = falha, **A8 = 0** (nenhum keepout no
> board, `plano/WP1_ROTEAMENTO.md` §3.3); **A2 na v7 é
> NÃO DETERMINADO** (o 12 é da v6 — ver §1 e §8.5). O alvo A3 = 0 só tem medição na v6
> (`fase3_pcb/v6/verificacao_v6.txt`) e precisa ser reconferido na v8.
>
> **Atenção ao `test -e`:** **dois** dos caminhos citados **ainda não existem**, e os dois são
> artefatos a produzir, não insumos: (1) `fase3_pcb/v8/verificacao_v8.txt` — o arquivo que o gate G1
> manda produzir; o diretório `fase3_pcb/v8/` está vazio desde 2026-09-11 22:37, porque
> `fase3_pcb/rota_v7.py` só grava depois do laço de roteamento
> (`plano/WP1_ROTEAMENTO.md` §2.3 e §5.1); (2) `fase3_pcb/gera_pcb_v8.py` — o gerador da v8, a
> criar a partir de `fase3_pcb/gera_pcb_v7.py` (que existe). **Todos os outros caminhos citados
> existem** — a lista completa, com a saída real do `test -e` e os dois ausentes marcados como "a
> produzir", está na tabela de correções abaixo.

### G2 — Pacote de fabricação completo (`plano/WP2_FABRICACAO.md` §5)

- `find` devolve 0 arquivo para: esquema nativo, netlist, CPL, `.lib`, `.drr`, `.gbrjob`.
- A BOM tem designator, MPN e fabricante em 43/43 linhas.
- O `.kicad_pcb` tem `stackup`, `dielectric`, `copper_thickness` e `impedance` com contagem ≥ 1.
- O zip de envio tem **uma única versão** de Gerber; as pastas `v1`–`v7` ficam de fora (§3.3 C4).
- Nenhum arquivo inválido de datasheet no pacote.

### G3 — Bancada aprovada (`fase4_entrega/PLANO_TESTE_BANCADA.md`)

- Todos os passos do plano executados com **critério de aceite atendido**, hélices removidas.
- VBAT medido em 19,8 / 22,2 / 25,2 V com erro < 2 % (passo 10).
- Sobreposição de gate = 0 (passo 9); corrente linear < 2 % entre 5 e 30 A (passo 12);
  corte de link ≤ 200 ms (passo 15).
- **30 A e 15 A deixam de ser `[PREMISSA]` e viram medido** — ou o projeto para aqui.

### G4 — Voo

- PID de 6 eixos, comutação de 6 passos, ESP-NOW, proteções e failsafe com os critérios de
  aceite de `plano/WP4_FIRMWARE.md` §5 medidos, não simulados.
- Requisitos de `fase4_entrega/SEGURANCA_E_REGULATORIO.md` verificados por escrito.

---

## 6. Riscos e mitigação

Os seis que **mudam o plano** (não só a lista). Os demais estão em `fase4_entrega/RISCOS.md` e
em `plano/WP4_FIRMWARE.md` §7.1.

| # | Risco | Número | Mitigação | Por quê muda o plano |
|---|---|---:|---|---|
| R-1 | **Dead-time dos motores 3 e 4 tem piso de 400 ns** | 400 / 520 / 650 ns no IR2104 (p.1 e p.3 do datasheet), contra **518,750 ns** do RTL; a placa alimenta os drivers a **12 V**, abaixo dos 15 V de caracterização | medir o dead-time real em bancada e usar o valor medido; usar `Rgo`/`Rgf` já presentes no gerador para limitar `dI/dt`; se ficar abaixo do aceitável, mover os motores 3 e 4 para MCPWM | Nenhum ajuste de software fecha isso. O piso de 400 ns é 118,75 ns (22,89 %) menor que o do RTL — o firmware **sobrestima** a proteção no pior caso (`plano/WP4_FIRMWARE.md` RF-14) |
| R-2 | **Qg do MOSFET é 168 nC, não 40 nC** | 168 nC typ / 210 nC max; Qgs 53 nC, Qgd 34/51 nC | refazer o dimensionamento do resistor de gate e da dissipação do driver (E1) | O dimensionamento da Fase 0 está subdimensionado ~4×. Se o Qg subir mais, pode exigir outro driver — e aí a escolha do MOSFET (D-08) vem antes de E1 |
| R-3 | **309 pads de GND/VBAT_PROT sem via** | 309 de 309 a mais de 1,6 mm de uma via; 945 pads SMD só em F_Cu | stitch vias no layout novo (D-10), na **mesma** revisão de E3 | Mesmo com as 138 nets roteadas, a placa não tocaria os planos. A folga de 309 vias de stitch cabe em 352,4 cm² e **talvez não caiba** em 165 cm² — por isso D-03 tem de ser decidida junto com D-02 (`plano/WP5_DECISOES.md` §4) |
| R-4 | **138 nets sem cobre** | 138 de 202; são as 9 redes dos ESCs e todo o barramento de controle | Opção B (6 camadas + ~150×110 mm) | A Opção A (reescrever o roteador) **não fecha no prazo**: `kicad-cli` não existe nesta máquina, o A* próprio não termina em 240 s, e 187 nets de sinal em 2 camadas sobre 352,4 cm² é densidade inválida para produção — a placa passaria no checklist e falharia na bancada (`plano/WP1_ROTEAMENTO.md` §4) |
| R-5 | **30 A e 15 A nunca foram validados** | `[PREMISSA]`, sem nenhuma medição | G3: bancada antes de qualquer voo | Toda a largura de trilha foi dimensionada por modelo, não por ensaio. Se a bancada reprovar 30 A, o layout refaz |
| R-6 | **Regulatório e exposição do repositório** | repo **público** com licença MIT, 3 commits no remoto e commits locais à frente não enviados | decidir D-06 (privado agora, se não foi intencional) e cumprir `fase4_entrega/SEGURANCA_E_REGULATORIO.md` antes do voo | D-06 é o item mais urgente em exposição do arquivo. Voar sem a checagem de registro/SISANT é irregularidade, não só risco |

Riscos técnicos que **não** mudam a ordem, mas mudam o firmware: RF-01/RF-02 (taxa do MCP3208
em 120 %/240 % do datasheet e ausência de amostragem simultânea), RF-03 (sem corte de gate por
software), RF-04 (sem watchdog externo), RF-07 (mapa de pinos divergente), RF-09 (SPI a 115,2 %
da largura de banda a 10 MHz). Fonte: `plano/WP4_FIRMWARE.md` §7.1.

---

## 7. Decisões pendentes

As 15 decisões, com opção, recomendação e detalhe, estão em **`plano/WP5_DECISOES.md`**
(`grep -cE '^\| \*\*D-[0-9]+\*\*' plano/WP5_DECISOES.md` → **15**; commit a7e4d35 criou a D-15).
Quatro são bloqueantes hoje: **D-01, D-02, D-06, D-08**. Duas são emergência de segurança:
**D-07** (failsafe e watchdog) e **D-13** (corte por software).

A **D-15 — fusível/e-fuse de entrada** (recomendação A: fusível 30 A 1206, US$ 0,30 / R$ 4,93
`[MEDIDO, orcamento/ORCAMENTO.md linha 89]`) é **trabalho de hardware**: acrescentar 1 footprint de
2 pinos no polo positivo do VBAT. Como peça de layout, ela entra **na mesma revisão de E3** que
empacota a D-10 e a D-13 (§4, E3) e é conferida pelo gate **G1/A8** junto com os keepouts.

### As 3 que mais destravam

| Ordem | Decisão | Recomendação do WP5 | O que ela destrava |
|---:|---|---|---|
| 1º | **D-08 — Part numbers finais** | A — fechar os 5 blocos críticos primeiro | D-11 (Qg real depende do MOSFET), D-09 (custo real do INA240 define se troca) e D-14 (nacional × importação precisa de preço real). Uma decisão, quatro desbloqueios. Sem isso, 37 itens seguem `[EST]` e 0 de 43 tem disponibilidade. |
| 2º | **D-02 + D-03 — Roteamento e tamanho** | B — 6 camadas + ~150×110 mm (as duas no mesmo dia) | D-04 (quantas placas encomendar), o custo do PCB e D-10 (se 309 vias de stitch cabem). Libera a única coisa que realmente trava: gerar um Gerber que fecha. |
| 3º | **D-01 — Firmware dentro ou fora do escopo** | B — firmware de bancada (160 h) | Define se o projeto é uma placa ou um drone. Enquanto a resposta não vem, M0–M6 está parado, e é ele que transforma a placa em algo testado. |

**Não podem esperar muito:** D-06 (repo público) e D-07 + D-13 (segurança de voo).

---

## 8. O que não pode ser prometido

1. **Nada aqui garante que a placa vai funcionar.** Nenhum ensaio de bancada foi executado. Os
   limites de 30 A e 15 A são `[PREMISSA]` desde a Fase 0.
2. **Nenhum número deste documento garante voo.** O caminho até voar tem 320 h `[EST]` de
   firmware que não começou, mais uma bancada que nunca rodou, mais a checagem regulatória.
3. **Nenhuma medição de bancada foi feita nesta máquina.** A pendência térmica, de EMI, de
   dead-time sob carga e a verificação experimental do ganho da cadeia de corrente estão todas
   fora do escopo desta máquina (`plano/WP3_PREMISSAS_DATASHEETS.md` §5.3).
4. **A fração de área com cobre, o número exato de chamadas ao A\* e o throughput do MCP3208 a
   3,3 V são NÃO DETERMINADOS** — e nenhum deles está substituído por estimativa neste
   documento (`plano/WP1_ROTEAMENTO.md` §7; `plano/WP4_FIRMWARE.md` RF-06).
5. **A2 não é afirmação sobre a v7.** O número 12 vem da v6 e a v7 mudou de netlist; medir
   exigiria isolar o bloco de verificação do `fase3_pcb/rota_v7.py`, o que não foi feito. O
   mesmo vale para o alvo A3, cuja única medição (0) é da v6.
6. **Este documento não substitui nenhum dos cinco WPs.** Ele dá a ordem; o detalhe — com o
   comando, a saída e a ressalva — está em `plano/WP1_ROTEAMENTO.md`,
   `plano/WP2_FABRICACAO.md`, `plano/WP3_PREMISSAS_DATASHEETS.md`, `plano/WP4_FIRMWARE.md` e
   `plano/WP5_DECISOES.md`.

---

## Apêndice — documentos deste plano

| Documento | Papel |
|---|---|
| `plano/WP1_ROTEAMENTO.md` | medição do layout, estratégia de fechamento, critério de aceite da v8 |
| `plano/WP2_FABRICACAO.md` | 11 artefatos de fabricação, naming dos Gerbers, BOM, checklist da fab |
| `plano/WP3_PREMISSAS_DATASHEETS.md` | P-01..P-15, o que foi refutado e o que segue sem lastro |
| `plano/WP4_FIRMWARE.md` | inventário de software, escopo mínimo de 14 módulos, riscos de firmware |
| `plano/WP5_DECISOES.md` | D-01..D-15 com opções A/B/C e recomendação |
| `fase4_entrega/PLANO_TESTE_BANCADA.md` | instrumentos, ensaios e critérios de aceite da bancada (G3) |
| `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` | ordem de solda e cuidados de montagem (E5) |
| `fase4_entrega/RISCOS.md` | matriz severidade × probabilidade, mitigação e detecção |
| `fase4_entrega/SEGURANCA_E_REGULATORIO.md` | segurança elétrica e requisitos regulatórios brasileiros (E10) |
| `fase4_entrega/ANALISE_WIFI_CONTROLE.md` | orçamento do link de controle (V10) |
| `orcamento/ORCAMENTO.md` | cenários nacional e importação, 43 itens |
| `fase0_especificacao/FASE0_ESPECIFICACAO.md` | origem das premissas P-01..P-15 e dos limites de 30 A/15 A |

*Documento gerado em 2026-09-28 por consolidação das cinco auditorias. Nenhum número foi
introduzido aqui sem fonte; todos os caminhos citados foram conferidos com `test -e`.*

---

## Correções round 2 (2026-09-28)

Seis defeitos apontados por verificador de comando, corrigidos neste round. **Nenhum número
existente foi alterado** — os 21 números-chave do documento continuam os mesmos.

| # | Defeito | Correção | Verificação |
|---|---|---|---|
| 1 | 🔴 Contagem de decisões desatualizada (14) em três pontos | §1 linha "Decisões pendentes" → **15 (D-01..D-15)**; §7 → "As **15** decisões"; apêndice → "D-01..D-15"; E0 → "as outras **11** decisões vêm depois" | `grep -cE '^\| \*\*D-[0-9]+\*\*' plano/WP5_DECISOES.md` → **15** |
| 2 | 🔴 D-15 sem dono | A D-15 (fusível 30 A 1206) entrou como item **(c)** do pacote único de correções de layout da **E3**, ao lado da D-10 e da D-13, e é citada na §7 | `plano/WP5_DECISOES.md` §3.15; `orcamento/ORCAMENTO.md` linha 89 |
| 3 | 🔴 Keepouts sem dono nem verificação | **(a)** item **(d)** da E3: definir os keepouts de potência e de sinal no gerador; **(b)** critério **A8** no gate G1: `grep -c "rule_area" fase3_pcb/v7/v7_drone.kicad_pcb` → hoje **0**, tem de dar **> 0** na v8. A1..A7 já ocupavam os IDs, então A8 não colide; o gate passa de 7 para **8** linhas | `grep -c "rule_area" fase3_pcb/v7/v7_drone.kicad_pcb` → **0**; `plano/WP1_ROTEAMENTO.md` §3.3 |
| 4 | 🟠 D-09 sem dono na revisão de layout | Item **(e)** da E3: D-09 é fechada **antes** de começar. Com a recomendação A (manter os 12× INA240A2) **o respin é desnecessário**; se você escolher B (INA181/INA241), a troca entra no mesmo pacote de E3 como quinto item | `plano/WP5_DECISOES.md` §3.9 |
| 5 | 🟠 G3/G4 não verificáveis por comando | §5 agora diz "verificável por comando **ou por medição em bancada/voo**" e separa explicitamente: **G1 e G2 de comando**, **G3 e G4 de medição** — com a nota de que nenhuma das duas medições foi feita | `fase4_entrega/PLANO_TESTE_BANCADA.md`; §8.1 |
| 6 | 🟡 Risco de dupla contagem em E0.1 | A linha E0.1 diz que as **1,5 h já estão contidas nos 30,0 h de E4** (F4 = 0,5 h + F7 = 1 h, §2) e que somar as duas seria contar o mesmo trabalho duas vezes | `plano/WP2_FABRICACAO.md` §1 itens 2 e 6 |

**Preservado sem alteração:** a ordem das seções, o sumário executivo, os 21 números-chave
(138, 309, 202/203, 220,10×160,10, 10, 319, 1.093, 30,0/34,0 h, 320 h, 6❌/3⚠️/2✅, Qg 168/210,
DT 400/520/650, 518,750 ns, R$ 1.706, R$ 1.354, 37/43, 12 V vs 15 V, 4× MCP3208, 2× MCPWM) e a
ressalva de que **nada foi validado em bancada**. Nenhum WP1..WP5, `plano/DO_PROJETO.md` ou
`prd.json` foi tocado.

---

## Correções round 3 (2026-09-28)

Defeito único, introduzido pelo round 2. **Nenhum número foi alterado** — os 21 números-chave, os
6 defeitos do round 2 e a ressalva de nada validado em bancada seguem como estavam.

| # | Defeito | Correção | Verificação |
|---|---|---|---|
| 7 | 🔴 E3(d) citava `fase3_pcb/gera_pcb_v8.py` como se fosse insumo, e a nota de `test -e` afirmava incondicionalmente que "Todos os outros caminhos citados existem" — os dois falsos | (a) **E3(d)** passa a dizer, com a mesma convenção já usada para o outro artefato, que o `fase3_pcb/gera_pcb_v8.py` **ainda não existe** e é o gerador da v8 **a criar copiando `fase3_pcb/gera_pcb_v7.py`**, que existe; (b) a nota do gate G1 passa a listar **os dois** artefatos ausentes, ambos a produzir, e a afirmação "todos os outros existem" ficou restrita aos 24 que existem | `ls fase3_pcb/gera_pcb_v*.py` → **v1 a v7**, `gera_pcb_v8.py` não está na lista; saída real do `test -e` abaixo |

**Saída real do `test -e` sobre os 26 caminhos citados no documento** (extração por
`grep -oE '`[^`]*\/[^`]*`'` filtrada para artefatos e diretórios; os dois `grep -c` da tabela do
round 2 foram descartados por serem comandos, não caminhos). **AUSENTE = a produzir:**

```
EXISTE   datasheets/
EXISTE   fase0_especificacao/dimensionamento_fase0_saida_v2.txt
EXISTE   fase0_especificacao/FASE0_ESPECIFICACAO.md
EXISTE   fase0_especificacao/verifica_limites_saida_v4.txt
EXISTE   fase2_simulacao/verilog/RELATORIO_VERILOG.md
EXISTE   fase3_pcb/calc_trilhas_vias_saida.txt
EXISTE   fase3_pcb/gera_pcb_v7.py
AUSENTE  fase3_pcb/gera_pcb_v8.py            <- a produzir (copia de gera_pcb_v7.py, item E3(d))
EXISTE   fase3_pcb/rota_v7.py
EXISTE   fase3_pcb/v6/verificacao_v6.txt
EXISTE   fase3_pcb/v7/v7_drone.kicad_pcb
EXISTE   fase3_pcb/v8/
AUSENTE  fase3_pcb/v8/verificacao_v8.txt     <- a produzir (gate G1)
EXISTE   fase4_entrega/ANALISE_WIFI_CONTROLE.md
EXISTE   fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md
EXISTE   fase4_entrega/PLANO_TESTE_BANCADA.md
EXISTE   fase4_entrega/RISCOS.md
EXISTE   fase4_entrega/SEGURANCA_E_REGULATORIO.md
EXISTE   orcamento/ORCAMENTO.md
EXISTE   plano/DO_PROJETO.md
EXISTE   plano/mede_v7_wp1.py
EXISTE   plano/WP1_ROTEAMENTO.md
EXISTE   plano/WP2_FABRICACAO.md
EXISTE   plano/WP3_PREMISSAS_DATASHEETS.md
EXISTE   plano/WP4_FIRMWARE.md
EXISTE   plano/WP5_DECISOES.md
existem=24  ausentes=2  total=26
```

Os dois ausentes são coerentes entre si: ambos são produtos da v8, nenhum é insumo. Nenhum WP1..WP5,
`plano/DO_PROJETO.md`, `README.md` ou `prd.json` foi tocado; nada foi enviado para fora.
