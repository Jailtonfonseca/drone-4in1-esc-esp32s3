# DECISÕES TOMADAS — registro das 15 decisões delegadas

> ## ⚠️ AVISO
> **Decisões tomadas por delegação do Jailton em 2026-09-28. Qualquer uma pode ser revertida; as que mudam layout custam um redesenho.**

> **Como este arquivo foi feito.** O Jailton delegou a escolha pelo critério *"faça da maneira mais garantida"*.
> Cada uma das 15 decisões abaixo foi resolvida pela **Opção recomendada do agente de auditoria**, ou seja,
> a alternativa que o próprio `plano/WP5_DECISOES.md` marca com ✅. **Nenhuma escolha de peça, de preço ou de
> prazo foi inventada**: onde não houve fonte, o item está marcado `PENDENTE`.
> **Origem de cada argumento:** `plano/WP5_DECISOES.md` — a seção está indicada em cada bloco, junto do
> arquivo de onde o número veio.
> **Nada foi editado** em `plano/WP5_DECISOES.md`, `PLANO_FINAL.md`, `orcamento/ORCAMENTO.md`,
> `orcamento/orcamento_detalhado.csv` ou `fase0_especificacao/`. Este arquivo é novo e é apenas o registro
> do que foi decidido.

**Convenção de etiqueta usada aqui, herdada do WP5:**
`[MEDIDO]` = número lido de arquivo do projeto ou de comando executado nesta máquina ·
`[DATASHEET]` = número de datasheet, com arquivo · `[CALC]` = conta feita a partir de números marcados ·
`[EST]` = estimativa do agente, **não** medição.

**Consequência prática do conjunto:** as 15 decisões que mudam a placa (D-02, D-03, D-04, D-09, D-10, D-11,
D-12, D-13, D-15) entram **na mesma revisão** (v8). O custo marginal de layout de decidir todas juntas é ≈ 0;
decidir uma depois do Gerber pago é um redesenho pago duas vezes.

---

## Índice

| # | Decisão | Opção | Custo | O que custa reverter |
|---|---|---|---|---|
| [D-01](#d-01--firmware-dentro-ou-fora-do-escopo) | Firmware no escopo | **B** | 320 h [EST] | Nada físico — só o backlog de firmware |
| [D-02](#d-02--roteamento-opção-a-ou-opção-b) | Roteamento | **B** — 6 camadas + placa menor | 2–3 semanas [EST] | 🔴 **Redesenho completo do layout** |
| [D-03](#d-03--tamanho-da-placa) | Tamanho | **B** — ~150×110 mm | — | 🔴 **Redesenho + recota de PCB** |
| [D-04](#d-04--número-de-placas) | Nº de placas | **A** — 1 | ~1/5 do lote | Nada físico — só custo de placa extra |
| [D-05](#d-05--montagem-caseira-ou-pcba) | Montagem | **A** — caseira | R$ 0 de setup | Nada físico — só trabalho manual |
| [D-06](#d-06--repo-do-github) | Repo | **B** — público MIT (como está) | US$ 0 | 1 comando: `gh repo edit --visibility private` |
| [D-07](#d-07--failsafe-e-watchdog-externo) | Failsafe + watchdog | **A** | ~US$ 0,90 [EST] | 1 pino e 1 CI a remover do layout |
| [D-08](#d-08--part-numbers-finais) | Part numbers | **A** — fechar os blocos críticos | 2–4 h de pesquisa [EST] | Nada físico |
| [D-09](#d-09--trocar-12-ina240-por-ina181ina241) | Amp de corrente | **A** — manter 12× INA240A2 | US$ 31,20 [EST] | 🔴 **Respin de layout** (footprint muda) |
| [D-10](#d-10--os-309-pads-de-plano-sem-via) | Stitch de vias | **A** — corrigir | +309 vias [EST] | Nada físico |
| [D-11](#d-11--premissa-qg-40--168-nc) | Dimensionamento de gate drive | **A** — 168/210 nC | 4–6 h [EST] | Nada físico |
| [D-12](#d-12--adc-4-mcp3208-ou-2-ads7953) | ADC | **B** — 2× ADS7953 | +US$ 5,60 [EST] | 🔴 **Respin de layout** |
| [D-13](#d-13--o-sd-dos-12-ir2104) | Shutdown dos drivers | **A** — 1 GPIO | ~0 h [EST] | 1 pino e 1 net a remover |
| [D-14](#d-14--compra-nacional-ou-importação) | Compra | **A** — nacional | R$ 1.706 [EST] | Nada físico |
| [D-15](#d-15--fusívelefuse-de-entrada) | Proteção de entrada | **A** — fusível 30 A 1206 | US$ 0,30 [EST] | Nada físico — 2 pinos |

🔴 = reverter custa redesenho de layout.

---

## D-01 — Firmware dentro ou fora do escopo

**Decidido: B — o firmware de bancada entra no escopo.** Módulos M0–M6 + M10 + M11.

**Por que (argumento de segurança).** A Opção A entregava placa e deixava 320 h [EST] de firmware sem dono;
o resultado seria um repositório chamado `drone-4in1-esc-esp32s3` cujo conteúdo é uma placa. Isso não é risco
técnico, é **risco de expectativa**: a entrega seria aceita como "projeto" e o dono não teria um drone.
A Opção C (firmware completo, 320 h) foi descartada porque **nenhuma validação de bancada foi feita até hoje**
[MEDIDO — `fase4_entrega/RISCOS.md` §5]: começar pelo fim põe 8 semanas de trabalho em cima de um layout que
tem 138 nets sem cobre [MEDIDO, `plano/WP1_ROTEAMENTO.md` §1.5]. A Opção B é o meio-termo que não abandona a
decisão já registrada por escrito — `PROMPT_AGENTE_DRONE.md` item 6 e
`fase0_especificacao/FASE0_ESPECIFICACAO.md` §9.6 tiram a lógica de voo do escopo, e B respeita isso.
**Origem:** `plano/WP5_DECISOES.md` §3.1. Custo: 320 h [EST] (160 h de PID/comutação + 160 h de firmware
completo, o que fecha a execução dos passos 9, 10, 11, 12, 14 e 15 de `fase4_entrega/PLANO_TESTE_BANCADA.md`).

**O que deixa de ser possível.** Não há mais entrega "placa + especificação" com o firmware fora. O mapa de pinos
do firmware deixa de ser adiável: **nenhuma linha de firmware pode ser escrita antes de D-02/D-03/D-10/D-13
fecharem**, porque o mapa de pinos diverge do layout nos motores 2, 3 e 4 [WP4 RF-07].

**Como reverter.** Decisão de escopo, zero rastro físico. Volta ao estado do briefing: apaga-se o backlog de
firmware do plano e o projeto passa a entregar placa + especificação. Não toca layout nem BOM.

---

## D-02 — Roteamento: Opção A ou Opção B

**Decidido: B — 6 camadas e placa reduzida.** A Opção A (reescrever o autorouter e manter 220×160 mm / 4 camadas)
foi descartada.

**Por que (argumento de segurança).** A Opção A mantém a densidade que já foi **medida como inválida para
produção**: 187 nets de sinal distribuidas em 2 camadas sobre 352,4 cm² [MEDIDO, `plano/WP1_ROTEAMENTO.md` §4],
carregando 319 footprints, 202 nets e 1093 pads. Mesmo com um roteador perfeito, a placa passaria no checklist
e falharia na bancada. Some-se o pior achado de EMC do projeto: a v7 tem **zero keepouts** [MEDIDO,
`grep -c "rule_area\|keepout"` = 0], ou seja, os setores de potência (VBAT, 30 A) e os de sinal de alta taxa
estão **no mesmo plano de cobre**. As 6 camadas separam os dois setores, e a redução de área derruba o custo de
cobre e o peso — em quadcopter, 100 g de placa é diferença de tempo de voo.
**Origem:** `plano/WP5_DECISOES.md` §3.2. A opção C (4 camadas partindo o sistema em 2 ESCs por placa) foi
descartada por dobrar placas, conectores e firmware — muda a mecânica do quad.

**O que deixa de ser possível.** As 202 nets e 319 footprints da v7 passam a ser **insumo, não entrega**: a v8 é
um redesenho, não um ajuste. Também deixa de ser possível cotar a placa pelo preço de 4 camadas com 2 oz
em 220×160 (R$ 359–770 [EST] para 5 unidades, `orcamento/ORCAMENTO.md` §1).

**Como reverter.** Só antes do Gerber: reconstruir a v7 em 4 camadas e rodar de novo
`fase3_pcb/rota_v7.py` (o WP1 registra que o medido é "não termina em 240 s", não "não termina nunca").
Depois que o Gerber for pago, reverter é um redesenho pago duas vezes.

---

## D-03 — Tamanho da placa

**Decidido: B — reduzir para ~150×110 mm.**

**Por que (argumento de segurança).** O `orcamento/ORCAMENTO.md` §6 já diz, textualmente, que
*"se a versão final couber em ~120×80 mm, a fabricação cai de faixa de US$ 70-150 para poucos dólares por
lote de 5"* e que *"antes de fechar compra, vale terminar o roteamento e recotar"*. Além disso, a redução de
área é o que torna a Opção B do D-02 **fisicamente honesta**: 6 camadas numa placa de 352,4 cm² seria
desperdício de cobre. Manter 220×160 [MEDIDO] é o maior alavanca de custo do projeto, na palavras do próprio
orçamento, e o maior peso para um quad.
**Origem:** `plano/WP5_DECISOES.md` §3.3. A opção C (~180×130 mm) foi descartada: meio termo raramente é a boa
opção, e nenhuma fecha rápido.

**O que deixa de ser possível.** Não dá mais para encomendar no contorno de 220×160. Posições de blocos mudam
(o gerador é `fase3_pcb/gera_pcb_v7.py`). A faixa de custo de PCB [EST] do orçamento se torna inválida e precisa
de recotação com Gerber real.

**Como reverter.** É a decisão mais barata de reverter **enquanto** a v8 não existir: basta manter o contorno
antigo no gerador. Depois do Gerber, é recotar e pagar a diferença.

---

## D-04 — Número de placas

**Decidido: A — 1 placa, para bring-up.**

**Por que (argumento de segurança).** Encomendar 5 placas de um layout que tem **138 nets com pad e zero trilha**
[MEDIDO] e **309 pads de plano a mais de 1,6 mm de uma via** [MEDIDO] é comprar 4 placas para trincheira.
Um lote de 5 só faz sentido depois que a v8 passar no critério de aceite do `plano/WP1_ROTEAMENTO.md` §5 — o
mesmo raciocínio que levou às D-02, D-03 e D-10 a serem resolvidas primeiro.
**Origem:** `plano/WP5_DECISOES.md` §3.4.

**O que deixa de ser possível.** Não há redundância: se a v8 vier com defeito de fabricação, espera-se o retrabalho
e a espera de um novo lote. Também não há como fazer teste de lote.

**Como reverter.** Nenhuma ação é necessária agora. O caminho é o oposto: quando a v8 passar no critério de
aceite,(reordered as 5 (o `orcamento/ORCAMENTO.md` §5.1 já diz que subir o Gerber no site do fabricante **sem
encomendar** dá a cotação real).

---

## D-05 — Montagem: caseira ou PCBA

**Decidido: A — montagem caseira na primeira placa.** O caminho C (PCBA dos SMD + THT manual) fica **registrado
como o plano para a série**, quando houver 5 placas.

**Por que (argumento de segurança).** Pagar setup de montagem para uma placa que talvez nem roteie é desperdício,
e o projeto está em **uma placa de bring-up** com 138 nets sem cobre [MEDIDO]. Além disso, XT60 e MR30 são
**through-hole** [EST, engenharia — o `orcamento/orcamento_detalhado.csv` não diz nada sobre tecnologia de
montagem; ver a ressalva de lastro em `plano/WP5_DECISOES.md` §3.5], e a montagem da JLCPCB não cobre a parte
que mais se sente. A ordem de solda caseira já está escrita em
`fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md`, o que é o que torna a Opção A executável e não apenas barata.
**Origem:** `plano/WP5_DECISOES.md` §3.5. Custo: R$ 0 de setup; 319 footprints [MEDIDO, WP2 §4.3] de trabalho
manual.

**O que deixa de ser possível.** Não há placa returning testada de fábrica. Os 319 footprints viram trabalho de
bancada, e o custo da bancada (ferro/hot-air, termopar) continua fora do `orcamento/ORCAMENTO.md` §5.6.

**Como reverter.** Nada a reverter na placa — a montagem é a última etapa. Se mudar de ideia: marcar o item 3 da
§1 do `plano/WP2_FABRICACAO.md` (CPL, 0,5 h [EST]) como necessário e enviar BOM + CPL para a JLCPCB, com
+US$ 41 [MEDIDO, `orcamento/ORCAMENTO.md` §1] de setup, lembrando que os conectores continuam manuais.

---

## D-06 — Repo do GitHub

**Decidido: manter público com licença MIT, como já está. Não foi mexido em nada.**

**Por que (argumento de segurança).** O estado verificado nesta máquina é público, e mudar visibilidade é
operação externa que depende de confirmação. O briefing da missão diz que o repo "já criado e privado", mas o
comando mede o contrário [MEDIDO]:

```console
$ gh repo view Jailtonfonseca/drone-4in1-esc-esp32s3 --json isPrivate,visibility
{"isPrivate":false,"visibility":"PUBLIC"}
```

Mantendo o estado atual, nada é publicado de novo e nada é escondido; inverter o sentido (baixar para privado)
é o passo reverso imediato de 1 comando.
**Origem:** `plano/WP5_DECISOES.md` §3.6.

**O que deixa de ser possível.** Esquema, netlist e medições de hardware permanecem sob MIT — que é **permissão de
uso, modificação e redistribuição, não ausência de garantia**. Se o Jailton quiser que não fiquem públicos, esta é
a decisão a reverter e é a mais urgente do arquivo em termos de exposição.

**Como reverter.** `gh repo edit --visibility private` (o token já tem escopo `repo` [MEDIDO]). Custo: US$ 0.
Observação do WP5: lowering a visibilidade não remove o conteúdo do cache de terceiros se já houver push.

---

## D-07 — Failsafe 200 ms + watchdog externo

**Decidido: A — failsafe de 200 ms em 10 quadros consecutivos a 50 Hz, e watchdog externo SIM.**

**Por que (argumento de segurança).** O prazo é o que decide: a queda em 200 ms é **19,62 cm / 1,96 m/s**
[MEDIDO, `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §2.4]. Em 100 ms o corte é curto demais e o risco de corte
falso sobe; em 500 ms a queda é **122,62 cm e 4,91 m/s** — a própria fonte diz *"para 500 ms já são 1,23 m — o
que já quebra hélice e braço"*, então a Opção C é fisicamente indefensável. "10 quadros consecutivos" em vez de
"um buraco de tempo" evita disparo por retry longo [EST].
O **watchdog externo** cobre o cenário que o ESP32-S3 sozinho **não** cobre: **firmware travado**. O TWDT
interno morre junto com o firmware — não é defesa. Hoje `WD_FEED` aparece em exatamente 2 lugares (pad 25 do MCU
e `TP_WD`) e não existe CI supervisor na placa [MEDIDO, WP4 RF-04]: a mitigação declarada em
`fase4_entrega/RISCOS.md` R-08 nunca foi implementada.
**Origem:** `plano/WP5_DECISOES.md` §3.7 (7a e 7b). Custo: ~US$ 0,90 [EST, é o valor do orçamento para a peça
genérica] e **1 CI de 8 pinos** (SOIC-8) + 1 pino no layout.

**O que deixa de ser possível.** O watchdog precisa entrar na v8. Se o mapa de pinos ficar sem GPIO livre, a
Opção C da D-13 (puxar `SD` pelo `/RESET` aberto-dreno do watchdog) passa a ser o caminho — e ela
**não dá para desligar os drivers em teste de bancada sem parar de alimentar o watchdog**. Ver
`orcamento/COTACAO_REAL.md`: a peça real cotada (TPS3813K33DBVR) é **SOT-23-6, não SOIC-8** — footprint novo.

**Como reverter.** É a decisão de menor custo de reversão de todo o arquivo: 1 CI de 6 pinos e 1 pino saem da
v8, e o failsafe volta a depender só do software (que é o estado de hoje, com R-04/R-08 abertos).

---

## D-08 — Part numbers finais para cotação real

**Decidido: A — fechar os 5 blocos críticos primeiro** (MOSFET, gate driver, amp de corrente, bucks, shunt),
na ordem MOSFET → amp → bucks, pelo critério "faça da maneira mais garantida".

**Por que (argumento de segurança).** Sem part number não há cotação, e 37 das 43 linhas do orçamento eram
`[EST]` [MEDIDO, `orcamento/ORCAMENTO.md` §1]. Fechar tudo de uma vez (Opção B) arrisca travar o pedido inteiro
num único item sem estoque; não fechar (Opção C) mantém a lista em `[EST]` e compra peça diferente da do layout.
A ordem não é estética: **Qg é propriedade do MOSFET e o MOSFET ainda não estava escolhido** — por isso D-11
também depende de D-08.
**Origem:** `plano/WP5_DECISOES.md` §3.8.

**O que deixa de ser possível.** Enquanto os 37 itens restantes não forem fechados, a lista de compra não está
pronta — mas os itens de baixo valor não travam o início do trabalho.

**Como reverter.** Nada físico: é uma ordem de trabalho. Na prática, a execução está em
`orcamento/BOM_FABRICACAO.csv` (43 linhas, com `status` por item).

---

## D-09 — Trocar 12× INA240 por INA181/INA241

**Decidido: A — manter 12× INA240A2.** Nenhuma troca.

**Por que (argumento de segurança).** O ganho de **50 V/V seleciona a variante A2** [DATASHEET,
`datasheets/ina240_ti_sbos662.pdf` p.1/p.3/p.5] — estoque de A1/A3/A4 invalida o ganho. O CMRR de **93 dB a
20 kHz** [DATASHEET, p.5] é exatamente a **folga** que protege a leitura de corrente com PWM a 20 kHz; trocar
gasta essa folga. E trocar peça por causa de um `[EST]` que ainda não foi cotado é **trocar no escuro** — a
cotação real já está em `orcamento/BOM_FABRICACAO.csv`.
**Origem:** `plano/WP5_DECISOES.md` §3.9. Custo de manter: US$ 31,20 [EST] (o item mais caro do catálogo
estimado). A Opção C (amp simples + shunt low-side) foi descartada: muda o esquema inteiro.

**O que deixa de ser possível.** Os ~31 % do orçamento estimado ficam no INA240. Se a cotação real vier muito
acima, a alternativa B (INA181/INA241) continua de porta — mas **exige respin de layout**, porque o footprint
muda, e o projeto já tem um respin previsto por D-02, D-10, D-12 e D-13. **Não abra um quinto.**

**Como reverter.** Trocar o MPN no BOM **e** refazer a biblioteca de footprints do bloco CORRENTE. Custo:
respin de layout. Observação de cotação: a peça real (`INA240A2DR`, SOIC-8) **não tem pad térmico**, enquanto a
lista pede `SOIC-8-1EP` — ver `orcamento/COTACAO_REAL.md`.

---

## D-10 — Os 309 pads de plano sem via

**Decidido: A — corrigir com stitch de vias em cada pad.** A Opção C (aceitar sem via) é bug de layout, não
opção de engenharia.

**Por que (argumento de segurança).** Lido literalmente: os 309 pads de retorno e de alimentação (207 de GND +
102 de VBAT_PROT) estão a mais de 1,6 mm de uma via [MEDIDO, `plano/WP1_ROTEAMENTO.md` §3.2]. São 945 pads
SMD que só estão em F_Cu, e um plano em In1_Cu só se alcança por via. **Mesmo que as 138 nets de sinal fossem
roteadas perfeitamente, os 309 pads não tocariam seus planos** — a placa não funcionaria.
**Origem:** `plano/WP5_DECISOES.md` §3.10. Custo: +309 vias [EST] a ~0,15 mm² cada [CALC].

**O que deixa de ser possível.** A densidade de furos sobe e compete com as 138 nets sem cobre do D-02. A Opção B
(estrelas de cobre entre os pads) fica reservada: se a placa ficar 150×110 mm [D-03], 309 vias individuais podem
não caber, e aí o stitch vira "estrelas + vias só nos pads de corrente alta". **A e B decidem juntas com D-02 e D-03.**

**Como reverter.** Nada a reverter do ponto de vista de compra: não é peça. É geometria do layout, gerada por
script. O script pode ser reescrito sem tocar em nada mais.

---

## D-11 — Premissa Qg: 40 nC → 168 nC

**Decidido: SIM — corrigir o dimensionamento de gate drive**, adotando Qg = 168 nC (typ) / 210 nC (max) e
refazendo os cálculos da Fase 0.

**Por que (argumento de segurança).** A premissa de 40 nC da Fase 0 é **~4× otimista** contra o datasheet do FET
escolhido [DATASHEET — `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` p.1 Table 1:
`QG(0V..10V) = 168 nC`]. O que o dimensionamento calcula é o **tempo** de comutação, `t = Qg/I`; com Qg = 168 nC
e o IR2104 entregando `IO+/− = 130/270 mA` [DATASHEET, `datasheets/ir2104_infineon_datasheet.pdf` p.1]:

```console
$ python3 -c "
Qg=168e-9
for I in (0.130,0.270):
    t=Qg/I
    print('Qg=168 nC, I=%.0f mA -> t=%.3f us ; dV/dt(10 V)=%.4f V/ns' % (I*1000, t*1e6, 10/(t*1e-9)/1e9))"
Qg=168 nC, I=130 mA -> t=1.292 us ; dV/dt(10 V)=0.0077 V/ns
Qg=168 nC, I=270 mA -> t=0.622 us ; dV/dt(10 V)=0.0161 V/ns
```

Manter 40 nC significa **perda de comutação e consumo de bateria subestimados em ~4×** — em projeto de missão isso
é erro de dimensionamento, não detalhe. Observação ligada à escolha do FET: o `RDS(on)` sobe de 1,7 mΩ (max a
10 V) para **2,2 mΩ (max a 6 V)** [DATASHEET, p.4], então **10 V de gate drive é o piso** — qualquer FET
escolhido com driver mais fraco cai no pior caso.
**Origem:** `plano/WP5_DECISOES.md` §3.11. Custo: 4–6 h [EST] para reexecutar
`fase0_especificacao/dimensionamento_fase0_saida_v2.txt` e `fase0_especificacao/verifica_limites_saida_v4.txt`
(ambos existem [MEDIDO]). **Nota de sequência:** a ordem correta é D-08 (escolher MOSFET) → D-11 → D-08 de novo
(cotar). Fazer D-11 com o Qg de uma peça de referência seria trocar um `[EST]` por outro `[EST]`.

**O que deixa de ser possível.** A saída v2/v4 da Fase 0 e o texto de dimensionamento da D-05 (BOM) não podem ser
usados como estão. A quiescência do IR2104 também precisa sair de 2,5 mA [PREMISSA] para 0,325 mA [DATASHEET,
p.3: IQCC 270 µA + IQBS 55 µA].

**Como reverter.** Nenhuma peça muda. Reverter é rodar de novo o dimensionamento com 40 nC — o que reintroduz o
erro de 4×.Decisão de segurança: **não recomendada**.

---

## D-12 — ADC: 4× MCP3208 ou 2× ADS7953

**Decidido: B — trocar por 2× ADS7953** no lugar de 4× MCP3208.

**Por que (argumento de segurança).** Dois riscos 🔴 Críticos que nenhum software resolve. **RF-01:** 6 canais por
CI × 20 kHz = 120 ksps por CI, e o MCP3208 entrega **100 ksps a 5 V e 50 ksps a 2,7 V** [DATASHEET,
`datasheets/mcp3208_microchip_ds21298e.pdf`] — isso é **120 % do datasheet a 5 V e 240 % a 2,7 V**. **RF-02:**
o MCP3208 **multiplexa** (*"programmable to provide four pseudo-differential input pairs or eight single-ended
inputs"*, p.1); a Fase 0 §4.2 vendeu amostragem **simultânea** das 3 fases e com 4× MCP3208 isso **não se
materializa** — as 3 fases são lidas em 3 instantes diferentes. A escolha atual foi feita **por custo**
[`fase3_pcb/gera_pcb_v7.py` linhas 15–18] e é exatamente a que falha nos dois riscos.
**Origem:** `plano/WP5_DECISOES.md` §3.12. Custo: +US$ 5,60 [EST] (2× US$ 8,00 contra 4× US$ 2,60) — o melhor
preço de destravamento do arquivo. Como a v8 já vai ser feita por D-02, D-10 e D-13, o custo marginal de layout
é ≈ 0 se decidido agora.

**O que deixa de ser possível.** Sai o MCP3208 do BOM e do layout. A comutação sem sensor fica implementável.
**Atenção ao saldo:** o BOM original tinha **1** ADS7953; a decisão exige **2** — o 2º CI precisa entrar
(registrado em `orcamento/BOM_FABRICACAO.csv`, linha do ADC, na coluna `observacao_de_compra`).

**Como reverter.** Voltar a 4× MCP3208 exige refazer o layout do bloco ADC **e** reabrir RF-01/RF-02, que são
documentados como 🔴 Críticos. Reversão técnica possível, segurança ruim.

---

## D-13 — O `SD` dos 12 IR2104 vai para um GPIO?

**Decidido: A — rotar `SD` para 1 GPIO do ESP32-S3.**

**Por que (argumento de segurança).** Hoje `Rsd%s` vai de `SD%s` a `3V3`
[`fase3_pcb/gera_pcb_v7.py` linhas 238–239] e a rede `SD%s` **não chega a nenhum GPIO do MCU** [linhas 401–412,
`MCU_NETS`, sem nenhuma entrada `SDx`] [MEDIDO, `plano/WP4_FIRMWARE.md` RF-03]. Consequência direta:
**não existe instrução de firmware capaz de desligar os 12 IR2104.** O corte depende de zerar o duty — e a
semântica de repouso do RTL (`duty=0` → low-side ligado) **não é** a do IR2104 com `IN=0`: firmware escrito
contra o RTL pode deixar dois low-sides ligados. O `plano/WP4_FIRMWARE.md` §8 chama isso de *"a correção mais
barata e a mais séria"*. Sem isso não há failsafe por software — e sem failsafe por software não há failsafe de
verdade.
**Origem:** `plano/WP5_DECISOES.md` §3.13. Custo: ~0 h [EST] — 1 linha no gerador, +1 pino e +1 net.

**O que deixa de ser possível.** Consome 1 GPIO. Se o mapa ficar sem GPIO livre (RF-07 já diz que o mapa diverge),
o caminho é usar um dos 4 `ADC_CS` [MEDIDO: a v7 tem 4 CS nos pads 23, 15, 33, 34, enquanto a Fase 0 previa 1] —
isso é detalhe de layout, não de escopo. A Opção C (puxar `SD` pelo `/RESET` do watchdog externo) fica como plano B
de layout: protege contra firmware travado sem gastar GPIO, mas só existe se D-07b for aprovada e **não dá para
desligar os drivers em bancada sem parar de alimentar o watchdog**.

**Como reverter.** 1 linha no gerador volta a ligar `SD` em `3V3`; some 1 pino e 1 net da v8. Reverte o
benefício sem custo de layout relevante.

---

## D-14 — Compra nacional ou importação

**Decidido: A — compra nacional nesta iteração (R$ 1.706 [EST]); importação quando o volume justificar.**

**Por que (argumento de segurança).** Com D-04 = 1 placa, o ganho absoluto de importar é pequeno (R$ 1.354 contra
R$ 1.706 [MEDIDO, `orcamento/ORCAMENTO.md` §1 e §4]) e a espera de 3–6 semanas [MEDIDO, §6] atrasa todo o bench.
A observação decisive do próprio orçamento é que os cenários **empatam dentro da barra de erro** — banda de
R$ 1.448 a R$ 1.965 no nacional — ou seja, **a diferença real é tempo, não dinheiro**. Somando-se o risco de
alfândega e a divergência de imposto em até US$ 50 [MEDIDO, §5.4], a opção nacional é a mais garantida.
**Origem:** `plano/WP5_DECISOES.md` §3.14. A Opção C (misto) fica registrada como o plano da série: nacional na
1ª placa, importação nas 4 restantes.

**O que deixa de ser possível.** A compra nacional **diverge da montagem que vamos fazer** (peças diferentes das do
catálogo, e o markup real de ~3,2× ainda não foi medido peça a peça). Em compensação, chega em dias e sem
alfândega.

**Como reverter.** Nenhuma ação física: é uma escolha de fornecedor. Importar depois é permitido e é a Opção C.
Atenção operacional do WP5: *"BOM duplica indutores e capacitores de saída … Se for pedir direto do CSV, o pedido
vira 6 indutores e 12 capacitores"* — corrigir antes do pedido.

---

## D-15 — Fusível/e-fuse de entrada

**Decidido: A — fusível 30 A 1206 no polo positivo do VBAT.** A Opção B (e-fuse TPS2594x com enable por GPIO)
fica registrada como evolução de produção.

**Por que (argumento de segurança).** Esta é a **pergunta 11 da §11 da Fase 0**, que segue aberta [MEDIDO]. O
pack é de 6S com corrente de projeto na casa das dezenas de ampères e há TVS no BOM — mas **TVS não limita
corrente de falha: ele satura e queima**. As duas coisas resolvem problemas diferentes. Sem elemento em série,
qualquer falha de curcircuito é **destrutiva**, não um fusível de R$ 1. A Opção B é a resposta *melhor* em
engenharia e a resposta *certa* para produção (corte programável, I²t, OVP, telemetria), mas só faz sentido
depois que existir um e-fuse com cotação real — hoje a única fonte de preço é a própria linha do orçamento,
marcada `[EST]`.
**Origem:** `plano/WP5_DECISOES.md` §3.15. Custo: US$ 0,30 [EST] (R$ 4,93), 1 item, 0 GPIO, 0 net de sinal.
Cotação real da peça escolhida: ver `orcamento/BOM_FABRICACAO.csv`.

**O que deixa de ser possível.** O fusível **não é resetável**: um transiente, curto ou erro de montagem queima
o fusível e a placa vai para a bancada de qualquer jeito. Não há telemetria de corrente de falha, nem corte por
software — corte por software é assunto da D-13.

**Como reverter.** Nada a reverter agora: é um componente de 2 pinos que **não altera nenhuma net** e pode ser
tratado como "não comprado" sem consequência para o layout. Subir para a Opção B depois significa +1 CI de
4 pinos, +1 GPIO e o gate drive do corte no layout.

---

## O que estas 15 decisões **não** decidiram

Registrado para não haver dúvida depois:

- **Preço e estoque reais.** 29 das 43 linhas de `orcamento/BOM_FABRICACAO.csv` estão `CONFIRMADO` com URL e
  preço lidos nesta máquina; as outras continuam `PENDENTE`. **Nenhum número de preço, estoque ou prazo foi
  inventado** — ver `orcamento/COTACAO_REAL.md` para o registro de cada tentativa.
- **Custo de fabricação do PCB.** Exige Gerber no site do fabricante (`orcamento/ORCAMENTO.md` §5.1).
- **Lead time.** A fonte consultada não publica prazo de entrega por peça; a coluna `lead_time` do BOM diz isso
  explicitamente onde está preenchida.
- **O que o firmware faz em M0–M6.** Isso é D-01 já decidido, mas o conteúdo dos módulos ainda não foi escrito.
