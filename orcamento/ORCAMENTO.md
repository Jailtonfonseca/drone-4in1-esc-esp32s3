# Orcamento de componentes -- drone (ESC 4x + ESP32-S3 numa PCB)

Gerado por `orcamento.py` em 11/09/2026. Quantidades vindas de
`fase0_especificacao/lista_componentes_fase0.csv` (43 linhas, 1 placa).

**Dolar usado:** R$ 5.1312 (Bloomberg Linea, 11/09/2026).

## 1. Resumo

| Cenario | O que e' | Total |
|---|---|---|
| A -- compra nacional | Mercado Livre / lojas BR, componentes + frete | **R$ 1706** |
| A -- banda honesta | k de markup entre 2.7 e 3.7 | R$ 1448 a R$ 1965 |
| B -- importacao direta | LCSC + frete + II 60% (menos US$30) + ICMS 17% + IOF 3,5% | **R$ 1354** |
| Cenario A + PCB | 5 placas nuas, 4 camadas, 2 oz (220x160 mm) | + R$ 359 a R$ 770 |
| Cenario B + montagem | PCBA JLCPCB (setup + joints + stencil + partes extendidas) | + R$ 210 (US$ 41) |

- Componentes, valor de catalogo (US$ LCSC-equivalente): **US$ 100.88**
- Com folga de lote/MOQ (x1.15): **US$ 116.01**
- Linhas com preco cotado agora: 3 de 43 | apenas estimativa: 37

## 2. Custo por bloco (cenario nacional)

| Bloco | Linhas | US$ | R$ | % |
|---|---:|---:|---:|---:|
| CORRENTE | 3 | 35.16 | 577 | 34.9% |
| ENERGIA | 6 | 11.25 | 185 | 11.2% |
| POTENCIA | 2 | 10.80 | 177 | 10.7% |
| ADC | 2 | 10.40 | 171 | 10.3% |
| BANCO | 3 | 8.57 | 141 | 8.5% |
| GATE DRIVE | 6 | 6.36 | 104 | 6.3% |
| IMU | 1 | 4.91 | 81 | 4.9% |
| MCU | 4 | 3.64 | 60 | 3.6% |
| BAROMETRO | 1 | 3.50 | 57 | 3.5% |
| EXTRA | 4 | 1.64 | 27 | 1.6% |
| MOTOR | 1 | 1.40 | 23 | 1.4% |
| USB | 3 | 1.22 | 20 | 1.2% |
| PROTECAO | 3 | 0.73 | 12 | 0.7% |
| BEMF | 2 | 0.72 | 12 | 0.7% |
| ENTRADA | 1 | 0.58 | 10 | 0.6% |
| MECANICO | 1 | 0.00 | 0 | 0.0% |
| **TOTAL** | 43 | **100.88** | **1656** | 100% |

## 3. Detalhe linha a linha

| Bloco | Item | Qtd | US$/un | US$ tot | R$ nac | Conf. | Fonte |
|---|---|---:|---:|---:|---:|---|---|
| ENTRADA | Conector de bateria | 1 | 0.5800 | 0.58 | 9.52 | [CALC] | ML: XT60 3 pares R$28,78 -> R$9,59/par / (5,1312*3,2) |
| PROTECAO | TVS unidirecional | 1 | 0.1200 | 0.12 | 1.97 | [EST] | SMBJ33A SMB, ~US$0,10-0,15 no LCSC |
| PROTECAO | P-FET anti-inversao | 1 | 0.5500 | 0.55 | 9.03 | [EST] | P-ch 40V TO-252, ~US$0,4-0,8 |
| PROTECAO | Resistor de gate do P-FET + zenner | 2 | 0.0300 | 0.06 | 0.99 | [EST] | kit de passivos |
| BANCO | Capacitor de entrada | 6 | 1.1000 | 6.60 | 108.37 | [EST] | polimero SMD 470uF/35V (PTH radial low-ESR = R$1,67 COT moduloeletronica) |
| BANCO | Ceramico de alta freq. | 12 | 0.1400 | 1.68 | 27.59 | [EST] | 10uF/50V X7R 1206 |
| BANCO | Ceramico de alta freq. | 48 | 0.0060 | 0.29 | 4.73 | [EST] | 100nF/50V X7R 0402 |
| POTENCIA | MOSFET N | 24 | 0.4500 | 10.80 | 177.33 | [EST] | N-ch 40V ~2-3 mOhm TO-252; NCE3050K (30V) = US$0,09 COT LCSC, 40V e' mais caro |
| POTENCIA | Dissipador / area de cobre | - | 0.0000 | 0.00 | 0.00 | [-] | GERADO NO LAYOUT (custo no preco do cobre da PCB) |
| GATE DRIVE | Driver half-bridge single-input | 12 | 0.3000 | 3.60 | 59.11 | [EST] | EG2134/EG2133: EG2133 = US$0,2222 COT (LCSC) |
| GATE DRIVE | Resistor de gate | 24 | 0.0100 | 0.24 | 3.94 | [EST] | 10 ohm 0805 |
| GATE DRIVE | Resistor de gate (desliga) | 24 | 0.0100 | 0.24 | 3.94 | [EST] | 2,2 ohm 0805 |
| GATE DRIVE | Capacitor de bootstrap | 12 | 0.0300 | 0.36 | 5.91 | [EST] | 1uF/25V X7R 0805 |
| GATE DRIVE | Diodo de bootstrap | 12 | 0.0200 | 0.24 | 3.94 | [EST] | ultrarrapido 100V SOD-123 |
| GATE DRIVE | Capacitor local do driver | 12 | 0.1400 | 1.68 | 27.59 | [EST] | 10uF/25V X7R 1206 |
| CORRENTE | Shunt de fase | 12 | 0.3000 | 3.60 | 59.11 | [EST] | 0,5 mOhm 2W 2512 manganina; eBay 50pcs US$13,30 = US$0,27 COT |
| CORRENTE | Amplificador diferencial | 12 | 2.6000 | 31.20 | 512.30 | [EST] | INA240A2; modulo breakout = US$7,80 COT (7semi); CI ~US$2,5-3,3 |
| CORRENTE | Divisor de referencia | 12 | 0.0300 | 0.36 | 5.91 | [EST] | 2x R 0603 1% + 100nF |
| BEMF | Divisor de fase | 12 | 0.0200 | 0.24 | 3.94 | [EST] | 2x R 0603 1% por fase |
| BEMF | Filtro + clamp | 12 | 0.0400 | 0.48 | 7.88 | [EST] | 1nF 0402 + zener clamp |
| ADC | ADC externo SPI | 1 | 8.0000 | 8.00 | 131.36 | [EST] | ADS7953 16ch 12b 1Msps (Mouser single = US$13,56 COT) |
| ADC | Mux analogico (se usar 2x CI de 8 canais) | 2 | 1.2000 | 2.40 | 39.41 | [EST] | alternativa barata: 2x MCP3208 ~US$2,60 cada -> ver nota |
| MCU | Modulo ESP32-S3-WROOM-1 | 1 | 3.5000 | 3.50 | 57.47 | [CALC] | ML modulo N16R8 R$56,91 COT / (5,1312*3,2) |
| MCU | Botao BOOT + EN | 2 | 0.0500 | 0.10 | 1.64 | [EST] | tatico SMD |
| MCU | Pull-ups de I2C | 2 | 0.0200 | 0.04 | 0.66 | [EST] | 2x 4,7k 0603 (kit) |
| MCU | Pads de programacao | - | 0.0000 | 0.00 | 0.00 | [-] | test points sem custo no BOM (qtd '-') |
| IMU | IMU 6 eixos | 1 | 4.9100 | 4.91 | 80.62 | [COT] | ICM-42688-P US$4,91 (DigiKey, 11/09/2026) |
| BAROMETRO | Barometro | 1 | 3.5000 | 3.50 | 57.47 | [EST] | BMP390 LGA-10 (BMP581 vizinho = US$3,07 COT DigiKey) |
| ENERGIA | Buck 12 V | 1 | 2.2000 | 2.20 | 36.12 | [EST] | CI buck 36V/3A tipo TPS5430 (modulo = EUR6,30 COT) |
| ENERGIA | Buck 5 V | 1 | 2.2000 | 2.20 | 36.12 | [EST] | idem |
| ENERGIA | Buck 3,3 V | 1 | 2.2000 | 2.20 | 36.12 | [EST] | idem |
| ENERGIA | LDO 3,3 V_A | 1 | 0.6000 | 0.60 | 9.85 | [EST] | SOT-23 baixo ruido tipo TPS7A2033 |
| ENERGIA | Indutor de saida | 3 | 0.6500 | 1.95 | 32.02 | [EST] | media 12x12mm 89uH / SRR1210A 17uH / SRN8040 5uH |
| ENERGIA | Capacitor de saida | 6 | 0.3500 | 2.10 | 34.48 | [EST] | 22uF/25V X7R 1210 |
| MOTOR | Conector de motor | 4 | 0.3500 | 1.40 | 22.99 | [EST] | MR30 3 pinos (XT60/XT30 reais: ~US$0,3-0,6 COT) |
| USB | Receptaculo USB-C | 1 | 0.6000 | 0.60 | 9.85 | [EST] | GCT USB4085 16p, so' programacao |
| USB | Protecao ESD USB | 1 | 0.1200 | 0.12 | 1.97 | [EST] | USBLC6-2SC6 SOT-23-6 |
| USB | Ideal diode do VBUS | 1 | 0.5000 | 0.50 | 8.21 | [EST] | P-FET + controlador SOT-23-6 (LM66100) |
| EXTRA | LED de status | 1 | 0.0400 | 0.04 | 0.66 | [EST] | LED 0805 + R 1k |
| EXTRA | Buzzer | 1 | 0.6000 | 0.60 | 9.85 | [EST] | SMD 4 kHz CPT-9019S + transistor |
| EXTRA | Watchdog externo (opcional) | 1 | 0.7000 | 0.70 | 11.49 | [EST] | SOIC-8 -- opcional, decisao do Jailton |
| EXTRA | Fusivel/e-fuse de entrada | 1 | 0.3000 | 0.30 | 4.93 | [EST] | fusivel 30A 1206 (e-fuse TPS2594x ~US$0,90) |
| MECANICO | PCB | 1 | 0.0000 | 0.00 | 0.00 | [-] | custo tratado no bloco FAB (nao e' componente) |

## 4. Contas dos cenarios (para conferir)

```
Importacao: base = componentes(US$ 116.01) + frete(US$ 35) = US$ 151.01
            II    = 60% x base - US$30 = US$ 60.61
            ICMS  = (base+II)/(1-0,17) x 0,17 = US$ 43.34
            IOF   = 3,5% sobre (base+II+ICMS) = US$ 8.92
            total = US$ 263.88 -> R$ 1354
Nacional:   componentes x US$ 5.1312 x k(3,2) + frete R$50 = R$ 1706
Montagem:   setup US$8 + 800 joints x US$0,0017 + stencil US$1.50 + 10 partes extendidas x US$3 = US$ 40.86
```

## 5. O que NAO esta' cotado de verdade

1. **PCB nua** -- US$ 70-150 para 5 pcs e' estimativa; a cotacao real exige subir o
   Gerber de `fase3_pcb/v6/` no site do fabricante. Area medida hoje: 220,1 x 160,1 mm =
   352 cm2 em 4 camadas -- board grande e' o maior alavanca de custo (ver nota 6).
2. **Preco unitario de 37 das 43 linhas e' [EST]** -- ordem de grandeza, nao cotacao.
   LCSC e Mercado Livre bloqueiam leitura automatica daqui (LCSC/Akamai devolveu
   'Access Denied'; Mercado Livre devolveu pagina de erro). Script usado: `orcamento.py`,
   tentativas registradas na conversa de 11/09/2026.
3. **Disponibilidade/lead time** nao verificado em nenhum item (0 de 43).
4. **Imposto de importacao**: as fontes divergem na faixa ate US$ 50 (0% por MP 1.357/2026
   vs 20% em material mais antigo). Acima de US$ 50 todas concordam: 60% com deducao de
   US$ 30 + ICMS 17%. O cenario B esta' na faixa acima de US$ 50, entao o numero vale.
5. **MOQ/partes extendidas** da JLCPCB: assumi 10 partes fora da biblioteca basica a US$ 3.
6. **Nao incluso:** bateria 6S, helice, motores (ja existem), bancada (fonte, osciloscopio,
   ferro/hot-air, termopar), consumiveis (pasta, estanho, fluxo, malha).

## 6. Observacoes de engenharia que mexem no custo

- **Board de 220x160 mm e' 5 placas de 100x100 em area.** O layout v6 esta' espalhado
  (238 footprints, 367 nets ainda nao roteadas). Se a versao final couber em ~120x80 mm,
  a fabricacao cai de faixa de US$ 70-150 para poucos dolares por lote de 5. Antes de
  fechar compra, vale terminar o roteamento e recotar.
- **BOM duplica indutores e capacitores de saida**: as linhas 'Buck 12/5/3,3 V' ja'
  incluem L e Cout na descricao, e as linhas 'Indutor de saida' (3x) e 'Capacitor de
  saida' (6x) repetem os mesmos componentes. Precifiquei o CI do buck e os passivos
  separados -> se for pedir direto do CSV, o pedido vira' 6 indutores e 12 capacitores.
- **12x INA240 = o item mais caro do projeto** (US$ 31,20, ~31% do BOM). Alternativa:
  INA181/INA241 mais barato ou medicao de shunt low-side com amp simples, ao custo de
  perder rejeicao de PWM. Decisao de engenharia, nao de compra.
- **ADC**: ADS7953 (US$ 8) contra 2x MCP3208 (~US$ 5,20) -- a segunda opcao ja' esta'
  prevista no BOM como 'mux analogico' e sai mais barata, com 2 chips a mais de firmware.
- **Cenarios A e B empatam dentro da barra de erro** (R$ 1706 vs R$ 1354). A diferenca real
  e' tempo: importar = 3-6 semanas + risco de alfandega; nacional = dias, porem com markup
  de ~3,2x sobre o preco de catalogo.
- **Reserva de engenharia x1.25** (~R$ 414) e' obrigatoria numa placa de 30 A com 24
  MOSFETs, 4 half-bridges e pegada propria do ESP32-S3: o primeiro power-up queima coisa.

