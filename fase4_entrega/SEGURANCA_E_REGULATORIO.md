# SEGURANÇA E REGULATÓRIO (FASE 4)

**Projeto:** drone 4×ESC trifásico + ESP32-S3 na mesma PCB · LiPo 6S
**Pasta:** `/opt/jupyter/work/drone/fase4_entrega/` · **Data:** 2026-09-11 · **TZ:** America/Bahia

## Como ler

| Etiqueta | Significado |
|---|---|
| `[FONTE]` | fonte externa consultada **ao vivo** nesta sessão, com URL e data |
| `[DISCO]` | fato conferido em arquivo do projeto |
| `[EST]` | estimativa de engenharia, não medida |
| `[VERIFICAR]` | **não confirmado** — leia como "não confie nisto sem checar na fonte oficial" |

> **Regra desta seção:** tudo que eu não confirmei com fonte ao vivo está marcado
> `[VERIFICAR]`. As fontes que consultei são, em boa parte, **secundárias** (blogs do setor,
> escritórios de certificação). A palavra final é do texto oficial da ANAC, do DECEA e da
> ANATEL. Onde eu só tinha resumo de busca, marquei.

---

## PARTE 1 — BATERIA LiPo (risco de incêndio: o mais grave do projeto)

Pack do projeto: **LiPo 6S** `[PREMISSA P-02]` — 25,2 V cheio (4,20 V/célula) ·
22,2 V nominal (3,70 V/célula) · **19,8 V no mínimo (3,30 V/célula)** `[CALC]`
(`fase4_entrega/calcs_fase4.txt`).

### 1.1 Regras que não se negociam

| # | Regra | Por quê |
|---|---|---|
| 1 | **Carregar SEMPRE com carregador balanceador** | sem balanceamento, as células divergem e uma pode passar de 4,20 V → inchaço/incêndio |
| 2 | **NUNCA carregar sem supervisão** | a maioria dos incêndios de LiPo acontece em carga não assistida |
| 3 | **Carregar em local não inflamável** (piso de cerâmica/concreto, longe de cortina/papel) | se pegar fogo, o ambiente não pode propagar |
| 4 | **NUNCA descarregar abaixo de ~3,3 V/célula** (19,8 V neste pack) | abaixo disso a célula sofre dano irreversível e pode inchar |
| 5 | **Armazenar a ~3,8 V/célula** (22,8 V neste pack) `[CALC]` — modo *storage* do carregador | cheio ou vazio por muito tempo degrada e aumenta o risco |
| 6 | **Saco de LiPo (LiPo bag) para guardar e para carregar** | contém a propagação por alguns minutos; não é garantia |
| 7 | **NUNCA usar pack amassado, inchado, perfurado ou com cheiro doce** | é o pack que vai falhar. Descarte em ponto de coleta específico — **nunca no lixo comum** |
| 8 | **Nunca soldar/puncionar/morder** o pack; nunca deixar em carro quente | curto interno = fogo |
| 9 | **Extintor classe D (ou areia seca) por perto** | água em LiPo piora. `[EST]` balde de areia é o mais prático em bancada |
| 10 | **Conferir a tensão POR CÉLULA**, não só o total | o total pode estar em 22,2 V com uma célula em 3,0 V e outra em 4,2 V |

### 1.2 Números para o alarme de subtensão

| Condição | Por célula | Pack 6S | Ação |
|---|---:|---:|---|
| Cheio | 4,20 V | **25,2 V** | — |
| Nominal | 3,70 V | **22,2 V** | — |
| Alerta | 3,50 V | **21,0 V** | pousar |
| **Limite duro** | **3,30 V** | **19,8 V** | **cortar/aterrissar agora** |
| Armazenamento | 3,80 V | **22,8 V** | aterrissar/ajustar |

`[CALC]` — todos os valores 6S conferidos em `calcs_fase4.txt`.
`[EST]` A tensão cai sob carga: 19,8 V **em repouso** é diferente de 19,8 V a 30 A. Meça em
repouso para decidir e use o alarme sob carga com margem maior.

### 1.3 O que o hardware deste projeto faz e não faz

`[DISCO]` `lista_componentes_fase0.csv` prevê "Fusivel/e-fuse de entrada; 30 A; recomendado —
decisão pendente do Jailton" e um "Watchdog externo (opcional); corte de motores independente
do firmware; recomendado para failsafe". Ambos estão **pendentes de decisão**.

`[DISCO]` `FASE0_ESPECIFICACAO.md` §10.1 já registra tudo isso e §11 pergunta 11:
"Precisa de fusível/e-fuse de entrada? (recomendo sim)".

> **Minha posição:** e-fuse de entrada **sim**, watchdog externo **sim** se a placa for voar
> sobre qualquer coisa que não seja pasto vazio. Um firmware pode travar; um watchdog não.
> `[EST]`

---

## PARTE 2 — HÉLICES: REMOVIDAS, SEMPRE

**Regra absoluta de bancada: hélice removida em 100 % dos testes.**

`[DISCO]` `FASE0_ESPECIFICACAO.md` §10.2 já escreve:

> "1. **Hélices REMOVIDAS** sempre em bancada.
> 2. Primeira energização **com fonte de bancada com limite de corrente** (ex.: 1 A, 12 V),
>    **não** com a bateria. Só depois de tudo medido, bateria com hélice fora.
> 3. (...)
> 4. Só instalar hélice depois de: PWM medido, dead-time medido, corrente de fase coerente,
>    failsafe testado e motores girando controladamente nos 4 sentidos."

**Por quê.** Um motor brushless 2207 `[PREMISSA P-01]` com hélice de 5" gera empuxo de
centenas de gramas. O `[F0]` §7 estima **hélices 167 W** em cruzeiro. Uma hélice solta na
bancada é uma lâmina afiada girando a milhares de rpm, sem carenagem e sem ninguém
esperando. **Não é exagero: é amputação.**

**Checklist antes de energizar qualquer motor:**

- [ ] hélices **fora** da placa (não "só soltas" — fora)
- [ ] placa presa (não solta na mesa)
- [ ] óculos de proteção
- [ ] ninguém com a mão na área de giro
- [ ] fonte com limite de corrente ajustado
- [ ] botão/kill switch acessível `[EST]`
- [ ] extintor/areia por perto

---

## PARTE 3 — PRIMEIRA ENERGIZAÇÃO

### 3.1 Nunca com a bateria

`[DISCO]` §10.2 da Fase 0 e `PLANO_TESTE_BANCADA.md` passo 4. Sequência:

1. Fonte de bancada **em 19,8 V** `[CALC]` — que é a tensão que corresponde às simulações da
   Fase 2 (buck12 simulado com Vin = 19,8 V) **e** é pack vazio, logo o cenário mais seguro.
2. **Limite de corrente em 50 mA** para a primeira subida.
3. Subir a tensão devagar. Se a fonte entrar em modo corrente, **desligar**.
4. Só depois de ok: 200 mA → 500 mA → 1 A.
5. Bateria **só depois de todos os passos 1–14** do plano de teste.

### 3.2 Por que a fonte limitada salva a placa

Um curto de fase em 19,8 V sem limite entrega centenas de ampères por milissegundos — o
suficiente para abrir trilha, estourar FET e queimar o driver. Com limite em 50 mA, o curto
simplesmente **não tem energia para destruir nada**: a tensão colapsa e você vê.

---

## PARTE 4 — ALTA CORRENTE **NÃO** SE VALIDA EM SOFTWARE

Isto está escrito no enunciado do projeto e eu confirmo com os números do próprio projeto.

### 4.1 O que o cálculo diz e o que ele **não** prova

`[DISCO]` `fase3_pcb/calc_trilhas_vias_saida.txt` (fórmula IPC-2221, 2 oz, ΔT 10 °C):

```
VBAT continuo (cruzeiro 4 motores)         7.50    2.42mm
VBAT pico (rajada, <1 s)                  30.00   16.37mm
Fase do motor (RMS)                       15.00    6.29mm
I=120 A, dT=10 C -> largura = 110.78 mm  << nao existe trilha de 120 A continuo
```

`[DISCO]` `FASE0_ESPECIFICACAO.md` §7 conclui honestamente:

> "120 A é **pico de rajada**, não contínuo. O barramento será dimensionado para dezenas de
> ampères (cruzeiro ~7,5 A, nominal de projeto até 30 A) em **2 oz + camada interna dedicada
> + metal exposto**, e o pico é absorvido por massa de cobre e capacitância —
> **isso não se valida em software**."

### 4.2 O que **só** a bancada prova

| Grandeza | Número de projeto | Por que software não resolve |
|---|---|---|
| 30 A contínuo | 16,37 mm de trilha (ΔT 10 °C) | a fórmula é **empírica**; o cobre real, as vias e o fluxo de ar mudam tudo |
| Térmica do FET | `[CALC]` pico → Tj = 60,0 °C, com **`Rth_ja = 60 °C/W` `[PREMISSA]`** | o Rth é premissa, não datasheet. Só termopar/câmera resolve |
| Ripple no barramento | `[CALC]` 634 µV a 237 mV conforme C/ESR | o SPICE não tem ESL de trilha nem de via |
| EMI | spike de **60 V** calculado (100 nH, 30 A, 50 ns) | precisa de câmara/bancada de pré-conformidade |
| Vias | 40 vias de 0,3 mm por transição, margem 1,3× | `[DISCO]` o próprio calc marca: "**[NAO VERIFICADO nesta maquina: termografia/termopar]**" |

**Frase para levar a sério:** qualquer relatório — meu ou de qualquer um — que diga
"aguenta 30 A" sem termopar e sem carga real está **chutando**.

---

## PARTE 5 — O QUE CHECAR ANTES DE VOAR NO BRASIL

> ### ⚠️ Aviso de data: a regulamentação MUDOU em 2026.
> Consultei fontes ao vivo em **2026-09-11** e o cenário é este. **Reconfira nos sites
> oficiais antes de voar** — as regras abaixo entraram em vigor há poucos meses.

### 5.1 ANAC — cadastro, peso e categorias

`[FONTE]` OCA Drones, "RBAC 100: o que muda na regulamentação de drones no Brasil",
publicado 2026-06-17, consultado 2026-09-11 —
https://ocadrones.com/rbac-100-o-que-muda-na-regulamentacao-de-drones-no-brasil

| Fato | Conteúdo |
|---|---|
| **Resolução ANAC nº 805, de 15/06/2026** | aprova o **RBAC 100**, em vigor desde **16/06/2026**; **substitui integralmente o RBAC-E nº 94** (vigente desde 2017) |
| **Resolução nº 806** | trata drones **até 250 g** e aeromodelos recreativos |
| **Categoria Aberta** | peso em voo **até 25 kg**, VLOS/EVLOS, **altura máx. 120 m**, longe de terceiros → **sem autorização prévia** da ANAC se cumprir tudo |
| **Categoria Específica** | BVLOS **ou** > 25 kg **ou** perto de pessoas não envolvidas **ou** acima de 120 m → exige **SORA** (avaliação de risco) + autorização operacional |
| **Certificado de aeronavegabilidade** | `[FONTE]` mesmo artigo: o art. 100.201(a)(2) exige certificado de aeronavegabilidade válido para toda UA na categoria específica, exceto em cenário padrão publicado. "O SORA não elimina essa exigência" |
| **Cadastro SISANT** | aeromodelos **acima de 250 g** precisam de cadastro no SISANT, vinculado a CPF ou CNPJ, validade 24 meses `[FONTE]` Unmanned Airspace, consultado 2026-09-11 — https://www.unmannedairspace.info/latest-news-and-information/brazils-anac-publishes-new-risk-based-drone-rule-proposals-introducing-sora |
| **≤ 250 g** | dispensa cadastro na ANAC e seguro obrigatório; operador considerado licenciado automaticamente `[FONTE]` OCA Drones, idem |
| **Distância horizontal** | manter pelo menos **30 m** de pessoas não envolvidas `[FONTE]` idem |
| **Exame teórico** | obrigatório para piloto remoto (fora de recreativo e sub-250 g); **dispensa até 31/12/2026**, obrigatório a partir de **01/01/2027**; prova já disponível e gratuita `[FONTE]` idem |

### 5.2 DECEA — acesso ao espaço aéreo (SARPAS)

`[FONTE]` DroneShow, "DECEA atualiza ICA 100-40 para acesso ao espaço aéreo por drones",
consultado 2026-09-11 —
https://droneshowla.com/decea-atualiza-ica-100-40-para-acesso-ao-espaco-aereo-por-drones

| Fato | Conteúdo |
|---|---|
| **Portaria DECEA nº 2094/DNOR8**, de **18/03/2026** | publicada no BCA nº 058, de 30/03/2026 |
| **Vigência** | **01/07/2026** |
| **Revoga** | ICA 100-40/2023, **MCA 56-5/2023** (operações aéreas especiais) e **MCA 56-2/2023** (aeromodelos) |
| **Mudança mais importante** | **solicitação prévia de autorização para TODAS as aeronaves não tripuladas, independentemente do peso** — inclusive as de **até 250 g**, que antes tinham tratamento diferenciado, agora exigem autorização via **SARPAS** |
| **Prazo** | mínimo para operações com espaço aéreo segregado **caiu de 12 para 8 dias corridos** |
| **Zona UTM** | limite de **até 1 hora por voo** |
| **Áreas** | até **15 km²** em VLOS e até **30 km²** em BVLOS |
| **Área Adequada** | conceito novo: espaço aéreo com dimensões definidas, criado pelos Órgãos Regionais do DECEA |

`[FONTE]` A publicação oficial está em https://publicacoes.decea.mil.br/publicacao/ica-100-40
(consultado 2026-09-11): "Entrada em vigor na data de 1 de julho de 2026. Publicada no BCA Nº 58
de 30 de março de 2026."

### 5.3 Divergências ANAC × DECEA (vale a regra mais restritiva)

`[FONTE]` OCA Drones, consultado 2026-09-11 — **este é o trecho que mais exige atenção**:

| Tema | ANAC | DECEA | Na prática |
|---|---|---|---|
| **Altura recreativa** | 120 m (400 ft) | **60 m (200 ft)** | **60 m** |
| **Distância horizontal** | não fixa número, exige linha de visada | **300 m** do piloto | **300 m** |
| **Critério de peso** | "peso em voo" | "PMD" (peso máx. de decolagem) | conceitos próximos, nomes diferentes |
| **FPV** | — | FPV sem observador = **BVLOS** → segregação de espaço aéreo + certificação de aeronavegabilidade + **8 dias** de antecedência no SARPAS | óculos FPV exigem observador |

### 5.4 Distâncias de aeródromo — `[VERIFICAR]`

`[VERIFICAR]` **Não li o texto oficial da nova ICA 100-40.** Os números abaixo vêm de
**resumos secundários** em resultados de busca (canal e blog do setor), consultados
2026-09-11. **Trate como ordem de grandeza, não como regra.**

| Faixa / distância do aeródromo | Teto citado no resumo |
|---|---|
| < 1,7 km | proibido, qualquer altura |
| 1,7 – 2,3 km | 30 m |
| 2,3 – 2,9 km | 90 m |
| 2,9 – 3,5 km | 120 m |
| **> 3,5 km** | acima de 120 m |
| **Faixa Alfa (2 – 5,4 km)** | até 30 m |
| **Faixa Bravo (5,4 – 9,3 km)** | até 60 m |
| **além de 9,3 km** | teto padrão da Categoria Aberta (120 m) |
| Heliponto | **3 km** do centro, independente da altura do heliponto `[VERIFICAR]` |
| Aviação agrícola | 2 km de áreas com operações previstas `[VERIFICAR]` |

`[FONTE]` (para os trechos acima) resumos em https://futuriste.com.br/blog/nova-ica-100-40-como-as-regras-de-frz-e-o-sarpas-ng-impactam-seu-voo
e https://www.modelismobh.com.br/blog/legislacao-de-drones-no-brasil-conheca-os-pontos-mais-importantes
— ambos secundários, consultados 2026-09-11. **Reconfira na ICA 100-40 oficial.**

> **Nota de honestidade:** o vídeo/artigo que li também cita "até 9 km" para aeródromos
> cadastrados e uma "ZAD" com distância de 9 km na versão **de 2020** da ICA.
> **Há divergência entre os resumos. Leia o documento oficial.**

### 5.5 ANATEL — homologação do rádio

`[FONTE]` ABCP Certificação, "Homologação ANATEL de Drones e RPAS", consultado 2026-09-11 —
https://abcpcertificacao.com.br/certificacao-anatel/drones

| Fato | Conteúdo |
|---|---|
| **Norma base** | Resolução ANATEL **nº 715/2019** (avaliação da conformidade e homologação), com atualização pela **Resolução nº 780/2025** `[FONTE]` (segunda fonte: https://irlenmenezes.com.br/como-homologar-drone-anatel-2026, consultada 2026-09-11) |
| **Radiação restrita** | Resolução ANATEL **nº 680/2017** |
| **Requisitos de RF** | Ato ANATEL **nº 14.448/2017** (faixas 2,4 GHz e 5,8 GHz), alterado pelo Ato nº 1.379/2019 |
| **WiFi 2,4 GHz** | `[FONTE]` ABCP, "Produtos que precisam de homologação": equipamentos Wi-Fi (2,4 e 5 GHz), Bluetooth, ZigBee, LoRa etc. são **Equipamentos de Radiação Restrita (Categoria II)** e estão sujeitos a **homologação obrigatória** — https://abcpcertificacao.com.br/blog/produtos-que-precisam-homologacao-anatel (consultado 2026-09-11) |
| **O que é avaliado** | os **transmissores de RF** (controle remoto, telemetria, transmissor de vídeo), **não a plataforma** do drone |
| **Sanção** | sem homologação: **apreensão** e penalidades administrativas |
| **Infrações são paralelas** | `[FONTE]` irlenmenezes: "a infração é pela FALTA de homologação, independente de você já ter cadastrado o drone no SISANT ou pedido SARPAS — são obrigações paralelas, e faltar uma não substitui a outra" |

`[VERIFICAR]` — **não confirmei** se o módulo **ESP32-S3-WROOM-1** tem homologação ANATEL
própria válida para uso, e **não confirmei** se um drone caseiro com esse módulo e antena de
PCB precisa de nova avaliação. `[DISCO]` a Fase 0 §10.4 já registra a dúvida: "o rádio 2,4 GHz
do módulo precisa estar **homologado** (módulos certificados já vêm com homologação; a
antena/PCB não pode ser alterada sem reavaliação)". **Consulte a ANATEL.**

### 5.6 Locais proibidos e bom senso

- `[VERIFICAR]` proximidade de aeródromos/helipontos (tabela da §5.4 — **reconfira**)
- `[VERIFICAR]` áreas com restrição de voo (FRZ) — verificar antes no SARPAS
- `[EST]` **nunca** sobre pessoas, vias públicas, patrimônio de terceiros, aglomerações,
  unidades de saúde, presídios, áreas de segurança
- `[DISCO]` Fase 0 §10.4: "Este é um **equipamento caseiro**; em caso de queda, a
  responsabilidade é sua."
- `[EST]` **Não** use bloqueador/jammer de 2,4 GHz "por segurança" — além de ilegal,
  `[FONTE]` a **Resolução ANATEL** trata bloqueio de drones sob ato próprio com requisitos
  técnicos específicos (Ato nº 9.207, de 01/08/2025) —
  https://informacoes.anatel.gov.br/legislacao/.../1969-ato-10988 (consultado 2026-09-11).
  **Bloqueador não é item de projeto amador.**
- `[EST]` Seguro RC (Responsabilidade Civil) contra danos a terceiros: a Fase 0 §10.4 pede
  verificar "exigências de seguro". O seguro obrigatório só vale para operações na
  categoria específica `[VERIFICAR]` — para recreativo acima de 250 g, **vale confirmar**.

---

## PARTE 6 — RESUMO OPERACIONAL (o que fazer, na ordem)

```
ANTES DE SOLDAR
  [ ] ler MONTAGEM_ORDEM_DE_SOLDA.md §0 (a placa v6 NÃO está roteada)
  [ ] pulseira ESD, bancada aterrada, exaustão para solda com Pb

ANTES DE ENERgIZAR
  [ ] hélices FORA da placa
  [ ] passos 1–3 do plano de teste (inspeção + continuidade + resistência)
  [ ] fonte com limite de corrente em 50 mA

ANTES DE LIGAR O MOTOR
  [ ] passos 4–9 aprovados (trilhos, ripple, PWM, gate, DEAD-TIME)
  [ ] óculos de proteção, placa presa, ninguém perto
  [ ] hélices CONTINUAM fora

ANTES DE USAR A BATERIA
  [ ] passos 10–14 aprovados
  [ ] alarme de subtensão configurado (corte em 19,8 V do pack)
  [ ] carregador balanceador em mãos, LiPo bag, local não inflamável

ANTES DE VOAR
  [ ] cadastro SISANT (se > 250 g)
  [ ] autorização SARPAS (obrigatória para TODA UA desde 01/07/2026)
  [ ] homologação ANATEL do transmissor de RF
  [ ] seguro RC (conferir exigência)  [VERIFICAR]
  [ ] altura ≤ 60 m (o limite mais restritivo DECEA/ANAC)
  [ ] distância ≤ 300 m do piloto, VLOS, ≥ 30 m de pessoas
  [ ] NÃO voar perto de aeródromo/heliponto  [VERIFICAR tabela]
```

---

## PARTE 7 — O QUE NÃO ESTÁ VERIFICADO NESTA SEÇÃO

1. **Nada aqui foi testado por mim em bancada.** Zero LiPo, zero voo, zero multímetro.
2. **A legislação eu li em fontes secundárias** (blogs do setor, escritório de certificação),
   com data. **Não baixei o PDF do RBAC 100 nem o texto da ICA 100-40.** Tudo nesse material
   pode ter erro de interpretação de terceiros. **`[VERIFICAR]` no documento oficial.**
3. **A tabela de distâncias de aeródromo (§5.4) é a parte mais frágil** — os resumos que achei
   se contradizem entre si e com a versão de 2020 da ICA.
4. **Homologação ANATEL do ESP32-S3-WROOM-1 — `[VERIFICAR]`**, não confirmada.
5. **Seguro RC para uso recreativo acima de 250 g — `[VERIFICAR]`**, não confirmado.
6. **Regras mudam.** Estas entradas em vigor em jun/2026 e jul/2026; a obrigatoriedade do
   exame teórico só em 01/01/2027. **Reconsulte antes de cada temporada de voo.**
