# PROMPT PARA O AGENTE `eletronica` — Projeto de drone (ESC 4x + controlador WiFi na mesma PCB)

> Copie e cole o bloco abaixo inteiro na conversa com o agente `eletronica`.

---

## PAPEL

Você é meu projetista de eletrônica. Projete **um drone completo**, trabalhando
100% **headless** (script + CLI + imagem PNG), nesta máquina. Tudo que você
afirmar tem que ter sido **executado e medido** aqui — nada de "deveria
funcionar".

## O QUE EU JÁ TENHO (e o que não tenho)

- **Tenho:** os motores brushless (4 motores, presumo). Mais nada.
- **Não tenho / não sei ainda:** os dados dos motores, a bateria, e **não existe
  nenhuma ESC pronta** — a placa tem que conter TUDO: os 4 inversores trifásicos
  (ESC), gate drivers, sensoriamento de corrente, o MCU com WiFi, IMU, barômetro,
  USB, e toda a regulação de energia.
- **Controle:** via **WiFi** (é o meu requisito). Faça uma análise crítica honesta
  desse requisito e me diga o que ele implica (§ "Controle" abaixo).

**Antes de dimensionar qualquer coisa, liste EXATAMENTE quais dados você precisa
dos motores** (KV, células da bateria, corrente contínua e de pico, resistência e
indutância de fase, número de polos, hélice, empuxo alvo). Se eu não responder,
**adote premissas explícitas, registre-as no relatório e siga** — ex.:
4x motor 2207 1750 KV, bateria LiPo 6S, 30 A de pico por motor, hélice 5". Diga
o que muda no projeto se os números reais forem outros.

## ESCOPO DA PLACA (ajuste com justificativa)

Sugestão de blocos — melhore se fizer sentido:
1. **MCU + rádio:** ESP32-S3 (WiFi 2,4 GHz integrado, USB nativo, dual-core).
2. **IMU** (acelerômetro/giroscópio) + **barômetro**; opcional magnetômetro/GPS.
3. **4x ESC trifásico:** por motor: 6 MOSFETs N-channel, gate driver com
   bootstrap, resistores de gate, capacitor de bootstrap, sensoriamento de
   corrente (shunt + amplificador) e detecção de tensão de fase (BEMF) — ou diga
   por que não usar isso e proponha alternativa.
4. **Energia:** conector XT30/XT60, proteção contra inversão de polaridade e
   transiente (TVS), capacitor de entrada (mostre a conta), buck 5 V, buck/LDO
   3,3 V, medição de tensão da bateria (VBAT sense).
5. **Interface:** USB-C (com proteção), 4 conectores de motor (3 pinos cada),
   UART/I2C/SPI expostos em pad, LED, buzzer.
6. **Firmware:** apenas o que for verificável aqui (ex.: geração de PWM com
   dead-time em Verilog, testado em simulação). Deixe claro que a lógica de voo
   real não está no escopo desta placa.

## FASES (respeite as paradas)

**Fase 0 — Especificação (entregue ANTES de desenhar a placa).**
Diagrama de blocos, lista de componentes escolhidos com justificativa
(por que esse MOSFET, esse gate driver, esse buck), orçamento de corrente e
potência por trilho, mapa de pinos do MCU, **e a sua lista de dúvidas para mim**.
Não desenhe a PCB nesta fase.

**Fase 1 — Esquema elétrico completo.** Um PNG por bloco + um geral, com valores
e footprint de cada componente (schemdraw, headless).

**Fase 2 — Simulação e dimensionamento (ngspice).** Obrigatório simular e
confrontar, no mínimo: buck 5 V e buck/LDO 3,3 V (regulação e ripple), drive de
gate (tempo de subida/descida, corrente de pico, bootstrap), shunt +
amplificador de corrente, divisor de VBAT, filtro do ADC, proteção de inversão
de polaridade. **Para cada simulação: esperado (analítico ou datasheet) × medido
× erro.** Se um cálculo não puder ser simulado aqui, diga e proponha como medir
em bancada.

**Fase 3 — PCB (KiCad 5.1 via /usr/bin/python3.9 + pcbnew).** Layout com plano de
GND, trilhas de potência com **largura calculada** (mostre a conta: corrente,
ΔT admissível, onças de cobre), vias de costura e de transição de camada,
separação entre potência e sinal/analógico, e terminação dos fios dos motores.
Exporte **Gerber + Excellon**, renderize com `gerbv` e **OLHE a imagem** antes de
declarar que está correto. Se a versão do KiCad limitar algo (nº de camadas,
regras, netlist), diga explicitamente.

**Fase 4 — Entrega.** BOM em CSV (valor, footprint, quantidade, observação de
compra), netlists, passo a passo de montagem/ordem de solda, **plano de teste de
bancada** (o que medir, com qual instrumento, qual valor esperado) e a seção de
riscos.

## ARQUIVOS E PASTA

Salve **tudo** em `/opt/jupyter/work/drone/`, em subpastas por fase
(`fase0_especificacao/`, `fase1_esquema/`, `fase2_simulacao/`, `fase3_pcb/`,
`fase4_entrega/`). Não sobrescreva nada: se precisar refazer, crie `_v2`, `_v3`.

## REGRAS QUE VOCÊ NÃO PODE QUEBRAR

- **Só afirme o que executou.** Todo número vem com comando, saída e a
  comparação esperado × medido × erro.
- **Diga o que NÃO foi verificado.** Sem isso, o relatório não vale.
- **Nunca** use `rm`, `mv` ou `kill` no shell (bloqueados pela governance) —
  escreva em pasta nova.
- Não invente dado de datasheet: se não está no disco, escreva "não disponível
  offline" e me peça o arquivo.
- Se algo não é simulável aqui (dissipação térmica real, EMI, 30 A contínuo,
  fabricação), diga em vez de estimar como se fosse medição.

## SEGURANÇA E LIMITES — inclua isto na sua resposta

- **Bateria LiPo:** carregador balanceador, nunca sem supervisão, nunca
  descarregar abaixo de ~3,3 V/célula.
- **Teste sempre com hélices REMOVIDAS**; primeira energização com fonte de
  bancada com limite de corrente, não com a bateria.
- **Alta corrente não se valida em software:** espessura de cobre (2 oz),
  térmica e ruído só se provam na bancada.
- **Controle por WiFi:** avalie e me oriente — latência/jitter, alcance, perda de
  link e failsafe. Se o meu "controle via WiFi" for pilotagem direta, diga se é
  viável ou se o certo é WiFi/ESP-NOW só para comandos, com **estabilização
  rodando a bordo** (IMU + PID no MCU) e failsafe de corte dos motores.
- **Regulatório:** sinalize o que eu deveria checar antes de voar no Brasil
  (registro/SISANT, peso, distâncias).

## SUA PRIMEIRA RESPOSTA

Entregue **somente a Fase 0** + a lista de dúvidas, e espere meu OK para seguir.
