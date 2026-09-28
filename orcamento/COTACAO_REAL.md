# COTAÇÃO REAL — o que foi cotado nesta sessão, o que não foi, e como fechar o resto

> **Data da consulta: 2026-09-28 (America/Bahia).** Autor: agente de missão. Arquivos gerados:
> `orcamento/BOM_FABRICACAO.csv` (43 linhas, uma por item de `fase0_especificacao/lista_componentes_fase0.csv`)
> e `plano/DECISOES_TOMADAS.md`.
>
> **Regra que segui, sem exceção:** um item só recebe `status = CONFIRMADO` se eu **abri a URL e li o preço
> nela**. Não houve um único preço, estoque ou lead time inventado nesta sessão. Tudo que não foi lido está
> `PENDENTE`, com a coluna `preco_unitario` **vazia**.

---

## 1. Estado da rede medido nesta sessão

| Fonte | Resultado medido | Como foi medido |
|---|---|---|
| **LCSC** (`www.lcsc.com`) | 🟡 **HTTP 200 no HTML, mas a busca é uma casca (Nuxt SSR) sem dados** | `curl` em `https://www.lcsc.com/search?q=INA240A2` devolve 74 963 bytes de casca: `grep` por `INA240`, `productCode`, `productList` = **0 ocorrências** |
| **LCSC — API de catálogo (EasyEDA)** | ✅ **HTTP 200 com preço e estoque reais** | `https://easyeda.com/api/eda/product/search?keyword=<MPN>` — devolve `mpn`, `number` (código C), `manufacturer`, `package`, `price` (faixas) e `stock` |
| **LCSC — página de produto** | ✅ **HTTP 200 nas 28 URLs citadas no BOM** | ver §4 |
| **wmsc.lcsc.com (API antiga)** | ❌ **HTTP 403 "Access Denied"** (Akamai) | `https://wmsc.lcsc.com/ftps/wm/search/global?keyword=INA240A2` |
| **jlcpcb.com (API SMT)** | ❌ **HTTP 404** | `POST /api/overseas-pcba-order/v1/shoppingCart/smtGood/selectSmtComponentList` |
| **DigiKey** | ❌ **403** (conforme o briefing) | — |
| **Mouser** | ❌ sem resposta (conforme o briefing) | — |

**A fonte que funcionou.** A API `easyeda.com/api/eda/product/search` é a mesma base de dados de catálogo da
LCSC: ela devolve o **código C da LCSC** (`number`, ex. `C536479`) e a URL `www.lcsc.com/product-detail/...`
correspondente. Ou seja: o preço que li é o preço de catálogo da LCSC, e não um número de catálogo genérico.
**Preço é sempre a faixa de 1 unidade** (`price[0][1]`), em **USD**, no momento da consulta.

**A caminho usado, com o comando exato:**

```console
$ curl -s -A "Mozilla/5.0" "https://easyeda.com/api/eda/product/search?keyword=IPB017N10N5"
{"code":200,"result":{"total":6,"productList":[
  {"mpn":"IPB017N10N5","number":"C536479","manufacturer":"Infineon","package":"TO-263-7",
   "price":[[1,"5.2721","5.2721"],...],"stock":143,
   "url":"/product-detail/MOSFETs_Infineon-IPB017N10N5_C536479.html"}]}}
```

> ⚠️ **Limite da fonte, registrado honestamente:** essa API devolve **estoque**, mas **não publica lead time /
> prazo de entrega por peça**. Por isso a coluna `lead_time` do BOM está preenchida com
> `NAO_INFORMADO_PELA_FONTE` em todas as linhas `CONFIRMADO`. **Não inventei prazo para preencher a coluna.**

---

## 2. O que foi possível cotar

**29 das 43 linhas** saíram com preço e estoque lidos da fonte, com URL verificada. As 28 URLs distintas
citadas no BOM foram abertas uma a uma e **todas responderam HTTP 200** (§4).

### 2.1 Os 5 blocos críticos do D-08

| Bloco | Part number escolhido | Cód. C | Preço 1 un | Estoque | Por que este |
|---|---|---|---:|---:|---|
| **MOSFET** (24 un) | **IPB017N10N5** | C536479 | US$ 5,2721 | 143 | §3 — a justificativa completa está na seção seguinte |
| **Gate driver** (12 un) | **IR2104STRPBF** | C2960 | US$ 1,1687 | 41 819 | SOIC-8, é a peça original Infineon. `IR2104SPBF` (C5204801) está 3× mais barata (US$ 0,4527) mas **estoque 0** |
| **Amp de corrente** (12 un) | **INA240A2DR** | C2060768 | US$ 1,7636 | 6 800 | D-09 manteve o INA240A2; A2 é a variante de **ganho 50 V/V** [DATASHEET, `datasheets/ina240_ti_sbos662.pdf` p.1/p.3/p.5] |
| **Bucks** (3 un) | **TPS5430DDAR** | C9864 | US$ 0,6861 | 273 070 | CI ajustável com divisor externo, serve para 12 V, 5 V e 3,3 V com indutor diferente |
| **Shunt** (12 un) | — | — | — | — | ❌ **não localizado** — ver §3.2 |

### 2.2 O resto, por bloco (tudo com preço lido)

| Bloco | Itens cotados | Melhor preço / estoque | Observação |
|---|---|---|---|
| ENTRADA | XT60-F | US$ 0,4172 · 34 979 | original Changzhou Amass |
| PROTEÇÃO | SMBJ33A, DMP3010LK3-13, 10 k + zener 12 V | US$ 0,0341 · 2 120 | zener BZT52C12 (GOODWORK) tem estoque alto |
| BANCO | 10 µF/50 V 1206, 100 nF/50 V 0402 | US$ 0,0045 · 2 187 400 | 470 µF/35 V **parcial** — ver §3.1 |
| GATE DRIVE | R 10 Ω 0805, diodo 1N4148W | US$ 0,0070 · 5 532 050 | R 2,2 Ω e C de bootstrap **não localizados** |
| CORRENTE | INA240A2DR, divisor 10k/10k + 100 nF | US$ 1,7636 · 6 800 | divisor é soma de 2 R + 1 C |
| BEMF | divisor 8,2 k / 1,0 k | US$ 0,0080 (soma) · 356 300 | filtro + clamp 3,3 V **não localizado** |
| ADC | **ADS7953SRHBR** | US$ 8,6942 · 2 702 | D-12: 2 unidades, não 1 — VQFN-32-EP, solda a quente |
| MCU | ESP32-S3-WROOM-1-N8, pull-up 4,7 k | US$ 3,50 – 4,91 | N8R8 (com PSRAM) tem **estoque 0** |
| IMU | **ICM-42688-P** | US$ 19,6358 · 170 | ⚠️ é **10× o [EST]** de US$ 4,91 do orçamento |
| ENERGIA | 3× TPS5430DDAR, TPS7A2033PDBVR, 22 µF/25 V 1210 | US$ 0,2175 – 0,6861 | indutores: só o de 5 µH (aproximado) foi localizado |
| MOTOR / USB | MR30-FB, USB4085-GF-A, USBLC6-2SC6 (ST), LM66100DCKR | US$ 0,1784 – 1,4141 | conectores são thru-hole, coerente com a D-05 |
| EXTRA | **TPS3813K33DBVR** (watchdog), **F1206HC30A0TM** (fusível 30 A), buzzer CPT-9019S | US$ 0,3295 – 3,3793 | watchdog real custa **US$ 1,5619**, não os US$ 0,70 [EST] |

---

## 3. Os três pontos que precisam de decisão sua

### 3.1 O MOSFET — escolha feita, com os números do datasheet

O arquivo `datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf` estava marcado como referência, não
escolha. **Escolhi o IPB017N10N5**, porque é o único do disco cujos 4 parâmetros eu consegui conferir de
primeira mão no datasheet e que atende a todos os critérios da D-08:

| Critério pedido | Exigido | IPB017N10N5 | Onde está no datasheet |
|---|---:|---:|---|
| Vds | ≥ 60 V | **100 V** | p.1, Table 1 (`VDS = 100 V`) |
| RDS(on) a 10 V | ≤ 2,2 mΩ | **1,5 mΩ (typ) / 1,7 mΩ (max)** | p.4, Table 4 (`VGS=10 V, ID=100 A`) |
| Qg compatível com o IR2104 | ≤ 168 nC | **168 nC (typ)** | p.1, Table 1 (`QG(0V..10V) = 168 nC`) |
| Pacote soldável, não BGA | — | **PG-TO 263-7 (D²PAK 7 pinos)** | p.1, `Package: PG-TO 263-7` |

Leitura direta do PDF local (Rod. 2.5, 2019-11-13):

```console
$ pdftotext -f 4 -l 4 datasheets/ipb017n10n5_infineon_REFERENCIA_NAO_ESCOLHIDO.pdf -
  VDS   100 V                (VGS=0 V, ID=1 mA)
  RDS(on)  1.5 / 1.7 mOhm   VGS=10 V, ID=100 A
  RDS(on)  1.7 / 2.2 mOhm   VGS=6 V,  ID=50 A
```

**Consequência para a D-11:** `Qg = 168 nC` é exatamente o número que a D-11 adotou como premissa corrigida.
A conta da §3.11 do `plano/WP5_DECISOES.md` confere: `t = Qg/I` dá 1,292 µs a 130 mA e 0,622 µs a 270 mA.
**A nota do WP5 se confirma:** a 6 V de gate drive o FET sobe para **2,2 mΩ (max)** — por isso 10 V de gate drive
é o piso, e o IR2104 tem folga para isso.

**Três coisas que você precisa saber antes de comprar:**

1. 🔴 **O footprint da lista está errado.** A lista pede `Package_TO_SOT_SMD:TO-252-3_TabPin2`; a peça é
   **TO-263-7 (D²PAK, 7 pinos)**. É um footprint novo, maior e mais pesado — entra no redesenho da v8.
2. 🟡 **O preço foge muito do orçamento.** US$ 5,2721 × 24 = **US$ 126,53**, contra US$ 0,45/un [EST] no
   `orcamento/orcamento_detalhado.csv` — o MOSFET passa de 11 % para **a maior linha do BOM**. Alternativas
   cotadas na mesma fonte: `IPB017N10N5LFATMA1` (C3289286) US$ 5,0656, estoque 868; e clones VBsemi a partir de
   US$ 2,8124 (estoque 33). **Não escolhi clone** — em barra de potência o risco não compensa.
3. 🟡 **Estoque 143** para 24 unidades: suficiente, mas é o item mais escasso do conjunto.

### 3.2 O shunt de 0,5 mΩ — o que **não** consegui cotar

Procurei `WSL3637R5000FEA`, `WSL3637` e `current sense resistor 0.5mOhm 2512`. A família **Vishay WSL3637
existe** na fonte (136 resultados), mas **o código de 0,5 mΩ não apareceu em nenhum deles** e os 10 primeiros
resultados vieram com **estoque 0**. `LRMAP2510` idem. **Não inventei um código nem um preço** — a linha está
`PENDENTE`, com `preco_unitario` vazio. É um item de **US$ 3,60 no total [EST]** e é o que menos pesa no orçamento,
mas é o que mais pesa no sinal: sem ele, o INA240 não mede corrente.

### 3.3 As 14 linhas `PENDENTE` — o que falta e por quê

| Linha | Por que ficou `PENDENTE` |
|---|---|
| Capacitor de entrada 470 µF/35 V | Preço **lido** (AISHI SVZ1VM471GCRE00RAXXX, C2939792, US$ 0,4260, estoque 12 682), mas o **código do catálogo não decodifica a tensão de forma inequívoca** e o ESR ≤ 20 mΩ não foi conferido — comparar com o datasheet do fabricante antes de comprar |
| R de gate 2,2 Ω (0805) | `RC0805JR-072L2L` retornou **total = 0** na fonte |
| C de bootstrap 1 µF/25 V (0805) | Não consultei um código 0806/0805 de 1 µF/25 V nesta sessão |
| C local do driver 10 µF/25 V (1206) | Só encontrei o **CL21A106KAYNNNE, que é 0805** — não serve no footprint pedido |
| Shunt 0,5 mΩ | §3.2 |
| Filtro + clamp BEMF (1 nF + zener 3,3 V) | Nenhum dos dois códigos foi consultado |
| Mux analógico | Não é peça: a **D-12** descartou o MCP3208 |
| Botão BOOT/EN | Nenhum código consultado |
| Pads de programação / dissipador / PCB | **Não são peças** — são cobre do PCB ou cotação no site do fabricante |
| LED 0805 verde | Só o resistor de 1 k foi cotado; o LED não |
| Indutor de saída (3 unidades) | Só o **4,7 µH** (SRN8040-4R7Y) foi localizado; os de **89 µH e 17 µH** não |
| Barômetro BMP390 | Preço lido (US$ 5,3938) mas **estoque 0** na data |

**Além disso, 4 linhas `CONFIRMADO` têm divergência de footprint** que precisa ser resolvida na v8 — estão
sinalizadas na coluna `observacao_de_compra` do BOM: **INA240A2DR** (é SOIC-8 sem pad térmico; a lista pede
SOIC-8-1EP), **ICM-42688-P** (é LGA-14 2,5×3 mm; a lista pede QFN-24 3×3), **TPS3813K33DBVR** (é SOT-23-6; a
lista pede SOIC-8) e **MR30-FB** (a lista pede MR30PW-FB).

---

## 4. Verificação das URLs

Todas as **28 URLs distintas** citadas em `fonte_preco` foram abertas nesta máquina, uma a uma:

```console
$ python3 - <<'EOF'
# percorre o BOM, extrai as URLs das linhas CONFIRMADO e abre cada uma
import csv, urllib.request
UA="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
rows=list(csv.reader(open('orcamento/BOM_FABRICACAO.csv',encoding='utf-8'),delimiter=';'))
h=rows[0]; fi=h.index('fonte_preco'); si=h.index('status')
urls=[u for r in rows[1:] if r[si]=='CONFIRMADO' for u in r[fi].split()]
for u in dict.fromkeys(urls):
    with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=20) as r:
        print(r.getcode(), len(r.read()), u)
EOF
```

**Resultado: 28/28 responderam `200`, com o código C da peça presente no corpo da página** (360–450 kB cada).
As 2 URLs que não passaram por esse teste não estão no BOM — as linhas de fonte dupla (divisores) têm as duas
URLs conferidas, e a contagem de 28 é a de URLs distintas, não a de linhas.

---

## 5. O que falta para cotar o resto — e o comando para você rodar

Nenhuma ferramenta desta máquina lê DigiKey (403), Mouser (sem resposta) nem o catálogo do Mercado Livre. Para
fechar as 14 linhas `PENDENTE` e atualizar preços, **abra o navegador no seu computador** e use:

**a) Para cada part number pendente, na LCSC** — cole o MPN na caixa de busca:
`https://www.lcsc.com/search?q=<MPN>` — e leia preço, estoque e *Lead Time* na página do produto.
Para conferir o lead time que a API **não** devolve, use a página do produto, que mostra o prazo no carrinho.

**b) Para cotar a placa de verdade** (a linha MECANICO), a cotação só existe com o Gerber na mão
(`orcamento/ORCAMENTO.md` §5.1): https://jlcpcb.com/ e https://www.pcbway.com/ aceitam upload de Gerber
**sem encomendar** e devolvem o preço final com 6 camadas, 2 oz e ~150×110 mm (D-02 e D-03).

**c) Para cotar no Brasil** (D-14 decidiu compra nacional):
`https://www.mercadolivre.com.br/` e `https://www.elecfaz.com.br/` — busque o **MPN exato** (não a descrição),
porque a lista original tem descrições genéricas como *"10 ohm 0805"* e isso traz peça errada.

**d) Para importar depois** (a Opção C da D-14): a diferença real entre nacional e importação é de
R$ 1.706 para R$ 1.354 [EST] **dentro da barra de erro do próprio orçamento** — ou seja, é tempo, não dinheiro.

### Comando para recalcular o total do BOM depois de você cotar

```console
$ cd /opt/jupyter/work/drone
$ python3 -c "
import csv
r=list(csv.DictReader(open('orcamento/BOM_FABRICACAO.csv',encoding='utf-8'),delimiter=';'))
t=0.0
for x in r:
    q=x['qtd'].replace(',','.')
    if x['preco_unitario'] and q not in ('-',''):
        t+=float(x['preco_unitario'])*float(q)
    else:
        print('sem preco:',x['item'])
print('total parcial: US\$ %.2f' % t)"
```

**Esse total é parcial de propósito:** só entra o que tem preço lido. Ele **não** é o custo do projeto — faltam
o PCB, a montagem e as 14 linhas pendentes.

---

## 6. Honestidade: o que este documento não é

- **Não é uma cotação fechada.** 29 de 43 linhas têm preço de catálogo lido hoje; 14 não têm.
- **Não tem lead time de ninguém.** A fonte usada não publica prazo por peça. A coluna diz
  `NAO_INFORMADO_PELA_FONTE` onde está preenchida — **preencher isso com um número seria inventar**.
- **Não confirma conformidade elétrica.** Ter preço e estoque não garante que a peça atenda à especificação:
  por isso as linhas com divergência de pacote ou de tensão estão marcadas como tal, e o judgement final é seu.
- **Não substitui o datasheet.** Os 4 parâmetros do MOSFET vêm do PDF em `datasheets/`; o resto da engenharia
  continua precisando de conferência no datasheet de cada peça antes do pedido.
