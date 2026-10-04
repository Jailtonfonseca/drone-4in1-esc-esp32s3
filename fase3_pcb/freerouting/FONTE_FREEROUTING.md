# FreeRouting — origem do binário

O autorroteador **não** é versionado neste repositório (ver `.gitignore`: `*.jar`).
É um binário de terceiro, de 5 MB, e a forma correta de tener o ambiente é
reproduzi-lo, não copiá-lo.

## Versão usada

| | |
|---|---|
| Aplicativo | FreeRouting 1.9.0 (build-date 2023-10-30) |
| Arquivo | `freerouting-1.9.0.jar` |
| Tamanho | 5.044.336 bytes |
| SHA256 | `9084a4888937a7f31f857ecc…` (confirmar com `sha256sum` após o download) |
| Java | OpenJDK 17 arm64 (`apt-get install -y default-jre-headless`) |

## Por que 1.9.0 e não 1.4.4

A 1.4.4 foi baixada primeiro e o download veio **quebrado: 9 bytes**. A 1.9.0
abre o DSN desta placa. Registrado aqui para ninguém repetir o download errado.

## O que precisa ser configurado nesta máquina (medido, não presumido)

1. **`xvfb-run` é obrigatório.** Sem display o FreeRouting morre com
   `java.awt.HeadlessException`, mesmo em modo headless.
2. **O `cacerts` do JRE pode ser um symlink quebrado.** Se existir
   `ca-certificates-java` quebrado, o processo aborta com
   `trustAnchors parameter must be non-empty` ao tentar phone-home. Reconstruir
   com `keytool` a partir de `/usr/share/ca-certificates/mozilla/*.crt`.
3. **`freerouting.json`**: `num_threads` = **1** (o otimizador multithread do
   1.9.0 é bugado) e `optimization_improvement_threshold` ≈ **0,05**
   (ver item (c) abaixo). `disable_analytics: true`.
4. **O `freerouting.json` é lido de `java.io.tmpdir` (`/tmp/`), NÃO do
   diretório corrente** (`StartupOptions.java:17`). Após reboot o `/tmp` é
   limpo e as settings somem em silêncio. Copiar antes de rodar:
   `cp fase3_pcb/freerouting/freerouting.json /tmp/`.

Comandos (a partir da raiz do projeto):

```sh
mkdir -p fase3_pcb/freerouting/run && cd fase3_pcb/freerouting/run
cp ../freerouting.json /tmp/          # o app lê de java.io.tmpdir, não daqui
/usr/bin/python3.9 ../../freerouting/dsn_export.py     ../../v9/v9_drone.kicad_pcb v9_dsn_input.dsn
xvfb-run -a java -jar <caminho>/freerouting-1.9.0.jar     -de v9_dsn_input.dsn -do v9_final.ses
```

O SES só é escrito **no fim** do roteamento, e não há log de progresso durante
ele. Para não perder trabalho, deixe `save_intermediate_stages: true`.

## Erros encontrados e corrigidos em 2026-10-03 (medidos, código conferido)

O pipeline nunca tinha sido validado ponta a ponta: as execuções de 28/09 e a
primeira de 03/10 morreram **travadas**, não "calculando".

**(a) Diálogo modal trava o batch headless.** `import_design()`
(`BoardHandling.java:870`) abre um `JOptionPane` modal se a leitura do DSN
gerar *qualquer* warning. Dentro do Xvfb ninguém clica no OK e o processo fica
em `futex_wait` para sempre — antes de rotear qualquer coisa. Solução dupla:
DSN sem nenhum warning (itens b, d, e) e o **`fr_watchdog.py`** (novo), que
detecta o display do Xvfb pelo `/proc` e aperta Return via XTEST em qualquer
diálogo modal.

**(b) Ordem dos argumentos do círculo no DSN.** O exportador emitia
`(circle layer x y diam)`; o leitor (`Shape.read_circle_scope`) espera
`(circle layer diam x y)`. Pads em (0,0) viravam pontos de diâmetro ZERO
("the shape of padstack … is not an area") — o autorroteador ficava sem alvos
e "concluía" com 0 rotas. Corrigido.

**(c) `optimization_improvement_threshold: 0.0` = loop infinito.**
`BatchOptRoute.java:109`: `while (route_improved >= threshold)` — com 0.0 até
melhoria nula mantém o loop. A otimização nunca terminava (>400 s num recorte
de 9 nets). Corrigido para 0.05.

**(d) Outlines autointersectantes.** O exportador concatenava todas as linhas
da silkscreen num único polígono → warnings "winding number != 0" (gatilho do
modal do item (a)). Corrigido: outline = retângulo do bounding box.

**(e) `host_cad "kicad"` + versão baixa** → warning "old KiCad" (outro gatilho
de modal). Corrigido com nome honesto `dsn_export.py (pcbnew 5.1.9)`.

**(f) `ses_import.py`: escala da largura.** Largura do SES (µm) passada sem
×1000 ao `SetWidth` do pcbnew (nm) → trilhas 1000× mais finas. Corrigido.

**(g) Política de camadas/nets.** `In1.Cu`/`In4.Cu` viram `(type power)`
(roteador não põe sinal nos planos GND/VBAT); regra global `(width 0.25)
(clear 0.20)`; boundary recolhido 0,95 mm (as 3 rule areas); 28 nets de alta
corrente fora do DSN (GND, VBAT, VBAT_F, VBAT_PROT, 12× PHM fase 30 A, 12×
SNM shunt 30 A) — esse cobre vem de zonas no KiCad. Restam 150 nets roteáveis.

## Estado após as correções

O recorte de teste (`teste/corte_v9.*`, 16 módulos, 9 nets) roda **ponta a
ponta com exit=0**: leitura sem warnings, roteamento 0,82 s, otimização 0,07 s,
SES gravado.

**Problema ABERTO (8º erro, ainda sem correção):** o SES sai com **0 wires** —
as rotas existem no estágio intermediário (`.frb`, 126 KB) mas não chegam à
exportação. Suspeitos: via atravessando layer `power`, ou matching de
pin/padstack na saída. Próximo passo do diagnóstico antes da placa completa.
