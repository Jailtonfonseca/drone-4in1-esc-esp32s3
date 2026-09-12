# RISCOS DO PROJETO (FASE 4)

**Projeto:** drone 4×ESC trifásico + ESP32-S3 na mesma PCB · LiPo 6S
**Pasta:** `/opt/jupyter/work/drone/fase4_entrega/` · **Data:** 2026-09-11

## Como usar esta tabela

Cada risco tem: **severidade** (dano se acontecer), **probabilidade** (chance de acontecer),
**mitigação** (o que já está no projeto) e **como detectar** (o que medir e com qual
instrumento — todos os instrumentos estão em `PLANO_TESTE_BANCADA.md` §1).

Legenda: **S** = severidade · **P** = probabilidade · 🔴 Alta · 🟡 Média · 🟢 Baixa

Os riscos **CRÍTICOS** (perda de hardware ou risco físico) estão marcados com ⚠️.
Nenhum deles foi medido em bancada — todos são de projeto/simulação.

---

## 1. Matriz-resumo

| ID | Risco | S | P | Mitigação no projeto | Como detectar |
|---|---|---|---|---|---|
| **R-01** ⚠️ | **Shoot-through** (high-side e low-side ligados juntos) | 🔴 | 🟡 | Driver *single-input* que gera o complementar **em hardware**, com dead-time interno ~520 ns `[PREMISSA]`; RTL com dead-time de **518,750 ns** medido `[F2V]`; garantia **estrutural** no RTL (`hi=1` exige `pwm_in=1` estável, `lo=1` exige `pwm_in=0` estável → impossível coexistir) | Osciloscópio nos **dois gates** do mesmo half-bridge: janela de sobreposição = **0**. `PLANO_TESTE_BANCADA.md` passo 9 |
| **R-02** ⚠️ | **Bootstrap sem carga** (Cboot descarrega, high-side não satura) | 🔴 | 🟡 | `DUTY_MAX = 3890` (95 %) garante **2,5 µs de low-side por período** para recarga `[F2V]`; Cboot = 1 µF ≥ 20×Qg `[F0]` | Medir o **droop**: esperado **65,000 mV em 50 µs** `[F2]`; reprova acima de **500 mV**. Checar Vgs do high-side vs low-side (passo 8c) |
| **R-03** ⚠️ | **Corrente de partida / inrush** (fonte ou bateria entrega corrente demais no 1º instante) | 🔴 | 🟡 | Banco de **6× 470 µF** carregado de uma vez; primeira energização **obrigatoriamente com fonte de corrente limitada** | Fonte entrando em modo CC (passo 4); pico de corrente com sonda I6. Subir em etapas 50 mA → 200 mA → 500 mA → 1 A |
| **R-04** ⚠️ | **Curto de fase** (trilha/pad/via em curto entre fases ou ao GND) | 🔴 | 🟡 | Verificação de short no layout: `[DISCO]` `verificacao_v6.txt` → "pads de nets diferentes com bbox sobreposto: **0**". **Mas** há 12 pares "trilha × pad de net diferente **próximos**" (ex.: `trilha PHM101 × pad QM101H.2 (VBAT_PROT)`) ainda **não resolvidos** | Continuidade e resistência entre trilhos **antes** de energizar (passos 2 e 3); corrente da fonte subindo **sem** motor comandado |
| **R-05** | **Rotação do motor errada** | 🟡 | 🔴 | Nenhuma mitigação de hardware — é firmware/cabeamento | Teste com motor pequeno (passo 14). **Correção: trocar duas fases**, nunca inverter no firmware (inverte o BEMF junto) |
| **R-06** | **ADC/BEMF ruidoso** (leitura de corrente inútil) | 🟡 | 🔴 | ADC **externo por SPI** com amostragem simultânea `[F0]` §4.2; LDO 3,3 V_A dedicado e de baixo ruído; filtro do VBAT com fc = **132,0870 Hz** `[F2]`; BEMF fc = **178 564,1 Hz** `[F2]` | Comparar a mesma leitura com o motor **parado** e a 100 % de duty. Variação > 2 % = ruído. Passo 12 |
| **R-07** ⚠️ | **EMI do ESC entrando no IMU/barômetro** | 🔴 | 🟡 | 100 nF + 10 µF **colados a < 2 mm de cada par de MOSFET** `[F0]` §4.4 (o spike calculado é **60 V** com 100 nH e di/dt de 30 A em 50 ns); plano de GND; separação potência/sinal | Ler o IMU com motor parado vs 100 % duty: se o giroscópio **deriva** ou o barômetro dá picos, é EMI. Termopar/sonda perto do receptor de vídeo. **NÃO VALIDÁVEL por simulação** |
| **R-08** ⚠️ | **Perda de link de rádio** (drone voa sozinho) | 🔴 | 🟡 | **Failsafe obrigatório**: watchdog de link, ~**200 ms** sem comando → corte de motores ou descida controlada `[F0]` §3.2.3. Watchdog externo opcional no BOM | Teste deliberado: desligar o transmissor com o motor girando e medir o tempo até o corte. Tem de ser **≤ 200 ms** |
| **R-09** ⚠️ | **Brownout do ESP32-S3** (reset em pico de corrente do WiFi) | 🔴 | 🟡 | Buck de 3,3 V com folga de **2,9×** (0,518 A de carga para 1,50 A de capacidade) `[F0]` §7; trilho de gate **separado** (12 V) para o ruído de gate não voltar ao MCU; banco de entrada grande | Ler o **motivo do reset** no firmware. Se o reset aparecer junto com TX de WiFi, é brownout. `[F0]` §7: "ESP32-S3 pico WiFi TX 0.50 A" |
| **R-10** | **Térmica dos MOSFETs** | 🟡 | 🟡 | Rds ≤ 3 mΩ exigido (cada 1 mΩ a mais custa **5,4 W** de calor com 24 FETs `[F0]` §6); 2 oz + polígono de cobre no dreno | Termopar no tab do FET sob carga real. `[F0]` **calcula** pico 30 A → Tj = 60,0 °C com `Rth_ja = 60 °C/W` — e o próprio relatório marca o Rth como `[PREMISSA]` |
| **R-11** | **Respin de placa** (a v6 é inutilizável) | 🔴 | 🔴 | Versões preservadas (`v1`…`v6`) para não perder histórico; BOM/verificações por script | `[DISCO]` `verificacao_v6.txt`: **367 de 426 nets não roteadas**. Faça o DRC antes de cotar |
| **R-12** | **Pegada do ESP32-S3-WROOM-1 gerada por script** | 🔴 | 🟡 | `[DISCO]` `lista_componentes_fase0.csv`: `NAO EXISTE NO KICAD 5.1 - GERAR POR SCRIPT`; a Fase 0 pediu o *mechanical drawing* e **não foi recebido** | Conferir o pitch dos 41 pads contra o drawing **antes** de gerar o estêncil |
| **R-13** | **Dados de datasheet ausentes** (tudo [PREMISSA]) | 🟡 | 🔴 | Etiquetas `[N/D offline]` em todo o relatório; critério de escolha declarado em vez de número inventado | Qualquer medição de bancada vai revelar a diferença. Fase 2 §8: "Os números de Rds_on e KP são **escolhas numéricas declaradas** … não datasheet" |
| **R-14** | **Contagem de periféricos do ESP32-S3** (MCPWM/LEDC/ADC) | 🟡 | 🟡 | Plano B já declarado: "**CPLD/FPGA gerando as 24 saídas com dead-time programável**" `[F0]` §4.1 | Conferir no TRM da Espressif. Se o ADC2 for compartilhado com o rádio, a solução do ADC externo já cobre |
| **R-15** | **Regulatório** (voo irregular / apreensão) | 🟡 | 🔴 | Nada no hardware resolve — ver `SEGURANCA_E_REGULATORIO.md` | Consultar SARPAS/SISANT antes de voar |
| **R-16** | **Custo da placa grande** (220 × 160 mm = 352 cm²) | 🟡 | 🟡 | `[DISCO]` `orcamento/ORCAMENTO.md` §6: "board de 220x160 mm é **5 placas de 100x100 em área** … se couber em ~120x80 mm, a fabricação cai de US$ 70-150 para poucos dólares" | Recotar depois de fechar o roteamento |

---

## 2. Detalhe dos riscos críticos ⚠️

### R-01 — Shoot-through

**Por que é crítico.** Dois MOSFETs do mesmo half-bridge em condução simultânea = curto
direto do barramento de 19,8–25,2 V para o GND, limitado só pela resistência de trilha.
Com 24 FETs, uma falha pode levar o par, o driver e o barramento.

**O que o projeto já faz:**
- `[F0]` §4.1: "o driver gera o complementar e o **dead-time em hardware**, ~520 ns `[PREMISSA]`,
  o que evita shoot-through mesmo se o firmware errar".
- `[F2V]` §2: a garantia é **estrutural**, não um `$assert` — "hi = 1 exige `pwm_in = 1`
  estável, `lo = 1` exige `pwm_in = 0` estável; como `pwm_in` não pode ser os dois,
  **hi e lo nunca podem estar em 1 no mesmo ciclo**".
- `[F2V]` §4.2: **0 violações em 362 060 ciclos**, incluindo 60 000 ciclos de estresse com
  duty e dead-time pseudo-aleatórios.

**O que ainda falta:** `[F2V]` §7.3 avisa que o dead-time **real no MOSFET** = dead-time do RTL
**+ atrasos do driver**, e que esses atrasos "podem ser maiores que 520 ns". E §7.1: "Nada foi
gravado em FPGA/CPLD/ASIC". Portanto: **é simulação, não é medição.**

### R-02 — Bootstrap

`[F2]` mediu o droop: `vb_1ns = 12,00000 V` → `vb_50us = 11,93500 V` → **65,00000 mV**, erro **0**.
`[F2V]` §7.9 é honesto: "A reposição do capacitor de bootstrap em duty = 95 % só está
**argumentada** (2,5 µs de low-side por período); o tempo de carga real depende do valor do
capacitor, da resistência do diodo e da corrente do driver — **não** simulado aqui".

**Ação de bancada:** medir o droop nos dois extremos de duty (2 % e 95 %) e no **pior caso
térmico** (depois de 10 min ligado).

### R-07 — EMI no IMU e no barômetro

O número que justifica o medo: `[F0]` §4.4 —

```
Spike por indutância do cabo: L=100 nH, di=30 A, dt=50 ns -> 60 V (estoura o MOSFET de 40 V)
```

O próprio relatório conclui: "Isso é o argumento definitivo para **100 nF + 10 µF colados a
<2 mm de cada par de MOSFETs**, fechando o loop de comutação localmente".

**Isto não se valida em bancada sem instrumentação de RF.** O único teste acessível é
comportamental: com o motor girando a 100 % de duty, a saída do giroscópio deve ficar
estável (o ruído do IMU não pode crescer mais que ~10× o nível com motor parado).
`[EST]` — o fator 10× é critério de engenharia meu, não medido.

### R-08 — Failsafe de perda de link

`[F0]` §3.2 adota: watchdog de **200 ms** → corta motores ou entra em descida controlada.
A Fase 0 §11 pergunta 9 registra isso como **dúvida em aberto**: "Prazo de link aceitável para
o failsafe (sugiro 200 ms)?" — **ainda não respondida**. Ver `ANALISE_WIFI_CONTROLE.md` §6.

---

## 3. Riscos que a lista pedida não cobria, mas existem

| ID | Risco | S | P | Mitigação | Detecção |
|---|---|---|---|---|---|
| R-17 | **Falha de montagem manual** (0402 tombado, ponte em QFN de 0,4 mm) | 🟡 | 🔴 | Ordem de solda por etapas; inspeção obrigatória antes de energizar | `MONTAGEM_ORDEM_DE_SOLDA.md` §6 |
| R-18 | **Sem datasheet da pasta de solda** → perfil de reflow no chute | 🟡 | 🔴 | Perfis típicos documentados com fonte; perfil definitivo marcado `[VERIFICAR]` | Pedir o datasheet da pasta ao Jailton |
| R-19 | **Limpeza com ultrassom danifica o cristal do módulo** | 🟡 | 🟢 | Recomendado **não** usar ultrassom; usar pincel + IPA | — `[EST]/[VERIFICAR]` |
| R-20 | **IP do projeto de potência:** 30 A em placa de 2 oz com trilha mal dimensionada | 🔴 | 🟡 | `[DISCO]` `calc_trilhas_vias_saida.txt`: 30 A / ΔT 10 °C pedem **16,37 mm** de largura em 2 oz → decisão: "**VBAT: não usar trilha p/ os 30 A; usar POLÍGONO de cobre + transição por via**"; 40 vias de 0,3 mm por transição | Verificar no layout final se as transições de VBAT/GND têm as **40 vias** |
| R-21 | **Falso negativo no teste de curto** (umidade/resíduo de fluxo entre planos) | 🟡 | 🟡 | Lavar e secar antes de medir continuidade | Repetir o passo 2 **após** a limpeza |
| R-22 | **Bateria LiPo:** incêndio, descarga profunda, dano mecânico | 🔴 | 🟡 | Ver `SEGURANCA_E_REGULATORIO.md` — carregador balanceador, ≤ 3,3 V/célula, armazenamento a ~3,8 V | Alarme/telemetria de tensão por célula |

---

## 4. Os 5 riscos que eu atacaria primeiro

1. **R-11 (respin / placa não roteada).** 367 nets em aberto. É o mais provável de todos e o
   mais caro. Fechar o roteamento antes de qualquer compra.
2. **R-12 (pegada do ESP32-S3).** Um erro de 0,1 mm aqui inutiliza os módulos comprados.
   `[DISCO]`: a pegada não existe no KiCad e o *mechanical drawing* nunca chegou.
3. **R-01 (shoot-through).** Simulado com 0 violações em 362 060 ciclos, mas **só com o
   dead-time do RTL**. O atraso do driver vale tanto quanto o dead-time programado.
4. **R-04 (curto de fase).** Há 12 pares trilha×pad ainda "próximos" no layout.
   Um curto de fase com bateria é fumaça.
5. **R-08 (perda de link).** Não é risco de bancada, é risco de **voo**. O prazo do failsafe
   ainda é pergunta em aberto desde a Fase 0.

---

## 5. O que NÃO está verificado neste documento

1. **Nenhum risco foi observado ocorrer.** Zero bancada, zero voo, zero termopar.
2. As probabilidades (🔴/🟡/🟢) são **julgamento meu** `[EST]`, não estatística de campo.
3. As severidades se apoiam em números calculados/simulados do próprio projeto — esses estão
   citados com arquivo e seção.
4. Riscos de **fabricação** (tolerância de 2 oz, alinhamento do estêncil, capabilidade do
   fabricante) não foram avaliados.
5. Riscos **regulatórios** estão em documento separado, com fontes ao vivo e data.
