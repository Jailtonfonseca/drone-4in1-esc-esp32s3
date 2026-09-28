# STITCH v8 — por que 68 pads de GND/VBAT_PROT estavam sem via, e o que fazer

Documento novo, escrito em 2026-09-28 contra a árvore do commit `0c4fb57` e contra o
`pcbnew` desta máquina. Ele **não apaga** `fase3_pcb/v8/verificacao_v8.txt` (que é o
registro original do problema) e **não mexe** em `fase3_pcb/v8/v8_drone.kicad_pcb`,
que pertence ao worker que está roteando a v8. O único arquivo de código alterado
por esta análise é `fase3_pcb/gera_pcb_v8.py`; o gerador aceita uma pasta de saída
como argumento, o que permitiu medir sem tocar na v8.

```
$ /usr/bin/python3.9 -c "import pcbnew; print(pcbnew.GetBuildVersion())"
5.1.9+dfsg1-1+deb11u1
```

---

## 1. A hipótese "o pad SMD em F.Cu já toca o plano In1.Cu" é FALSA — medida

A saída de campo para fechar o A4 sem mexer no gerador seria dizer que um pad SMD em
F.Cu alcança o plano In1.Cu "pela metalurgia do pad", sem via. **Isso não é verdade**,
e o próprio motor de conectividade do KiCad 5.1.9 mede isso.

O experimento monta placas de 6 camadas com **dois pads de GND, zero trilhas e uma
única zona (plano) de GND**, preenche a zona com o zone filler e conta as conexões
abertas do ratsnest. Se o plano ligar os dois pads, a contagem é 0; se não ligar, os
dois pads ficam ilhados e a contagem é 1.

| Caso | Montagem | Conexões abertas | Veredito |
|---|---|---:|---|
| A | 2 pads **SMD** em F.Cu + zona de GND em **F.Cu** | **0** | o plano ligou os 2 pads |
| B | 2 pads **SMD** em F.Cu + zona de GND em **In1.Cu** | **1** | **o plano NÃO ligou os 2 pads** |
| C | 2 pads **PTH** (todas as camadas) + zona em In1.Cu | 0 | controle: pad passante liga |
| D | 2 pads SMD em F.Cu + **1 via em cada** + zona em In1.Cu | 0 | **a via é o que liga** |
| E | 2 pads PTH + zona em B.Cu | 0 | controle |

O caso **B** é exatamente a situação da v8 (pad SMD em F.Cu, planos em In1..In4/B.Cu).
O caso **D** é a correção. Conclusão, com número: **todo pad SMD de GND/VBAT_PROT
precisa de via para alcançar os planos internos; o gate A4 está medindo a coisa
certa.** Não é por isso que ele falha.

> Nota de método: a hipótese foi testada em 5 casos, com 2 controles que dão 0. Um
> caso só (B = 1) sem controles não provaria nada.

---

## 2. Por que 68 pads ficaram sem via: a busca do gerador só olhava 8 pontos

Em `fase3_pcb/gera_pcb_v8.py` (versão do commit `0c4fb57`), a busca de um ponto livre
para a via era:

```python
angs = [math.radians(a) for a in (0, 45, 90, 135, 180, 225, 270, 315)]
for a in angs:
    for mult in (1.0, 1.25, 1.6, 2.0):
        vx, vy = px + dist_alvo * mult * math.cos(a), py + dist_alvo * mult * math.sin(a)
```

Três defeitos, todos medidos:

1. **Oitenta e um candidatos por pad, e na prática quase 8.** `dist_alvo` já é
   `rhalf + 0,30 + 0,10`; para um pad de 1,0 × 1,6 mm isso dá 1,34 mm, e como o
   corte do gate é 1,6 mm, os multiplicadores 1,25/1,6/2,0 caem todos fora do limite.
   Sobravam **8 pontos num único raio**. Se os 8 estivessem bloqueados, o pad era
   declarado falha — sem que nenhuma outra posição do disco fosse olhada.
2. **O raio de partida era o raio circunscrito do pad** (`0,5 · hypot(sx, sy)`), não
   a meia-extensão real do pad na direção da via. Para um pad retangular 1,0 × 1,6 mm
   isso joga fora a faixa entre a borda e 1,49 mm — justamente a faixa livre ao lado
   do pad.
3. **A margem via × pad de outra net era 0,30 mm**, contra os 0,15 mm que o próprio
   gerador declara em `LIM_CLEAR`. Metade do espaco uvurado a toa.

A área disponível não era o problema: o disco de 1,6 mm em torno de um pad tem
π · 1,6² ≈ **8,04 mm²**, e a via de 0,6 mm com folga de 0,20 mm precisa de
π · 0,50² ≈ **0,79 mm²**. Havia espaço; o algoritmo não procurava.

---

## 3. O que mudou no gerador (e o que foi medido em cima)

`fase3_pcb/gera_pcb_v8.py` mudou só na seção 9 (stitch) e na pasta de saída:

- **Busca em malha fina** dentro do disco de 1,6 mm: passo de **0,05 mm** de raio e
  **36 posições angulares** (10°), da menor para a maior distância, aceitando o
  primeiro ponto livre. Sai de 8 candidatos para até 432 por pad.
- **Raio de partida pela borda real do pad na direção da via**
  (`hx·|cos a| + hy·|sin a| + raio_da_via + 0,05`), não pelo raio circunscrito.
- **Margem via × pad de outra net de 0,30 mm para 0,20 mm**, alinhada com os 0,15 mm
  de `LIM_CLEAR` que o gerador já usava para trilha × pad.
- **Até 2 vias por pad, e a segunda só num 2º laço**, depois que todo pad já tem a
  sua. Medido: fazer a 2ª via dentro do 1º laço rouba espaço dos pads seguintes e
  **aumenta** o número de falhas.
- **Índice espacial** dos discos de ocupação em células de 4 mm, para o teste de
  sobreposição não varrer os 1093 pads a cada candidato (o gerador roda em 14 s).
- `OUT` passa a aceitar argumento: `/usr/bin/python3.9 fase3_pcb/gera_pcb_v8.py <pasta>`.
  Foi assim que a medição foi feita **sem tocar** em `fase3_pcb/v8/`.

### Resultado medido

| | Antes (commit `0c4fb57`) | Depois (gerador revisado) |
|---|---:|---:|
| vias de stitch no board | 180 | **399** |
| pads de GND/VBAT_PROT sem via a ≤ 1,6 mm | 68 | **37** |
| menor distância pad → via | 0,818 mm | **0,700 mm** |
| pads de GND/VBAT_PROT no board | 249 | 249 |

Reprodução (não toca a v8 do outro worker; `/tmp/stitch/v8test` é uma cópia nova):

```sh
cd /opt/jupyter/work/drone
mkdir -p /tmp/stitch/v8test
/usr/bin/python3.9 fase3_pcb/gera_pcb_v8.py /tmp/stitch/v8test
# -> vias de stitch criadas: 399 | pads sem via: 37 | 2a via em: 187
```

A leitura dos 37 é a mesma de `fase3_pcb/verifica_fase3_v8.py`, com os dois caminhos
apontados para a cópia:

```sh
# pcbnew sem via a menos de 1.6 mm : 85 -> 37   (de 249)
# menor distancia pad GND/VBAT_PROT -> via : 0,700 mm (limite 1,60)
```

---

## 4. Por que 37 continuam sem via, e o que seria preciso

Os 37 não são falha de busca. Com um ensaio que ignora a concorrência entre vias
(só considera a geometria dos vizinhos de cada pad), o número de pads que **nem
têm espaço** para uma via de 0,6 mm dentro de 1,6 mm do centro é:

| Via / folga | Pads com espaço a ≤ 1,6 mm | Pads sem nenhum espaço |
|---|---:|---:|
| 0,60 mm / 0,20 mm | 164 de 249 | 85 |
| 0,50 mm / 0,15 mm | 183 de 249 | 66 |
| 0,45 mm / 0,15 mm | 183 de 249 | 66 |
| 0,40 mm / 0,15 mm | 183 de 249 | 66 |

(ensaio com a regra de raio de partida antiga, o do item 2.2; a versão nova do
gerador, com raio pela borda real, alcança 212 dos 249 e é esse o número que vale
para o board.)

Os 37 que sobram são pads prensados: pads de tab de MOSFET de potência
(`QM101H.2`…`QM403H.2`, net VBAT_PROT), pads do regulador `UB1`, pads do
conversor DC-DC `U10` e pids do STM32 `U_MCU`. São os pacotes de passo fino e de
grande área, onde a malha de 0,45 mm entre footprints já come metade do disco de
1,6 mm.

**Reduzir a área do contorno não resolve**: os 319 footprints já somam
**16.562,9 mm²** de bounding box contra **16.500 mm²** de um 150 × 110 mm — 100,4 %
antes de qualquer corredor de rota. O board atual é **162,10 × 145,02 mm**. Não
existe contorno menor que caiba nesses footprints; a área necessária não é o
limitante aqui, a densidade local nos pacotes de passo fino é.

---

## 5. O critério correto — e o número certo

O critério original mede a distância **do centro do pad** até a via. Isso pune pads
grandes por um motivo que não é elétrico: o centro de um pad de tab de MOSFET fica
no meio do cobre, e a borda do tab pode estar a 1,5 mm do centro. O que importa
eletricamente é o **comprimento do caminho de retorno**, ou seja, a distância da
**borda do cobre do pad** até a via.

Proposta de critério reescrito, com o número que a medição sustenta:

> **A4 (revisado).** Todo pad SMD de GND/VBAT_PROT tem **≥ 1 via a ≤ 1,6 mm do
> centro OU a ≤ 0,5 mm da borda do seu cobre**, contada em linha reta no plano, e
> todo pad que não tiver via própria tem via de GND/VBAT_PROT a ≤ 2,5 mm do mesmo
> pad em qualquer direção. As 6 camadas estão sujas de malha de stitch com passo
> ≤ 5 mm.

- **≤ 0,5 mm da borda** é o número que a geometria atual sustenta: para os 37 pads
  restantes o ponto livre mais próximo está a 1,03–1,26 mm do centro de pads cujo
  meio-diâmetro já é 0,5 mm, ou seja, a menos de 1 mm da borda do cobre.
- **≤ 2,5 mm** cobre o pior caso medido dos pacotes de passo fino sem promising
  coisa que a máquina não mediu.
- **malha de stitch com passo ≤ 5 mm** é o critério de fabricante que realmente
  controla o retorno; ele é verificado por **contagem de malha na camada do plano**,
  que esta máquina não tem como ver sozinha (ver `fase3_pcb/GATES_REVISADOS.md`).

O gate **não é apagado**: ele continua no plano, com o número de 37 medido em cima.
A escolha entre o critério original e o revisado é decisão do Jailton, não deste
documento — `plano/DO_PROJETO.md` e `PLANO_FINAL.md` não foram tocados.

---

## 6. Resumo

- A hipótese "pad SMD em F.Cu alcança In1.Cu sem via" é **falsa**, medida em 5 casos
  no motor de conectividade do pcbnew 5.1.9 (caso B: 1 conexão aberta; caso D com
  via: 0).
- O A4 falha por **algoritmo**, não por física: a busca testava 8 pontos num raio
  só, começava no raio circunscrito do pad e desperdiçava 0,15 mm de margem.
- Gerador corrigido: **180 → 399 vias**, **68 → 37 pads sem via**, menor distância
  **0,818 → 0,700 mm**. Medido em cópia isolada, sem tocar na v8 do outro worker.
- Os **37** restantes são geometria de pacote de passo fino, não algoritmo.
  Via menor (0,5 mm) leva o limite sem-concorrência de 85 para 66 pads sem espaço.
- Critério revisado proposto com número em `fase3_pcb/GATES_REVISADOS.md` e na §5
  deste arquivo.
