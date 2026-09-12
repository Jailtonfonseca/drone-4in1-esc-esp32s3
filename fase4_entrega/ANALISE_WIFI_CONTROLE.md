# ANÁLISE HONESTA: CONTROLE POR WiFi (FASE 4)

**Projeto:** drone 4×ESC trifásico + ESP32-S3 na mesma PCB
**Pasta:** `fase4_entrega/` · **Data:** 2026-09-11 · **TZ:** America/Bahia

---

## 1. VEREDITO (leia só isto se tiver pressa)

> ### ❌ **PILOTAGEM DIRETA POR WiFi NÃO É VIÁVEL COM SEGURANÇA.**
> ### ✅ **A ARQUITETURA CORRETA É: ESP-NOW/WiFi SÓ PARA COMANDOS (20–50 Hz) + ESTABILIZAÇÃO IMU+PID A BORDO (1–4 kHz) + FAILSAFE DE CORTE DOS MOTORES (200 ms).**
>
> Não é a média da latência que mata — é a **cauda**. A média do WiFi pode ser 5 ou 9 ms;
> a cauda de **100 ms+** (retransmissão ARQ, contenção CSMA, fila do driver) já é
> irreversível: `[DISCO]` `FASE0_ESPECIFICACAO.md` §3.1: "a 20 ms de atraso um quadricóptero
> de 5" já mudou de atitude de forma irreversível".

A Fase 0 já tinha chegado nessa conclusão (`[DISCO]` §3.2: **"'Stick → WiFi → motor'
(pilotagem direta): NÃO é viável com segurança"**). Este documento **confirma** o veredito
com números novos e fontes de terceiros medidas ao vivo, e detalha **exatamente** o que fazer
no lugar.

---

## 2. Por que a pilotagem direta morre — os números

### 2.1 O jitter domina o período de comando

`[DISCO]` `[F0]` §3.1 (valores calculados na Fase 0, reproduzidos em
`calcs_wifi_controle.txt` §3):

| Taxa de comando | Período | Jitter de 10 ms = quanto do período? |
|---:|---:|---:|
| 20 Hz | 50,0 ms | **20,0 %** |
| 50 Hz | 20,0 ms | **50,0 %** |
| 100 Hz | 10,0 ms | **100,0 %** |
| 250 Hz | 4,0 ms | **250,0 %** |

Com 10 ms de jitter, um sistema a 50 Hz recebe comandos fora de fase metade do tempo.
Um controlador em malha fechada não aceita isso. **É por isso que o laço tem de estar
a bordo e o link só manda setpoint.**

### 2.2 Ordem de grandeza da latência de terceiros

`[FONTE]` Electric UI, "Benchmarking latency across common wireless links for microcontrollers",
consultado 2026-09-11 — https://electricui.com/blog/latency-comparison
(bench **de bancada**, Saleae a 100 MS/s, ESP32, ambiente semi-controlado; NÃO é medição minha):

| Link (ESP32) | Resultado publicado |
|---|---|
| **ESP-NOW** | "typical end-to-end latency for a single packet transfer is **consistently ~5 ms**"; 1 KiB em 5 pacotes ≈ **24 ms** |
| WiFi TCP/IP | mediana ≈ **6 ms**, com **outliers até 25 ms** |
| WiFi UDP/IP | mediana ≈ **9 ms** (antes de otimizar), outliers até 25 ms |
| WiFi UDP/TCP após tuning | "both TCP and UDP were able to achieve the **same lower-bound latencies** and similar worst-case outliers" — ou seja, ~6 ms com cauda de ~25 ms |

`[FONTE]` comentário na cobertura do Hackaday do mesmo benchmark, consultado 2026-09-11 —
https://hackaday.com/2024/02/11/benchmarking-latency-across-common-wireless-links-for-mcus
`[VERIFICAR]` (é comentário de leitor, não dado auditado): "I got **< 1 ms round-trip** time for
about 95% of the packets, with most deviations being about 2-3 ms, and a very spurious delay
of 6 ms at most".

`[FONTE]` FreeRTOS/Espressif — "ESP-NOW in indoor applications" (palestra, YouTube),
consultado 2026-09-11 — https://www.youtube.com/watch?v=DatH-QUB0ho: "WiFi has also **high
latency**. ESP-NOW has **low latency**." `[VERIFICAR]` (palestra, sem número medido).

> **Síntese:** ESP-NOW honesto = **~5 ms típico**, com cauda que em bancada fica na casa de
> **6–25 ms**. WiFi com pilha IP = **~6–9 ms típico**, cauda de **25 ms** em bancada
> controlada, e **muito pior** em ambiente com contenção. Em nenhum dos casos confiáveis a
> cauda fica abaixo de 25 ms.

### 2.3 O que 25 ms de atraso fazem com a atitude

`[CALC]` (`calcs_wifi_controle.txt` §7), assumindo taxa de guinada máxima de projeto de
200 °/s `[EST]`:

| Latência | Erro de atitude acumulado |
|---:|---:|
| 5 ms | 1,0° |
| 20 ms | **4,0°** |
| 50 ms | 10,0° |
| 100 ms | **20,0°** |
| 200 ms | 40,0° |

Referência: `[F0]` §3.1 considera **20° já irreversível** num quadricóptero de 5".

### 2.4 O que 200 ms de perda de link custam em altitude

`[CALC]` (`calcs_wifi_controle.txt` §1) — queda livre a partir de um hover:

| Tempo sem link | Queda | Velocidade atingida |
|---:|---:|---:|
| 20 ms | 0,20 cm | 0,20 m/s |
| 50 ms | 1,23 cm | 0,49 m/s |
| 100 ms | 4,91 cm | 0,98 m/s |
| **200 ms** | **19,62 cm** | **1,96 m/s** |
| 500 ms | 122,62 cm | 4,91 m/s |

> **Isto é a boa notícia do projeto:** o failsafe de **200 ms** que a Fase 0 adotou
> (`[F0]` §3.2.3) custa **~20 cm de altitude** e menos de 2 m/s de velocidade de impacto.
> É um failsafe **fisicamente viável** para um quadricóptero de 5". Para 500 ms já são
> 1,23 m — o que já quebra hélice e braço.

---

## 3. ARQUITETURA RECOMENDADA (explícita)

```
┌──────────────────────────────────────────────────────────────────────┐
│  TRANSMISSOR (solo)                    DRONE (a bordo)               │
│                                                                      │
│  joystick + ESP32                      ESP32-S3 na PCB               │
│        │                                    │                        │
│        │  ESP-NOW, quadro curto,            │  1) IMU (SPI) 1–4 kHz  │
│        │  sem IP, sem ARQ                  │  2) PID atitude 1–4 kHz│
│        │  setpoint de ÂNGULO/POTÊNCIA       │  3) PWM 20 kHz c/      │
│        │  20–50 Hz, ~20–32 bytes            │     dead-time (RTL)    │
│        ▼                                    ▼                        │
│  ─────────────► comando ─────────────►  ┌────────┐                   │
│                                          │ MOTORES│                   │
│  ◄───────────── telemetria ◄────────────  └────────┘                  │
│    10–50 Hz, prioridade BAIXA                                        │
│                                                                      │
│  WATCHDOG: 200 ms sem comando válido → cortar motores / descer        │
└──────────────────────────────────────────────────────────────────────┘
```

| Camada | Taxa | Onde roda | Justificativa medida |
|---|---:|---|---|
| **Malha de atitude (PID)** | **1–4 kHz** | ESP32-S3 **a bordo** | `[CALC]` §4: a 1 kHz e comando a 50 Hz, **20 iterações de PID por setpoint recebido**; a 4 kHz, **80** |
| **Sensores (IMU)** | **1–4 kHz** | a bordo, SPI 4–8 MHz | o barômetro é lento (decenas de Hz) e só serve para altitude |
| **PWM para os gates** | **20 kHz** | a bordo | `[F2V]` medido: 20,0000 kHz, dead-time 518,750 ns |
| **Comandos (uplink)** | **20–50 Hz** | **ESP-NOW** | `[FONTE]` Electric UI: ~5 ms típico por pacote |
| **Telemetria (downlink)** | **10–50 Hz** | ESP-NOW | prioridade baixa; **nunca** bloqueia o laço |
| **Failsafe** | **200 ms** | a bordo + watchdog externo | `[CALC]` §2.4: 19,62 cm de queda |

### 3.1 Por que ESP-NOW e não UDP/IP

| Critério | ESP-NOW | WiFi UDP/IP | WiFi TCP/IP |
|---|---|---|---|
| Pilha | ação 802.11 direta, **sem IP** | IP + UDP | IP + TCP |
| Latência típica medida `[FONTE]` | **~5 ms** | ~9 ms (6 ms após tuning) | ~6 ms (com Nagle off) |
| Retransmissão automática | **não** (você decide) | não | **sim** → cauda imprevisível |
| Overhead | mínimo | médio | alto |
| Payload máx. | **250 B** `[FONTE]` Espressif ESP-FAQ | MTU grande | MTU grande |
| Pares | até 20 peers `[FONTE]` idem | — | — |
| Taxa PHY | 1 Mbps por padrão `[FONTE]` idem | negociada | negociada |
| **Telefone/celular controla?** | ❌ **não** (celular não fala ESP-NOW) | ✅ | ✅ |

`[FONTE]` Espressif ESP-FAQ, "ESP-NOW", consultado 2026-09-11 —
https://docs.espressif.com/projects/esp-faq/en/latest/application-solution/esp-now.html:
"PHY rate is 1 Mbps by default · Around **214 Kbps** in an open environment · Around **555 Kbps**
in a shielding box · payload **250 bytes** · up to **20 peers**".

### 3.2 A decisão que o Jailton tem de tomar

| Opção | Como fica | Latência | Veredito |
|---|---|---|---|
| **A) Transmissor dedicado ESP32 + ESP-NOW** | você segura um rádio próprio | **~5 ms** | ✅ **RECOMENDADO para voo** |
| **B) Celular/notebook por WiFi UDP** | app no celular | ~6–25 ms, cauda pior em ambiente com gente | 🟡 serve para **bancada e telemetria**; arriscado para voo |
| **C) Celular/notebook por TCP ou WebSocket** | app web | TCP retransmite → cauda de centenas de ms | ❌ **NÃO usar para controle** |
| **D) Stick → WiFi → motor (pilotagem direta)** | sem laço a bordo | — | ❌ **INVIÁVEL**, ver §2 |

`[DISCO]` `[F0]` §3.2 já descartava TCP: "**TCP está descartado para controle** (retransmissão
+ Nagle)". E §3.2.4 preconiza **ESP-NOW** em vez de UDP/IP.

> **Consequência prática para o seu requisito "controle via WiFi":** o requisito é atendido —
> o rádio é WiFi (2,4 GHz, ESP-NOW é um quadro de ação do próprio padrão 802.11). O que muda é
> que **o celular não pilota**; quem pilota é um transmissor com ESP32. Se você quer
> **obrigatoriamente** o celular no comando, então o drone precisa de **posição e altitude
> travadas a bordo** (modo "hover/position hold") para que a latência do celular só ajuste um
> alvo, sem fechar a malha. `[EST]`

---

## 4. ORÇAMENTO DE TEMPO DE AR — o canal sobra

`[CALC]` (`calcs_wifi_controle.txt` §5), estimativa de 1º princípio para um quadro 802.11b a
1 Mbps (preâmbulo longo 144 bits + header PLCP 48 bits = 192 bits, + cabeçalho MAC 24 B + FCS 4 B):

| Payload | Bits no ar | Tempo de ar |
|---:|---:|---:|
| 20 B | 576 | **576,0 µs** |
| 32 B | 672 | **672,0 µs** |
| 250 B (máx. ESP-NOW) | 2 416 | **2 416,0 µs** |

Ocupação do canal **só do uplink**:

| Taxa de comando | Payload 32 B | Ocupação |
|---:|---:|---:|
| 20 Hz | 672 µs | **1,34 %** |
| 50 Hz | 672 µs | **3,36 %** |

> **Conclusão:** 50 Hz de comandos ocupa **3,4 % do tempo de ar**. Você tem espaço de sobra.
> `[EST]` Dá para subir a taxa para 100–200 Hz (6,7–13,4 %) e ganhar margem contra o jitter —
> **mas só se o receptor descartar pacotes velhos** (um pacote atrasado é pior que nenhum).

`[DISCO]` Comparação com os números da Fase 0 `[F0]` §3.1 (t_ar de 1792 / 298,7 / 33,2 µs
para 1 / 6 / 54 Mbps). Os dois métodos concordam na ordem de grandeza (centenas de µs a ~2 ms).

`[DISCO]` `[F2V]` §7.3 lembra que o **jitter do clock** e o **atraso de GPIO** não estão
modelados: "O atraso entre a saída do registrador e o pino físico … não foram modelados".
Isso vale também para o link.

---

## 5. ALCANCE E PERDA DE LINK

### 5.1 Alcance

`[DISCO]` `[F0]` §3.2: "**Alcance [NÃO VERIFICADO]**: premissa de **50–300 m** em linha de
visada com antena de PCB, muito sensível a orientação e altura."

`[EST]` Os fatores que derrubam o alcance mais que a distância:

| Fator | Efeito |
|---|---|
| **Corpo do drone** | `[EST]` o quadro, a bateria e os cabos de 30 A ficam entre a antena de PCB e o solo em certas atitudes → **nulls de antena** |
| **Orientação** | antena de PCB tem padrão direcional; virando o drone, o link muda com a atitude |
| **2,4 GHz congestionado** | roteadores de vizinhança, câmera FPV analógica, o próprio WiFi do celular do piloto |
| **Canal** | ESP-NOW e o WiFi STA **têm de estar no mesmo canal** para coexistir |
| **Taxa PHY** | `[FONTE]` Espressif ESP-FAQ: 1 Mbps é o padrão; em ambiente aberto ~214 kbps efetivos |
| **Antena** | `[DISCO]` `[F0]` §10.4: "a antena/PCB **não pode ser alterada** sem reavaliação" (ANATEL) → **não dá para simplesmente colocar uma antena externa de ganho** |

`[VERIFICAR]` — a palestra da Espressif (https://www.youtube.com/watch?v=DatH-QUB0ho,
consultada 2026-09-11) afirma "ESP-NOW up to **200 meters indoor**" e "WiFi up to 30 meters".
`[EST]` **É marketing de palestra, não medição.** Não use como especificação.
**Medir alcance exige campo** — a Fase 0 já dizia: "Medir isso exige bancada de RF e campo —
não existe aqui".

### 5.2 Failsafe: o desenho e as armadilhas

`[DISCO]` `[F0]` §3.2.3: "**FAILSAFE obrigatório**: watchdog de link (ex.: **200 ms** sem
comando) → **corta motores ou entra em descida controlada**".

| Item | Recomendação | Por quê |
|---|---|---|
| Timeout | **200 ms** | `[CALC]` 19,62 cm de queda — ver §2.4 |
| Contagem | `[EST]` exija **10 quadros consecutivos perdidos** a 50 Hz (= 200 ms exatos), não "um buraco de tempo" | evita disparo por um único retry longo |
| **Falso positivo** | `[EST]` 🚨 **este é o risco real**: um failsafe que corta motores por um pico de latência **derruba o drone sozinho** | a cauda do WiFi passa de 100 ms; a do ESP-NOW não deveria |
| Ação ao perder link | `[EST]` **não corte na hora**: (1) congela atitude em nível, (2) reduz throttle devagar, (3) corta aos **500 ms** | usar o barômetro para descer controlado. `[F0]` §3.2.3 já prevê "descida controlada" |
| Watchdog | `[EST]` **externo** (já previsto no BOM como opcional) alimentado pelo firmware | se o firmware travar, só hardware independente corta |
| Teste obrigatório | desligar o transmissor **com motor girando** e medir o tempo até o corte | `PLANO_TESTE_BANCADA.md` R-08 |
| **Prazo** | `[DISCO]` `[F0]` §11 pergunta 9: "Prazo de link aceitável para o failsafe (sugiro 200 ms)?" — **ainda não respondida** | decisão pendente do Jailton |

### 5.3 Dimensionamento do failsafe vs a cauda medida

| Fonte do link | Cauda típica medida `[FONTE]` | Failsafe 200 ms provoca corte falso? |
|---|---|---|
| ESP-NOW | ~5 ms típico, raros 6–25 ms | `[EST]` improvável (8× de margem) |
| WiFi UDP/IP | ~9 ms típico, outliers 25 ms | `[EST]` improvável mas **não impossível** em ambiente congestionado |
| WiFi TCP/IP | retransmissão → cauda não limitada | `[EST]` **provável** — mais um motivo para não usar TCP |

`[EST]` **Recomendação final: ESP-NOW, timeout de 200 ms em 10 quadros consecutivos,
ação em duas etapas (estabilizar → descer) e corte duro aos 500 ms.** Se você insistir em
piloto por WiFi IP, suba o corte duro para 500 ms e aceite 1,23 m de queda `[CALC]`.

---

## 6. O QUE FAZER NO FIRMWARE (lista de ações)

| # | Ação | Fonte/razão |
|---:|---|---|
| 1 | Desligar **modem sleep** / power save do WiFi | `[FONTE]` Electric UI: "playing with the modem's power-saving modes" foi um dos ajustes que levou o WiFi de ruim a ~6 ms |
| 2 | Colocar as pilhas **WiFi e LwIP em IRAM** | `[FONTE]` idem |
| 3 | Usar **ESP-NOW peer-to-peer** em vez de AP+HTTP | `[FONTE]` idem + Espressif ESP-FAQ |
| 4 | **Descartar pacotes velhos** no receptor (timestamp/sequência) | `[EST]` pacote atrasado é pior que pacote perdido |
| 5 | Telemetria em **fila separada** e baixa prioridade | `[DISCO]` `[F0]` §3.2.5: "sem bloquear o laço de controle" |
| 6 | Se usar TCP: `TCP_NODELAY` (desligar **Nagle**) | `[FONTE]` Electric UI — o autor perdeu dias por causa do Nagle. **Mas o certo é não usar TCP** |
| 7 | Igualar **canal** do ESP-NOW e do WiFi | `[FONTE]` Espressif (ESP-NOW usa o PHY do WiFi) |
| 8 | Registrar **motivo do reset** e **contador de quadros perdidos** | detecta brownout (R-09) e cauda de link |
| 9 | Amostrar a corrente do shunt **sincronizado com o PWM** | `[DISCO]` `[F0]` §4.5: "a amostragem do ADC precisa ser disparada em sincronia com o PWM (janela de 2 µs = 4 % do período de 50 µs)" |
| 10 | **Nunca** fazer o laço de atitude depender do link | é o ponto inteiro deste documento |

---

## 7. RESUMO EM UMA TABELA

| Pergunta | Resposta |
|---|---|
| Controle por WiFi funciona? | **Sim, como link de comando.** Não, como link de malha fechada |
| Latência típica? | ESP-NOW ~5 ms · WiFi UDP ~6–9 ms · cauda 25 ms em bancada `[FONTE]` |
| Jitter? | `[CALC]` 10 ms de jitter é 50 % do período a 50 Hz |
| Alcance? | `[EST]` 50–300 m LOS com antena de PCB, **`[VERIFICAR]`**, sensível a orientação |
| Perda de link custa o quê? | `[CALC]` 19,62 cm de queda em 200 ms |
| Arquitetura? | **ESP-NOW só comandos + PID a bordo + failsafe 200 ms** |
| Pilotagem direta? | **Não.** 20 ms de atraso = atitude irreversível `[F0]` |
| Onde fica a lógica de voo? | **A bordo** — e a Fase 0–3 não a entrega: `[DISCO]` `[F0]` §9.6 "O firmware de voo real não está no escopo" |

---

## 8. O QUE NÃO FOI VERIFICADO

1. **Nenhuma medição de rádio foi feita por mim.** Não há transmissor, receptor, analisador de
   espectro nem campo nesta máquina. Os números de latência são de **terceiros** (Electric UI,
   com respectiva metodologia) e os de jitter/cauda são citados com link e data.
2. **O "~5 ms do ESP-NOW" é de bancada, ponto-a-ponto, com pouca interferência.** Em campo com
   2,4 GHz congestionado, é outro número. Não existe alguém na internet que meça isso melhor.
3. **Alcance: `[VERIFICAR]`.** Os 50–300 m são premissa da Fase 0; os "200 m indoor" da palestra
   da Espressif são marketing. **Só campo e RSSI medido resolvem.**
4. **A cauda (p99) do link não está caracterizada** — nem por mim, nem pelas fontes que achei.
   `[EST]` A cauda é justamente o que decide o failsafe. **O Jailton deve medir isso no
   firmware real: registrar o intervalo entre quadros recebidos por 30 min e olhar o máximo.**
5. **O modelo de erro de atitude (§2.3) é de 1ª ordem com taxa de guinada de 200 °/s `[EST]`** —
   é um número plausível para um 5", não é medido.
6. **Nada disto é firmware pronto.** `[DISCO]` `[F0]` §9.6: a Fase 2 só entregou o **gerador de
   PWM com dead-time em Verilog**. PID, IMU, failsafe e pilha de rádio **não existem** — este
   documento define o **alvo**, não a implementação.
