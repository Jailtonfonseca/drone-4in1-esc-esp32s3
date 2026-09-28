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
3. **`freerouting.json`**: `disable_analytics: true` e `num_threads` ≥ 2.

Comandos (a partir da raiz do projeto):

```sh
mkdir -p fase3_pcb/freerouting/run && cd fase3_pcb/freerouting/run
cp ../freerouting.json .
/usr/bin/python3.9 ../../freerouting/dsn_export.py     ../../v9/v9_drone.kicad_pcb v9_dsn_input.dsn
xvfb-run -a java -jar <caminho>/freerouting-1.9.0.jar     -de v9_dsn_input.dsn -do v9_final.ses
```

O SES só é escrito **no fim** do roteamento, e não há log de progresso durante
ele. Para não perder trabalho, deixe `save_intermediate_stages: true`.
