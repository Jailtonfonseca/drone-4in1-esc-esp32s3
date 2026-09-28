PACOTE DE FABRICACAO -- drone_v7
============================================================
projeto ........: drone (FPGA/controlador de voo)
revisao ........: v7
data ...........: 2026-09-28
autor ..........: Jailton
board de origem : /opt/jupyter/work/drone/fase3_pcb/v7/v7_drone.kicad_pcb
gerado em ......: 2026-09-28 08:59:12
pcbnew .........: 5.1.9+dfsg1-1+deb11u1

CONTEUDO DO PACOTE
------------------------------------------------------------
GERBERS (RS-274X, extensao de protel, na ordem F -> B):
  drone_v7_F_Cu.gtl          cobre superior (sinal)                     375084 bytes
  drone_v7_In1_Cu.g2         cobre interno 1 (sinal)                    162219 bytes
  drone_v7_In2_Cu.g3         cobre interno 2 (sinal)                    635727 bytes
  drone_v7_B_Cu.gbl          cobre inferior (sinal)                     132600 bytes
  drone_v7_F_Mask.gts        mascara de solda superior (verniz)         262928 bytes
  drone_v7_B_Mask.gbs        mascara de solda inferior (verniz)         2926 bytes
  drone_v7_F_SilkS.gto       silk top (identificacao dos componentes)   315458 bytes
  drone_v7_B_SilkS.gbo       silk bottom (identificacao dos componentes) 2929 bytes
  drone_v7_Edge_Cuts.gm1     perfil/contorno da placa ( Edge.Cuts )     747 bytes

FUROS (Excellon, PTH e NPTH separados):
  drone_v7-PTH.drl           furos  plated thru-hole , 5693 bytes
  drone_v7-NPTH.drl          furos nao plated thru-hole, 368 bytes

JOB FILE:
  drone_v7.gbrjob            2937 bytes

MAPA DE FUROS:
  drone_v7-NPTH-drl_map.pdf  3983 bytes
  drone_v7-PTH-drl_map.pdf   21457 bytes
  drone_v7_mapa_furos.png    100876 bytes

PICK-AND-PLACE (PosX/PosY em milesimos de mm, rot em graus):
  drone_v7-Top.pos           319 componentes (camada Top)
  drone_v7-Bottom.pos        0 componentes (camada Bottom)
  drone_v7-pos.csv           319 componentes (Top+Bottom)

RELATORIOS:
  drone_v7-DRC.rpt           ver o arquivo: o DRC nao roda nesta maquina

RESUMO DO BOARD
------------------------------------------------------------
  footprints                         319
  pads                               1093
  pads PTH (com furo metalizado)     44
  pads NPTH (furo isolado)           4
  pads SMD (sem furo)                1045
  nets                               203
  camadas de cobre                   4
  dimensoes da placa (mm)            220.10 x 160.10
  espessura do substrato (mm)        1.60

COMO ESTE PACOTE FOI NOMEADO
------------------------------------------------------------
  O .kicad_pcb de origem NAO tem bloco 'title_block'. O pcbnew 5.1 monta o
  nome do plot como '<basename do board>-<plot>.<ext>'; sem basename ele
  emite '-drone_F_Cu.gtl' (hifen na frente, mesmo nome em v1..v7).
  Aqui o title_block e preenchido EM MEMORIA antes do plot e cada arquivo
  e renomeado para 'drone_v7_<Camada>.<ext>', sem hifen e com a versao.
  O .kicad_pcb do repositorio NAO foi alterado: o title block serve so ao
  plot e ao .gbrjob desta pasta.

NOTA SOBRE O .gbrjob
------------------------------------------------------------
  O pcbnew 5.1 aceita SetCreateGerberJobFile(True) mas nao emite nenhum
  arquivo .gbrjob em modo headless (verificado: 0 arquivos). O job file
  desta pasta foi escrito pela GERBER_JOBFILE_WRITER.WriteJSONJobFile(),
  que e o unico caminho que produz o arquivo nesta versao.

NOTA SOBRE O .drr
------------------------------------------------------------
  EXCELLON_WRITER.GenDrillReportFile() ABORTA o processo (terminate:
  throwing an instance of 'IO_ERROR' / Aborted) no pcbnew 5.1.9 headless.
  Por isso nao ha .drr: no lugar entraram o PDF de mapa de furos gerado
  pelo proprio KiCad (CreateMapFilesSet) e um PNG equivalente em matplotlib.

NOTA SOBRE O DRC
------------------------------------------------------------
  O modulo Python do pcbnew 5.1.9 nao expoe API de DRC e o pcbnew e GTK,
  sem display: o DRC so roda na interface grafica. Ver drone_v7-DRC.rpt.
  A copia do board com o title_block preenchido, pronta para abrir no
  pcbnew e rodar o DRC na mao, esta em:
    _inspecao/board_para_drc.kicad_pcb

NOTA SOBRE A SERIGRAFIA
------------------------------------------------------------
  A serigrafia foi plotada SEM referencia e SEM valor dos componentes
  (padrao de producao: com 319 footprints o texto fica ilegivel). Para
  inspecao ou montagem use as flags --silk-com-refs e --silk-com-valores.
