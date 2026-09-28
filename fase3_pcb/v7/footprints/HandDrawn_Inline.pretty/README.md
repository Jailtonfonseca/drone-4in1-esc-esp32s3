# Biblioteca extraida do board: HandDrawn_Inline

Gerada por `gera_cpl_v7.py` a partir de `fase3_pcb/v7/v7_drone.kicad_pcb`.

## O QUE ESTA PASTA CONTEM

6 arquivo(s) `.kicad_mod`, **extracao** do board: cada um tem o `fp_text reference`,
o `fp_text value`, o `fp_text user` e a geometria `fp_line`/`fp_arc`/`fp_circle`,
alem dos pads (numero, tipo, shape, tamanho, rotacao, camadas e furo),
tudo copiado do `.kicad_pcb` sem alteracao de geometria.

## O QUE FALTA NESTA EXTRACAO

Tres coisas nao podem ser recuperadas do board e por isso NAO estao nos arquivos:

1. **lib nickname** -- o formato `.kicad_pcb` versao 20171130 (KiCad 5.1) descarta o
   nickname de biblioteca de cada modulo ao salvar. A biblioteca desta pasta foi
   resolvida por busca do nome do footprint em `/usr/share/kicad/modules`; se um
   nome existisse em varias bibliotecas, foi escolhido o primeiro em ordem alfabetica.
2. **modelos 3D** -- o board nao tem nenhum link `3dmodel`.
3. **grupo `path`** -- o board nao grava o caminho de origem da biblioteca.

Nada foi inventado: o que esta nos arquivos veio do board; o que falta esta listado acima.

## BIBLIOTECA REAL

A biblioteca original **NAO existe** neste sistema em `/usr/share/kicad/modules`.
Os arquivos desta pasta sao extracao fiel desses modulos do board, nao invencao:
pads e geometria vieram do `.kicad_pcb`. O que falta e so o metadado de
biblioteca (nickname e caminho de origem), que o formato do board nao guarda:
e preciso instalar a biblioteca KiCad correspondente ou fornecer os arquivos
originais para poder reproduzi-la.

## CONTEUDO

- `HandDrawn_Inline.pretty/MAO_UB1.kicad_mod` &mdash; 8 pads, modulo de origem `UB1` no board
- `HandDrawn_Inline.pretty/MAO_UB2.kicad_mod` &mdash; 8 pads, modulo de origem `UB2` no board
- `HandDrawn_Inline.pretty/MAO_UB3.kicad_mod` &mdash; 8 pads, modulo de origem `UB3` no board
- `HandDrawn_Inline.pretty/MAO_U_BARO.kicad_mod` &mdash; 8 pads, modulo de origem `U_BARO` no board
- `HandDrawn_Inline.pretty/MAO_U_LDO.kicad_mod` &mdash; 6 pads, modulo de origem `U_LDO` no board
- `HandDrawn_Inline.pretty/MAO_U_MCU.kicad_mod` &mdash; 41 pads, modulo de origem `U_MCU` no board
