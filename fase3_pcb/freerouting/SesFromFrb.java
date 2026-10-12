import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.ObjectInputStream;
import java.io.OutputStream;

import app.freerouting.board.RoutingBoard;
import app.freerouting.designforms.specctra.SpecctraSesFileWriter;

/**
 * Extrai um SES do estado bancado do .frb do FreeRouting — sem GUI e sem
 * rotear mais nada. Le o RoutingBoard serializado (com todas as rotas e
 * keepouts) e grava o Specctra Session File.
 *
 * Uso: java SesFromFrb entrada.frb saida.ses
 */
public class SesFromFrb {
  public static void main(String[] args) throws Exception {
    if (args.length < 2) {
      System.err.println("uso: java SesFromFrb entrada.frb saida.ses");
      System.exit(2);
    }
    try (ObjectInputStream in =
             new ObjectInputStream(new FileInputStream(args[0]))) {
      RoutingBoard board = (RoutingBoard) in.readObject();
      System.out.println(
          "board carregado: " + board.get_items().size() + " itens");
      try (OutputStream out = new FileOutputStream(args[1])) {
        boolean ok = SpecctraSesFileWriter.write(board, out, "v10");
        System.out.println("SES gravado: " + ok + " -> " + args[1]);
        if (!ok) {
          System.exit(3);
        }
      }
    }
  }
}
