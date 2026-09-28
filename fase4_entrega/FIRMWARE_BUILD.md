# FIRMWARE_BUILD — dá para compilar firmware do ESP32-S3 nesta máquina?

**Data:** 2026-09-28
**Máquina:** Orange Pi 3B — Linux 5.10.160-rockchip-rk356x, **aarch64**, Debian 11 (Bullseye), sem desktop
**Pergunta:** o firmware do drone (`plano/WP4_FIRMWARE.md` §5) pode ser compilado aqui?

---

## 1. Veredito, em uma linha

**Metade sim, metade não.** O **compilador** do ESP32-S3 foi instalado nesta
máquina e foi verificado com um programa real — gera `.o`, `.elf` e `.bin`
para a arquitetura Xtensa. O **ESP-IDF**, que é o framework sem o qual nenhum
projeto de firmware é construído, **não está instalado e não foi instalado**,
porque ele passaria de 2 GB. Portanto `firmware/main/*.c` **não foi compilado
e não pode ser compilado aqui ainda**.

## 2. O estado inicial, medido

```
$ which idf.py xtensa-esp32s3-elf-gcc arduino-cli pio platformio
(vazio — nenhum dos cinco existe)

$ ls -d /opt/esp* ~/esp ~/.espressif
ls: cannot access '/opt/esp*': No such file or directory
ls: cannot access '/root/esp': No such file or directory
ls: cannot access '/root/.espressif': No such file or directory
```

Ferramentas de base que já existiam:

```
python3  -> /root/.qwenpaw/venv/bin/python3     (Python 3.12.13)
pip3     -> /root/.qwenpaw/venv/bin/pip3        (python3-pip 20.3.4 instalado)
cmake    -> /usr/local/bin/cmake                 (3.29.3; o apt tem 3.25.1)
ninja    -> AUSENTE
git      -> /usr/bin/git                        (2.30.2)
wget     -> /usr/bin/wget                       (1.21.1)
curl     -> /usr/bin/curl                       (7.74.0)
gcc      -> /usr/bin/gcc                        (10.2.1, do host, não é cross)
make     -> /usr/bin/make

$ uname -a
Linux orangepi3b 5.10.160-rockchip-rk356x #1.0.8 SMP Nov 18 11:49:28 CST 2024 aarch64 GNU/Linux

$ df -B1 --output=avail / | tail -1
55690661888        (52 GB livres)
```

## 3. O que o apt oferece — e por que não basta

```
$ apt-cache policy gcc-xtensa-lx106-elf
(vazio — o pacote não existe neste repositório)

$ apt-cache search xtensa
binutils-xtensa-lx106 - GNU binary utilities, for Xtensa lx106 core
gcc-xtensa-lx106     - GNU C compiler for Xtensa lx106 core
picolibc-xtensa-lx106-elf - Smaller embedded C library for ESP8266 development
qemu-system-misc     - QEMU full system emulation binaries (miscellaneous)

$ apt-cache search esp32
esptool - create and flash firmware files to ESP8266 and ESP32 chips

$ apt-cache search espressif
(vazio)
```

O que o Debian Bullseye oferece é **`gcc-xtensa-lx106`**, que é o core do
**ESP8266**. O ESP32-S3 é **Xtensa LX7**, não LX106. Não há pacote de
toolchain para ele no apt, e não há pacote `espressif` nenhum. O `esptool` que
existe é de232, útil para gravar, inútil para compilar.

**O apt não é caminho.** O caminho oficial é o ESP-IDF.

## 4. O que a web diz: existe release para aarch64?

**Sim, e foi isso que mudou a resposta.** O que estava em dúvida era se o
toolchain Xtensa da Espressif seria publicado para host `aarch64` ou só para
`x86_64` — em que caso compilar aqui seria impossível sem emulação.

A fonte primária é o `tools.json` da própria ESP-IDF, que é o arquivo que o
`idf_tools.py` usa para decidir o que baixar. Branch `v5.4`, ferramenta
`xtensa-esp-elf`:

```
$ curl -sS https://raw.githubusercontent.com/espressif/esp-idf/v5.4/tools/tools.json
```

Trecho literal, com o campo `size` em bytes:

```json
{
  "name": "xtensa-esp-elf",
  "version_cmd": ["xtensa-esp-elf-gcc", "--version"],
  "supported_targets": ["esp32", "esp32s2", "esp32s3"],
  "versions": [
    {
      "name": "esp-14.2.0_20241119",
      "status": "recommended",
      "linux-amd64": {
        "url": ".../xtensa-esp-elf-14.2.0_20241119-x86_64-linux-gnu.tar.xz",
        "size": 174652716,
        "sha256": "e3e6dcf3d275c3c9ab0e4c8a9d93fd10e7efc035d435460576c9d95b4140c676"
      },
      "linux-arm64": {
        "url": ".../xtensa-esp-elf-14.2.0_20241119-aarch64-linux-gnu.tar.xz",
        "size": 176920772,
        "sha256": "ac2b311dc0003386425086bfc813bf2aeb3cdf3b117845802df6ebef5f69955f"
      },
      "macos-arm64": { "size": 167948176, ... }
    }
  ]
}
```

Duas conclusões que fecham a discussão:

1. **`supported_targets` inclui `esp32s3`.** O toolchain é o certo.
2. **`linux-arm64` existe, com 176.920.772 bytes (169 MiB).** Não há
   emulação, não há container x86, não há gambiarra: o binário nativo para
   aarch64 é publicado oficialmente.

A documentação de downloads do ESP-IDF confirma a mesma coisa na tabela de
plataformas de `esp32s3/api-guides/tools/idf-tools.html`, que lista
`linux-amd64`, `linux-arm64`, `linux-armel`, `linux-armhf` para as ferramentas
da família.

**O procedimento oficial de instalação** (que é o que o Jailton deve seguir
para o restante) está em
`https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/linux-setup.html`:
repositório EIM da Espressif no apt → `eim install`. A ESP-IDF v6.0+ passou a
usar o *ESP-IDF Installation Manager*; a ESP-IDF v5.x usa o método legado,
`git clone --recursive` + `install.sh`. As duas páginas estão citadas na
seção 5.

## 5. O que foi instalado, e quanto ocupou

Duas coisas, e só duas. Nada de sistema foi sobrescrito: `ninja-build` era um
pacote **novo** (não estava instalado antes), e o toolchain foi para
`/root/esp`, fora do sistema.

### 5.1 Toolchain Xtensa (o compilador)

Sonda de velocidade antes de comprometer o download:

```
$ curl -sSL -o /dev/null --max-time 25 -r 0-8388607 -w \
    "baixados=%{size_download} bytes em %{time_total}s => %{speed_download} B/s\n" <url>
baixados=8388608 bytes em 10.152098s => 826301 B/s
```

826 kB/s ÷ 176.920.772 B ≈ 214 s. Abaixo do limite de 10 min da tarefa, então
o download foi feito:

```
$ curl -sSL --max-time 900 -o xtensa-esp-elf-14.2.0_20241119-aarch64-linux-gnu.tar.xz -w \
    "http=%{http_code} bytes=%{size_download} tempo=%{time_total}s media=%{speed_download}B/s\n" <url>
http=200 bytes=176920772 tempo=148.269942s media=1193241B/s
```

**Download verificado contra o sha256 publicado no `tools.json`:**

```
$ sha256sum xtensa-esp-elf-14.2.0_20241119-aarch64-linux-gnu.tar.xz
ac2b311dc0003386425086bfc813bf2aeb3cdf3b117845802df6ebef5f69955f  <arquivo>
```

Idêntico ao `ac2b311dc0003386425086bfc813bf2aeb3cdf3b117845802df6ebef5f69955f`
do `tools.json`. **Esperado × medido × erro: erro 0.**

Instalado no layout que a própria ESP-IDF usa, para que uma instalação futura
do ESP-IDF reconheça a ferramenta:

```
$ tar -xJf xtensa-esp-elf-...tar.xz \
      -C /root/esp/.espressif/tools/xtensa-esp-elf/esp-14.2.0_20241119 \
      --strip-components=1

$ du -sb /root/esp/.espressif/tools/xtensa-esp-elf/esp-14.2.0_20241119
1093379305        (1,0 GB extraído; o .tar.xz de 169 MiB também ficou em disco)

$ du -sh <mesmo diretório>/*
78M  bin      24M lib      84M libexec    365M picolibc   495M xtensa-esp-elf
```

| Item | Bytes |
|---|---:|
| `.tar.xz` baixado (fica em `dist/`) | 176.920.772 |
| toolchain extraído | 1.093.379.305 |
| **total ocupado pelo toolchain** | **1.270.300.077** (≈ 1,18 GiB) |

### 5.2 `ninja-build` (pré-requisito de qualquer build ESP-IDF)

```
$ apt-cache show ninja-build | grep -E '^(Version|Size|Installed-Size)'
Version: 1.10.1-1
Size: 106824
Installed-Size: 335

$ apt-get install -y ninja-build
Setting up ninja-build (1.10.1-1) on arm64 ...

$ ninja --version
1.10.1
```

| Item | Bytes |
|---|---:|
| download | 106.824 |
| instalado (`/usr/bin/ninja`) | 232.664 |

Nenhum pacote foi **removido** nem **substituído**:
`0 upgraded, 1 newly installed, 0 to remove, 13 not upgraded`.

### 5.3 O que NÃO foi instalado, e por quê

**O ESP-IDF.** Dimensionado a partir de dados reais, não de estimativa:

```
$ curl -sS https://api.github.com/repos/espressif/esp-idf | python3 -c "..."
size (KB, sem submodules): 458774          (= 448 MB só o repo, sem submódulos)

$ curl -sS https://raw.githubusercontent.com/espressif/esp-idf/v5.4/.gitmodules | grep -c submodule
23                                          (23 submódulos por cima disso)
```

448 MB de repo + 23 submódulos + o venv de Python (`--features`, ~100 MB de
dependências) + as ferramentas que o `install.sh` baixa (openocd, cmake,
bootloader, e também um `xtensa-esp-elf-gdb` de ~150 MB para `linux-arm64`)
soma com folga mais de 2 GB, o que ultrapassa o teto da tarefa. Some-se a isso
o fato de a ESP-IDF v6 exigir **Python 3.10 ou superior**, e o Python do
sistema aqui ser o **3.9.2** (`/usr/bin/python3 -> python3.9`), o que já é um
bloqueio por si só no caminho do instalador.

**Portanto: o ESP-IDF não foi instalado, e `firmware/main/*.c` não foi
compilado.** Nenhuma linha daquele código passou pelo compilador.

## 6. O que foi realmente compilado, e o que isso prova

Um **teste de fumaça** do compilador: um `.c` de 5 linhas, sem ESP-IDF, sem
startup, sem linker script da Espressif. A saída completa, verbatim, está em
[`../firmware/build_log.txt`](../firmware/build_log.txt). Resumo:

```
$ xtensa-esp32s3-elf-gcc --version
xtensa-esp-elf-gcc (crosstool-NG esp-14.2.0_20241119) 14.2.0

$ xtensa-esp32s3-elf-gcc -print-multi-lib | grep esp32s3
esp32s3;@mdynconfig=xtensa_esp32s3.so
esp32s3/no-rtti;@mdynconfig=xtensa_esp32s3.so@fno-rtti

$ xtensa-esp32s3-elf-gcc -c -O2 -Wall -Wextra -std=gnu17 hello_world.c -o hello_world.o
exit=0   (1316 bytes, sem aviso)

$ xtensa-esp32s3-elf-objdump -f hello_world.o
hello_world.o:     file format elf32-xtensa-le
architecture: xtensa, flags 0x00000011:

$ xtensa-esp32s3-elf-gcc -nostdlib -nostartfiles -Wl,-Ttext=0x400d0000 ... -o hello_world.elf
ld: warning: cannot find entry symbol _start; defaulting to 400d0000
exit=0   (5040 bytes)

$ xtensa-esp32s3-elf-readelf -h hello_world.elf | grep -E 'Class|Machine|Entry'
  Class:                             ELF32
  Machine:                           Tensilica Xtensa Processor
  Entry point address:               0x400d0000

$ xtensa-esp32s3-elf-objcopy -O binary hello_world.elf hello_world.bin
exit=0   (25 bytes)
```

### Esperado × medido × erro

| O quê | Esperado | Medido | Erro |
|---|---|---|---:|
| download do toolchain | 176.920.772 B | 176.920.772 B | **0 B** |
| sha256 do download | `ac2b311d…955f` | `ac2b311d…955f` | idêntico |
| formato do objeto | `elf32-xtensa-le` | `elf32-xtensa-le` | — |
| `Machine` do ELF | Tensilica Xtensa | Tensilica Xtensa | — |
| `exit code` do `gcc -c` | 0 | 0 | — |
| `exit code` do link | 0 | 0 | — |
| `exit code` do `objcopy` | 0 | 0 | — |

### O que esse teste **não** é

O `.bin` de 25 bytes **não é gravável** num ESP32-S3 e não faria o chip
bootar: o link foi feito com `-nostdlib` e um `-Ttext` provisório, e o próprio
`ld` avisou que não achou `_start`. Não há startup, nem tabela de partições, nem
particionamento, nem bootloader. O que ele prova é **uma coisa só**: que o
compilador C desta máquina fala Xtensa e produz ELF de 32 bits para o ESP32-S3.

## 7. O que falta, para compilar o firmware de verdade

| Falta | Tamanho estimado | Como resolver |
|---|---:|---|
| ESP-IDF (repo + 23 submódulos) | ~700 MB–1,2 GB | `git clone --recursive` ou `eim install` |
| Python ≥ 3.10 para o instalador | ~150 MB | o sistema tem 3.9.2; usar `/root/.qwenpaw/venv` (3.12.13) ou instalar 3.10+ |
| Ferramentas que o `install.sh` baixa | ~200 MB+ | automático, via `IDF_TOOLS_PATH` |
| `esp32s3.project.ld` e startup | incluído no ESP-IDF | automático |
| Módulos de driver (MCPWM, LEDC, SPI, ADC) | incluído no ESP-IDF | automático |
| **Mapa pad → GPIO** | 0 bytes, **mas é o gargalo real** | `datasheets/esp32-s3-wroom-1_datasheet_en.pdf` |

A última linha é a que mais importa, e não é uma instalação: é a **RF-07** do
`plano/WP4_FIRMWARE.md`. Todos os GPIO de `firmware/main/board_pins.h` estão
`-1` de propósito. A Fase 0 §8 e o layout v7 discordam nos motores 2, 3 e 4
inteiros (o pad 8, que a Fase 0 dava ao motor 2, é `PWM_M403` no layout), e
traduzir pad → GPIO exige a tabela de pinagem do módulo, que **não foi extraída
nesta sessão**. Escrever os números por dedução da Fase 0 produziria um
binário que não funciona na placa — que é literalmente o que a RF-07 acusa.

## 8. Comando exato de build de teste

**Hoje, sem ESP-IDF, este é o único build honesto** — e ele prova o toolchain,
não o firmware:

```bash
export PATH=/root/esp/.espressif/tools/xtensa-esp-elf/esp-14.2.0_20241119/bin:$PATH
xtensa-esp32s3-elf-gcc --version          # deve dizer 14.2.0
printf 'int main(void){return 0;}\n' > /tmp/t.c
xtensa-esp32s3-elf-gcc -c /tmp/t.c -o /tmp/t.o && echo "COMPILADOR OK"
```

**Depois que o ESP-IDF for instalado** (M0 do `plano/WP4_FIRMWARE.md` §5), o
comando de build do firmware do drone é:

```bash
# uma vez, na shell de setup
. $HOME/esp/esp-idf/export.sh

# build de teste do esqueleto — o comando que o Jailton vai rodar
cd /opt/jupyter/work/drone/firmware
idf.py set-target esp32s3
idf.py build
```

**Espere-se que este build falhe**, e a falha esperada está documentada: ele
para em `board_pins.h`, porque todo GPIO é `GPIO_NAO_CONFERIDO` (-1). Isso é o
comportamento projetado. O primeiro build de verdade é o que documenta os erros
de API dos quatro módulos, e vale a pena colar essa saída no repositório antes
de mexer em qualquer número.

Para gravar depois (com a placa em modo DFU/USB-C e a hélice removida):

```bash
idf.py -p /dev/ttyACM0 flash monitor
```

Nada foi gravado em hardware: não há placa conectada a esta máquina.

## 9. Decisão que cabe ao Jailton

Instalar o ESP-IDF ocupa **~2 a 3 GB** nesta máquina, que tem
52 GB livres — dá, mas é a maior instalação já feita aqui e ela **pode mexer
no Python 3.9 do sistema**, se o instalador não olhar as dependências antes.
Três caminhos:

1. **Instalar o ESP-IDF aqui** (M0 inteiro, 12 h **[EST]** na §5). Habilita
   M1–M13. É o caminho que o plano assume.
2. **Não instalar e compilar o firmware em outra máquina** (x86-64, mais
   comum), mantendo esta para simulação e documentação — que é o que ela já faz
   desde a fase 0.
3. **Instalar só o gdb** (o `linux-arm64` do `xtensa-esp-elf-gdb` existe,
   mesma família) para depurar firmware gravado por outra via. ~100 MB, resolve
   pouco.

Nenhuma delas foi executada sem a decisão. A recomendação, se o objetivo for
continuar o firmware na Fase 4, é a **1** — a máquina tem disco, tem cmake 3.29,
tem ninja 1.10.1 e agora tem o compilador. O único bloqueio real é o mapa
pad → GPIO, que é trabalho de bancada e de datasheet, não de instalação.
