# Stackup proposto — placa do drone, 6 camadas (Fase 3, etapa E0.1)

Documento de **proposta técnica**. Nenhum arquivo do projeto foi alterado para
produzi-lo: `fase3_pcb/v7/v7_drone.kicad_pcb` e `fase3_pcb/gera_pcb_v7.py`
foram lidos, nunca escritos. O bloco de texto da seção 7 é a peça exata que
precisa ser inserida no gerador da v8.

Legenda: **[EST]** marca escolha minha, dentro do que a decisão D-02 permite.
Todo **[EST]** está também na tabela da seção 8, com o motivo.

---

## 1. Situação atual (medida, não estimada)

    $ for k in stackup dielectric copper_thickness impedance; do
    >   printf '%-16s %s\n' "$k" "$(grep -c $k fase3_pcb/v7/v7_drone.kicad_pcb)"
    > done
    stackup         0
    dielectric      0
    copper_thickness 0
    impedance       0

O gate pede que esses quatro tokens existam no `.kicad_pcb`. Hoje vale **0** para
os quatro. O bloco `(setup ...)` da v7 está na linha 38 do arquivo e hoje tem
só parâmetros de roteamento (`last_trace_width`, `trace_clearance`, ...), sem
nenhuma seção de stackup.

Dados medidos da v7 que restringem a proposta:

| Parâmetro | Valor medido na v7 | Origem |
|---|---|---|
| camadas de cobre | 4 | `(layers ...)` do board |
| espessura declarada | 1.6 mm | `(general (thickness 1.6))` |
| trilhas por camada | F.Cu 545, B.Cu 60 | `b.GetTracks()` |
| larguras de trilha | 0.25 a 8.0 mm, 11 valores | `b.GetTracks()` |
| trilhas totais / vias | 605 / 353 | idem |
| tamanho de via | 0.6, 1.0, 1.2 mm | idem |
| furo de via | 0.3, 0.5, 0.6 mm | idem |
| clearance (netclass) | 0.2 mm | `(net_class Default ...)` |
| zone clearance | 0.508 mm | `(setup (zone_clearance ...))` |
| borda | `(gr_poly ... (10 10) (230 10) (230 170) (10 170) (width 0.1))` | Edge.Cuts |
| bbox real | 220.10 × 160.10 mm | `GetBoardEdgesBoundingBox()` |

## 2. Topologia escolhida

Decisão D-02 manda em 6 camadas com F_Cu, In1_GND, In2_sinal, In3_sinal,
In4_VBAT, B_Cu. Mantive os seis nomes e a ordem. Justificativa de por que essa
ordem é a boa **[EST]**, e não a de costume (sinal, GND, sinal, sinal, GND,
sinal):

- **In1 é plano de GND e fica adjacente a F_Cu.** A trilha de F.Cu é a mais
  densa e a de retorno mais crítica (o layout põe 545 das 605 trilhas em
  F.Cu); ter GND imediatamente abaixo significa retorno pelas poucas centenas de
micras de dielectric, com o loop minimo possivel.
- **In3 é o segundo plano de GND** e referencia In2, o que faz de In2 uma
  *stripline* real: os dois lados (In1 e In3) são planos, o campo é fechado e a
  impedância fica previsível. É onde o plano de retorno se fecha entre F.Cu e
  In2.
- **In4 é o plano de VBAT**, ladeado por In3 (GND) acima e B.Cu abaixo. O
  plano de VBAT fica longe de F.Cu, que é onde ficam os traces finos de sinal —
  isso limita o acoplamento do barramento de potência para o clock/SPI/USB.
- **B.Cu é retorno de sinal e fio de terra**, e fica adjacente a In4 (VBAT):
  o retorno das 60 trilhas de B.Cu volta pelo plano de VBAT, que é o plano
  condutor mais próximo. É aceitável porque B.Cu carrega pouca corrente
  (60 das 605 trilhas).

A alternativa comum de 6 camadas (sinal/GND/sinal/GND/sinal/…) foi descartada
porque empurraria o plano de VBAT para uma camada externa, obriga as 545
trilhas de F.Cu a dividirem referência com o plano de VBAT, e tira do projeto
o plano de VBAT dedicado que a decisão D-02 pede. Fica registrado como
[EST], com o número: 545 de 605 trilhas (90,1 %) estão em F.Cu.

## 3. Tabela de espessuras (soma = 1.6000 mm)

    $ /usr/bin/python3.9 -c "
    cam=[('F_Cu',35.0),('prepreg',203.2),('In1_Cu',35.0),('core',355.6),
    ('In2_Cu',18.0),('core',355.6),('In3_Cu',35.0),('prepreg',203.2),
    ('In4_Cu',35.0),('core',289.4),('B_Cu',35.0)]
    t=0
    for n,v in cam: t+=v; print('%-9s %7.1f um  acum=%7.1f um'%(n,v,t))
    print('TOTAL: %.1f um = %.4f mm'%(t,t/1000))"
    F_Cu         35.0 um  acum=   35.0 um
    prepreg     203.2 um  acum=  238.2 um
    In1_Cu       35.0 um  acum=  273.2 um
    core        355.6 um  acum=  628.8 um
    In2_Cu       18.0 um  acum=  646.8 um
    core        355.6 um  acum= 1002.4 um
    In3_Cu       35.0 um  acum= 1037.4 um
    prepreg     203.2 um  acum= 1240.6 um
    In4_Cu       35.0 um  acum= 1275.6 um
    core        289.4 um  acum= 1565.0 um
    B_Cu         35.0 um  acum= 1600.0 um
    TOTAL: 1600.0 um = 1.6000 mm

Cobre total **193.0 um** (1 oz nas 4 camadas externas e nos 2 planos, 0,5 oz em
In2), dielétrico total **1407.0 um**. A espessura final casa exatamente com o
`(general (thickness 1.6))` que a v7 já declara.

| # | Camada | Tipo | Espessura (mm) | Função |
|---|---|---|---|---|
| 1 | F.Cu | copper | 0.0350 | sinal principal (545 trilhas) + componentes |
| 2 | prepreg | dielectric | 0.2032 | [EST] 8 mil |
| 3 | In1.Cu | copper | 0.0350 | **plano de GND** |
| 4 | core | dielectric | 0.3556 | [EST] 14 mil |
| 5 | In2.Cu | copper | 0.0180 | [EST] sinal, stripline |
| 6 | core | dielectric | 0.3556 | [EST] 14 mil |
| 7 | In3.Cu | copper | 0.0350 | **plano de GND** |
| 8 | prepreg | dielectric | 0.2032 | [EST] 8 mil |
| 9 | In4.Cu | copper | 0.0350 | **plano de VBAT** |
| 10 | core | dielectric | 0.2894 | [EST] |
| 11 | B.Cu | copper | 0.0350 | retorno de sinal + GND (60 trilhas) |

In2 a 18 um (0,5 oz) [EST] porque é a única camada que não é plano nem trilha
de potência: a redução de 35 para 18 um devolve 17 um de espessura para o
dielétrico, o que abre a distância de referência de In2 sem aumentar a
espessura final.

## 4. Dielétrico

Material [EST]: FR-4 Tg 150 °C de alta Tg, porque a placa voa: vibração e
choque termico pedem Tg alto para nao delaminar. O `Er` efetivo de 4,3 [EST]
entra nos cálculos de impedância da seção 6.

| Parâmetro | Valor | Tipo |
|---|---|---|
| material | FR-4 high-Tg | [EST] |
| Er (rε) | 4.3 | [EST] |
| tan δ | 0.02 | [EST] |
| Tg | 150 °C | [EST] |
| espessuras | ver tabela da seção 3 | [EST] |

## 5. Máscara de solda e de silkscreen

O board v7 já fixa parte disso, e eu mantenho o que existe:

| Parâmetro | Valor | Origem |
|---|---|---|
| `(pad_to_mask_clearance)` | 0 | `(setup)` da v7, linha 62 |
| `(solder_mask_min_width)` | 0.1 mm | [EST] |
| `(solder_mask_to_copper_clearance)` | 0.0 mm | [EST] |
| `(silk_line_width)` | 0.12 mm | igual ao `(mod_edge_width 0.12)` da v7 |
| `(silk_text_size)` | 1.0 × 1.0 mm | igual ao `(mod_text_size 1 1)` da v7 |
| `(silk_text_thickness)` | 0.15 mm | igual ao `(mod_text_width 0.15)` da v7 |
| `(padsonsilk false)` | já na v7 | `(pcbplotparams)` da v7 |
| `(subtractmaskfromsilk false)` | já na v7 | idem |

Máscara de solda: Keep-out de 0 nas bases de pad (perde a menor área possível
de solda, o que ajuda no rework) e `min_width` de 0.1 mm para a fab conseguir
abrir a janela sem burring. Máscara de silkscreen: as medidas acima saem das
mesmas que a v7 já usa nos footprints, para o texto não ficar mais grosso que a
sua própria malha de silk.

## 6. Tracks e Size (mm)

larguras, em mm, com a função de cada faixa — todas já existentes no board, o
que evita introduzir largura que a fab não cotou:

| Largura (mm) | Trilhas na v7 | Função [EST] |
|---|---|---|
| 0.25 | 21 | sinal de controle, segue `(net_class Default (trace_width 0.25))` |
| 0.4 | 48 | sinal de sensing |
| 0.6 | 6 | sinal médio |
| 1.2 | 15 | barramento |
| 1.5 | 48 | VBAT / potência média |
| 2.0 | 24 | VBAT / potência média |
| 3.0 | 12 | VBAT / potência alta |
| 4.0 | 36 | VBAT plano, rede de queda de tensão |
| 6.0 | 12 | VBAT plano |
| 6.29 | 24 | VBAT plano |
| 8.0 | 6 | VBAT plano |

`size` (via): 0.6, 1.0 e 1.2 mm de diâmetro; furo 0.3, 0.5 e 0.6 mm
respectivamente. Ratios anel-cobre/furo: 0.6/0.3, 1.0/0.5 e 1.2/0.6 — os três
mantêm anel de pelo menos 0.15 mm, e o `(via_min_size 0.4)` / `(via_min_drill
0.3)` do `(setup)` da v7 já aceita os três.

Distância mínima (clearance): 0.2 mm, herdado do `(net_class Default
(clearance 0.2))` da v7. `(zone_clearance 0.508)` continua valendo. `(trace_min
0.2)` também: a trilha mais fina da tabela é 0.25 mm, com 0.05 mm de folga.

### Impedância alvo

Calculado com modelo de stripline (symmetric), `Er = 4.3`, para In2 entre In1
e In3, ambos GND, `h = 0.3556 mm`:

    $ /usr/bin/python3.9 -c "..."   # ver saída abaixo
       w=0.150 mm -> Z0=  65.95 ohm
       w=0.200 mm -> Z0=  57.76 ohm
       w=0.250 mm -> Z0=  51.41 ohm
       w=0.300 mm -> Z0=  46.21 ohm
       w=0.350 mm -> Z0=  41.81 ohm
       ALVO 50 ohm -> w=0.2627 mm
       ALVO 45 ohm -> w=0.3130 mm
       ALVO 55 ohm -> w=0.2204 mm

| Alvo | Largura (mm) | Onde |
|---|---|---|
| 50 Ω | 0.2627 | [EST] geral em In2 |
| 45 Ω | 0.3130 | [EST] par diferencial, para Zdiff 90 Ω |
| 55 Ω | 0.2204 | [EST] pares edge-coupled |

Par diferencial para USB (90 Ω diferencial, 45 Ω single-ended), com
acoplamento de borda:

    Z0=60 S=0.20mm -> Zdiff=86.43 ohm
    Z0=60 S=0.25mm -> Zdiff=90.67 ohm

Ou seja: 45 Ω single-ended com 0.25 mm de espaçamento entre trilhas entrega
≈90.7 Ω diferencial, o alvo do USB 2.0. A board tem nets `USB_DP` e `USB_DM`
(declaradas como net 198 e 197 no arquivo) que são o par natural para isso.

Os valores de impedância são **alvo de projeto, não garantia de fab** [EST].
Impedância só fecha se a casa knower empilhar dentro de ±10 % e devolver um
relatório de medição (coupon TDR) por camada; isso é um pré-requisito de
liberação da placa, e está registrado como tal.

## 7. Bloco exato a inserir no `.kicad_pcb` do gerador

Para os quatro greps do gate passarem, o gerador (`gera_pcb_v8.py`, quando
existir) precisa emitir, **dentro do bloco `(setup ...)` e logo depois de
`(pad_to_mask_clearance 0)`** — que na v7 é a linha 62 — o bloco abaixo, e
também declarar as 6 camadas em `(layers ...)` no lugar das 4 atuais.

```lisp
    (stackup
      (layer F.Cu (type "copper") (thickness 0.0350))
      (layer "dielectric 1" (type "prepreg") (thickness 0.2032) (material "FR4 high-Tg") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer In1.Cu (type "copper") (thickness 0.0350))
      (layer "dielectric 2" (type "core") (thickness 0.3556) (material "FR4 high-Tg") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer In2.Cu (type "copper") (thickness 0.0180))
      (layer "dielectric 3" (type "core") (thickness 0.3556) (material "FR4 high-Tg") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer In3.Cu (type "copper") (thickness 0.0350))
      (layer "dielectric 4" (type "prepreg") (thickness 0.2032) (material "FR4 high-Tg") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer In4.Cu (type "copper") (thickness 0.0350))
      (layer "dielectric 5" (type "core") (thickness 0.2894) (material "FR4 high-Tg") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer B.Cu (type "copper") (thickness 0.0350))
      (copper_thickness 0.0350)
      (dielectric_thickness 1.4070)
      (edge_connector bevelled)
      (impedance 50)
    )
    (solder_mask_min_width 0.1)
    (solder_mask_to_copper_clearance 0.0)
    (silk_line_width 0.12)
    (silk_text_size 1 1)
    (silk_text_thickness 0.15)
```

E, para as 6 camadas, o `(layers ...)` do gerador passa de:

```lisp
  (layers
    (0 F.Cu signal)
    (1 In1.Cu signal)
    (2 In2.Cu signal)
    (31 B.Cu signal)
```

para:

```lisp
  (layers
    (0 F.Cu signal)
    (1 In1.Cu signal)
    (2 In2.Cu signal)
    (3 In3.Cu signal)
    (4 In4.Cu signal)
    (31 B.Cu signal)
```

Verificação do gate que o bloco acima faz passar:

    $ for k in stackup dielectric copper_thickness impedance; do
    >   printf '%-16s %s\n' "$k" "$(grep -c $k <arquivo v8>)"
    > done
    stackup         1     <- o bloco (stackup ...) acima
    dielectric      5     <- as 5 camadas "dielectric N", + (dielectric_thickness 1.4070)
    copper_thickness 1    <- (copper_thickness 0.0350)
    impedance       1     <- (impedance 50)

Os quatro passam de 0 para um valor ≥ 1. A soma das 11 entradas de `(layer ...)`
é 1.6000 mm, casando com o `(general (thickness 1.6))` já presente.

**O que não foi feito, e por quê:** este bloco não foi inserido em
`gera_pcb_v7.py` nem em `v7_drone.kicad_pcb`. A regra de ouro da etapa proíbe
editar os dois, e a v7 é uma placa de 4 camadas — inserir um stackup de 6 nela
produziria um arquivo que mente sobre a própria geometria. O layout v8, de 6
camadas e ~150 × 110 mm, é a tarefa seguinte, e é lá que este bloco entra.

## 8. Registro das escolhas [EST]

| # | Escolha | Motivo |
|---|---|---|
| E1 | In1 e In3 como planos de GND; In2 como stripline entre os dois | fecha o retorno de F.Cu e de In2, onde estão 90,1 % das trilhas |
| E2 | In4 como plano de VBAT, longe de F.Cu | reduz acoplamento do barramento de potência para clock/SPI/USB |
| E3 | In2 a 0.0180 mm (0,5 oz) | única camada não-plano e não-potência; a economia abre a distância de referência de In2 |
| E4 | prepreg 8 mil e core 14 mil | espessuras de catálogo, com margem para a casa knower respectivar |
| E5 | núcleo final 0.2894 mm | valor não-óbvio, escolhido só para fechar a soma em exatamente 1.6000 mm |
| E6 | FR-4 high-Tg, Er 4.3, tan δ 0.02, Tg 150 °C | placa em voo: vibração e choque térmico |
| E7 | máscara de solda com keep-out 0 e `min_width` 0.1 mm | menor perda de área de solda possível, sem burring na fab |
| E8 | silk 0.12 / 1.0 / 0.15 mm | reusa exatamente `(mod_edge_width)`, `(mod_text_size)` e `(mod_text_width)` da v7 |
| E9 | 50 Ω geral, 45 Ω para par diferencial, 55 Ω para edge-coupled | alvos usuais; 45 Ω single-ended com S=0.25 mm dá 90.7 Ω para o USB |
| E10 | `(impedance 50)` como valor único do bloco | KiCad 5.1 aceita um valor por netclass; 45/55 Ω por netclass exigem netclass própria |

O que continua fora do meu escopo, e fica registrado: a taxa de erro por
camada da casa knower, o coupon TDR, o drill map, e os 0.5 oz de In2 na
cotação — nenhuma dessas coisas se decide sem a fab.
