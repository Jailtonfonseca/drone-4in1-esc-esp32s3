# WP5 — Registro das decisões que só o Jailton pode tomar

> Data: 2026-09-28. Autor: agente de auditoria (WP5, US-005).
> Fontes: `plano/WP1_ROTEAMENTO.md`, `plano/WP2_FABRICACAO.md`, `plano/WP3_PREMISSAS_DATASHEETS.md`,
> `plano/WP4_FIRMWARE.md`, `orcamento/ORCAMENTO.md`, `fase4_entrega/`.
> Convenção de etiqueta: **[MEDIDO]** = número lido de arquivo do projeto ou de comando executado nesta máquina;
> **[DATASHEET]** = número do datasheet, com arquivo e página; **[EST]** = estimativa do agente;
> **[CALC]** = conta feita a partir de números marcados.

---

## 1. Como usar

Este arquivo não é um plano de trabalho: é a **lista fechada do que o plano não consegue decidir sozinho**.
Cada seção traz uma pergunta já fechada em A/B/C (a sub-tabela 7b do D-07 é uma pergunta binária A/B),
o que cada opção destrava e o que trava, o custo em horas ou
reais quando existe, a recomendação do agente com o porquê, e — importante — **o que dá para fazer em paralelo
enquanto a resposta não vem**. Nada aqui exige resposta para continuar trabalhando: as 15 decisões estão
ordenadas por urgência, e a maior parte do trabalho de arquivo (30,0 h [EST], `plano/WP2_FABRICACAO.md` §1)
é comum a todas as alternativas. Você pode responder só as 3 primeiras (§4) e o projeto anda.

**Regra de leitura:** toda linha marcada `[EST]` é estimativa minha, não medição. Trate `[EST]` como ordem de grandeza.
Nenhum número deste arquivo foi inventado: quando não havia fonte, a opção está marcada como não cotada.

---

## 2. Tabela-resumo

| # | Decisão | Urgência — o que trava hoje | Recomendação | Detalhe |
|---:|---|---|---|---|
| **D-01** | Firmware dentro ou fora do escopo | Define se a entrega é uma placa ou um drone. Nenhuma linha de firmware pode ser escrita antes (map de pinos divergente) | **B** — firmware de bancada (160 h [EST]) | [§3.1](#31-d-01--firmware-dentro-ou-fora-do-escopo) |
| **D-02** | Roteamento: Opção A (reescrever o A*) ou Opção B (6 camadas + placa menor) | **138 nets com pad e zero trilha** + 309 pads de plano sem via. A placa não funciona roteada nem metade | **B** — 6 camadas + ~150×110 mm | [§3.2](#32-d-02--roteamento-opção-a-ou-opção-b) |
| **D-03** | Tamanho da placa: 220×160 mm mantido ou reduzido | Entra no Gerber e no cálculo de custo e peso. Não dá para cotar PCB sem isso | **B** — reduzir para ~150×110 mm | [§3.3](#33-d-03--tamanho-da-placa-220160-mm-ou-reduzido) |
| **D-04** | Número de placas: 1 ou 5 | Custo de fab por unidade muda de 5× para 1×. Trava o upload do Gerber no site do fabricante | **A** — 1 placa para bring-up | [§3.4](#34-d-04--número-de-placas-1-ou-5) |
| **D-05** | Montagem: caseira ou PCBA (JLCPCB) | Trava a BOM de fabricação e se os CIs precisam estar na biblioteca da JLC | **A** — caseira nesta revisão | [§3.5](#35-d-05--montagem-caseira-ou-pcba-jlcpcb) |
| **D-06** | Repo do GitHub: privado ou público | **Estado verificado: o repo está PÚBLICO agora.** Se isso não foi intencional, é a decisão mais urgente do arquivo | **A** — privado, agora | [§3.6](#36-d-06--repo-do-github-privado-ou-público) |
| **D-07** | Failsafe: 200 ms é o prazo? E watchdog externo: sim ou não? | Módulo M10 do firmware não tem timeout definido. Watchdog não está no layout | **A** — 200 ms em 10 quadros + watchdog externo | [§3.7](#37-d-07--failsafe-200-ms-e-watchdog-externo) |
| **D-08** | Part numbers finais para cotação real dos 37 itens [EST] | **0 de 43 itens** com disponibilidade/lead time verificados. Nenhuma compra é possível sem isso | **A** — fechar os 5 blocos críticos primeiro | [§3.8](#38-d-08--part-numbers-finais-para-cotação-real) |
| **D-09** | Trocar 12× INA240 (31 % do BOM) por INA181/INA241 | Se trocar, é respin de layout + troca de ganho. Não dá para cotar antes | **A** — manter INA240A2 | [§3.9](#39-d-09--trocar-12-ina240-por-ina181ina241) |
| **D-10** | Os 309 pads de plano sem via: corrigir no layout ou aceitar? | Os 309 pads de GND/VBAT_PROT estão a mais de 1,6 mm de uma via [MEDIDO]. A placa não toca seus planos | **A** — corrigir com stitch vias | [§3.10](#310-d-10--os-309-pads-de-plano-sem-via) |
| **D-11** | Adotar a premissa Qg contradita (40 → 168 nC) e refazer o gate drive | O dimensionamento da Fase 0 está subdimensionado ~4× [WP3 P-06] | **A** — adotar 168/210 nC e refazer | [§3.11](#311-d-11--premissa-qg-40--168-nc-e-o-que-muda-no-gate-driver) |
| **D-12** | ADC: manter 4× MCP3208 ou trocar por 2× ADS7953 | RF-01 e RF-02 são críticos: 120 % e 240 % do datasheet | **A** — trocar por ADS7953 | [§3.12](#312-d-12--adc-4-mcp3208-ou-2-ads7953) |
| **D-13** | `SD` dos 12 IR2104: rotar para um GPIO do ESP32-S3? | Não existe corte de gate por software. Correção de 1 pino | **A** — rotar para GPIO | [§3.13](#313-d-13--o-sd-dos-12-ir2104-vai-para-um-gpio) |
| **D-14** | Compra: nacional (R$ 1.706) ou importação (R$ 1.354) | Trava a data de chegada das peças e todo o cronograma | **A** — nacional nesta iteração | [§3.14](#314-d-14--compra-nacional-ou-importação) |
| **D-15** | Fusível/e-fuse de entrada: sim, qual, ou nenhum | Pergunta 11 da Fase 0 ainda aberta [MEDIDO]. O item já está no BOM a US$ 0,30 | **A** — fusível 30 A 1206 | [§3.15](#315-d-15--fusívelefuse-de-entrada) |

**Contagem: 15 decisões.** Quatro são bloqueantes hoje (D-01, D-02, D-06, D-08). Duas são de emergência de
segurança, não de escopo (D-07, D-13).

---

## 3. As decisões, uma a uma

### 3.1 D-01 — Firmware dentro ou fora do escopo

**Pergunta fechada:** o firmware de bordo (PID, IMU, comutação, failsafe) faz parte do que este projeto entrega,
ou o projeto entrega placa + especificação e o firmware fica para outro?

**O que está travando hoje:** o mapa de pinos do firmware não existe, e o que existe na Fase 0 diverge do layout
inteiro nos motores 2, 3 e 4 [WP4 RF-07]. Escrever firmware agora produz um binário que não funciona na placa.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Fora do escopo** (estado atual do briefing) | Envio para fab da placa; ~30,0 h [EST] de trabalho de arquivo (§D-05) | **O drone não voa**; 320 h [EST] de firmware ficam sem dono | 0 h | O repositório se chama `drone-4in1-esc-esp32s3` e o conteúdo é placa. Risco de Expectativa, não técnico |
| **B — Firmware de bancada (M0–M6 + M10 + M11) dentro** ✅ | Executa os passos 9, 10, 11, 12, 14, 15 de `fase4_entrega/PLANO_TESTE_BANCADA.md`; a placa sai do papel | Os 160 h de PID e comutação | **160 h** [EST] | Precisa dos 3 bloqueios de hardware (D-12, D-13, D-07) resolvidos antes |
| **C — Firmware completo dentro** | O drone voa | Nada do escopo está livre | **320 h** [EST] = 8 semanas de 40 h [WP4 §9.2] | Nenhuma validação de bancada foi feita até hoje [MEDIDO — `fase4_entrega/RISCOS.md` §5]. Começar por aqui é começar pelo fim |

**Recomendação: B.** O briefing original já retirou a lógica de voo **por escrito** — `PROMPT_AGENTE_DRONE.md`
item 6 e `fase0_especificacao/FASE0_ESPECIFICACAO.md` §9.6 dizem a mesma frase [WP4 §6.2(a)]. Ou seja, **A é o
padrão e mudar para dentro é decisão sua, não omissão**. B é o meio-termo que não abandona a decisão já
registrada: mantém a lógica de voo fora, mas entrega o firmware mínimo sem o qual o plano de bancada escrito
no próprio repositório não pode ser executado. C é tentador e é o erro caro: 320 h contra 0 h de bancada feita
até hoje [MEDIDO].

**Em paralelo, sem esperar a resposta:** escrever o arquivo de netlist de produção (0,5 h [EST], `plano/WP2_FABRICACAO.md`
§1 item 2) e o sketch do Stackup (1 h [EST], item 6) são comuns às três opções.

---

### 3.2 D-02 — Roteamento: Opção A ou Opção B

**Pergunta fechada:** você investe em reescrever o autorouter (`fase3_pcb/rota_v7.py`) para fechar a v7 na v8
mantendo 220×160 mm e 4 camadas, ou aceita reduzir a placa e ganhar camadas?

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Reescrever o roteador** (checkpoint incremental, union-find no grid, rip-up and reroute por largura de trilha) | Mantém as 202 nets e 319 footprints já cotados [MEDIDO, `fase3_pcb/v7/v7_drone.kicad_pcb`] | Nada sai enquanto o script não rodar | **2–3 semanas** [EST] | Densidade **inválida para produção**: 187 nets de sinal em 2 camadas sobre 352,4 cm² [MEDIDO, WP1 §4]. Mesmo com roteador perfeito, a placa passa no checklist e falha na bancada |
| **B — 6 camadas + placa ~150×110 mm** ✅ | Resolve de raiz a densidade, os keepouts e o custo de cobre | 202 nets e 319 footprints passam a ser insumo, não entrega | **2–3 semanas** [EST] | Duas correções de layout (D-10 stitch vias, D-13 SD) precisam entrar na mesma revisão |
| **C — 4 camadas, partindo o sistema** (2 ESCs por placa) | Mantém a densidade viável sem redesenhar | Dobra a contagem de placas, de conectores e de firmware | Maior custo de fab [EST] | Muda a mecânica do quad; provavelmente não é o que você quer |

**Recomendação: B.** A v7 não está errada — está **subdimensionada em camadas e superdimensionada em área**
[WP1 §4]. Medido: bbox de 220,10 × 160,10 mm = **352,4 cm²** [MEDIDO] carregando 319 footprints, 202 nets,
1093 pads; **138 nets com pad e zero trilha** [MEDIDO, WP1 §1.5], e são justamente as 9 redes de ESC
(GHM101/102/103, 201/202/203, 301/302/303) mais todo o barramento de sinal. Ou seja: **a placa não tem uma rede de
comunicação; tem todas elas sem cobre.** A Opção A só vence se o prazo for curto — e mesmo aí o WP1 deixa
registrado que o que está medido é "não termina em 240 s", não "não termina nunca".

**Impacto em custo, peso e EMC [EST, derivado de WP1 §4]:** a área cai de 352,4 cm² para ~165 cm² (47 %), o que
reduz proporcionalmente o custo de cobre e o peso. Em quadcopter, 100 g de placa é diferença de tempo de voo.
As 6 camadas resolvem a separação entre os setores de potência (VBAT, 30 A) e os de sinal de alta taxa — hoje
**não existe nenhuma região de keepout na v7** [MEDIDO, WP1 §3.3: `grep -c "rule_area\|keepout"` = 0], e os
setores de potência e de sinal estão **no mesmo plano de cobre**. Esse é o ponto de EMC mais concreto do projeto.

**Em paralelo:** as 30,0 h [EST] de artefatos do `plano/WP2_FABRICACAO.md` §1 (esquema nativo, netlist, CPL,
bibliotecas, stackup, drill map, `.gbrjob`, contorno) são **idênticas nas duas opções**.

---

### 3.3 D-03 — Tamanho da placa: 220×160 mm ou reduzido

**Pergunta fechada:** o contorno final é 220×160 mm [MEDIDO] ou ~150×110 mm?

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Manter 220×160 mm** | Nada que não estivesse destravado com B | Densidade de roteamento [WP1 §4]; o `orcamento/ORCAMENTO.md` §6 chama isso de "**o maior alavanca de custo**": PCB de 220×160 é 5 placas de 100×100 em área | PCB entre **R$ 359 e R$ 770** para 5 placas, 4 camadas, 2 oz [EST, `orcamento/ORCAMENTO.md` §1] | Peso alto para quad; maior chance de EMC |
| **B — Reduzir para ~150×110 mm** ✅ | Cotação de PCB real; peso; layout de 6 camadas cabe | Exige a v8 com contorno novo | A **US$ 70–150 [EST] vira poucos dólares por lote de 5** [MEDIDO, `orcamento/ORCAMENTO.md` §6] | Reposicionar blocos; o gerador `fase3_pcb/gera_pcb_v7.py` produz a posição deles |
| **C — Intermediário, ~180×130 mm** | Compromisso se 150×110 não couber com 6 camadas | Nenhuma opção fecha rápido | Intermediário [EST] | Escolha de meio termo raramente é a boa |

**Recomendação: B.** O `orcamento/ORCAMENTO.md` §6 já diz textualmente que *"se a versão final couber em
~120×80 mm, a fabricação cai de faixa de US$ 70-150 para poucos dólares por lote de 5"* e que *"antes de
fechar compra, vale terminar o roteamento e recotar"*. Isso é advice que o próprio orçamento já deu e que
depende só de você. **Importante:** a redução de área é o que torna a Opção B do D-02 fisicamente honesta —
6 camadas numa placa de 352,4 cm² seria desperdício.

**Em paralelo:** nada. Esta é a decisão que mais trava por dependência — ela define D-02, D-04 e o custo do D-14.
Responda antes delas.

---

### 3.4 D-04 — Número de placas: 1 ou 5

**Pergunta fechada:** você encomenda 1 placa (bring-up) ou 5 (lote)?

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — 1 placa, bring-up** ✅ | Nada desperdiça: nenhuma placa é feita antes do layout fechar (138 nets sem cobre) | Sem redundância se a placa vier com defeito | ~1/5 do lote; cotação só depois de D-02 e D-03 | Se a v8 vier com defeito de fab, espera-se o retrabalho |
| **B — 5 placas de uma vez** | Reserva para 4 motores + 1 de sobra, e teste de lote | **Trava se o layout não fechar** — hoje ele não fecha | **R$ 359 a R$ 770** [EST, `orcamento/ORCAMENTO.md` §1] | 4 placas jogadas fora se D-02 for mudada depois de o Gerber estar pago |
| **C — 2 placas** | 1 para bring-up, 1 de reserva | Nada além de prazo | ~R$ 100–200 [EST] | Custo por placa maior que em 5, menor que em 1 |

**Recomendação: A.** Pedir 5 placas de um layout que tem **138 nets com pad e zero trilha** [MEDIDO] e **309 pads
de plano a mais de 1,6 mm de uma via** [MEDIDO] é comprar 4 placas para trincheira. O lote de 5 só faz sentido
depois que a v8 passar no critério de aceite do `plano/WP1_ROTEAMENTO.md` §5.

**Em paralelo:** subir o Gerber de teste no site do fabricante para **ler a cotação real** sem encomendar — o
`orcamento/ORCAMENTO.md` §5.1 já diz que *"a cotação real exige subir o Gerber no site do fabricante"*, e é
exatamente por isso que a faixa US$ 70–150 [EST] ainda é estimativa.

---

### 3.5 D-05 — Montagem: caseira ou PCBA (JLCPCB)

**Pergunta fechada:** a placa vem nua e você solda, ou você encomenda montagem?

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Caseira** ✅ | Nada: a `fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` já está escrita | Nada | R$ 0 de setup; a bancada não está no `orcamento/ORCAMENTO.md` §5.6 ("não incluso: ferro/hot-air, termopar") | 319 footprints [MEDIDO, WP2 §4.3] é trabalho manual |
| **B — PCBA da JLCPCB** | A placa volta soldada e testada | **Exige que os CIs estejam na biblioteca da JLC** e que o CPL exista (não existe, WP2 §1 item 3) | **+ R$ 210 (US$ 41)** [MEDIDO, `orcamento/ORCAMENTO.md` §1] | XT60 e MR30 são **through-hole** [EST, engenharia] — a JLC não os monta; montagem fica meio manual de qualquer jeito (ver ressalva abaixo) |
| **C — PCBA só dos SMD, THT manual** | Reduz o trabalho manual ao conectores | Depende de CIs na biblioteca | Intermediário [EST] | Divisão de trabalho entre fab e bancada |

**Recomendação: A nesta revisão, C na próxima.** A PCBA é classicamente um ganho de tempo em produção, e aqui o
projeto ainda está em **uma placa de bring-up** (D-04) com **138 nets sem cobre** [MEDIDO]. Pagar setup para
montar uma placa que talvez nem roteie é desperdício. Além disso, XT60 e MR30 são through-hole [EST, engenharia] — a
montagem da JLC não cobre a parte que você mais sente. Reavalie quando o layout fechar e você tiver 5 placas.

**Ressalva de lastro (2026-09-28):** a afirmação "XT60 e MR30 são through-hole" vem de **conhecimento de
engenharia**, não do CSV. As linhas citadas do `orcamento/orcamento_detalhado.csv` **existem e apontam para as
peças certas**, mas **não dizem nada sobre tecnologia de montagem** [MEDIDO]:

```console
$ grep -n "XT60\|MR30" orcamento/orcamento_detalhado.csv
2:ENTRADA;Conector de bateria;XT60 macho+femea, 60 A [N/D offline];1;...
36:MOTOR;Conector de motor;MR30 3 pinos (fases U/V/W);4;...

$ grep -inE "through|THT" orcamento/orcamento_detalhado.csv
(vazio: nenhuma ocorrencia)
```

O que o CSV de fato afirma nas linhas 2 e 36 é a **especificação comercial** do conector (XT60 "macho+fêmea,
60 A, [N/D offline]", US$ 0,58; MR30 "3 pinos (fases U/V/W)", US$ 0,35 × 4) e a **procedência do preço**. A
classificação como *through-hole* é **[EST, engenharia]** — XT60 e MR30 são, por construção, montados em furo
passante. A conclusão prática (a JLC não os monta) permanece válida; o que mudou foi a **etiqueta**: era
`[MEDIDO]` sem lastro e passou a ser `[EST]`.

**Em paralelo:** o item 3 da §1 do `plano/WP2_FABRICACAO.md` (CPL, 0,5 h [EST]) só é necessário se você escolher B
ou C. Se escolher A, marque como não aplicável e economize a tarefa.

---

### 3.6 D-06 — Repo do GitHub: privado ou público

> ### 🔴 Estado verificado nesta máquina, 2026-09-28 01:42 (America/Bahia)
>
> ```console
> $ gh repo view Jailtonfonseca/drone-4in1-esc-esp32s3 --json name,isPrivate,defaultBranchRef,visibility
> {"defaultBranchRef":{"name":"main"},"isPrivate":false,
>  "name":"drone-4in1-esc-esp32s3","visibility":"PUBLIC"}
>
> $ gh auth status | head -3
>   ✓ Logged in to github.com account Jailtonfonseca (/root/.config/gh/hosts.yml)
>   - Active account: true
>   - Token scopes: 'gist', 'read:org', 'repo'
>
> $ git log --oneline origin/main..main
> (lista os commits locais ainda não enviados — o número cresce a cada commit e por isso
>  não é fixado neste documento; consulte o comando para saber o estado atual)
>
> $ git cat-file -t origin/main ; git log --oneline origin/main | head -3
> commit
> a22f9bf refactor: remove fingerprint da maquina do projeto
> be5a1d0 docs: adiciona licença MIT e atualiza seção de licença do README
> 5848ced Projeto drone: ESC 4x trifasico + ESP32-S3 em PCB unica
> ```
>
> **O briefing desta missão diz que o repositório "já criado e privado". O comando acima diz `PUBLIC`.**
> O estado real é: repo existe, `gh` autenticado como `Jailtonfonseca` (escopo `repo`, pode mudar visibilidade),
> **visibilidade pública**, com **commits locais ainda não enviados** e o remoto em `main`. Quanto a origem
> conhece: `git log --oneline origin/main | head -3` acima, o commit mais recente é `a22f9bf`.

**Pergunta fechada:** o repositório fica público (com licença MIT, como está) ou você baixa para privado?

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Baixar para privado** ✅ | Nada trava; é reversível em 1 comando | Nenhum | US$ 0 | Perde a visibilidade de portfólio, se isso importasse |
| **B — Manter público** | Repositório serve de portfólio técnico | Nada | US$ 0 | Publica esquema, netlist e **fotos/medições de hardware sob MIT** |
| **C — Manter público agora, baixar depois** | Um compromisso | Deixa o conteúdo exposto no intervalo | US$ 0 | Push é imediato; o conteúdo fica no cache de terceiros mesmo depois de baixar |

**Recomendação: A, agora.** A licença **MIT** já está no repositório [MEDIDO — commit `be5a1d0`], e um esquema
de ESC 4× com ESP32-S3 é documentável, mas o MIT é uma **permissão de uso, modificação e redistribuição** —
não é "sem garantia nenhuma". Se você publicar, é escolha consciente; enquanto for dúvida, privado é o estado que não
exige desfazer depois. Não fiz a mudança: mudar a visibilidade de um repositório é operação externa e
**depende da sua confirmação**.

**Em paralelo:** nenhum push foi feito (os commits que `git log --oneline origin/main..main` listar seguem
locais, por instrução explícita). Se você escolher A, o próximo passo é `gh repo edit --visibility private` e
só depois decidir sobre push.

---

### 3.7 D-07 — Failsafe: 200 ms é o prazo? E watchdog externo: sim ou não?

**Pergunta fechada (são duas, mas andam juntas):** o timeout de link do failsafe é 200 ms, e você aceita
adicionar um CI supervisor de watchdog externo à placa?

**Estado registrado hoje, como pendente sua:** `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §5.2 linha de "Prazo"
registra a pergunta 9 da §11 da Fase 0 (*"Prazo de link aceitável para o failsafe (sugiro 200 ms)?")* como
**"ainda não respondida"** desde 2026-09-11 [MEDIDO]. O watchdog externo aparece como pendência em
`fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md` D4 (*"SOIC-8 — decisão pendente do Jailton"*) [MEDIDO] e como
*"Watchdog externo (opcional) … decisao do Jailton"* em `orcamento/orcamento_detalhado.csv` linha 42 [MEDIDO].

**7a — prazo do failsafe**

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — 200 ms, em 10 quadros consecutivos a 50 Hz** ✅ | M10 fechado com número | Nada | 0 | Cauda do WiFi passa de 100 ms [EST, §5.3] — por isso **ESP-NOW**, não WiFi |
| **B — 100 ms** | Corte mais rápido | Precisa de link com latência abaixo de 100 ms | 0 | 5,0 cm de queda [MEDIDO, §2.4]; risco alto de corte falso |
| **C — 500 ms** | Link mais tolerante | **Fisicamente inviável** | 0 | **122,62 cm de queda e 4,91 m/s de impacto** [MEDIDO, `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §2.4]. A §2.4 diz sobre 500 ms: *"Para 500 ms já são 1,23 m — o que já quebra hélice e braço."* |

**O número que decide:** a queda em 200 ms é **19,62 cm / 1,96 m/s** [MEDIDO, `fase4_entrega/ANALISE_WIFI_CONTROLE.md`
§2.4]. Essa é a "boa notícia do projeto", como o documento diz textualmente.

**Refeito a partir da fonte, 2026-09-28 [MEDIDO, `fase4_entrega/ANALISE_WIFI_CONTROLE.md` §2.4]:**

```console
$ grep -nE "^\| (100|200|500) ms" /opt/jupyter/work/drone/fase4_entrega/ANALISE_WIFI_CONTROLE.md
94:| 100 ms | 4,91 cm | 0,98 m/s |
95:| **200 ms** | **19,62 cm** | **1,96 m/s** |
96:| 500 ms | 122,62 cm | 4,91 m/s |

$ python3 -c "import math; [print('%d ms -> %.2f cm ; %.2f m/s' % (t, 0.5*9.81*(t/1000)**2*100, 9.81*(t/1000))) for t in (100,200,500)]"
100 ms -> 4.91 cm ; 0.98 m/s
200 ms -> 19.62 cm ; 1.96 m/s
500 ms -> 122.62 cm ; 4.91 m/s
```

> A queda é `h = ½·a·t²` com `a = 9,81 m/s²` — a velocidade de impacto é `v = a·t`. A versão que circulava
> neste arquivo (49,05 cm para 500 ms) era `0,98 m/s × 0,5 s`: a **velocidade** da linha de 100 ms aplicada ao
> **tempo** de 500 ms, misturando as duas. O número correto é **122,62 cm**, e ele torna a Opção C ainda mais
> indefensável do que o texto dizia — 1,23 m de queda é mais que a altura de voo típica do pacote.

**7b — watchdog externo**

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Sim, adicionar** ✅ | Fecha a mitigação que a Fase 4 já declarou para R-08 | 1 CI + 1 pino a entrar no layout | **US$ 0,70** [MEDIDO, `orcamento/orcamento_detalhado.csv` linha 42] | Precisa entrar na v8, junto com D-10 e D-13 |
| **B — Não** | Nada | **Se o firmware travar, os motores ficam no último duty até o fim de bateria** [WP4 RF-04] | US$ 0 | O TWDT interno morre junto com o firmware — não é defesa |

**Estado atual do layout [MEDIDO, WP4 RF-04]:** `WD_FEED` aparece em exatamente 2 lugares (pad 25 do MCU e o
test point `TP_WD`); buscar por `U_WD`, `MAX706`, `TPS3813` ou `watchdog` no gerador devolve **0**. **Não existe
watchdog externo na placa hoje** — a mitigação declarada não foi implementada.

**Recomendação: A nas duas.** 200 ms em 10 quadros consecutivos (não "um buraco de tempo" — [EST] §5.2, evita
disparo por retry longo) e o watchdog sim. O custo é US$ 0,70 e 1 pino; o custo de não ter é o pior cenário
possível do projeto, e ele está escrito em `fase4_entrega/RISCOS.md` R-08.

**Em paralelo:** o módulo de failsafe pode ser especificado com timeout **parametrizado em compilação**
(default 200 ms) — isso custa 2 h a mais [EST] e deixa a decisão aberta até o bench, sem reescrever código.

---

### 3.8 D-08 — Part numbers finais para cotação real

**Pergunta fechada:** quais são os part numbers definitivos de MOSFET, gate driver, amp de corrente, bucks,
shunt e conectores — para sair da estimativa e entrar na cotação?

**O que está travando hoje [MEDIDO, `orcamento/ORCAMENTO.md` §1 e §5]:**

```
- Componentes, valor de catalogo (US$ LCSC-equivalente): US$ 100.88
- Com folga de lote/MOQ (x1.15): US$ 116.01
- Linhas com preco cotado agora: 3 de 43 | apenas estimativa: 37
- 3. Disponibilidade/lead time nao verificado em nenhum item (0 de 43).
- 2. Preco unitario de 37 das 43 linhas e' [EST] -- ordem de grandeza, nao cotacao.
```

O motivo técnico está registrado: *"LCSC e Mercado Livre bloqueiam leitura automática daqui (LCSC/Akamai
devolveu 'Access Denied'; Mercado Livre devolveu página de erro)"* [MEDIDO]. A escolha de peça é sua e a
cotação é sua; nenhum agente nesta máquina tem como ler os dois catálogos.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Fechar os 5 blocos críticos primeiro** ✅ | Cotação real de ~80 % do valor; começa a chegar peça | Os itens de menor valor | 2–4 h seu de pesquisa [EST] | Atraso se algum bloco demore |
| **B — Fechar os 43 de uma vez** | Compra em um pedido só | Nada | 6–8 h seu [EST] | Um item sem estoque travaria o pedido inteiro |
| **C — Não fechar, comprar pela linha da lista** | Compra imediata | Nada fecha: continua sendo [EST] | — | Peça diferente da do layout; 6 datasheets sem lastro [MEDIDO, `plano/WP3_PREMISSAS_DATASHEETS.md` §5.2] |

**Os 5 blocos críticos** (por valor e por dependência de layout):

| Bloco | Qtd | Linha atual | O que definir |
|---|---:|---|---|
| **MOSFET** | 24 | `fase0_especificacao/lista_componentes_fase0.csv` linha 9: *"Vds >= 40 V, Rds <= 3 mOhm @10V, **Qg <= 60 nC [PREMISSA]**"* | O único PDF no disco é `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` — **referência, não escolha** [MEDIDO] |
| **Gate driver** | 12 | IR2104 | Se mantém ou troca. Ligado a D-11 |
| **Amp de corrente** | 12 | `orcamento/ORCAMENTO.md` linha 64: *"INA240A2 … CI ~US$2,5-3,3"* | A2 é a variante de 50 V/V [DATASHEET, `datasheets/ina240_ti_sbos662.pdf` p.3 Table 5-1]. Ligado a D-09 |
| **Bucks 12/5/3,3 V** | 3 | Sem CI escolhido [WP3 §5.2] | Part number + indutor. Define P-08 |
| **Shunt 0,5 mΩ 2512** | 12 | `orcamento/ORCAMENTO.md` linha 63: *"2W 2512 manganina"* | PN real. O "2 W" é catálogo genérico, não extraído [WP3 P-09] |

**Recomendação: A.** A ordem importa: **MOSFET primeiro** (porque D-11 muda o dimensionamento do gate drive),
**amp de corrente em segundo** (porque D-09 pode trocar a peça e o footprint), **bucks em terceiro** (4 dos
43 itens [EST] dependem deles). Os 37 itens restantes são predominantemente passivos, que podem ficar para a
segunda rodada.

**Em paralelo:** o `plano/WP3_PREMISSAS_DATASHEETS.md` §6.7 pede exatamente isto — registrar o part number em
`fase0_especificacao/lista_componentes_fase0.csv` antes de gerar footprints. O script de join BOM↔board
(4 h [EST], `plano/WP2_FABRICACAO.md` §4.3) pode ser escrito com a coluna vazia e preenchida depois.

---

### 3.9 D-09 — Trocar 12× INA240 por INA181/INA241

**Pergunta fechada:** você paga US$ 31,20 [MEDIDO] em 12 amplificadores diferenciais, ou troca por uma peça
mais barata aceitando perder desempenho?

**O número [MEDIDO, `orcamento/ORCAMENTO.md` §6]:** *"12x INA240 = o item mais caro do projeto (US$ 31,20,
~31% do BOM). Alternativa: INA181/INA241 mais barato ou medição de shunt low-side com amp simples, ao custo
de perder rejeição de PWM."*(unitário: US$ 2,60, linha 64)

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Manter 12× INA240A2** ✅ | Nada a fazer; a rejection de ripple de PWM está garantida | US$ 31,20 [MEDIDO] no orçamento | US$ 31,20 | O ganho de 50 V/V **seleciona a variante A2** [DATASHEET, p.1/p.3/p.5]. Estoque de A1/A3/A4 invalida o ganho |
| **B — Trocar por INA181/INA241** | Barato; [EST] a faixa dinâmica cai | Precisa de **respin** — o footprint muda | Menor [EST] | Perde CMRR sob PWM. P-07 diz que a 20 kHz o CMRR 93 dB do INA240 [DATASHEET p.5] é folga; trocar **gasta essa folga** |
| **C — Amp simples + shunt low-side** | O mais barato | Reispin maior; perde isolamento | Mínimo [EST] | A medição passa a depender da topologia do shunt — muda o esquema |

**Recomendação: A — manter os 12 INA240A2.** Três razões, com números: (1) os 31 % do BOM [MEDIDO] são do **catálogo
estimado**; com cotação real (D-08) esse número pode cair, e trocar peça por causa de um [EST] que ainda não foi
cotado é trocar no escuro. (2) O CMRR a 20 kHz é a **folga** que protege a leitura de corrente com PWM a 20 kHz
— ela só deixa de ser folga se o PWM subir, o que é decisão sua e não do orçamento. (3) Trocar agora significa
**respin**, e você já tem um respin previsto por D-02, D-10, D-12 e D-13. Não abra um quinto.

**Em paralelo:** cotar o INA240A2 na JLCPCB (D-08) resolve a pergunta sem mudar nada. A alternativa B fica de
porta se a cotação vier acima do orçamento.

---

### 3.10 D-10 — Os 309 pads de plano sem via

**Pergunta fechada:** você aceita que os 309 pads de GND e VBAT_PROT fiquem sem via de stitch, ou corrige o layout?

**O que está travando hoje [MEDIDO, `plano/WP1_ROTEAMENTO.md` §3.2]:**

```
pads de GND e VBAT_PROT SEM via a menos de 1,6 mm:
   GND         pads=207  vias=296  pads_sem_via_perto=207
   VBAT_PROT   pads=102  vias=21    pads_sem_via_perto=102
```

**Todos os 309 pads (207 + 102) estão a mais de 1,6 mm de uma via.** Lido literalmente: mesmo que as 138 nets
de sinal fossem roteadas perfeitamente, **os 309 pads de retorno e de alimentação não tocariam seus planos** —
a placa não funcionaria. São 945 pads SMD que só estão em F_Cu, e um plano em In1_Cu só se alcança por via.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Stitch vias em cada pad** ✅ | Os 309 pads alcançam os planos; a placa fica eletricamente viável | Nada | +309 vias [EST] a ~0,15 mm² cada [CALC] | Densidade: mais furos competing com as 138 nets sem cobre (D-02) |
| **B — Estrelas de cobre entre os pads** | Menos furos | Funciona só se o cobre couber | Mais área de cobre | Em 220×160 há espaço; em ~150×110 [D-03] pode não haver |
| **C — Aceitar sem via** | Nada | **A placa não funciona** | US$ 0 | Não é uma opção de engenharia, é um bug de layout |

**Recomendação: A.** C não é opção. Entre A e B, a escolha depende de D-03: **se a placa ficar 150×110 mm, a
densidade de furos pode inviabilizar 309 vias individuais** e o stitch vira "(B) estrelas + vias só nos pads de
corrente alta". Ou seja: **A e B decidem juntas com D-03 e D-02** — é por isso que estas três são as que mais
destravaram (§4).

**Em paralelo:** nada isoladamente, mas o resultado do gerador de stitch pode ser escrito como script separado
(`fase3_pcb/calc_trilhas_vias.py` já existe [MEDIDO]) e reaproveitado quando o contorno fechar.

---

### 3.11 D-11 — Premissa Qg: 40 nC → 168 nC, e o que muda no gate driver

**Pergunta fechada:** você adota Qg = 168/210 nC [DATASHEET] no lugar dos 40 nC [PREMISSA] e refaz o dimensionamento
do gate drive, ou mantém a premissa da Fase 0?

**O dado [DATASHEET, `plano/WP3_PREMISSAS_DATASHEETS.md` P-06, `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf`]:**

- p.1 Table 1: `QG(0V..10V) = 168 nC`
- p.4: `Qg = 168 nC (typ) / 210 nC (max)`, condição `VDD=50 V, ID=100 A, VGS=0 to 10 V`
- p.4: `Qgs = 53 nC`, `Qgd = 34 nC (typ) / 51 nC (max)`

**A premissa de 40 nC é ~4× otimista.** O que muda, com conta:

- O IR2104 entrega `IO+/− = 130/270 mA` [DATASHEET, `datasheets/ir2104_infineon_datasheet.pdf` p.1].
- O que se calcula é o **tempo** de comutação de gate, `t = Qg/I`. Com Qg = 168 nC: **1,292 µs** a 130 mA e
  **0,622 µs** a 270 mA. Convertido em slew para um VGS de 10 V (`dV/dt = ΔV/t`): **0,0077 V/ns** a 130 mA e
  **0,0161 V/ns** a 270 mA [CALC]. A Fase 0 dimensionou com 40 nC, ou seja, com um slew ~4× maior do que o
  FET real aceita.

```console
$ python3 -c "
Qg=168e-9
for I in (0.130,0.270):
    t=Qg/I
    print('Qg=168 nC, I=%.0f mA -> t=%.3f us ; dV/dt(10 V)=%.4f V/ns' % (I*1000, t*1e6, 10/(t*1e-9)/1e9))"
Qg=168 nC, I=130 mA -> t=1.292 us ; dV/dt(10 V)=0.0077 V/ns
Qg=168 nC, I=270 mA -> t=0.622 us ; dV/dt(10 V)=0.0161 V/ns
```

> **Erro corrigido em 2026-09-28 (round 2).** Este parágrafo dizia *"com 168 nC e 130 mA: 0,64 V/ns; com
> 270 mA: 1,33 V/ns"*. Os dois números estão com a **unidade trocada e com as correntes trocadas**: 0,64 e 1,33
> são `Qg/I` em **µs**, não V/ns. E o emparelhamento está invertido — 0,64 µs (exato: 0,622 µs) é o caso de
> **270 mA**, e 1,33 µs (exato: 1,292 µs) é o de **130 mA**. Um slew de 0,64 V/ns significaria comutar 10 V em
> 15,6 ns — fisicamente impossível com 130 mA de pico. O erro é de **~83×** contra o valor correto de slew.
> **A origem é o `plano/WP3_PREMISSAS_DATASHEETS.md` P-06**, cuja tabela registra *"o slew de gate cai para
> ~0,6–1,3 V/ns"* com o mesmo cálculo. O WP3 **não foi editado** (fora do escopo desta rodada); a correção
> fica registrada aqui e o WP3 continua precisando do mesmo ajuste.
- **O dimensionamento de resistor de gate e de dissipação do IR2104 feito na Fase 0 está subdimensionado
  por um fator ~4** [WP3 P-06] e precisa ser refeito.
- Isso **aumenta a perda de comutação e a dissipação no driver** — o que, num quad de 4 motores com 6 MOSFETs
  cada, é perda real de bateria.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Adotar 168/210 nC e refazer** ✅ | Dimensionamento correto do gate drive | Exige reexecutar `fase0_especificacao/dimensionamento_fase0_saida_v2.txt` e `fase0_especificacao/verifica_limites_saida_v4.txt` [MEDIDO — ambos existem] | 4–6 h [EST] | Se o FET final for outro, Qg muda de novo |
| **B — Manter 40 nC** | Nada | Nada | 0 | **Perda de comutação e de bateria subestimada em ~4×**. Num projeto de missão isso é erro de dimensionamento, não detalhe |
| **C — Adiar até escolher o MOSFET** | Evita refazer duas vezes | Nada é correto até lá | 0 | A dependência é real: D-08 precisa vir antes |

**Recomendação: A, e A só depois de D-08.** As duas decisões são a mesma: **Qg é propriedade do MOSFET, e o
MOSFET ainda não foi escolhido.** A ordem correta é D-08 (escolher MOSFET) → D-11 (refazer com o Qg real) →
D-08 de novo (cotar). Fazer D-11 agora com o Qg da peça de referência é trocar um [EST] por outro [EST].

**Nota ligada à escolha do gate driver:** o P-05 registra que o `RDS(on)` **sobe de 1,7 mΩ (typ) para 2,2 mΩ
(max) quando VGS cai a 6 V** [DATASHEET, p.4]. Como o IR2104 entrega 10–20 V de gate drive [DATASHEET p.1],
10 V é o piso — então o FET opera no melhor caso, mas **qualquer FET escolhido com driver mais fraco cai no
pior caso**. Isso entra no critério de escolha em D-08.

**Em paralelo:** `plano/WP3_PREMISSAS_DATASHEETS.md` §6.1 e §6.2 já pedem exatamente estas duas correções
(Qg e P-11). A P-11 (quiescência: 2,5 mA [PREMISSA] → **0,325 mA** [DATASHEET, IR2104 p.3: IQCC 270 µA +
IQBS 55 µA]) é um número de texto, não de layout: corrigir agora custa 5 min e não depende de ninguém.

---

### 3.12 D-12 — ADC: 4× MCP3208 ou 2× ADS7953

**Pergunta fechada:** você mantém os 4× MCP3208 que estão no layout, ou troca por 2× ADS7953?

**Os dois riscos [MEDIDO, `plano/WP4_FIRMWARE.md` §8 item 1 e RF-01/RF-02]:**

- **RF-01:** 6 canais por CI × 20 kHz = **120 ksps por CI**. O MCP3208 entrega **100 ksps a 5 V** e **50 ksps
  a 2,7 V** [DATASHEET, `datasheets/mcp3208_microchip_ds21298e.pdf`]. Isso é **120 % do datasheet a 5 V e
  240 % a 2,7 V**.
- **RF-02:** o MCP3208 **multiplexa** — *"programmable to provide four pseudo-differential input pairs or eight
  single-ended inputs"* [DATASHEET, p.1]. A Fase 0 §4.2 vendeu amostragem **simultânea** das 3 fases; com
  4× MCP3208 **isso não se materializa**: as 3 fases são lidas em 3 instantes diferentes.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — 2× ADS7953 (16 ch, 1 Msps)** ✅ | Fecha RF-01 e RF-02; devolve comutação sem sensor | Respin (RF-11: a Fase 0 e o layout não concordam) | **+US$ 5,60** [WP4 §8 — 2× US$ 8,00 = US$ 16,00 contra 4× US$ 2,60 = US$ 10,40] **[EST]**, preços de `orcamento/ORCAMENTO.md` linhas 68–69 | O BOM só tem 1 ADS7953; o 2º CI precisa entrar |
| **B — Manter 4× MCP3208** | Nada | A amostragem fica em 120–240 % do datasheet, e não é simultânea | US$ 10,40 | Comutação sem sensor fica fora; medição de pico de corrente com erro |
| **C — 1 ADS7953 + mux** | Barato | Metade dos canais | [EST] intermediário | Mux reintroduz não-simultaneidade |

**Recomendação: A.** US$ 5,60 [EST] para fechar dois riscos 🔴 Críticos que nenhum software resolve — é o
melhor preço de destravamento de todo o arquivo. E note que a escolha atual foi feita **por custo**
[fase3_pcb/gera_pcb_v7.py linhas 15–18] e é exatamente a que falha nos dois riscos.

**Em paralelo:** como a v8 já vai ser feita por D-02, D-10 e D-13, esta troca entra **na mesma revisão** —
custo marginal de layout ≈ 0 se for decidido antes de gerar o Gerber.

---

### 3.13 D-13 — O `SD` dos 12 IR2104 vai para um GPIO?

**Pergunta fechada:** o shutdown dos 12 gate drivers, hoje preso em 3V3, vai para um GPIO do ESP32-S3?

**O que está travando hoje [MEDIDO, `plano/WP4_FIRMWARE.md` RF-03]:** `Rsd%s` vai de `SD%s` a `3V3`
[fase3_pcb/gera_pcb_v7.py linhas 238–239]; a rede `SD%s` só aparece nessas 2 linhas e **não chega a nenhum GPIO
do MCU** [linhas 401–412, `MCU_NETS`, sem nenhuma entrada `SDx`]. Consequência: **não existe instrução de
firmware capaz de desligar os 12 IR2104.** O corte depende de zerar o duty — e a semântica de repouso do RTL
(`duty=0` → low-side ligado) **não é** a do IR2104 com `IN=0`. Firmware escrito contra o RTL pode deixar dois
low-sides ligados.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Rotar `SD` para 1 GPIO** ✅ | Corte de gate por software; fecha RF-03 | +1 pino e +1 net no layout | ~0 h [EST] — 1 linha no gerador | Precisa de um GPIO livre (RF-07 diz que o mapa já diverge) |
| **B — Deixar preso em 3V3** | Nada | Não existe shutdown por software | 0 | Sem failsafe por software, sem failsafe de verdade |
| **C — `SD` puxado pelo `/RESET` aberto-dreno do watchdog externo** | Shutdown por **hardware**, independente do firmware — cobre o caso "MCU travou", que nem GPIO resolve; 0 GPIO gasto | Acopla esta decisão à **D-07b**: só existe se o watchdog for aprovado; não há corte por software isolado | ~0 h [EST] — 1 net, sem pino | Não dá para desligar os drivers em teste de bancada sem parar de alimentar o watchdog; a rede `SD` vira dependência de um CI que ainda não foi escolhido |

**Recomendação: A.** O próprio `plano/WP4_FIRMWARE.md` §8 a classifica como *"a correção mais barata e a mais
séria"*. Custa 1 pino e fecha um risco 🔴 Crítico. Se o ESP32-S3 não tiver GPIO livre no mapa, o caminho é
usar um dos 4 `ADC_CS` [MEDIDO: o v7 tem 4 CS nos pads 23, 15, 33, 34, enquanto a Fase 0 previa 1] — mas isso
é um detalhe de layout, não uma decisão sua.

**Por que A e não C:** C é a única das três que protege contra *firmware travado*, que é o cenário mais grave —
mas ela não existe sem o watchdog externo (D-07b) e troca "corte comandado" por "corte por estouro de tempo".
Se D-07b vier **B** (sem watchdog), a Opção C é automaticamente indisponível. Se D-07b vier **A** e o mapa de
pinos estiver mesmo sem GPIO livre, C passa a ser o plano B de layout — ela deve ser resolvida **junta** com a
D-07b, nunca antes dela.

**Em paralelo:** nada. É a decisão mais rápida de tomar do arquivo e destrava o desenho do M-firmware de corte.

---

### 3.14 D-14 — Compra: nacional ou importação

**Pergunta fechada:** você compra no mercado nacional com markup, ou importa direto da LCSC?

**Os números [MEDIDO, `orcamento/ORCAMENTO.md` §1 e §4]:**

| Cenário | Total |
|---|---:|
| **A — Nacional** (Mercado Livre / lojas BR, componentes + frete) | **R$ 1.706** |
| A — banda honesta (markup k entre 2,7 e 3,7) | R$ 1.448 a R$ 1.965 |
| **B — Importação direta** (LCSC + frete + II 60% + ICMS 17% + IOF 3,5%) | **R$ 1.354** |

Diferença: **R$ 352** [CALC]. A conta do §4: `Nacional: componentes × US$ 5.1312 × k(3,2) + frete R$50 = R$ 1706`;
`total = US$ 263.88 → R$ 1354`.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Nacional nesta iteração** ✅ | Chega em dias; sem alfândega | Diverge da montagem que vamos fazer | R$ 1.706 | Markup ~3,2× sobre catálogo [MEDIDO] |
| **B — Importação** | Mais barato no papel, e peças que o ML não tem | **3–6 semanas + risco de alfândega** [MEDIDO, §6] | R$ 1.354 | A faixa de imposto diverge em até US$ 50 [MEDIDO, §5.4] |
| **C — Misto: nacional na 1ª placa, importação na 2ª** | Velocidade e preço | Dois pedidos, duas listas | R$ 1.706 + ~R$ 1.354 para as 4 restantes [EST] | Mais trabalho administrativo |

**Recomendação: A nesta iteração.** Com D-04 = 1 placa, o ganho absoluto de B é pequeno e a espera de 3–6
semanas [MEDIDO] atrasa todo o bench. E a observação do próprio orçamento é que os cenários **empatam dentro
da barra de erro** [MEDIDO]: R$ 1.706 vs R$ 1.354, com banda de R$ 1.448–1.965 no nacional — ou seja,
**a diferença real é tempo, não dinheiro**.

**Em paralelo:** a decisão de compra só pode ser executada **depois de D-08** (part numbers). E atenção ao item
do `orcamento/ORCAMENTO.md` §6: *"BOM duplica indutores e capacitores de saída … Se for pedir direto do CSV, o
pedido vira 6 indutores e 12 capacitores."* — corrigir isso antes do pedido, não depois.

---

### 3.15 D-15 — Fusível/e-fuse de entrada

**Pergunta fechada:** a entrada de bateria leva fusível, e-fuse, ou nada? Esta é a **pergunta 11 da §11 da
Fase 0**, que continua aberta [MEDIDO] e não tinha virado decisão neste arquivo.

```console
$ grep -n "11\." fase0_especificacao/FASE0_ESPECIFICACAO.md | head
431:11. Precisa de **fusível/e-fuse** de entrada? (recomendo sim)

$ grep -niE "fus[ií]vel|e-?fuse" fase0_especificacao/FASE0_ESPECIFICACAO.md orcamento/ORCAMENTO.md
fase0_especificacao/FASE0_ESPECIFICACAO.md:383:- **Fusível/e-fuse na entrada** é opcional no meu desenho de hoje — eu recomendo incluir
fase0_especificacao/FASE0_ESPECIFICACAO.md:431:11. Precisa de **fusível/e-fuse** de entrada? (recomendo sim)
orcamento/ORCAMENTO.md:89:| EXTRA | Fusivel/e-fuse de entrada | 1 | 0.3000 | 0.30 | 4.93 | [EST] | fusivel 30A 1206 (e-fuse TPS2594x ~US$0,90) |
```

**O que já está registrado:** a Fase 0 §10.1 diz, com as próprias palavras, que o fusível *"é opcional no meu desenho
de hoje — eu recomendo incluir"* [MEDIDO, `fase0_especificacao/FASE0_ESPECIFICACAO.md` linha 383], e o item já
está no BOM com US$ 0,30 / R$ 4,93 [MEDIDO, `orcamento/ORCAMENTO.md` linha 89]. Ou seja: **falta a sua assinatura,
não falta o item.** O pack é de 6S com corrente de projeto na casa das dezenas de ampères, e há TVS
(`SMBJ33A`, US$ 0,12 [MEDIDO, `orcamento/orcamento_detalhado.csv` linha 3]) — mas TVS **não** limita corrente
de falha: ele satura e queima. As duas coisas resolvem problemas diferentes.

| Opção | O que destrava | O que trava | Custo | Risco |
|---|---|---|---|---|
| **A — Fusível 30 A 1206 no polo positivo** ✅ | Proteção contra curto e contra inversão de bateria na cabeceira; 1 item, 0 GPIO, 0 net de sinal | Nada | **US$ 0,30 (R$ 4,93)** [MEDIDO, `orcamento/ORCAMENTO.md` linha 89] | Não é resetável: um transiente, curto ou erro de montagem queima o fusível e a placa vai para a bancada de qualquer jeito |
| **B — e-fuse (TPS2594x) com enable por GPIO** | Corte de corrente **programável**, com I²t, OVP e telemetria ao firmware; some o fusível físico | +1 CI (4 pinos), +1 GPIO e o gate drive do corte entra no layout | **~US$ 0,90** [MEDIDO, fonte da própria linha 89 do `orcamento/ORCAMENTO.md`] | US$ 0,60 a mais e um CI a mais em D-08; a corrente de corte precisa ser cotada contra o de pico da bateria [CALC] |
| **C — Nenhum (só o TVS já no BOM)** | Zero custo, zero footprint | Nada é limitado em caso de falha; o TVS não substitui fusível | US$ 0 | Falha de curto vira **destruição da placa**, não um fusível de R$ 1 |

**Recomendação: A nesta iteração.** Um fusível de 30 A 1206 custa US$ 0,30 [MEDIDO], cabe no footprint
(1206 SMD, o mesmo pacote de vários itens do BOM), não consome pino e protege contra exatamente os dois
cenários de projeto — curto na fiação da bateria e conector XT60 invertido na cabeceira. B é a resposta
*melhor* em engenharia e a resposta *certa* para produção: ela só faz sentido depois que existir um e-fuse
com cotação real, e hoje a única fonte de preço é a própria linha de orçamento, marcada `[EST]`. C é
descartável — sem elemento em série, qualquer falha de curcircuito é destrutiva.

**Em paralelo:** nada precisa esperar. A resposta depende de uma escolha de componente (o PN exato do fusível,
com a corrente e o `I²t`), que é a **mesma tarefa de D-08** — se a lista de compra for fechada, o fusível já sai
com cotação real. Se você não responder, o item fica no BOM a US$ 0,30 [EST] e pode ser tratado como "não
comprado" sem consequências para o layout, porque é um componente de 2 pinos que não altera nenhuma net.

---

## 4. As 3 decisões que mais destravam

Em ordem. Se você responder só três, responda estas.

### 1º — **D-08 — Part numbers finais** (e ela vem antes de D-11, D-09 e D-14)

Sem part number não há cotação, e sem cotação os outros 37 itens [EST] continuam sendo 37 itens [EST]. Puxa
D-11 (Qg real depende do MOSFET), D-09 (custo real do INA240 define se trocar) e D-14 (a escolha nacional ×
importação precisa de preço de verdade, não de [EST]). **Uma decisão, quatro desbloqueios.**

### 2º — **D-02 + D-03 — Roteamento e tamanho da placa** (decididas juntas, no mesmo dia)

D-03 é a pré-condição de D-02, e as duas determinam D-04 (quantas placas encomendar) e o custo do PCB
(R$ 359–770 vs "poucos dólares" [MEDIDO, `orcamento/ORCAMENTO.md` §6]). Juntas também decidem D-10: **309 vias
de stitch cabem em 352 cm² e talvez não caibam em 165 cm².** Decidir essas duas libera a única coisa que
realmente trava o projeto — gerar um Gerber que fecha.

### 3º — **D-01 — Firmware dentro ou fora**

É a decisão que define o que o projeto **é**. A placa (320 h [EST] de firmware) e o drone são projetos com
nomes diferentes, e `plano/WP4_FIRMWARE.md` §6.3 diz exatamente isso: *"na opção A, quando o layout fechar e
o Gerber final sair; na opção C, quando voar."*. Enquanto essa resposta não vem, o M0–M6 de bancada está
parado, e ele é o que transforma a placa em algo testado.

**Fora do top 3, mas não podem esperar muito:** D-06 (o repo está **público** agora — se não foi intencional,
é o item mais urgente do arquivo em termos de exposição) e D-07 + D-13 (segurança de voo: watchdog e
shutdown por software).

---

## 5. Índice de caminhos citados

Todos conferidos com `test -e` a partir de `/opt/jupyter/work/drone` em 2026-09-28 01:43 (America/Bahia):

```console
$ for p in plano/WP1_ROTEAMENTO.md plano/WP2_FABRICACAO.md plano/WP3_PREMISSAS_DATASHEETS.md \
    plano/WP4_FIRMWARE.md plano/mede_v7_wp1.py orcamento/ORCAMENTO.md orcamento/orcamento_detalhado.csv \
    fase4_entrega/ANALISE_WIFI_CONTROLE.md fase4_entrega/MONTAGEM_ORDEM_DE_SOLDA.md \
    fase4_entrega/PLANO_TESTE_BANCADA.md fase4_entrega/RISCOS.md fase4_entrega/SEGURANCA_E_REGULATORIO.md \
    fase0_especificacao/lista_componentes_fase0.csv fase0_especificacao/FASE0_ESPECIFICACAO.md \
    fase0_especificacao/dimensionamento_fase0_saida_v2.txt fase0_especificacao/verifica_limites_saida_v4.txt \
    fase1_esquema fase2_simulacao/verilog/RELATORIO_VERILOG.md fase2_simulacao/verilog/pwm_deadtime.v \
    fase3_pcb/gera_pcb_v7.py fase3_pcb/rota_v7.py fase3_pcb/v7/v7_drone.kicad_pcb \
    fase3_pcb/v6/verificacao_v6.txt PROMPT_AGENTE_DRONE.md \
    datasheets/ir2104_infineon_datasheet.pdf datasheets/ina240_ti_sbos662.pdf \
    datasheets/mcp3208_microchip_ds21298e.pdf \
    datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf \
    datasheets/esp32-s3_datasheet_en.pdf; do
    [ -e "$p" ] && echo "OK   $p" || echo "FALTA $p"
  done
```

Os **28 caminhos** listados no comando acima retornaram todos `OK` (recontagem em 2026-09-28, round 2).
Comando de estado do repositório usado na §3.6:

```console
$ gh repo view Jailtonfonseca/drone-4in1-esc-esp32s3 --json name,isPrivate,defaultBranchRef,visibility
{"defaultBranchRef":{"name":"main"},"isPrivate":false,
 "name":"drone-4in1-esc-esp32s3","visibility":"PUBLIC"}
$ gh auth status | head -3
  ✓ Logged in to github.com account Jailtonfonseca (/root/.config/gh/hosts.yml)
$ git log --oneline origin/main..main
(commits locais ainda não enviados — a contagem muda a cada commit; ver §3.6)
```

**Nenhum push foi executado.** Os commits que `git log --oneline origin/main..main` listar continuam locais.

---

## 6. O que este documento NÃO é

- **Não é o PLANO_FINAL.** Ele não ordena execução, não define passes e não escolhe o que fazer primeiro.
- **Não cria decisão que não exista no projeto.** Todas as 15 saem de um número medido em um dos quatro WP,
  do `orcamento/ORCAMENTO.md`, da `fase4_entrega/` ou da `fase0_especificacao/FASE0_ESPECIFICACAO.md`,
  com a origem indicada na linha.
- **Não cotou nada.** Os 37 itens [EST] continuam [EST]. Nenhum agente nesta máquina tem acesso à LCSC nem ao
  Mercado Livre [MEDIDO, `orcamento/ORCAMENTO.md` §5.2].
- **Não mudou nada fora de `plano/`.** Nenhum push, nenhuma alteração de visibilidade, nenhuma edição de
  arquivo existente.

---

## 7. Correções round 2 (2026-09-28)

Oito defeitos localizados neste arquivo foram corrigidos nesta rodada. Nenhuma delas mudou a **recomendação** de
uma decisão já fechada, exceto a letra da D-09, que apontava para a opção contrária. Registro do que foi feito:

**1. 🔴 D-09 — a letra da recomendação apontava para a opção errada.**
A §3.9 recomendava `C — manter o INA240A2`, mas **C** na tabela é *"Amp simples + shunt low-side"*, exatamente a
opção que o próprio texto desaconselha (*"Não abra um quinto [respin]"*). Responder "C" faria o oposto do advice.
Corrigido para **A** nos dois lugares: na §2 (tabela-resumo) e na §3.9 (recomendação). O fundamento não mudou —
manter o INA240A2; só a letra estava errada.
**Varredura das 14 decisões:** cada letra de recomendação foi comparada com a letra da opção que ela descreve.
Resultado: **só a D-09 divergia.** D-01 B, D-02 B, D-03 B, D-04 A, D-05 A, D-06 A, D-07a A, D-07b A, D-08 A,
D-10 A, D-11 A, D-12 A, D-13 A, D-14 A — todas batem com a linha marcada ✅ da sua tabela.

**2. 🔴 D-07 — número errado e citação fabricada na opção de 500 ms.**
O arquivo afirmava `49,05 cm de queda [MEDIDO, §2.4]`. A fonte
`fase4_entrega/ANALISE_WIFI_CONTROLE.md` §2.4 diz, para 500 ms: **122,62 cm e 4,91 m/s**. O 49,05 era
`0,98 m/s × 0,5 s` — a **velocidade** da linha de 100 ms multiplicada pelo **tempo** de 500 ms. Cálculo refeito
com `h = ½·a·t²` e `v = a·t`, comando e saída colados na §3.7. A citação *"já são [inviável]"* **não existe na
fonte**; trocada pela literal: *"Para 500 ms já são 1,23 m — o que já quebra hélice e braço."*. Isso deixa a
Opção C **mais** indefensável, não menos: 1,23 m de queda.

**3. 🟡 D-13 não tinha opção C.** Acrescentada a opção **C — `SD` puxado pelo `/RESET` aberto-dreno do watchdog
externo**: shutdown por hardware, sem gastar GPIO. A recomendação **continua A**; a C é o plano B de layout e só
existe se D-07b for aprovada — a §3.13 agora diz isso explicitamente.

**4. 🟡 D-11 — `[CALC]` errado por 83×.** O texto dizia "0,64 V/ns" e "1,33 V/ns". São valores de `Qg/I` em **µs**,
com as correntes trocadas: 0,622 µs é o caso de 270 mA e 1,292 µs o de 130 mA. Corrigido para **1,292 µs /
0,622 µs** e para o slew em V/ns: **0,0077 V/ns** e **0,0161 V/ns**, com o comando colado.
**A origem do erro é o `plano/WP3_PREMISSAS_DATASHEETS.md` P-06**, que registra *"o slew de gate cai para
~0,6–1,3 V/ns"*. O WP3 **não foi editado** — está fora do escopo desta rodada e segue precisando do ajuste.

**5. 🟡 D-05 — `[MEDIDO]` sem lastro.** O arquivo afirmava que XT60 e MR30 são through-hole com lastro em
`orcamento/orcamento_detalhado.csv` linhas 2 e 36. As linhas existem e apontam para as peças certas, mas **não
dizem nada sobre tecnologia de montagem**: `grep -i "through\|THT"` não retorna nada. Reetiquetado como
**`[EST, engenharia]`**, com a ressalva e os greps colados na §3.5. A conclusão prática (a JLC não os monta)
permanece válida.

**6. 🟢 Contagens auto-referenciais.** As contagens exatas de commits (`git rev-list --count HEAD` → 15 e
"12 não pushados") foram removidas das duas seções onde apareciam (§3.6 e §5) e substituídas por
`git log --oneline origin/main..main`, que continua válido depois de qualquer commit. A §5 dizia "as 30 linhas
acima" para uma lista de **28 caminhos** — corrigido para 28 e reconferido com `test -e`.

**7. 🟢 Faltava a decisão do fusível.** A pergunta 11 da Fase 0 (*"Precisa de fusível/e-fuse de entrada?"*)
não tinha virado decisão. Acrescentada a **D-15**, com A/B/C e recomendação **A** (fusível 30 A 1206,
US$ 0,30 [MEDIDO, `orcamento/ORCAMENTO.md` linha 89]), ancorada nos dois greps pedidos. O arquivo vai de 14
para **15 decisões**; a §4 continua com o mesmo top 3.

**8. 🟢 Higiene de escrita.** Corrigidos três anglicismos em texto corrido: *"my estimate"* → *"estimativa minha"*
(§1), *"Aternative B"* → *"A alternativa B"* (§3.9), *"we'll fazer"* → *"vamos fazer"* (§3.14). Varredura com
`grep -nE "\bwe'll|\bmy estimate\b|\bAlternative\b|\bcheck\b|\bfile\b|\bcommit\b"`: o que sobrou são **saída de
comando** e **referência a commit** (`git log`, `commit be5a1d0`), legítimos em contexto de shell. Na mesma
varredura saíram três typos do mesmo tipo: `semATCH` → *"sem garantia nenhuma"* (§3.6), `e_A` → *"e A só depois
de D-08"* (§3.11) e *"sãoemergência"* → *"são de emergência"* (§2). Ficou de propósito um único anglicismo:
**"advice"** na §3.3, no sentido de recomendação técnica, aceito em português corrente.

**Preservado sem alteração:** as 7 decisões obrigatórias, a ordem de urgência, o top 3 da §4, o registro de que o
repositório está **público** com licença MIT, os 28 caminhos válidos da §5 e as três primeiras opções de cada
decisão.
