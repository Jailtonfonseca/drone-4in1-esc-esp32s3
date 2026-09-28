# Biblioteca extraida do board: Connector_USB

Gerada por `gera_cpl_v7.py` a partir de `fase3_pcb/v7/v7_drone.kicad_pcb`.

## O QUE ESTA PASTA CONTEM

1 arquivo(s) `.kicad_mod`, **extracao** do board: cada um tem o `fp_text reference`,
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

A biblioteca original **existe** neste sistema:

    /usr/share/kicad/modules/Connector_USB.pretty

Para obter os footprints verdadeiros desta placa, extraia do board e grave com
o proprio pcbnew, que le a geometria completa da biblioteca:

    /usr/bin/python3.9 - <<'PY'
    import pcbnew
    b = pcbnew.LoadBoard('fase3_pcb/v7/v7_drone.kicad_pcb')
    fp = pcbnew.FootprintLoad('/usr/share/kicad/modules/Connector_USB.pretty', '<NOME>')
    pcbnew.SaveBoard('saida.kicad_pcb', b)  # ou fp.Save('.pretty/NOME.kicad_mod')
    PY

O escopo deste script foi limitado a ler o board e gravar arquivos novos, sem
tocar no `v7_drone.kicad_pcb`.

## CONTEUDO

- `Connector_USB.pretty/USB_C_Receptacle_GCT_USB4085.kicad_mod` &mdash; 20 pads, modulo de origem `J2` no board
